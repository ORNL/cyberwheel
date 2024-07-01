"""
Module defines the class to execute actions in the emulator.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from cyberwheel.red_actions.red_base import RedAction, RedActionResults

class EmulateRedAction(RedAction, ABC):
    """
    Abstract class to exeucte actions in the emulator.
    User needs to implement emulate_execute().
    """
    def sim_execute(self) -> type[NotImplementedError]:
        """Not used in emulator"""
        return NotImplementedError

    def perfect_alert(self):
        """Not used in emulator"""

    @abstractmethod
    def emulator_execute(self) -> RedActionResults | type[NotImplementedError]:
        """Execute action in emulator."""
        raise NotImplementedError
