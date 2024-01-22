from abc import abstractmethod
from typing import List
import random

from network.network_base import Network
from alert import Alert


# Detector converts the state change resulting from a red action into an alert. I don't know what red actions will return right now,
# but currently their result is saved in a network object. So, I'll just use that for now
class Detector:
    # This should be called to make the alerts that will be passed on to become blue observations.
    # It'll chose which alerts to keep or throw out.
    # Input is subject to change based on red action work.
    @abstractmethod
    def obs(self, network_state: Network)-> List[Alert]:
        raise NotImplementedError    

    # This is what actually creates the alerts. It should create an alert for each affected host. 
    # Currently, we just have a binary flag for compromised/uncompromised so this means there is an alert for a host only 
    # if it is compromised. This probably won't be true in the future as more states for hosts are supported. This can be updated 
    # to get information that a real-world detector would reasonably know.
    @abstractmethod
    def examine_network_state(self, network_state: Network)-> List[Alert]:
        raise NotImplementedError



class CoinFlipDetector(Detector):
    """Example detector that keeps everything or throws away everything with 50/50 odds."""

    def obs(self, network_state:Network)-> List[Alert]:
        perfect_alert = self.examine_network_state(network_state)
        flip = random.randint(0,1)
        if flip:
            return perfect_alert
        return []
    
    def examine_network_state(self, network_state: Network) -> List[Alert]:
        compromised_hosts = [host for host in network_state.get_hosts() if host.is_compromised]
        alerts = []
        for compromised_host in compromised_hosts:
            alerts.append(Alert(compromised_host, None, None, None)) # Last 3 args are not implemented yet.
        return alerts
    

class PerfectDetector(Detector):
    def obs(self, network_state:Network) -> List[Alert]:
        return self.examine_network_state(network_state)
    
    def examine_network_state(self, network_state: Network) -> List[Alert]:
        compromised_hosts = [host for host in network_state.get_hosts() if host.is_compromised]
        alerts = []
        for compromised_host in compromised_hosts:
            alerts.append(Alert(compromised_host, None, None, None)) # Last 3 args are not implemented yet.
        return alerts