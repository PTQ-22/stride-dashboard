"""Overview-tab callbacks: KPIs and the four summary charts."""

from __future__ import annotations

from dash import Output, callback

from ..components import charts
from ..data import transform as T
from ..layout.overview import KPI_IDS
from ._common import FILTER_INPUTS, GRANULARITY_INPUT, filtered_frame


@callback(
    [Output(f"kpi-{k}", "children") for k in KPI_IDS],
    Output("ov-volume", "figure"),
    Output("ov-cumulative", "figure"),
    Output("ov-donut", "figure"),
    Output("ov-heatmap", "figure"),
    *FILTER_INPUTS,
    GRANULARITY_INPUT,
)
def update_overview(sports, date_idx, distance, granularity):
    df = filtered_frame(sports, date_idx, distance)

    kpi = T.kpi_summary(df)
    kpi_values = [kpi[k] for k in KPI_IDS]

    return (
        *kpi_values,
        charts.volume_chart(T.volume_over_time(df, granularity), granularity),
        charts.cumulative_distance_chart(df),
        charts.activity_donut(T.activity_breakdown(df)),
        charts.monthly_heatmap(df),
    )
