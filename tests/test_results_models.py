"""results/models_*.csv, paired_deltas*.csv, selected_features.csv and predictions.csv: consistency,
verdicts re-derived from the numbers, the Table 3 overlap, and the README tables regenerated verbatim."""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from src.eval.readme_tables import model_participant_table, model_summary_table, top_features_table, verdict_table
from src.models import ABLATIONS

ROOT = Path(__file__).resolve().parents[1]


def _rows(name):
    with open(ROOT / "results" / name) as f:
        return list(csv.DictReader(f))


def test_models_cover_every_regime_and_ablation_on_the_baseline_rows():
    summ = {(r["regime"], r["config"]): r for r in _rows("models_summary.csv")}
    base = {(r["regime"], r["baseline"]): r for r in _rows("baselines_summary.csv")}
    assert set(summ) == {(reg, cfg) for reg in ("R1_lopo", "R1_halves", "R3_blocked") for cfg in ABLATIONS}
    for (reg, cfg), r in summ.items():
        b = base[(reg, "B2_hba1c_sex_linear" if reg == "R1_lopo" else "B1_participant_mean")]
        assert r["n_rows"] == b["n_rows"] and r["n_participants"] == b["n_participants"]     # identical rows
        assert 0 < float(r["n_features_mean"]) <= len(ABLATIONS[cfg])


def test_summary_means_match_the_participant_rows_and_deltas_are_paired():
    per = _rows("models_per_participant.csv"); summ = _rows("models_summary.csv")
    dpp = _rows("paired_deltas_per_participant.csv"); dsum = {(r["regime"], r["config"]): r for r in _rows("paired_deltas.csv")}
    bper = {(r["regime"], r["baseline"], r["participant"]): r for r in _rows("baselines_per_participant.csv")}
    for s in summ:
        g = [r for r in per if r["regime"] == s["regime"] and r["config"] == s["config"]]
        v = np.array([float(r["rmse"]) for r in g])
        assert abs(v.mean() - float(s["rmse_mean"])) < 2e-3 and abs(v.std() - float(s["rmse_sd"])) < 2e-3
        d = [r for r in dpp if r["regime"] == s["regime"] and r["config"] == s["config"]]
        dv = np.array([float(r["delta_rmse"]) for r in d])
        assert abs(dv.mean() - float(dsum[(s["regime"], s["config"])]["delta_rmse_mean"])) < 2e-3
        assert int(dsum[(s["regime"], s["config"])]["participants_model_better"]) == int((dv > 0).sum())
        for r in d:   # the baseline side of each delta is the baseline run's own number on the same rows
            b = bper[(r["regime"], r["baseline"], r["participant"])]
            assert b["n"] == r["n"] and abs(float(b["rmse"]) - float(r["baseline_rmse"])) < 1e-6
            assert abs(float(r["baseline_rmse"]) - float(r["model_rmse"]) - float(r["delta_rmse"])) < 2e-3


def test_verdicts_follow_from_the_numbers():
    pred = {(r["prediction"], r["part"]): r for r in _rows("predictions.csv")}
    d = {(r["regime"], r["config"]): r for r in _rows("paired_deltas.csv")}
    s = {(r["regime"], r["config"]): r for r in _rows("models_summary.csv")}
    assert pred[("P1", "b")]["verdict"] == ("held" if float(d[("R1_halves", "full_69")]["delta_rmse_mean"]) < 3 else "failed")
    assert pred[("P2", "b")]["verdict"] == ("held" if float(d[("R1_lopo", "full_69")]["delta_rmse_mean"]) < 3 else "failed")
    for reg, word in (("R1_lopo", "(LOPO)"), ("R1_halves", "(halves)")):
        food = float(s[(reg, "minus_food")]["rmse_mean"]) - float(s[(reg, "full_69")]["rmse_mean"])
        e4 = float(s[(reg, "minus_e4")]["rmse_mean"]) - float(s[(reg, "full_69")]["rmse_mean"])
        assert (("food costs more " + word) if food > e4 else ("E4 costs more " + word)) in pred[("P5", "")]["verdict"]
    assert pred[("P3", "")]["verdict"] == "pending"
    assert all(pred[k]["verdict"] == "held" for k in (("P1", "a"), ("P2", "a"), ("P4", "")))


def test_top_15_features_overlap_the_papers_table_3():
    paper = {"Minfrommid", "sugar24hr", "HbA1c", "carbs2hr", "Biological Sex", "Activity24", "sugar2hr", "sugar8hr", "ACC_mean_2hrs", "WakeTime", "ID",
             "ACC_max_2hrs", "protein24hr", "PeakEDA2hr_mean", "carbs24hr"}
    rows = [r for r in _rows("selected_features.csv") if r["regime"] == "R1_lopo" and r["config"] == "full_69"]
    assert len(rows) == 69 and all(r["folds"] == "16" for r in rows)
    rows.sort(key=lambda r: -float(r["importance_mean"]))
    assert rows[0]["feature"] == "Minfrommid"
    assert len({r["feature"] for r in rows[:15]} & paper) == 14


def test_readme_tables_are_the_generated_ones():
    text = (ROOT / "README.md").read_text()
    for table in (model_summary_table(), model_participant_table(), top_features_table(), verdict_table()):
        assert table in text, "README table differs from the one generated from results/*.csv"
    assert text.count(verdict_table()) == 1
    for quoted in ("21.29 ± 4.00", "+0.19 mg/dL [−0.63, +1.12]", "1.36 mg/dL [−3.34, +0.46]", "14 of the paper's top 15"):
        assert quoted in text
