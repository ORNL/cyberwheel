import time
from tqdm import tqdm
import argparse

from typing import List

import gym
import wandb
import torch
import torch.nn as nn
import numpy as np
import pandas as pd

from torch.distributions.categorical import Categorical

from cyberwheel.cyberwheel_envs.cyberwheel_restore import RestoreCyberwheel
from cyberwheel.cyberwheel_envs.cyberwheel_dynamic import DynamicCyberwheel
from cyberwheel.blue_agents.decoy_blue import DecoyBlueAgent
from cyberwheel.red_agents import KillChainAgent, ARTAgent
from cyberwheel.cyberwheel_envs.cyberwheel_decoyagent import *

from cyberwheel.visualize import visualize


def layer_init(layer, std=np.sqrt(2), bias_const=0.0):
    """Initialise neural network weights using orthogonal initialization. Works well in practice."""
    torch.nn.init.orthogonal_(layer.weight, std)
    torch.nn.init.constant_(layer.bias, bias_const)
    return layer


class Agent(nn.Module):
    """
    The agent class that contains the code for defining the actor and critic networks used by PPO.
    Also includes functions for getting values from the critic and actions from the actor.
    """

    def __init__(self, envs):
        super().__init__()
        # Actor network has an input layer, 2 hidden layers with 64 nodes, and an output layer.
        # Input layer is the size of the observation space and output layer is the size of the action space.
        # Predicts the best action to take at the current state.
        print(envs.single_observation_space.shape)
        self.actor = nn.Sequential(
            layer_init(
                nn.Linear(int(np.array(envs.single_observation_space.shape).prod()), 64)
            ),
            nn.ReLU(),
            layer_init(nn.Linear(64, 64)),
            nn.ReLU(),
            layer_init(nn.Linear(64, envs.single_action_space.n), std=0.01),
        )

        # Critic network has an input layer, 2 hidden layers with 64 nodes, and an output layer.
        # Input layer is the size of the observation space and output layer has 1 node for the predicted value.
        # Predicts the "value" - the expected cumulative reward from using the actor policy from the current state onward.
        self.critic = nn.Sequential(
            layer_init(
                nn.Linear(int(np.array(envs.single_observation_space.shape).prod()), 64)
            ),
            nn.ReLU(),
            layer_init(nn.Linear(64, 64)),
            nn.ReLU(),
            layer_init(nn.Linear(64, 1), std=1.0),
        )

    def get_value(self, x):
        """Gets the value for a given state x by running x through the critic network"""
        return self.critic(x)

    def get_action_and_value(self, x, action=None):
        """
        Gets the action and value for the current state by running x through the actor and critic respectively.
        Also calculates the log probabilities of the action and the policy's entropy which are used to calculate PPO's training loss.
        """
        logits = self.actor(x)
        probs = Categorical(logits=logits)
        if action is None:
            action = probs.sample()
        return action, probs.log_prob(action), probs.entropy(), self.critic(x)


def make_env(
    env_id: str,
    rank: int,
    network_config: str,
    decoy_host_file: str,
    host_def_file: str,
    detector_config: str,
    seed: int = 0,
    min_decoys=1,
    max_decoys=1,
    blue_reward_scaling=10,
    reward_function="default",
    red_agent="killchain_agent",
    max_steps=50,
):
    """
    Utility function for multiprocessed env.

    :param env_id: the environment ID
    :param num_env: the number of environments you wish to have in subprocesses
    :param seed: the inital seed for RNG
    :param rank: index of the subprocess
    """

    def _init():
        env = DynamicCyberwheel(
            network_config=network_config,
            decoy_host_file=decoy_host_file,
            host_def_file=host_def_file,
            detector_config=detector_config,
            min_decoys=min_decoys,
            max_decoys=max_decoys,
            blue_reward_scaling=blue_reward_scaling,
            reward_function=reward_function,
            red_agent=red_agent,
            evaluation=True,
            max_steps=max_steps,
        )
        env.reset(seed=seed + rank)  # Reset the environment with a specific seed
        return env

    return _init


def parse_args():
    parser = argparse.ArgumentParser()
    # parser.add_argument('--visualize', help='generate the graphs with matplotlib, displayed in WandB', action='store_true')
    parser.add_argument(
        "--download-model",
        help="Download agent model from WandB. If present, requires --run flag.",
        action="store_true",
    )
    parser.add_argument(
        "--agent",
        help="Red agent strategy to evaluate against",
        default="killchain_agent",
    )
    parser.add_argument(
        "--run", help="Run ID from WandB for pretrained blue agent to use", default=None
    )
    parser.add_argument(
        "--experiment",
        help="Experiment name for storing/retrieving agent model",
        default="temp_model",
    )
    parser.add_argument(
        "--visualize",
        help="Store graphs of network state at each step/episode. Can be viewed in dash server.",
        action="store_true",
    )
    # parser.add_argument('--baseline', help='Use baseline observation and actions.', action='store_true')
    parser.add_argument(
        "--graph-name",
        help="Override naming convention of graph storage directory.",
        default=None,
    )
    # network generation args
    parser.add_argument(
        "--network-config",
        help="Input the network config filename",
        type=str,
        default="example_config.yaml",
    )
    parser.add_argument(
        "--decoy-config",
        help="Input the decoy config filename",
        type=str,
        default="decoy_hosts.yaml",
    )
    parser.add_argument(
        "--host-config",
        help="Input the host config filename",
        type=str,
        default="host_definitions.yaml",
    )

    parser.add_argument(
        "--detector-config",
        help="Path to detector config file",
        type=str,
        default="decoys_only.yaml",
    )

    # reward calculator args
    parser.add_argument(
        "--min-decoys",
        help="Minimum number of decoys that should be used",
        type=int,
        default=2,
    )
    parser.add_argument(
        "--max-decoys",
        help="Maximum number of decoys that should be used",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--reward-scaling",
        help="Variable used to increase rewards",
        type=float,
        default=5.0,
    )
    parser.add_argument(
        "--reward-function",
        help="Which reward function to use. Current options: default | step_detected",
        type=str,
        default="default",
    )

    parser.add_argument(
        "--num-steps",
        help="Number of steps per episode for evaluation",
        type=int,
        default=50,
    )

    parser.add_argument(
        "--num-episodes", help="Number of episodes to evaluate", type=int, default=10
    )

    args = parser.parse_args()

    # print(args)

    bool_run = args.run != None  # true if run given, false if run not given

    if args.download_model != bool_run:
        parser.error("--run and --download-model flag required when downloading model")

    return args


def evaluate_cyberwheel():
    args = parse_args()
    device = torch.device("cpu")
    print(f"Using device {device}")

    env_funcs = [
        make_env(
            1,
            0,
            network_config=args.network_config,
            decoy_host_file=args.decoy_config,
            host_def_file=args.host_config,
            detector_config=args.detector_config,
            min_decoys=args.min_decoys,
            max_decoys=args.max_decoys,
            blue_reward_scaling=args.reward_scaling,
            reward_function=args.reward_function,
            red_agent=args.agent,
            max_steps=args.num_steps,
        )
    ]
    envs = gym.vector.SyncVectorEnv(env_funcs)

    agent = Agent(envs).to(device)

    experiment_name = args.experiment
    if args.download_model:
        api = wandb.Api()
        run = api.run(f"oeschsec/Cyberwheel/runs/{args.run}")
        model = run.file("agent.pt")
        model.download(f"models/{experiment_name}/", exist_ok=True)

    agent.load_state_dict(
        torch.load(f"models/{experiment_name}/agent.pt", map_location=device)
    )
    agent.eval()

    print("Resetting the environment...")
    start_time = time.time()

    episode_rewards = []
    total_reward = 0
    steps = 0
    obs = envs.reset()

    logging = True

    print("Playing environment with random actions...")

    if args.graph_name != None:
        now_str = args.graph_name
    else:
        now_str = f"{experiment_name}_evaluate_{args.network_config.split('.')[0]}_killchainagent_{args.min_decoys}-{args.max_decoys}_scaling{args.reward_scaling}_{args.reward_function}reward"
    log_file = f"action_logs/{now_str}.csv"

    actions_df = pd.DataFrame()
    full_episodes = []
    full_steps = []
    full_red_action_type = []
    full_red_action_src = []
    full_red_action_dest = []
    full_red_action_success = []
    full_blue_actions = []
    full_rewards = []

    for episode in tqdm(range(args.num_episodes)):
        blue_actions = []
        red_actions = []
        for step in range(args.num_steps):
            if step == 0:
                obs = obs[0]
            obs = torch.Tensor(obs).to(device)
            action, logprob, _, value = agent.get_action_and_value(obs)

            all_action = None
            blue_action = None
            red_action = None

            obs, rew, done, _, info = envs.step(action.cpu().numpy())
            rew = rew[0]
            done = done[0]

            if "final_observation" in list(info.keys()):
                all_action = info["final_info"][0]["action"]
                net = info["final_info"][0]["network"]
                history = info["final_info"][0]["history"]
                killchain = info["final_info"][0]["killchain"]
            else:
                all_action = info["action"][0]
                net = info["network"][0]
                history = info["history"][0]
                killchain = info["killchain"][0]
            # print(all_action)
            # print(rew)
            blue_action = all_action["Blue"]
            red_action = all_action["Red"]
            red_action_parts = red_action.split(" ")
            red_action_type = red_action_parts[2]
            red_action_src = red_action_parts[4]
            red_action_dest = red_action_parts[6]
            red_action_success = red_action_parts[0] == "Success"

            full_episodes.append(episode)
            full_steps.append(step)
            full_red_action_type.append(red_action_type)
            full_red_action_src.append(red_action_src)
            full_red_action_dest.append(red_action_dest)
            full_red_action_success.append(red_action_success)
            full_blue_actions.append(blue_action)
            full_rewards.append(rew)

            if args.visualize:
                visualize(net, episode, step, now_str, history, killchain)

            total_reward += rew
            steps += 1
        steps = 0
        obs = envs.reset()
        episode_rewards.append(total_reward)
        total_reward = 0

    actions_df = pd.DataFrame(
        {
            "episode": full_episodes,
            "step": full_steps,
            "red_action_success": full_red_action_success,
            "red_action_type": full_red_action_type,
            "red_action_src": full_red_action_src,
            "red_action_dest": full_red_action_dest,
            "blue_action": full_blue_actions,
            "reward": full_rewards,
        }
    )

    actions_df.to_csv(log_file)

    total_time = time.time() - start_time
    print("charts/SPS", int(2000 / total_time))
    total_reward = sum(episode_rewards)
    episodes = len(episode_rewards)
    if episodes == 0:
        print(f"Mean Episodic Reward: {float(total_reward)}")
    else:
        print(f"Mean Episodic Reward: {float(total_reward) / episodes}")

    print(f"Total Time Elapsed: {total_time}")


if __name__ == "__main__":
    evaluate_cyberwheel()