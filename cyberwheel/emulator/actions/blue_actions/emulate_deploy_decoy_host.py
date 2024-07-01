"""
Module defines the class to deploy a decoy in the emulator.
"""

from __future__ import annotations
import subprocess
from cyberwheel.emulator.actions import stdout_to_list
from cyberwheel.blue_actions.dynamic_blue_base import (DynamicBlueAction,
                                                       DynamicBlueActionReturn,
                                                       generate_id)

class EmulateDeployDecoyHost(DynamicBlueAction): #pylint: disable=too-few-public-methods
    """
    Class deploy decoy in the emulator.
    """
    def execute(self) -> DynamicBlueActionReturn:
        """
        Exeucute deploying a decoy in the emulator.
        Current implementation connects a virtual machine to the router.
        """
        name = generate_id()

        # TODO add commands to connect VM to router in Firewheel
        command = [ "pwd" ]
        print("command: ", command)

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
            values = stdout_to_list(output)
            print("values: ", values)

        return DynamicBlueActionReturn(name, True, 1)
