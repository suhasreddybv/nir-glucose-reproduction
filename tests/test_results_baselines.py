"""results/baselines_*.csv, predictions.csv and the label tables: internal consistency, verdicts
re-derived from the numbers, and the README tables regenerated from the CSVs and found verbatim."""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from src.eval.readme_tables import baseline_participant_table, baseline_summary_table, verdict_table

ROOT = Path(__file__).resolve().parents[1]


def _rows(name):
    with open(ROOT / "results" / name) as f:
        return list(csv.DictReader(f))


def test_summary_means_are_the_means_of_the_participant_rows():
    per = _rows("baselines_per_participant.csv"); summ = _rows("baselines_summary.csv")
    for s in summ:
        g = [r for r in per if r["regime"] == s["regime"] and r["baseline"] == s["baseline"]]
        assert len(g) == int(s["n_participants"]) and sum(int(r["n"]) for r in g) == int(s["n_rows"])
        v = np.array([float(r["rmse"]) for r in g])
        assert abs(v.mean() - float(s["rmse_mean"])) < 2e-3 and abs(v.std() - float(s["rmse_sd"])) < 2e-3
        assert float(s["rmse_ci_lo"]) <= float(s["rmse_mean"]) <= float(s["rmse_ci_hi"])
        a = np.array([float(r["accuracy"]) for r in g]); m = np.array([float(r["mape"]) for r in g])
        assert np.allclose(a, 100 - m)


def test_regimes_have_the_expected_coverage():
    summ = {(r["regime"], r["baseline"]): r for r in _rows("baselines_summary.csv")}
    assert int(summ[("R1_lopo", "B0_population_mean")]["n_rows"]) == 28964
    assert summ[("R1_lopo", "B0_population_mean")]["n_participants"] == "16"
    assert summ[("R1_halves", "B1_participant_mean")]["n_participants"] == "16"
    assert summ[("R3_blocked", "B1_participant_mean")]["n_participants"] == "15"      # 015 has nothing beyond its exclusion zone
    assert ("R1_lopo", "B1_participant_mean") not in summ                              # B1 needs the participant's own training data


def test_verdicts_follow_from_the_numbers():
    summ = {(r["regime"], r["baseline"]): r for r in _rows("baselines_summary.csv")}
    pred = {(r["prediction"], r["part"]): r for r in _rows("predictions.csv")}
    b1 = float(summ[("R1_halves", "B1_participant_mean")]["rmse_mean"])
    assert pred[("P1", "a")]["verdict"] == ("held" if abs(b1 - 21.10) <= 3 else "failed")
    b0 = float(summ[("R1_lopo", "B0_population_mean")]["rmse_mean"]); b2 = float(summ[("R1_lopo", "B2_hba1c_sex_linear")]["rmse_mean"])
    assert pred[("P2", "a")]["verdict"] == ("held" if min(abs(b0 - 21.22), abs(b2 - 21.22)) <= 3 else "failed")
    acc = float(summ[("R1_halves", "B1_participant_mean")]["accuracy_mean"])
    assert pred[("P4", "")]["verdict"] == ("held" if acc > 84 else "failed")
    assert pred[("P3", "")]["verdict"] == "pending"          # P1b, P2b, P5 are judged by the models (tests/test_results_models.py)


def test_b3_is_compared_with_b1_on_identical_rows():
    per = _rows("baselines_per_participant.csv")
    for reg in ("R1_halves", "R3_blocked"):
        b3 = {r["participant"]: r for r in per if r["regime"] == reg and r["baseline"] == "B3_e4_linear"}
        b1 = {r["participant"]: r for r in per if r["regime"] == reg and r["baseline"] == "B1_on_B3_rows"}
        assert b3.keys() == b1.keys() and all(b3[p]["n"] == b1[p]["n"] for p in b3)


def test_labels_tables_are_consistent():
    lab = _rows("labels.csv"); bal = _rows("balanced_set.csv"); dist = _rows("label_distribution.csv")
    for r in lab:
        assert int(r["labelled"]) + int(r["unlabelled_first_hour"]) == int(r["readings"]) and int(r["unlabelled_first_hour"]) == 11
        assert int(r["PersLow"]) + int(r["PersNorm"]) + int(r["PersHigh"]) == int(r["labelled"])
        assert int(r["in_balanced_set"]) <= int(r["complete_labelled"]) <= int(r["usable_labelled"]) <= int(r["labelled"])
    assert sum(int(r["in_balanced_set"]) for r in lab) == int(bal[1]["N"]) == 3 * int(bal[1]["PersLow"])
    assert bal[1]["PersLow"] == bal[1]["PersNorm"] == bal[1]["PersHigh"] == bal[0]["PersLow"]        # smallest class is PersLow
    assert sum(int(r["complete_labelled"]) for r in lab) == int(bal[0]["N"]) == 25644
    for d in dist:
        assert abs(float(d["mean"]) - float(d["paper_mean"])) < 2.0 and abs(float(d["sd"]) - float(d["paper_sd"])) < 2.0
    assert {d["label"]: int(d["n"]) for d in dist} == {k: sum(int(r[k]) for r in lab) for k in ("PersLow", "PersNorm", "PersHigh")}


def test_readme_tables_are_the_generated_ones():
    text = (ROOT / "README.md").read_text()
    for table in (baseline_summary_table(), baseline_participant_table(), verdict_table()):
        assert table in text, "README table differs from the one generated from results/*.csv"
    for quoted in ("20.99 ± 4.17", "86.97 %", "21.47 ± 3.94", "N = 10,230", "8,081 of the 28,964"):
        assert quoted in text
