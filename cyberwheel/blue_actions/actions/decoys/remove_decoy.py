from blue_actions.blue_base import BlueAction
from network.network_base import Network
from network.host import Host, HostType
from network.subnet import Subnet


class RemoveDecoyHost(BlueAction):
    def __init__(self, network: Network, host: Host) -> None:
        """
            A class that allows the blue agent to create a decoy host.
            ### Parameters
            - `network`: the game's network object
            - `subnet`: the subnet this host should be added on
            - `type`: the type of host this decoy will impersonate

            ### Member variables
            - `initial_cost`: the negative effect this action has on
            - `recurring_cost`:
        """
        
        self.network: Network = network
        self.host: Host = host
        self.reward: int = -5


    def execute(self) -> int:
        self.network.remove_host_from_subnet(self.host)
        # self.host = Host()
        return self.reward