"""About / Help tab: project description, dataset notes and usage guide."""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import html

from .. import __version__
from ..components.cards import panel
from ..data.loader import DatasetMeta


def _help_item(icon: str, title: str, text: str) -> html.Div:
    return html.Div(
        [
            html.I(className=f"bi {icon} help-icon"),
            html.Div([html.Strong(title), html.P(text)], className="help-text"),
        ],
        className="help-item",
    )


def layout(meta: DatasetMeta) -> dbc.Container:
    about = panel(
        "About Stride",
        html.Div(
            [
                html.P(
                    "Stride is an interactive dashboard for exploring six years of "
                    "personal running data exported from a Garmin Connect account. "
                    "It turns a raw activity log into a story about training volume, "
                    "pace progression, cardiovascular fitness and running form."
                ),
                html.P(
                    [
                        f"The dataset covers {meta.n_activities:,} activities recorded "
                        f"between {meta.min_date.strftime('%B %Y')} and "
                        f"{meta.max_date.strftime('%B %Y')}, including runs, rides, "
                        "walks and one mountaineering outing.",
                    ]
                ),
                html.P(
                    [
                        "Built with ", html.Strong("Dash"), ", ", html.Strong("Plotly"),
                        " and ", html.Strong("pandas"), ". Data is processed offline by an "
                        "ETL script (", html.Code("scripts/prepare_data.py"),
                        ") that normalises Garmin's raw units into km, minutes and min/km.",
                    ]
                ),
            ]
        ),
    )
    how = panel(
        "How to use it",
        html.Div(
            [
                _help_item("bi-sliders", "Filter globally",
                           "Use the left-hand panel to set a date range, pick sports and "
                           "constrain distance. Every chart and the table react instantly."),
                _help_item("bi-graph-up", "Read the Overview",
                           "Headline KPIs plus volume, pace, activity mix and a distance "
                           "calendar give the big picture at a glance."),
                _help_item("bi-table", "Explore activities",
                           "On the Explorer tab, click a scatter point or select a table "
                           "row — the detail panel and map update to that exact run."),
                _help_item("bi-heart-pulse", "Dig into physiology",
                           "The Physiology tab tracks VO₂max, running form (cadence vs "
                           "pace) and how effort is distributed across heart-rate zones."),
            ]
        ),
    )
    return dbc.Container(
        [
            dbc.Row(
                [dbc.Col(about, lg=6), dbc.Col(how, lg=6)],
                className="g-3",
            ),
            html.Div(
                [
                    html.Span(f"Stride v{__version__}"),
                    html.Span(" · data is personal & used with consent · "),
                    html.A("source on GitHub", href="https://github.com/", target="_blank"),
                ],
                className="about-footer",
            ),
        ],
        fluid=True, className="tab-body",
    )
