"""Load pre-fetched grayscale basemaps for the 3-D route floor.

The basemaps are produced offline by ``scripts/fetch_basemaps.py`` and bundled
as a single compressed ``.npz``. Loading is lazy and cached; the app makes no
network calls. The feature degrades gracefully (returns ``None``) when the file
is absent, in which case the 3-D view falls back to a plain reference plane.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import numpy as np

from ..config import BASEMAPS_PATH

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load() -> dict:
    if not BASEMAPS_PATH.exists():
        logger.warning("Basemaps not found at %s — 3-D route uses a plain floor", BASEMAPS_PATH)
        return {}
    # mmap keeps memory low; arrays are tiny (128x128 uint8) and copied on use.
    npz = np.load(BASEMAPS_PATH, mmap_mode="r")
    logger.info("Loaded %d basemaps from %s", sum(1 for k in npz.files if not k.endswith("_e")),
                BASEMAPS_PATH)
    return {k: npz[k] for k in npz.files}


def get_basemap(activity_id: float | int) -> tuple[np.ndarray, np.ndarray] | None:
    """Return ``(grid, extent)`` for an activity, or ``None`` if unavailable.

    ``grid`` is a HxW uint8 luminance image (row 0 = south); ``extent`` is
    ``[lon_min, lon_max, lat_min, lat_max]``.
    """
    store = _load()
    key = str(int(activity_id))
    if key not in store or f"{key}_e" not in store:
        return None
    return np.asarray(store[key]), np.asarray(store[f"{key}_e"])
