import copy
from importlib.resources import files
import gymnasium as gym
from gymnasium import spaces
from typing import Dict, Iterable, List
import yaml

from .cyberwheel import Cyberwheel
from blue_agents.isolate_blue import IsolateBlueAgent
from blue_agents.observation import HistoryObservation
from detectors.alert import Alert
# from detectors.detector import DecoyDetector, CoinFlipDetector
from detectors.detectors.isolate_detector import IsolateDetector
from detectors.detectors.probability_detector import ProbabilityDetector
from detectors.detectors.example_detectors import DecoyDetector
from network.network_base import Network
from network.host import Host
from red_agents import KillChainAgent, RecurringImpactAgent
from reward.reward import StepDetectedReward
from reward.isolate_reward import IsolateReward
from copy import deepcopy



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
        # for dst_host in alert.dst_hosts:
        #     if dst_host.decoy:
        #         return True
        if alert.src_host.disconnected:
            return True
    return False

class IsolateAgentCyberwheel(gym.Env, Cyberwheel):
    metadata = {"render.modes": ["human"]}

    def __init__(
        self,
        network_config="example_config.yaml",
        decoy_host_file="decoy_hosts.yaml",
        host_def_file="host_definitions.yaml",
        detector_config="",
        min_decoys=0,
        max_decoys=1,
        blue_reward_scaling=10,
        reward_function="default",
        red_agent="killchain_agent",
        **kwargs,
    ):
        network_conf_file = files("cyberwheel.network").joinpath(network_config)
        decoy_conf_file = files("cyberwheel.resources.metadata").joinpath(
            decoy_host_file
        )
        host_conf_file = files("cyberwheel.resources.metadata").joinpath(host_def_file)
        super().__init__(config_file_path=network_conf_file)
        self.total = 0
        self.max_steps = 100
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
        self.max_decoys = 4
        """
        Possible actions are deploying a type of decoy on a subnet
        and isolating one of the deployed decoys. There's only a certain
        number of decoys that can be deployed which is defined by self.max_decoys
        """
        self.action_space = spaces.Discrete(num_decoys * num_subnets + self.max_decoys)
        self.observation_space = spaces.Box(0, 1, shape=(2 * num_hosts,))
        self.alert_converter = HistoryObservation(
            self.observation_space.shape, host_to_index_mapping(self.network)
        )
        self.red_agent_choice = red_agent

        if self.red_agent_choice == "recurring_impact":
            self.red_agent = RecurringImpactAgent(
                self.network.get_random_user_host(), network=self.network
            )
        else:
            self.red_agent = KillChainAgent(
                self.network.get_random_user_host(), network=self.network
            )

        

        self.blue_agent = IsolateBlueAgent(self.network, self.decoy_info, self.host_defs, self.max_decoys)
        
        detector_conf_file = files("cyberwheel.resources.configs").joinpath(detector_config)
        self.detector = ProbabilityDetector(detector_conf_file)
        # self.detector = IsolateDetector()
        # self.detector2 = DecoyDetector()

        self.reward_function = reward_function

        if reward_function == "step_detected":
            self.reward_calculator = StepDetectedReward(
                blue_rewards=self.blue_agent.get_reward_map(),
                r=(min_decoys, max_decoys),
                scaling_factor=blue_reward_scaling,
                max_steps=self.max_steps,
            )
        else:
            self.reward_calculator = IsolateReward(
                self.red_agent.get_reward_map(),
                # scaling_factor=blue_reward_scaling,
            )


    def step(self, action):
        # print(action)
        blue_action_name, rec_id, successful = self.blue_agent.act(action)
        # print(blue_action_name, rec_id, successful)
        # self.reward_calculator.handle_blue_action_output(blue_action_name, rec_id)
        red_action_name = (
            self.red_agent.act().get_name()
        )  # red_action includes action, and target of action
        
        action_metadata = self.red_agent.history.history[-1]

        red_action_type, red_action_src, red_action_dst = action_metadata.action

        red_action_success = action_metadata.success

        red_action_str = "Success - " if red_action_success else "Failed - "

        red_action_str += f"{red_action_type.__name__} from {red_action_src.name} to {red_action_dst.name}"
        red_action_result = (
            self.red_agent.history.recent_history()
        )  # red action results
        alerts = self.detector.obs(red_action_result.detector_alert) #+ self.detector2.obs(red_action_result.detector_alert)   
        obs_vec = self._get_obs(alerts)
        alerted = decoy_alerted(alerts)
        if self.reward_function == "step_detected":
            reward = self.reward_calculator.calculate_reward(
                blue_action_name, successful, alerted, self.current_step
            )
        else:
            reward = self.reward_calculator.calculate_reward(
                red_action_name, successful, alerted
            )

        self.total += reward

        if self.current_step >= self.max_steps:  # Maximal number of steps
            done = True
        else:
            done = False
        self.current_step += 1
        # print(len(self.network.get_hosts()))
        # print(red_action_str)
        # print(blue_action_name)
        # print(reward)
        return (
            obs_vec,
            reward,
            done,
            False,
            {
                "action": {"Blue": blue_action_name, "Red": red_action_str},
                # "network": self.blue_agent.network,
                # "history": self.red_agent.history,
                # "killchain": self.red_agent.killchain,
            },

        )

    def _get_obs(self, alerts: List[Alert]) -> Iterable:
        return self.alert_converter.create_obs_vector(alerts)

    def _reset_obs(self) -> Iterable:
        return self.alert_converter.reset_obs_vector()

    def flatten_red_alert(red_alert):
        pass

    def reset(self, seed=None, options=None):
        self.total = 0
        self.current_step = 0

        # There's a performance issue here
        self.network.reset()

        #NOTE: Have we tested the deepcopy instead of removing decoys?
        #self.network = deepcopy(self.network_copy)    
         
        if self.red_agent_choice == "recurring_impact":
            self.red_agent = RecurringImpactAgent(
                self.network.get_random_user_host(), network=self.network
            )
        else:
            self.red_agent = KillChainAgent(
                self.network.get_random_user_host(), network=self.network
            )

        self.blue_agent = IsolateBlueAgent(self.network, self.decoy_info, self.host_defs, self.max_decoys)

        self.alert_converter = HistoryObservation(
            self.observation_space.shape, host_to_index_mapping(self.network)
        )
        # self.detector = NIDSDetector()
        self.reward_calculator.reset()
        return self._reset_obs(), {}

    # can implement existing GUI here???
    def render(self, mode="human"):
        pass

    # if you open any other processes close them here
    def close(self):
        pass