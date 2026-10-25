"""The 69 features on synthetic inputs with hand-computed answers (docs/features.md), and the
two mechanical guards of protocol §10: nothing at or after the target time enters a feature,
and no feature is derived from a CGM value.

Every expected number below was computed by hand before the test was run; a test that fails
is a bug in the implementation or in the hand count, never a reason to move a definition.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data.loader import Channel, SubjectRecord
from src.features.build import FEATURES, build_matrix, epoch_table
from src.features.epoch import activity_bouts, circadian, eda_peaks, hrv, rolling, summary_stats, wake_time
from src.features.food import eating_events, food_features


# ------------------------------------------------------------------ per-epoch statistics

def test_summary_stats_follow_pandas_conventions():
    rng = np.random.default_rng(0)
    x = rng.gamma(2.0, 1.0, size=1200)
    got = summary_stats(x)
    s = pd.Series(x)
    assert got["Mean"] == pytest.approx(s.mean())
    assert got["Std"] == pytest.approx(s.std())            # ddof = 1
    assert got["Min"] == s.min() and got["Max"] == s.max()
    assert got["Q1G"] == pytest.approx(s.quantile(0.25)) and got["Q3G"] == pytest.approx(s.quantile(0.75))
    assert got["Skew"] == pytest.approx(s.skew())          # adjusted Fisher-Pearson


def test_summary_stats_undefined_cases():
    assert all(np.isnan(v) for v in summary_stats(np.array([])).values())
    one = summary_stats(np.array([3.0]))
    assert one["Mean"] == 3.0 and np.isnan(one["Std"]) and np.isnan(one["Skew"])
    flat = summary_stats(np.array([2.0, 2.0, 2.0, 2.0]))
    assert flat["Std"] == 0.0 and np.isnan(flat["Skew"])


# ------------------------------------------------------------------ EDA peaks

def test_eda_peaks_counts_prominent_peaks_one_second_apart():
    # 4 Hz: three bumps of prominence 0.5 uS at 5 s spacing, two of 0.1 uS, and a doublet 2 samples apart
    x = np.full(200, 1.0)
    for c in (20, 40, 60):
        x[c] += 0.5
    for c in (80, 100):
        x[c] += 0.1                                     # below the 0.3 uS prominence
    x[120] += 0.6; x[122] += 0.6                         # 0.5 s apart: distance=4 keeps one
    assert eda_peaks(x) == 4
    assert eda_peaks(np.array([1.0, 2.0])) == 0


# ------------------------------------------------------------------ HRV

def test_hrv_hand_computed():
    got = hrv(np.array([0.8, 0.85, 0.8, 0.9]))           # ms: 800, 850, 800, 900; |diffs| 50, 50, 100
    assert got["maxHRV"] == 900 and got["minHRV"] == 800
    assert got["meanHRV"] == pytest.approx(837.5) and got["medianHRV"] == pytest.approx(825.0)
    assert got["SDNN"] == pytest.approx(np.sqrt(6875 / 3))          # ddof = 1
    assert got["NN50"] == 1                                         # strictly above 50 ms: only the 100
    assert got["pNN50"] == pytest.approx(100 / 3)                   # percent of 3 differences
    assert got["RMSSD"] == pytest.approx(np.sqrt((2500 + 2500 + 10000) / 3))


def test_hrv_needs_two_intervals():
    assert all(np.isnan(v) for v in hrv(np.array([0.8])).values())
    assert all(np.isnan(v) for v in hrv(np.array([])).values())


# ------------------------------------------------------------------ activity bouts, circadian

def test_activity_bouts_use_the_expanding_exclusive_mean():
    bouts = activity_bouts(np.array([1.0, 2.0, 3.0, 1.0]), np.array([60.0, 70.0, 80.0, 60.0]))
    # z=1: 2 > 1 and 70 > 60; z=2: 3 > 1.5 and 80 > 65; z=3: 1 > 2 fails; z=0: nothing prior
    assert bouts.tolist() == [0.0, 1.0, 1.0, 0.0]
    # a NaN epoch is not a bout and does not enter the running mean
    b = activity_bouts(np.array([1.0, np.nan, 5.0]), np.array([60.0, np.nan, 90.0]))
    assert b.tolist() == [0.0, 0.0, 1.0]


def test_circadian_as_crhythm_computes_it():
    minutes, hours = circadian(pd.DatetimeIndex(["2020-02-13 07:30:40", "2020-02-13 00:00:00", "2020-02-13 23:59:30"]))
    # 60*7 + 30 + round(40/60) = 451; 23:59:30: round(0.5) = 0 under round-half-to-even, as crhythm's Python round does
    assert minutes.tolist() == [451.0, 0.0, 1439.0]
    assert hours.tolist() == [8.0, 0.0, 24.0]                # round(451/60 = 7.52) = 8; round(23.98) = 24


# ------------------------------------------------------------------ rolling windows

def test_rolling_is_trailing_and_right_closed_over_irregular_times():
    idx = pd.DatetimeIndex(["2020-01-01 00:00", "2020-01-01 00:05", "2020-01-01 01:00", "2020-01-01 03:00"])
    s = pd.Series([1.0, 2.0, 3.0, 4.0], index=idx)
    assert rolling(s, "2h", "sum").tolist() == [1.0, 3.0, 6.0, 4.0]     # 03:00 window (01:00, 03:00] excludes 01:00
    assert rolling(s, "2h", "mean").tolist() == [1.0, 1.5, 2.0, 4.0]
    assert rolling(s, "2h", "max").tolist() == [1.0, 2.0, 3.0, 4.0]


# ------------------------------------------------------------------ food log

def _food_log():
    return pd.DataFrame({
        "date": ["2020-01-01"] * 4, "time": ["08:00:00", "08:00:00", "12:00:00", "20:00:00"],
        "time_begin": ["2020-01-01 08:00:00", "2020-01-01 08:00:00", "2020-01-01 12:00:00", "2020-01-01 20:00:00"],
        "time_end": [np.nan] * 4, "logged_food": ["eggs", "toast", "lunch", "dinner"], "amount": [2, 1, 1, 1], "unit": ["", "", "", ""],
        "searched_food": ["", "", "", ""], "calorie": [300.0, 100.0, 600.0, np.nan], "total_carb": [2.0, 20.0, 50.0, 30.0],
        "dietary_fiber": [np.nan] * 4, "sugar": [1.0, 2.0, 10.0, 5.0], "protein": [20.0, 3.0, 30.0, 25.0], "total_fat": [np.nan] * 4})


def test_eating_events_merge_rows_at_one_time_and_count_missing_nutrients():
    ev = eating_events(_food_log())
    assert len(ev) == 3 and ev.attrs["rows"] == 4 and ev.attrs["rows_missing_nutrient"] == 1
    assert ev.loc[0, "calorie"] == 400.0 and ev.loc[0, "total_carb"] == 22.0
    assert ev.loc[2, "calorie"] == 0.0                     # the missing calorie contributes 0


def test_food_features_hand_computed():
    ev = eating_events(_food_log())
    T = pd.DatetimeIndex(["2020-01-01 13:00:00", "2020-01-01 12:00:00", "2020-01-01 12:03:00", "2020-01-02 07:00:00"])
    f = food_features(ev, T)
    # 13:00: [11:00, 13:00) holds lunch; [05:00, 13:00) holds breakfast and lunch
    assert f.loc[T[0], "calories2hr"] == 600 and f.loc[T[0], "calories8hr"] == 1000 and f.loc[T[0], "carbs8hr"] == 72
    assert f.loc[T[0], "Eatcnt2hr"] == 1 and f.loc[T[0], "Eatcnt8hr"] == 2 and f.loc[T[0], "Eatcnt24hr"] == 2
    assert f.loc[T[0], "Eat"] == 0
    # exactly 12:00: lunch is not before T; breakfast is 4 h back
    assert f.loc[T[1], "calories2hr"] == 0 and f.loc[T[1], "Eatcnt2hr"] == 0 and f.loc[T[1], "Eat"] == 0
    # 12:03: the epoch [11:58, 12:03) contains lunch
    assert f.loc[T[2], "Eat"] == 1 and f.loc[T[2], "calories2hr"] == 600
    # next morning 07:00: [07:00 prev, 07:00) holds all three events (08:00 is inside, 24 h window is left-closed at 07:00)
    assert f.loc[T[3], "Eatcnt24hr"] == 3 and f.loc[T[3], "calories24hr"] == 1000 and f.loc[T[3], "sugar24hr"] == 18


# ------------------------------------------------------------------ wake time

def _sleep_wake_epochs(days=2, sleep=(23, 7)):
    t = pd.date_range("2020-01-01 00:00", periods=days * 288, freq="5min")
    asleep = np.array([(h >= sleep[0]) or (h < sleep[1]) for h in t.hour])
    hr_m = np.where(asleep, 55.0, 80.0); hr_s = np.where(asleep, 1.0, 6.0)
    acc_m = np.where(asleep, 0.98, 1.1); acc_s = np.where(asleep, 0.005, 0.1)
    return t, hr_m, hr_s, acc_m, acc_s


def test_wake_time_is_found_after_the_night_and_only_once_confirmed():
    t, hm, hs, am, as_ = _sleep_wake_epochs(days=3)
    w = wake_time(t, hm, hs, am, as_)
    # day 1 has no history: during its night the trailing means equal the sleeping values, nothing is
    # "below" them, the indicator never falls, and there is no rising edge -> nothing until day 2
    assert np.isnan(w[t < "2020-01-02 07:00"]).all()
    # day 2: the night sits below the trailing 24-h mean, the 3-h average rises from 07:00 -> the edge is
    # at 07:00 (420 min), confirmed 75 min later; the feature holds that value through the day
    i_conf = np.flatnonzero(t == "2020-01-02 08:15")[0]
    assert np.isnan(w[i_conf - 1]) and w[i_conf] == 420.0
    assert (w[(t >= "2020-01-02 08:15") & (t < "2020-01-03 08:15")] == 420.0).all()
    # day 3: before its own confirmation the feature still carries day 2's wake time
    i = np.flatnonzero(t == "2020-01-03 07:05")[0]
    assert w[i] == 420.0 and w[np.flatnonzero(t == "2020-01-03 08:15")[0]] == 420.0
    assert np.unique(w[~np.isnan(w)]).tolist() == [420.0]


def test_wake_time_accepts_series_with_a_positional_index():
    """The matrix builder passes DataFrame columns (RangeIndex); aligning them to the time index
    silently produced all-NaN input and no wake time on any participant (found on the first run)."""
    t, hm, hs, am, as_ = _sleep_wake_epochs(days=3)
    w_arrays = wake_time(t, hm, hs, am, as_)
    w_series = wake_time(t, pd.Series(hm), pd.Series(hs), pd.Series(am), pd.Series(as_))
    np.testing.assert_array_equal(w_arrays, w_series)
    assert np.nanmax(w_series) == 420.0


def test_wake_time_ignores_a_brief_night_waking():
    t, hm, hs, am, as_ = _sleep_wake_epochs(days=3)
    k = np.flatnonzero(t == "2020-01-02 03:00")[0]           # one awake epoch at 03:00 on night 2
    hm[k], hs[k], am[k], as_[k] = 80.0, 6.0, 1.1, 0.1
    w = wake_time(t, hm, hs, am, as_)
    assert np.unique(w[~np.isnan(w)]).tolist() == [420.0]


def test_wake_time_is_nan_without_a_confirmed_crossing():
    t = pd.date_range("2020-01-01 00:00", periods=100, freq="5min")
    w = wake_time(t, np.full(100, 70.0), np.full(100, 3.0), np.full(100, 1.0), np.full(100, 0.05))
    assert np.isnan(w).all()


# ------------------------------------------------------------------ the matrix and its guards

def _synthetic_record(seed=0, hours=30):
    rng = np.random.default_rng(seed)
    start = np.datetime64("2020-02-13T00:00:00")
    def ts(hz):
        n = int(hours * 3600 * hz)
        return start + (np.arange(n) * int(1e9 / hz)).astype("timedelta64[ns]")
    acc = Channel("ACC", ts(32), 1.0 + rng.normal(0, 0.05, (int(hours * 3600 * 32), 3)) / np.sqrt(3))
    eda = Channel("EDA", ts(4), 1.0 + np.abs(rng.normal(0, 0.2, int(hours * 3600 * 4))))
    temp = Channel("TEMP", ts(4), 33.0 + rng.normal(0, 0.1, int(hours * 3600 * 4)))
    hr = Channel("HR", ts(1), 70.0 + rng.normal(0, 3, int(hours * 3600)), derived=True)
    ibi_vals = rng.uniform(0.7, 1.0, int(hours * 3600 * 0.9))
    ibi_ts = start + np.cumsum(ibi_vals * 1e9 * 1.2).astype("timedelta64[ns]")
    ibi = Channel("IBI", ibi_ts, ibi_vals, derived=True)
    cgm_ts = start + np.timedelta64(30, "m") + (np.arange(int(hours * 12) - 6) * np.timedelta64(5, "m")).astype("timedelta64[ns]")
    cgm = Channel("Dexcom", cgm_ts, 100 + rng.normal(0, 15, len(cgm_ts)))
    bvp = Channel("BVP", ts(64), rng.normal(0, 50, int(hours * 3600 * 64)))
    food = _food_log()
    food["time_begin"] = pd.to_datetime(["2020-02-13 08:00:00", "2020-02-13 08:00:00", "2020-02-13 12:00:00", "2020-02-13 20:00:00"])
    return SubjectRecord("003", "FEMALE", 5.9, {"ACC": acc, "EDA": eda, "TEMP": temp, "HR": hr, "IBI": ibi, "Dexcom": cgm, "BVP": bvp}, food)


def test_matrix_has_the_69_features_and_the_target():
    df = build_matrix(_synthetic_record(), use_cache=False)
    assert list(df.columns[:3]) == ["participant", "t", "glucose"]
    assert [c for c in df.columns if c in FEATURES] == list(FEATURES) and len(FEATURES) == 69
    assert (df["ID"] == 3).all() and (df["Biological Sex"] == 0).all() and (df["HbA1c"] == 5.9).all()
    assert df["n_ACC"].min() > 0 and df[["EDA_Mean", "HR_Mean", "TEMP_Mean", "ACC_Mean"]].notna().all().all()
    assert df["Minfrommid"].iloc[0] == 30.0 and df["Hourfrommid"].iloc[0] == 0.0     # first target at 00:30 -> round(0.5) = 0


def test_no_sample_at_or_after_the_target_changes_a_feature():
    """Protocol §10: perturb every wearable sample and every CGM value from T onwards; row T is unchanged."""
    rec = _synthetic_record()
    base = build_matrix(rec, use_cache=False)
    k = len(base) // 2
    T = np.datetime64(base["t"].iloc[k])
    rng = np.random.default_rng(1)
    chans = {}
    for name, c in rec.channels.items():
        v = np.array(c.values, dtype=float, copy=True)
        m = c.ts >= T
        v[m] = v[m] * 3.0 + rng.normal(0, 10, m.sum() if v.ndim == 1 else (m.sum(), v.shape[1]))
        chans[name] = Channel(name, c.ts, v, derived=c.derived)
    food = rec.food_log.copy()
    food.loc[food["time_begin"] >= pd.Timestamp(T), ["calorie", "total_carb", "sugar", "protein"]] = 9999.0
    pert = build_matrix(SubjectRecord(rec.participant, rec.gender, rec.hba1c, chans, food), use_cache=False)
    a, b = base.iloc[k][FEATURES].astype(float), pert.iloc[k][FEATURES].astype(float)
    same = (a == b) | (a.isna() & b.isna())
    assert same.all(), f"features at T changed by samples at/after T: {list(a.index[~same])}"
    # and the previous row too (its epoch ends before T)
    a, b = base.iloc[k - 1][FEATURES].astype(float), pert.iloc[k - 1][FEATURES].astype(float)
    assert ((a == b) | (a.isna() & b.isna())).all()


def test_no_feature_depends_on_the_cgm_value():
    rec = _synthetic_record()
    base = build_matrix(rec, use_cache=False)
    c = rec.channels["Dexcom"]
    chans = dict(rec.channels); chans["Dexcom"] = Channel("Dexcom", c.ts, c.values + 200.0)
    shifted = build_matrix(SubjectRecord(rec.participant, rec.gender, rec.hba1c, chans, rec.food_log), use_cache=False)
    pd.testing.assert_frame_equal(base[FEATURES], shifted[FEATURES])
    assert (shifted["glucose"] - base["glucose"]).round(6).eq(200.0).all()


def test_unusable_epochs_are_those_with_an_empty_required_channel():
    rec = _synthetic_record(hours=6)
    tab = epoch_table(rec)
    assert tab["usable"].all()
    # remove all EDA samples in the epoch before the 10th reading
    T = np.datetime64(tab["t"].iloc[9]); e = rec.channels["EDA"]
    keep = ~((e.ts >= T - np.timedelta64(5, "m")) & (e.ts < T))
    chans = dict(rec.channels); chans["EDA"] = Channel("EDA", e.ts[keep], e.values[keep])
    tab2 = epoch_table(SubjectRecord("003", "FEMALE", 5.9, chans, rec.food_log))
    assert not tab2["usable"].iloc[9] and tab2["usable"].drop(index=9).all()
    df = build_matrix(SubjectRecord("003", "FEMALE", 5.9, chans, rec.food_log), use_cache=False)
    assert len(df) == len(tab) - 1
