"""Explorer-tab callbacks, including the linked table/scatter/detail/map views.

Selection flow
--------------
1. ``populate_table``     filters -> table rows (and clears any selection).
2. ``resolve_selection``  a table row OR a scatter click -> selected activity id
                          (stored in ``selected-activity``).
3. ``render_explorer``    filters + selected id -> scatter, map and detail panel.

Keeping the selected id in a ``dcc.Store`` decouples the two possible selection
*sources* (table, plot) from the three *consumers* (scatter highlight, map
highlight, detail panel), which avoids a tangle of cross-wired callbacks.
"""

from __future__ import annotations

from dash import Input, Output, State, callback, ctx, no_update

from ..components import charts
from ..components.charts_3d import route_3d
from ..components.detail import run_detail
from ..components.map import route_map
from ..components.table import TABLE_ID, to_table_records
from ..data import get_activities, get_tracks
from ..data import transform as T
from ..layout.explorer import ROUTE3D_COLORBY, ROUTE3D_GRAPH
from ..layout.main import SELECTED_STORE
from ..layout.map_tab import MAP_GRAPH
from ..theme import empty_figure
from ._common import FILTER_INPUTS, filtered_frame

SCATTER_ID = "ex-scatter"
DETAIL_ID = "ex-detail"


@callback(
    Output(TABLE_ID, "data"),
    Output(TABLE_ID, "selected_rows"),
    *FILTER_INPUTS,
)
def populate_table(sports, date_idx, distance):
    """Refresh table rows whenever the global filters change."""
    df = filtered_frame(sports, date_idx, distance)
    return to_table_records(df), []


@callback(
    Output(SELECTED_STORE, "data"),
    Input(TABLE_ID, "selected_rows"),
    Input(SCATTER_ID, "clickData"),
    State(TABLE_ID, "data"),
)
def resolve_selection(selected_rows, click_data, table_data):
    """Map either selection source to a single activity id (or ``None``)."""
    trigger = ctx.triggered_id
    if trigger == TABLE_ID:
        if selected_rows and table_data:
            return table_data[selected_rows[0]]["activity_id"]
        return None
    if trigger == SCATTER_ID and click_data:
        point = click_data["points"][0]
        custom = point.get("customdata")
        if custom:
            return custom[0]
    return no_update


@callback(
    Output(SCATTER_ID, "figure"),
    Output(DETAIL_ID, "children"),
    *FILTER_INPUTS,
    Input(SELECTED_STORE, "data"),
)
def render_explorer(sports, date_idx, distance, selected_id):
    """Render scatter and the linked detail panel for filters + selection."""
    df = filtered_frame(sports, date_idx, distance)
    runs = T.pace_trend(df)  # running activities with a valid pace
    selected_run = T.get_activity(df, selected_id) if selected_id is not None else None
    return (
        charts.pace_vs_distance_scatter(runs, selected_id),
        run_detail(selected_run, get_tracks()),
    )


@callback(
    Output(MAP_GRAPH, "figure"),
    *FILTER_INPUTS,
    Input(SELECTED_STORE, "data"),
)
def render_map(sports, date_idx, distance, selected_id):
    """Render the big coverage map (Map tab), reacting to filters + selection."""
    df = filtered_frame(sports, date_idx, distance)
    return route_map(df, get_tracks(), selected_id)


@callback(
    Output(ROUTE3D_GRAPH, "figure"),
    Input(SELECTED_STORE, "data"),
    Input(ROUTE3D_COLORBY, "value"),
)
def render_route_3d(selected_id, color_by):
    """Render the large 3-D route of the selected run, coloured by chosen metric."""
    if selected_id is None:
        return empty_figure("Select a run (table or scatter) to see its 3-D route")
    tracks = get_tracks()
    trk = tracks[tracks["activity_id"] == float(selected_id)]
    df = get_activities()
    row = df[df["activity_id"] == float(selected_id)]
    name = row["name"].iloc[0] if not row.empty else ""
    return route_3d(trk, color_by or "alt", name)
