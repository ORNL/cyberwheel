from typing import Dict, List, Tuple, Any

from cyberwheel.blue_actions.actions.restore import Restore
from cyberwheel.blue_agents.blue_agent_base import BlueAgent, BlueAgentResult
from cyberwheel.network.network_base import Network
from cyberwheel.reward import RewardMap

class RestoreBlueAgent(BlueAgent):

    def __init__(
        self, network: Network, host_defs: Dict[str, Any]
        ) -> None:
        self.network = network
        self.num_hosts = len(self.network.get_hosts())
        self.action_space_length = self.num_hosts + 1 # restore host or do nothing
        self.host_defs = host_defs

    def act(self, action) -> BlueAgentResult:
        if action == 0:
            return "nothing", None, True
        
        host = self.network.get_hosts()[action - 1]
        restore = Restore()
        success = restore.execute(host)
        return "restore", None, success

    def get_reward_map(self) -> RewardMap:
        return {"restore": (100,0), "nothing": (0,0)}
