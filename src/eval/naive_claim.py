"""Supplementary, added on 29 October 2026 after the pre-registered numbers existed (D-016): the
paper's own sentence - "Both the personalized model and the traditional population model
outperformed the naive models (mean and median)" - checked as literally as it can be. The
pre-registered baselines (§8) include means but no median. Here, per regime, the naive mean
and median of the training rows the paper's regime makes available: under LOPO the other
participants' pooled training glucose; under first-half / second-half the participant's own
first half. Paired per-participant RMSE against the full XGBoost, 16-participant bootstrap.
Writes results/naive_claim.csv."""
from __future__ import annotations

import csv
import sys

import numpy as np
import pandas as pd

from src.data.loader import REPO_ROOT
from src.eval.baselines import bootstrap_mean, metrics
from src.features.build import load_all
from src.splits import halves, lopo


def main() -> None:
    df = load_all()
    model = {(r["regime"], r["participant"]): float(r["rmse"]) for r in csv.DictReader(open(REPO_ROOT / "results" / "models_per_participant.csv")) if r["config"] == "full_69"}
    rows = []
    per = []
    for pid, tr, te in lopo(df):
        y = df.loc[te, "glucose"].to_numpy(float); g = df.loc[tr, "glucose"]
        for name, c in (("population_mean", g.mean()), ("population_median", g.median())):
            per.append(dict(regime="R1_lopo", naive=name, participant=pid, rmse=metrics(y, np.full(len(y), c))["rmse"]))
    tr, te = halves(df)
    for pid in sorted(df["participant"].unique()):
        g = df.loc[tr & (df["participant"] == pid).to_numpy(), "glucose"]; y = df.loc[te & (df["participant"] == pid).to_numpy(), "glucose"].to_numpy(float)
        for name, c in (("participant_mean", g.mean()), ("participant_median", g.median())):
            per.append(dict(regime="R1_halves", naive=name, participant=pid, rmse=metrics(y, np.full(len(y), c))["rmse"]))
    pf = pd.DataFrame(per)
    for (reg, name), g in pf.groupby(["regime", "naive"], sort=False):
        m = np.array([model[(reg, p)] for p in g["participant"]]); n = g["rmse"].to_numpy(float)
        d = n - m; lo, hi = bootstrap_mean(d)
        rows.append(dict(regime=reg, naive=name, n_participants=len(g), naive_rmse_mean=round(float(n.mean()), 3), model_rmse_mean=round(float(m.mean()), 3),
                         naive_minus_model=round(float(d.mean()), 3), ci_lo=round(lo, 3), ci_hi=round(hi, 3), participants_model_better=int((d > 0).sum()),
                         model_outperforms=bool(d.mean() > 0)))
        print(rows[-1])
    with open(REPO_ROOT / "results" / "naive_claim.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("wrote results/naive_claim.csv")


if __name__ == "__main__":
    sys.exit(main())
