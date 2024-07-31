from ..blue_action import CustomSharedData
from cyberwheel.network.host import Host
from cyberwheel.network.subnet import Subnet

class IsolateData(CustomSharedData):
    def __init__(self, **kwargs):
        self.size: int = kwargs.get("size", 10)
        self.decoys = []

    def __getitem__(self, k):
        return self.decoys[k]

    def __len__(self):
        return len(self.decoys)

    def append_decoy(self, decoy: Host, subnet: Subnet)-> bool:
        if len(self.decoys) >= self.size:
            return False
        self.decoys.append((decoy, subnet))
        return True

    def clear(self):
        self.decoys.clear()