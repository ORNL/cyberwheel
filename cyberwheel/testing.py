from cyberwheel.red_actions.technique import Technique
import sys
import time
from cyberwheel.network.network_base import Network

# sys.path.append("/Users/67x/cyberwheel/cyberwheel")
from cyberwheel.redagents.killchain_agent import KillChainAgent
from pprint import pprint, pformat

import random

net = Network("test")
net = net.create_network_from_yaml()
hosts = net.get_all_hosts()
user_hosts = []
for h in hosts:
    if h.host_type != None and "workstation" in h.host_type.name.lower():
        user_hosts.append(h)
entry_host = random.choice(user_hosts)
kc_agent = KillChainAgent(entry_host=entry_host)

for i in range(100):
    kc_agent.act()
    print(
        f"------------------------\n{kc_agent.history.step}\n------------------------"
    )
    print()
    print("Hosts:")
    for k, v in kc_agent.history.hosts.items():
        print(f"\tHost {k}: {v.type}")
    print("\nAction:")
    print("\t" + kc_agent.history.history[i].info)

    print("\n")
    time.sleep(0.5)
