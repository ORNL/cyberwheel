from cyberwheel.red_actions.actions.art_killchain_phase import ARTAction
from cyberwheel.network.network_base import Host

class Nothing(ARTAction):
    """
    Red action that does nothing.
    """

    name: str = "nothing"

    def __init__(self, src_host: Host, dst_host: Host) -> None:
        super().__init__(src_host, dst_host)
        self.action_results.action = type(self)
    
    def sim_execute(self):
        self.action_results.add_successful_action()
        return self.action_results