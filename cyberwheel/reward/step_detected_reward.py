from cyberwheel.reward.reward_base import RewardMap
from cyberwheel.reward.rl_reward import RLReward

class StepDetectedReward(RLReward):
    def __init__(
        self,
        blue_rewards: RewardMap,
        max_steps,
    ) -> None:
        """
        Reward is maximized if red agent is detected early by blue agent. The best reward it can get is
        one in which the blue agent immediately detects the red agent's actions. The worst reward it can get
        is one in which the blue agent detects the red agent at the final step of the episode.

        Reward Function: max_steps / n, where n is the number of steps

        TODO: Needs testing with recent reward changes.
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