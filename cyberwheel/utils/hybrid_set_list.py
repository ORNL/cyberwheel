import random
import os

from typing import Iterable, Any

class HybridSetList:
    """
    Defines a Hybrid Set/List object. This allows us to take advantage of the O(1) time complexity for
    membership checking of sets, while taking advantage of the O(1) time complexity of random.choice()
    of lists.
    """

    def __init__(self, data: Iterable = None):
        if data:
            self.data_set = set(data)
            self.data_list = list(data)
        else:
            self.data_set = set()
            self.data_list = []
        self.seed = 0
        self.deterministic = os.getenv("CYBERWHEEL_DETERMINISTIC", "False").lower() in ('true', '1', 't')
    
    def __iter__(self):
        return iter(self.data_list)
    
    def __getitem__(self, i: int):
        return self.data_list[i]
    
    def __contains__(self, item: Any):
        return item in self.data_set
    
    def __len__(self):
        return len(self.data_set)

    def add(self, value: Any):
        if value not in self.data_set:
            self.data_set.add(value)
            self.data_list.append(value)

    def remove(self, value: Any):
        if value in self.data_set:
            self.data_set.remove(value)
            self.data_list.remove(value)

    def get_random(self):
        if self.deterministic:
            #print(self.seed)
            random.seed(self.seed)
            self.seed += 1
            return random.choice(self.data_list)
        else:
            return random.choice(self.data_list)
    
    def reset(self):
        self.data_set = set()
        self.data_list = []