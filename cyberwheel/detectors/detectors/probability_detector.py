import random
import yaml
from typing import Iterable

from cyberwheel.detectors.alert import Alert
from cyberwheel.detectors.detector_base import Detector

def _read_detector_yaml(filename: str):
    with open(filename, "r") as yaml_file:
        techniques = yaml.safe_load(yaml_file)
    return techniques

class ProbabilityDetector(Detector):
    """
    A detector that can detect techniques with some probability.
    The techniques that a detector supports should be defined in a YAML file along with a probabilty of detection for that technique.
    """

    name = "ProbabilityDetector"
    def __init__(self, config) -> None:
        self.technique_probabilites = _read_detector_yaml(config)

    def obs(self, perfect_alerts: Iterable[Alert]) -> Iterable[Alert]:
        alerts = []
        for perfect_alert in perfect_alerts:
            for dst in perfect_alert.dst_hosts:
                detection_failed = True

                # If the YAML file is empty, then only accessing decoys can create alerts
                if not self.technique_probabilites:
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
