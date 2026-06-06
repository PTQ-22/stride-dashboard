"""Geographic views of where activities happened.

Primary view draws the **full GPS routes** of the filtered activities as
translucent polylines, building a personal "heatmap" of training coverage. The
selected activity's route is overlaid in the accent colour and the camera zooms
to it. When no track data is available the module degrades gracefully to
start-point markers.

Uses Plotly's MapLibre basemaps (``carto-darkmatter``), which need no API token,
so the live demo works without secrets.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from ..theme import COLORS, SEQUENTIAL, empty_figure


# Default camera: the Poznań / Swarzędz home-training area, where the vast
# majority of activities take place (the dataset also contains far-away travel
# runs that would otherwise zoom the map all the way out to fit them).
FOCUS_CENTER = dict(lat=52.418, lon=17.01)
FOCUS_ZOOM = 10.6


def _zoom_for_span(lat_span: float, lng_span: float) -> float:
    """Rough world-tile zoom that fits the given degree span."""
    span = max(lat_span, lng_span, 1e-3)
    return float(np.clip(math.log2(360.0 / span) - 0.5, 3, 15))


# Coverage layer is decimated for snappy WebGL rendering; the selected route
# is always drawn at full stored resolution.
_COVERAGE_STRIDE = 4


def _coverage_traces(tracks: pd.DataFrame) -> tuple[list, list]:
    """Flatten per-activity tracks into one lat/lng stream with ``None`` breaks.

    A ``None`` between activities lets a single Scattermap trace draw many
    disconnected polylines cheaply. (``None`` — not ``NaN`` — is required: NaN
    coordinates break MapLibre's WebGL renderer.)
    """
    lats: list = []
    lngs: list = []
    for _, grp in tracks.groupby("activity_id", sort=False):
        lats.extend(grp["lat"].iloc[::_COVERAGE_STRIDE].tolist() + [None])
        lngs.extend(grp["lng"].iloc[::_COVERAGE_STRIDE].tolist() + [None])
    return lats, lngs


def route_map(
    activities: pd.DataFrame,
    tracks: pd.DataFrame,
    selected_id: float | None = None,
) -> go.Figure:
    """Coverage map of all filtered routes, with the selected route highlighted."""
    ids = set(activities["activity_id"].tolist())
    trk = tracks[tracks["activity_id"].isin(ids)] if not tracks.empty else tracks

    if trk.empty:
        return _start_point_fallback(activities, selected_id)

    fig = go.Figure()
    cov_lat, cov_lng = _coverage_traces(trk)
    fig.add_trace(
        go.Scattermap(
            lat=cov_lat, lon=cov_lng, mode="lines",
            line=dict(color="rgba(255,107,53,0.35)", width=1.6),
            hoverinfo="skip", name="routes",
        )
    )

    # default camera = home-training area (not the global bounds, which include
    # far-away travel runs)
    center, zoom = FOCUS_CENTER, FOCUS_ZOOM

    if selected_id is not None:
        sel = trk[trk["activity_id"] == float(selected_id)]
        if not sel.empty:
            fig.add_trace(
                go.Scattermap(
                    lat=sel["lat"], lon=sel["lng"], mode="lines",
                    line=dict(color=COLORS["accent"], width=4),
                    hoverinfo="skip", name="selected route",
                )
            )
            fig.add_trace(
                go.Scattermap(
                    lat=[sel["lat"].iloc[0]], lon=[sel["lng"].iloc[0]], mode="markers",
                    marker=dict(size=12, color=COLORS["good"]),
                    hoverinfo="skip", name="start",
                )
            )
            center = dict(lat=float(sel["lat"].mean()), lon=float(sel["lng"].mean()))
            zoom = _zoom_for_span(sel["lat"].max() - sel["lat"].min(),
                                  sel["lng"].max() - sel["lng"].min())

    fig.update_layout(
        map=dict(style="carto-darkmatter", center=center, zoom=zoom),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
    )
    return fig


def _start_point_fallback(df: pd.DataFrame, selected_id: float | None) -> go.Figure:
    """Start-location markers, used when no GPS tracks are available."""
    geo = df.dropna(subset=["start_lat", "start_lng"])
    geo = geo[(geo["start_lat"].between(-90, 90)) & (geo["start_lng"].between(-180, 180))]
    if geo.empty:
        return empty_figure("No GPS data in range")
    fig = go.Figure(
        go.Scattermap(
            lat=geo["start_lat"], lon=geo["start_lng"], mode="markers",
            marker=dict(size=9, color=geo["distance_km"], colorscale=SEQUENTIAL,
                        showscale=True, colorbar=dict(title="km", thickness=10), opacity=0.75),
            customdata=geo[["name", "distance_km"]],
            hovertemplate="%{customdata[0]}<br>%{customdata[1]:.1f} km<extra></extra>",
        )
    )
    center = dict(lat=geo["start_lat"].median(), lon=geo["start_lng"].median())
    zoom = 10
    if selected_id is not None:
        sel = geo[geo["activity_id"] == float(selected_id)]
        if not sel.empty:
            fig.add_trace(go.Scattermap(
                lat=sel["start_lat"], lon=sel["start_lng"], mode="markers",
                marker=dict(size=20, color=COLORS["accent"]), hoverinfo="skip"))
            center = dict(lat=float(sel["start_lat"].iloc[0]), lon=float(sel["start_lng"].iloc[0]))
            zoom = 13
    fig.update_layout(
        map=dict(style="carto-darkmatter", center=center, zoom=zoom),
        margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
    )
    return fig
