"""The paper's regression model (protocol cell 4) under the regimes of §9, with the ablations.

XGBoost regressor, max depth 6, 100 estimators, learning rate 0.1 (Methods "Glucose
prediction"), `random_state = 0`. Feature selection inside each training fold: a random-forest
regressor of 1,000 trees (`random_state = 0`) on the training rows with every feature present,
keeping features whose impurity importance is at least 0.005 (the paper's cutoff; the DBDP
`loocvRF.py` applies the same rule on the training fold only). The selection is repeated per
personalised model on that participant's training rows (the paper states it per LOPO fold and
is silent for the personalised model; the same rule is applied, D-013). XGBoost takes NaN
natively, so the model is evaluated on every usable test row.

Ablations (protocol §9, `docs/features.md` groupings): the two clock features stay in every set.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

from src.features.build import CLOCK_FEATURES, E4_FEATURES, FEATURES, FOOD_FEATURES, USER_MODEL_FEATURES

XGB = dict(max_depth=6, n_estimators=100, learning_rate=0.1, random_state=0, n_jobs=4)
RF_TREES = 1000
IMPORTANCE_CUTOFF = 0.005

ABLATIONS = {
    "full_69": list(FEATURES),
    "minus_food": [f for f in FEATURES if f not in FOOD_FEATURES],
    "minus_user_model": [f for f in FEATURES if f not in USER_MODEL_FEATURES],
    "minus_e4": [f for f in FEATURES if f not in E4_FEATURES],
    "e4_only": list(E4_FEATURES) + list(CLOCK_FEATURES),
    "food_only": list(FOOD_FEATURES) + list(CLOCK_FEATURES),
}
assert {len(v) for v in ABLATIONS.values()} == {69, 50, 66, 24, 47, 21}


def select_features(train: pd.DataFrame, cols: list[str], n_trees: int = RF_TREES, cutoff: float = IMPORTANCE_CUTOFF, n_jobs: int = -1) -> tuple[list[str], pd.Series]:
    """Features with RF impurity importance >= cutoff on the training rows (rows with any NaN
    among `cols` dropped for the forest, as the forest needs complete rows)."""
    tr = train.dropna(subset=cols)
    rf = RandomForestRegressor(n_estimators=n_trees, random_state=0, n_jobs=n_jobs)
    rf.fit(tr[cols].to_numpy(float), tr["glucose"].to_numpy(float))
    imp = pd.Series(rf.feature_importances_, index=cols)
    kept = [c for c in cols if imp[c] >= cutoff]
    return (kept if kept else list(cols)), imp


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, cols: list[str], select: bool = True) -> tuple[np.ndarray, list[str], pd.Series]:
    """Train on `train`, predict `test`. Reads the test rows' features only."""
    kept, imp = select_features(train, cols) if select else (list(cols), pd.Series(np.nan, index=cols))
    m = XGBRegressor(**XGB).fit(train[kept].to_numpy(float), train["glucose"].to_numpy(float))
    return m.predict(test[kept].to_numpy(float)).astype(float), kept, imp
