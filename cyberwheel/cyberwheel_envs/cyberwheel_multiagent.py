from pettingzoo import ParallelEnv
from network.network_base import Network
from .cyberwheel import Cyberwheel
from redagents.multiagent.simple_red import SimpleRedAgent
from blueagents.simple_blue import SimpleBlueAgent
from gymnasium.spaces import Discrete, MultiBinary
import functools
from copy import copy


class MultiagentCyberwheel(ParallelEnv, Cyberwheel):

    metadata = {"render.modes": ["human"]}

    def __init__(self, **kwargs):
        # super(MultiagentCyberwheel, self).__init__()
        # use config_file_path kwarg if supplied, otherwise use default
        config_file_path = kwargs.get("config_file_path", "network/example_config.yaml")
        super().__init__(config_file_path=config_file_path)

        self.max_steps = 100

        ## self.network is now instantiated in the Cyberwheel class
        # self.network = Network.create_network_from_yaml('network/config.yaml')
        # self.network.draw()

        self.possible_agents = ["red_agent", "blue_agent"]
        self.agent_name_to_agent = {}

        self.agent_name_to_agent["red_agent"] = SimpleRedAgent(self.network)
        self.agent_name_to_agent["blue_agent"] = SimpleBlueAgent(self.network)

        # Initialize observation_spaces and action_spaces dictionaries
        self.observation_spaces = {
            "red_agent": self.observation_space("red_agent"),
            "blue_agent": self.observation_space("blue_agent"),
        }
        self.action_spaces = {
            "red_agent": self.action_space("red_agent"),
            "blue_agent": self.action_space("blue_agent"),
        }

        self.timestep = 0

    # def _get_obs(self, agent):
    #    # this should be specific to each agent...
    #    return self.network.generate_observation_vector()

    def step(self, actions):
        rewards = {}
        dones = {}
        infos = {}

        for agent, action in actions.items():

            rewards[agent], dones[agent] = self.agent_name_to_agent[agent].act(action)

            infos[agent] = {}

        terminations = {a: False for a in self.agents}

        if dones["red_agent"]:
            terminations = {a: True for a in self.agents}

        # Check truncation conditions (overwrites termination conditions)
        truncations = {a: False for a in self.agents}
        if self.timestep > self.max_steps:
            truncations = {"red_agent": True, "blue_agent": True}

        self.timestep += 1

        observations = {a: self._get_obs(a) for a in self.agents}

        if any(terminations.values()) or all(truncations.values()):
            self.agents = []

        return observations, rewards, terminations, truncations, infos

    def reset(self, seed=None, options=None):
        self.agents = copy(self.possible_agents)
        self.timestep = 0
        self.network = Network.create_network_from_yaml(self.config_file_path)
        self.agent_name_to_agent["red_agent"] = SimpleRedAgent(self.network)
        self.agent_name_to_agent["blue_agent"] = SimpleBlueAgent(self.network)

        observations = {a: self._get_obs(a) for a in self.agents}

        # Get dummy infos. Necessary for proper parallel_to_aec conversion
        infos = {a: {} for a in self.agents}

        return observations, infos

    def render(self, mode="human"):
        pass

    def close(self):
        pass

    # Observation space should be defined here.
    # lru_cache allows observation and action spaces to be memoized, reducing clock cycles required to get each agent's space.
    # If your spaces change over time, remove this line (disable caching).
    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent):
        # gymnasium spaces are defined and documented here: https://gymnasium.farama.org/api/spaces/
        return MultiBinary(self.network.get_action_space_size() - 1)

    # Action space should be defined here.
    # If your spaces change over time, remove this line (disable caching).
    @functools.lru_cache(maxsize=None)
    def action_space(self, agent):
        return Discrete(self.network.get_action_space_size())
