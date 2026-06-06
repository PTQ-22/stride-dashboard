"""Shared callback helpers: turn control-widget values into a filtered frame."""

from __future__ import annotations

import pandas as pd
from dash import Input

from ..components.controls import DATE_RANGE, DISTANCE_SLIDER, GRANULARITY, SPORT_CHECKLIST
from ..data import get_activities, get_meta
from ..data.transform import filter_activities

# The canonical ordered list of filter Inputs reused by every data callback.
# Order matters: callbacks unpack (sports, date_idx, distance).
FILTER_INPUTS = [
    Input(SPORT_CHECKLIST, "value"),
    Input(DATE_RANGE, "value"),
    Input(DISTANCE_SLIDER, "value"),
]
GRANULARITY_INPUT = Input(GRANULARITY, "value")


def filtered_frame(sports, date_idx, distance) -> pd.DataFrame:
    """Apply the global filters to the cached activities frame.

    ``date_idx`` is the ``[start, end]`` month-index pair from the date slider;
    it is converted to real dates via the dataset's month axis.
    """
    meta = get_meta()
    start, end = meta.month_bounds(tuple(date_idx)) if date_idx else (None, None)
    dist = tuple(distance) if distance else None
    return filter_activities(get_activities(), sports, (start, end), dist)
