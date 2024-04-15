from abc import abstractmethod
from typing import Dict, List, NewType, Tuple

RewardMap = NewType('RewardMap', Dict[str, Tuple[int | float, int | float]])

class RecurringAction():
    def __init__(self, id: str, action: str) -> None:
        self.id = id
        self.action = action

class RewardCalculator():
    @abstractmethod
    def calculate_reward(self) -> int | float:
        raise NotImplementedError
    
    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError
    
class Reward(RewardCalculator):
    def __init__(self, red_rewards: RewardMap, blue_rewards: RewardMap) -> None:
        self.red_rewards = red_rewards
        self.blue_rewards = blue_rewards
        self.recurring_actions: List[RecurringAction] = []

    def calculate_reward(self, red_action: str, blue_action: str, blue_success: bool, red_action_alerted: bool) -> int | float:
        if red_action_alerted:
            r = 100
        else:
            r = self.red_rewards[red_action][0]

        if blue_action == "" and blue_success:
            b = 0
        elif self.blue_success:
            b = self.blue_rewards[blue_action][0]
        else:
            b = -100

        return r + b + self.sum_recurring()

    def sum_recurring(self) -> int | float:
        sum = 0
        for ra in self.recurring_actions:
            sum += self.blue_rewards[ra.action][1]
        return sum

    def add_recurring_action(self,id: str, action: str)-> None:
        self.recurring_actions.append(RecurringAction(id, action))

    def remove_recurring_action(self, name: str)-> None:
        for i in range(len(self.recurring_actions)):
            if self.recurring_actions[i].id == name:
                self.recurring_actions.pop(i)
                break

    def handle_blue_action_output(self, blue_action: str, rec_id: str):
        if blue_action:
            self.add_recurring_action(rec_id, blue_action)
        else:
            self.remove_recurring_action(rec_id)

    def reset(self)-> None:
        self.recurring_actions = []
