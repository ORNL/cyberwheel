from typing import Dict

from cyberwheel.blue_actions.dynamic_blue_base import HostAction, DynamicBlueActionReturn
from cyberwheel.network.network_base import Network
from cyberwheel.network.host import Host


class Restore(HostAction):
    def __init__(self, network: Network, configs: Dict[str, any], **kwargs) -> None:
        super().__init__(network, configs)
    
    def execute(self, host: Host, **kwargs) -> DynamicBlueActionReturn:
        if host.restored:
            return DynamicBlueActionReturn("", False)
        
        host.remove_process("malware.exe")
        host.restored = True

        return DynamicBlueActionReturn("", True)
        