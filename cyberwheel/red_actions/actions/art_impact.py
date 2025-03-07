from cyberwheel.red_actions.actions.art_killchain_phase import ARTKillChainPhase
from cyberwheel.network.host import Host

class ARTImpact(ARTKillChainPhase):
    """
    Impact Killchain Phase Attack. As described by MITRE:

    The adversary is trying to manipulate, interrupt, or destroy your systems and data.

    Impact consists of techniques that adversaries use to disrupt availability or compromise integrity by manipulating business and
    operational processes. Techniques used for impact can include destroying or tampering with data. In some cases, business processes
    can look fine, but may have been altered to benefit the adversaries' goals. These techniques might be used by adversaries to follow
    through on their end goal or to provide cover for a confidentiality breach.
    """

    name: str = "impact"

    def __init__(
        self, src_host: Host, target_host: Host, valid_techniques: list[str] = []
    ) -> None:
        super().__init__(src_host, target_host, valid_techniques=valid_techniques)
        self.action_results.action = type(self)