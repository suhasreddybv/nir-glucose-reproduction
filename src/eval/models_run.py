"""Run the paper's model and its ablations under R1 (LOPO; halves) and R3 (time-blocked,
personalised), score per participant, pair against B1 / B2 on identical rows, judge P1b, P2b,
P5. Writes results/models_per_participant.csv, models_summary.csv, paired_deltas.csv,
selected_features.csv, and updates results/predictions.csv.
"""
from __future__ import annotations

import csv
import sys
import time
from datetime import date

import numpy as np
import pandas as pd

from src.data.loader import REPO_ROOT
from src.eval.baselines import PAPER, b1, b2, bootstrap_mean, metrics
from src.features.build import load_all
from src.models import ABLATIONS, fit_predict
from src.splits import halves, lopo, time_blocked

SUMMARY_KEYS = ("rmse", "mape", "accuracy", "clarke_AB_pct", "parkes_AB_pct", "mard_pct")


def _summ(rows: list[dict], keys=("regime", "config")) -> list[dict]:
    out = []
    pf = pd.DataFrame(rows)
    for k, g in pf.groupby(list(keys), sort=False):
        row = dict(zip(keys, k)); row.update(n_participants=len(g), n_rows=int(g["n"].sum()))
        for m in SUMMARY_KEYS:
            v = g[m].to_numpy(float); lo, hi = bootstrap_mean(v)
            row.update({f"{m}_mean": round(float(v.mean()), 3), f"{m}_sd": round(float(v.std()), 3), f"{m}_ci_lo": round(lo, 3), f"{m}_ci_hi": round(hi, 3)})
        row["n_features_mean"] = round(float(g["n_features"].mean()), 1)
        out.append(row)
    return out


def run(df: pd.DataFrame, configs=ABLATIONS) -> tuple[list[dict], list[dict], list[dict]]:
    per, deltas, selected = [], [], []
    pids = sorted(df["participant"].unique())
    for regime in ("R1_lopo", "R1_halves", "R3_blocked"):
        for config, cols in configs.items():
            t0 = time.time()
            preds, base_name, base_pred, imps = {}, "", {}, []
            if regime == "R1_lopo":
                base_name = "B2_hba1c_sex_linear"
                for pid, tr_m, te_m in lopo(df):
                    tr, te = df[tr_m], df[te_m]
                    p, kept, imp = fit_predict(tr, te, cols)
                    preds[pid] = (te["glucose"].to_numpy(float), p, len(kept)); base_pred[pid] = b2(tr, te); imps.append(imp)
            else:
                base_name = "B1_participant_mean"
                tr_m, te_m = halves(df) if regime == "R1_halves" else time_blocked(df)
                tr, te = df[tr_m], df[te_m]
                for pid in pids:
                    trp, tep = tr[tr["participant"] == pid], te[te["participant"] == pid]
                    if len(tep) == 0:
                        continue
                    p, kept, imp = fit_predict(trp, tep, cols)
                    preds[pid] = (tep["glucose"].to_numpy(float), p, len(kept)); base_pred[pid] = b1(trp, tep); imps.append(imp)
            d = []
            for pid, (y, p, nk) in preds.items():
                mm = metrics(y, p); mb = metrics(y, base_pred[pid])
                per.append(dict(regime=regime, config=config, participant=pid, n_features=nk, **mm))
                d.append(mb["rmse"] - mm["rmse"])
                deltas.append(dict(regime=regime, config=config, participant=pid, baseline=base_name, n=mm["n"], baseline_rmse=mb["rmse"], model_rmse=mm["rmse"],
                                   delta_rmse=round(mb["rmse"] - mm["rmse"], 3), baseline_mape=mb["mape"], model_mape=mm["mape"], delta_mape=round(mb["mape"] - mm["mape"], 3)))
            imp_df = pd.concat(imps, axis=1)
            for f in cols:
                selected.append(dict(regime=regime, config=config, feature=f, folds=imp_df.shape[1], times_selected=int((imp_df.loc[f] >= 0.005).sum()),
                                     importance_mean=round(float(imp_df.loc[f].mean()), 4), importance_sd=round(float(imp_df.loc[f].std(ddof=0)), 4)))
            d = np.array(d); lo, hi = bootstrap_mean(d)
            print(f"  {regime:<10} {config:<17} RMSE {np.mean([r['rmse'] for r in per if r['regime'] == regime and r['config'] == config]):6.2f}  "
                  f"delta vs {base_name[:2]} {d.mean():+.2f} [{lo:+.2f}, {hi:+.2f}]  better in {int((d > 0).sum())}/{len(d)}  ({time.time() - t0:.0f} s)", flush=True)
    return per, deltas, selected


def delta_summary(deltas: list[dict]) -> list[dict]:
    out = []
    for (regime, config, base), g in pd.DataFrame(deltas).groupby(["regime", "config", "baseline"], sort=False):
        d = g["delta_rmse"].to_numpy(float); lo, hi = bootstrap_mean(d)
        dm = g["delta_mape"].to_numpy(float); mlo, mhi = bootstrap_mean(dm)
        out.append(dict(regime=regime, config=config, baseline=base, n_participants=len(g), delta_rmse_mean=round(float(d.mean()), 3), delta_rmse_ci_lo=round(lo, 3),
                        delta_rmse_ci_hi=round(hi, 3), participants_model_better=int((d > 0).sum()), delta_mape_mean=round(float(dm.mean()), 3),
                        delta_mape_ci_lo=round(mlo, 3), delta_mape_ci_hi=round(mhi, 3)))
    return out


def judge(summary: list[dict], dsum: list[dict]) -> None:
    s = {(r["regime"], r["config"]): r for r in summary}; d = {(r["regime"], r["config"]): r for r in dsum}
    pred = list(csv.DictReader(open(REPO_ROOT / "results" / "predictions.csv")))
    today = str(date.today())
    full_h, full_l = s[("R1_halves", "full_69")], s[("R1_lopo", "full_69")]
    dh, dl = d[("R1_halves", "full_69")], d[("R1_lopo", "full_69")]
    cost = {reg: dict(food=round(s[(reg, "minus_food")]["rmse_mean"] - s[(reg, "full_69")]["rmse_mean"], 3),
                      e4=round(s[(reg, "minus_e4")]["rmse_mean"] - s[(reg, "full_69")]["rmse_mean"], 3)) for reg in ("R1_lopo", "R1_halves")}
    for r in pred:
        key = (r["prediction"], r["part"])
        if key == ("P1", "b"):
            r.update(value=f"model {full_h['rmse_mean']}; B1 - model {dh['delta_rmse_mean']} [{dh['delta_rmse_ci_lo']}, {dh['delta_rmse_ci_hi']}]",
                     verdict="held" if dh["delta_rmse_mean"] < 3 else "failed", judged=today, source="results/paired_deltas.csv")
        elif key == ("P2", "b"):
            r.update(value=f"model {full_l['rmse_mean']}; B2 - model {dl['delta_rmse_mean']} [{dl['delta_rmse_ci_lo']}, {dl['delta_rmse_ci_hi']}]",
                     verdict="held" if dl["delta_rmse_mean"] < 3 else "failed", judged=today, source="results/paired_deltas.csv")
        elif key == ("P5", ""):
            r.update(value=f"LOPO: minus food +{cost['R1_lopo']['food']}, minus E4 +{cost['R1_lopo']['e4']}; halves: minus food +{cost['R1_halves']['food']}, minus E4 +{cost['R1_halves']['e4']}",
                     verdict=("food costs more" if cost["R1_lopo"]["food"] > cost["R1_lopo"]["e4"] else "E4 costs more") + " (LOPO); "
                             + ("food costs more" if cost["R1_halves"]["food"] > cost["R1_halves"]["e4"] else "E4 costs more") + " (halves)",
                     judged=today, source="results/models_summary.csv")
    with open(REPO_ROOT / "results" / "predictions.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pred[0])); w.writeheader(); w.writerows(pred)
    for r in pred:
        if r["judged"] == today:
            print(f"  {r['prediction']}{r['part']}: {r['verdict']} — {r['value']}")


def write(rows, name):
    with open(REPO_ROOT / "results" / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"wrote results/{name}")


def main() -> None:
    df = load_all()
    per, deltas, selected = run(df)
    summary = _summ(per); dsum = delta_summary(deltas)
    write(per, "models_per_participant.csv"); write(summary, "models_summary.csv"); write(deltas, "paired_deltas_per_participant.csv")
    write(dsum, "paired_deltas.csv"); write(selected, "selected_features.csv")
    judge(summary, dsum)


if __name__ == "__main__":
    sys.exit(main())
