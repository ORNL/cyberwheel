from abc import abstractmethod
from typing import Iterable
# from pathlib import Path
import random
import yaml

from cyberwheel.network.network_base import Network
from .alert import Alert

def technique_probabilities(filename: str):
    with open(filename, 'r') as yaml_file:
        probabilites = yaml.safe_load(yaml_file)
    return probabilites

class Detector:
    @abstractmethod
    def obs(self, perfect_alert: Alert) -> Iterable[Alert]:
        raise NotImplementedError

class CoinFlipDetector(Detector):
    """Example detector that keeps everything or throws away everything with 50/50 odds."""

    def obs(self, perfect_alert: Alert) -> Iterable[Alert]:
        flip = random.randint(0, 1)
        if flip:
            return [perfect_alert]
        return []
    
class DecoyDetector(Detector):
    """A detector that only gives alerts for hosts that access decoys"""
    def obs(self, perfect_alert: Alert) -> Iterable[Alert]:
        a = [Alert(src_host=perfect_alert.src_host, dst_hosts=[host], services=perfect_alert.services) for host in perfect_alert.dst_hosts if host.decoy]
        return a
class PerfectDetector(Detector):
    def obs(self, perfect_alert: Alert) -> Iterable[Alert]:
        return [perfect_alert]
