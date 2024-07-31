from typing import Dict, Tuple
from cyberwheel.blue_actions.blue_action import StandaloneAction, generate_id, BlueActionReturn
from cyberwheel.network.network_base import Network

class Nothing(StandaloneAction):
    def __init__(self, network: Network, configs: Dict[str, any], **kwargs) -> None:
        super().__init__(network, configs)

    def execute(self, **kwargs) ->  BlueActionReturn:
        return BlueActionReturn(generate_id(), True)                                                                                                                                                                                                                   
