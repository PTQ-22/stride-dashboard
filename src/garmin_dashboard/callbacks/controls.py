"""Control-panel callbacks (reset button restores all filters to defaults)."""

from __future__ import annotations

from dash import Input, Output, callback

from ..components.controls import (
    DATE_LABEL, DATE_RANGE, DISTANCE_SLIDER, GRANULARITY, RESET_BTN, SPORT_CHECKLIST,
)
from ..data.loader import get_meta


@callback(
    Output(DATE_RANGE, "value"),
    Output(SPORT_CHECKLIST, "value"),
    Output(DISTANCE_SLIDER, "value"),
    Output(GRANULARITY, "value"),
    Input(RESET_BTN, "n_clicks"),
    prevent_initial_call=True,
)
def reset_filters(_n_clicks):
    meta = get_meta()
    max_km = int(meta.max_distance_km) + 1
    return ([0, len(meta.months) - 1], meta.sport_types, [0, max_km], "M")


@callback(
    Output(DATE_LABEL, "children"),
    Input(DATE_RANGE, "value"),
)
def update_date_label(date_idx):
    """Show the human-readable month range above the slider."""
    meta = get_meta()
    start, end = meta.month_bounds(tuple(date_idx))
    return f"{start.strftime('%b %Y')} — {end.strftime('%b %Y')}"
