from abc import ABC, abstractmethod
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