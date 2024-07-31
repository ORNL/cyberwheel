from typing import List, Tuple

from cyberwheel.reward.reward_base import Reward, RewardMap, RecurringAction, calc_quadratic

class RecurringReward(Reward):
    def __init__(
        self,
        red_rewards: RewardMap,
        blue_rewards: RewardMap,
    ) -> None:
        super().__init__(red_rewards, blue_rewards)
        self.blue_recurring_actions: List[RecurringAction] = []
        self.red_recurring_actions: List[RecurringAction] = []

    def calculate_reward(
        self,
        red_action: str,
        blue_action: str,
        red_success: str,
        blue_success: bool,
        decoy: bool
    ) -> int | float:
        if red_success and not decoy:
            r = self.red_rewards[red_action][0]
        else:
            r = 50

        if blue_success:
            b = self.blue_rewards[blue_action][0]
        else:
            b = -100
        
        if len(self.blue_recurring_actions) < 1:
            b -= 100

        return r + b + self.sum_recurring_blue() + self.sum_recurring_red()

    def sum_recurring_blue(self) -> int | float:
        sum = 0
        for ra in self.blue_recurring_actions:
            sum += self.blue_rewards[ra.action][1]
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
                sum -= self.red_rewards[ra[0].action][1] * 10
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