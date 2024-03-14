import json
import random
import yaml

from typing import List

from cyberwheel.blue_actions.blue_base import BlueAction
from cyberwheel.network.network_base import Network
from cyberwheel.network.host import Host, HostType
from cyberwheel.network.service import Service
from cyberwheel.network.subnet import Subnet


class DeployDecoyFile(BlueAction):
    def __init__(self, host: Host, reward=0, recurring_reward=0) -> None:
        super().__init__(reward, recurring_reward)
        
    

    