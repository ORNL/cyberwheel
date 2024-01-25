class NetworkObject:
    '''
    Base class for host, subnet, and router objects
    '''
    def __init__(self, name, firewall_rules=[]):
        self.name = name
        self.firewall_rules = firewall_rules


    def is_traffic_allowed(self, src, dest, port, proto='tcp') -> bool:
        '''
        Checks object's firewall to see if network traffic should be allowed

        :param str src: source subnet or host of traffic
        :param str dest: destination subnet or host of traffic
        :param int port: destination port
        :param str proto: protocol (i.e. tcp/udp, default = tcp)
        '''
        # default to 'allow all' if no rules defined
        ### this is antithetical to how firewalls work in the real world,
        ### but seemed pragmatic in our case
        try:
            if not self.firewall_rules:
                return True
        except NameError:
            return True

        # TODO: catch any common exceptions (KeyError, etc.)
        # loop over each rule/element in firewall_rules
        for rule in self.firewall_rules:

            # does src subnet/host match?
            # or is src None? (if src == None assume allow all src)
            if 'src' not in rule or rule['src'] is None or \
                src in rule['src'] or 'all' in rule['src']:

                # does dest subnet/host match?
                # or is dest None? (if dest == None assume allow all dest)
                if 'dest' not in rule or rule['dest'] is None or \
                        dest in rule['dest'] or 'all' in rule['dest']:

                    # does port match?
                    if port in rule['port']:

                        # does protocol match?
                        if proto in rule['proto']:
                            return True

        return False


    def add_firewall_rule(self, rules):
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
