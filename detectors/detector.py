from abc import abstractmethod
from typing import List
import random

from network.network_base import Network
from alert import Alert



class Detector:
    @abstractmethod
    def obs(self, perfect_alert: Alert)-> List[Alert]:
        raise NotImplementedError    

class CoinFlipDetector(Detector):
    """Example detector that keeps everything or throws away everything with 50/50 odds."""

    def obs(self, perfect_alert: Alert)-> List[Alert]:
        flip = random.randint(0,1)
        if flip:
            return [perfect_alert]
        return []

    

class PerfectDetector(Detector):
    def obs(self, perfect_alert:Alert) -> List[Alert]:
        return perfect_alert