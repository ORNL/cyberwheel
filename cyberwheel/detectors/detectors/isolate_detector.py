from typing import Iterable
from cyberwheel.detectors.alert import Alert
from cyberwheel.detectors.detector_base import Detector

class IsolateDetector(Detector):
    """A detector that only gives alerts for hosts that access decoys"""

    name = "IsolateDetector"
    def obs(self, perfect_alerts: Iterable[Alert]) -> Iterable[Alert]:
        
        alert = []
        for perfect_alert in perfect_alerts:
            if perfect_alert.src_host.disconnected: 
                alert = [perfect_alert]  
            else:
                for dst in perfect_alert.dst_hosts:
                    if dst.disconnected:
                        alert.append(Alert(perfect_alert.src_host, dst_hosts=[dst]))
        return alert
