import random
from typing import Iterable

from network.network_base import Network
from ..detector_base import read_detector_yaml, Detector
from ..alert import Alert

class HIDSDetector(Detector):
    def __init__(self, network: Network) -> None:
        self.network = network
        self.technique_probabilites = read_detector_yaml('resources/configs/hids_detector.yaml')
    
    def obs(self, perfect_alert: Alert) -> Iterable[Alert]: 
        alerts = []
        
        for dst in perfect_alert.dst_hosts:
            detection_failed = True
            
            # Check to see if the detector can successfully detect the action based on the technique used
            for technique in perfect_alert.techniques:
                # Detector might not be able to detect the technique at all
                if technique.name not in self.technique_probabilites:
                    continue

                # Use probability of successful detection to determine if the action was noticed
                detection_probability = float(self.technique_probabilites[technique.name])
                if random.random() > detection_probability:
                    continue
                
                # Detector only has to be successful on 1 technique?
                detection_failed = False
                break
        
            if detection_failed:
                return alerts
    
            new_alert = Alert(src_host=perfect_alert.src_host, dst_hosts=[dst], services=perfect_alert.services)
            alerts.append(new_alert)
            return alerts