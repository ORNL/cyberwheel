from typing import Iterable
from detectors.detector_base import Detector
from detectors.alert import Alert

class IsolateDetector(Detector):
    """A detector that only gives alerts for hosts that access decoys"""
    def obs(self, perfect_alert: Alert) -> Iterable[Alert]:
        return [perfect_alert] if perfect_alert.src_host.disconnected else []
