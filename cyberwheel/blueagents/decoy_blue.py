from typing import List

from cyberwheel.network.network_base import Network
from cyberwheel.blue_actions.actions.decoys.deploy_decoy_host import DeployDecoyHost, random_decoy
from cyberwheel.blue_actions.blue_base import BlueAction

class DecoyBlueAgent:
    def __init__(self, network: Network):
        self.network = network
        self.subnets = self.network.get_all_subnets()
        self.num_hosts = len(network.get_hosts())
        self.history = [0 for i in range(self.num_hosts)]
       

        # Keep track of actions that have recurring rewards
        self.recurring_actions: List[BlueAction] = []


    def act(self, action):
        # Even if the agent choses to do nothing, the recurring rewards of 
        # previous actions still need to be summed.
        rec_rew = self.calc_recurring_reward_sum()

        # Decide what action to take
        if action[0] == 0:
            return rec_rew
        host_index = action[0] - 1
        subnet_index = action[1]

        # Perform the action
        selected_subnet = self.subnets[subnet_index]
        decoy = random_decoy(self.network, selected_subnet)        
        _, rew = decoy.execute()
        
        # Add the action if it has a recurring reward
        self.recurring_actions.append(decoy)
    
    
        return rew + rec_rew
    

    

    def calc_recurring_reward_sum(self)->int:
        """
        Calculates the sum of all recurring rewards for this agent.
        """
        sum = 0
        for recurring_action in self.recurring_actions:
           sum = recurring_action.calc_recurring_reward(sum)
        return sum