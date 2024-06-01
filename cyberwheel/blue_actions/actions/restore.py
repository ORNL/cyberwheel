from blue_actions.blue_base import BlueAction
from network.network_base import Network
from network.host import Host, HostType
from network.subnet import Subnet


class Restore(BlueAction):
    def __init__(self, reward=0, recurring_reward=0) -> None:
        super().__init__(reward=reward, recurring_reward=recurring_reward)

    def execute(self, host: Host) -> bool:
        if not host.is_compromised or host.restored:
            return False
        
        host.remove_process("malware.exe")
        host.restored = True

        return True
        