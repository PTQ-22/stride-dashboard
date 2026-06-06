"""The linked run-detail panel shown on the Explorer tab.

Rendered from a single activity row when the user selects a table row or
clicks a scatter point. This is the 'select-here-updates-there' interaction.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html

from ..config import HR_ZONE_COLS, HR_ZONE_LABELS
from ..data.transform import format_duration as fmt_duration
from ..data.transform import format_pace as fmt_pace
from ..theme import COLORS, apply_theme
from .cards import stat_row


def _zone_mini(run: pd.Series) -> go.Figure:
    mins = [float(run.get(c, 0) or 0) for c in HR_ZONE_COLS]
    palette = [COLORS["grid"], COLORS["secondary"], COLORS["good"],
               COLORS["warn"], COLORS["accent"], "#e03131"]
    fig = go.Figure(go.Bar(
        x=[HR_ZONE_LABELS[i].split(" · ")[0] for i in range(6)],
        y=mins, marker_color=palette,
        hovertemplate="%{x}<br>%{y:.0f} min<extra></extra>",
    ))
    apply_theme(fig, height=170, margin=dict(l=30, r=8, t=8, b=24),
                yaxis=dict(title=""), xaxis=dict(title=""))
    return fig


def detail_placeholder() -> html.Div:
    return html.Div(
        [
            html.I(className="bi bi-hand-index-thumb detail-hint-icon"),
            html.P("Select a run from the table or scatter plot to inspect it."),
        ],
        className="detail-placeholder",
    )


def run_detail(run: pd.Series | None, tracks: pd.DataFrame | None = None) -> html.Div:
    """Render the detail card for a selected activity (or a hint if none).

    When GPS+elevation track data is available for the activity, a rotatable
    3-D elevation profile of the route is appended.
    """
    if run is None:
        return detail_placeholder()

    sport = str(run["activity_type"]).capitalize()
    date = pd.to_datetime(run["start_time"]).strftime("%A, %d %B %Y · %H:%M")
    return html.Div(
        [
            html.Div(
                [
                    html.Span(sport, className="detail-badge"),
                    html.H4(run["name"], className="detail-title"),
                    html.Span(date, className="detail-date"),
                    html.Span([html.I(className="bi bi-geo-alt me-1"), run.get("location", "Unknown")],
                              className="detail-location"),
                ],
                className="detail-head",
            ),
            html.Div(
                [
                    stat_row("Distance", f"{run['distance_km']:.2f} km", "bi-rulers"),
                    stat_row("Pace", f"{fmt_pace(run['pace_min_km'])} /km", "bi-speedometer2"),
                    stat_row("Moving time", fmt_duration(run["duration_min"]), "bi-stopwatch"),
                    stat_row("Avg / Max HR", f"{_num(run['avg_hr'])} / {_num(run['max_hr'])} bpm", "bi-heart-pulse"),
                    stat_row("Cadence", f"{_num(run['cadence_spm'])} spm", "bi-arrow-repeat"),
                    stat_row("Elevation gain", f"{_num(run['elevation_gain_m'])} m", "bi-graph-up-arrow"),
                    stat_row("Calories", f"{_num(run['calories'])} kcal", "bi-fire"),
                    stat_row("VO₂max", _num(run["vo2max"]), "bi-lungs"),
                ],
                className="detail-stats",
            ),
            html.Div("Heart-rate zones", className="detail-section-label"),
            dcc.Graph(figure=_zone_mini(run), config={"displayModeBar": False}),
        ],
        className="detail-content",
    )


def _num(v) -> str:
    return "–" if v is None or pd.isna(v) else f"{v:.0f}"
