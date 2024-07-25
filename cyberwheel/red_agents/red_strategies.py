import random

def impact_all_servers(agent_obj):
    current_host_type = agent_obj.history.hosts[agent_obj.current_host.name].type

    """
    It should continue impacting the current host if: it is Unknown or if it is a Server that has not been impacted yet. Otherwise it should move to another host.
    It should prioritize attacking other Servers that are unimpacted in its view. Then it should prioritize Unknown hosts in its view.
    If there are no unimpacted Servers or Unknown hosts in its view, it has succeeded. Maybe give this a very large cost to signify failure on the blue agent side.
    """
    
    target_host = agent_obj.current_host
    if current_host_type == "Unknown" or agent_obj.unimpacted_servers.check_membership(agent_obj.current_host.name):
        target_host = agent_obj.current_host
    elif agent_obj.unimpacted_servers.length() > 0:
        target_host = agent_obj.history.mapping[agent_obj.unimpacted_servers.get_random()] # O(1)
    elif agent_obj.unknowns.length() > 0:
        target_host = agent_obj.history.mapping[agent_obj.unknowns.get_random()] # O(1)
    return target_host
    
def dfs_impact(agent_obj):
    if (
        agent_obj.history.hosts[agent_obj.current_host.name].last_step
        == len(agent_obj.killchain) - 1
    ):
        unimpacted_hosts = [
            h
            for h, info in agent_obj.history.hosts.items()
            if info.last_step < len(agent_obj.killchain) - 1
        ]
        if len(unimpacted_hosts) > 0:
            target_host_name = random.choice(unimpacted_hosts)
            target_host = agent_obj.history.mapping[target_host_name]
            return target_host
    return agent_obj.current_host