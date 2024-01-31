import unittest

from detectors.alert import Alert
from detectors.detector import PerfectDetector
from red_actions.red_base import PingSweep
from blueagents.observation import TestObservation
from network.network_base import Network
from network.service import Service

class TestPipeline(unittest.TestCase):
    def test_pipeline(self): 
        network = Network.create_network_from_yaml('network/example_config.yaml')
        all_hosts = network.get_hosts()
        src_host = all_hosts[0]
        target_hosts = all_hosts[1:]
        target_service = Service("", "", "ping", "ICMP")
        
        red_action = PingSweep(src_host, target_service, target_hosts, [])
        detector = PerfectDetector()
        observation = TestObservation()
        observation.set_network(network)
        
        perfect_alert = red_action.sim_execute().detector_alert
        filtered_alert = detector.obs(perfect_alert)
        obs_vector = observation.create_obs_vector(filtered_alert)
        self.assertListEqual(list(obs_vector), [0,1,1,1])

if __name__ == "__main__":
    unittest.main()