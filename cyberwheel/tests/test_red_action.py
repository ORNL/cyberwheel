import unittest
from cyberwheel.network.network_base import Network
from cyberwheel.network.host import Host
from cyberwheel.network.service import Service
from cyberwheel.detectors.alert import Alert
from cyberwheel.red_actions.red_base import PingSweep, RedActionResults


class TestRedActionResult(unittest.TestCase):
    def setUp(self):
        self.network = Network.create_network_from_yaml("network/example_config.yaml")
        self.action_result = RedActionResults()
        self.host = self.network.get_hosts()[0]
        self.service = self.host.services[0]
        self.alert = Alert()

    def test_red_action_result_add_host(self):
        self.action_result.add_host(self.host)
        self.assertListEqual(self.action_result.discovered_hosts, [self.host])

    def test_red_action_result_modify_alert_host(self):
        self.alert.add_dst_host(self.host)
        self.action_result.modify_alert(self.host)
        self.assertEqual(self.action_result.detector_alert, self.alert)

    def test_red_action_result_modify_alert_service(self):
        self.alert.add_service(self.service)
        self.action_result.modify_alert(self.service)
        self.assertEqual(self.action_result.detector_alert, self.alert)

    def test_red_action_result_add_successful_action(self):
        self.action_result.add_successful_action(self.host)
        self.assertListEqual(self.action_result.attack_success, [self.host])


class TestRedAction(unittest.TestCase):
    def setUp(self):
        self.network = Network.create_network_from_yaml("network/example_config.yaml")
        self.host = self.network.get_hosts()[0]
        self.src_host = self.network.get_hosts()[1]
        self.service = self.host.services[0]
        self.attack = PingSweep(self.src_host, self.service, [self.host], [])

    def test_sim_execute(self):
        action_result = self.attack.sim_execute()
        true_result = RedActionResults()
        true_result.add_host(self.host)
        true_result.add_successful_action(self.host)
        true_result.modify_alert(self.host)
        true_result.modify_alert(self.service)
        self.assertEqual(action_result, true_result)


if __name__ == "__main__":
    unittest.main()
