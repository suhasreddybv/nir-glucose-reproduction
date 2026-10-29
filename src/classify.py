"""The paper's classification (protocol cells 1, 4, 5; §9 R1-R3) as functions.

Decision tree (scikit-learn defaults, `random_state = 0`) after recursive feature elimination
to the 20 most important features **inside each training fold**, with a decision tree as the
RFE estimator - the estimator the paper reports winning its comparison of five (cell 4). The
same pipeline (RFE-20 by a decision tree, then the classifier) is used for the 70/30 decision
tree and the 70/30 logistic regression, which the paper does not describe separately (D-015,
decided before the run). Logistic regression: scikit-learn defaults with `max_iter = 1000`,
unscaled, as cell 7 i froze it.

Metrics as the paper's Methods name them (scikit-learn): balanced accuracy, weighted
precision, weighted recall, weighted F1, and R^2 on the class codes PersLow 0, PersNorm 1,
PersHigh 2, thresholded at zero (Table 2's footnote). Beside them, per regime: the pooled
confusion matrix, per-class recall ("class accuracy", Fig. 4), and the prevalence-adjusted
positive predictive value per class - the PPV the classifier would have on the unbalanced
stream, from its per-class recall matrix and the true class prevalence of the complete
labelled epochs.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_selection import RFE
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score, precision_score, r2_score, recall_score
from sklearn.tree import DecisionTreeClassifier

from src.labels import LABELS

CODE = {lab: i for i, lab in enumerate(LABELS)}          # PersLow 0, PersNorm 1, PersHigh 2
N_SELECT = 20


def make_classifier(kind: str):
    if kind == "tree":
        return DecisionTreeClassifier(random_state=0)
    if kind == "logistic":
        return LogisticRegression(max_iter=1000)
    raise ValueError(kind)


def fit_predict(X_tr: np.ndarray, y_tr: np.ndarray, X_te: np.ndarray, kind: str = "tree") -> tuple[np.ndarray, np.ndarray]:
    """RFE-20 with a decision tree on the training rows, then the classifier on the kept columns.
    Returns predictions and the boolean mask of kept features. Reads no test label."""
    rfe = RFE(DecisionTreeClassifier(random_state=0), n_features_to_select=N_SELECT, step=1).fit(X_tr, y_tr)
    keep = rfe.support_
    clf = make_classifier(kind)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        clf.fit(X_tr[:, keep], y_tr)
    return clf.predict(X_te[:, keep]), keep


def scores(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return dict(n=int(len(y_true)),
                balanced_accuracy=float(balanced_accuracy_score(y_true, y_pred)),
                precision_weighted=float(precision_score(y_true, y_pred, average="weighted", zero_division=0)),
                recall_weighted=float(recall_score(y_true, y_pred, average="weighted", zero_division=0)),
                f1_weighted=float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
                r2=float(max(0.0, r2_score(y_true, y_pred))))


def confusion(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    """Rows true class, columns predicted, in the order of LABELS."""
    return confusion_matrix(y_true, y_pred, labels=[0, 1, 2])


def per_class_recall(cm: np.ndarray) -> np.ndarray:
    return cm.diagonal() / cm.sum(axis=1)


def prevalence_adjusted_ppv(cm: np.ndarray, prevalence: np.ndarray) -> np.ndarray:
    """PPV of each predicted class if the classifier, with this confusion matrix's per-class
    rates, ran on a stream with the given true-class prevalence:
    PPV_k = P(pred k | true k) pi_k / sum_j P(pred k | true j) pi_j."""
    rates = cm / cm.sum(axis=1, keepdims=True)            # row-normalised: P(pred | true)
    num = rates.diagonal() * prevalence
    den = (rates * prevalence[:, None]).sum(axis=0)
    return num / den
