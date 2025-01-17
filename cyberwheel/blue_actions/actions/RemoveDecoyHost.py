from typing import Dict

from cyberwheel.blue_actions.blue_action import SubnetAction, BlueActionReturn
from cyberwheel.network.network_base import Network
from cyberwheel.network.subnet import Subnet


class RemoveDecoyHost(SubnetAction):
    def __init__(self, network: Network, configs: Dict[str, any]) -> None:
        super().__init__(network, configs)

    def execute(self, subnet: Subnet, **kwargs) -> int:
        success = False
        id = ""
        for host in subnet.get_connected_hosts():
            if host.decoy:
                self.network.remove_host_from_subnet(host)
                success = True
                id = host.name
                break
        return BlueActionReturn(id, success, -1)
