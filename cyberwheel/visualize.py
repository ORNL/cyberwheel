import yaml
import os
import sys
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import imageio
import pandas as pd
import io
import pickle

from pprint import pprint
from PIL import Image

from typing import Any, List, Tuple

from cyberwheel.network.network_base import Network


def color_map(state) -> str:
    if state == "Discovery":
        return "green"
    elif state == "Reconnaissance":
        return "yellow"
    elif state == "PrivilegeEscalation":
        return "orange"
    elif state == "Impact":
        return "red"
    else:
        return "gray"


def visualize(network: Network, episode, step, experiment_name, history, killchain):
    window_size = (15, 7)

    if not os.path.exists(os.path.join("graphs", experiment_name)):
        os.mkdir(os.path.join("graphs", experiment_name))

    G = network.graph

    host_info = history.hosts
    subnet_info = history.subnets
    source_host = history.history[-1].action[1].name
    target_host = history.history[-1].action[2].name
    current_action = history.history[-1].action[0].__name__
    if current_action == "LateralMovement":
        source_host = target_host

    host_color = {}
    subnet_color = {}

    host_color = {
        k: (
            color_map(killchain[host_info[k].last_step].__name__)
            if host_info[k].last_step >= 0 and host_info[k].last_step < len(killchain)
            else "red" if host_info[k].last_step > len(killchain) else "gray"
        )
        for k in host_info.keys()
    }
    subnet_color = {
        k: "yellow" if subnet_info[k].scanned else "gray" for k in subnet_info.keys()
    }

    colors = []
    shapes = []

    for node_name in list(G.nodes):
        color = "gray"
        state = "Safe"
        edgecolor = "black"
        linewidth = 2
        if "subnet" in node_name and node_name in subnet_color.keys():
            color = subnet_color[node_name]
            state = "Scanned" if color == "yellow" else "Safe"
        else:
            if node_name in host_color.keys():
                color = host_color[node_name]
                state = "Discovery - Ports Scanned" if color == "green" else "Reconnaissance - Information Gathered" if color == "yellow" else "Privilege Escalation - Process level escalated to 'root'" if color == "orange" else "Impact - Host impacted" if color == "red" else "Safe"
            else:
                color = "gray"
        if node_name == source_host:
            edgecolor = "blue"
            linewidth = 4
            state += "<br>Red Agent Position"
        G.nodes[node_name]["color"] = color
        G.nodes[node_name]["state"] = state
        G.nodes[node_name]["outline_color"] = edgecolor
        G.nodes[node_name]["outline_width"] = linewidth

    fig, axe = plt.subplots(figsize=window_size)
    pos = nx.drawing.nx_agraph.graphviz_layout(
        G, prog="dot"
    )  # , args='-Grankdir="LR"')

    for node in list(pos.keys()):
        G.nodes[node]["pos"] = (pos[node][0], pos[node][1])

    nodes = nx.draw_networkx_nodes(G, pos=pos, node_color=colors)
    edges = nx.draw_networkx_edges(G, pos=pos)
    labels = nx.draw_networkx_labels(G, pos=pos)

    outpath = os.path.join("graphs", experiment_name, f"{episode}_{step}.pickle")
    with open(outpath, 'wb') as f:
        pickle.dump(G, f)
    plt.close()
