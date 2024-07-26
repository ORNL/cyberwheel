import random
from typing import Iterable

from cyberwheel.detectors.alert import Alert
from cyberwheel.detectors.detector_base import Detector


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
        a = [
            Alert(
                src_host=perfect_alert.src_host,
                dst_hosts=[host],
                services=perfect_alert.services,
            )
            for host in perfect_alert.dst_hosts
            if host.decoy
        ]
        return a


class IsolateDetector(Detector):
    """A detector that only gives alerts for hosts that access decoys"""

    def obs(self, perfect_alert: Alert) -> Iterable[Alert]:
        a = [
            Alert(
                src_host=perfect_alert.src_host,
                dst_hosts=[host],
                services=perfect_alert.services,
            )
            for host in perfect_alert.dst_hosts
            if host.isolated
        ]
        return a


class PerfectDetector(Detector):
    def obs(self, perfect_alert: Alert) -> Iterable[Alert]:
        return [perfect_alert]
