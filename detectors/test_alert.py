import unittest
import numpy as np
from alert import Alert
from network.host import Host
from network.service import Service
from detector import PerfectDetector
from network.network_base import Network
from blueagents.observation import TestObservation

class TestAlertMethods(unittest.TestCase):

    def test_to_dict(self):
        self.maxDiff=None
        src_host = Host("Host1", "Workstation", "Subnet1")
        dst_hosts = [Host("Host2", "Workstation", "Subnet2"), Host("Host1", "Workstation", "Subnet2"), Host("Host1", "Printer", "Subnet2")]
        local_services = [Service("1", "0.0", "foo")]
        remote_services = [Service("2", "0.0", "bar")]
        alert = Alert(src_host, dst_hosts, local_services, remote_services)
        t = {"src_host": src_host,
             "dst_hosts": dst_hosts,
             "local_services": local_services,
             "remote_services": remote_services}
        self.assertDictEqual(alert.to_dict(), t)

    def test_detector(self):
        detector = PerfectDetector()
        src_host = Host("Host1", "Workstation", "Subnet1")
        dst_hosts = [Host("Host2", "Workstation", "Subnet2"), Host("Host1", "Workstation", "Subnet2"), Host("Host1", "Printer", "Subnet2")]
        local_services = [Service("1", "0.0", "foo")]
        remote_services = [Service("2", "0.0", "bar")]
        perfect_alert = Alert(src_host, dst_hosts, local_services, remote_services)
        new_alert = detector.obs(perfect_alert)
        t = [perfect_alert]
        self.assertListEqual(new_alert, t)

    def test_observation(self):
        network = Network.create_network_from_yaml('network/config.yaml')
        detector = PerfectDetector()
        src_host = Host("Host1", "Workstation", "Subnet1")
        dst_hosts = [Host("HostA1", "Workstation", "Subnet2"), Host("HostC2", "Workstation", "Subnet2"), Host("Host1", "Printer", "Subnet2")]
        local_services = [Service("1", "0.0", "foo")]
        remote_services = [Service("2", "0.0", "bar")]
        perfect_alert = Alert(src_host, dst_hosts, local_services, remote_services)
        new_alert = detector.obs(perfect_alert)
        observation = TestObservation()
        observation.set_network(network)
        observation_vector = observation.create_obs_vector(new_alert)
        num_hosts = sum(isinstance(data_object, Host) for _, data_object in network.graph.nodes(data='data'))
        t = np.zeros(num_hosts, dtype=np.int8)
        t[7] = 1
        t[18] = 1
        self.assertListEqual(list(observation_vector),list(t))


if __name__ == "__main__":
    unittest.main()