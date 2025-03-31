import gymnasium as gym
import numpy as np
import importlib

from typing import Iterable, Any 
from gymnasium import spaces

from cyberwheel.cyberwheel_envs.cyberwheel import Cyberwheel
from cyberwheel.blue_agents import RLBlueAgent, InactiveBlueAgent
from cyberwheel.network.network_base import Network
from cyberwheel.red_agents import RLRedAgent, ARTAgent, ARTCampaign
from cyberwheel.utils import YAMLConfig, HybridSetList
from cyberwheel.utils.set_seed import set_seed

import pandas as pd


class CyberwheelRL(gym.Env, Cyberwheel):
    metadata = {"render.modes": ["human"]}

    def __init__(
        self,
        args: YAMLConfig,
        network: Network = None,
        evaluation: bool = False
    ):
        """
        The CyberwheelRL class is used to define the Cyberwheel environment. It allows you to use a YAML
        file to configure the actions, rewards, and logic of the blue agent. Given various configurations, it
        will initiate the environment with the red agent, blue agent, reward functions, and network state.
        Important member variables:

        * `args`: required
            - YAMLConfig instance defining the environment state.

        * `network`: optional
            - The Network object to use throughout the environment. This prevents longer start-up times when training with multiple environments.
            - If not passed, it will build the network with the config file passed.
            - Default: None
        """
        super().__init__(args, network=network)

        reward_function = args.reward_function
        rfm = importlib.import_module("cyberwheel.reward")

        self.reward_calculator = getattr(rfm, reward_function)(
            self.red_agent.get_reward_map(), 
            self.blue_agent.get_reward_map(),
            self.args.valid_targets,
            self.network)

        self.evaluation = evaluation
        self.total = 0
    
    def initialize_agents(self) -> None:
        args = self.args
        if args.train_red:
            self.red_agent = RLRedAgent(self.network, args)
            self.blue_agent = InactiveBlueAgent()
            self.rl_agent = self.red_agent
            self.static_agent = self.blue_agent

            self.observation_space = spaces.MultiDiscrete(np.array([3] * self.red_agent.observation.max_size))

            self.max_action_space_size = len(self.network.hosts) * self.red_agent.action_space.num_actions * 2
            self.action_space = self.red_agent.action_space.create_action_space(self.max_action_space_size)
            self.reward_sign = -1
        else:
            self.red_agent = ARTCampaign(self.network, args) if args.campaign else ARTAgent(self.network, args)
            self.blue_agent = RLBlueAgent(self.network, args)
            self.rl_agent = self.blue_agent
            self.static_agent = self.red_agent

            self.observation_space = spaces.MultiBinary(self.blue_agent.observation.shape)

            self.max_action_space_size = len(self.network.subnets) * 2
            self.action_space = self.blue_agent.create_action_space(self.max_action_space_size)
            self.reward_sign = 1

    def step(self, action: int) -> tuple[Iterable, int | float, bool, bool, dict[str, Any]]:
        """
        Steps through environment.
        1. Blue agent runs action
        2. Red agent runs action
        3. Calculate reward based on red/blue actions and network state
        4. Get obs from Red or Blue Observation
        5. Return obs and related metadata
        """
        blue_agent_result = self.blue_agent.act(action)

        red_agent_result = self.red_agent.act(action)

        obs_vec = self.red_agent.get_observation_space() if self.args.train_red else self.blue_agent.get_observation_space(red_agent_result)

        reward = self.reward_sign * self.reward_calculator.calculate_reward(
            red_agent_result.action.get_name(),
            blue_agent_result.name,
            red_agent_result.success,
            blue_agent_result.success,
            red_agent_result.target_host,
            blue_id=blue_agent_result.id,
            blue_recurring=blue_agent_result.recurring
        )

        self.total += reward

        done = self.current_step >= self.max_steps

        self.current_step += 1
        info = {}
        if self.evaluation:
            info = {
                "red_action": red_agent_result.action.get_name(),
                "red_action_src": red_agent_result.src_host.name,
                "red_action_dst": red_agent_result.target_host.name,
                "red_action_success": red_agent_result.success,
                "blue_action": blue_agent_result.name,
                "blue_action_id": blue_agent_result.id,
                "blue_action_target": blue_agent_result.target,
                "killchain": self.red_agent.killchain,
                "network": self.network,
                "history": self.red_agent.history,
                "commands": red_agent_result.action_results.metadata
                    .get(red_agent_result.target_host.name, {})
                    .get("commands", [])
            }

        return obs_vec, reward, done, False, info

    def reset(self, seed=None, options=None) -> tuple[Iterable, dict]:
        if seed is not None:
            set_seed(seed)
        self.current_step = 0
        self.network.reset()
        self.red_agent.reset()
        self.blue_agent.reset()
        self.reward_calculator.reset()
        self.total = 0
        if self.args.train_red:
            return self.red_agent.observation.obs_vec, {}
        else:
            return self.blue_agent.observation.reset(), {} # TODO
        
    def close(self) -> None:
        pass

    @property
    def rl_agent_action_space_size(self):
        return self.rl_agent.action_space._action_space_size
