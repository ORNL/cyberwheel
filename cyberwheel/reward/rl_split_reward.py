from cyberwheel.red_actions.actions import (
    ARTPingSweep,
    ARTPortScan,
    ARTDiscovery,
    ARTLateralMovement,
    ARTPrivilegeEscalation,
    ARTImpact
)
from cyberwheel.reward.reward_base import Reward

class RLSplitReward(Reward):
    """
    Splits reward function depending on how much of the network red agent has explored.
    TODO: Needs testing
    """
    def __init__(
        self,
        red_rewards,
        blue_rewards
    ) -> None:
        self.red_exploration_rewards = {
            ARTPingSweep.get_name(): (0, 0),
            ARTPortScan.get_name(): (0, 0),
            ARTDiscovery.get_name(): (200, 0),
            ARTLateralMovement.get_name(): (0, 0),
            ARTPrivilegeEscalation.get_name(): (0, 0),
            ARTImpact.get_name(): (0, 0),
        }
        self.red_exploitation_rewards = {
            ARTPingSweep.get_name(): (0, 0),
            ARTPortScan.get_name(): (0, 0),
            ARTDiscovery.get_name(): (0, 0),
            ARTLateralMovement.get_name(): (0, 0),
            ARTPrivilegeEscalation.get_name(): (0, 0),
            ARTImpact.get_name(): (200, 0),
        }

        super().__init__(
            red_rewards, 
            blue_rewards
        )

    def calculate_reward(
        self,
        red_action: str,
        blue_action: str,
        red_success: str,
        blue_success: bool,
        decoy: bool,
        observation: dict
    ) -> int | float:
        done_exploring = True
        for hostname in observation:
            if not observation[hostname].discovered:
                done_exploring = False
                break
        if done_exploring and red_success:
            r = self.red_exploitation_rewards[red_action][0]
        elif not done_exploring and red_success:
            r = self.red_exploration_rewards[red_action][0]
        else:
            r = 0

        b = 0 

        return r + b

    def reset(self) -> None:
        self.blue_recurring_actions = []
        self.red_recurring_actions = []
