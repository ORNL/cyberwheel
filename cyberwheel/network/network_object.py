import ipaddress as ipa
from pydantic import BaseModel


class Route(BaseModel):
    dest: ipa.IPv4Network | ipa.IPv6Network
    via: ipa.IPv4Address | ipa.IPv6Address

    def __hash__(self):
        return hash((self.dest, self.via))


class FirewallRule(BaseModel):
    name: str = 'allow all'
    src: str = 'all'
    port: int | str = 'all'
    proto: str = 'tcp'
    desc: str | None = None


class NetworkObject:
    """
    Base class for host, subnet, and router objects
    """
    def __init__(self, name, firewall_rules: list[FirewallRule] = []):
        self.name = name
        # default to 'allow all' if no rules defined
        ### this is antithetical to how firewalls work in the real world,
        ### but seemed pragmatic in our case
        #self.firewall_rules = self._generate_implied_allow_rules(firewall_rules)
        self.firewall_rules = firewall_rules
        self.is_compromised = False


    def __eq__(self, other: object) -> bool:
        if isinstance(other, NetworkObject):
            return self.name == other.name
        return False


    def add_firewall_rule(self, rule: FirewallRule) -> None:
        '''
        Adds new firewall rule

        :param FirewallRule rule: firewall rule
        '''
        self.firewall_rules.append(rule)


    def add_firewall_rules(self, rules: list[FirewallRule]) -> None:
        '''
        Adds new firewall rules

        :param list[FirewallRule] rules: list of firewall rule(s)
        '''
        self.firewall_rules.extend(rules)

    # TODO: make rule_name case insensitive
    def remove_firewall_rule(self, rule_name: str):
        """
        Removes an existing firewall rule

        :param str rule_name: name of existing fw rule
        """
        # iterate over existing rules and discard rule if rule['name'] equals
        # the rule_name param
        updated_rules = [rule for rule in self.firewall_rules if
                rule.name != rule_name]

        # update firewall rules
        self.firewall_rules = updated_rules


    def generate_ip_object(self, ip: str) -> ipa.IPv4Address | ipa.IPv6Address:
        try:
            return ipa.ip_address(ip)
        except ValueError as e:
            # TODO: raise custom exception here?
            raise e


    def generate_ip_network_object(self, net: str) -> ipa.IPv4Network | ipa.IPv6Network:
        try:
            return ipa.ip_network(net)
        except ValueError as e:
            # TODO: raise custom exception here?
            raise e
