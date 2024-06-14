"""
Module to test the EmulatorDetector class.
"""

import os
import unittest
from dotenv import load_dotenv
from cyberwheel.emulator.detectors import EmulatorDectector
from cyberwheel.emulator.siem import SiemQuery

load_dotenv()

USER = "paustria"
IP = os.getenv("SIEM_IP")


class TestEmulatorDetector(unittest.TestCase):
    """Unit tests for the the EmulatorDetector class"""

    def test_submit_obs_query(self) -> None:
        """Test observation query to SIEM"""
        eoc = EmulatorDectector()

        if IP is None:
            self.fail("SIEM IP address missing in .env")

        response = eoc.submit_obs_query(USER, IP, SiemQuery())
        self.assertIsNotNone(response)
