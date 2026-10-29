"""results/classification_*.csv, naive_claim.csv and the three generated documents: consistency,
the P3 verdict re-derived from its frozen words, and README.md, docs/reproduction.md and
docs/classification.md byte-identical to what src/eval/write_docs.py generates from results/."""
from __future__ import annotations

import csv
import re
from pathlib import Path

import numpy as np

from src.classify import prevalence_adjusted_ppv
from src.eval.write_docs import classification_doc, readme, reproduction_doc

ROOT = Path(__file__).resolve().parents[1]
TEST_COUNT = re.compile(r"# \d+ tests; \d+ need the dataset")


def _rows(name):
    with open(ROOT / "results" / name) as f:
        return list(csv.DictReader(f))


def test_generated_documents_match_the_results():
    for path, text in (("README.md", readme()), ("docs/reproduction.md", reproduction_doc()), ("docs/classification.md", classification_doc())):
        on_disk = (ROOT / path).read_text()
        # the ship script rewrites the test-count line after the suite runs; compare without it
        assert TEST_COUNT.sub("#", on_disk) == TEST_COUNT.sub("#", text), f"{path} is stale: run python -m src.eval.write_docs"


def test_fold_rows_reproduce_the_summary():
    folds = _rows("classification_folds.csv"); summ = {r["regime"]: r for r in _rows("classification_summary.csv")}
    for reg, s in summ.items():
        ba = np.array([float(r["balanced_accuracy"]) for r in folds if r["regime"] == reg]) * 100
        assert len(ba) == int(s["folds"]) and abs(ba.mean() - float(s["balanced_accuracy_mean"])) < 0.01


def test_confusion_matrices_give_the_reported_recall_and_ppv():
    cm = _rows("classification_confusion.csv"); summ = {r["regime"]: r for r in _rows("classification_summary.csv")}
    bal = _rows("balanced_set.csv")[0]
    prev = np.array([int(bal[k]) for k in ("PersLow", "PersNorm", "PersHigh")], float); prev /= prev.sum()
    for reg, s in summ.items():
        m = np.array([[int(r[f"pred_{k}"]) for k in ("PersLow", "PersNorm", "PersHigh")] for r in cm if r["regime"] == reg])
        assert m.sum() == int(s["n_test_total"])
        rec = m.diagonal() / m.sum(1) * 100; ppv = prevalence_adjusted_ppv(m, prev) * 100
        for i, k in enumerate(("PersLow", "PersNorm", "PersHigh")):
            assert abs(rec[i] - float(s[f"recall_{k}"])) < 0.01 and abs(ppv[i] - float(s[f"ppv_adjusted_{k}"])) < 0.01


def test_p3_verdict_follows_from_its_words():
    s = {r["regime"]: float(r["balanced_accuracy_mean"]) for r in _rows("classification_summary.csv")}
    a1, a2, a3 = s["R1_window_kfold"], s["R2_participant_grouped"], s["R3_time_blocked"]
    held = abs(a1 - 84.3) <= 3 and a1 - a2 > 15 and a1 - a3 > 15
    p3 = next(r for r in _rows("predictions.csv") if r["prediction"] == "P3")
    assert p3["verdict"] == ("held" if held else "failed") and p3["judged"]
    assert abs(a1 - 84.3) <= 10          # the stop rule did not trigger, so R2 and R3 were allowed to run
    assert all(r["verdict"] != "pending" for r in _rows("predictions.csv"))


def test_neighbour_shares_describe_the_splits():
    nb = {r["regime"]: r for r in _rows("classification_neighbours.csv")}
    assert float(nb["R1_window_kfold"]["share_within_5min"]) > 0.5
    assert int(nb["R2_participant_grouped"]["no_same_participant_training_window"]) == int(nb["R2_participant_grouped"]["test_windows"])
    assert float(nb["R3_time_blocked"]["share_within_24h"]) == 0.0      # the exclusion zones hold


def test_naive_claim_rows_match_the_model_and_baseline_runs():
    nv = {(r["regime"], r["naive"]): r for r in _rows("naive_claim.csv")}
    m = {(r["regime"], r["config"]): r for r in _rows("models_summary.csv")}
    b = {(r["regime"], r["baseline"]): r for r in _rows("baselines_summary.csv")}
    for (reg, name), r in nv.items():
        assert abs(float(r["model_rmse_mean"]) - float(m[(reg, "full_69")]["rmse_mean"])) < 2e-3
    assert abs(float(nv[("R1_lopo", "population_mean")]["naive_rmse_mean"]) - float(b[("R1_lopo", "B0_population_mean")]["rmse_mean"])) < 2e-3
    assert abs(float(nv[("R1_halves", "participant_mean")]["naive_rmse_mean"]) - float(b[("R1_halves", "B1_participant_mean")]["rmse_mean"])) < 2e-3
    assert nv[("R1_lopo", "population_mean")]["model_outperforms"] == "True" and nv[("R1_halves", "participant_mean")]["model_outperforms"] == "False"
