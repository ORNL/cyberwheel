import unittest
from red_actions.state_diff import StateDifference
from detectors.alert import Alert
from network.host import Host
from network.service import Service

class TestStateDifference(unittest.TestCase):
    def test_state_diff_make_alert(self):
        correct_alert  = Alert()
        state_diff = StateDifference(Host(None, None, None))
        self.assertEqual(state_diff.get_alert(), correct_alert)

    #TODO something is broken with these next two tests
    def test_state_diff_add_host(self):
        correct_alert = Alert(dst_hosts=[Host("test_host", None, None)])
        state_diff = StateDifference(Host(None, None, None))
        state_diff.add_host(Host("test_host", None, None))
        self.assertEqual(state_diff.get_alert(), correct_alert)

    def test_state_diff_add_service(self):
        correct_alert = Alert(services=[Service(None, None, "test_service")])
        state_diff = StateDifference(Host(None, None, None))
        state_diff.add_service(Service(None, None, "test_service"))
        self.assertEqual(state_diff.get_alert(), correct_alert, msg=f'{state_diff.get_alert()==correct_alert}')

if __name__ == "__main__":
    unittest.main()