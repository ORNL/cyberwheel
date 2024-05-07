from abc import abstractmethod
from typing import Dict, List, NewType, Tuple

RewardMap = NewType("RewardMap", Dict[str, Tuple[int | float, int | float]])


def calc_quadratic(x: float, a=0.0, b=0.0, c=0.0) -> float:
    return a * x**2 + b * x + c


class RecurringAction:
    def __init__(self, id: str, action: str) -> None:
        self.id = id
        self.action = action


class RewardCalculator:
    @abstractmethod
    def calculate_reward(self) -> int | float:
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError


class Reward(RewardCalculator):
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
        self.red_rewards = red_rewards
        self.blue_rewards = blue_rewards
        self.blue_recurring_actions: List[RecurringAction] = []
        self.red_recurring_impacts: List[str] = []
        self.range = r
        self.scaling_factor = scaling_factor

    def calculate_reward(
        self,
        red_action: str,
        blue_action: str,
        blue_success: bool,
        red_action_alerted: bool,
    ) -> int | float:
        if red_action_alerted:
            r = abs(self.red_rewards[red_action][0]) * self.scaling_factor
        else:
            r = self.red_rewards[red_action][0]
            self.handle_red_action_output(red_action)

        if blue_success:
            b = self.blue_rewards[blue_action][0]
        else:
            b = -100

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
            sum -= calc_quadratic(x, a=self.scaling_factor * 1.5)
        return sum


    def add_recurring_blue_action(self, id: str, action: str) -> None:
        self.blue_recurring_actions.append(RecurringAction(id, action))

    def remove_recurring_blue_action(self, name: str) -> None:
        for i in range(len(self.blue_recurring_actions)):
            if self.blue_recurring_actions[i].id == name:
                self.blue_recurring_actions.pop(i)
                break

    def sum_recurring_red(self) -> int | float:
        return self.red_rewards["impact"][1] * self.red_recurring_impacts

    def add_recurring_red_impact(self) -> None:
        self.red_recurring_impacts += 1

    def handle_blue_action_output(self, blue_action: str, rec_id: str):
        if "remove" in blue_action:
            self.remove_recurring_blue_action(rec_id)
        elif blue_action == "failed":
            return
        elif blue_action != "nothing":
            self.add_recurring_blue_action(rec_id, blue_action)
    
    def handle_red_action_output(self, red_action: str):
        if "impact" in red_action.lower():
            self.add_recurring_red_impact()
        return

    def reset(self) -> None:
        self.blue_recurring_actions = []
        self.red_recurring_impacts = 0


class StepDetectedReward(Reward):
    def __init__(
        self,
        blue_rewards: RewardMap,
        r: Tuple[int, int] = (2, 5),
        scaling_factor: float = 10.0,
        max_steps: int = 50,
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
            r=r,
            scaling_factor=scaling_factor,
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
