from cyberwheel.network.network_base import Network
from copy import deepcopy, copy


class Cyberwheel:

    def __init__(self, **kwargs):
        # use config_file_path kwarg if supplied
        self.config_file_path = kwargs.get("config_file_path")

        # self.network = RandomNetwork(number_hosts,number_subnets,connect_subnets_probability)
        # print("begin reading")
        net = kwargs.get("network", None)
        if net == None:
            print("creating from yaml")
            self.network = Network.create_network_from_yaml(self.config_file_path)
        else:
            self.network = net
        #self.network_copy = copy(self.network)
        self.evaluation = False

    @classmethod
    def create_from_yaml(cls, config_file_path):

        return cls(config_file_path=config_file_path)
