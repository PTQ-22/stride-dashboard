"""The activities DataTable used on the Explorer tab.

Selecting a row drives the linked detail panel and highlights the matching
point on the scatter plot, satisfying the cross-component interaction
requirement.
"""

from __future__ import annotations

import pandas as pd
from dash import dash_table

from ..theme import COLORS
from ..data.transform import format_pace

TABLE_ID = "activity-table"

# (column id, display name) — kept narrow for readability.
COLUMNS = [
    ("date_str", "Date"),
    ("name", "Activity"),
    ("activity_type", "Sport"),
    ("distance_km", "Distance (km)"),
    ("pace_str", "Pace /km"),
    ("avg_hr", "Avg HR"),
    ("duration_str", "Time"),
]


def to_table_records(df: pd.DataFrame) -> list[dict]:
    """Project the activities frame into display-ready table rows."""
    if df.empty:
        return []
    out = pd.DataFrame({
        "activity_id": df["activity_id"],
        "date_str": df["start_time"].dt.strftime("%Y-%m-%d"),
        "name": df["name"],
        "activity_type": df["activity_type"].str.capitalize(),
        "distance_km": df["distance_km"].round(2),
        "pace_str": df["pace_min_km"].apply(format_pace),
        "avg_hr": df["avg_hr"].round(0),
        "duration_str": df["duration_min"].apply(
            lambda m: f"{int(m // 60)}h {int(m % 60):02d}m" if m >= 60 else f"{int(m)}m"
        ),
    })
    return out.sort_values("date_str", ascending=False).to_dict("records")


def activity_table() -> dash_table.DataTable:
    """Build the (empty) DataTable; rows are injected by a callback."""
    return dash_table.DataTable(
        id=TABLE_ID,
        columns=[{"name": disp, "id": cid} for cid, disp in COLUMNS],
        data=[],
        row_selectable="single",
        selected_rows=[],
        sort_action="native",
        sort_by=[{"column_id": "date_str", "direction": "desc"}],
        filter_action="native",
        page_action="native",
        page_size=11,
        cell_selectable=False,
        style_as_list_view=True,
        style_table={"overflowX": "auto", "minHeight": "440px"},
        style_header={
            "backgroundColor": COLORS["surface_alt"],
            "color": COLORS["text_muted"],
            "fontWeight": "600",
            "border": "none",
            "textTransform": "uppercase",
            "fontSize": "11px",
            "letterSpacing": "0.04em",
        },
        style_cell={
            "backgroundColor": COLORS["surface"],
            "color": COLORS["text"],
            "border": "none",
            "borderBottom": f"1px solid {COLORS['grid']}",
            "padding": "10px 12px",
            "fontFamily": "Inter, sans-serif",
            "fontSize": "13px",
            "textAlign": "left",
        },
        style_data_conditional=[
            {"if": {"state": "selected"},
             "backgroundColor": "rgba(255,107,53,0.18)",
             "border": "none"},
            {"if": {"row_index": "odd"}, "backgroundColor": COLORS["surface_alt"]},
        ],
        style_filter={"backgroundColor": COLORS["surface_alt"], "color": COLORS["text"]},
    )
