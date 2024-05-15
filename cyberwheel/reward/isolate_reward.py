from typing import Dict, List, NewType, Tuple

from cyberwheel.reward.reward import RewardCalculator, RewardMap

class IsolateReward(RewardCalculator):
    def __init__(
        self,
        red_rewards: RewardMap,
    ) -> None:
        """
        Increases the negative reward if the number of recurring actions is less than `r[0]` or greater than `r[1]`.
        If this number falls within the range, the sum of the recurring rewards is calculated normally. Otherwise,
        the cost of these actions increases scaling based on how far it is from the range. This is meant to prevent two things:

        1. the agent always choosing to do nothing instead of deploying hosts.
        2. the agent spamming decoys (20 decoys on a network of a dozen or so hosts is a bit absurd)

        It is important to note that the number of recurring actions is not strictly bound to `range`. The agent could
        create fewer or more recurring actions.

        `scaling_factor` impacts how much being outside `r` affects the reward
        """
        self.red_rewards = red_rewards

    def calculate_reward(
        self,
        red_action: str,
        blue_success: bool,
        red_action_alerted: bool,
    ) -> int | float:
        if red_action_alerted:
            r = abs(self.red_rewards[red_action][0])
        else:
            r = self.red_rewards[red_action][0]
        b = 0
        if not blue_success:
            b = -100
        return r + b


    def reset(self) -> None:
        self.blue_recurring_actions = []
        self.red_recurring_impacts = 0