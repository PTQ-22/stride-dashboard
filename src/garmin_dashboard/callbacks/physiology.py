"""Physiology-tab callbacks: VO2max, running form and effort distribution."""

from __future__ import annotations

from dash import Output, callback

from ..components import charts
from ..data import transform as T
from ._common import FILTER_INPUTS, filtered_frame


@callback(
    Output("phys-vo2", "figure"),
    Output("phys-ef", "figure"),
    Output("phys-pace", "figure"),
    Output("phys-cadence", "figure"),
    Output("phys-zones", "figure"),
    *FILTER_INPUTS,
)
def update_physiology(sports, date_idx, distance):
    df = filtered_frame(sports, date_idx, distance)
    runs = df[df["activity_type"] == "running"]
    return (
        charts.vo2max_chart(T.vo2max_trend(df)),
        charts.hr_vs_pace_chart(runs),
        charts.pace_by_year_chart(T.pace_trend(df)),
        charts.cadence_pace_chart(runs),
        charts.hr_zone_chart(T.hr_zone_distribution(df)),
    )
