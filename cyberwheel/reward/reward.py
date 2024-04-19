from abc import abstractmethod
from typing import Dict, List, NewType, Tuple

RewardMap = NewType('RewardMap', Dict[str, Tuple[int | float, int | float]])

def calc_quadratic(x: float, a=0.0, b=0.0, c=0.0) -> float:
    return a*x**2 + b*x + c


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
    def __init__(self, red_rewards: RewardMap, blue_rewards: RewardMap, r: Tuple[int, int] = (0,10), scaling_factor: float = 10.0) -> None:
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
        self.blue_rewards = blue_rewards
        self.recurring_actions: List[RecurringAction] = []
        self.range = r
        self.scaling_factor = scaling_factor


    def calculate_reward(self, red_action: str, blue_action: str, blue_success: bool, red_action_alerted: bool) -> int | float:
        if red_action_alerted:
            r = abs(self.red_rewards[red_action][0]) * self.scaling_factor
        else:
            r = self.red_rewards[red_action][0]

        if blue_action == "" and blue_success:
            b = 0
        elif blue_success:
            b = self.blue_rewards[blue_action][0]
        else:
            b = -100

        return r + b + self.sum_recurring()

    def sum_recurring(self) -> int | float:
        sum = 0
        for ra in self.recurring_actions:
            sum += self.blue_rewards[ra.action][1]

        # Subtract the distance times the scaling factor away from the range
        if len(self.recurring_actions) > self.range[1]:
            x = len(self.recurring_actions) - self.range[1]
            sum -= calc_quadratic(x, a=self.scaling_factor)
        elif len(self.recurring_actions) < self.range[0]:
            x = self.range[0] - len(self.recurring_actions)
            sum -= calc_quadratic(x, a=self.scaling_factor*1.5)

        print(len(self.recurring_actions), sum, end=" ")
        return sum

    def add_recurring_action(self, id: str, action: str)-> None:
        self.recurring_actions.append(RecurringAction(id, action))

    def remove_recurring_action(self, name: str)-> None:
        for i in range(len(self.recurring_actions)):
            if self.recurring_actions[i].id == name:
                self.recurring_actions.pop(i)
                break

    def handle_blue_action_output(self, blue_action: str, rec_id: str):
        if blue_action == "remove":
            self.remove_recurring_action(rec_id)
        elif blue_action != "nothing":
            self.add_recurring_action(rec_id, blue_action)

    def reset(self)-> None:
        self.recurring_actions = []
