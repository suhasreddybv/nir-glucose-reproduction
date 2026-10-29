"""The classification pipeline on synthetic data: hand-computed prevalence-adjusted PPV, the
R^2 threshold, in-fold RFE reading no test label, and grouped folds that never split a participant."""
from __future__ import annotations

import numpy as np
import pytest
from sklearn.model_selection import StratifiedGroupKFold

from src.classify import N_SELECT, confusion, fit_predict, per_class_recall, prevalence_adjusted_ppv, scores


def test_prevalence_adjusted_ppv_hand_computed():
    # balanced test set, 100 per class; recall 0.8 for each class, errors split evenly
    cm = np.array([[80, 10, 10], [10, 80, 10], [10, 10, 80]])
    assert per_class_recall(cm).tolist() == [0.8, 0.8, 0.8]
    assert prevalence_adjusted_ppv(cm, np.array([1 / 3] * 3)) == pytest.approx([0.8, 0.8, 0.8])
    # on a stream that is 70 % PersNorm: PPV_low = 0.8*0.15 / (0.8*0.15 + 0.1*0.7 + 0.1*0.15) = 0.12 / 0.205
    ppv = prevalence_adjusted_ppv(cm, np.array([0.15, 0.70, 0.15]))
    assert ppv[0] == pytest.approx(0.12 / 0.205) and ppv[2] == pytest.approx(0.12 / 0.205)
    assert ppv[1] == pytest.approx(0.56 / (0.015 + 0.56 + 0.015))


def test_scores_threshold_r2_at_zero_and_name_the_paper_metrics():
    y = np.array([0, 1, 2, 0, 1, 2]); p = np.array([2, 1, 0, 2, 1, 0])
    s = scores(y, p)
    assert s["r2"] == 0.0 and s["balanced_accuracy"] == pytest.approx(1 / 3)
    assert set(s) == {"n", "balanced_accuracy", "precision_weighted", "recall_weighted", "f1_weighted", "r2"}
    assert confusion(y, p).sum() == 6


def test_fit_predict_selects_20_and_reads_no_test_label():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(600, 30)); y = (X[:, 0] > 0.5).astype(int) + (X[:, 0] > -0.5).astype(int)
    tr, te = np.arange(400), np.arange(400, 600)
    pred, keep = fit_predict(X[tr], y[tr], X[te])
    assert keep.sum() == N_SELECT and keep[0]
    assert scores(y[te], pred)["balanced_accuracy"] > 0.8
    pred2, keep2 = fit_predict(X[tr], y[tr], X[te].copy())
    np.testing.assert_array_equal(pred, pred2); np.testing.assert_array_equal(keep, keep2)


def test_grouped_folds_never_split_a_participant():
    rng = np.random.default_rng(1)
    groups = np.repeat(np.arange(16), 50); y = rng.integers(0, 3, len(groups)); X = rng.normal(size=(len(y), 3))
    for tr, te in StratifiedGroupKFold(n_splits=10, shuffle=True, random_state=0).split(X, y, groups):
        assert not set(groups[tr]) & set(groups[te])
