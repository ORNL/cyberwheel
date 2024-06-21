import builtins
import importlib
import uuid
import yaml

from importlib.resources import files
from typing import Iterable, Union, Dict, Tuple, List, NewType

from cyberwheel.blue_agents.blue_agent_base import BlueAgent, BlueAgentResult
from cyberwheel.blue_actions.dynamic_blue_base import DynamicBlueAction
from cyberwheel.reward.reward_base import RewardMap
from cyberwheel.network.network_base import Network
from cyberwheel.network.host import Host
from cyberwheel.network.subnet import Subnet


range = NewType("range", Tuple[int, int])


class _ActionConfigInfo():
    def __init__(self, name="", 
                 configs=[], 
                 immediate_reward=0.0, 
                 recurring_reward=0.0, 
                 action_type: str="", 
                 shared_data=[],
                 range=0) -> None:
        self.name = name
        self.configs = configs
        self.immediate_reward = immediate_reward
        self.recurring_reward = recurring_reward
        self.action_type = action_type
        self.shared_data = shared_data
        self.range = range

    def __str__(self) -> str:
        return f'config: {self.configs}, immediate_reward: {self.immediate_reward}, reccuring_reward: {self.recurring_reward}, action_type: {self.action_type}'

class _ActionRuntime():
    def __init__(self, name: str, action_type: str, action: DynamicBlueAction, range: range, is_recurring: bool) -> None:
        self.name = name
        self.action_type = action_type
        self.action = action
        self.range = range
        self.is_recurring = is_recurring

    def check_range(self, action: int) -> bool:
        return  action >= self.range[0] and action < self.range[1]

class DynamicBlueAgent(BlueAgent):
    """
    The purpose of this blue agent is to prevent having to create new blue agents everytime a new 
    blue action is introduced. The idea is to have a config file specify what blue actions this instance
    has and import them dynamically (I think that's the right term...).

    Actions need to be very standardized. Each one will need to have the following associated with it:
    - An action name: The name of the action performed. If you have two deploy actions, then the names would
    be something like: decoy0 and decoy1. Used by the reward calculator to determine reward.
    - A unique ID: Recurring rewards need an ID to identify them from other recurring actions. A UUID should
    be sufficient for this. If an action has no recurring cost (i.e. 0) then the ID can be "".

    This agent should also keep track of blue action config files. The config for decoys is an example. 
    """
    def __init__(self, config: str, network: Network) -> None:
        super().__init__()
        self.config = config
        self.from_yaml()
        self.configs: Dict[str, any] = {}
        self.action_space_size = 0

        self.network = network
        self.hosts = network.get_hosts()
        self.subnets = network.get_all_subnets()
        self.num_hosts = len(self.hosts)
        self.num_subnets = len(self.subnets)

        self._init_action_runtime_info()
        self._init_reward_map()
    
    def from_yaml(self):
        module_path = "blue_actions.actions."
        actions = []
        with open(self.config, "r") as r:
            contents = yaml.safe_load(r)
        # Load class types and get action info
        for k, v in contents['actions'].items():
            module_name = v['module']
            class_name = v['class']
            configs = {}
            if isinstance(v['configs'], Dict):
                configs = v['configs']
            shared_data = []
            if isinstance(v['shared_data'], List):
                shared_data = v['shared_data']
            range = 0
            if v['type'] == 'range':
                range = v['range']
            import_path = module_path + module_name
            a = importlib.import_module(import_path)
            class_ = getattr(a, class_name)
            action_info = _ActionConfigInfo(k, 
                                            configs, 
                                            v['reward']['immediate'], 
                                            v['reward']['recurring'], 
                                            v['type'], 
                                            shared_data,
                                            range)
            actions.append((class_, action_info))
        self.actions = actions
        # Set up additional data that actions have requested.
        self.shared_data = {}
        self.reset_map = {}
        if contents['shared_data'] is None:
            return
        for k, v in contents['shared_data'].items():
            if v in ('list', 'set', 'dict'):
                data_type = getattr(builtins, v)
                self.shared_data[k] = data_type()
            else:
                if 'module' not in v or 'class' not in v:
                    raise KeyError("If using custom object, 'module' and 'class' must be defined.")
                a = importlib.import_module(v['module'])
                data_type = getattr(a, v['class'])
                
                kwargs = {}
                if 'args' in v and v['args'] is not None:
                    kwargs = v['args']
                
                self.shared_data[k] = data_type(**kwargs)
            
    def _init_action_runtime_info(self)-> None:
        self.runtime_info: List[_ActionRuntime] = []
        for action_class, action_info in self.actions:
            # Check configs and read them if they are new
            action_configs = {}
            for name, config in action_info.configs.items():
                # Skip configs that have already been seen
                if not config in self.configs:                    
                    conf_file = files("cyberwheel.resources.metadata").joinpath(config)            
                    with open(conf_file, "r") as f:
                        contents = yaml.safe_load(f)
                    self.configs[config] = contents
                    action_configs[name] = contents
                else:
                    action_configs[name] = self.configs[config]
            # print(action_configs)
            # Calculate action space size and initialize blue actions
            start = self.action_space_size
            if action_info.action_type == "standalone":
                self.action_space_size += 1
            elif action_info.action_type.lower() == "host":
                self.action_space_size += self.num_hosts
            elif action_info.action_type.lower() == "subnet":
                self.action_space_size += self.num_subnets
            elif action_info.action_type.lower() == "range":
                self.action_space_size += action_info.range
            else:
                raise ValueError(f"action_type for {action_info.name} must be 'host', 'subnet', 'standalone', or 'range'")
            end = self.action_space_size
            r = (start, end)

            kwargs = {}
            for sd in action_info.shared_data:
                kwargs[sd] = self.shared_data[sd]
            runtime = _ActionRuntime(action_info.name, 
                                     action_info.action_type, 
                                     action_class(self.network, action_configs, **kwargs), 
                                     r, 
                                     bool(action_info.recurring_reward))
            self.runtime_info.append(runtime)

    def _init_reward_map(self) -> None:
        self.reward_map: RewardMap = {}
        for _, action_config_info in self.actions:
            if action_config_info.name in self.reward_map:
                raise KeyError("error constructing reward map: action names should be unique")
            self.reward_map[action_config_info.name] = (action_config_info.immediate_reward, action_config_info.recurring_reward)

    def act(self, action: int) -> BlueAgentResult:
        for ri in self.runtime_info:
            if not ri.check_range(action):
                continue
            name = ri.name
            if ri.action_type == "standalone":
                result = ri.action.execute()
                break
            elif ri.action_type == "host":
                index = (action - ri.range[0]) % self.num_hosts
                result = ri.action.execute(self.hosts[index])
                break
            elif ri.action_type == "subnet":
                index = (action - ri.range[0]) % self.num_subnets
                result = ri.action.execute(self.subnets[index])
                break
            elif ri.action_type == "range":
                index = (action - ri.range[0]) % (ri.range[1]- ri.range[0])
                result = ri.action.execute(index)
                break
            else:
                raise TypeError("Unknown action type.")
        
        id = result.id
        success = result.success
        recurring = result.recurring
        return name, id, success, recurring
    
    def get_reward_map(self) -> RewardMap:
        return self.reward_map

    def get_action_space_size(self) -> int:
        return self.action_space_size
    
    def reset(self):
        # I think all this needs to do is set all shared_data values to their default values
        for v in self.shared_data.values():
            v.clear()

if __name__ == "__main__":
    network = Network.create_network_from_yaml("/home/70d/cyberwheel/cyberwheel/resources/metadata/10-host-network.yaml")
    agent = DynamicBlueAgent("/home/70d/cyberwheel/cyberwheel/resources/configs/dynamic_blue_agent.yaml", network)
    agent.act(1)
    agent.act(2)
    agent.act(2)
    agent.act(2)
    agent.act(7)
    agent.act(7)
    agent.act(9)
    agent.act(10)
    # print(agent.shared_data)
    # agent.act(2)
    # agent.act(3)
    # r = agent.get_reward_map()
    network.draw(filename="test.png")

    # print(network.get_host_names())