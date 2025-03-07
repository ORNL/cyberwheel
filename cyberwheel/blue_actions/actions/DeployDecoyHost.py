import json

from typing import Dict, List

from cyberwheel.blue_actions.blue_action import SubnetAction, generate_id, BlueActionReturn
from cyberwheel.network.network_base import Network
from cyberwheel.network.host import HostType
from cyberwheel.network.subnet import Subnet


def get_host_types() -> List[Dict[str, any]]:
    with open("resources/metadata/host_definitions.json", "rb") as f:
        host_defs = json.load(f)
    return host_defs["host_types"]


class DeployDecoyHost(SubnetAction):
    """
    This class represents the action for deploying a decoy Host in the network.
    """
    def __init__(self, network: Network, configs: Dict[str, any], **kwargs) -> None:
        super().__init__(network, configs)
        self.define_configs()
        self.define_services()
        self.decoy_list : list[str] = kwargs.get("decoy_list", [])

    def execute(self, subnet: Subnet, **kwargs) ->  BlueActionReturn:
        """
        This executes the action to deploy a decoy host.

        When ran, this function will add a decoy Host to the
        network with a UUID name.
        """
        seed = kwargs.get("seed", None)
        name = generate_id(seed=seed)
        if "server" in self.type.lower():
            host_type = HostType(
                name="Server", services=self.services, decoy=True, cve_list=self.cves
            )
        else:
            host_type = HostType(
                name="Workstation",
                services=self.services,
                decoy=True,
                cve_list=self.cves,
            )

        self.host = self.network.create_decoy_host(name, subnet, host_type)
        self.decoy_list.append(name)
        return BlueActionReturn(name, True, 1, target=subnet.name)
