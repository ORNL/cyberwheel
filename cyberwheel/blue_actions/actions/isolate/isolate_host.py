from cyberwheel.blue_actions.blue_base import BlueAction
from cyberwheel.network.network_base import Network
from cyberwheel.network.host import Host


class IsolateHost(BlueAction):
    def __init__(self, network: Network) -> None:
        self.network: Network = network
        super().__init__()

    def execute(self, host: Host) -> None:
        host.disconnected = True
        self.network.disconnect_node(host.name, host.subnet.name)
