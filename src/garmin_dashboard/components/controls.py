"""The global filter panel shared by the Overview and Explorer tabs.

Widget IDs are defined here as module constants so callbacks can import them
instead of hard-coding strings (single source of truth for the wiring).
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from ..data.loader import DatasetMeta
from ..theme import SPORT_COLORS

# --- widget ids (imported by callbacks) ---
DATE_RANGE = "ctl-date-range"
DATE_LABEL = "ctl-date-label"
SPORT_CHECKLIST = "ctl-sports"
DISTANCE_SLIDER = "ctl-distance"
GRANULARITY = "ctl-granularity"
RESET_BTN = "ctl-reset"


def _date_range_slider(meta: DatasetMeta) -> html.Div:
    """A themeable month-range slider (replaces the un-stylable calendar)."""
    n = len(meta.months)
    # one mark per January (plus the first month) so the axis stays readable
    marks = {
        i: {"label": ts.strftime("'%y"), "style": {"color": "#8b91a3", "fontSize": "10px"}}
        for i, ts in enumerate(meta.months) if ts.month == 1
    }
    marks[0] = {"label": meta.months[0].strftime("'%y"),
                "style": {"color": "#8b91a3", "fontSize": "10px"}}
    return html.Div(
        [
            html.Div(id=DATE_LABEL, className="date-range-label"),
            dcc.RangeSlider(
                id=DATE_RANGE, min=0, max=n - 1, step=1, value=[0, n - 1],
                marks=marks, allowCross=False, pushable=1,
                tooltip={"placement": "bottom", "always_visible": False},
                className="control-slider date-slider",
            ),
        ]
    )


def control_panel(meta: DatasetMeta) -> dbc.Card:
    """Build the filter sidebar, seeded with the dataset's real bounds."""
    sport_options = [
        {
            "label": html.Span(
                [html.Span(className="legend-dot", style={"background": SPORT_COLORS.get(s, "#888")}),
                 s.capitalize()],
                className="sport-option",
            ),
            "value": s,
        }
        for s in meta.sport_types
    ]
    max_km = int(meta.max_distance_km) + 1
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div("Filters", className="controls-heading"),

                html.Label("Date range", className="control-label"),
                _date_range_slider(meta),

                html.Label("Activity type", className="control-label mt-3"),
                dbc.Checklist(
                    id=SPORT_CHECKLIST,
                    options=sport_options,
                    value=meta.sport_types,
                    className="control-checklist",
                ),

                html.Label("Distance (km)", className="control-label mt-3"),
                dcc.RangeSlider(
                    id=DISTANCE_SLIDER,
                    min=0, max=max_km, step=1,
                    value=[0, max_km],
                    marks={0: "0", max_km: str(max_km)},
                    tooltip={"placement": "bottom", "always_visible": False},
                    className="control-slider",
                ),

                html.Label("Volume granularity", className="control-label mt-3"),
                dbc.RadioItems(
                    id=GRANULARITY,
                    options=[{"label": "Weekly", "value": "W"}, {"label": "Monthly", "value": "M"}],
                    value="M",
                    inline=True,
                    className="control-radio",
                ),

                dbc.Button(
                    [html.I(className="bi bi-arrow-counterclockwise me-2"), "Reset filters"],
                    id=RESET_BTN, color="secondary", outline=True, size="sm",
                    className="mt-4 w-100",
                ),
            ]
        ),
        className="controls-card",
    )
