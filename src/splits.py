"""The split regimes of protocol §9, as boolean masks over a matrix with `participant` and `t`.

R1 regression: `lopo` (one participant out) and `halves` (first contiguous half of each
participant's usable epochs by count trains, the rest tests - cell 7 e).
R3: `time_blocked` - the first 70 % of each participant's epochs train, the last 30 % test,
and no epoch within 24 h of the boundary on either side belongs to either set.
R1/R2 classification folds (window-level repeated stratified k-fold; participant-grouped
k-fold) are built in the classification script on Wednesday with scikit-learn's splitters.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

GAP = pd.Timedelta(hours=24)


def lopo(df: pd.DataFrame):
    for pid in sorted(df["participant"].unique()):
        test = (df["participant"] == pid).to_numpy()
        yield pid, ~test, test


def halves(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """train, test masks: per participant, rows in time order, the first n // 2 train."""
    train = np.zeros(len(df), bool)
    for pid, g in df.groupby("participant"):
        order = g.sort_values("t").index.to_numpy()
        pos = df.index.get_indexer(order)
        train[pos[: len(pos) // 2]] = True
    return train, ~train


def time_blocked(df: pd.DataFrame, train_frac: float = 0.7, gap: pd.Timedelta = GAP) -> tuple[np.ndarray, np.ndarray]:
    """train, test masks with the exclusion zone; rows inside the zone are in neither."""
    train = np.zeros(len(df), bool); test = np.zeros(len(df), bool)
    for pid, g in df.groupby("participant"):
        g = g.sort_values("t")
        pos = df.index.get_indexer(g.index.to_numpy())
        t = pd.DatetimeIndex(g["t"])
        k = int(np.floor(len(g) * train_frac))
        boundary = t[k] if k < len(g) else t[-1] + pd.Timedelta(seconds=1)
        train[pos[np.asarray(t < boundary - gap)]] = True
        test[pos[np.asarray(t >= boundary + gap)]] = True
    return train, test
