from abc import ABC, abstractmethod

class CustomSharedData(ABC):
    """
    An abstract base class for defining custom shared data to use with the dynamic blue agent. All custom shared data objects should have
    a `clear()` method that resets the object's member variables to their default value. `clear()` is called whenever the environment resets.
    """
    @abstractmethod
    def clear(self):
        raise NotImplementedError
