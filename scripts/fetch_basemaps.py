"""ETL pipeline: pre-fetch a static OSM basemap per activity (run once, offline).

Each activity has a fixed GPS bounding box, so the map underlay shown beneath
the 3-D route never changes — there is no reason to hit a tile server at request
time. This script renders one small grayscale basemap per activity and stores
them all in a single compressed ``basemaps.npz`` that the app loads locally, so
the live dashboard makes **zero** network calls.

Why grayscale: Plotly's 3-D ``Surface`` can only texture a plane via a scalar
``surfacecolor`` grid mapped through a colorscale, so a single luminance channel
is all that can be displayed anyway.

Usage::

    pip install -e ".[etl]"            # staticmap + Pillow
    python scripts/fetch_basemaps.py   # reads data/processed/tracks.csv
"""

from __future__ import annotations

import argparse
import logging
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from staticmap import StaticMap

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("fetch_basemaps")

IMG = 1024         # render size (px) fetched from tiles
GRID = 384         # stored grid resolution (after cropping to the route bbox)
TILE = 256
PAD = 0.08         # bbox padding fraction (small margin around the route)
# Carto "dark matter" tiles — the same elegant dark basemap the Map tab uses
# (no labels: text would be unreadable on a tilted, mirrored 3-D floor).
TILE_URL = "https://a.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}.png"
UA = "stride-dashboard/0.1 (personal running analytics; contact via github)"


def _lon_px(lon: float, z: int) -> float:
    return (lon + 180) / 360 * TILE * 2**z


def _lat_px(lat: float, z: int) -> float:
    s = math.sin(math.radians(lat))
    return (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * TILE * 2**z


def _px_lon(px: float, z: int) -> float:
    return px / (TILE * 2**z) * 360 - 180


def _px_lat(px: float, z: int) -> float:
    return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * px / (TILE * 2**z)))))


def _fit_zoom(lo0, lo1, la0, la1) -> int:
    for z in range(17, 2, -1):
        if (_lon_px(lo1, z) - _lon_px(lo0, z)) <= IMG and (_lat_px(la0, z) - _lat_px(la1, z)) <= IMG:
            return z
    return 3


def _fetch_one(trk: pd.DataFrame) -> tuple[np.ndarray, np.ndarray] | None:
    lo0, lo1 = trk["lng"].min(), trk["lng"].max()
    la0, la1 = trk["lat"].min(), trk["lat"].max()
    dx, dy = (lo1 - lo0) * PAD + 1e-3, (la1 - la0) * PAD + 1e-3
    lo0, lo1, la0, la1 = lo0 - dx, lo1 + dx, la0 - dy, la1 + dy
    clon, clat = (lo0 + lo1) / 2, (la0 + la1) / 2
    z = _fit_zoom(lo0, lo1, la0, la1)

    m = StaticMap(IMG, IMG, url_template=TILE_URL, headers={"User-Agent": UA})
    img = m.render(zoom=z, center=[clon, clat]).convert("L")

    # Crop the rendered frame to exactly the (padded) route bounding box, so the
    # floor hugs the route — no wasted map, and the grid pixels are spent only
    # on the area that matters (sharper for the same stored resolution).
    cx, cy = _lon_px(clon, z), _lat_px(clat, z)
    left, top = cx - IMG / 2, cy - IMG / 2
    c_lo = max(0, int(_lon_px(lo0, z) - left))
    c_hi = min(IMG, int(round(_lon_px(lo1, z) - left)))
    r_top = max(0, int(_lat_px(la1, z) - top))     # la1 = north = smaller pixel row
    r_bot = min(IMG, int(round(_lat_px(la0, z) - top)))
    if c_hi - c_lo < 8 or r_bot - r_top < 8:        # degenerate tiny bbox
        c_lo, c_hi, r_top, r_bot = 0, IMG, 0, IMG
    img = img.crop((c_lo, r_top, c_hi, r_bot))

    # extent = the actual geographic bounds of the crop
    extent = np.array([
        _px_lon(left + c_lo, z), _px_lon(left + c_hi, z),   # lon_min, lon_max
        _px_lat(top + r_bot, z), _px_lat(top + r_top, z),   # lat_min, lat_max
    ], dtype=np.float32)

    # downsample, flip so row 0 == south (ascending latitude)
    grid = np.asarray(img.resize((GRID, GRID), Image.BILINEAR), dtype=np.uint8)
    grid = np.flipud(grid).copy()
    return grid, extent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracks", type=Path, default=Path("data/processed/tracks.csv"))
    parser.add_argument("--out", type=Path, default=Path("data/processed/basemaps.npz"))
    parser.add_argument("--delay", type=float, default=0.25, help="seconds between fetches (be polite)")
    args = parser.parse_args()

    tracks = pd.read_csv(args.tracks)
    store: dict[str, np.ndarray] = {}
    ids = tracks["activity_id"].unique()
    ok = fail = 0
    for n, aid in enumerate(ids, 1):
        trk = tracks[tracks["activity_id"] == aid]
        try:
            result = _fetch_one(trk)
            if result is None:
                fail += 1
                continue
            grid, extent = result
            store[str(int(aid))] = grid
            store[f"{int(aid)}_e"] = extent
            ok += 1
        except Exception as exc:  # network / tile error — skip, app falls back
            fail += 1
            logger.warning("activity %s failed: %s", int(aid), exc)
        if n % 50 == 0:
            logger.info("…%d/%d (ok=%d fail=%d)", n, len(ids), ok, fail)
        time.sleep(args.delay)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.out, **store)
    size_mb = args.out.stat().st_size / 1e6
    logger.info("Wrote %s — %d basemaps, %.1f MB (failed %d)", args.out, ok, size_mb, fail)


if __name__ == "__main__":
    main()
