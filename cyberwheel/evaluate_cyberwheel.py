import time
import argparse
import gym
import wandb
import torch
import sys
import torch.nn as nn
import numpy as np
import pandas as pd

from copy import deepcopy
from importlib.resources import files
from tqdm import tqdm
from torch.distributions.categorical import Categorical

from cyberwheel.cyberwheel_envs.cyberwheel_dynamic import DynamicCyberwheel
from cyberwheel.red_agents import ARTAgent
from cyberwheel.red_agents.strategies import DFSImpact, ServerDowntime
from cyberwheel.network.network_base import Network
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
    max_decoys=3,
    blue_reward_scaling=10.0,
    reward_function="default",
    red_agent="art_agent",
    blue_config="dynamic_blue_agent.yaml",
    num_steps=50,
    network=None,
    service_mapping={},
    red_strategy=ServerDowntime
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
            blue_config=blue_config,
            num_steps=num_steps,
            network=network,
            service_mapping=service_mapping,
            evaluation=True,
            red_strategy=red_strategy
        )
        env.reset(seed=seed + rank)  # Reset the environment with a specific seed
        env = gym.wrappers.RecordEpisodeStatistics(
            env
        )  # This tracks the rewards of the environment that it wraps. Used for logging
        return env

    return _init


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--download-model",
        help="Download agent model from WandB. If present, requires --run, --wandb-entity, --wandb-project-name flags.",
        action="store_true",
    )
    parser.add_argument(
        "--red-agent",
        help="Red agent to evaluate against",
        default="art_agent",
    )
    parser.add_argument(
        "--red-strategy",
        help="Red agent strategy to evaluate against. Current options: server_downtime (default) | dfs_impact",
        default="server_downtime",
    )
    parser.add_argument(
        "--blue-config", 
        help="Input the blue agent config filename", 
        type=str, 
        default='dynamic_blue_agent.yaml'
    )
    parser.add_argument(
        "--run", help="Run ID from WandB for pretrained blue agent to use. Required when downloading model from W&B", required = "--download-model" in sys.argv
    )
    parser.add_argument(
        "--experiment",
        help="Experiment name for storing/retrieving agent model",
        default="temp_model",
    )
    parser.add_argument(
        "--visualize",
        help="Stores graphs of network state at each step/episode. Can be viewed in dash server.",
        action="store_true",
    )
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
        default="15-host-network.yaml",
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
        default="host_defs_services.yaml",
    )

    parser.add_argument(
        "--detector-config",
        help="Path to detector config file",
        type=str,
        default="detector_handler.yaml",
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
        default=10.0,
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
        default=100,
    )

    parser.add_argument(
        "--num-episodes", help="Number of episodes to evaluate", type=int, default=10
    )

    parser.add_argument(
        "--wandb-entity", help="Username where W&B model is stored. Required when downloading model from W&B", type=str, required = "--download-model" in sys.argv
    )

    parser.add_argument(
        "--wandb-project-name", help="Project name where W&B model is stored. Required when downloading model from W&B", type=str, required = "--download-model" in sys.argv
    )

    return parser.parse_args()

def evaluate_cyberwheel():
    """
    This function evaluates a trained model in the Cyberwheel environment.
    At each step of the evaluation, it saves metadata for logging actions.
    If visualizing, it will also save pickled networkx graphs to the graphs/
    directory, allowing the dash server to load them.
    """
    args = parse_args()
    device = torch.device("cpu")
    print(f"Using device {device}")

    # Set up network and Host-Technique mapping outside of environment.
    # This keeps the time-consuming processes from running for each environment.
    network_config = files("cyberwheel.resources.configs.network").joinpath(args.network_config)
    network = Network.create_network_from_yaml(network_config)

    service_mapping = {}
    if args.red_agent == "art_agent":
        service_mapping = ARTAgent.get_service_map(network)
    if args.red_strategy == "dfs_impact":
        args.red_strategy = DFSImpact
    else:
        args.red_strategy = ServerDowntime

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
            red_agent=args.red_agent,
            blue_config=args.blue_config,
            num_steps=args.num_steps,
            network=deepcopy(network),
            service_mapping=service_mapping,
            red_strategy=args.red_strategy
        )
        for i in range(1)
    ]
    envs = gym.vector.SyncVectorEnv(env_funcs)

    agent = Agent(envs).to(device)

    experiment_name = args.experiment
    
    # If download from W&B, use API to get run data.
    if args.download_model:
        api = wandb.Api()
        run = api.run(f"{args.wandb_entity}/{args.wandb_project_name}/runs/{args.run}")
        model = run.file("agent.pt")
        model.download(files("cyberwheel.models").joinpath(experiment_name), exist_ok=True)

    # Load model from models/ directory
    agent.load_state_dict(
        torch.load(files(f"cyberwheel.models.{experiment_name}").joinpath("agent.pt"), map_location=device)
    )
    agent.eval()

    print("Resetting the environment...")
    start_time = time.time()

    episode_rewards = []
    total_reward = 0
    steps = 0
    obs = envs.reset()

    print("Playing environment...")

    # Set up dirpath to store action logs CSV
    if args.graph_name != None:
        now_str = args.graph_name
    else:
        now_str = f"{experiment_name}_evaluate_{args.network_config.split('.')[0]}_{args.red_agent}_{args.red_strategy.__name__}_{args.min_decoys}-{args.max_decoys}_scaling{int(args.reward_scaling)}_{args.reward_function}reward"
    log_file = files("cyberwheel.action_logs").joinpath(f"{now_str}.csv")

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
        for step in range(args.num_steps):
            if step == 0:
                obs = obs[0]
            obs = torch.Tensor(obs).to(device)
            action, _, _, _ = agent.get_action_and_value(obs)

            obs, rew, done, _, info = envs.step(action.cpu().numpy())
            rew = rew[0]
            done = done[0]

            if "final_observation" in list(info.keys()):
                blue_action = info["final_info"][0]["blue_action"]
                red_action_type = info["final_info"][0]["red_action"]
                red_action_src = info["final_info"][0]["red_action_src"]
                red_action_dest = info["final_info"][0]["red_action_dst"]
                red_action_success = info["final_info"][0]["red_action_success"]
                net = info["final_info"][0]["network"]
                history = info["final_info"][0]["history"]
                killchain = info["final_info"][0]["killchain"]
            else:
                blue_action = info["blue_action"][0]
                red_action_type = info["red_action"][0]
                red_action_src = info["red_action_src"][0]
                red_action_dest = info["red_action_dst"][0]
                red_action_success = info["red_action_success"][0]
                net = info["network"][0]
                history = info["history"][0]
                killchain = info["killchain"][0]

            full_episodes.append(episode)
            full_steps.append(step)
            full_red_action_type.append(red_action_type)
            full_red_action_src.append(red_action_src)
            full_red_action_dest.append(red_action_dest)
            full_red_action_success.append(red_action_success)
            full_blue_actions.append(blue_action)
            full_rewards.append(rew)

            # If generating graphs for dash server view
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

    # Save action metadata to CSV in action_logs/
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
