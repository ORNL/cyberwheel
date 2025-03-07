from cyberwheel.network.network_base import Network
from cyberwheel.red_agents import ARTAgent
from cyberwheel.red_actions.actions import Nothing
from cyberwheel.red_agents.red_agent_base import RedAgentResult
from cyberwheel.reward import RewardMap
from cyberwheel.utils import YAMLConfig

class InactiveRedAgent(ARTAgent):
    def __init__(self, network: Network, args: YAMLConfig):
        super().__init__(network, args, "InactiveRedAgent", map_services=False)

    def act(self, action=None) -> RedAgentResult:
        action_results = Nothing(self.current_host, self.current_host).sim_execute()
        return RedAgentResult(action_results.action, self.current_host, self.current_host, True, action_results=action_results)

    def handle_network_change(self):
        pass

    def select_next_target(self):
        pass

    def run_action(self, target_host):
        pass

    def add_host_info(self, all_metadata):
        pass

    def get_reward_map(self) -> RewardMap:
        return {"nothing": (0, 0)}
    
    def reset(self):
        super().reset()
