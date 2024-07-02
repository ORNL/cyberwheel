from typing import List, Tuple

from cyberwheel.reward.reward_base import (
    Reward,
    RewardMap,
    RecurringAction,
    calc_quadratic,
)


class DecoyReward(Reward):
    def __init__(
        self,
        red_rewards: RewardMap,
        blue_rewards: RewardMap,
        r: Tuple[int, int] = (0, 10),
        scaling_factor: float = 10.0,
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

        super().__init__(red_rewards, blue_rewards)
        self.blue_recurring_actions: List[RecurringAction] = []
        self.red_recurring_actions= []
        self.range = r
        self.scaling_factor = scaling_factor

    def calculate_reward(
        self,
        red_action: str,
        blue_action: str,
        red_success: str,
        blue_success: bool,
        red_action_alerted: bool,
    ) -> int | float:
        if red_action_alerted:
            r = abs(self.red_rewards[red_action][0]) * self.scaling_factor * 10
        elif red_success:
            r = self.red_rewards[red_action][0]
            # self.handle_red_action_output(red_action)
        else:
            r = 0

        if blue_success:
            b = self.blue_rewards[blue_action][0]
        else:
            b = -100 * self.scaling_factor
        return r + b + self.sum_recurring_blue() + self.sum_recurring_red()

    def sum_recurring_blue(self) -> int | float:
        sum = 0
        for ra in self.blue_recurring_actions:
            sum += self.blue_rewards[ra.action][1]

        # Subtract the distance times the scaling factor away from the range
        if len(self.blue_recurring_actions) > self.range[1]:
            x = len(self.blue_recurring_actions) - self.range[1]
            sum -= calc_quadratic(x, a=self.scaling_factor)
        elif len(self.blue_recurring_actions) < self.range[0]:
            x = self.range[0] - len(self.blue_recurring_actions)
            sum -= calc_quadratic(x, a=self.scaling_factor)
        
        if len(self.blue_recurring_actions) == 0:
            sum = -100
        return sum

    def add_recurring_blue_action(self, id: str, action: str) -> None:
        self.blue_recurring_actions.append(RecurringAction(id, action))

    def remove_recurring_blue_action(self, name: str) -> None:
        for i in range(len(self.blue_recurring_actions)):
            if self.blue_recurring_actions[i].id == name:
                self.blue_recurring_actions.pop(i)
                break

    def sum_recurring_red(self) -> int | float:
        sum = 0
        for ra in self.red_recurring_actions:
            if ra[1]:
                sum -= self.red_rewards[ra[0].action][1] * self.scaling_factor * 10
            else:
                sum += self.red_rewards[ra[0].action][1]
        return sum

    def add_recurring_red_impact(self, red_action, is_decoy) -> None:
        self.red_recurring_actions.append((RecurringAction("", red_action), is_decoy))

    def handle_blue_action_output(self, blue_action: str, rec_id: str, success: bool, recurring: int):
        if not success:
            return
        
        if recurring == -1:
            self.remove_recurring_blue_action(rec_id)
        elif recurring == 1:
            self.add_recurring_blue_action(rec_id, blue_action)
        elif recurring:
            raise ValueError("recurring must be either -1, 0, or 1")
    
    def handle_red_action_output(self, red_action: str, is_decoy):
        if "impact" in red_action.lower():
            self.add_recurring_red_impact(red_action.lower(), is_decoy)
        return

    def reset(self) -> None:
        self.blue_recurring_actions = []
        self.red_recurring_actions = []
