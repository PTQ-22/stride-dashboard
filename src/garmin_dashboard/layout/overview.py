"""Overview tab: KPIs + volume, mix and calendar visualisations."""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc

from ..components.cards import kpi_card, panel

# KPI ids consumed by the overview callback.
KPI_IDS = {
    "activities": ("bi-list-check", "Activities"),
    "distance": ("bi-rulers", "Total distance"),
    "time": ("bi-stopwatch", "Moving time"),
    "pace": ("bi-speedometer2", "Median pace"),
    "elevation": ("bi-graph-up-arrow", "Elevation gain"),
    "vo2max": ("bi-lungs", "Latest VO₂max"),
}


def _graph(graph_id: str, height: int = 320):
    return dcc.Graph(id=graph_id, config={"displayModeBar": False},
                     style={"height": f"{height}px"})


def layout() -> dbc.Container:
    kpis = dbc.Row(
        [kpi_card(f"kpi-{k}", icon, label) for k, (icon, label) in KPI_IDS.items()],
        className="g-3",
    )
    return dbc.Container(
        [
            kpis,
            dbc.Row(
                dbc.Col(panel("Training volume", _graph("ov-volume", 340),
                              subtitle="distance & activity count over time"), width=12),
                className="g-3 mt-1",
            ),
            dbc.Row(
                [
                    dbc.Col(panel("Cumulative distance", _graph("ov-cumulative", 320),
                                  subtitle="kilometres banked over the years"), lg=8),
                    dbc.Col(panel("Activity mix", _graph("ov-donut", 320)), lg=4),
                ],
                className="g-3 mt-1",
            ),
            dbc.Row(
                dbc.Col(panel("Distance calendar", _graph("ov-heatmap", 300),
                              subtitle="total kilometres per month"), width=12),
                className="g-3 mt-1",
            ),
        ],
        fluid=True, className="tab-body",
    )
