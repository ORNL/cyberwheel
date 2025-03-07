from cyberwheel.red_actions.actions.art_killchain_phase import ARTKillChainPhase
from cyberwheel.network.host import Host

class ARTDiscovery(ARTKillChainPhase):
    """
    Discovery Killchain Phase Attack. As described by MITRE:

    The adversary is trying to figure out your environment.

    Discovery consists of techniques an adversary may use to gain knowledge about the system and internal network.
    These techniques help adversaries observe the environment and orient themselves before deciding how to act.
    They also allow adversaries to explore what they can control and what's around their entry point in order to
    discover how it could benefit their current objective. Native operating system tools are often used toward
    this post-compromise information-gathering objective.
    """

    name: str = "discovery"

    def __init__(
        self, src_host: Host, target_host: Host, valid_techniques: list[str] = []
    ) -> None:
        super().__init__(src_host, target_host, valid_techniques=valid_techniques)
        self.action_results.action = type(self)

    def sim_execute(self):
        super().sim_execute()
        if self.action_results.attack_success:
            self.action_results.add_metadata(
                self.target_host.name,
                {"type": self.target_host.host_type.name},
            )
        return self.action_results