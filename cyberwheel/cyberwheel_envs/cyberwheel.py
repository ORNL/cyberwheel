import yaml

from importlib.resources import files

from cyberwheel.network.network_base import Network
from cyberwheel.red_agents import InactiveRedAgent
from cyberwheel.red_agents.red_agent_base import RedAgentResult
from cyberwheel.blue_agents import InactiveBlueAgent
from cyberwheel.blue_agents.blue_agent import BlueAgentResult


class Cyberwheel:
    """
    Cyberwheel base class. Defining this environment will set up the environment
    without any RL components for various other use cases.
    """

    def __init__(self, args, network: Network = None):
        self.args = args
        network_conf_file = files("cyberwheel.data.configs.network").joinpath(
            args.network_config
        )
        host_conf_file = files(
            "cyberwheel.data.configs.host_definitions"
        ).joinpath(args.host_config)
        
        self.network = network if network else Network.create_network_from_yaml(network_conf_file)
        with open(host_conf_file, "r") as f:
            self.host_defs = yaml.safe_load(f)["host_types"]
        
        self.initialize_agents()

        # Initializing environment states
        self.max_steps = args.num_steps
        self.current_step = 0
        self.service_mapping = args.service_mapping
        

    def initialize_agents(self) -> None:
        self.red_agent = InactiveRedAgent(self.network, self.args)
        self.blue_agent = InactiveBlueAgent()

    def run_blue_agent(self, action) -> BlueAgentResult:
        return self.blue_agent.act(action)

    def run_red_agent(self, action) -> RedAgentResult:
        return self.red_agent.act(action)

    def step(self, action=None) -> dict[str, RedAgentResult | BlueAgentResult]:
        blue_agent_result = self.run_blue_agent(action)

        red_agent_result = self.run_red_agent(action)

        self.current_step += 1
        return {
            "red_agent_result": red_agent_result,
            "blue_agent_result": blue_agent_result,
        }

    def reset(self) -> None:
        self.current_step = 0
        self.network.reset()
        self.red_agent.reset()
        self.blue_agent.reset()

    def close(self) -> None:
        pass

    @classmethod
    def create_from_yaml(cls, config_file_path):
        return cls(config_file_path=config_file_path)
