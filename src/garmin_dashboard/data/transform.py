"""Pure, stateless transforms used by callbacks to shape data for views.

Keeping these as free functions (no Dash imports) makes them trivially unit
testable and keeps the callback layer thin: callbacks read inputs, call a
transform, hand the result to a component factory.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import HR_ZONE_COLS, HR_ZONE_LABELS


# --- formatting ------------------------------------------------------------
def format_pace(pace_min_km: float | None) -> str:
    """Convert a decimal pace (min/km) into ``m:ss /km`` display form."""
    if pace_min_km is None or pd.isna(pace_min_km) or pace_min_km <= 0:
        return "–"
    minutes = int(pace_min_km)
    seconds = round((pace_min_km - minutes) * 60)
    if seconds == 60:
        minutes, seconds = minutes + 1, 0
    return f"{minutes}:{seconds:02d}"


def format_duration(minutes: float | None) -> str:
    """Human-readable ``h m`` / ``m s`` duration from a minute count."""
    if minutes is None or pd.isna(minutes):
        return "–"
    total_s = int(round(minutes * 60))
    h, rem = divmod(total_s, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m"
    return f"{m}m {s:02d}s"


# --- filtering -------------------------------------------------------------
def filter_activities(
    df: pd.DataFrame,
    sports: list[str] | None = None,
    date_range: tuple[str, str] | None = None,
    distance_range: tuple[float, float] | None = None,
) -> pd.DataFrame:
    """Apply the global control-panel filters and return a new frame."""
    mask = pd.Series(True, index=df.index)
    if sports:
        mask &= df["activity_type"].isin(sports)
    if date_range and date_range[0] and date_range[1]:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        mask &= df["date"].between(start, end)
    if distance_range:
        lo, hi = distance_range
        mask &= df["distance_km"].between(lo, hi)
    return df.loc[mask].copy()


# --- aggregations ----------------------------------------------------------
def kpi_summary(df: pd.DataFrame) -> dict[str, str]:
    """Headline numbers for the KPI cards."""
    if df.empty:
        return {k: "–" for k in ("activities", "distance", "time", "pace", "elevation", "vo2max")}
    runs = df[df["activity_type"] == "running"]
    return {
        "activities": f"{len(df):,}",
        "distance": f"{df['distance_km'].sum():,.0f} km",
        "time": format_duration(df["duration_min"].sum()),
        "pace": f"{format_pace(runs['pace_min_km'].median())} /km" if not runs.empty else "–",
        "elevation": f"{df['elevation_gain_m'].sum():,.0f} m",
        "vo2max": f"{df['vo2max'].dropna().iloc[-1]:.0f}" if df["vo2max"].notna().any() else "–",
    }


def volume_over_time(df: pd.DataFrame, freq: str = "W") -> pd.DataFrame:
    """Aggregate distance, count and moving time per week (``W``) or month (``M``)."""
    if df.empty:
        return pd.DataFrame(columns=["period", "distance_km", "count", "duration_min"])
    key = df["start_time"].dt.to_period(freq).dt.start_time
    grouped = (
        df.groupby(key)
        .agg(distance_km=("distance_km", "sum"),
             count=("activity_id", "size"),
             duration_min=("duration_min", "sum"))
        .reset_index(names="period")
    )
    return grouped


def pace_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Running activities with a valid pace, sorted in time (for trend lines)."""
    runs = df[(df["activity_type"] == "running") & df["pace_min_km"].notna()]
    return runs.sort_values("start_time")


def hr_zone_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Total minutes spent in each HR zone across the filtered set."""
    totals = df[HR_ZONE_COLS].sum()
    return pd.DataFrame({
        "zone": [HR_ZONE_LABELS[i] for i in range(6)],
        "minutes": [totals[c] for c in HR_ZONE_COLS],
    })


def activity_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Count + distance per sport type for the donut chart."""
    if df.empty:
        return pd.DataFrame(columns=["activity_type", "count", "distance_km"])
    return (
        df.groupby("activity_type")
        .agg(count=("activity_id", "size"), distance_km=("distance_km", "sum"))
        .reset_index()
        .sort_values("count", ascending=False)
    )


def vo2max_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Time series of VO2max estimates (running only, deduped to changes)."""
    s = df[df["vo2max"].notna()].sort_values("start_time")[["start_time", "vo2max"]]
    return s


def personal_records(df: pd.DataFrame) -> dict[str, object]:
    """Best efforts within the filtered set (longest, fastest, biggest climb)."""
    runs = df[df["activity_type"] == "running"]
    if runs.empty:
        return {}
    longest = runs.loc[runs["distance_km"].idxmax()]
    fastest = runs.loc[runs[runs["distance_km"] >= 3]["pace_min_km"].idxmin()] \
        if (runs["distance_km"] >= 3).any() else runs.loc[runs["pace_min_km"].idxmin()]
    climb = df.loc[df["elevation_gain_m"].idxmax()]
    return {"longest": longest, "fastest": fastest, "climb": climb}


def get_activity(df: pd.DataFrame, activity_id: int | float | str) -> pd.Series | None:
    """Fetch a single activity row by id for the detail panel."""
    if activity_id is None:
        return None
    match = df[df["activity_id"] == float(activity_id)]
    return match.iloc[0] if not match.empty else None
