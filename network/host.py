from .network_object import NetworkObject

class Host(NetworkObject):
    def __init__(self, name, type, subnet, firewall_rules=[]):
        '''
        :param str name: name of host
        :param str type: type of host
        :param str subnet: subnet to be connected to
        :param list[dict] firewall_rules: list of firewall rules (emtpy rules = allow all)
                Example:
                [
                    {
                        'name': 'https',
                        'src': 'some_subnet'
                        'port': 443,
                        'proto': 'tcp',
                        'desc': 'Allow all src to all dest on dest port 443'
                    },
                    {
                        'name': 'foo'
                        'src': 'some_host'
                        'port': 3128,
                        'proto': 'tcp',
                        'desc': 'Allow some_host to use foo service'
                    }
                ]
        '''
        super().__init__(name, firewall_rules)
        self.type = type
        self.subnet = subnet
        self.is_compromised = False  # Default to not compromised
