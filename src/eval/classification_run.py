"""Run the classification under R1 (the paper's repeated stratified 10-fold x 3 on windows, and
its 70/30 split), R2 (participant-grouped 10-fold x 3) and R3 (time-blocked within participant,
24-h exclusion zones), on the class-balanced set of D-011. Judge P3; write
results/classification_folds.csv, classification_summary.csv, classification_confusion.csv,
classification_selected.csv; update results/predictions.csv.

Stop rule (protocol §11): if the R1 balanced accuracy is more than 10 points from 84.3 %, the
script writes the R1 numbers, prints STOP and does not run R2 or R3.
"""
from __future__ import annotations

import csv
import sys
from datetime import date

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedGroupKFold, train_test_split

from src.classify import CODE, confusion, fit_predict, per_class_recall, prevalence_adjusted_ppv, scores
from src.data.loader import REPO_ROOT
from src.eval.baselines import bootstrap_mean
from src.eval.label_counts import labelled_matrix
from src.features.build import FEATURES, load_all
from src.labels import LABELS, balanced_set
from src.splits import time_blocked

PAPER = {"R1_cv": 84.3, "R1_70_30_tree": 82.0, "R1_70_30_logistic": 52.0}
STOP_POINTS = 10.0


def _fold(X, y, tr, te, kind):
    pred, keep = fit_predict(X[tr], y[tr], X[te], kind)
    return te, pred, keep


def run_folds(name, X, y, splits, kind="tree"):
    out = Parallel(n_jobs=8)(delayed(_fold)(X, y, tr, te, kind) for tr, te in splits)
    rows, cm, keeps = [], np.zeros((3, 3), int), []
    for k, (te, pred, keep) in enumerate(out):
        s = scores(y[te], pred); rows.append(dict(regime=name, fold=k, **s))
        cm += confusion(y[te], pred); keeps.append(keep)
    return rows, cm, np.array(keeps)


def summarise(name, rows, cm, prevalence, paper=None, unit="fold"):
    ba = np.array([r["balanced_accuracy"] for r in rows]) * 100
    out = dict(regime=name, unit=unit, folds=len(rows), n_test_total=int(sum(r["n"] for r in rows)),
               balanced_accuracy_mean=round(ba.mean(), 2), balanced_accuracy_sd=round(ba.std(), 2))
    if len(rows) > 1:
        lo, hi = bootstrap_mean(ba); out.update(balanced_accuracy_ci_lo=round(lo, 2), balanced_accuracy_ci_hi=round(hi, 2))
    else:
        out.update(balanced_accuracy_ci_lo="", balanced_accuracy_ci_hi="")
    for k in ("precision_weighted", "recall_weighted", "f1_weighted", "r2"):
        v = np.array([r[k] for r in rows]) * (100 if k != "r2" else 1)
        out[f"{k}_mean"] = round(v.mean(), 3 if k == "r2" else 2); out[f"{k}_sd"] = round(v.std(), 3 if k == "r2" else 2)
    rec = per_class_recall(cm) * 100; ppv = prevalence_adjusted_ppv(cm, prevalence) * 100
    for i, lab in enumerate(LABELS):
        out[f"recall_{lab}"] = round(rec[i], 2); out[f"ppv_adjusted_{lab}"] = round(ppv[i], 2)
    out["paper_balanced_accuracy"] = paper if paper is not None else ""
    return out


def cm_rows(name, cm):
    return [dict(regime=name, true=LABELS[i], **{f"pred_{LABELS[j]}": int(cm[i, j]) for j in range(3)}) for i in range(3)]


def write(rows, name):
    with open(REPO_ROOT / "results" / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"wrote results/{name}")


def main() -> int:
    full = labelled_matrix(load_all())
    complete = full[full["label"].notna()].dropna(subset=list(FEATURES))
    prevalence = complete["label"].value_counts(normalize=True).reindex(list(LABELS)).to_numpy()
    bal = balanced_set(complete, seed=0)
    X = bal[list(FEATURES)].to_numpy(float); y = bal["label"].map(CODE).to_numpy(int)
    groups = bal["participant"].to_numpy()
    print(f"balanced set N = {len(bal):,}; true prevalence on {len(complete):,} complete labelled epochs: "
          + ", ".join(f"{l} {p:.1%}" for l, p in zip(LABELS, prevalence)))
    folds, summ, cms, sel = [], [], [], []

    def record(name, rows, cm, keeps, paper=None, unit="fold"):
        folds.extend(rows); s = summarise(name, rows, cm, prevalence, paper, unit); summ.append(s); cms.extend(cm_rows(name, cm))
        for j, f in enumerate(FEATURES):
            sel.append(dict(regime=name, feature=f, folds=len(keeps), times_selected=int(keeps[:, j].sum())))
        print(f"  {name:<22} balanced accuracy {s['balanced_accuracy_mean']:6.2f} ± {s['balanced_accuracy_sd']:5.2f}"
              + (f"  (paper {paper})" if paper is not None else "")
              + "  recall L/N/H " + "/".join(f"{s[f'recall_{l}']:.1f}" for l in LABELS)
              + "  adj. PPV L/N/H " + "/".join(f"{s[f'ppv_adjusted_{l}']:.1f}" for l in LABELS), flush=True)
        return s

    # R1: the paper's split
    rskf = RepeatedStratifiedKFold(n_splits=10, n_repeats=3, random_state=0)
    r1 = record("R1_window_kfold", *run_folds("R1_window_kfold", X, y, list(rskf.split(X, y))), paper=PAPER["R1_cv"])
    idx = np.arange(len(y)); tr, te = train_test_split(idx, test_size=0.3, stratify=y, random_state=0)
    for kind, key in (("tree", "R1_70_30_tree"), ("logistic", "R1_70_30_logistic")):
        record(key, *run_folds(key, X, y, [(tr, te)], kind), paper=PAPER[key], unit="split")
    off = abs(r1["balanced_accuracy_mean"] - PAPER["R1_cv"])
    if off > STOP_POINTS:
        write(folds, "classification_folds.csv"); write(summ, "classification_summary.csv"); write(cms, "classification_confusion.csv")
        print(f"STOP: R1 balanced accuracy {r1['balanced_accuracy_mean']} is {off:.1f} points from 84.3 (> {STOP_POINTS}); R2 and R3 not run")
        return 2
    # R2: participant-grouped
    splits = []
    for rep in range(3):
        splits += list(StratifiedGroupKFold(n_splits=10, shuffle=True, random_state=rep).split(X, y, groups))
    r2 = record("R2_participant_grouped", *run_folds("R2_participant_grouped", X, y, splits))
    # R3: time-blocked within participant; boundary and exclusion zones from the full usable matrix
    trm, tem = time_blocked(full)
    in_tr = set(zip(full.loc[trm, "participant"], full.loc[trm, "t"])); in_te = set(zip(full.loc[tem, "participant"], full.loc[tem, "t"]))
    keys = list(zip(bal["participant"], bal["t"]))
    tr3 = np.array([k in in_tr for k in keys]); te3 = np.array([k in in_te for k in keys])
    print(f"  R3: {tr3.sum():,} balanced rows train, {te3.sum():,} test, {len(keys) - tr3.sum() - te3.sum():,} in the exclusion zones")
    r3 = record("R3_time_blocked", *run_folds("R3_time_blocked", X, y, [(np.flatnonzero(tr3), np.flatnonzero(te3))]), unit="split")
    write(folds, "classification_folds.csv"); write(summ, "classification_summary.csv")
    write(cms, "classification_confusion.csv"); write(sel, "classification_selected.csv")
    # P3, against the frozen words
    a1, a2, a3 = r1["balanced_accuracy_mean"], r2["balanced_accuracy_mean"], r3["balanced_accuracy_mean"]
    held = abs(a1 - 84.3) <= 3 and (a1 - a2) > 15 and (a1 - a3) > 15
    pred = list(csv.DictReader(open(REPO_ROOT / "results" / "predictions.csv")))
    for r in pred:
        if r["prediction"] == "P3":
            r.update(value=f"R1 {a1}; R2 {a2} (drop {a1 - a2:.2f}); R3 {a3} (drop {a1 - a3:.2f})", verdict="held" if held else "failed",
                     judged=str(date.today()), source="results/classification_summary.csv")
    write(pred, "predictions.csv")
    print(f"  P3: {'held' if held else 'failed'} — R1 {a1} (|R1 - 84.3| = {abs(a1 - 84.3):.2f}), R1 - R2 = {a1 - a2:.2f}, R1 - R3 = {a1 - a3:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
