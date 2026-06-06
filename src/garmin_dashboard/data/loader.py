"""Load the processed activities table once and cache it in memory.

The dashboard is read-only over a small (~700 row) dataset, so we load the CSV
a single time at import and hand out cheap copies. ``functools.lru_cache``
gives us lazy, thread-safe, process-local memoisation without a heavyweight
cache backend.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from ..config import DATA_PATH, TRACKS_PATH

logger = logging.getLogger(__name__)

# Columns that must be parsed as datetimes when reading the CSV.
_DATE_COLS = ["start_time", "date", "week"]


@dataclass(frozen=True)
class DatasetMeta:
    """Lightweight summary used to seed control widgets and the About page."""

    n_activities: int
    min_date: pd.Timestamp
    max_date: pd.Timestamp
    sport_types: list[str]
    max_distance_km: float
    months: tuple[pd.Timestamp, ...]  # month-start axis for the date range slider

    def month_bounds(self, idx_range: tuple[int, int]) -> tuple[pd.Timestamp, pd.Timestamp]:
        """Map a [start_idx, end_idx] slider range to actual start/end dates."""
        lo = self.months[max(0, min(idx_range[0], len(self.months) - 1))]
        hi_month = self.months[max(0, min(idx_range[1], len(self.months) - 1))]
        hi = hi_month + pd.offsets.MonthEnd(1)  # include the whole end month
        return lo, hi


@lru_cache(maxsize=1)
def get_activities() -> pd.DataFrame:
    """Return the full activities frame (cached). Callers must not mutate it."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Processed data not found at {DATA_PATH}. "
            "Run `python scripts/prepare_data.py` first."
        )
    df = pd.read_csv(DATA_PATH, parse_dates=_DATE_COLS)
    logger.info("Loaded %d activities from %s", len(df), DATA_PATH)
    return df


@lru_cache(maxsize=1)
def get_tracks() -> pd.DataFrame:
    """Return GPS track points (activity_id, seq, lat, lng), or empty if absent.

    Tracks are optional: the dashboard degrades to start-point markers when the
    file has not been generated (``scripts/extract_tracks.py``).
    """
    if not TRACKS_PATH.exists():
        logger.warning("Track file not found at %s — map falls back to start points", TRACKS_PATH)
        return pd.DataFrame(columns=["activity_id", "seq", "lat", "lng"])
    df = pd.read_csv(TRACKS_PATH)
    logger.info("Loaded %d track points for %d activities",
                len(df), df["activity_id"].nunique())
    return df


@lru_cache(maxsize=1)
def get_meta() -> DatasetMeta:
    """Derive dataset-level metadata for bootstrapping the UI."""
    df = get_activities()
    months = pd.date_range(
        df["date"].min().to_period("M").start_time,
        df["date"].max().to_period("M").start_time,
        freq="MS",
    )
    return DatasetMeta(
        n_activities=len(df),
        min_date=df["date"].min(),
        max_date=df["date"].max(),
        sport_types=sorted(df["activity_type"].dropna().unique().tolist()),
        max_distance_km=float(df["distance_km"].max()),
        months=tuple(months),
    )
