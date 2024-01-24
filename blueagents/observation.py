from abc import abstractmethod
from typing import List
import numpy as np

from network.network_base import Network
from network.host import Host
from detectors.alert import Alert


# 
class AlertsConversion():
    """
    A base class for converting from detector produced alerts to blue observations.
    Hopefully, this can be used to create different observation vectors easily. 
    """
    @abstractmethod
    def create_obs_vector(self, alerts: List[Alert])-> List:
        """create_obs_vector() maps alerts to the blue observation space represented by a vector"""
        pass
    
    def set_network(self, network: Network)-> None:
        self.network = network

class TestObservation(AlertsConversion):
    def create_obs_vector(self, alerts: List[Alert]) -> List:
        num_hosts = sum(isinstance(data_object, Host) for _, data_object in self.network.graph.nodes(data='data'))
        observation_vector = np.zeros(num_hosts, dtype=np.int8)

        index = 0
        # for _, data_object in self.network.graph.nodes(data='data'):
        #     if isinstance(data_object, Host):
        #         is_compromised = data_object.is_compromised
        #         observation_vector[index] = 1 if is_compromised else 0
        #         index += 1

        for _, data_object in self.network.graph.nodes(data='data'):
            if not isinstance(data_object, Host):
                index += 1
                continue
            for alert in alerts:
                if data_object in alert.dst_hosts:
                    observation_vector[index] = 1
            index += 1


        return observation_vector