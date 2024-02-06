class NetworkObject:
    '''
    Base class for host, subnet, and router objects
    '''
    def __init__(self, name, firewall_rules=[]):
        self.name = name
        # default to 'allow all' if no rules defined
        ### this is antithetical to how firewalls work in the real world,
        ### but seemed pragmatic in our case
        self.firewall_rules = self._generate_implied_allow_rules(firewall_rules)


    def _generate_implied_allow_rules(self, rules):
        # if no rules are defined, add an 'allow all' rule
        if rules is None or rules == []:
            implied_rules = []
            allow_all_rule = {'name': 'allow all',
                              'src': 'all',
                              'dest': 'all',
                              'port': 'all',
                              'proto': 'all'}

            implied_rules.append(allow_all_rule)
            return implied_rules

        # if some rules are defined, populate any implied allows
        else:
            for rule in rules:
                if 'src' not in rule:
                    rule['src'] = 'all'
                if 'dest' not in rule:
                    rule['dest'] = 'all'
                if 'port' not in rule:
                    rule['port'] = 'all'
                if 'proto' not in rule:
                    rule['proto'] = 'all'

            return rules


    def add_firewall_rules(self, rules: list[dict]):
        '''
        Adds new firewall rule(s)

        :param list[dict] rules: firewall rule(s)
                Example:
                [
                    {
                        'name': 'https',
                        'src': 'some_subnet',
                        'port': 443,
                        'proto': 'tcp',
                        'desc': 'Allow some_subnet to all dest on dest port 443/tcp'
                    },
                    {
                        'name': 'squid-proxy',
                        'src': 'some_host',
                        'port': 3128,
                        'proto': 'tcp',
                        'desc': 'Allow some_host to all dest hosts on dest port 3128/tcp'
                    },
                    {
                        'name': 'foo service',
                        'port': 1234,
                        'proto': 'tcp',
                        'desc': 'Allow all src to all dest on port 1234/tcp'
                    }
                ]
        '''
        self.firewall_rules.append(rules)


    # TODO: make rule_name case insensitive
    def remove_firewall_rule(self, rule_name: str):
        '''
        Removes an existing firewall rule

        :param str rule_name: name of existing fw rule
        '''
        # iterate over existing rules and discard rule if rule['name'] equals
        # the rule_name param
        updated_rules = [rule for rule in self.firewall_rules if
                rule.get('name') != rule_name]

        # update firewall rules
        self.firewall_rules = updated_rules


    ## TODO: check if port is between 1 and 2**16-1
    #def is_traffic_allowed(self, src: str, dest: str, port: int, proto: str ='tcp') -> bool:
    #    '''
    #    Checks object's firewall to see if network traffic should be allowed

    #    :param str src: source subnet or host of traffic
    #    :param str dest: destination subnet or host of traffic
    #    :param int port: destination port
    #    :param str proto: protocol (i.e. tcp/udp, default = tcp)
    #    '''
    #    def _does_src_match(src: str, rule: dict) -> bool:
    #        if 'src' not in rule or rule['src'] is None:
    #            return True
    #        if src in rule['src'] or 'all' in rule['src']:
    #            return True
    #        return False


    #    def _does_dest_match(dest: str, rule: dict) -> bool:
    #        if 'dest' not in rule or rule['dest'] is None:
    #            return True
    #        if dest in rule['dest'] or 'all' in rule['dest']:
    #            return True
    #        return False


    #    def _does_port_match(port: int, rule: dict) -> bool:
    #        if 'port' not in rule or rule['port'] is None:
    #            return True
    #        if port in rule['port'] or 'all' in rule['port']:
    #            return True
    #        return False


    #    def _does_proto_match(proto: str, rule: dict) -> bool:
    #        if 'proto' not in rule or rule['proto'] is None:
    #            return True
    #        if proto in rule['proto'] or 'all' in rule['proto']:
    #            return True
    #        return False


    #    # TODO: catch any common exceptions (KeyError, etc.)
    #    # loop over each rule/element in firewall_rules
    #    for rule in self.firewall_rules:
    #        # break if src doesn't match
    #        if not _does_src_match(src, rule):
    #            break

    #        # break if dest doesn't match
    #        elif not _does_dest_match(dest, rule):
    #            break

    #        # break if port doesn't match
    #        elif not _does_port_match(port, rule):
    #            break

    #        # break if proto doesn't match
    #        elif not _does_proto_match(proto, rule):
    #            break

    #        # matching rule found
    #        else:
    #            return True

    #    return False


