from typing import Dict

from cyberwheel.blue_actions.blue_action import HostAction, BlueActionReturn
from cyberwheel.network.network_base import Network
from cyberwheel.network.host import Host


class Restore(HostAction):
    def __init__(self, network: Network, configs: Dict[str, any], **kwargs) -> None:
        super().__init__(network, configs)
    
    def execute(self, host: Host, **kwargs) -> BlueActionReturn:
        if host.restored:
            return BlueActionReturn("", False)
        
        host.remove_process("malware.exe")
        host.restored = True

        return BlueActionReturn("", True)
        
