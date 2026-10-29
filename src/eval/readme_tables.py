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


# ------------------------------------------------------------------ the models (Tuesday)

REGIME_LABEL = {"R1_lopo": "LOPO (paper's population regime)", "R1_halves": "first half → second half (paper's personalised regime)",
                "R3_blocked": "time-blocked, 24-h exclusion zones"}
CONFIG_LABEL = {"full_69": "full model, 69 features", "minus_food": "minus the food log (50)", "minus_user_model": "minus sex, HbA1c, ID (66)",
                "minus_e4": "minus all E4 features (24)", "e4_only": "E4 features + clock only (47)", "food_only": "food log + clock only (21)"}


def model_summary_table() -> str:
    s = {(r["regime"], r["config"]): r for r in _rows("models_summary.csv")}
    d = {(r["regime"], r["config"]): r for r in _rows("paired_deltas.csv")}
    paper = {"R1_lopo": "21.22 ± 4.14", "R1_halves": "21.10 ± 4.50", "R3_blocked": "—"}
    out = ["| Regime | Model | Participants | Rows | RMSE mean ± SD [95 % CI] | MAPE | \"Accuracy\" | Features kept (mean) | Baseline − model RMSE, mean [95 % CI] | Participants where the model is better | Paper |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for reg in ("R1_lopo", "R1_halves", "R3_blocked"):
        for cfg in ("full_69", "minus_food", "minus_user_model", "minus_e4", "e4_only", "food_only"):
            r, q = s.get((reg, cfg)), d.get((reg, cfg))
            if r is None:
                continue
            base = "B2" if reg == "R1_lopo" else "B1"
            out.append(f"| {REGIME_LABEL[reg]} | {CONFIG_LABEL[cfg]} | {r['n_participants']} | {int(r['n_rows']):,} | **{float(r['rmse_mean']):.2f}** ± {float(r['rmse_sd']):.2f} "
                       f"[{float(r['rmse_ci_lo']):.2f}, {float(r['rmse_ci_hi']):.2f}] | {float(r['mape_mean']):.2f} % | {float(r['accuracy_mean']):.2f} % | {float(r['n_features_mean']):.1f} | "
                       f"{base}: {float(q['delta_rmse_mean']):+.2f} [{float(q['delta_rmse_ci_lo']):+.2f}, {float(q['delta_rmse_ci_hi']):+.2f}] | {q['participants_model_better']} / {q['n_participants']} | "
                       f"{paper[reg] if cfg == 'full_69' else ''} |")
    return "\n".join(out)


def model_participant_table() -> str:
    d = {(r["regime"], r["config"], r["participant"]): r for r in _rows("paired_deltas_per_participant.csv")}
    out = ["| Participant | LOPO n | B2 RMSE | XGBoost RMSE | Δ | Second-half n | B1 RMSE | personalised XGBoost RMSE | Δ | Time-blocked n | B1 RMSE | XGBoost RMSE | Δ |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    pids = sorted({k[2] for k in d})
    for pid in pids:
        cells = [pid]
        for reg in ("R1_lopo", "R1_halves", "R3_blocked"):
            r = d.get((reg, "full_69", pid))
            cells += ([f"{int(r['n']):,}", f"{float(r['baseline_rmse']):.2f}", f"{float(r['model_rmse']):.2f}", f"{float(r['delta_rmse']):+.2f}"] if r else ["—"] * 4)
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def top_features_table(n: int = 15) -> str:
    rows = [r for r in _rows("selected_features.csv") if r["regime"] == "R1_lopo" and r["config"] == "full_69"]
    rows.sort(key=lambda r: -float(r["importance_mean"]))
    paper = ["Minutes from midnight", "Sugar intake (previous 24 h)", "Hemoglobin A1c (HbA1c)", "Carbohydrates (previous 2 h)", "Biological sex", "Activity (previous 24 h)",
             "Sugar intake (previous 2 h)", "Sugar intake (previous 8 h)", "Accelerometry (mean previous 2 h)", "Wake time", "ID", "Accelerometry (max previous 2 h)",
             "Protein (previous 24 h)", "Peak electrodermal activity (mean previous 2 h)", "Carbohydrates (previous 24 h)"]
    out = ["| Rank | Feature (this reproduction) | RF importance mean ± SD over 16 LOPO folds | Selected in folds | Paper's Table 3 at this rank |", "|---|---|---|---|---|"]
    for i, r in enumerate(rows[:n]):
        out.append(f"| {i + 1} | {r['feature']} | {float(r['importance_mean']):.3f} ± {float(r['importance_sd']):.3f} | {r['times_selected']} / {r['folds']} | {paper[i]} |")
    return "\n".join(out)


# ------------------------------------------------------------------ classification (Wednesday) and the front page

CLS_LABEL = {"R1_window_kfold": "Paper's split: random windows, repeated stratified 10-fold × 3", "R1_70_30_tree": "Paper's 70/30 random-window split, decision tree",
             "R1_70_30_logistic": "Paper's 70/30 split, logistic regression", "R2_participant_grouped": "Participant-grouped 10-fold × 3",
             "R3_time_blocked": "Time-blocked within participant, 24-h exclusion zones"}


def classification_table() -> str:
    out = ["| Regime | Folds | Test windows (all folds) | Balanced accuracy, mean ± SD [95 % CI] | Weighted F1 | R² | Paper |", "|---|---|---|---|---|---|---|"]
    for r in _rows("classification_summary.csv"):
        ci = f" [{float(r['balanced_accuracy_ci_lo']):.2f}, {float(r['balanced_accuracy_ci_hi']):.2f}]" if r["balanced_accuracy_ci_lo"] else ""
        sd = f" ± {float(r['balanced_accuracy_sd']):.2f}" if int(r["folds"]) > 1 else ""
        paper = {"R1_window_kfold": "84.3 ± 1.3; R² 0.505", "R1_70_30_tree": "82.0; R² 0.455", "R1_70_30_logistic": "52.0; R² 0"}.get(r["regime"], "—")
        out.append(f"| {CLS_LABEL[r['regime']]} | {r['folds']} | {int(r['n_test_total']):,} | **{float(r['balanced_accuracy_mean']):.2f} %**{sd}{ci} | "
                   f"{float(r['f1_weighted_mean']):.2f} % | {float(r['r2_mean']):.3f} | {paper} |")
    return "\n".join(out)


def classification_class_table() -> str:
    out = ["| Regime | Recall PersLow | Recall PersNorm | Recall PersHigh | PPV PersLow at true prevalence | PPV PersNorm | PPV PersHigh |", "|---|---|---|---|---|---|---|"]
    for r in _rows("classification_summary.csv"):
        out.append(f"| {CLS_LABEL[r['regime']]} | {float(r['recall_PersLow']):.1f} % | {float(r['recall_PersNorm']):.1f} % | {float(r['recall_PersHigh']):.1f} % | "
                   f"{float(r['ppv_adjusted_PersLow']):.1f} % | {float(r['ppv_adjusted_PersNorm']):.1f} % | {float(r['ppv_adjusted_PersHigh']):.1f} % |")
    return "\n".join(out)


def confusion_tables() -> str:
    cm = _rows("classification_confusion.csv")
    blocks = []
    for reg in CLS_LABEL:
        rows = [r for r in cm if r["regime"] == reg]
        b = [f"**{CLS_LABEL[reg]}** (rows true, columns predicted, summed over folds)", "", "| | PersLow | PersNorm | PersHigh |", "|---|---|---|---|"]
        b += [f"| {r['true']} | {int(r['pred_PersLow']):,} | {int(r['pred_PersNorm']):,} | {int(r['pred_PersHigh']):,} |" for r in rows]
        blocks.append("\n".join(b))
    return "\n\n".join(blocks)


def front_page_table() -> str:
    """The headline: the paper's number, this reproduction's, and the baseline it has to beat, per regime."""
    m = {(r["regime"], r["config"]): r for r in _rows("models_summary.csv")}
    b = {(r["regime"], r["baseline"]): r for r in _rows("baselines_summary.csv")}
    d = {(r["regime"], r["config"]): r for r in _rows("paired_deltas.csv")}
    c = {r["regime"]: r for r in _rows("classification_summary.csv")}
    out = ["| Task and regime | Paper | This reproduction | The baseline it has to beat | Model − baseline (paired, 95 % CI) |", "|---|---|---|---|---|"]
    for reg, label, paper, base_key, base_label in (
            ("R1_lopo", "Glucose, RMSE mg/dL — leave one person out (paper's)", "21.22 ± 4.14", "B2_hba1c_sex_linear", "linear on HbA1c + sex"),
            ("R1_halves", "Glucose, RMSE — first half → second half (paper's)", "21.10 ± 4.50", "B1_participant_mean", "the participant's first-half mean"),
            ("R3_blocked", "Glucose, RMSE — time-blocked, 24-h zones", "—", "B1_participant_mean", "the participant's own mean")):
        r, q, bb = m[(reg, "full_69")], d[(reg, "full_69")], b[(reg, base_key)]
        out.append(f"| {label} | {paper} | **{float(r['rmse_mean']):.2f}** ± {float(r['rmse_sd']):.2f} | {base_label}: {float(bb['rmse_mean']):.2f} ± {float(bb['rmse_sd']):.2f} | "
                   f"{-float(q['delta_rmse_mean']):+.2f} [{-float(q['delta_rmse_ci_hi']):+.2f}, {-float(q['delta_rmse_ci_lo']):+.2f}]; worse in {int(q['n_participants']) - int(q['participants_model_better'])} of {q['n_participants']} |")
    for reg, label, paper in (("R1_window_kfold", "Excursion class, balanced accuracy — random windows (paper's)", "84.3 ± 1.3 %"),
                              ("R2_participant_grouped", "Excursion class — participant-grouped", "—"), ("R3_time_blocked", "Excursion class — time-blocked", "—")):
        r = c[reg]
        out.append(f"| {label} | {paper} | **{float(r['balanced_accuracy_mean']):.1f} %** | chance: 33.3 % | — |")
    return "\n".join(out)


def ablation_table() -> str:
    s = {(r["regime"], r["config"]): r for r in _rows("models_summary.csv")}
    out = ["| Features | Leave one person out | First half → second half | Time-blocked |", "|---|---|---|---|"]
    for cfg in ("full_69", "minus_food", "minus_user_model", "minus_e4", "e4_only", "food_only"):
        out.append(f"| {CONFIG_LABEL[cfg]} | " + " | ".join(f"{float(s[(reg, cfg)]['rmse_mean']):.2f}" for reg in ("R1_lopo", "R1_halves", "R3_blocked")) + " |")
    b = {(r["regime"], r["baseline"]): r for r in _rows("baselines_summary.csv")}
    out.append("| *Baseline: HbA1c + sex (across) / own mean (within)* | " + " | ".join(
        f"*{float(b[(reg, k)]['rmse_mean']):.2f}*" for reg, k in (("R1_lopo", "B2_hba1c_sex_linear"), ("R1_halves", "B1_participant_mean"), ("R3_blocked", "B1_participant_mean"))) + " |")
    return "\n".join(out)
