import unittest
import numpy as np
from cyberwheel.detectors.alert import Alert
from cyberwheel.network.host import Host
from cyberwheel.network.service import Service
from cyberwheel.detectors.detector import PerfectDetector
from cyberwheel.network.network_base import Network
from blueagents.observation import TestObservation


class TestAlert(unittest.TestCase):
    def test_alert_to_dict(self):
        self.maxDiff = None
        src_host = Host("Host1", "Workstation", None)
        dst_hosts = [
            Host("Host2", "Workstation", None),
            Host("Host1", "Workstation", None),
            Host("Host1", "Printer", None),
        ]
        services = [Service("2", "0.0", "bar")]
        alert = Alert(src_host, dst_hosts, services)
        t = {"src_host": src_host, "dst_hosts": dst_hosts, "services": services}
        self.assertDictEqual(alert.to_dict(), t)

    def test_alert_detector(self):
        detector = PerfectDetector()
        src_host = Host("Host1", "Workstation", None)
        dst_hosts = [
            Host("Host2", "Workstation", None),
            Host("Host1", "Workstation", None),
            Host("Host1", "Printer", None),
        ]
        services = [Service("2", "0.0", "bar")]
        perfect_alert = Alert(src_host, dst_hosts, services)
        new_alert = detector.obs(perfect_alert)
        t = [perfect_alert]
        self.assertListEqual(new_alert, t)  # type: ignore

    def test_alert_add_host(self):
        correct_alert = Alert(dst_hosts=[Host("test_host", None, None)])
        test_alert = Alert()
        test_alert.add_dst_host(Host("test_host", None, None))
        self.assertEqual(test_alert, correct_alert)

    def test_alert_add_service(self):
        correct_alert = Alert(services=[Service(None, None, "test_service")])
        test_alert = Alert()
        test_alert.add_service(Service(None, None, "test_service"))
        self.assertEqual(test_alert, correct_alert)


if __name__ == "__main__":
    unittest.main()
