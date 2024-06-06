from typing import Dict, Tuple
from cyberwheel.blue_actions.dynamic_blue_base import StandaloneAction, generate_id, DynamicBlueActionReturn
from cyberwheel.network.network_base import Network

class Nothing(StandaloneAction):
    def __init__(self, network: Network, configs: Dict[str, any]) -> None:
        super().__init__(network, configs)

    def execute(self) ->  DynamicBlueActionReturn:
        return DynamicBlueActionReturn(generate_id(), True)                                                                                                                                                                                                                   
