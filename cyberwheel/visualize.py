import os
import networkx as nx
import matplotlib.pyplot as plt
import pickle

from cyberwheel.network.network_base import Network, Host
from cyberwheel.red_agents.red_agent_base import AgentHistory
from typing import Any
from importlib.resources import files


def color_map(state) -> str:
    """
    Maps the state of the Host with a corresponding color.

    Pingsweep & PortScan    -->     Green
    Discovery               -->     Yellow
    Privilege Escalation    -->     Orange
    Impact                  -->     Red
    """
    if state == "ARTDiscovery":
        return "yellow"
    elif state == "ARTPingSweep" or state == "ARTPortScan":
        return "green"
    elif state == "ARTPrivilegeEscalation":
        return "orange"
    elif state == "ARTImpact":
        return "red"
    else:
        return "gray"


def visualize(
    network: Network,
    episode: int,
    step: int,
    experiment_name: str,
    history: AgentHistory,
    killchain: list[Any],
):
    """
    A function to visualize the state of the network at a given episode/step.
    Given the state of the environment at this episode and step, generates a
    visualization as a graph object and saves it in `graphs/{experiment_name}`

    * `network`: Network object representing the network at this step of the evaluation.
    * `episode`: integer representing the episode of the evaluation.
    * `step`: integer representing the step of the evaluation.
    * `experiment_name`: string representing the experiment name to save graphs under.
    * `history`: AgentHistory object representing the red agent history at this step of the evaluation.
    * `killchain`: List of KillChain Phases representing the killchain of the red agent.
    """
    window_size = (15, 7)  # Set size of visualization window

    # Create `graphs/experiment_name` directory if it doesn't exist
    experiment_dir = files("cyberwheel.graphs").joinpath(experiment_name)
    if not os.path.exists(experiment_dir):
        os.mkdir(experiment_dir)

    # Initialize network graph and environment state information
    G = network.graph

    host_info = history.hosts
    subnet_info = history.subnets
    last_step_info = history.history[-1]
    source_host = last_step_info["src_host"]
    target_host = last_step_info["target_host"]
    current_action = last_step_info["action"]
    mitre_id = last_step_info["techniques"]["mitre_id"]
    technique = last_step_info["techniques"]["technique"]
    step_commands = last_step_info["techniques"]["commands"]

    if (
        current_action == "ARTLateralMovement"
    ):  # If Lateral Movement, change host position in visualization
        source_host = target_host

    # Set colors of hosts and subnets
    host_color = {}
    subnet_color = {}
    for hostname in host_info:
        temp_action = "nothing yet"
        if host_info[hostname].last_step == -1:
            if host_info[hostname].ports_scanned or host_info[hostname].ping_sweeped:
                temp_action = (
                    "ARTPingSweep"
                    if host_info[hostname].ping_sweeped
                    else "ARTPortScan"
                )
            else:
                temp_action = "nothing"
        elif host_info[hostname].last_step >= len(killchain):
            temp_action = "ARTImpact"
        else:
            temp_action = killchain[host_info[hostname].last_step].__name__
        host_color[hostname] = color_map(temp_action)
    subnet_color = {
        k: "yellow" if subnet_info[k].scanned else "gray" for k in subnet_info
    }

    # Set design of nodes in graph based on state
    colors = []
    for node_name in list(G.nodes):
        color = "gray"
        state = "Safe"
        commands = []
        if (
            isinstance(G.nodes[node_name]["data"], Host)
            and G.nodes[node_name]["data"].name == target_host
        ):
            commands = step_commands

        edgecolor = "black"
        linewidth = 2
        if "subnet" in node_name and node_name in subnet_color:
            color = subnet_color[node_name]
            state = "Scanned" if color == "yellow" else "Safe"
        else:
            if node_name in host_color:
                color = host_color[node_name]
                if color == "green":
                    state = "PingSweep/PortScan"
                elif color == "yellow":
                    state = "Discovery"
                elif color == "orange":
                    state = "Privilege Escalation - Process level escalated to 'root'"
                elif color == "red":
                    state = "Impact"
                else:
                    state = "Safe"
            else:
                color = "gray"
        if node_name == source_host:
            edgecolor = "blue"
            linewidth = 4
            state += "<br>Red Agent Position<br>"

        if "commands" not in G.nodes[node_name]:
            G.nodes[node_name]["commands"] = []
        G.nodes[node_name]["color"] = color
        G.nodes[node_name]["state"] = state
        G.nodes[node_name]["commands"].extend(commands)
        G.nodes[node_name]["outline_color"] = edgecolor
        G.nodes[node_name]["outline_width"] = linewidth

    fig, axe = plt.subplots(figsize=window_size)

    # Use Graphviz for neat, hierarchical layout
    pos = nx.drawing.nx_agraph.graphviz_layout(G, prog="dot")

    for node in pos:
        G.nodes[node]["pos"] = (pos[node][0], pos[node][1])

    # Draw graph
    nodes = nx.draw_networkx_nodes(G, pos=pos, node_color=colors)
    edges = nx.draw_networkx_edges(G, pos=pos)
    labels = nx.draw_networkx_labels(G, pos=pos)

    # Save graph to experiment directory
    outpath = experiment_dir.joinpath(f"{episode}_{step}.pickle")
    with open(outpath, "wb") as f:
        pickle.dump(G, f)
    plt.close()
