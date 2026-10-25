"""The four pre-registered baselines (protocol §8) under the regression regimes of §9, with
every metric of §10, per participant with n, the paper's mean ± SD over participants, and the
16-participant bootstrap. Run before any model exists; P1 (first half), P2 (first half) and
P4 are judged here and written to results/predictions.csv.

Baselines are functions of the training rows only: `fit_predict(train, test)` may read the
test rows' features and participant, never their glucose. `tests/test_baselines.py` perturbs
the test glucose and asserts every prediction is unchanged.

  B0  population mean - the training rows' mean glucose (under LOPO: the other 15; under the
      within-participant regimes: all participants' training portions pooled).
  B1  per-participant mean of that participant's training portion (within-participant regimes).
  B2  a linear model glucose ~ HbA1c + sex, fitted on the training rows.
  B3  a per-participant linear model on the 45 E4 features, ridge alpha = 1 on standardised
      features (chosen before any number: 45 collinear quartile/min/max columns and ~700-1,200
      training rows make plain OLS extrapolate wildly), fitted on the participant's training
      rows with all 45 present, evaluated on test rows with all 45 present; n reported, and B1
      re-evaluated on exactly those rows for the paired delta.
"""
from __future__ import annotations

import csv
import sys
from datetime import date

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge

from src.data.loader import REPO_ROOT
from src.eval.clinical import clarke, mard, parkes
from src.features.build import E4_FEATURES, load_all
from src.splits import halves, lopo, time_blocked

PAPER = {"lopo_rmse": 21.22, "lopo_mape": 14.33, "halves_rmse": 21.10, "halves_mape": 13.26}
BOOT = 2000
RIDGE_ALPHA = 1.0


# ------------------------------------------------------------------ the baselines

def b0(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    return np.full(len(test), float(train["glucose"].mean()))


def b1(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    means = train.groupby("participant")["glucose"].mean()
    return test["participant"].map(means).to_numpy(dtype=float)


def b2(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    cols = ["HbA1c", "Biological Sex"]
    m = LinearRegression().fit(train[cols].to_numpy(float), train["glucose"].to_numpy(float))
    return m.predict(test[cols].to_numpy(float))


def b3(train: pd.DataFrame, test: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Per participant. Returns predictions (NaN where the test row lacks a feature or the
    participant has no complete training rows) and the mask of rows predicted."""
    cols = list(E4_FEATURES)
    pred = np.full(len(test), np.nan)
    for pid in test["participant"].unique():
        tr = train[(train["participant"] == pid)].dropna(subset=cols)
        te_mask = ((test["participant"] == pid) & test[cols].notna().all(axis=1)).to_numpy()
        if len(tr) < 2 * len(cols) or not te_mask.any():
            continue
        X = tr[cols].to_numpy(float); mu, sd = X.mean(0), X.std(0); sd[sd == 0] = 1.0
        m = Ridge(alpha=RIDGE_ALPHA).fit((X - mu) / sd, tr["glucose"].to_numpy(float))
        pred[te_mask] = m.predict((test.loc[te_mask, cols].to_numpy(float) - mu) / sd)
    return pred, ~np.isnan(pred)


# ------------------------------------------------------------------ metrics

def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    y = np.asarray(y, float); p = np.asarray(p, float)
    err = p - y
    mape = float(np.mean(np.abs(err) / y) * 100)
    out = dict(n=int(len(y)), rmse=round(float(np.sqrt(np.mean(err ** 2))), 3), mape=round(mape, 3), accuracy=round(100 - mape, 3))
    c, pk = clarke(y, p), parkes(y, p)
    out.update(clarke_A_pct=c["zone_A_pct"], clarke_AB_pct=c["zone_AB_pct"], parkes_A_pct=pk["zone_A_pct"], parkes_AB_pct=pk["zone_AB_pct"],
               mard_pct=mard(y, p)["mard_pct"])
    return out


def bootstrap_mean(values: np.ndarray, n_boot: int = BOOT, seed: int = 0) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    v = np.asarray(values, float)
    idx = rng.integers(0, len(v), size=(n_boot, len(v)))
    means = v[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


# ------------------------------------------------------------------ the run

def run(df: pd.DataFrame) -> tuple[list[dict], list[dict]]:
    """Per-participant rows and summary rows for every (regime, baseline)."""
    per = []
    regimes = {"R1_lopo": None, "R1_halves": halves(df), "R3_blocked": time_blocked(df)}
    for regime, masks in regimes.items():
        if regime == "R1_lopo":
            for pid, tr_m, te_m in lopo(df):
                tr, te = df[tr_m], df[te_m]
                for name, fn in (("B0_population_mean", b0), ("B2_hba1c_sex_linear", b2)):
                    per.append(dict(regime=regime, baseline=name, participant=pid, **metrics(te["glucose"], fn(tr, te))))
            continue
        tr_m, te_m = masks
        tr, te = df[tr_m], df[te_m]
        p0, p1, p2 = b0(tr, te), b1(tr, te), b2(tr, te)
        p3, m3 = b3(tr, te)
        for pid in sorted(df["participant"].unique()):
            sel = (te["participant"] == pid).to_numpy()
            y = te["glucose"].to_numpy(float)
            if not sel.any():          # R3 can leave a short record (015) with nothing beyond the exclusion zone
                print(f"  {regime}: {pid} has no test rows after the exclusion zone; omitted (n_participants says so)")
                continue
            for name, p in (("B0_population_mean", p0), ("B1_participant_mean", p1), ("B2_hba1c_sex_linear", p2)):
                per.append(dict(regime=regime, baseline=name, participant=pid, **metrics(y[sel], p[sel])))
            s3 = sel & m3
            if s3.any():
                per.append(dict(regime=regime, baseline="B3_e4_linear", participant=pid, **metrics(y[s3], p3[s3])))
                per.append(dict(regime=regime, baseline="B1_on_B3_rows", participant=pid, **metrics(y[s3], p1[s3])))
    summary = []
    pf = pd.DataFrame(per)
    for (regime, name), g in pf.groupby(["regime", "baseline"], sort=False):
        row = dict(regime=regime, baseline=name, n_participants=len(g), n_rows=int(g["n"].sum()))
        for k in ("rmse", "mape", "accuracy", "clarke_AB_pct", "parkes_AB_pct", "mard_pct"):
            v = g[k].to_numpy(float)
            row[f"{k}_mean"] = round(float(v.mean()), 3); row[f"{k}_sd"] = round(float(v.std()), 3)   # np.std, as loocvRF reports it
            lo, hi = bootstrap_mean(v); row[f"{k}_ci_lo"] = round(lo, 3); row[f"{k}_ci_hi"] = round(hi, 3)
        summary.append(row)
    return per, summary


def judge(summary: list[dict]) -> list[dict]:
    s = {(r["regime"], r["baseline"]): r for r in summary}
    b1h = s[("R1_halves", "B1_participant_mean")]; b0l = s[("R1_lopo", "B0_population_mean")]; b2l = s[("R1_lopo", "B2_hba1c_sex_linear")]
    today = str(date.today())
    rows = [
        dict(prediction="P1", part="a", statement="B1 under the personalised regime lands within 3 mg/dL of the paper's 21.10",
             value=b1h["rmse_mean"], reference=PAPER["halves_rmse"], criterion="|value - 21.10| <= 3",
             verdict="held" if abs(b1h["rmse_mean"] - PAPER["halves_rmse"]) <= 3 else "failed", judged=today, source="results/baselines_summary.csv"),
        dict(prediction="P1", part="b", statement="the personalised XGBoost beats B1 by less than 3 mg/dL", value="", reference=b1h["rmse_mean"],
             criterion="B1 rmse - model rmse < 3", verdict="pending", judged="", source=""),
        dict(prediction="P2", part="a", statement="B0 or B2 under LOPO lands within 3 mg/dL of the paper's 21.22",
             value=f"B0 {b0l['rmse_mean']}; B2 {b2l['rmse_mean']}", reference=PAPER["lopo_rmse"], criterion="either |value - 21.22| <= 3",
             verdict="held" if min(abs(b0l["rmse_mean"] - PAPER["lopo_rmse"]), abs(b2l["rmse_mean"] - PAPER["lopo_rmse"])) <= 3 else "failed",
             judged=today, source="results/baselines_summary.csv"),
        dict(prediction="P2", part="b", statement="the population XGBoost beats B2 by less than 3", value="", reference=b2l["rmse_mean"],
             criterion="B2 rmse - model rmse < 3", verdict="pending", judged="", source=""),
        dict(prediction="P3", part="", statement="classification reproduces within 3 points under R1 (84.3%) and falls by more than 15 points under R2 and R3",
             value="", reference=84.3, criterion="|R1 - 84.3| <= 3 and R1 - R2 > 15 and R1 - R3 > 15", verdict="pending", judged="", source=""),
        dict(prediction="P4", part="", statement="B1's accuracy (100 - MAPE) is above 84%, from a constant", value=b1h["accuracy_mean"], reference=84.0,
             criterion="value > 84", verdict="held" if b1h["accuracy_mean"] > 84 else "failed", judged=today, source="results/baselines_summary.csv"),
        dict(prediction="P5", part="", statement="measurement: removing the food log costs more RMSE than removing all E4 features", value="", reference="",
             criterion="report which way it goes", verdict="pending", judged="", source=""),
    ]
    return rows


def write(rows: list[dict], name: str) -> None:
    with open(REPO_ROOT / "results" / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"wrote results/{name}")


def main() -> None:
    df = load_all()
    print(f"{len(df):,} usable epochs, {df['participant'].nunique()} participants")
    tr, te = time_blocked(df)
    print(f"R3 time-blocked: {tr.sum():,} train, {te.sum():,} test, {len(df) - tr.sum() - te.sum():,} in the 24-h exclusion zones")
    per, summary = run(df)
    write(per, "baselines_per_participant.csv"); write(summary, "baselines_summary.csv")
    for r in summary:
        print(f"  {r['regime']:<11} {r['baseline']:<22} RMSE {r['rmse_mean']:6.2f} ± {r['rmse_sd']:5.2f} [{r['rmse_ci_lo']:.2f}, {r['rmse_ci_hi']:.2f}]  "
              f"MAPE {r['mape_mean']:5.2f}  acc {r['accuracy_mean']:5.2f}  Clarke A+B {r['clarke_AB_pct_mean']:5.1f}  MARD {r['mard_pct_mean']:5.2f}  n={r['n_rows']:,}")
    verdicts = judge(summary)
    write(verdicts, "predictions.csv")
    for v in verdicts:
        if v["verdict"] != "pending":
            print(f"  {v['prediction']}{v['part']}: {v['verdict']} — {v['statement']} (value {v['value']}, reference {v['reference']})")


if __name__ == "__main__":
    sys.exit(main())
