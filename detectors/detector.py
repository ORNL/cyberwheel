from abc import abstractmethod
from typing import List

from alert import Alert
import random
# Detector converts the state change resulting from a red action into an alert
class Detector:

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def obs(self, perfect_alert: Alert)-> List[Alert]:
        raise NotImplementedError    


class CoinFlipDetector(Detector):
    """Sample detector that keeps everything or throws away everything with 50/50 odds"""
    def __init__(self):
        super.__init__("CoinFlip")
        random.seed()

    def obs(self, perfect_alert:Alert)-> List[Alert]:
        flip = random.randint(0,1)
        if flip:
            return [perfect_alert]
        return []