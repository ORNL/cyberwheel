import copy
from importlib.resources import files
from gym import spaces
import gym
from typing import Dict, Iterable, List
import yaml

from .cyberwheel import Cyberwheel
from cyberwheel.blue_agents import DynamicBlueAgent
from cyberwheel.observation import HistoryObservation
from cyberwheel.detectors.alert import Alert
from cyberwheel.detectors.handler import DetectorHandler
from cyberwheel.network.network_base import Network
from cyberwheel.network.host import Host
from cyberwheel.red_agents import ARTAgent
from cyberwheel.red_agents.strategies import ServerDowntime
from cyberwheel.reward import DecoyReward, StepDetectedReward
from cyberwheel.reward.recurring_reward import RecurringReward
from cyberwheel.reward.restore_reward import RestoreReward


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


class DynamicCyberwheel(gym.Env, Cyberwheel):
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
        red_agent="art_agent",
        evaluation=False,
        blue_config="dynamic_blue_agent.yaml",
        network=None,
        service_mapping={},
        **kwargs,
    ):
        network_conf_file = files("cyberwheel.resources.configs.network").joinpath(
            network_config
        )
        decoy_conf_file = files("cyberwheel.resources.configs.decoy_hosts").joinpath(
            decoy_host_file
        )
        host_conf_file = files(
            "cyberwheel.resources.configs.host_definitions"
        ).joinpath(host_def_file)
        super().__init__(config_file_path=network_conf_file, network=network)
        self.total = 0
        self.max_steps = kwargs.get("num_steps", 100)
        self.current_step = 0

        # Create action space. Decoy action for each decoy type for each subnet.
        # Length = num_decoy_host_types * num_subnets
        with open(decoy_conf_file, "r") as f:
            self.decoy_info = yaml.safe_load(f)

        with open(host_conf_file, "r") as f:
            self.host_defs = yaml.safe_load(f)["host_types"]

        self.decoy_types = list(self.decoy_info.keys())

        num_hosts = len(self.network.get_hosts())

        self.observation_space = spaces.Box(0, 1, shape=(2 * num_hosts,))
        self.alert_converter = HistoryObservation(
            self.observation_space.shape, host_to_index_mapping(self.network)
        )
        self.red_agent_choice = red_agent
        self.service_mapping = service_mapping

        self.red_strategy = kwargs.get("red_strategy", ServerDowntime)

        self.red_agent = ARTAgent(
            self.network.get_random_user_host(), network=self.network, service_mapping=self.service_mapping, red_strategy=self.red_strategy
        )

        self.blue_conf_file = files("cyberwheel.resources.configs.blue_agent").joinpath(
            blue_config
        )
        self.blue_agent = DynamicBlueAgent(self.blue_conf_file, self.network)
        self.action_space = self.blue_agent.create_action_space()
        # self.blue_agent = DecoyBlueAgent(self.network, self.decoy_info, self.host_defs)

        detector_conf_file = files("cyberwheel.resources.configs.detector").joinpath(detector_config)
        self.detector = DetectorHandler(detector_conf_file)

        self.reward_function = reward_function

        if reward_function == "step_detected":
            self.reward_calculator = StepDetectedReward(
                blue_rewards=self.blue_agent.get_reward_map(),
                r=(min_decoys, max_decoys),
                scaling_factor=blue_reward_scaling,
                max_steps=self.max_steps,
            )
        else:
            self.reward_calculator = RecurringReward(
                self.red_agent.get_reward_map(),
                self.blue_agent.get_reward_map(),
            )

        self.evaluation = evaluation

    def step(self, action):
        blue_agent_result = self.blue_agent.act(action)
        self.reward_calculator.handle_blue_action_output(blue_agent_result.name, blue_agent_result.id, blue_agent_result.success, blue_agent_result.recurring)
        red_action_name = (
            self.red_agent.act().get_name()
        )  # red_action includes action, and target of action
        action_metadata = self.red_agent.history.history[-1]

        red_action_type = action_metadata["action"]
        red_action_src = action_metadata["src_host"]
        red_action_dst = action_metadata["target_host"]
        red_action_success = action_metadata["success"]

        self.reward_calculator.handle_red_action_output(red_action_name, self.red_agent.history.mapping[red_action_dst].decoy)

        red_action_result = (
            self.red_agent.history.recent_history()
        )

        alerts = self.detector.obs([red_action_result.detector_alert])
        obs_vec = self._get_obs(alerts)
        #print(obs_vec)
        
        if self.reward_function == "step_detected":
            reward = self.reward_calculator.calculate_reward(
                blue_agent_result.name, blue_agent_result.success, x, self.current_step
            )
        else:
            # print(red_action_name)
            reward = self.reward_calculator.calculate_reward(
                red_action_name, blue_agent_result.name, red_action_success, blue_agent_result.success, self.red_agent.history.mapping[red_action_dst].decoy
            )
        self.total += reward

        if self.current_step >= self.max_steps:  # Maximal number of steps
            done = True
        else:
            done = False
        self.current_step += 1

        info = {}
        if self.evaluation:
            info = {
                "red_action": red_action_type,
                "red_action_src": red_action_src,
                "red_action_dst": red_action_dst,
                "red_action_success": red_action_success,
                "blue_action": blue_agent_result.name,
                "network": self.blue_agent.network,
                "history": self.red_agent.history,
                "killchain": self.red_agent.killchain,
            }
        self.detector.reset()
        self.detector.reset()
        return (
            obs_vec,
            reward,
            done,
            False,
            info,
        )

    def _get_obs(self, alerts: List[Alert]) -> Iterable:
        return self.alert_converter.create_obs_vector(alerts)

    def _reset_obs(self) -> Iterable:
        return self.alert_converter.reset_obs_vector()

    def reset(self, seed=None, options=None):
        self.total = 0
        self.current_step = 0
        self.network.reset()

        self.red_agent.reset(
            self.network.get_random_user_host(), network=self.network
        )

        self.blue_agent.reset()
        
        self.alert_converter = HistoryObservation(
            self.observation_space.shape, host_to_index_mapping(self.network)
        )
        self.reward_calculator.reset()
        return self._reset_obs(), {}

    # if you open any other processes close them here
    def close(self):
        pass
