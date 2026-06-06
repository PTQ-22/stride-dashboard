"""Small presentational building blocks: KPI tiles and panel wrappers."""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import html


def kpi_card(card_id: str, icon: str, label: str, value: str = "–") -> dbc.Col:
    """A single headline-metric tile. ``value`` is updated by a callback."""
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.I(className=f"bi {icon} kpi-icon"),
                    html.Div(value, id=card_id, className="kpi-value"),
                    html.Div(label, className="kpi-label"),
                ]
            ),
            className="kpi-card h-100",
        ),
        xs=6, md=4, xl=2, className="mb-3",
    )


def panel(title: str, body, *, subtitle: str | None = None, className: str = "") -> dbc.Card:
    """A titled surface used to frame every chart/table in a consistent way."""
    header = [html.Span(title, className="panel-title")]
    if subtitle:
        header.append(html.Span(subtitle, className="panel-subtitle"))
    return dbc.Card(
        [
            dbc.CardHeader(header, className="panel-header"),
            dbc.CardBody(body, className="panel-body"),
        ],
        className=f"panel {className}",
    )


def stat_row(label: str, value: str, icon: str | None = None) -> html.Div:
    """A label/value line used inside the run-detail panel."""
    left = [html.I(className=f"bi {icon} me-2") if icon else None, label]
    return html.Div(
        [html.Span(left, className="stat-label"), html.Span(value, className="stat-value")],
        className="stat-row",
    )
