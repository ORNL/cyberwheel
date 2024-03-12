import unittest
import yaml
from cyberwheel.detectors.alert import Alert
from cyberwheel.network.host import Host, HostType
from cyberwheel.network.service import Service
from cyberwheel.network.network_base import Network
from cyberwheel.blue_actions.actions.decoys.deploy_decoy_host import DeployDecoyHost, deploy_from_yaml

class TestDeployDecoyHost(unittest.TestCase):
    def setUp(self) -> None:
        self.network = Network.create_network_from_yaml('network/example_config.yaml')
        self.subnet = self.network.get_all_subnets()[0]
        services = [Service(**{'name':'HTTP', 'port':80}), Service(**{'name':'HTTPS', 'port':443}), Service(**{'name':'SSH', 'port':22})]
        self.host_type = HostType(**{"name": "decoy", "services": services, "decoy": True, "os": ''})
        self.correct_deploy = DeployDecoyHost(self.network, self.subnet, self.host_type, -10, -1)
    
    def test_decoy_host(self):
        with open('resources/metadata/decoy_hosts.yaml', 'r') as r:
            config = yaml.safe_load(r)
            deploy = deploy_from_yaml('resources/metadata/decoy_hosts.yaml', self.network, self.subnet)
            deploy.execute()
        self.assertTrue(self.correct_deploy == deploy, f'\n---------------\n{self.correct_deploy}\n\n{deploy}---------------')

if __name__ == "__main__":
    unittest.main()