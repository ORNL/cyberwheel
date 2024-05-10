from typing import Tuple

from cyberwheel.reward.reward_base import Reward, RewardMap

class StepDetectedReward(Reward):
    def __init__(
        self,
        blue_rewards: RewardMap,
    ) -> None:
        """
        Increases the reward the earlier that the red agent is detected. So the best reward it can get is
        one in which the blue agent immediately detects the red agent's actions. The worst reward it can get
        is one in which the blue agent detects the red agent at the final step of the episode.

        reward function: 100 - n (n is the step detected)

        trying 1000 / n

        TODO: Change 100, 200 to max_steps and max_steps * 2, respectively.
        """
        self.reward_function = 1000
        self.step_detected = 99999999
        super().__init__(
            red_rewards={},
            blue_rewards=blue_rewards,
        )


    def calculate_reward(
        self,
        blue_action: str,
        blue_success: bool,
        red_action_alerted: bool,
        step_detected: int,
    ) -> int | float:
        step_detected_reward = 0
        if red_action_alerted and step_detected < self.step_detected:
            self.step_detected = step_detected
            step_detected_reward = self.reward_function / self.step_detected

        if blue_success:
            b = self.blue_rewards[blue_action.split(" ")[0]][0]
        else:
            b = 0
        # print(f"Step Detected: {self.step_detected}, Step Detected Reward: {step_detected_reward}, Blue Agent: {b}, Recurring: {self.sum_recurring()}")
        return step_detected_reward + b + self.sum_recurring()

    def reset(
        self,
    ) -> None:  # TODO: Change 100, 200 to max_steps and max_steps * 2, respectively.
        self.reward_function = 1000
        self.step_detected = 999999999
        self.blue_recurring_actions = []