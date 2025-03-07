import random

from cyberwheel.red_agents.strategies.red_strategy import RedStrategy
from cyberwheel.network.host import Host


class DFSImpact(RedStrategy):
    """
    The DFS Impact strategy is to attack the current host until it's impacted,
    move to another random unimpacted host, and repeat.
    """
    @classmethod
    def select_target(cls, agent_obj) -> Host:
        """
        If current host has been impacted: choose a random other unimpacted host
        Else: Continue attacking current host
        """
        if (
            agent_obj.history.hosts[agent_obj.current_host.name].last_step
            == len(agent_obj.killchain) - 1
        ):
            return agent_obj.network.hosts[agent_obj.unimpacted_hosts.get_random()]
        return agent_obj.current_host
