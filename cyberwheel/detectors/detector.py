from abc import abstractmethod
from typing import Iterable
import random

from cyberwheel.network.network_base import Network
from .alert import Alert


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
        

        # If one of the destination hosts is a decoy, then this alert is always detected 
        alerted_hosts = [Alert(src_host=perfect_alert.src_host, dst_hosts=[host], services=perfect_alert.services) for host in perfect_alert.dst_hosts if host.decoy]
        return alerted_hosts


class PerfectDetector(Detector):
    def obs(self, perfect_alert: Alert) -> Iterable[Alert]:
        return [perfect_alert]
