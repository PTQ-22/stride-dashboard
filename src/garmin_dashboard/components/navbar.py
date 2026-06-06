"""Top navigation bar with the Stride monogram and dataset date-range badge."""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import html

from ..config import APP_TAGLINE
from ..data.loader import DatasetMeta


def navbar(meta: DatasetMeta) -> dbc.Navbar:
    span = f"{meta.min_date.strftime('%b %Y')} – {meta.max_date.strftime('%b %Y')}"
    brand = html.A(
        [
            html.Img(src="/assets/logo.svg", className="brand-logo"),
            html.Div(
                [
                    html.Span("Stride", className="brand-name"),
                    html.Span(APP_TAGLINE, className="brand-tagline"),
                ],
                className="brand-text",
            ),
        ],
        href="/", className="brand-link",
    )
    badge = dbc.Badge(
        [html.I(className="bi bi-calendar3 me-2"), span],
        color=None, className="dataset-badge",
    )
    return dbc.Navbar(
        dbc.Container(
            [brand, badge],
            fluid=True, className="navbar-inner",
        ),
        className="app-navbar", dark=True,
    )
