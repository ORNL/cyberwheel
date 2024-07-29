from importlib.resources import files
import gymnasium as gym
from gymnasium import spaces
from typing import Dict, Iterable, List
import yaml

from .cyberwheel import Cyberwheel
from cyberwheel.blue_agents.restore_agent import RestoreBlueAgent
from cyberwheel.observation import HistoryObservation
from cyberwheel.detectors.alert import Alert
from cyberwheel.detectors.detectors.probability_detector import ProbabilityDetector
from cyberwheel.network.network_base import Network
from cyberwheel.network.host import Host
from cyberwheel.red_agents.restore_agent import RestoreAgent
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


class RestoreCyberwheel(gym.Env, Cyberwheel):
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
        evaluation=False,
        **kwargs,
    ):
        network_conf_file = files("cyberwheel.resources.configs.network").joinpath(
            network_config
        )
        host_conf_file = files("cyberwheel.resources.configs.decoy_hosts").joinpath(
            host_def_file
        )
        super().__init__(config_file_path=network_conf_file)
        self.total = 0
        self.max_steps = 100
        self.current_step = 0

        # Create action space. Decoy action for each decoy type for each subnet.
        # Length = num_decoy_host_types * num_subnets
        with open(host_conf_file, "r") as f:
            self.host_defs = yaml.safe_load(f)["host_types"]
        num_hosts = len(self.network.get_hosts())
        """
        There needs to be an action for deploying each host on each subnet.
        action_space[0] == which decoy host type to deploy
        action_space[1] == which subnet to deploy it on
        """

        self.action_space = spaces.Discrete(num_hosts + 1)
        self.observation_space = spaces.Box(0, 1, shape=(2 * num_hosts,))
        self.alert_converter = HistoryObservation(
            self.observation_space.shape, host_to_index_mapping(self.network)
        )

        self.red_agent_choice = red_agent
        self.red_agent = RestoreAgent(
            self.network.get_random_user_host(), network=self.network
        )
        self.blue_agent = RestoreBlueAgent(self.network, self.host_defs)

        self.detector = ProbabilityDetector(
            files("cyberwheel.resources.configs.detector").joinpath("hids.yaml")
        )  # PerfectDetector()
        self.detector2 = ProbabilityDetector(
            files("cyberwheel.resources.configs.detector").joinpath("nids.yaml")
        )
        self.reward_function = reward_function

        # TODO define new reward function for restore
        self.reward_calculator = RestoreReward(
            self.red_agent.get_reward_map(), self.blue_agent.get_reward_map()
        )

        self.evaluation = evaluation

    def step(self, action):
        blue_action_name, rec_id, blue_success = self.blue_agent.act(action)
        red_action_name = (
            self.red_agent.act().get_name()
        )  # red_action includes action, and target of action
        action_metadata = self.red_agent.history.history[-1]
        red_action_type, red_action_src, red_action_dst = action_metadata.action

        red_action_success = action_metadata.success

        red_action_result = (
            self.red_agent.history.recent_history()
        )  # red action results
        alerts = self.detector.obs(
            red_action_result.detector_alert
        ) + self.detector2.obs(red_action_result.detector_alert)
        obs_vec = self._get_obs(alerts)

        reward = self.reward_calculator.calculate_reward(
            red_action_name, blue_action_name, red_action_success, blue_success
        )

        self.total += reward

        if self.current_step >= self.max_steps:  # Maximal number of steps
            done = True
        else:
            done = False
        self.current_step += 1

        info = {}
        if self.evaluation:
            red_action_str = "Success - " if red_action_success else "Failed - "
            red_action_str += f"{red_action_type.__name__} from {red_action_src.name} to {red_action_dst.name}"
            info = {
                "action": {"Blue": blue_action_name, "Red": red_action_str},
                "network": self.blue_agent.network,
                "history": self.red_agent.history,
                "killchain": self.red_agent.killchain,
            }
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

    def flatten_red_alert(red_alert):
        pass

    def reset(self, seed=None, options=None):
        self.total = 0
        # print()
        self.current_step = 0

        self.network.reset()

        # NOTE: Have we tested the deepcopy instead of removing decoys?
        self.network = deepcopy(self.network_copy)

        self.red_agent = RestoreAgent(
            self.network.get_random_user_host(), network=self.network
        )

        self.blue_agent = RestoreBlueAgent(self.network, self.host_defs)

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
