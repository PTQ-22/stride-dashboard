"""Unit tests for the pure transform layer (no Dash, no real data needed)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from garmin_dashboard.data import transform as T


@pytest.fixture
def sample() -> pd.DataFrame:
    """A tiny, hand-built activities frame mirroring the processed schema."""
    times = pd.to_datetime(["2024-01-01 08:00", "2024-01-08 18:30", "2024-02-01 07:15"])
    df = pd.DataFrame({
        "activity_id": [1.0, 2.0, 3.0],
        "name": ["Easy", "Intervals", "Long run"],
        "activity_type": ["running", "running", "cycling"],
        "start_time": times,
        "date": times.normalize(),
        "distance_km": [5.0, 8.0, 30.0],
        "duration_min": [30.0, 40.0, 60.0],
        "pace_min_km": [6.0, 5.0, np.nan],
        "avg_hr": [150.0, 165.0, 140.0],
        "max_hr": [160.0, 178.0, 150.0],
        "cadence_spm": [160.0, 172.0, np.nan],
        "elevation_gain_m": [20.0, 35.0, 120.0],
        "calories": [300.0, 420.0, 800.0],
        "vo2max": [52.0, 53.0, np.nan],
        "start_lat": [52.4, 52.4, 52.5],
        "start_lng": [16.9, 16.9, 17.0],
        "location": ["Poznan", "Poznan", "Swarzedz"],
        **{f"hr_zone_{i}_min": [i, i + 1, 0] for i in range(6)},
    })
    return df


def test_format_pace():
    assert T.format_pace(5.0) == "5:00"
    assert T.format_pace(5.835) == "5:50"
    assert T.format_pace(None) == "–"
    assert T.format_pace(4.999) == "5:00"  # rounds 59.94s -> carry


def test_format_duration():
    assert T.format_duration(30) == "30m 00s"
    assert T.format_duration(312.5) == "5h 12m"
    assert T.format_duration(None) == "–"


def test_filter_by_sport(sample):
    runs = T.filter_activities(sample, sports=["running"])
    assert len(runs) == 2
    assert set(runs["activity_type"]) == {"running"}


def test_filter_by_distance(sample):
    short = T.filter_activities(sample, distance_range=(0, 10))
    assert len(short) == 2
    assert short["distance_km"].max() <= 10


def test_filter_by_date(sample):
    jan = T.filter_activities(sample, date_range=("2024-01-01", "2024-01-31"))
    assert len(jan) == 2


def test_kpi_summary(sample):
    kpi = T.kpi_summary(sample)
    assert kpi["activities"] == "3"
    assert kpi["distance"] == "43 km"
    assert kpi["pace"] == "5:30 /km"  # median of running paces (5.0, 6.0)


def test_volume_over_time(sample):
    weekly = T.volume_over_time(sample, "W")
    assert weekly["distance_km"].sum() == pytest.approx(43.0)
    assert "period" in weekly.columns


def test_get_activity(sample):
    row = T.get_activity(sample, 2.0)
    assert row is not None and row["name"] == "Intervals"
    assert T.get_activity(sample, 999) is None


def test_empty_frame_is_safe():
    empty = pd.DataFrame(columns=["activity_type", "distance_km"])
    assert T.kpi_summary(empty)["distance"] == "–"
