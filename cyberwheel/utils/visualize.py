import os
import networkx as nx
import matplotlib.pyplot as plt
import pickle

from cyberwheel.network.network_base import Network, Host
from cyberwheel.red_agents.red_agent_base import AgentHistory, KnownHostInfo
from typing import Any
from importlib.resources import files
from cyberwheel.observation import RedObservation

def color_map(host_view) -> str:
    """
    Maps the state of the Host with a corresponding color.

    sweeped or scanned          -->     Green
    discovered                  -->     Yellow
    escalated                   -->     Orange
    impacted                    -->     Red
    """
    if host_view.impacted:
        return "red"
    elif host_view.escalated:
        return "orange"
    elif host_view.discovered:
        return "yellow"
    elif host_view.scanned:
        return "green"
    elif host_view.sweeped:
        return "green"
    else:
        return "gray"

def visualize(
    episode: int,
    step: int,
    experiment_name: str,
    info: dict[str, Any],
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
    experiment_dir = files("cyberwheel.data.graphs").joinpath(experiment_name)
    if not os.path.exists(experiment_dir):
        os.mkdir(experiment_dir)
    
    host_info = info["host_info"]
    network: Network = info["network"]

    source_host = info["source_host"]
    target_host = info["target_host"]
    step_commands = info["commands"]

    # Initialize network graph and environment state information
    G = network.graph

    host_color = {}
    on_host = ""
    for h, host_view in host_info.items():
        host_color[h] = color_map(host_view)
        on_host = h if host_view.on_host else source_host

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
        if "subnet" in node_name:
            color = "gray"
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
                    color = "gray"
                    state = "Safe"
            else:
                color = "gray"
        if node_name == on_host:
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