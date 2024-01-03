import gymnasium as gym
from gymnasium import spaces
from network import *
from redagent import *

class Cyberwheel(gym.Env):

    metadata = {'render.modes': ['human']}

    def __init__(self, number_hosts, number_subnets,number_targets):
        super(Cyberwheel, self).__init__()
        # Define action and observation space
        # They must be gym.spaces objects
        self.number_hosts = number_hosts
        self.number_subnets = number_subnets
        self.number_targets = number_targets

        self.network = Network(number_hosts,number_subnets,number_targets)

        self.network_size = number_hosts*number_subnets

        # Action space: 0 for no action, 1 to N for restore action on the corresponding host
        self.action_space = spaces.Discrete(self.network_size + 1)

        # Observation space: Binary vector indicating whether each host is compromised or not
        self.observation_space = spaces.MultiBinary(self.network_size)

        self.red_agent = RedAgent(self.observation_space, self.network.graph, self.network.source, self.network.target, self.network.host_to_index)

    # private method that converts state into observation 
    # convert the dictionary of Host objects into the observation vector
    def _get_obs(self):
        
        observation_vector = np.zeros(self.network_size, dtype=np.int8)
        
        n = 0
        for host_id, host_object in self.network.hosts.items():

            # Check if the host is compromised and update the corresponding element in the observation vector
            if host_object.is_compromised:
                observation_vector[n] = 1
            
            n+=1

        return observation_vector.astype(np.int8)

    def step(self, action):

        reward = 0

        # Example logic: If the action is to restore a host, set the corresponding element in the state to 1
        if action > 0:
            # since action is integer and key is string need a list of values
            l = list(self.network.hosts.values())

            # more actions than hosts by 1 since 0 is do nothing
            if l[action-1].is_compromised:
                patched = True
                reward = 10
            else:
                patched = False

            self.network.hosts[l[action-1].host_name].is_compromised = False
            
        self.observation_space = self._get_obs()

        if self.red_agent.act(self.observation_space) == "owned":
            done = True
            reward = -100
        else: 
            done = False

        return self._get_obs(), reward, done, False, {}
        #return observation, reward, done, info

    def reset(self, seed=None, options=None):

        self.network = Network(self.number_hosts,self.number_subnets,self.number_targets)
        
        return self._get_obs(), {} # observation, info

    # can implement existing GUI here???
    def render(self, mode='human'):
        pass

    # if you open any other processes close them here
    def close (self):
        pass