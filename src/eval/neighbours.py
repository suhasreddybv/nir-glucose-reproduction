"""How close is each test window to a training window of the same participant, under each
classification regime? Writes results/classification_neighbours.csv: per regime, the share of
test windows with a same-participant training window within 5, 15, 60 minutes and 24 hours,
pooled over folds. Measures the mechanism P3 rests on; changes no number elsewhere."""
from __future__ import annotations

import csv
import sys

import numpy as np
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedGroupKFold

from src.classify import CODE
from src.data.loader import REPO_ROOT
from src.eval.label_counts import labelled_matrix
from src.features.build import FEATURES, load_all
from src.labels import balanced_set
from src.splits import time_blocked

LAGS = {"5min": 300, "15min": 900, "60min": 3600, "24h": 86400}


def nearest_train_gap(t_s: np.ndarray, pid: np.ndarray, tr: np.ndarray, te: np.ndarray) -> np.ndarray:
    out = np.full(len(te), np.inf)
    for p in np.unique(pid[te]):
        tt = np.sort(t_s[tr][pid[tr] == p]); sel = np.flatnonzero(pid[te] == p)
        if not len(tt):
            continue
        x = t_s[te][sel]; k = np.searchsorted(tt, x)
        left = np.abs(x - tt[np.clip(k - 1, 0, len(tt) - 1)]); right = np.abs(tt[np.clip(k, 0, len(tt) - 1)] - x)
        out[sel] = np.minimum(left, right)
    return out


def main() -> None:
    full = labelled_matrix(load_all())
    complete = full[full["label"].notna()].dropna(subset=list(FEATURES))
    bal = balanced_set(complete, seed=0).reset_index(drop=True)
    y = bal["label"].map(CODE).to_numpy(); pid = bal["participant"].to_numpy()
    t_s = bal["t"].astype("int64").to_numpy() / 1e9
    regimes = {"R1_window_kfold": list(RepeatedStratifiedKFold(n_splits=10, n_repeats=3, random_state=0).split(bal, y)),
               "R2_participant_grouped": [s for rep in range(3) for s in StratifiedGroupKFold(n_splits=10, shuffle=True, random_state=rep).split(bal, y, pid)]}
    trm, tem = time_blocked(full)
    in_tr = set(zip(full.loc[trm, "participant"], full.loc[trm, "t"])); in_te = set(zip(full.loc[tem, "participant"], full.loc[tem, "t"]))
    keys = list(zip(bal["participant"], bal["t"]))
    regimes["R3_time_blocked"] = [(np.flatnonzero([k in in_tr for k in keys]), np.flatnonzero([k in in_te for k in keys]))]
    rows = []
    for name, splits in regimes.items():
        gaps = np.concatenate([nearest_train_gap(t_s, pid, tr, te) for tr, te in splits])
        row = dict(regime=name, test_windows=len(gaps), median_gap_min=round(float(np.median(gaps[np.isfinite(gaps)]) / 60), 1) if np.isfinite(gaps).any() else "",
                   no_same_participant_training_window=int(np.isinf(gaps).sum()))
        row.update({f"share_within_{k}": round(float((gaps <= v).mean()), 4) for k, v in LAGS.items()})
        rows.append(row); print(row)
    with open(REPO_ROOT / "results" / "classification_neighbours.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("wrote results/classification_neighbours.csv")


if __name__ == "__main__":
    sys.exit(main())
