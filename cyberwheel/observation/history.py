import numpy as np
from typing import Dict, Iterable

from cyberwheel.detectors.alert import Alert
from cyberwheel.network.host import Host
from cyberwheel.observation.observation import Observation

class HistoryObservation(Observation):
    def __init__(self, shape: int, mapping: Dict[Host, int]) -> None:
        self.shape = shape
        self.mapping = mapping
        self.obs_vec = np.zeros(shape)

    def create_obs_vector(self, alerts: Iterable[Alert]) -> Iterable:
        # Refresh the non-history portion of the obs_vec
        obs_length = len(self.obs_vec)
        barrier = obs_length // 2
        for i in range(barrier):
            self.obs_vec[i] = 0
        for alert in alerts:
            alerted_host = alert.src_host
            if alerted_host.name not in self.mapping:
                continue
            index = self.mapping[alerted_host.name]
            self.obs_vec[index] = 1
            self.obs_vec[index + barrier] = 1
        return self.obs_vec

    def reset_obs_vector(self) -> Iterable:
        self.obs_vec = np.zeros(self.shape)
        return self.obs_vec