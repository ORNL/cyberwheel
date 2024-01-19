import ipaddress

class Host:
    def __init__(self, name, type, subnet, firewall_rules={}):
        '''
        :param str name: name of host
        :param str type: type of host
        :param str subnet: subnet to be connected to
        :param dict: firewall_rules: firewall rules dict (emtpy rules = allow all)
                Example:
                {'service-name':
                    {'port': 443,
                     'proto': 'tcp',
                     'desc': 'Allow all src to all dest on dest port 443'},
                 'foo service':
                    {'port': 3128,
                     'proto': 'tcp',
                     'src': ['subnet_a', 'subnet_b'],
                     'desc': 'Allow only subnet_a and subnet_b to use foo service'
                     }
                }
        '''
        self.name = name
        self.type = type
        self.subnet = subnet
        self.firewall_rules = firewall_rules  # Dict of firewall rules specific to this host
        self.is_compromised = False  # Default to not compromised

    def add_firewall_rule(self, rule):
        '''
        Adds new firewall rule(s)

        :param dict: firewall_rules: firewall rules dict (emtpy rules = allow all)
                Example:
                {'service-name':
                    {'port': 443,
                     'proto': 'tcp',
                     'desc': 'Allow all src to all dest on dest port 443'},
                 'foo service':
                    {'port': 3128,
                     'proto': 'tcp',
                     'src': ['subnet_a', 'subnet_b'],
                     'desc': 'Allow only subnet_a and subnet_b to use foo service'
                     }
                }
        '''
        # if a new rule is added that has overlapping keys (i.e. service name)
        # with an existing rule it will overwrite the previous existing rule
        self.firewall_rules.update(rule)


    def remove_firewall_rule(self, rule_name: str):
        '''
        Removes an existing firewall rule

        :param str rule_name: service name of existing fw rule
        '''
        try:
            self.firewall_rules.pop(rule_name)
        except KeyError as e:
            # TODO: raise custom exception here?
            raise e

