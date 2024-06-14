"""
Module defines the Emulator Dectectory class.
"""

from __future__ import annotations
from subprocess import CompletedProcess
from typing import Any, Iterable
import json
import subprocess
from cyberwheel.detectors.alert import Alert
from cyberwheel.detectors.detector import Detector
from cyberwheel.emulator.siem import SiemQuery


class EmulatorDectector(Detector):
    """
    Class to communicate with SIEM (elasticsearch) within the emulator.
    The detector, Sysmon, fowards information to the SIEM.
    """

    def query_to_json(self, result: CompletedProcess[str]) -> Any | None:
        """Converts SIEM query reponse to JSON."""
        return json.loads(result.stdout)

    def submit_test_query(
        self, user: str, ip: str, query: SiemQuery
    ) -> CompletedProcess[str] | None:
        """SSHs into the host with the SIEM and submits a query."""
        command = [
            "ssh",
            f"{user}@{ip}",
            f"curl -u elastic:elastic -X GET http://localhost:9200/{query.is_alive()}",
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        if result.returncode != 0:
            error = {"error": result.stderr}
            print(json.dumps(error))
            return None

        return result

    def submit_obs_query(
        self, user: str, ip: str, query: SiemQuery
    ) -> CompletedProcess[str] | None:
        """Shells into the SIEM VM and submits a query to get the oberstation state."""
        command = [
            "ssh",
            f"{user}@{ip}",
            f"curl -u elastic:elastic \
            X GET \
            http://localhost:9200/logs-sysmon_linux.log-*/_search?size=1000 \
            -H 'kbn-xsrf: reporting' \
            -H 'Content-Type: application/json' \
            -d '{query.get_observation()}'",
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        if result.returncode != 0:
            error = {"error": result.stderr}
            print(json.dumps(error))
            return None

        return result

    def obs(self, perfect_alert: Alert) -> Iterable[Alert]:
        """
        Creates an array of alerts using information from the SIEM's query response.
        TODO: implement
        """
        alerts = []
        return alerts
