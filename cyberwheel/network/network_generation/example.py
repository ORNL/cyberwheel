# Running this script recreates most of network/example_config.yaml.
# Keys are in alphabetical order in the new file, but this shouldn't matter.
# The one major difference is that the "internet" subnet has been removed.
# I don't think we use this subnet right now, but it is possible to add it 
# if it turns out to be necessary.

from cyberwheel.network.network_generation.network_generator import NetworkYAMLGenerator

network = NetworkYAMLGenerator()


# Create router
network.router("core_router",)
network.add_route_to_router("core_router", "10.0.0.0/8", "10.0.0.1")
network.add_route_by_name("core_router", "user_subnet")

# Create subnets
network.subnet("user_subnet", router_name="core_router", ip_range="192.168.0.0/24", dns_server="192.168.0.1")
network.add_firewall_to_subnet("user_subnet", name="allow all from server_subnet", src="server_subnet")
network.add_firewall_to_subnet("user_subnet", name="allow ssh from dmz_jump_box", src="dmz_jump_box", port=22)
network.subnet("server_subnet", router_name="core_router", ip_range="192.168.1.0/24")
network.add_firewall_to_subnet("server_subnet", name="allow admin to server_subnet", src="admin_workstation", dest="server_subnet")
network.add_firewall_to_subnet("server_subnet", name="allow DNS", src="user_subnet", dest="server_subnet", port=53)
network.add_firewall_to_subnet("server_subnet", name="allow DHCP", src="user_subnet", dest="server_subnet", port=68, protocol="udp")

network.subnet("dmz_subnet", router_name="core_router", ip_range="192.168.2.0/24")

# Add hosts to user_subnet
network.host("user01", "user_subnet", "example")
network.add_route_to_host("user01", "192.168.2.0/24", "192.168.0.1")

network.host("user02", "user_subnet", "workstation")
network.add_firewall_to_host("user02", name="foo", src="server01", port=3389)

network.host("user03", "user_subnet", "workstation")

network.host("admin_workstation", "user_subnet", "workstation")
network.add_firewall_to_host("admin_workstation", name="allow SSH", src="all", port=22)

# Add hosts to server_subnet
for i in range(1,4):
    network.host(f"server0{i}", "server_subnet", "web_server")

for i in range(1,4):
    network.host(f"dmz0{i}", "dmz_subnet", "workstation")
network.add_firewall_to_host("dmz03", name="foo", src="all", dest="dmz03", port=443, protocol="tcp")

network.host("dmz_jump_box", "dmz_subnet", "workstation")
network.add_firewall_to_host("dmz_jump_box", name="allow SSH", port=22)

# Add interfaces
network.interface("user01", "dmz01")

# Specify which host type config file to use with this network
network.set_host_type_config("resources/metadata/host_definitions.json")

# Write to YAML
network.output()