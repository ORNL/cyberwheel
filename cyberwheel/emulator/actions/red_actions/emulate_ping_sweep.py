"""
Module defines the class to execute ping sweep action in the emulator.
"""

from __future__ import annotations
import os
import subprocess
from cyberwheel.red_actions.red_base import RedActionResults
from cyberwheel.emulator.actions import stdout_to_list
from .emulate_red_action_base import EmulateRedAction

file_path = os.path.realpath(__file__)
dir_name = os.path.dirname(file_path)

class EmulatePingSweep(EmulateRedAction):
    """
    Class to exeucte ping sweep in the emulator.
    """
    name = "Remote System Discovery - sweep"

    def emulator_execute(self,
                         start_host: int=1,
                         end_host: int=254,
                         subnet: str="192.168.1"
        ) -> RedActionResults:
        """
        Execute ping sweep in the emulator. Discovered IP addresses are added to
        discovered hosts in RedActionResults.

        Argruments:
            start_host - start ip range value (e.g. 1)
            end_host - end ip range value (e.g. start_host< value <=254)
            subnet - host subnet (e.g. 192.168.1)
        """
        command = [
            f"{dir_name}/scripts/linux_ping_sweep.sh",
            f"{start_host}",
            f"{end_host}",
            f"{subnet}",
        ]
        print("command", command)

        # execute command
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        # capture output after executing command
        if result.returncode != 0:
            print(result.stderr)
        else:
            output = result.stdout
            discovered_ips = stdout_to_list(output)
            print("discovered ips: ", discovered_ips)

        # TODO convert IPs to [Host] and add to action_results

        return self.action_results
