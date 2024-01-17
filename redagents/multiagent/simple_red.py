class SimpleRedAgent:

    def __init__(self, network):
        self.network = network

    def act(self, action):
        # If the action is to compromise a host, set the corresponding element in the state to True
        if action > 0:
            self.network.set_host_compromised(action-1, True)
        
        if self.is_finished():
            return 1000, True # Reward red agent for winning and finish game

        return 0, False
    
    def is_finished(self):
        return self.network.is_any_subnet_fully_compromised()