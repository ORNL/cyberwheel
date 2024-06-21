from cyberwheel.network.network_base import Network
from copy import deepcopy


class Cyberwheel:

    def __init__(self, **kwargs):
        # use config_file_path kwarg if supplied
        # self.config_file_path = kwargs.get('config_file_path', 'network/config.yaml')
        self.config_file_path = kwargs.get("config_file_path")

        # self.network = RandomNetwork(number_hosts,number_subnets,connect_subnets_probability)
        # print("begin reading")
        self.network = Network.create_network_from_yaml(self.config_file_path)
        # self.network_copy = deepcopy(self.network)
        self.evaluation = False
        # print("end reading")
    # private method that converts state into observation
    # convert the dictionary of Host objects into the observation vector
    # def _get_obs(self):

    #     return self.network.generate_observation_vector()

    @classmethod
    def create_from_yaml(cls, config_file_path):

        return cls(config_file_path=config_file_path)
