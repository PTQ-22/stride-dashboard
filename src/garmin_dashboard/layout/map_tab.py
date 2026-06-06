"""Map tab: a large route-coverage map of every recorded GPS track."""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from ..components.cards import panel

MAP_GRAPH = "map-coverage"


def layout() -> dbc.Container:
    body = [
        dcc.Graph(
            id=MAP_GRAPH,
            config={"displayModeBar": False, "scrollZoom": True},
            style={"height": "74vh", "minHeight": "560px"},
        ),
        html.Div(
            "Every GPS-recorded activity drawn as a translucent route — repeated "
            "streets build up into a personal heatmap of where the training "
            "happens. Filter by date, sport or distance on the left; select a run "
            "on the Explorer tab to highlight it here.",
            className="map-caption",
        ),
    ]
    return dbc.Container(
        panel("Route coverage", body, subtitle="all GPS tracks · scroll to zoom"),
        fluid=True, className="tab-body",
    )
