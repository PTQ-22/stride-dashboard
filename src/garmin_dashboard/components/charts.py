"""Plotly figure factories.

Each function takes an already-shaped DataFrame (see :mod:`data.transform`) and
returns a themed :class:`plotly.graph_objects.Figure`. They never touch global
state, which keeps them pure and easy to reason about.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from ..theme import COLORS, SEQUENTIAL, SPORT_COLORS, apply_theme, empty_figure


def volume_chart(agg: pd.DataFrame, freq: str = "W") -> go.Figure:
    """Bars of distance per period with a count line on a secondary axis."""
    if agg.empty:
        return empty_figure()
    fig = go.Figure()
    fig.add_bar(
        x=agg["period"], y=agg["distance_km"], name="Distance",
        marker_color=COLORS["accent"], opacity=0.85,
        hovertemplate="%{x|%d %b %Y}<br>%{y:.1f} km<extra></extra>",
    )
    fig.add_scatter(
        x=agg["period"], y=agg["count"], name="Activities", yaxis="y2",
        mode="lines+markers", line=dict(color=COLORS["secondary"], width=2),
        marker=dict(size=5),
        hovertemplate="%{x|%d %b %Y}<br>%{y} activities<extra></extra>",
    )
    apply_theme(
        fig,
        yaxis=dict(title="km"),
        yaxis2=dict(title="count", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.08, x=0),
        margin=dict(l=52, r=48, t=28, b=40),
    )
    return fig


def pace_by_year_chart(runs: pd.DataFrame) -> go.Figure:
    """Box plot of running pace per year — shows the distribution shifting."""
    runs = runs.dropna(subset=["pace_min_km"])
    if runs.empty:
        return empty_figure()
    runs = runs.assign(year=runs["start_time"].dt.year.astype(str))
    years = sorted(runs["year"].unique())
    fig = go.Figure()
    for yr in years:
        sub = runs[runs["year"] == yr]
        fig.add_box(
            y=sub["pace_min_km"], name=yr, boxpoints="outliers",
            marker_color=COLORS["accent"], line_color=COLORS["accent_soft"],
            fillcolor="rgba(255,107,53,0.12)",
            hovertemplate="%{x}<br>%{y:.2f} min/km<extra></extra>",
        )
    apply_theme(
        fig, showlegend=False,
        yaxis=dict(title="pace (min/km)", autorange="reversed"),
        xaxis=dict(title=""), margin=dict(l=56, r=16, t=20, b=36),
    )
    return fig


def hr_zone_chart(zones: pd.DataFrame) -> go.Figure:
    """Horizontal bar of total minutes per heart-rate zone."""
    if zones.empty or zones["minutes"].sum() == 0:
        return empty_figure("No heart-rate data in range")
    palette = [COLORS["grid"], COLORS["secondary"], COLORS["good"],
               COLORS["warn"], COLORS["accent"], "#e03131"]
    fig = go.Figure(
        go.Bar(
            x=zones["minutes"], y=zones["zone"], orientation="h",
            marker_color=palette, text=zones["minutes"].round().astype(int),
            texttemplate="%{text} min", textposition="auto",
            hovertemplate="%{y}<br>%{x:.0f} min<extra></extra>",
        )
    )
    apply_theme(fig, xaxis=dict(title="minutes"),
                yaxis=dict(autorange="reversed", automargin=True),
                margin=dict(l=120, r=16, t=20, b=40))
    return fig


def activity_donut(breakdown: pd.DataFrame) -> go.Figure:
    """Donut of activity counts by sport type."""
    if breakdown.empty:
        return empty_figure()
    fig = go.Figure(
        go.Pie(
            labels=breakdown["activity_type"].str.capitalize(),
            values=breakdown["count"], hole=0.62, sort=False,
            marker=dict(colors=[SPORT_COLORS.get(s, "#888") for s in breakdown["activity_type"]],
                        line=dict(color=COLORS["bg"], width=2)),
            textinfo="percent", textposition="inside",
            hovertemplate="%{label}<br>%{value} activities (%{percent})<extra></extra>",
        )
    )
    apply_theme(
        fig, showlegend=True,
        legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center",
                    font=dict(color=COLORS["text_muted"])),
        uniformtext=dict(minsize=11, mode="hide"),
        margin=dict(l=8, r=8, t=16, b=8),
        annotations=[dict(text=f"<b>{int(breakdown['count'].sum())}</b><br>total",
                          showarrow=False, font=dict(size=16, color=COLORS["text"]))],
    )
    return fig


def pace_vs_distance_scatter(runs: pd.DataFrame, selected_id: float | None = None) -> go.Figure:
    """Explorer scatter: how pace relates to run distance, coloured by heart rate.

    This separates run *types* (short fast intervals, steady mid-runs, long slow
    runs) and shows the natural trade-off between distance and pace. Selectable:
    the chosen run is ringed so plot and table selections stay linked.
    """
    runs = runs.dropna(subset=["pace_min_km", "distance_km"])
    if runs.empty:
        return empty_figure()
    fig = go.Figure()
    fig.add_scatter(
        x=runs["distance_km"], y=runs["pace_min_km"], mode="markers",
        marker=dict(
            size=8, color=runs["avg_hr"], colorscale="Turbo",
            showscale=True, colorbar=dict(title="avg<br>HR", thickness=10),
            line=dict(width=0.5, color=COLORS["bg"]), opacity=0.82,
        ),
        customdata=np.stack([runs["activity_id"], runs["name"], runs["avg_hr"]], axis=-1),
        hovertemplate="%{customdata[1]}<br>%{x:.1f} km · %{y:.2f} min/km<br>"
                      "%{customdata[2]:.0f} bpm<extra></extra>",
        name="runs",
    )
    if selected_id is not None:
        sel = runs[runs["activity_id"] == float(selected_id)]
        if not sel.empty:
            fig.add_scatter(
                x=sel["distance_km"], y=sel["pace_min_km"], mode="markers",
                marker=dict(size=20, color="rgba(0,0,0,0)",
                            line=dict(width=3, color=COLORS["text"])),
                hoverinfo="skip", showlegend=False, name="selected",
            )
    apply_theme(
        fig,
        xaxis=dict(title="distance (km)"),
        yaxis=dict(title="pace (min/km)", autorange="reversed"),
        margin=dict(l=56, r=16, t=20, b=44),
    )
    return fig


def hr_vs_pace_chart(runs: pd.DataFrame) -> go.Figure:
    """Aerobic efficiency: heart rate vs pace, coloured by year.

    The classic fitness read — for a given pace, a lower heart rate means a
    fitter runner. Colouring by year shows the cloud drifting down/right over
    time as fitness improves. Implausible HR readings are filtered out.
    """
    runs = runs.dropna(subset=["pace_min_km", "avg_hr"])
    runs = runs[(runs["avg_hr"].between(90, 210))]
    if runs.empty:
        return empty_figure("No heart-rate data in range")
    years = runs["start_time"].dt.year
    fig = go.Figure(
        go.Scatter(
            x=runs["pace_min_km"], y=runs["avg_hr"], mode="markers",
            marker=dict(size=7, color=years, colorscale="Turbo", opacity=0.8,
                        colorbar=dict(title="year", thickness=10),
                        line=dict(width=0.4, color=COLORS["bg"])),
            customdata=runs["name"],
            hovertemplate="%{customdata}<br>%{x:.2f} min/km · %{y:.0f} bpm<extra></extra>",
        )
    )
    apply_theme(
        fig, xaxis=dict(title="pace (min/km)", autorange="reversed"),
        yaxis=dict(title="avg heart rate (bpm)"),
        margin=dict(l=56, r=16, t=20, b=40),
    )
    return fig


def cumulative_distance_chart(df: pd.DataFrame) -> go.Figure:
    """Cumulative distance over time, stacked by sport.

    Each sport is resampled onto a shared daily index and cumulatively summed so
    the stacked areas are strictly monotonic — avoiding the interpolation spikes
    that occur when stacking traces with mismatched, irregular timestamps.
    """
    if df.empty:
        return empty_figure()
    daily = (
        df.assign(day=df["start_time"].dt.normalize())
        .pivot_table(index="day", columns="activity_type", values="distance_km",
                     aggfunc="sum", fill_value=0.0)
    )
    full_idx = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
    daily = daily.reindex(full_idx, fill_value=0.0).cumsum()

    fig = go.Figure()
    for sport in ["running", "cycling", "walking"]:
        if sport not in daily.columns:
            continue
        fig.add_scatter(
            x=daily.index, y=daily[sport], mode="lines",
            name=sport.capitalize(), stackgroup="one",
            line=dict(width=0.5, color=SPORT_COLORS.get(sport)),
            fillcolor=SPORT_COLORS.get(sport),
            hovertemplate=sport + " · %{x|%b %Y}<br>%{y:,.0f} km cumulative<extra></extra>",
        )
    apply_theme(
        fig, yaxis=dict(title="cumulative km"),
        legend=dict(orientation="h", y=1.1, x=0),
        margin=dict(l=60, r=16, t=24, b=40),
    )
    return fig


def vo2max_chart(series: pd.DataFrame) -> go.Figure:
    """VO2max estimate over time (area + line)."""
    if series.empty:
        return empty_figure("No VO2max estimates in range")
    fig = go.Figure(
        go.Scatter(
            x=series["start_time"], y=series["vo2max"], mode="lines",
            line=dict(color=COLORS["accent"], width=2.5),
            fill="tozeroy", fillcolor="rgba(255,107,53,0.12)",
            hovertemplate="%{x|%d %b %Y}<br>VO₂max %{y:.0f}<extra></extra>",
        )
    )
    lo = max(0, series["vo2max"].min() - 3)
    apply_theme(fig, yaxis=dict(title="VO₂max (ml/kg/min)", range=[lo, series["vo2max"].max() + 2]),
                margin=dict(l=56, r=16, t=20, b=40))
    return fig


def cadence_pace_chart(runs: pd.DataFrame) -> go.Figure:
    """Running cadence vs pace, coloured by heart rate (form analysis)."""
    runs = runs.dropna(subset=["cadence_spm", "pace_min_km"])
    if runs.empty:
        return empty_figure("No cadence data in range")
    fig = go.Figure(
        go.Scatter(
            x=runs["pace_min_km"], y=runs["cadence_spm"], mode="markers",
            marker=dict(size=7, color=runs["avg_hr"], colorscale="Turbo",
                        showscale=True, colorbar=dict(title="bpm", thickness=10), opacity=0.8),
            customdata=runs["name"],
            hovertemplate="%{customdata}<br>%{x:.2f} min/km · %{y:.0f} spm<extra></extra>",
        )
    )
    apply_theme(fig, xaxis=dict(title="pace (min/km)", autorange="reversed"),
                yaxis=dict(title="cadence (steps/min)"), margin=dict(l=56, r=16, t=20, b=44))
    return fig


def monthly_heatmap(df: pd.DataFrame) -> go.Figure:
    """Calendar heatmap of distance by year (rows) and month (columns)."""
    if df.empty:
        return empty_figure()
    tmp = df.copy()
    tmp["yr"] = tmp["start_time"].dt.year
    tmp["mo"] = tmp["start_time"].dt.month
    pivot = (tmp.groupby(["yr", "mo"])["distance_km"].sum()
             .unstack(fill_value=0).reindex(columns=range(1, 13), fill_value=0))
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    fig = go.Figure(
        go.Heatmap(
            z=pivot.values, x=months, y=pivot.index.astype(str),
            colorscale=SEQUENTIAL, xgap=3, ygap=3,
            colorbar=dict(title="km", thickness=10),
            hovertemplate="%{y} %{x}<br>%{z:.0f} km<extra></extra>",
        )
    )
    apply_theme(fig, yaxis=dict(title="", autorange="reversed"),
                margin=dict(l=44, r=16, t=20, b=40))
    return fig
