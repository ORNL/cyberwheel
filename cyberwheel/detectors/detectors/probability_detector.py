import random
import yaml
from typing import Iterable

from network.network_base import Network
from detectors.detector_base import Detector
from detectors.alert import Alert

def _read_detector_yaml(filename: str):
    with open(filename, 'r') as yaml_file:
        techniques = yaml.safe_load(yaml_file)
    return techniques

# The difference between NIDS and HIDS seems to only be what techniques they can detect. 
# Define their techniques in a YAML file. 
# Unless we use more specific data other than just techniques. Then they'd be quite different.
class ProbabilityDetector(Detector):
    """
        A detector that can detect techniques with some probability.
        The techniques that a detector supports should be defined in a YAML file along with a probabilty of detection for that technique.
    """
    def __init__(self) -> None:
        self.technique_probabilites = _read_detector_yaml('resources/configs/nids_detector.yaml')

    def obs(self, perfect_alert: Alert) -> Iterable[Alert]:
        alerts = []
        
        for dst in perfect_alert.dst_hosts:
            detection_failed = True
            if dst.decoy:
                new_alert = Alert(src_host=perfect_alert.src_host, dst_hosts=[dst], services=perfect_alert.services)
                alerts.append(new_alert)
                continue
            techniques = set(perfect_alert.techniques) & set(self.technique_probabilites.keys())
            # Check to see if the detector can successfully detect the action based on the technique used
            for technique in techniques:
                # Use probability of successful detection to determine if the action was noticed
                detection_probability = float(self.technique_probabilites[technique])
                if random.random() > detection_probability:
                    continue
                
                # Detector only has to be successful on 1 technique
                detection_failed = False
                break
        
            if detection_failed:
                continue
    
            new_alert = Alert(src_host=perfect_alert.src_host, dst_hosts=[dst], services=perfect_alert.services)
            alerts.append(new_alert)
        return alerts