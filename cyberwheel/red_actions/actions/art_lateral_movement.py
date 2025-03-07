from cyberwheel.red_actions.actions.art_killchain_phase import ARTKillChainPhase
from cyberwheel.network.host import Host

class ARTLateralMovement(ARTKillChainPhase):
    """
    LateralMovement Killchain Phase Attack. As described by MITRE:

    The adversary is trying to move through your environment.

    Lateral Movement consists of techniques that adversaries use to enter and control remote systems on a network.
    Following through on their primary objective often requires exploring the network to find their target and
    subsequently gaining access to it. Reaching their objective often involves pivoting through multiple systems
    and accounts to gain. Adversaries might install their own remote access tools to accomplish Lateral Movement
    or use legitimate credentials with native network and operating system tools, which may be stealthier.
    """

    name: str = "lateral-movement"

    def __init__(
        self, src_host: Host, target_host: Host, valid_techniques: list[str] = []
    ) -> None:
        super().__init__(src_host, target_host, valid_techniques=valid_techniques)
        self.action_results.action = type(self)