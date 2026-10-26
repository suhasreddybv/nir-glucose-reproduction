"""The model wrapper on synthetic data: ablation sets, in-fold selection, and the guard that
neither selection nor prediction reads a test-portion glucose."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.build import CLOCK_FEATURES, FEATURES
from src.models import ABLATIONS, fit_predict, select_features
from src.splits import halves
from tests.test_baselines import _matrix


def test_ablation_sets():
    assert {k: len(v) for k, v in ABLATIONS.items()} == {"full_69": 69, "minus_food": 50, "minus_user_model": 66, "minus_e4": 24, "e4_only": 47, "food_only": 21}
    for v in ABLATIONS.values():
        assert set(CLOCK_FEATURES) <= set(v) and set(v) <= set(FEATURES)
    assert "ID" not in ABLATIONS["minus_user_model"] and "calories2hr" not in ABLATIONS["minus_food"] and "SDNN" not in ABLATIONS["minus_e4"]


def _full_matrix(n_per=200):
    df = _matrix(n_per=n_per)
    rng = np.random.default_rng(3)
    for f in FEATURES:
        if f not in df.columns:
            df[f] = rng.normal(0, 1, len(df))
    df["ID"] = df["participant"].astype(int).astype(float)
    df["glucose"] = df["glucose"] + 20 * df["HR_Mean"]          # one feature carries signal
    return df


def test_selection_keeps_the_informative_feature_and_uses_training_rows_only():
    df = _full_matrix()
    tr, te = halves(df)
    kept, imp = select_features(df[tr], list(FEATURES), n_trees=50)
    assert "HR_Mean" in kept and imp["HR_Mean"] > 0.3
    pert = df.copy(); pert.loc[te, "glucose"] += 1000
    kept2, imp2 = select_features(pert[tr], list(FEATURES), n_trees=50)
    assert kept == kept2 and imp.equals(imp2)


def test_no_prediction_reads_a_test_glucose():
    df = _full_matrix(n_per=120)
    tr, te = halves(df)
    train, test = df[tr], df[te]
    p, kept, _ = fit_predict(train, test, ABLATIONS["minus_food"], select=False)
    pert = test.copy(); pert["glucose"] = pert["glucose"] * 2 + 300
    q, kept2, _ = fit_predict(train, pert, ABLATIONS["minus_food"], select=False)
    np.testing.assert_allclose(p, q); assert kept == kept2 == ABLATIONS["minus_food"]
    assert len(p) == len(test) and np.isfinite(p).all()


def test_model_handles_nan_features_natively():
    df = _full_matrix(n_per=120)
    df.loc[df.index[::7], "SDNN"] = np.nan
    tr, te = halves(df)
    p, kept, _ = fit_predict(df[tr], df[te], ["HR_Mean", "SDNN", "Minfrommid"], select=False)
    assert np.isfinite(p).all() and len(p) == te.sum()
