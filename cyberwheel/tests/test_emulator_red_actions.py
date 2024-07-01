"""
Module to test the red actions in the emulator.
"""

import unittest
from cyberwheel.emulator.actions.red_actions import EmulatePingSweep
from cyberwheel.network.host import Host
from cyberwheel.network.router import Router
from cyberwheel.network.service import Service
from cyberwheel.network.subnet import Subnet

# setup network for tests
router = Router(name="192.168.1.0")
subnet = Subnet(name="192.168.1.0", ip_range="192.168.1.0", router=router)
host = Host(name="test", subnet=subnet, host_type=None)

class TestEmulatorRedActions(unittest.TestCase):
    """Unit tests for the the emulator red actions"""

    def test_ping_sweep(self) -> None:
        """
        Test ping sweep in emulator.
        """
        red_action = EmulatePingSweep(src_host=host,
                                      target_service=Service,
                                      target_hosts=[host],
                                      techniques=[])
        print(EmulatePingSweep.get_name())

        results = red_action.emulator_execute(start_host=1,
                                              end_host=3,
                                              subnet="192.168.1")

        self.assertIsNotNone(results.attack_success)
