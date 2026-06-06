"""Central configuration: paths, constants and tunables.

Everything that another module might want to tweak lives here so there are no
magic strings scattered across the codebase. Values can be overridden with
environment variables to keep deployments twelve-factor friendly.
"""

from __future__ import annotations

import os
from pathlib import Path

# --- paths -----------------------------------------------------------------
PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]

DATA_PATH = Path(
    os.environ.get("STRIDE_DATA_PATH", PROJECT_ROOT / "data" / "processed" / "activities.csv")
)
TRACKS_PATH = Path(
    os.environ.get("STRIDE_TRACKS_PATH", PROJECT_ROOT / "data" / "processed" / "tracks.csv")
)
BASEMAPS_PATH = Path(
    os.environ.get("STRIDE_BASEMAPS_PATH", PROJECT_ROOT / "data" / "processed" / "basemaps.npz")
)

# --- app metadata ----------------------------------------------------------
APP_TITLE = "Stride · Running Analytics"
APP_TAGLINE = "Six years on foot, one dashboard."

# --- domain constants ------------------------------------------------------
# Heart-rate zone labels (Garmin zones 0-5; zone 0 is rest/warm-up).
HR_ZONE_LABELS = {
    0: "Z0 · Rest",
    1: "Z1 · Warm-up",
    2: "Z2 · Easy",
    3: "Z3 · Aerobic",
    4: "Z4 · Threshold",
    5: "Z5 · Maximal",
}
HR_ZONE_COLS = [f"hr_zone_{i}_min" for i in range(6)]

# Sport types we surface in the activity-type control.
SPORT_TYPES = ["running", "cycling", "walking", "mountaineering"]

# Default range for the distance slider (km).
DISTANCE_MIN_KM = 0
DISTANCE_MAX_KM = 50

# Server defaults (overridable via env for hosting platforms).
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8050"))
DEBUG = os.environ.get("STRIDE_DEBUG", "false").lower() == "true"
