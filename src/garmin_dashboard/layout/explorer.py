"""Explorer tab: scatter + datatable + linked run-detail panel + big 3-D route."""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from ..components.cards import panel
from ..components.detail import detail_placeholder
from ..components.table import activity_table

ROUTE3D_GRAPH = "ex-route3d"
ROUTE3D_COLORBY = "ex-route3d-colorby"


def _graph(graph_id: str, height: int = 360):
    return dcc.Graph(id=graph_id, config={"displayModeBar": False},
                     style={"height": f"{height}px"})


def _route3d_panel() -> dbc.Card:
    """Large, attribute-coloured 3-D route view for the selected run."""
    colorby = dbc.RadioItems(
        id=ROUTE3D_COLORBY,
        options=[
            {"label": "Elevation", "value": "alt"},
            {"label": "Pace", "value": "pace"},
            {"label": "Heart rate", "value": "hr"},
        ],
        value="alt", inline=True, className="control-radio route3d-colorby",
    )
    header = html.Div(
        [
            html.Div([html.Span("3-D route", className="panel-title"),
                      html.Span("rotate · zoom · colour by metric", className="panel-subtitle")]),
            html.Div(["Colour by:", colorby], className="route3d-controls"),
        ],
        className="panel-header route3d-header",
    )
    body = dcc.Loading(
        dcc.Graph(id=ROUTE3D_GRAPH, config={"displayModeBar": False, "scrollZoom": True},
                  style={"height": "70vh", "minHeight": "520px"}),
        type="default",
    )
    return dbc.Card([header, dbc.CardBody(body, className="panel-body")], className="panel")


def layout() -> dbc.Container:
    return dbc.Container(
        [
            dbc.Row(
                dbc.Col(panel("Pace vs distance", _graph("ex-scatter", 360),
                              subtitle="colour = avg heart rate · click a point to inspect a run"),
                        width=12),
                className="g-3",
            ),
            dbc.Row(
                [
                    dbc.Col(panel("Activities", activity_table(),
                                  subtitle="search, sort & select a row"), lg=7),
                    dbc.Col(panel("Run detail",
                                  dcc.Loading(html.Div(detail_placeholder(), id="ex-detail"),
                                              type="default"),
                                  className="detail-panel", subtitle="linked view"),
                            lg=5, id="ex-detail-col"),
                ],
                className="g-3 mt-1",
            ),
            dbc.Row(dbc.Col(_route3d_panel(), width=12), className="g-3 mt-1"),
        ],
        fluid=True, className="tab-body",
    )
