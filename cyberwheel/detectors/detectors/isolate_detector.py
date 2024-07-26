from typing import Iterable
from cyberwheel.detectors.detector_base import Detector
from cyberwheel.detectors.alert import Alert


class IsolateDetector(Detector):
    """A detector that only gives alerts for hosts that access decoys"""

    def obs(self, perfect_alert: Alert) -> Iterable[Alert]:

        alert = []
        if perfect_alert.src_host.disconnected:
            alert = [perfect_alert]
        else:
            for dst in perfect_alert.dst_hosts:
                if dst.disconnected:
                    alert.append(Alert(perfect_alert.src_host, dst_hosts=[dst]))
        return alert
