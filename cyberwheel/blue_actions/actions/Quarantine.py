from typing import Dict

from cyberwheel.blue_actions.blue_action import HostAction
from cyberwheel.blue_actions.blue_action import BlueActionReturn
from cyberwheel.network.network_base import Network
from cyberwheel.network.host import Host


class QuarantineHost(HostAction):
    def __init__(self, network: Network, configs: Dict[str, any], **kwargs) -> None:
        super().__init__(network, configs)
        self.quarantine_list = kwargs.get("quarantine_list", [])


    def execute(self, host: Host, **kwargs) -> None:
        if host.name in self.quarantine_list:
            return BlueActionReturn("", False)

        self.network.isolate_host(host, host.subnet)
        self.quarantine_list.append(host.name)
        return BlueActionReturn("", True, 0)


class RemoveQuarantineHost(HostAction):
    def __init__(self, network: Network, configs: Dict[str, any], **kwargs) -> None:
        super().__init__(network, configs)
        self.quarantine_list = kwargs.get("quarantine_list", [])


    def execute(self, host: Host, **kwargs) -> None:
        if host.name not in self.quarantine_list:
            return BlueActionReturn("", False)

        self.network.connect_nodes(host.name, host.subnet.name)
        self.quarantine_list.remove(host.name)
        return BlueActionReturn("", True)