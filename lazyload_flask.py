# app_lazy_cached.py
from dash import Dash, dcc, html, Output, Input, State
import dash_bootstrap_components as dbc
from flask_caching import Cache
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import time

app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
server = app.server

# configure cache - use "SimpleCache" for dev; use Redis or filesystem in prod
cache = Cache(
    server, config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300}
)


# simulate expensive data generation; cache it
@cache.memoize()
def expensive_df_build(seed, n=10000):
    # pretend this takes time (e.g., DB fetch, heavy transform)
    time.sleep(1.0)  # simulate delay
    rng = np.random.default_rng(seed)
    t = pd.date_range("2025-01-01", periods=n, freq="S")
    return pd.DataFrame({"t": t, "val": rng.normal(size=n)})


# small shell for tab
def file_uploads_shell():
    return html.Div(
        [
            html.H4("File Uploads"),
            # placeholders for heavy graphs (populated by callbacks)
            dcc.Loading(html.Div(id="file-count-graph"), type="default"),
            html.Br(),
            dcc.Loading(html.Div(id="file-timeline-graph"), type="default"),
            # a hidden store or simple button could trigger updates; we'll trigger via tabs.value
        ],
        style={"padding": "12px"},
    )


def device_health_shell():
    return html.Div(
        [
            html.H4("Device Health"),
            dcc.Loading(html.Div(id="device-health-graph"), type="default"),
        ],
        style={"padding": "12px"},
    )


app.layout = dbc.Container(
    [
        dcc.Tabs(
            id="tabs",
            value="tab-files",
            children=[
                dcc.Tab(label="Files", value="tab-files"),
                dcc.Tab(label="Device Health", value="tab-health"),
            ],
        ),
        html.Div(id="tab-shell"),
    ],
    fluid=True,
)


@app.callback(Output("tab-shell", "children"), Input("tabs", "value"))
def render_tab_shell(tab_value):
    # immediate small shell returned quickly
    if tab_value == "tab-files":
        return file_uploads_shell()
    elif tab_value == "tab-health":
        return device_health_shell()
    return html.Div("Select a tab")


# Chart callback 1: file count (builds only when tabs.value == tab-files)
@app.callback(Output("file-count-graph", "children"), Input("tabs", "value"))
def load_file_count(tab_value):
    if tab_value != "tab-files":
        # return empty to avoid building when not needed
        return html.Div()
    # call cached expensive build
    df = expensive_df_build("seed1", n=5000)
    # aggregation
    bucket = df.set_index("t").resample("5min").count()["val"]
    fig = go.Figure(go.Bar(x=bucket.index, y=bucket.values))
    fig.update_layout(template="plotly_dark", title="File counts (cached)")
    return dcc.Graph(figure=fig)


# Chart callback 2: file timeline
@app.callback(Output("file-timeline-graph", "children"), Input("tabs", "value"))
def load_file_timeline(tab_value):
    if tab_value != "tab-files":
        return html.Div()
    df = expensive_df_build("seed1", n=5000)  # cheap due to cache
    # downsample for timeline visualization
    df_small = df.iloc[::10]
    fig = go.Figure(go.Scattergl(x=df_small["t"], y=df_small["val"], mode="markers"))
    fig.update_layout(template="plotly_dark", title="File timeline (downsampled)")
    return dcc.Graph(figure=fig)


# Device health chart callback (only runs when tab selected)
@app.callback(Output("device-health-graph", "children"), Input("tabs", "value"))
def load_device_health(tab_value):
    if tab_value != "tab-health":
        return html.Div()
    df = expensive_df_build("seed2", n=2000)
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=df["val"], nbinsx=50))
    fig.update_layout(template="plotly_dark", title="Device health distribution")
    return dcc.Graph(figure=fig)


if __name__ == "__main__":
    app.run(debug=True)
