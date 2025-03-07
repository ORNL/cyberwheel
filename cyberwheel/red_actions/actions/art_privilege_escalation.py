from cyberwheel.red_actions.actions.art_killchain_phase import ARTKillChainPhase
from cyberwheel.network.host import Host

class ARTPrivilegeEscalation(ARTKillChainPhase):
    """
    PrivilegeEscalation Killchain Phase Attack. As described by MITRE:

    The adversary is trying to gain higher-level permissions.

    Privilege Escalation consists of techniques that adversaries use to gain higher-level permissions on a system or network.
    Adversaries can often enter and explore a network with unprivileged access but require elevated permissions to follow
    through on their objectives. Common approaches are to take advantage of system weaknesses, misconfigurations, and
    vulnerabilities. Examples of elevated access include:
    - SYSTEM/root level
    - local administrator
    - user account with admin-like access
    - user accounts with access to specific system or perform specific function

    These techniques often overlap with Persistence techniques, as OS features that let an adversary persist can execute in an elevated context.
    """

    name: str = "privilege-escalation"

    def __init__(
        self, src_host: Host, target_host: Host, valid_techniques: list[str] = []
    ) -> None:
        super().__init__(src_host, target_host, valid_techniques=valid_techniques)
        self.action_results.action = type(self)