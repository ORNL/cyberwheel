import time
import inspect
import sys
from tqdm import tqdm
import argparse

from typing import List

import gym
import wandb
import datetime
import torch
import torch.nn as nn
import numpy as np
import pandas as pd

from torch.distributions.categorical import Categorical
from stable_baselines3.common.monitor import Monitor
from pprint import pprint
import yaml

from cyberwheel.blue_agents.decoy_blue import DecoyBlueAgent
from cyberwheel.red_agents.killchain_agent import KillChainAgent
from cyberwheel.cyberwheel_envs.cyberwheel_decoyagent import *


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


def create_cyberwheel_env(
    network_config: str, decoy_host_file: str, host_def_file: str
):
    """Create a Cyberwheel environment"""
    env = DecoyAgentCyberwheel(
        network_config=network_config,
        decoy_host_file=decoy_host_file,
        host_def_file=host_def_file,
    )
    return env


def make_env(env_id: str, rank: int, seed: int = 0):
    """
    Utility function for multiprocessed env.

    :param env_id: the environment ID
    :param num_env: the number of environments you wish to have in subprocesses
    :param seed: the inital seed for RNG
    :param rank: index of the subprocess
    """

    def _init():
        # env = SingleAgentCyberwheel(50,1,1)  # Create an instance of the Cyberwheel environment
        env = DecoyAgentCyberwheel()
        env.reset(seed=seed + rank)  # Reset the environment with a specific seed
        log_file = f"monitor_vecenv_logs/{env_id}_{rank}"
        env = Monitor(env, log_file, allow_early_resets=True)
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
        "--config",
        help="Network config to evaluate agent against",
        default="example_config.yaml",
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
    args = parser.parse_args()

    print(args)

    bool_run = args.run != None  # true if run given, false if run not given

    if args.download_model != bool_run:
        parser.error("--run and --download-model flag required when downloading model")

    return args


if __name__ == "__main__":
    args = parse_args()
    device = torch.device("cpu")  # "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device {device}")

    config = args.config

    env_funcs = [make_env(1, i) for i in range(1)]
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
        now_str = f"{experiment_name}_evaluate_{args.config}_killchainagent"
    log_file = f"action_logs/{now_str}.csv"

    actions_df = pd.DataFrame()
    full_episodes = []
    full_steps = []
    full_red_actions = []
    full_blue_actions = []
    full_rewards = []

    for episode in tqdm(range(20)):
        blue_actions = []
        red_actions = []
        for step in range(100):
            if step == 0:
                obs = obs[0]
            obs = torch.Tensor(obs).to(device)
            action, logprob, _, value = agent.get_action_and_value(obs)
            # action = envs.action_space.sample()
            all_action = None
            blue_action = None
            red_action = None

            # print(f"\n\n{action}\n\n")
            obs, rew, done, _, info = envs.step(action.cpu().numpy())
            # obs = obs[0]
            rew = rew[0]
            done = done[0]
            # info = info[0]
            all_action = info["action"][0]
            print(all_action)
            blue_action = all_action["Blue"]
            red_action = all_action["Red"]

            full_episodes.append(episode)
            full_steps.append(step)
            full_red_actions.append(red_action)
            full_blue_actions.append(blue_action)
            full_rewards.append(rew)

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
            "red_action": full_red_actions,
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

    print(actions_df)

    # scenario_path = f"CybORG/CybORG/Shared/Scenarios/{scenario}.yaml"

    # read_actions_csv = pd.read_csv(log_file)
    # action_table = wandb.Table(dataframe=read_actions_csv)
    # action_table_artifact = wandb.Artifact(
    #    "action_artifact",
    #    type="dataset"
    #    )
    # table_name = "test_action_table"
    # action_table_artifact.add(action_table, table_name)
    # action_table_artifact.add_file(log_file)

    # run_name = args.run
    # run = wandb.init(project="Cage", name=experiment_name)
    # run.log({"actions": action_table})
    # run.log_artifact(action_table_artifact)
    # run.finish()

    # if args.visualize:
    #    frames, alt_rewards = visualize(scenario_path, log_file)
    #    labels = ["Exploit", "Escalate", "Impact"]
    #    for i in range(len(alt_rewards)):
    #        print(f"# of successful {labels[i]} actions per episode: {alt_rewards[i]}")
    #    print(f"View Graph At: http://127.0.0.1:8050/graphs/{now_str}")
