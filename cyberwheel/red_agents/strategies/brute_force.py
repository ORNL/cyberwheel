from cyberwheel.red_agents.strategies.red_strategy import RedStrategy


class BruteForce(RedStrategy):
    """
    The Brute Force strategy is to attack the same host over and over.
    """
    @classmethod
    def select_target(cls, agent_obj):
        """
        Attack the host it's already on.
        """
        return agent_obj.current_host