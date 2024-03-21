from cyberwheel.red_actions.technique import Technique
import sys
import time
from cyberwheel.network.network_base import Network

# sys.path.append("/Users/67x/cyberwheel/cyberwheel")
from cyberwheel.redagents.killchain_agent import KillChainAgent
from pprint import pprint, pformat

import random

net = Network("test")
net = net.create_network_from_yaml("network/simple_network_config.yaml")
hosts = net.get_all_hosts()
# print([h.ip_address for h in hosts])
user_hosts = []
for h in hosts:
    # print(h.type)
    if h.type != None and "User Workstation" in h.type:
        user_hosts.append(h)
# user_hosts = [h for h in hosts if "Workstation" in h.type]
entry_host = random.choice(user_hosts)
print(entry_host.subnet.connected_hosts)
print(entry_host.ip_address)
kc_agent = KillChainAgent(entry_host=entry_host)

for i in range(100):
    kc_agent.act()
    print(
        f"------------------------\n{kc_agent.history.step}\n------------------------"
    )
    print("Known Info:")
    for k, v in kc_agent.history.hosts.items():
        print(f"Host {k}: {v.type}")
    print("\nAction:")
    print(kc_agent.history.history[i].info)
    print("\n")
    time.sleep(0.5)
