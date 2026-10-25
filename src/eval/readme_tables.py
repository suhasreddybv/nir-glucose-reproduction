"""Markdown tables for the README, generated from the committed results CSVs so that no number is
typed by hand; `tests/test_results_baselines.py` asserts the README contains them verbatim."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _rows(name):
    with open(ROOT / "results" / name) as f:
        return list(csv.DictReader(f))


def baseline_summary_table() -> str:
    s = {(r["regime"], r["baseline"]): r for r in _rows("baselines_summary.csv")}
    names = {"B0_population_mean": "B0 population mean", "B1_participant_mean": "B1 per-participant mean (training half)",
             "B2_hba1c_sex_linear": "B2 linear on HbA1c + sex", "B3_e4_linear": "B3 per-participant linear on the 45 E4 features",
             "B1_on_B3_rows": "B1 on B3's rows"}
    regimes = [("R1_lopo", "Paper's population regime: leave-one-person-out", "21.22 ± 4.14 (XGBoost, LOPO)"),
               ("R1_halves", "Paper's personalised regime: first half → second half", "21.10 ± 4.50 (XGBoost, personalised)"),
               ("R3_blocked", "Time-blocked: first 70 % → last 30 %, 24-h exclusion zones", "—")]
    out = ["| Regime | Baseline | Participants | Rows | RMSE mean ± SD [95 % CI over participants] | MAPE | \"Accuracy\" (100 − MAPE) | Clarke A+B | Paper's model |",
           "|---|---|---|---|---|---|---|---|---|"]
    for reg, label, paper in regimes:
        for b in ("B0_population_mean", "B1_participant_mean", "B2_hba1c_sex_linear", "B3_e4_linear", "B1_on_B3_rows"):
            r = s.get((reg, b))
            if r is None:
                continue
            out.append(f"| {label} | {names[b]} | {r['n_participants']} | {int(r['n_rows']):,} | **{float(r['rmse_mean']):.2f}** ± {float(r['rmse_sd']):.2f} "
                       f"[{float(r['rmse_ci_lo']):.2f}, {float(r['rmse_ci_hi']):.2f}] | {float(r['mape_mean']):.2f} % | {float(r['accuracy_mean']):.2f} % | "
                       f"{float(r['clarke_AB_pct_mean']):.1f} % | {paper} |")
    return "\n".join(out)


def baseline_participant_table() -> str:
    per = _rows("baselines_per_participant.csv")
    d = {(r["regime"], r["baseline"], r["participant"]): r for r in per}
    out = ["| Participant | Second-half n | B1 RMSE | B1 MAPE | B1 \"accuracy\" | B2 RMSE (LOPO) | B3 RMSE (n) | B1 on B3's rows |", "|---|---|---|---|---|---|---|---|"]
    for pid in sorted({r["participant"] for r in per}):
        b1 = d[("R1_halves", "B1_participant_mean", pid)]; b2 = d[("R1_lopo", "B2_hba1c_sex_linear", pid)]
        b3 = d.get(("R1_halves", "B3_e4_linear", pid)); b13 = d.get(("R1_halves", "B1_on_B3_rows", pid))
        out.append(f"| {pid} | {int(b1['n']):,} | {float(b1['rmse']):.2f} | {float(b1['mape']):.2f} % | {float(b1['accuracy']):.2f} % | {float(b2['rmse']):.2f} | "
                   + (f"{float(b3['rmse']):.2f} ({int(b3['n']):,}) | {float(b13['rmse']):.2f} |" if b3 else "— | — |"))
    return "\n".join(out)


def verdict_table() -> str:
    out = ["| Prediction | Statement | Value | Reference | Verdict |", "|---|---|---|---|---|"]
    for r in _rows("predictions.csv"):
        out.append(f"| {r['prediction']}{r['part']} | {r['statement']} | {r['value'] or '—'} | {r['reference'] or '—'} | **{r['verdict']}** |")
    return "\n".join(out)


if __name__ == "__main__":
    print(baseline_summary_table()); print(); print(baseline_participant_table()); print(); print(verdict_table())
