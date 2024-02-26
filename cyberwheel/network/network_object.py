class NetworkObject:
    """
    Base class for host, subnet, and router objects
    """

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
            allow_all_rule = {
                "name": "allow all",
                "src": "all",
                "dest": "all",
                "port": "all",
                "proto": "all",
                "desc": 'auto generated allow-all rule"',
            }

            implied_rules.append(allow_all_rule)
            return implied_rules

        # if some rules are defined, populate any implied allows
        else:
            for rule in rules:
                if "src" not in rule:
                    rule["src"] = "all"
                if "dest" not in rule:
                    rule["dest"] = "all"
                if "proto" not in rule:
                    rule["proto"] = "all"
                if "port" not in rule:
                    rule["port"] = "all"

            return rules

    def add_firewall_rules(self, rules: list[dict]):
        """
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
                    },
                    {
                        'name': 'allow ICMP',
                        'proto': 'icmp',
                        'desc': 'Allow pings from anywhere'
                    }
                ]
        """
        self.firewall_rules.append(rules)

    # TODO: make rule_name case insensitive
    def remove_firewall_rule(self, rule_name: str):
        """
        Removes an existing firewall rule

        :param str rule_name: name of existing fw rule
        """
        # iterate over existing rules and discard rule if rule['name'] equals
        # the rule_name param
        updated_rules = [
            rule for rule in self.firewall_rules if rule.get("name") != rule_name
        ]

        # update firewall rules
        self.firewall_rules = updated_rules
