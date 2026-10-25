"""Labels on every reading, their distribution against the paper's Table 1, and the balanced set.
Writes results/labels.csv (per participant), results/label_distribution.csv (per class, pooled,
beside Table 1), results/balanced_set.csv (what undersampling produced, beside N = 8,666)."""
from __future__ import annotations

import csv
import sys

import numpy as np
import pandas as pd

from src.data.loader import PARTICIPANTS, REPO_ROOT, load_participant
from src.features.build import FEATURES, load_all
from src.labels import LABELS, balanced_set, pers_labels

TABLE1 = {"PersNorm": (112.4, 14.5, 66.0, 164.0), "PersHigh": (149.9, 24.4, 93.0, 260.0), "PersLow": (90.8, 11.1, 46.0, 120.0)}


def labelled_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """The feature matrix with the label of each reading joined on (participant, t)."""
    parts = []
    for pid in PARTICIPANTS:
        rec, _ = load_participant(pid)
        lab = pers_labels(rec.cgm.ts, rec.cgm.values); lab["participant"] = pid
        parts.append(lab[["participant", "t", "label", "roll_mean", "roll_sd"]])
    labels = pd.concat(parts, ignore_index=True)
    return df.merge(labels, on=["participant", "t"], how="left")


def main() -> None:
    rows, pooled = [], []
    for pid in PARTICIPANTS:
        rec, _ = load_participant(pid)
        lab = pers_labels(rec.cgm.ts, rec.cgm.values)
        lab["participant"] = pid
        pooled.append(lab)
        n = len(lab); labelled = int(lab["label"].notna().sum())
        c = lab["label"].value_counts()
        rows.append(dict(participant=pid, readings=n, labelled=labelled, unlabelled_first_hour=n - labelled,
                         **{k: int(c.get(k, 0)) for k in LABELS}, **{f"share_{k}": round(c.get(k, 0) / labelled, 4) for k in LABELS}))
    allab = pd.concat(pooled, ignore_index=True)
    dist = []
    for k in LABELS:
        v = allab.loc[allab["label"] == k, "glucose"].to_numpy(float)
        dist.append(dict(label=k, n=len(v), mean=round(v.mean(), 1), sd=round(v.std(ddof=1), 1), min=v.min(), max=v.max(),
                         paper_mean=TABLE1[k][0], paper_sd=TABLE1[k][1], paper_min=TABLE1[k][2], paper_max=TABLE1[k][3]))
    df = labelled_matrix(load_all())
    usable_lab = df[df["label"].notna()]
    complete = usable_lab.dropna(subset=list(FEATURES))
    bal = balanced_set(complete, seed=0)
    bc = bal["label"].value_counts()
    for r in rows:
        r["usable_labelled"] = int((usable_lab["participant"] == r["participant"]).sum())
        r["complete_labelled"] = int((complete["participant"] == r["participant"]).sum())
        r["in_balanced_set"] = int((bal["participant"] == r["participant"]).sum())
    bal_rows = [dict(set="complete_labelled_epochs", N=len(complete), **{k: int((complete["label"] == k).sum()) for k in LABELS}, rule="", seed="", paper_N=""),
                dict(set="balanced", N=len(bal), **{k: int(bc[k]) for k in LABELS}, rule="undersample every class to the smallest class's count", seed=0, paper_N=8666)]
    for data, fn in ((rows, "labels.csv"), (dist, "label_distribution.csv"), (bal_rows, "balanced_set.csv")):
        with open(REPO_ROOT / "results" / fn, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0])); w.writeheader(); w.writerows(data)
        print(f"wrote results/{fn}")
    tot = {k: sum(r[k] for r in rows) for k in LABELS}; L = sum(r["labelled"] for r in rows)
    print(f"labelled {L:,} of {sum(r['readings'] for r in rows):,} readings: " + ", ".join(f"{k} {tot[k]:,} ({tot[k] / L:.1%})" for k in LABELS))
    for d in dist:
        print(f"  {d['label']}: {d['mean']} ± {d['sd']} [{d['min']:.0f}-{d['max']:.0f}] n={d['n']:,}  (paper {d['paper_mean']} ± {d['paper_sd']} [{d['paper_min']:.0f}-{d['paper_max']:.0f}])")
    print(f"complete labelled epochs {len(complete):,}; balanced set N = {len(bal):,} ({dict(bc)}); paper N = 8,666")


if __name__ == "__main__":
    sys.exit(main())
