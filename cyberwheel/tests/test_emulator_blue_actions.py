"""
Module to test the EmulatorDetector class.
"""

import unittest
from cyberwheel.emulator.actions.blue_actions import EmulateDeployDecoyHost
from cyberwheel.network.network_base import Network

class TestEmulatorBlueActions(unittest.TestCase):
    """Unit tests for the the emulator blue actions"""

    def test_deploy_decoy_host(self) -> None:
        """Test deploying decoy hosts in emulator"""
        decoy = EmulateDeployDecoyHost(network=Network("test"), configs={})
        action_result = decoy.execute()
        self.assertTrue(action_result.success)
