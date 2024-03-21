import unittest

from cyberwheel.detectors.detector import PerfectDetector
from blueagents.observation import TestObservation
from cyberwheel.network.network_base import Network
from cyberwheel.network.service import Service
from cyberwheel.red_actions.art_techniques import NetworkServiceDiscovery
from cyberwheel.red_actions.actions.port_scan import PortScan
from cyberwheel.red_actions.actions.ping_sweep import PingSweep


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.network = Network.create_network_from_yaml("network/example_config.yaml")
        self.all_hosts = self.network.get_hosts()
        self.src_host = self.all_hosts[0]
        self.target_hosts = self.all_hosts[1:]
        self.detector = PerfectDetector()
        self.observation = TestObservation()
        self.observation.set_network(self.network)

    def test_pipeline(self):
        target_service = Service("", "", "ping", "ICMP")
        self.target_hosts[2].services = [target_service]
        self.target_hosts[1].services = [target_service]
        self.target_hosts[0].services = [target_service]
        red_action = PingSweep(self.src_host, target_service, self.target_hosts, [])

        perfect_alert = red_action.sim_execute().detector_alert
        filtered_alert = self.detector.obs(perfect_alert)
        obs_vector = self.observation.create_obs_vector(filtered_alert)

        self.assertListEqual(list(obs_vector), [0, 1, 1, 1])

    def test_pipeline_with_technique(self):
        technique = NetworkServiceDiscovery()
        target_service = Service(
            "8080", "3.4.25", "IPFilter", vulnerabilities=["CVE-2002-0515"]
        )  # Port is made up, but the vulnerability is real
        extra_service = Service("22", "", "ssh", vulnerabilities=["CVE-2020-15202"])
        self.target_hosts[2].services = [target_service]
        self.target_hosts[1].services = [extra_service]
        self.target_hosts[0].services = [extra_service, target_service]
        red_action = PortScan(
            self.src_host, target_service, self.target_hosts, [technique]
        )

        res = red_action.sim_execute()
        perfect_alert = res.detector_alert

        filtered_alert = self.detector.obs(perfect_alert)
        obs_vector = self.observation.create_obs_vector(filtered_alert)

        self.assertListEqual(list(obs_vector), [0, 1, 0, 1])


if __name__ == "__main__":
    unittest.main()
