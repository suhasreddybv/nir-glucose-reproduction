"""Labels, splits and baselines on synthetic data: hand counts, and the §10 guard that no
baseline reads a test-portion glucose value."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.eval.baselines import b0, b1, b2, b3, bootstrap_mean, metrics
from src.features.build import E4_FEATURES
from src.labels import balanced_set, pers_labels
from src.splits import halves, lopo, time_blocked


# ------------------------------------------------------------------ labels

def test_pers_labels_hand_computed():
    t = pd.date_range("2020-01-01 00:00", periods=16, freq="5min")
    g = np.array([100.0] * 11 + [120.0, 100.0, 100.0, 60.0, 100.0])
    lab = pers_labels(t.to_numpy(), g)
    assert lab["label"].iloc[:11].isna().all()                 # fewer than 12 readings
    # reading 12 (index 11): window = all 12, mean 101.67, sd 5.77 -> 120 > 107.4 -> PersHigh
    assert lab["label"].iloc[11] == "PersHigh"
    assert lab["label"].iloc[12] == "PersNorm" and lab["label"].iloc[13] == "PersNorm"
    assert lab["label"].iloc[14] == "PersLow"                   # 60 far below mean - sd
    assert lab["roll_mean"].iloc[11] == pytest.approx(101.6667, abs=1e-3)


def test_pers_labels_window_is_24h_trailing():
    t = pd.date_range("2020-01-01 00:00", periods=600, freq="5min")     # 50 h
    g = np.r_[np.full(300, 200.0), np.full(300, 100.0)]                # a step down at 25 h
    lab = pers_labels(t.to_numpy(), g)
    # just after the step the 24-h window still holds the 200s: 100 is PersLow
    assert lab["label"].iloc[300] == "PersLow"
    # 24 h after the step the window holds only 100s: sd 0 -> PersNorm
    assert lab["label"].iloc[-1] == "PersNorm" and lab["roll_sd"].iloc[-1] == 0.0


def test_balanced_set_undersamples_to_the_smallest_class_reproducibly():
    df = pd.DataFrame({"label": ["PersNorm"] * 50 + ["PersHigh"] * 7 + ["PersLow"] * 12 + [None] * 5, "x": range(74)})
    b = balanced_set(df, seed=0)
    assert b["label"].value_counts().to_dict() == {"PersNorm": 7, "PersHigh": 7, "PersLow": 7}
    assert set(b.index) <= set(df.index) and b["label"].notna().all()
    pd.testing.assert_frame_equal(b, balanced_set(df, seed=0))
    assert not b.index.equals(balanced_set(df, seed=1).index)


# ------------------------------------------------------------------ splits

def _matrix(n_per=100, pids=("001", "002", "003"), seed=0):
    rng = np.random.default_rng(seed)
    frames = []
    for i, pid in enumerate(pids):
        t = pd.date_range("2020-01-01", periods=n_per, freq="5min") + pd.Timedelta(days=10 * i)
        d = pd.DataFrame({"participant": pid, "t": t, "glucose": 100 + 10 * i + rng.normal(0, 10, n_per),
                          "HbA1c": 5.5 + 0.2 * i, "Biological Sex": float(i % 2)})
        for f in E4_FEATURES:
            d[f] = rng.normal(0, 1, n_per)
        frames.append(d)
    return pd.concat(frames, ignore_index=True).sample(frac=1, random_state=1).reset_index(drop=True)   # shuffled rows


def test_halves_split_by_count_in_time_order():
    df = _matrix(n_per=101)
    tr, te = halves(df)
    for pid, g in df.groupby("participant"):
        assert tr[g.index].sum() == 50 and te[g.index].sum() == 51
        assert g.loc[tr[g.index], "t"].max() < g.loc[te[g.index], "t"].min()


def test_time_blocked_leaves_a_24h_zone_on_both_sides():
    df = _matrix(n_per=1000)                                    # 1000 epochs = 83 h per participant
    tr, te = time_blocked(df)
    assert not (tr & te).any()
    for pid, g in df.groupby("participant"):
        boundary = g.sort_values("t")["t"].iloc[700]
        assert g.loc[tr[g.index], "t"].max() < boundary - pd.Timedelta(hours=24)
        assert g.loc[te[g.index], "t"].min() >= boundary + pd.Timedelta(hours=24)
        zone = g.index[~tr[g.index] & ~te[g.index]]
        assert len(zone) == 24 * 12 * 2                       # 48 h of 5-min epochs excluded


def test_lopo_holds_out_exactly_one_participant():
    df = _matrix()
    folds = list(lopo(df))
    assert [p for p, _, _ in folds] == ["001", "002", "003"]
    for pid, tr, te in folds:
        assert set(df.loc[te, "participant"]) == {pid} and pid not in set(df.loc[tr, "participant"])


# ------------------------------------------------------------------ baselines

def test_b1_is_the_training_mean_and_b0_the_pooled_mean():
    df = _matrix()
    tr, te = halves(df)
    p1 = b1(df[tr], df[te])
    for pid in ("001", "002", "003"):
        sel = (df[te]["participant"] == pid).to_numpy()
        assert np.allclose(p1[sel], df[tr & (df["participant"] == pid)]["glucose"].mean())
    assert np.allclose(b0(df[tr], df[te]), df[tr]["glucose"].mean())


def test_b3_predicts_only_rows_with_all_e4_features():
    df = _matrix(n_per=300)
    df.loc[df.index[:20], "SDNN"] = np.nan
    tr, te = halves(df)
    p, m = b3(df[tr], df[te])
    assert m.sum() == len(df[te]) - df[te]["SDNN"].isna().sum() and np.isnan(p[~m]).all()


def test_no_baseline_reads_a_test_glucose():
    """Protocol §10 / the brief's stop condition: perturb every test-portion glucose; no prediction moves."""
    df = _matrix(n_per=300)
    for tr, te in (halves(df), time_blocked(df, train_frac=0.5, gap=pd.Timedelta(hours=1))):
        train, test = df[tr], df[te]
        pert = test.copy(); pert["glucose"] = pert["glucose"] * 3 + 500
        for fn in (b0, b1, b2):
            np.testing.assert_array_equal(fn(train, test), fn(train, pert))
        p, m = b3(train, test); q, mq = b3(train, pert)
        np.testing.assert_array_equal(m, mq); np.testing.assert_allclose(p[m], q[mq])
    for _, tr, te in lopo(df):
        train, test = df[tr], df[te]
        pert = test.copy(); pert["glucose"] += 999
        np.testing.assert_array_equal(b0(train, test), b0(train, pert)); np.testing.assert_array_equal(b2(train, test), b2(train, pert))


def test_metrics_hand_computed():
    m = metrics(np.array([100.0, 200.0]), np.array([110.0, 180.0]))
    assert m["rmse"] == pytest.approx(np.sqrt((100 + 400) / 2), abs=1e-3)
    assert m["mape"] == pytest.approx((10 + 10) / 2, abs=1e-3) and m["accuracy"] == pytest.approx(90.0, abs=1e-3)
    assert m["clarke_AB_pct"] == 100.0 and m["mard_pct"] == pytest.approx(10.0, abs=1e-3)


def test_bootstrap_mean_brackets_the_mean_and_is_seeded():
    v = np.arange(16, dtype=float)
    lo, hi = bootstrap_mean(v)
    assert lo < v.mean() < hi and (lo, hi) == bootstrap_mean(v)
