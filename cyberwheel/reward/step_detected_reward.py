from typing import Tuple

from cyberwheel.reward.reward_base import Reward, RewardMap
from cyberwheel.reward.recurring_reward import RecurringReward
import time

class StepDetectedReward(RecurringReward):
    def __init__(
        self,
        blue_rewards: RewardMap,
        max_steps,
    ) -> None:
        """
        Increases the reward the earlier that the red agent is detected. So the best reward it can get is
        one in which the blue agent immediately detects the red agent's actions. The worst reward it can get
        is one in which the blue agent detects the red agent at the final step of the episode.

        Reward Function: max_steps / n, where n is the number of steps
        """
        self.reward_function = max_steps * 10
        self.step_detected = 99999999
        super().__init__(
            red_rewards={},
            blue_rewards=blue_rewards,
        )

    def calculate_reward(
        self,
        red_action_alerted: bool,
        step_detected: int,
    ) -> int | float:
        step_detected_reward = 0
        if red_action_alerted and step_detected < self.step_detected:
            self.step_detected = step_detected
            step_detected_reward = self.reward_function / self.step_detected

        b = 0
        if len(self.blue_recurring_actions) < 1: # Should deploy at least 1 decoy
            b = -100
        return step_detected_reward + b + self.sum_recurring_blue()

    def reset(
        self,
    ) -> None:
        self.step_detected = 999999999
        self.blue_recurring_actions = []