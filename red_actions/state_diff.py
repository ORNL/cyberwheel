from detectors.alert import Alert
from network.host import Host
from network.service import Service



class StateDifference():
    """
    A class for handling the changes to the state created by the red agent's actions.

    Whenever a red action does something on the network, such as ping a host(s) or expoiting a service on a host, it should update
    the the state difference. This update should reflect what a real detector should reasonably see. Right now, this includes the src 
    host, the destination host(s), and the service(s) being accessed. This list can be expanded. 
    """
    def __init__(self, src_host: Host) -> None:
        self.src_host = src_host
        self.alert = Alert()

    def add_host(self, host: Host) -> None:
        self.alert.add_dst_host(host)
    
    def add_service(self, service: Service ) -> None: 
        self.alert.add_service(service)

    def get_alert(self) -> Alert:
        return self.alert

    