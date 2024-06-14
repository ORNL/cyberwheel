"""
Module defines the Emulator History Observation class and is used to convert the
SIEM reponse from the emulator into the (history) observation space.
This module is equivlaent to the Observation Converter in paper diagrams.
"""

from typing import Dict, Iterable
import numpy as np
from cyberwheel.detectors.alert import Alert
from cyberwheel.network.host import Host
from cyberwheel.observation.observation import Observation


class EmulatorHistoryObservation(Observation):
    """
    Class to convert response from the SIEM and generate an obervation space that
    includes detector history values.
    """

    def __init__(self, shape: int, mapping: Dict[Host, int]) -> None:
        self.shape = shape
        self.mapping = mapping
        self.obs_vec = np.zeros(shape)

    def create_obs_vector(self, alerts: Iterable[Alert]) -> Iterable:
        """
        Converts the SIEM response into the observation vector for the Agent
        to consume.
        """

        # return the obersvation space vector
        return [0]

    def reset_obs_vector(self) -> Iterable:
        """Zeros out observation vector."""
        self.obs_vec = np.zeros(self.shape)
        return self.obs_vec
