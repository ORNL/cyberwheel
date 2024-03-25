from abc import abstractmethod
from typing import Iterable, Tuple, Dict
import numpy as np
from gymnasium import spaces

from cyberwheel.network.network_base import Network
from cyberwheel.network.host import Host
from cyberwheel.detectors.alert import Alert


#
class AlertsConversion:
    """
    A base class for converting from detector produced alerts to blue observations.
    Hopefully, this can be used to create different observation vectors easily.
    """

    @abstractmethod
    def create_obs_vector(self, alerts: Iterable[Alert]) -> Iterable:
        """create_obs_vector() maps alerts to the blue observation space represented by a vector"""
        pass

    def reset_obs_vector(self) -> Iterable:
        """Resets the obs_vector and returns the observation of the initial state"""

    def set_network(self, network: Network) -> None:
        self.network = network


class TestObservation(AlertsConversion):
    def create_obs_vector(self, alerts: Iterable) -> Iterable:
        num_hosts = sum(
            isinstance(data_object, Host)
            for _, data_object in self.network.graph.nodes(data="data")
        )
        observation_vector = np.zeros(num_hosts, dtype=np.int8)
        index = 0
        for _, data_object in self.network.graph.nodes(data="data"):
            if not isinstance(data_object, Host):
                continue
            for alert in alerts:
                if data_object in alert.dst_hosts:
                    observation_vector[index] = 1
            index += 1
        return observation_vector
    
class HistoryObservation(AlertsConversion):
    def __init__(self, _len: int, mapping: Dict[Host, int])-> None:
        self.len = _len
        self.mapping = mapping
        self.obs_vec = np.zeros((2, self.len))

    def create_obs_vector(self, alerts: Iterable[Alert]) -> Iterable:
        # Refresh the non-history portion of the obs_vec
        self.obs_vec[0] = np.zeros(self.len)
        for alert in alerts:
            alerted_host = alert.src_host
            index = self.mapping[alerted_host]
            self.obs_vec[0][index] = 1
            self.obs_vec[1][index] = 1
        return self.obs_vec
    
    def reset_obs_vector(self) -> Iterable:
        self.obs_vec = np.zeros((2,self.len))
        return self.obs_vec



        

