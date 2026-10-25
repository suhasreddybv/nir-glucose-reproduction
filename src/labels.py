"""PersHigh / PersLow / PersNorm labels and the class-balanced set (protocol cells 1, 7 c, 7 d).

A reading is PersHigh when it exceeds the trailing 24-hour mean of the participant's CGM by
more than one SD, PersLow when it falls more than one SD below it, PersNorm otherwise
(Methods "Developing personalized definitions ..."). The window is time-based, trailing,
includes the current reading, SD with ddof = 1, and needs at least 12 readings (one hour);
earlier readings are unlabelled (cell 7 d). The statistic is of the CGM stream alone - it is
a label, never a feature - and is computed on every reading, usable epoch or not.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

LABELS = ("PersLow", "PersNorm", "PersHigh")
MIN_READINGS = 12
WINDOW = "24h"


def pers_labels(ts: np.ndarray, glucose: np.ndarray) -> pd.DataFrame:
    """Per reading: the trailing 24-h mean and SD, and the label (None where unlabelled)."""
    s = pd.Series(np.asarray(glucose, dtype=float), index=pd.DatetimeIndex(ts))
    r = s.rolling(WINDOW, closed="right", min_periods=MIN_READINGS)
    mean, sd = r.mean(), r.std(ddof=1)
    label = np.where(s > mean + sd, "PersHigh", np.where(s < mean - sd, "PersLow", "PersNorm")).astype(object)
    label[(mean.isna() | sd.isna()).to_numpy()] = None
    return pd.DataFrame({"t": s.index, "glucose": s.to_numpy(), "roll_mean": mean.to_numpy(), "roll_sd": sd.to_numpy(), "label": label})


def balanced_set(df: pd.DataFrame, label_col: str = "label", seed: int = 0) -> pd.DataFrame:
    """Random undersampling of every class to the smallest class's count, seed fixed, done once
    on the full labelled set before any split (cell 7 c). Rows keep their original index."""
    d = df[df[label_col].notna()]
    counts = d[label_col].value_counts()
    k = int(counts.min())
    rng = np.random.default_rng(seed)
    keep = []
    for lab in LABELS:
        idx = d.index[d[label_col] == lab].to_numpy()
        keep.append(np.sort(rng.choice(idx, size=k, replace=False)))
    return d.loc[np.sort(np.concatenate(keep))]
