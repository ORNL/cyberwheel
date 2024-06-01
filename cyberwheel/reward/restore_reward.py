from typing import List, Tuple

from cyberwheel.reward.reward_base import Reward, RewardMap, RecurringAction, calc_quadratic

class RestoreReward(Reward):
    def __init__(
        self,
        red_rewards: RewardMap,
        blue_rewards: RewardMap,
    ) -> None:
        super().__init__(red_rewards, blue_rewards)

    def calculate_reward(
        self,
        red_action: str,
        blue_action: str,
        red_success: str,
        blue_success: bool,
    ) -> int | float:
        if red_success:
            r = self.red_rewards[red_action][0]
        else:
            r = -1 * self.red_rewards[red_action][0]

        if blue_success:
            b = self.blue_rewards[blue_action][0]
        else:
            b = -1 * self.blue_rewards[blue_action][0]
        
        # print(r,b, red_action, blue_action)
        return r + b

    def reset(self) -> None:
        return