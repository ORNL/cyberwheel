class SimpleBlueAgent:

    def __init__(self, network):
        self.network = network

    def act(self, action):
        # If the action is to restore a host, set the corresponding element in the state to 1
        if action > 0:
            if self.network.set_host_compromised(action-1,False):
                return 10, False

        return 0, False