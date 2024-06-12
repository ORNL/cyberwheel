from typing import Dict

from cyberwheel.blue_actions.dynamic_blue_base import StandaloneAction
from cyberwheel.blue_actions.dynamic_blue_base import DynamicBlueActionReturn
from cyberwheel.network.network_base import Network


class IsolateDecoy(StandaloneAction):
    def __init__(self, network: Network, configs: Dict[str, any], **kwargs) -> None:
        super().__init__(network, configs)
        self.isolate_data = kwargs.get("isolate_data")


    def execute(self, i, **kwargs) -> None:
        if i >= len(self.isolate_data.decoys):
            return DynamicBlueActionReturn("", False)
        host, subnet = self.isolate_data.decoys[i]

        if host.isolated:
            return DynamicBlueActionReturn("", False)

        self.network.isolate_host(host, subnet)
        return DynamicBlueActionReturn("", True)

