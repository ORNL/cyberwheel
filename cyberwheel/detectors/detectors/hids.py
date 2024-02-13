from typing import Iterable

from ..detector_base import Detector, read_detector_yaml
from ..alert import Alert
from network.network_base import Network

class HIDSDetector(Detector):
    def __init__(self, network: Network) -> None:
        self.network = network
        self.technique_probabilites = read_detector_yaml('resources/configs/nids_detector.yaml')
    
    def obs(self, perfect_alert: Alert) -> Iterable[Alert]: 
        
        raise NotImplementedError