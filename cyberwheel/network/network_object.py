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
    def __init__(self, name, firewall_rules: list[FirewallRule | None] = []):
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


    def add_firewall_rules(self, rules: list[FirewallRule]) -> None:
        '''
        Adds new firewall rules

        :param list[FirewallRule] rules: list of firewall rule(s)
        '''
        self.firewall_rules.extend(rules)


    # TODO: refactor for FirewallRule
    def remove_firewall_rule(self, rule_name: str):
        """
        Removes an existing firewall rule

        :param str rule_name: name of existing fw rule
        """
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


    def generate_route(self,
                       dest_net: ipa.IPv4Network | ipa.IPv6Network,
                       via_ip: ipa.IPv4Address | ipa.IPv6Address) -> Route:
        '''
        Generate a Route object from dest network and nexthop IP

        :param IPv4Network | IPv6Network dest: destination network
        :param IPv4Address | IPv6Address via: next hop IP
        :raises ValueError:
        '''
        return Route(dest=dest_net, via=via_ip)


    def generate_route_from_str(self, dest_net: str, via_ip: str) -> Route:
        '''
        Generate a Route object from dest network and nexthop IP

        :param str dest: destination network
        :param str via: next hop IP
        :raises ValueError:
        '''
        try:
            dest: ipa.IPv4Network | ipa.IPv6Network = ipa.ip_network(dest_net)
            via: ipa.IPv4Address | ipa.IPv6Address = ipa.ip_address(via_ip)
        except ValueError as e:
            # TODO: raise custom exception?
            raise e
        return Route(dest=dest, via=via)
