from cyberwheel.network.network_generation.network_generator import NetworkYAMLGenerator

a = NetworkYAMLGenerator(network_name="network-cac9fa081e8a4edd856345da364c79b3")


# Create router
a.router("core_router", "internet")
a.add_route_to_router("core_router", "10.0.0.0/8", "10.0.0.1")
a.add_route_by_name("core_router", "user_subnet")

# Create subnets
a.subnet("user_subnet", router_name="core_router", ip_range="192.168.0.0/24", dns_server="192.168.0.1")
a.add_firewall_to_subnet("user_subnet", name="allow all from server_subnet", src="server_subnet")
a.add_firewall_to_subnet("user_subnet", name="allow ssh from dmz_jump_box", src="dmz_jump_box", port=22)
a.add_firewall_to_subnet("user_subnet", src="internet")

a.subnet("server_subnet", router_name="core_router", ip_range="192.168.1.0/24")
a.add_firewall_to_subnet("server_subnet", name="allow admin to server_subnet", src="admin_workstation", dest="server_subnet")
a.add_firewall_to_subnet("server_subnet", name="allow DNS", src="user_subnet", dest="server_subnet", port=53)
a.add_firewall_to_subnet("server_subnet", name="allow DHCP", src="user_subnet", dest="server_subnet", port=68, protocol="udp")

a.subnet("dmz_subnet", router_name="core_router", ip_range="192.168.2.0/24")

# Add hosts to user_subnet
a.host("user01", "user_subnet", "example")
a.add_route_to_host("user01", "192.168.2.0/24", "192.168.0.1")

a.host("user02", "user_subnet", "workstation")
a.add_firewall_to_host("user02", name="foo", src="server01", port=3389)

a.host("user03", "user_subnet", "workstation")

a.host("admin_workstation", "user_subnet", "workstation")
a.add_firewall_to_host("admin_workstation", name="allow SSH", src="all", port=22)


# Add hosts to server_subnet
for i in range(1,4):
    a.host(f"server0{i}", "server_subnet", "web_server")

for i in range(1,4):
    a.host(f"dmz0{i}", "dmz_subnet", "workstation")
a.add_firewall_to_host("dmz03", name="foo", src="all", dest="dmz03", port=443, protocol="tcp")

a.host("dmz_jump_box", "dmz_subnet", "workstation")
a.add_firewall_to_host("dmz_jump_box", name="allow SSH", port=22)

# Add interfaces
a.interface("user01", "dmz01")

# Specify which host type config file to use with this network
a.set_host_type_config("resources/metadata/host_definitions.json")

# Write to YAML
a.output()