"""Pure functions for the per-epoch and rolling wearable features (protocol cell 7, `docs/features.md`).

Every function takes arrays or Series and returns numbers or Series; nothing here reads a
file or touches a CGM value. The epoch is [T - 5 min, T) for a target reading at T; rolling
windows over epochs are trailing, (T - W, T], by the epoch's end time.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

EPOCH = pd.Timedelta(minutes=5)
STATS = ("Mean", "Std", "Min", "Max", "Q1G", "Q3G", "Skew")
HRV_NAMES = ("maxHRV", "minHRV", "medianHRV", "meanHRV", "SDNN", "NN50", "pNN50", "RMSSD")

# EDA peak detection as the first author's wearablecompute.PeaksEDA calls it: raw signal,
# distance 4 samples (1 s at 4 Hz), prominence 0.3 uS, height 0 (cell 7 f).
EDA_PEAK_KWARGS = dict(height=0, distance=4, prominence=0.3)


def summary_stats(x: np.ndarray) -> dict[str, float]:
    """The seven statistics of Supplementary Table 1 on one channel's epoch samples, in the
    pandas conventions of cell 7 k: std ddof = 1, adjusted Fisher-Pearson skew, linear quantiles.
    NaN where undefined (std needs 2 samples, skew 3 and a non-zero spread)."""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n == 0:
        return {s: np.nan for s in STATS}
    mu = float(x.mean())
    out = {"Mean": mu, "Min": float(x.min()), "Max": float(x.max()),
           "Q1G": float(np.quantile(x, 0.25)), "Q3G": float(np.quantile(x, 0.75))}
    out["Std"] = float(x.std(ddof=1)) if n > 1 else np.nan
    if n > 2:
        d = x - mu
        m2 = float((d ** 2).mean()); m3 = float((d ** 3).mean())
        out["Skew"] = float(np.sqrt(n * (n - 1)) / (n - 2) * m3 / m2 ** 1.5) if m2 > 0 else np.nan
    else:
        out["Skew"] = np.nan
    return out


def eda_peaks(eda: np.ndarray) -> int:
    """PeakEDA: the number of find_peaks peaks in the epoch's raw EDA samples."""
    eda = np.asarray(eda, dtype=float)
    if len(eda) < 3:
        return 0
    peaks, _ = find_peaks(eda, **EDA_PEAK_KWARGS)
    return int(len(peaks))


def hrv(ibi_s: np.ndarray) -> dict[str, float]:
    """The eight HRV metrics on the epoch's IBI values (seconds in the file, milliseconds here),
    as wearablecompute defines them: statistics of the raw intervals; SDNN ddof = 1; NN50 the
    count of successive absolute differences strictly above 50 ms; pNN50 in percent of the
    differences; RMSSD the root mean square of the successive differences. No gap check and no
    smoothing (cell 7 f). NaN throughout when fewer than 2 intervals."""
    ibi = np.asarray(ibi_s, dtype=float) * 1000.0
    ibi = ibi[~np.isnan(ibi)]
    if len(ibi) < 2:
        return {k: np.nan for k in HRV_NAMES}
    d = np.abs(np.diff(ibi))
    nn50 = int((d > 50).sum())
    return {"maxHRV": float(ibi.max()), "minHRV": float(ibi.min()), "medianHRV": float(np.median(ibi)),
            "meanHRV": float(ibi.mean()), "SDNN": float(ibi.std(ddof=1)), "NN50": float(nn50),
            "pNN50": float(nn50 / len(d) * 100.0), "RMSSD": float(np.sqrt((d ** 2).mean()))}


def activity_bouts(acc_mean: np.ndarray, hr_mean: np.ndarray) -> np.ndarray:
    """wearablecompute.exercisepts: epoch z is a bout when its ACC_Mean exceeds the mean of all
    earlier epochs' ACC_Mean and its HR_Mean exceeds the mean of all earlier epochs' HR_Mean
    (expanding, exclusive). The first epoch is never a bout; a NaN epoch is not a bout and
    does not enter the running mean."""
    a = pd.Series(np.asarray(acc_mean, dtype=float)); h = pd.Series(np.asarray(hr_mean, dtype=float))
    prior_a = a.expanding().mean().shift(1); prior_h = h.expanding().mean().shift(1)
    bout = (a > prior_a) & (h > prior_h)
    return bout.to_numpy(dtype=float)


def circadian(t: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray]:
    """Minfrommid and Hourfrommid as wearablecompute.crhythm computes them: minutes = 60 h + m
    + round(s / 60); hours = round(minutes / 60), an integer."""
    t = pd.DatetimeIndex(t)
    minutes = t.hour.to_numpy() * 60 + t.minute.to_numpy() + np.round(t.second.to_numpy() / 60).astype(int)
    hours = np.round(minutes / 60).astype(int)
    return minutes.astype(float), hours.astype(float)


def rolling(s: pd.Series, window: str, how: str) -> pd.Series:
    """Trailing time-based window (t - W, t] over an irregular, time-indexed Series; NaN-skipping.
    `how` in {sum, mean, max}. A window with no non-NaN value gives NaN (sum gives 0 only when
    the window has rows; pandas' sum over an all-NaN window is 0, which is the paper's own
    behaviour for a food sum with nothing logged)."""
    r = s.rolling(window, closed="right", min_periods=1)
    return getattr(r, how)()


def wake_time(t: pd.DatetimeIndex, hr_mean, hr_std, acc_mean, acc_std) -> np.ndarray:
    """WakeTime under protocol cell 7 h, online and historical.

    An epoch is sleep-like when at least two of HR_Mean, HR_Std, ACC_Mean, ACC_Std are below
    their own trailing 24-h mean; the awake indicator (1 - sleep-like) is averaged over a
    trailing 3-h window. A calendar day's wake candidate is the first rising edge of that
    average in the day - an epoch whose first difference is positive after a non-positive one
    (the paper's "slope sharply changed"); it is kept only if the average at the first epochs
    at or after +25 min and +75 min is higher than at the candidate ("remained consistently
    higher 25 and 75 min after"). A brief night waking makes an edge but fails the check,
    because the 3-h average does not keep rising. The feature at epoch T is the
    most recent kept wake time whose +75-min confirmation epoch is at or before T, in minutes
    from midnight; NaN before the first confirmation. Nothing after T is read.
    """
    t = pd.DatetimeIndex(t)
    # arrays, not Series: a Series with its own index would be aligned to `t` and turn into NaN
    frame = pd.DataFrame({"hm": np.asarray(hr_mean, dtype=float), "hs": np.asarray(hr_std, dtype=float),
                          "am": np.asarray(acc_mean, dtype=float), "as": np.asarray(acc_std, dtype=float)}, index=t)
    trailing = frame.rolling("24h", closed="right", min_periods=1).mean()
    points = (frame < trailing).sum(axis=1)                     # a NaN quantity scores no point
    awake = (points < 2).astype(float)
    awake3h = awake.rolling("3h", closed="right", min_periods=1).mean().to_numpy()
    tt = t.to_numpy()
    n = len(tt)
    confirmed_at = np.full(n, np.datetime64("NaT", "ns"), dtype="datetime64[ns]")   # when each candidate is confirmed
    slope = np.diff(awake3h, prepend=np.nan)
    wake_min = np.full(n, np.nan)
    day = t.normalize().to_numpy()
    seen_day = set()
    for i in range(1, n):
        if day[i] in seen_day:
            continue
        if not (slope[i] > 0 and slope[i - 1] <= 0):          # a rising edge
            continue
        j25 = np.searchsorted(tt, tt[i] + np.timedelta64(25, "m"))
        j75 = np.searchsorted(tt, tt[i] + np.timedelta64(75, "m"))
        if j75 >= n:
            continue                                          # not confirmable within the record
        # the confirmation epochs must exist near their nominal offsets (within one epoch)
        if tt[j25] - tt[i] > np.timedelta64(30, "m") or tt[j75] - tt[i] > np.timedelta64(80, "m"):
            continue
        if awake3h[j25] > awake3h[i] and awake3h[j75] > awake3h[i]:
            seen_day.add(day[i])
            confirmed_at[i] = tt[j75]
            wake_min[i] = t[i].hour * 60 + t[i].minute + round(t[i].second / 60)
    # feature: the most recent confirmed wake time at each epoch
    out = np.full(n, np.nan)
    cand = np.flatnonzero(~np.isnat(confirmed_at))
    if len(cand):
        order = cand[np.argsort(confirmed_at[cand])]
        conf_times = confirmed_at[order]
        k = np.searchsorted(conf_times, tt, side="right") - 1    # last candidate confirmed by tt
        ok = k >= 0
        out[ok] = wake_min[order[k[ok]]]
    return out
