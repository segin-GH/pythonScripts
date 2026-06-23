import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ------------------------------------------------------------
# Dash App with Dark Theme
# ------------------------------------------------------------
app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

# ------------------------------------------------------------
# Dummy File Upload Data
# ------------------------------------------------------------
N_FILES = 720

# Each file has:
# recorded_at, uploaded_at, compute_start, compute_end
recorded_at = pd.date_range("2025-01-01 10:00", periods=N_FILES, freq="2min")

upload_delay_seconds = np.random.randint(30, 120, N_FILES)
uploaded_at = recorded_at + pd.to_timedelta(upload_delay_seconds, unit="s")

compute_delay = np.random.randint(10, 30, N_FILES)
compute_start = uploaded_at + pd.to_timedelta(5, unit="s")  # begins soon after upload
compute_end = compute_start + pd.to_timedelta(compute_delay, unit="s")

file_ids = [f"file_{i}" for i in range(N_FILES)]

df_files = pd.DataFrame(
    {
        "file_id": file_ids,
        "recorded_at": recorded_at,
        "uploaded_at": uploaded_at,
        "upload_delay_s": upload_delay_seconds,
        "compute_start": compute_start,
        "compute_end": compute_end,
        "compute_time_s": compute_delay,
        "end_to_end_s": (compute_end - recorded_at).total_seconds(),
    }
)

# ------------------------------------------------------------
# Summary Stats
# ------------------------------------------------------------
df_today = df_files[
    df_files["recorded_at"].dt.date == df_files["recorded_at"].max().date()
]

summary_stats = {
    "files_today": len(df_today),
    "avg_upload_delay": df_today["upload_delay_s"].mean(),
    "avg_compute_time": df_today["compute_time_s"].mean(),
    "avg_end_to_end": df_today["end_to_end_s"].mean(),
    "files_per_2min": len(df_today)
    / (24 * 30),  # approx 2min data per file → 30 per hour
}


def make_summary_cards():
    return dbc.Row(
        [
            dbc.Col(
                html.Div(
                    [
                        html.Div(
                            "Files Uploaded Today",
                            style={"fontSize": "12px", "color": "#888"},
                        ),
                        html.Div(
                            f"{summary_stats['files_today']}",
                            style={"fontSize": "26px"},
                        ),
                    ],
                    style={"padding": "8px"},
                ),
                md=2,
            ),
            dbc.Col(
                html.Div(
                    [
                        html.Div(
                            "Avg Upload Delay (s)",
                            style={"fontSize": "12px", "color": "#888"},
                        ),
                        html.Div(
                            f"{summary_stats['avg_upload_delay']:.1f}",
                            style={"fontSize": "26px"},
                        ),
                    ],
                    style={"padding": "8px"},
                ),
                md=2,
            ),
            dbc.Col(
                html.Div(
                    [
                        html.Div(
                            "Avg Compute Time (s)",
                            style={"fontSize": "12px", "color": "#888"},
                        ),
                        html.Div(
                            f"{summary_stats['avg_compute_time']:.1f}",
                            style={"fontSize": "26px"},
                        ),
                    ],
                    style={"padding": "8px"},
                ),
                md=2,
            ),
            dbc.Col(
                html.Div(
                    [
                        html.Div(
                            "Avg End-to-End (s)",
                            style={"fontSize": "12px", "color": "#888"},
                        ),
                        html.Div(
                            f"{summary_stats['avg_end_to_end']:.1f}",
                            style={"fontSize": "26px"},
                        ),
                    ],
                    style={"padding": "8px"},
                ),
                md=2,
            ),
            dbc.Col(
                html.Div(
                    [
                        html.Div(
                            "Files / 2 min", style={"fontSize": "12px", "color": "#888"}
                        ),
                        html.Div(
                            f"{summary_stats['files_per_2min']:.2f}",
                            style={"fontSize": "26px"},
                        ),
                    ],
                    style={"padding": "8px"},
                ),
                md=2,
            ),
        ],
        className="mb-3",
        justify="start",
    )


# ------------------------------------------------------------
# File Upload Graphs
# ------------------------------------------------------------


def make_file_timeline():
    """Graph: Recorded vs Uploaded"""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df_files["recorded_at"],
            y=df_files["file_id"],
            mode="markers+lines",
            name="Recorded",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df_files["uploaded_at"],
            y=df_files["file_id"],
            mode="markers+lines",
            name="Uploaded",
        )
    )

    fig.update_layout(
        title="File Recorded vs Uploaded Timeline",
        template="plotly_dark",
        height=1000,
        xaxis_title="Time",
        yaxis_title="File ID",
    )
    return fig


def make_file_upload_delay():
    """Graph: Upload Delay"""
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_files["recorded_at"],
            y=df_files["upload_delay_s"],
            name="Upload Delay (s)",
        )
    )
    fig.update_layout(
        title="File Upload Delay",
        template="plotly_dark",
        height=350,
        xaxis_title="Recorded Time",
        yaxis_title="Delay (seconds)",
    )
    return fig


def make_compute_time():
    """Graph: Compute Duration"""
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_files["uploaded_at"],
            y=df_files["compute_time_s"],
            name="Compute Time (s)",
        )
    )
    fig.update_layout(
        title="Compute Time per File",
        template="plotly_dark",
        height=350,
        xaxis_title="Uploaded At",
        yaxis_title="Duration (seconds)",
    )
    return fig


def make_end_to_end():
    """Graph: End-to-End Pipeline Duration"""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_files["recorded_at"],
            y=df_files["end_to_end_s"],
            mode="markers+lines",
            name="End-to-End (s)",
        )
    )
    fig.update_layout(
        title="End-to-End File Pipeline Duration",
        template="plotly_dark",
        height=350,
        xaxis_title="Recorded Time",
        yaxis_title="Total Time (seconds)",
    )
    return fig


def make_file_count():
    """Graph: File Upload Count vs Time"""
    df_bucket = df_files.resample("30min", on="uploaded_at").count()

    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_bucket.index, y=df_bucket["file_id"]))

    fig.update_layout(
        title="Number of Files Uploaded vs Time",
        template="plotly_dark",
        height=350,
        xaxis_title="Time",
        yaxis_title="File Count",
    )
    return fig


# ------------------------------------------------------------
# Minimalist Tab Styles
# ------------------------------------------------------------
TAB_STYLE = {
    "padding": "6px 12px",
    "backgroundColor": "transparent",
    "color": "#888",
    "border": "none",
    "borderTop": "0px",
    "borderLeft": "0px",
    "borderRight": "0px",
}

TAB_SELECTED_STYLE = {
    "padding": "6px 12px",
    "backgroundColor": "transparent",
    "color": "white",
    "border": "none",
    "borderTop": "0px",
    "borderLeft": "0px",
    "borderRight": "0px",
    "borderBottom": "3px solid #0d6efd",  # only underline
    "fontWeight": "500",
}


# ------------------------------------------------------------
# App Layout
# ------------------------------------------------------------
app.layout = dbc.Container(
    [
        # --------------------------------------------------------
        # Clean Minimal Header
        # --------------------------------------------------------
        html.H3(
            "S1 Dashboard",
            style={
                "textAlign": "center",
                "marginTop": "20px",
                "marginBottom": "10px",
                "fontWeight": "300",
                "letterSpacing": "1px",
                "color": "white",
            },
        ),
        # --------------------------------------------------------
        # Minimal Tabs
        # --------------------------------------------------------
        dcc.Tabs(
            [
                # --------------------------------------------------
                # TAB 1: File Uploads
                # --------------------------------------------------
                dcc.Tab(
                    label="File Uploads",
                    children=[
                        html.Br(),
                        make_summary_cards(),
                        html.Br(),
                        dcc.Graph(figure=make_file_count()),
                        dcc.Graph(figure=make_file_timeline()),
                        dcc.Graph(figure=make_file_upload_delay()),
                        dcc.Graph(figure=make_compute_time()),
                        dcc.Graph(figure=make_end_to_end()),
                    ],
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                ),
                # --------------------------------------------------
                # TAB 2: Network & Upload
                # --------------------------------------------------
                dcc.Tab(
                    label="Network & Upload",
                    children=[
                        html.Br(),
                        dcc.Graph(figure=make_file_upload_delay()),
                    ],
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                ),
                # --------------------------------------------------
                # TAB 3: Device Health
                # --------------------------------------------------
                dcc.Tab(
                    label="Device Health",
                    children=[
                        html.Br(),
                        dcc.Graph(figure=make_compute_time()),
                    ],
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                ),
                # --------------------------------------------------
                # TAB 4: Logs & Errors
                # --------------------------------------------------
                dcc.Tab(
                    label="Logs & Errors",
                    children=[
                        html.Br(),
                        dcc.Graph(figure=make_end_to_end()),
                    ],
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                ),
            ],
            style={
                "borderBottom": "1px solid #444",
                "height": "45px",
            },
        ),
    ],
    fluid=True,
)
# ------------------------------------------------------------
# Run App
# ------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
