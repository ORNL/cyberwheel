from cyberwheel.red_agents.strategies.red_strategy import RedStrategy
from cyberwheel.network.host import Host


class Exfiltration(RedStrategy):
    """
    The Exfiltration strategy is to find and impact a specific host in the network.
    Once it discovers it (runs Discovery on it), it will impact it.
    """
    @classmethod
    def select_target(cls, agent_obj) -> Host:
        """
        It should continue impacting the current host if: it is Unknown or if it is the Target. Otherwise it should move to another host.
        It should prioritize attacking other Servers that are unimpacted in its view. Then it should prioritize Unknown hosts in its view.
        """
        current_host_type = agent_obj.history.hosts[agent_obj.current_host.name].type
        target_host = agent_obj.current_host
        if (
            current_host_type == "Unknown"
            or agent_obj.history.hosts[agent_obj.current_host.name].is_leader
        ):
            target_host = agent_obj.current_host
        elif len(agent_obj.unknowns) > 0:
            target_host = agent_obj.network.hosts[agent_obj.unknowns.get_random()]
        return target_host