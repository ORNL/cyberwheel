from dash import Dash, html, dcc, dash_table, callback, Input, Output, State
import plotly.graph_objects as go
import dash
import os
import pandas as pd
from PIL import Image
import pickle
import sys


def main_page_layout():
    graph_list = []
    basepath = "graphs/"
    for path in os.scandir(basepath):
        if os.path.isdir(path.path) and any(
            ".pickle" in g for g in os.listdir(path.path)
        ):
            graph_list.append(path.name)
    # print(plugin_list)
    graph_dict = {"name": []}
    for graph in graph_list:
        graph_dict["name"].append(
            f"[{graph}]({dash.get_relative_path(f'/graph/{graph}')})"
        )
    df = pd.DataFrame(graph_dict, columns=list(graph_dict.keys()))
    return dash_table.DataTable(
        df.to_dict("records"),
        [
            (
                {"id": x, "name": x, "presentation": "markdown"}
                if x == "name"
                else {"id": x, "name": x}
            )
            for x in df.columns
        ],
        markdown_options={"link_target": "_self", "html": False},
    )


def graph_page_layout(graph_name: str):
    num_episodes = set()
    num_steps = set()
    for filename in os.listdir(f"graphs/{graph_name}"):
        if ".pickle" not in filename:
            continue
        episode = int(filename.split("_")[0])
        step = int(filename.split("_")[-1].split(".")[0])
        num_episodes.add(episode)
        num_steps.add(step)

    num_episodes = list(num_episodes)
    num_steps = len(num_steps)

    return html.Div(
        [
            html.H1(id="state-graph-name", children=graph_name),
            html.Br(),
            html.Div(id="output-slider-container"),
            html.Br(),
            html.P("Choose Episode:"),
            dcc.Dropdown(
                id="input-episode-dropdown",
                options=sorted(num_episodes),
                placeholder="Select Episode",
                value=0,
            ),
            html.P("Choose Step: "),
            dcc.Slider(
                0, num_steps - 1, 1, value=0, id="input-step-slider", updatemode="drag"
            ),
            html.Br(),
            html.Div(id="output-datatable-container"),
            html.Div(id="node-redirect-id"),
        ]
    )


@callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/":
        return html.Div([main_page_layout()])
    if "/graph/" in pathname:
        return html.Div([graph_page_layout(pathname.split("/")[-1])])
    else:
        return "404"


@callback(
    Output("output-datatable-container", "children"),
    Input("input-episode-dropdown", "value"),
    State("state-graph-name", "children"),
)
def update_datatable(episode, graph_name):
    df = pd.read_csv(f"action_logs/{graph_name}.csv")
    df = df.drop(df.columns[df.columns.str.contains("Unnamed", case=False)], axis=1)
    df = df[df["episode"] == episode]
    return dash_table.DataTable(
        df.to_dict("records"), [{"id": x, "name": x} for x in df.columns]
    )


@callback(
    Output("output-slider-container", "children"),
    Input("input-episode-dropdown", "value"),
    Input("input-step-slider", "value"),
    State("state-graph-name", "children"),
)
def update_graph(episode, step, graph_name):
    G = None
    with open(f"graphs/{graph_name}/{episode}_{step}.pickle", "rb") as f:
        G = pickle.load(f)

    # Create Edges

    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = G.nodes[edge[0]]["pos"]
        x1, y1 = G.nodes[edge[1]]["pos"]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        mode="lines",
    )

    # Create Nodes
    node_x = []
    node_y = []
    node_colors = []
    node_states = []
    line_colors = []
    line_widths = []
    for node in G.nodes():
        x, y = G.nodes[node]["pos"]
        node_x.append(x)
        node_y.append(y)
        node_colors.append(G.nodes[node]["color"])
        node_states.append(f"{node}:\n{G.nodes[node]['state']}")
        line_colors.append(G.nodes[node]["outline_color"])
        line_widths.append(G.nodes[node]["outline_width"])

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="text",
        marker=dict(
            color=node_colors, size=20, line=dict(color=line_colors, width=line_widths)
        ),
    )

    node_trace.marker.color = node_colors
    node_trace.text = node_states

    # Create network graph

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[
                dict(
                    text=f"Episode {episode}, Step {step}",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.005,
                    y=-0.002,
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )
    return dcc.Graph(figure=fig)


def run_visualization_server(port: int, debug: bool):
    app = Dash(__name__, suppress_callback_exceptions=True)
    app.layout = html.Div(
        [
            dcc.Location(id="url", refresh=False),
            html.H1("Cyberwheel"),
            html.Br(),
            html.Div(id="page-content", children=main_page_layout()),
        ]
    )
    app.run(debug=debug, port=port)


if __name__ == "__main__":
    port = sys.argv[1]
    debug = True
    run_visualization_server(port, debug)
