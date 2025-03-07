import builtins
import importlib
import yaml

from importlib.resources import files
from typing import Dict, List, Any, Iterable
from gymnasium import Space

from cyberwheel.blue_agents.blue_agent import BlueAgent, BlueAgentResult
from cyberwheel.reward.reward_base import RewardMap
from cyberwheel.network.network_base import Network, Host
from cyberwheel.blue_agents.action_space.action_space import ActionSpace
from cyberwheel.observation import BlueObservation


def host_to_index_mapping(network: Network, deterministic: bool = False) -> Dict[Host, int]:
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

    if deterministic:
        hosts = sorted(list(network.hosts.keys() - network.decoys.keys()))
    else:
        hosts = network.hosts.keys() - network.decoys.keys()

    for host in hosts:
        mapping[host] = i
        i += 1
    return mapping

class _ActionConfigInfo():
    def __init__(self, 
                 name: str  = "", 
                 configs: List = [], 
                 immediate_reward: float = 0.0, 
                 recurring_reward: float = 0.0, 
                 action_space_args: Dict = {}, 
                 shared_data: List = []) -> None:
        self.name = name
        self.configs = configs
        self.immediate_reward = immediate_reward
        self.recurring_reward = recurring_reward
        self.shared_data = shared_data
        self.action_space_args = action_space_args

    def __str__(self) -> str:
        return f"config: {self.configs}, immediate_reward: {self.immediate_reward}, reccuring_reward: {self.recurring_reward}, action_type: {self.action_type}"

class RLBlueAgent(BlueAgent):
    """
    The purpose of this blue agent is to prevent having to create new blue agents everytime a new 
    blue action is introduced. The idea is to have a config file specify what blue actions this instance
    has and import them dynamically.

    Actions need to be very standardized. Each one will need to have the following associated with it:
    - An action name: The name of the action performed. If you have two deploy actions, then the names would
    be something like: decoy0 and decoy1. Used by the reward calculator to determine reward.
    - A unique ID: Recurring rewards need an ID to identify them from other recurring actions. A UUID should
    be sufficient for this. If an action has no recurring cost (i.e. 0) then the ID can be "".

    This agent should also keep track of blue action config files. The config for decoys is an example.
    """
    def __init__(self, network: Network, args) -> None:
        super().__init__()
        self.args = args
        self.config = files("cyberwheel.data.configs.blue_agent").joinpath(args.blue_agent)
        self.network = network

        self.observation = BlueObservation(2 * len(self.network.hosts), host_to_index_mapping(self.network, self.args.deterministic), args.detector_config)

        self.configs: Dict[str, Any] = {}
        self.action_space: ActionSpace = None
        
        self.from_yaml()
        self._init_blue_actions()
        self._init_reward_map()

    def from_yaml(self) -> None:
        with open(self.config, "r") as r:
            contents = yaml.safe_load(r)      
        
        # Initialize the action space converter
        action_space = contents['action_space']
        as_class = action_space['class']
        if 'args' in action_space and action_space['args']:
            as_args = action_space['args']
        else:
            as_args = {}
        m = importlib.import_module("cyberwheel.blue_agents.action_space")
        self.action_space = getattr(m, as_class)(self.network, **as_args)      

        # Get information needed to later initialize blue actions.
        actions = []
        for k, v in contents['actions'].items():
            class_name = v['class']
            configs = {}
            if "configs" in v and isinstance(v["configs"], Dict):
                configs = v["configs"]
            shared_data = []
            if "shared_data" in v and isinstance(v['shared_data'], List):
                shared_data = v['shared_data']
            
            import_path = "cyberwheel.blue_actions.actions"
            m = importlib.import_module(import_path)
            class_ = getattr(m, class_name)
            action_info = _ActionConfigInfo(k, 
                                            configs, 
                                            v['reward']['immediate'], 
                                            v['reward']['recurring'], 
                                            v['action_space_args'], 
                                            shared_data)
            actions.append((class_, action_info))
        self.actions = actions
        
        # Set up data shared between actions
        self.shared_data = {}
        self.reset_map = {}
        if "shared_data" in contents:
            for k, v in contents["shared_data"].items():
                if v in ("list", "set", "dict"):
                    data_type = getattr(builtins, v)
                    self.shared_data[k] = data_type()
                else:
                    if "module" not in v or "class" not in v:
                        raise KeyError(
                            "If using custom object, 'module' and 'class' must be defined."
                        )
                    a = importlib.import_module(v["module"])
                    data_type = getattr(a, v["class"])

                    kwargs = {}
                    if "args" in v and v["args"] is not None:
                        kwargs = v["args"]

                    self.shared_data[k] = data_type(**kwargs)
            
    def _init_blue_actions(self) -> None:
        for action_class, action_info in self.actions:
            # Check configs and read them if they are new
            action_configs = {}
            for name, config in action_info.configs.items():
                # Skip configs that have already been seen
                if not config in self.configs:
                    conf_file = files(f"cyberwheel.data.configs.{name}").joinpath(
                        config
                    )
                    with open(conf_file, "r") as f:
                        contents = yaml.safe_load(f)
                    self.configs[config] = contents
                    action_configs[name] = contents
                else:
                    action_configs[name] = self.configs[config]

            action_kwargs = {}
            for sd in action_info.shared_data:
                action_kwargs[sd] = self.shared_data[sd]
            action = action_class(self.network, action_configs, **action_kwargs)

            self.action_space.add_action(action_info.name, action, **action_info.action_space_args)
        self.action_space.finalize()

    def _init_reward_map(self) -> None:
        self.reward_map: RewardMap = {}
        for _, action_config_info in self.actions:
            if action_config_info.name in self.reward_map:
                raise KeyError(
                    "error constructing reward map: action names should be unique"
                )
            self.reward_map[action_config_info.name] = (
                action_config_info.immediate_reward,
                action_config_info.recurring_reward,
            )

    def act(self, action: int) -> BlueAgentResult:
        self.observation.detector.reset()
        asc_return = self.action_space.select_action(action)

        if self.args.deterministic:
            asc_return.kwargs["seed"] = self.args.seed
            self.args.seed += 1
        
        result = asc_return.action.execute(*asc_return.args, **asc_return.kwargs)
        
        return BlueAgentResult(asc_return.name, result.id, result.success, result.recurring, target=result.target)
    
    def get_reward_map(self) -> RewardMap:
        return self.reward_map

    def get_action_space_shape(self) -> tuple[int, ...]:
        return self.action_space.get_shape()
    
    def create_action_space(self, action_space_size: int) -> Space:
        return self.action_space.create_action_space(action_space_size)
    
    def get_observation_space(self, red_agent_result) -> Iterable:
        alerts = self.observation.detector.obs([red_agent_result.action_results.detector_alert])
        return self.observation.create_obs_vector(alerts)
    
    def reset(self) -> None:
        for v in self.shared_data.values():
            v.clear()
        self.observation.reset()