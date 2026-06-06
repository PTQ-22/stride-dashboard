"""ETL pipeline: Garmin Connect export -> tidy activities table.

Reads the ``*_summarizedActivities.json`` file produced by a Garmin account
data export, normalises the Garmin storage units (centimetres, milliseconds,
deci-metres/second ...) into human units (km, minutes, min/km), derives a set
of training-analysis features and writes a single tidy CSV that the dashboard
consumes at runtime.

Run from the project root::

    python scripts/prepare_data.py \
        --source /path/to/..._summarizedActivities.json \
        --out data/processed/activities.csv

The script is deliberately dependency-light (only pandas) and idempotent: it
can be re-run whenever a fresh Garmin export is downloaded.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("prepare_data")

# --- Garmin unit constants -------------------------------------------------
# Garmin stores most quantities as scaled integers; these factors normalise
# them to conventional units.
CM_PER_KM = 100_000.0          # distance stored in centimetres
CM_PER_M = 100.0               # elevation / stride stored in centimetres
MS_PER_S = 1_000.0             # durations stored in milliseconds
MS_PER_MIN = 60_000.0          # HR time-in-zone stored in milliseconds

# Columns copied straight through (after rename) when present.
PASSTHROUGH = {
    "activityId": "activity_id",
    "name": "name",
    "activityType": "activity_type",
    "locationName": "location",
    "avgHr": "avg_hr",
    "maxHr": "max_hr",
    "calories": "calories",
    "steps": "steps",
    "vO2MaxValue": "vo2max",
    "aerobicTrainingEffect": "aerobic_te",
    "anaerobicTrainingEffect": "anaerobic_te",
    "startLatitude": "start_lat",
    "startLongitude": "start_lng",
    "deviceId": "device_id",
}

HR_ZONE_COLS = [f"hrTimeInZone_{i}" for i in range(6)]


def _extract_activity_records(raw: object) -> list[dict]:
    """Return the flat list of activity dicts from the export envelope.

    Garmin wraps the activities in ``[{"summarizedActivitiesExport": [...]}]``
    but older / partial exports sometimes provide the bare list, so we handle
    both shapes defensively.
    """
    if isinstance(raw, list) and raw and isinstance(raw[0], dict) and "summarizedActivitiesExport" in raw[0]:
        return raw[0]["summarizedActivitiesExport"]
    if isinstance(raw, list):
        return raw
    raise ValueError("Unrecognised Garmin export structure")


def transform(records: list[dict]) -> pd.DataFrame:
    """Convert raw Garmin activity dicts into a tidy, unit-normalised frame."""
    df = pd.DataFrame.from_records(records)
    logger.info("Loaded %d raw activities", len(df))

    out = pd.DataFrame(index=df.index)
    for src, dst in PASSTHROUGH.items():
        out[dst] = df[src] if src in df.columns else np.nan

    # --- timestamps (ms epoch, local time) ---
    out["start_time"] = pd.to_datetime(df["startTimeLocal"], unit="ms", errors="coerce")
    out["date"] = out["start_time"].dt.normalize()
    out["year"] = out["start_time"].dt.year
    out["month"] = out["start_time"].dt.to_period("M").astype(str)
    out["week"] = out["start_time"].dt.to_period("W").apply(lambda p: p.start_time if pd.notna(p) else pd.NaT)
    out["weekday"] = out["start_time"].dt.day_name()
    out["hour"] = out["start_time"].dt.hour

    # --- distance / duration ---
    out["distance_km"] = df["distance"] / CM_PER_KM
    out["duration_min"] = df["duration"] / MS_PER_S / 60.0
    out["moving_min"] = df.get("movingDuration", df["duration"]) / MS_PER_S / 60.0
    out["elevation_gain_m"] = df.get("elevationGain", np.nan) / CM_PER_M

    # --- pace & speed (guard against zero distance) ---
    valid = out["distance_km"] > 0.05
    out["pace_min_km"] = np.where(valid, out["duration_min"] / out["distance_km"], np.nan)
    out["speed_kmh"] = np.where(valid, out["distance_km"] / (out["duration_min"] / 60.0), np.nan)

    # --- running dynamics ---
    out["cadence_spm"] = df.get("avgRunCadence", np.nan) * 2.0  # single-foot -> steps/min
    out["stride_m"] = df.get("avgStrideLength", np.nan) / CM_PER_M
    out["vertical_osc_cm"] = df.get("avgVerticalOscillation", np.nan) / 10.0  # stored in mm

    # --- heart-rate time in zone (ms -> minutes) ---
    for i in range(6):
        col = f"hrTimeInZone_{i}"
        out[f"hr_zone_{i}_min"] = df[col] / MS_PER_MIN if col in df.columns else 0.0
    zone_cols = [f"hr_zone_{i}_min" for i in range(6)]
    out[zone_cols] = out[zone_cols].fillna(0.0)

    # --- tidy up ---
    out["name"] = out["name"].fillna("Untitled activity")
    out["location"] = out["location"].fillna("Unknown")
    out["activity_type"] = out["activity_type"].fillna("other")

    # Keep only the sports that form a coherent training story. The export also
    # contains a single 42 km "mountaineering" outing whose distance/profile
    # skews every distance-based control, so it is excluded here.
    keep = {"running", "cycling", "walking"}
    out = out[out["activity_type"].isin(keep)]
    out = out.dropna(subset=["start_time", "distance_km"])
    out = out[out["distance_km"] > 0]  # drop strength-training rows w/o distance is handled below

    # keep all sport types (strength has 0 distance) but flag distance sports
    out["has_distance"] = out["distance_km"] > 0.05

    out = out.sort_values("start_time").reset_index(drop=True)
    logger.info(
        "Transformed %d activities | %s -> %s",
        len(out),
        out["date"].min().date(),
        out["date"].max().date(),
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Path to *_summarizedActivities.json from the Garmin export",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/processed/activities.csv"),
        help="Output CSV path",
    )
    args = parser.parse_args()

    raw = json.loads(args.source.read_text())
    records = _extract_activity_records(raw)
    df = transform(records)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    logger.info("Wrote %s (%d rows, %d cols)", args.out, len(df), df.shape[1])


if __name__ == "__main__":
    main()
