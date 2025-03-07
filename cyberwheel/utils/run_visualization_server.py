import dash
import os
import pandas as pd
import pickle
import plotly.graph_objects as go

from dash import Dash, html, dcc, dash_table, callback, Input, Output, State
from importlib.resources import files


def main_page_layout():
    graph_list = []
    basepath = files("cyberwheel.data").joinpath("graphs")
    for path in os.scandir(basepath):
        if os.path.isdir(path.path) and any(
            ".pickle" in g for g in os.listdir(path.path)
        ):
            graph_list.append(path.name)
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


app = Dash(__name__, suppress_callback_exceptions=True)
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        html.H1("Cyberwheel"),
        html.Br(),
        html.Div(id="page-content", children=main_page_layout()),
    ]
)


def graph_page_layout(graph_name: str):
    num_episodes = set()
    num_steps = set()
    for filename in os.listdir(files("cyberwheel.data.graphs").joinpath(graph_name)):
        if ".pickle" not in filename:
            continue
        episode = int(filename.split("_")[0])
        step = int(filename.split("_")[-1].split(".")[0])
        num_episodes.add(episode)
        num_steps.add(step)

    num_episodes = list(num_episodes)
    num_steps = len(num_steps)

    return [
        html.Div(
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
                    0,
                    num_steps - 1,
                    1,
                    marks={i: "" for i in range(num_steps)},
                    value=0,
                    id="input-step-slider",
                    updatemode="drag",
                ),
                html.Br(),
                html.Div(id="output-datatable-container"),
                html.Div(id="node-redirect-id"),
            ]
        ),
        html.Div(
            id="modal",
            style={
                "display": "none",  # Initially hidden
                "position": "fixed",
                "top": "50%",
                "left": "50%",
                "transform": "translate(-50%, -50%)",
                "width": "300px",
                "max-height": "200px",  # Limits height, makes it scrollable
                "overflow-y": "auto",  # Scroll if content overflows
                "background-color": "white",
                "border": "1px solid black",
                "padding": "10px",
                "z-index": "1000",
            },
        ),
    ]


@callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/":
        return html.Div([main_page_layout()])
    if "/graph/" in pathname:
        return html.Div(graph_page_layout(pathname.split("/")[-1]))
    else:
        return "404"


@callback(
    Output("output-datatable-container", "children"),
    Input("input-episode-dropdown", "value"),
    State("state-graph-name", "children"),
)
def update_datatable(episode, graph_name):
    df = pd.read_csv(files("cyberwheel.data.action_logs").joinpath(f"{graph_name}.csv"))
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
    with open(
        files(f"cyberwheel.data.graphs.{graph_name}").joinpath(f"{episode}_{step}.pickle"),
        "rb",
    ) as f:
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
    node_commands = []
    customdata = []
    for node in G.nodes():
        commands = []
        state = f"{node}:\n{G.nodes[node]['state']}"
        for c in G.nodes[node]["commands"]:
            commands.append(c)
            commands.append(html.Br())
        x, y = G.nodes[node]["pos"]
        node_x.append(x)
        node_y.append(y)
        node_colors.append(G.nodes[node]["color"])
        node_states.append(state)
        node_commands.append(commands)
        line_colors.append(G.nodes[node]["outline_color"])
        line_widths.append(G.nodes[node]["outline_width"])
        customdata.append(commands)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="text",
        marker=dict(
            color=node_colors, size=20, line=dict(color=line_colors, width=line_widths)
        ),
        customdata=customdata,
    )

    node_trace.marker.color = node_colors
    node_trace.text = node_states

    # Create network graph

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=True,
            hovermode="x unified",
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
    return dcc.Graph(id="network-graph", figure=fig)


@app.callback(
    Output("modal", "style"),
    Output("modal", "children"),
    Input("network-graph", "clickData"),
    State("modal", "style"),
)
def display_click_data(clickData, style):
    if clickData and style["display"] == "none":
        point = clickData["points"][1]
        # print(point)
        text = point["customdata"]
        if len(text) == 0:
            text = "No commands run on Host."
        return {
            "display": "block",  # Show the modal
            "position": "fixed",
            "top": "50%",
            "left": "50%",
            "transform": "translate(-50%, -50%)",
            "width": "1000px",
            "max-height": "500px",
            "overflow-y": "auto",
            "background-color": "black",
            "color": "white",
            "font-family": "ubuntu",
            "font-size": "80%",
            "padding": "10px",
            "z-index": "1000",
        }, text
    return {"display": "none"}, ""

def run_visualization_server(port):
    app.run(debug=True, port=port)
