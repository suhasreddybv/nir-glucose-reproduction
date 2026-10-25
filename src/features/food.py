"""Food-log features (Supplementary Table 1 rows 42-60), under protocol cell 7 j.

Events are the log's rows at `time_begin`; rows sharing a `time_begin` are one eating event
for the counts and the binary. Nutrient sums use the dataset's own columns as logged; a
missing nutrient contributes 0 and is counted. Windows are [T - W, T): strictly before T.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

NUTRIENTS = {"calories": "calorie", "protein": "protein", "sugar": "sugar", "carbs": "total_carb"}
WINDOWS = {"2hr": pd.Timedelta(hours=2), "8hr": pd.Timedelta(hours=8), "24hr": pd.Timedelta(hours=24)}


def eating_events(food: pd.DataFrame) -> pd.DataFrame:
    """One row per distinct time_begin with the nutrients summed over the rows logged at that
    time; rows without a parseable time are dropped and counted in attrs['dropped_no_time'];
    attrs['rows_missing_nutrient'] counts rows with any of the four nutrients missing."""
    f = food.copy()
    f["time_begin"] = pd.to_datetime(f["time_begin"], errors="coerce")
    no_time = int(f["time_begin"].isna().sum())
    f = f[f["time_begin"].notna()]
    cols = list(NUTRIENTS.values())
    for c in cols:
        f[c] = pd.to_numeric(f[c], errors="coerce")
    missing = int(f[cols].isna().any(axis=1).sum())
    ev = f.groupby("time_begin", sort=True)[cols].sum(min_count=0).reset_index()
    ev.attrs["dropped_no_time"] = no_time
    ev.attrs["rows_missing_nutrient"] = missing
    ev.attrs["rows"] = int(len(f))
    return ev


def food_features(events: pd.DataFrame, targets: pd.DatetimeIndex, epoch: pd.Timedelta = pd.Timedelta(minutes=5)) -> pd.DataFrame:
    """For each target time T: the 12 nutrient sums over [T - W, T), the binary Eat for
    [T - 5 min, T), and the three event counts over [T - W, T). Eatmean* are rolling means of
    Eat over epochs and are added by the matrix builder, where the epoch series lives."""
    t = pd.DatetimeIndex(targets).to_numpy()
    et = events["time_begin"].to_numpy() if len(events) else np.array([], dtype="datetime64[ns]")
    cums = {k: np.r_[0.0, np.cumsum(events[c].to_numpy(dtype=float))] if len(events) else np.array([0.0]) for k, c in NUTRIENTS.items()}
    out = {}
    hi = np.searchsorted(et, t, side="left")              # events strictly before T
    for wname, w in WINDOWS.items():
        lo = np.searchsorted(et, t - w.to_timedelta64(), side="left")   # events at or after T - W
        for k in NUTRIENTS:
            out[f"{k}{wname}"] = cums[k][hi] - cums[k][lo]
        out[f"Eatcnt{wname}"] = (hi - lo).astype(float)
    lo_e = np.searchsorted(et, t - epoch.to_timedelta64(), side="left")
    out["Eat"] = ((hi - lo_e) > 0).astype(float)
    return pd.DataFrame(out, index=pd.DatetimeIndex(targets))
