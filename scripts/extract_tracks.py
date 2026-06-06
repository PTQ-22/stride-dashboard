"""ETL pipeline: FIT files -> per-activity GPS tracks.

The Garmin export stores full GPS recordings as ``.fit`` files inside the
``UploadedFiles_*.zip`` archives. Their filenames use an *upload* id that does
**not** match the activity id in ``summarizedActivities.json``, so we join the
two by start timestamp instead: every FIT ``session`` message carries a UTC
``start_time`` that lines up with an activity's ``beginTimestamp``.

For each matched FIT we extract the latitude/longitude stream, downsample it to
keep the output small, and write a tidy ``tracks.csv`` (one row per track
point) that the dashboard renders as route polylines / coverage.

Usage::

    python scripts/extract_tracks.py \
        --summary  /path/to/..._summarizedActivities.json \
        --zips     /path/to/UploadedFiles_0-_Part1.zip /path/to/..._Part2.zip \
        --out      data/processed/tracks.csv
"""

from __future__ import annotations

import argparse
import bisect
import io
import json
import logging
import zipfile
from datetime import timezone
from pathlib import Path

import fitparse
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("extract_tracks")

SEMICIRCLE_TO_DEG = 180.0 / 2**31
MATCH_TOLERANCE_S = 180        # max gap between FIT start and activity start
MAX_POINTS_PER_TRACK = 450     # downsample target (dense enough for smooth 3-D routes)
COORD_PRECISION = 5            # ~1.1 m, keeps the CSV compact


def _activity_index(summary_path: Path) -> tuple[list[int], dict[int, int]]:
    """Return (sorted GMT-epoch list, epoch->activity_id) for matching."""
    raw = json.loads(summary_path.read_text())
    acts = raw[0]["summarizedActivitiesExport"] if isinstance(raw, list) else raw
    epoch_to_id: dict[int, int] = {}
    for a in acts:
        ts = a.get("beginTimestamp")
        if ts:
            epoch_to_id[int(ts // 1000)] = a["activityId"]
    return sorted(epoch_to_id), epoch_to_id


def _nearest_activity(epoch: int, epochs: list[int], lookup: dict[int, int]) -> int | None:
    """Find the activity whose start is within tolerance of ``epoch``."""
    if not epochs:
        return None
    i = bisect.bisect_left(epochs, epoch)
    best, best_gap = None, MATCH_TOLERANCE_S + 1
    for j in (i - 1, i):
        if 0 <= j < len(epochs):
            gap = abs(epochs[j] - epoch)
            if gap < best_gap:
                best, best_gap = epochs[j], gap
    return lookup[best] if best is not None else None


def _parse_fit(data: bytes) -> tuple[int | None, list[tuple]]:
    """Single pass over a FIT file: return (start_epoch_utc, track points).

    Each point is ``(lat, lng, altitude_m, heart_rate_bpm, pace_min_km)``; any
    field is NaN when the device did not record it.
    """
    fit = fitparse.FitFile(io.BytesIO(data))
    start_epoch: int | None = None
    track: list[tuple] = []
    for msg in fit.get_messages(("session", "record")):
        if msg.name == "session" and start_epoch is None:
            t = msg.get_value("start_time")
            if t is not None:
                start_epoch = int(t.replace(tzinfo=timezone.utc).timestamp())
        elif msg.name == "record":
            la, lo = msg.get_value("position_lat"), msg.get_value("position_long")
            if la is not None and lo is not None:
                alt = msg.get_value("enhanced_altitude")
                if alt is None:
                    alt = msg.get_value("altitude")
                hr = msg.get_value("heart_rate")
                spd = msg.get_value("enhanced_speed")
                if spd is None:
                    spd = msg.get_value("speed")
                # convert m/s -> pace min/km (NaN when stationary/missing)
                pace = (1000.0 / spd) / 60.0 if spd and spd > 0.3 else float("nan")
                track.append((
                    la * SEMICIRCLE_TO_DEG, lo * SEMICIRCLE_TO_DEG,
                    float(alt) if alt is not None else float("nan"),
                    float(hr) if hr is not None else float("nan"),
                    pace,
                ))
    return start_epoch, track


def _downsample(track: list[tuple]) -> list[tuple]:
    if len(track) <= MAX_POINTS_PER_TRACK:
        return track
    stride = len(track) // MAX_POINTS_PER_TRACK + 1
    sampled = track[::stride]
    if sampled[-1] != track[-1]:
        sampled.append(track[-1])  # always keep the finish point
    return sampled


def extract(summary: Path, zips: list[Path]) -> pd.DataFrame:
    epochs, lookup = _activity_index(summary)
    logger.info("Indexed %d activities for timestamp matching", len(lookup))

    rows: list[tuple] = []
    matched, scanned = 0, 0
    for zip_path in zips:
        with zipfile.ZipFile(zip_path) as zf:
            members = [m for m in zf.namelist() if m.lower().endswith(".fit")]
            logger.info("Scanning %s (%d FIT files)", zip_path.name, len(members))
            for name in members:
                scanned += 1
                try:
                    start_epoch, track = _parse_fit(zf.read(name))
                except Exception:  # corrupt / unsupported FIT — skip
                    continue
                if start_epoch is None or not track:
                    continue
                activity_id = _nearest_activity(start_epoch, epochs, lookup)
                if activity_id is None:
                    continue
                matched += 1
                for seq, (lat, lng, alt, hr, pace) in enumerate(_downsample(track)):
                    rows.append((
                        activity_id, seq,
                        round(lat, COORD_PRECISION), round(lng, COORD_PRECISION),
                        round(alt, 1) if alt == alt else "",      # NaN -> blank
                        round(hr) if hr == hr else "",
                        round(pace, 3) if pace == pace else "",
                    ))
                if scanned % 1000 == 0:
                    logger.info("…scanned %d, matched %d", scanned, matched)

    logger.info("Matched %d activities to GPS tracks (%d points)", matched, len(rows))
    return pd.DataFrame(rows, columns=["activity_id", "seq", "lat", "lng", "alt", "hr", "pace"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--zips", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, default=Path("data/processed/tracks.csv"))
    args = parser.parse_args()

    df = extract(args.summary, args.zips)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    logger.info("Wrote %s (%d rows)", args.out, len(df))


if __name__ == "__main__":
    main()
