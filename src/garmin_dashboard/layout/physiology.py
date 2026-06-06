"""Performance tab: fitness & form — VO2max, aerobic efficiency, pace, cadence."""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc

from ..components.cards import panel


def _graph(graph_id: str, height: int = 320):
    return dcc.Graph(id=graph_id, config={"displayModeBar": False},
                     style={"height": f"{height}px"})


def layout() -> dbc.Container:
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(panel("Aerobic fitness", _graph("phys-vo2", 320),
                                  subtitle="estimated VO₂max trajectory"), lg=6),
                    dbc.Col(panel("Aerobic efficiency", _graph("phys-ef", 320),
                                  subtitle="heart rate vs pace, by year · down/right = fitter"), lg=6),
                ],
                className="g-3",
            ),
            dbc.Row(
                [
                    dbc.Col(panel("Pace by year", _graph("phys-pace", 340),
                                  subtitle="how the pace distribution shifts each year"), lg=6),
                    dbc.Col(panel("Running form", _graph("phys-cadence", 340),
                                  subtitle="cadence vs pace, coloured by heart rate"), lg=6),
                ],
                className="g-3 mt-1",
            ),
            dbc.Row(
                dbc.Col(panel("Effort distribution", _graph("phys-zones", 300),
                              subtitle="total time in each heart-rate zone"), width=12),
                className="g-3 mt-1",
            ),
        ],
        fluid=True, className="tab-body",
    )
