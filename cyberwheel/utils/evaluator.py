
import gymnasium as gym
import time
import importlib
import pandas as pd
import torch
import wandb
import os
import random

from importlib.resources import files
from tqdm import tqdm

from cyberwheel.network.network_base import Network
from cyberwheel.utils import RLAgent, get_service_map
from cyberwheel.utils.visualize import visualize
from cyberwheel.utils.set_seed import set_seed


def get_action_mask(action_space_size, action_masks):
    for i in range(len(action_masks)):
        if i < action_space_size:
            action_masks[i] = True
        else:
            action_masks[i] = False
    return action_masks


class Evaluator:
    def __init__(self, args):
        self.args = args
        m = importlib.import_module("cyberwheel.cyberwheel_envs")
        self.env = getattr(m, args.environment)
        self.deterministic = os.getenv("CYBERWHEEL_DETERMINISTIC", "False").lower() in ('true', '1', 't')
        self.args.deterministic = self.deterministic
        self.seed = 0

    def make_env(self, rank, network: Network):
        """
        Utility function for multiprocessed env.

        :param env_id: the environment ID
        :param num_env: the number of environments you wish to have in subprocesses
        :param seed: the inital seed for RNG
        :param rank: index of the subprocess
        """

        def _init():
            env = self.env(self.args, network=network)
            env.evaluation = True

            self.max_action_space_size = env.max_action_space_size
            env.reset(
                seed=self.args.seed + rank
            )  # Reset the environment with a specific seed
            env = gym.wrappers.RecordEpisodeStatistics(
                env
            )  # This tracks the rewards of the environment that it wraps. Used for logging
            return env

        return _init

    def configure_evaluation(self):
        if self.deterministic:
            set_seed(self.seed)
            torch.backends.cudnn.deterministic = True
        else:
            set_seed(random.randint(0, 999999999))
            torch.backends.cudnn.deterministic = False

        self.device = torch.device("cpu")
        print(f"Using device {self.device}")

        # Set up network and Host-Technique mapping outside of environment.
        # This keeps the time-consuming processes from running for each environment.
        network_config = files("cyberwheel.data.configs.network").joinpath(
            self.args.network_config
        )
        network = Network.create_network_from_yaml(network_config)

        self.args.service_mapping = get_service_map(network)
        env_funcs = [self.make_env(i, network=network) for i in range(1)]
        self.envs = gym.vector.SyncVectorEnv(env_funcs)

        self.agent = RLAgent(self.envs).to(self.device)

        experiment_name = self.args.experiment_name

        agent_filename = f"{self.args.checkpoint}.pt"

        # If download from W&B, use API to get run data.
        if self.args.download_model:
            api = wandb.Api()
            run = api.run(
                f"{self.args.wandb_entity}/{self.args.wandb_project_name}/runs/{self.args.run}"
            )
            model = run.file(agent_filename)
            model.download(
                files("cyberwheel.data.models").joinpath(experiment_name), exist_ok=True
            )

        # Load model from models/ directory
        self.agent.load_state_dict(
            torch.load(
                files(f"cyberwheel.data.models.{experiment_name}").joinpath(agent_filename),
                map_location=self.device,
            )
        )
        self.agent.eval()

        print("Resetting the environment...")

        self.episode_rewards = []
        self.total_reward = 0
        self.steps = 0
        self.obs = self.envs.reset()

        print("Playing environment...")

        # Set up dirpath to store action logs CSV
        if self.args.graph_name != None:
            self.now_str = self.args.graph_name
        else:
            self.now_str = f"{experiment_name}_evaluate_{self.args.network_config.split('.')[0]}_{self.args.red_agent}_{self.args.reward_function}reward"
        self.log_file = files("cyberwheel.data.action_logs").joinpath(f"{self.now_str}.csv")

        self.actions_df = pd.DataFrame()
        self.full_episodes = []
        self.full_steps = []
        self.full_red_action_type = []
        self.full_red_action_src = []
        self.full_red_action_dest = []
        self.full_red_action_success = []
        self.full_blue_actions = []
        self.full_blue_action_ids = []
        self.full_blue_action_targets = []
        self.full_rewards = []

        self.max_action_space_size = self.envs.envs[0].unwrapped.max_action_space_size
        self.action_mask = [False] * self.max_action_space_size

    def evaluate(self):
        self.start_time = time.time()
        for episode in tqdm(range(self.args.num_episodes)):
            for step in range(self.args.num_steps):
                if self.deterministic:
                    set_seed(self.seed)
                self.seed += 1
                if step == 0:
                    self.obs = self.obs[0]

                self.obs = torch.Tensor(self.obs).to(self.device)
                action_space_size = self.envs.envs[
                    0
                ].unwrapped.rl_agent.action_space._action_space_size

                self.action_mask = get_action_mask(action_space_size, self.action_mask)

                self.action_mask = torch.asarray(self.action_mask)

                action, _, _, _ = self.agent.get_action_and_value(
                    self.obs, action_mask=self.action_mask
                )

                self.obs, rew, done, _, info = self.envs.step(action.cpu().numpy())
                rew = rew[0]
                done = done[0]
                if "final_observation" in list(info.keys()):
                    blue_action = info["final_info"][0]["blue_action"]
                    blue_action_id = info["final_info"][0]["blue_action_id"]
                    blue_action_target = info["final_info"][0]["blue_action_target"]
                    red_action_type = info["final_info"][0]["red_action"]
                    red_action_src = info["final_info"][0]["red_action_src"]
                    red_action_dest = info["final_info"][0]["red_action_dst"]
                    red_action_success = info["final_info"][0]["red_action_success"]
                    net = info["final_info"][0]["network"]
                    commands = info["final_info"][0]["commands"]
                    history = info["final_info"][0]["history"]
                else:
                    blue_action = info["blue_action"][0]
                    blue_action_id = info["blue_action_id"][0]
                    blue_action_target = info["blue_action_target"][0]
                    red_action_type = info["red_action"][0]
                    red_action_src = info["red_action_src"][0]
                    red_action_dest = info["red_action_dst"][0]
                    red_action_success = info["red_action_success"][0]
                    net = info["network"][0]
                    commands = info["commands"][0]
                    history = info["history"][0]

                self.full_episodes.append(episode)
                self.full_steps.append(step)
                self.full_red_action_type.append(red_action_type)
                self.full_red_action_src.append(red_action_src)
                self.full_red_action_dest.append(red_action_dest)
                self.full_red_action_success.append(red_action_success)
                self.full_blue_actions.append(blue_action)
                self.full_blue_action_ids.append(blue_action_id)
                self.full_blue_action_targets.append(blue_action_target)
                self.full_rewards.append(rew)

                # If generating graphs for dash server view
                #print(self.args.visualize)
                if self.args.visualize:
                    host_info = self.envs.envs[0].unwrapped.red_agent.observation.obs if self.args.train_red else history.hosts
                    step_info = {"source_host": red_action_src, "target_host": red_action_dest, "red_action": red_action_type, "commands": commands, "network": net, "host_info": host_info, "commands": commands}
                    visualize(episode, step, self.args.graph_name, step_info)
                    pass

                self.total_reward += rew
                self.steps += 1
            self.steps = 0
            self.obs = self.envs.reset()
            self.episode_rewards.append(self.total_reward)
            self.total_reward = 0

        self.actions_df = pd.DataFrame(
            {
                "episode": self.full_episodes,
                "step": self.full_steps,
                "red_action_success": self.full_red_action_success,
                "red_action_type": self.full_red_action_type,
                "red_action_src": self.full_red_action_src,
                "red_action_dest": self.full_red_action_dest,
                "blue_action": self.full_blue_actions,
                "blue_action_id": self.full_blue_action_ids,
                "blue_action_target": self.full_blue_action_targets,
                "reward": self.full_rewards,
            }
        )

        # Save action metadata to CSV in action_logs
        self.actions_df.to_csv(self.log_file)

        self.total_time = time.time() - self.start_time
        print("charts/SPS", int(2000 / self.total_time))
        self.total_reward = sum(self.episode_rewards)
        self.episodes = len(self.episode_rewards)
        if self.episodes == 0:
            print(f"Mean Episodic Reward: {float(self.total_reward)}")
        else:
            print(f"Mean Episodic Reward: {float(self.total_reward) / self.episodes}")

        print(f"Total Time Elapsed: {self.total_time}")
