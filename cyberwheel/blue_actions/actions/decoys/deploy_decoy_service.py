import yaml

from importlib.resources import files
from typing import List

from cyberwheel.blue_actions.blue_base import BlueAction
from cyberwheel.network.host import Host
from cyberwheel.network.network_base import Network
from cyberwheel.network.service import Service



class DeployDecoyService(BlueAction):
    def __init__(self, service: Service, host: Host, reward: int = 0, recurring_reward: int = 0) -> None:
        """
        A class that allows the blue agent to create decoy services on hosts.
        These are lighter weight than host since a fully new system doesn't need to be deployed.

        ### Parameters
        - `service` the decoy `Service` that is to be deployed 
        - `host` the `Host` this service will be on
        - `reward`: the effect this decoy has on the overall reward upon execution
        - `recurring_reward`: the recurring effect this decoy has on the overall reward

        NOTE: These will be run on "real" hosts, right? If so, then maybe they're a bit riskier than a decoy host but have a higher (less negative) reward?
        The decoy services might still have vulnerabilities and will be exploitable. One possible idea is to have these services still be vulnerable
        and thus make the host vulnerable to an attack, but the red action will always be detected. 
        """
        super().__init__(reward, recurring_reward)
        self.service = service
        self.host = host

    def execute(self) -> bool:
        self.host.add_service(self.service.name, self.service.port, protocol=self.service.protocol, version=self.service.version, deploy=True)
        return True
    

def deploy_service_from_yaml(decoy_name: str, host: Host, fname: str)-> DeployDecoyService:
    """
    Creates a DeployDecoyService object specified in a YAML file. 
    - `decoy_name`: name of the decoy service to deploy
    - `host`: the host to deploy this service on
    - `path`: path to the config file of the typ
    """
    conf_file = files('cyberwheel.resources.metadata').joinpath(fname)
    with open(conf_file, 'r') as r:
        config = yaml.safe_load(r)

    if decoy_name not in config:
        raise KeyError() 

    service_info = config[decoy_name]
    reward = int(config[decoy_name]['reward'])
    recurring_reward = int(config[decoy_name]['recurring_reward'])
    
    service_type = {'name': decoy_name, 'port': service_info['port'], 'protocol': service_info['protocol'], 'version': service_info['version']}
    service = Service(**service_type)

    decoy = DeployDecoyService(service, host, reward=reward, recurring_reward=recurring_reward)
    return decoy
    
if __name__ == "__main__":
    network = Network.create_network_from_yaml('network/example_config.yaml')
    host:Host = network.get_all_hosts()[0]
    for s in host.get_services():
        print(s)
    deploy = deploy_service_from_yaml('service_name', host, 'decoy_services.yaml')
    deploy.execute()
    for s in host.get_services():
        print(s)