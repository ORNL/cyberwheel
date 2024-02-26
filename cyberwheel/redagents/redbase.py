import networkx as nx
import numpy as np
from abc import ABC, abstractmethod


class RedAgentBase(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def act(self):
        pass
