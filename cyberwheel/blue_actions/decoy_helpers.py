import yaml

from importlib.resources import files
from typing import Dict

def get_host_type_info(type: str, definitions_path='host_definitions.json') -> Dict[str, any]:
    conf_file = files('cyberwheel.resources.metadata').joinpath(definitions_path)
    with open(conf_file, "r") as r:
        contents = yaml.safe_load(r)

    for host_type in contents['host_types']:
        if type == host_type['type']:
            return host_type
    raise KeyError(f'key {type} not found in {definitions_path}')

def load_decoy_host_options(conf_name: str='decoy_host.yaml')-> Dict[str, any]:
    """
    A function for parsing the decoy host config file. This is made with the blue agent in mind.
    It might be useful for `DeployDecoyHost` as well. 
    """
    conf_file = files('cyberwheel.resources.metadata').joinpath(conf_name)
    with open(conf_file, "r") as r:
        contents = yaml.safe_load(r)
    

    options: Dict[str, any] = {}
    for key in contents:
        decoy_info = contents[key]
        host_type = decoy_info['type']
        host_type_info = get_host_type_info(host_type)
        options[key] = {}

    
    
