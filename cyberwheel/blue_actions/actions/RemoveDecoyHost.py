from typing import Dict

from blue_actions.dynamic_blue_base import SubnetAction, generate_id, DynamicBlueActionReturn
from network.network_base import Network
from network.host import Host, HostType
from network.subnet import Subnet


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
        
        # self.host = Host()
        return DynamicBlueActionReturn(id, success, -1)