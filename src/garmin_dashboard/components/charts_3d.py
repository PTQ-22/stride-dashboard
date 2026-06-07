"""Three-dimensional view of a single activity's GPS track.

The 3-D *shape* is always longitude × latitude × elevation (so hills read as
hills); the marker *colour* encodes a user-chosen metric — elevation, pace or
heart rate — turning one run into a rich, rotatable story.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from ..data.basemaps import get_basemap
from ..theme import COLORS, apply_theme, empty_figure

# Dark ramp tuned for Carto "dark matter" tiles: near-black background with
# streets lifting to a muted blue-gray — matches the Map tab's basemap.
_MAP_COLORSCALE = [[0.0, "#0c0f15"], [0.5, "#222a36"], [1.0, "#48566b"]]

# colour-by option -> (track column, label, colorscale, reverse?)
COLOR_OPTIONS = {
    "alt": ("alt", "Elevation (m)", "Viridis", False),
    "pace": ("pace", "Pace (min/km)", "RdYlGn", False),   # green = fast (low)
    "hr": ("hr", "Heart rate (bpm)", "Turbo", False),
}


def route_3d(track: pd.DataFrame, color_by: str = "alt", name: str = "") -> go.Figure:
    """Rotatable 3-D route coloured by the selected metric."""
    if track.empty or "alt" not in track.columns or track["alt"].dropna().empty:
        return empty_figure("No elevation/GPS data for this activity")

    track = track.sort_values("seq").copy()
    col, label, scale, reverse = COLOR_OPTIONS.get(color_by, COLOR_OPTIONS["alt"])
    if col not in track.columns or track[col].dropna().empty:
        col, label, scale, reverse = COLOR_OPTIONS["alt"]

    values = pd.to_numeric(track[col], errors="coerce")
    # Smooth elevation: consumer-GPS altitude is noisy, and small jitter looks
    # like dramatic relief once the vertical axis is stretched. A centred
    # rolling mean averages it out so the profile reads honestly.
    alt_raw = pd.to_numeric(track["alt"], errors="coerce").ffill().bfill().fillna(0)
    win = max(3, len(track) // 25)
    alt = alt_raw.rolling(win, center=True, min_periods=1).mean()

    cmin = float(np.nanpercentile(values, 2)) if values.notna().any() else None
    cmax = float(np.nanpercentile(values, 98)) if values.notna().any() else None
    cvals = values.ffill().bfill().fillna(0)
    fig = go.Figure(
        go.Scatter3d(
            x=track["lng"], y=track["lat"], z=alt,
            mode="lines+markers",
            line=dict(color=cvals, colorscale=scale, reversescale=reverse,
                      width=6, cmin=cmin, cmax=cmax),
            marker=dict(
                size=2, color=cvals, colorscale=scale, reversescale=reverse,
                cmin=cmin, cmax=cmax, showscale=True,
                colorbar=dict(title=dict(text=label, side="right"), thickness=12,
                              len=0.75, x=1.0, y=0.5, yanchor="middle"),
            ),
            customdata=np.stack([cvals, alt], axis=-1),
            hovertemplate=f"{label}: %{{customdata[0]:.1f}}<br>elev %{{z:.0f}} m<extra></extra>",
            name=name, showlegend=False,
        )
    )

    # --- ground reference floor, placed below the route ---
    span = max(float(alt.max() - alt.min()), 1.0)
    floor = float(alt.min()) - span * 0.25
    aid = track["activity_id"].iloc[0] if "activity_id" in track.columns else None
    basemap = get_basemap(aid) if aid is not None else None

    if basemap is not None:
        # real (pre-fetched) grayscale OpenStreetMap textured onto the floor
        grid, extent = basemap
        rows, cols = grid.shape
        xs = np.linspace(extent[0], extent[1], cols)
        ys = np.linspace(extent[2], extent[3], rows)
        fig.add_trace(go.Surface(
            x=xs, y=ys, z=np.full((rows, cols), floor), surfacecolor=grid,
            colorscale=_MAP_COLORSCALE, showscale=False, opacity=1.0,
            lighting=dict(ambient=1, diffuse=0, specular=0), hoverinfo="skip",
        ))
    else:
        # fallback: faint plane when no basemap was pre-fetched
        lng_lo, lng_hi = track["lng"].min(), track["lng"].max()
        lat_lo, lat_hi = track["lat"].min(), track["lat"].max()
        px, py = (lng_hi - lng_lo) * 0.06 + 1e-4, (lat_hi - lat_lo) * 0.06 + 1e-4
        fig.add_trace(go.Mesh3d(
            x=[lng_lo - px, lng_hi + px, lng_hi + px, lng_lo - px],
            y=[lat_lo - py, lat_lo - py, lat_hi + py, lat_hi + py],
            z=[floor] * 4, i=[0, 0], j=[1, 2], k=[2, 3],
            color="#4cc9f0", opacity=0.06, hoverinfo="skip", showscale=False,
        ))

    # route footprint projected just above the floor (a small lift avoids
    # z-fighting with the map surface, which made the line look broken)
    fig.add_trace(go.Scatter3d(
        x=track["lng"], y=track["lat"], z=[floor + span * 0.015] * len(track),
        mode="lines", line=dict(color="rgba(255,107,53,0.85)", width=3),
        hoverinfo="skip", showlegend=False, name="footprint",
    ))

    s, e = track.iloc[0], track.iloc[-1]
    az = alt.to_numpy()
    fig.add_trace(go.Scatter3d(
        x=[s["lng"]], y=[s["lat"]], z=[az[0]], mode="markers", name="Start",
        marker=dict(size=7, color="#69db7c", line=dict(width=1, color="#0d0f14")),
        hovertemplate="Start<extra></extra>",
    ))
    fig.add_trace(go.Scatter3d(
        x=[e["lng"]], y=[e["lat"]], z=[az[-1]], mode="markers", name="Finish",
        marker=dict(size=7, color="#e03131", symbol="diamond",
                    line=dict(width=1, color="#0d0f14")),
        hovertemplate="Finish<extra></extra>",
    ))

    # Keep lon/lat to scale with each other (equirectangular latitude
    # correction); keep the vertical gently compressed so smoothed relief reads
    # honestly rather than as mountains.
    lat0 = float(track["lat"].mean())
    axis_common = dict(showbackground=True, backgroundcolor="#16181f",
                       gridcolor=COLORS["grid"], color=COLORS["text_muted"],
                       showticklabels=True, tickfont=dict(size=9), nticks=6)
    fig.update_layout(
        scene=dict(
            xaxis=dict(title="longitude", tickformat=".3f", **axis_common),
            yaxis=dict(title="latitude", tickformat=".3f", **axis_common),
            zaxis=dict(title="elevation (m)", **axis_common),
            aspectmode="manual",
            aspectratio=dict(x=1.0, y=1.0 / max(np.cos(np.radians(lat0)), 0.3), z=0.22),
            camera=dict(eye=dict(x=1.4, y=1.4, z=0.85)),
        ),
        margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(0,0,0,0)",
                    font=dict(color=COLORS["text_muted"], size=11)),
    )
    return apply_theme(fig)
