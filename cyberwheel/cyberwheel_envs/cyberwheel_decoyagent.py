from importlib.resources import files
import gymnasium as gym
from gymnasium import spaces
from typing import Dict, Iterable, List
import yaml

from .cyberwheel import Cyberwheel
from blue_agents.decoy_blue import DecoyBlueAgent
from blue_agents.observation import HistoryObservation
from detectors.alert import Alert
from detectors.detector import CoinFlipDetector
from network.network_base import Network
from network.host import Host
from red_agents.killchain_agent import KillChainAgent
from reward.reward import Reward
import random     


def host_to_index_mapping(network: Network) -> Dict[Host, int]:
    """
    This will help with constructing the obs_vec.
    It will need to be called and save during __init__()
    because deploying decoy hosts may affect the order of
    the list network.get_non_decoy_hosts() returns.
    This might not be the case, but this will ensure the
    original indices are preserved.
    """
    mapping: Dict[Host, int] = {}
    i = 0
    for host in network.get_nondecoy_hosts():
        mapping[host.name] = i
        i += 1
    return mapping

def decoy_alerted(alerts: List[Alert]) -> bool:
    for alert in alerts:
        for dst_host in alert.dst_hosts:
            if dst_host.decoy:
                return True
    return False

class DecoyAgentCyberwheel(gym.Env, Cyberwheel):
    metadata = {"render.modes": ["human"]}

    def __init__(
        self,
        network_config="example_config.yaml",
        decoy_host_file="decoy_hosts.yaml",
        host_def_file="host_definitions.yaml",
        **kwargs,
    ):
        network_conf_file = files("cyberwheel.network").joinpath(network_config)
        decoy_conf_file = files("cyberwheel.resources.metadata").joinpath(
            decoy_host_file
        )
        host_conf_file = files("cyberwheel.resources.metadata").joinpath(host_def_file)

        super().__init__(config_file_path=network_conf_file)
        self.total = 0
        self.max_steps = 50
        self.current_step = 0

        # Create action space. Decoy action for each decoy type for each subnet.
        # Length = num_decoy_host_types * num_subnets
        with open(decoy_conf_file, "r") as f:
            self.decoy_info = yaml.safe_load(f)

        with open(host_conf_file, "r") as f:
            self.host_defs = yaml.safe_load(f)["host_types"]

        self.decoy_types = list(self.decoy_info.keys())

        num_decoys = len(self.decoy_types)
        num_subnets = len(self.network.get_all_subnets())
        num_hosts = len(self.network.get_hosts())
        """
        There needs to be an action for deploying each host on each subnet.
        action_space[0] == which decoy host type to deploy
        action_space[1] == which subnet to deploy it on
        """

        self.action_space = spaces.Discrete(2 * num_decoys * num_subnets + 1)
        self.observation_space = spaces.Box(0, 1, shape=(2 * num_hosts,))
        self.alert_converter = HistoryObservation(
            self.observation_space.shape, host_to_index_mapping(self.network)
        )

        self.red_agent = KillChainAgent(
            self.network.get_random_user_host(), network=self.network
        )
        self.blue_agent = DecoyBlueAgent(self.network, self.decoy_info, self.host_defs)
        self.detector = CoinFlipDetector()
        

        self.reward_calculator = Reward(self.red_agent.get_reward_map(), self.blue_agent.get_reward_map(), r=(2,5), scaling_factor=10)

    def step(self, action):
        blue_action_name, rec_id, successful = self.blue_agent.act(action)
        self.reward_calculator.handle_blue_action_output(blue_action_name, rec_id)
        
        red_action_name = self.red_agent.act().get_name()  # red_action includes action, and target of action
        action_metadata = self.red_agent.history.history[-1]

        red_action_type, red_action_src, red_action_dst = action_metadata.action

        red_action_success = action_metadata.success

        red_action_str = "Success - " if red_action_success else "Failed - "

        red_action_str += f"{red_action_type.__name__} from {red_action_src.name} to {red_action_dst.name}"
        red_action_result = self.red_agent.history.recent_history() # red action results
        
        alerts = self.detector.obs(red_action_result.detector_alert)
        obs_vec = self._get_obs(alerts)

        # print(blue_action_name, red_action_name)
        x = decoy_alerted(alerts)
        print(x, end=" ")
        reward = self.reward_calculator.calculate_reward(red_action_name, blue_action_name, successful, x)
        print(reward)
        self.total += reward

        if self.current_step >= self.max_steps:  # Maximal number of steps
            done = True
        # elif red_action_name == "impact" and not x:
        #     done = True
        # elif x:
        #     print("ACCESSED DECOY")
        #     done = True
        else:
            done = False
        self.current_step += 1

        return obs_vec, reward, done, False, {"action": {"Blue": blue_action_name, "Red": red_action_str}}

    def _get_obs(self, alerts: List[Alert])-> Iterable:
        return self.alert_converter.create_obs_vector(alerts)

    def _reset_obs(self) -> Iterable:
        return self.alert_converter.reset_obs_vector()
    
    def flatten_red_alert(red_alert):
        pass

    def reset(self, seed=None, options=None):
        print(f"Reward: {self.total}")
        self.total = 0 
        self.current_step = 0
        self.network = Network.create_network_from_yaml(self.config_file_path)
        self.red_agent = KillChainAgent(
            self.network.get_random_user_host(), network=self.network
        )
        self.blue_agent = DecoyBlueAgent(self.network, self.decoy_info, self.host_defs)

        self.alert_converter = HistoryObservation(
            self.observation_space.shape, host_to_index_mapping(self.network)
        )
        self.detector = CoinFlipDetector()
        self.reward_calculator.reset()
        return self._reset_obs(), {} 

    # can implement existing GUI here???
    def render(self, mode="human"):
        pass

    # if you open any other processes close them here
    def close(self):
        pass

