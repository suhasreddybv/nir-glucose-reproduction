"""The per-epoch feature matrix for one participant, and the report over all sixteen.

For every Dexcom reading at time T the epoch is [T - 5 min, T). An epoch is usable when ACC,
EDA, TEMP and HR each have at least one sample in it (protocol cell 7 b); the 69 features of
`docs/features.md` are computed on the usable epochs only, the rolling features over the
participant's usable epochs by time. The matrix carries the target (`glucose`, the reading
itself), `t` (the reading's time) and `participant`, and is cached as parquet outside the
tree at `~/.cache/nir-glucose-reproduction/features/<pid>.parquet` (D-002).

Nothing here reads a sample at or after T, and no feature is derived from a CGM value: the
test `tests/test_features.py::test_no_sample_at_or_after_the_target_changes_a_feature`
perturbs everything from T onwards and asserts the row is unchanged.

`python -m src.features.build` builds all sixteen and writes results/epochs.csv (usable
epochs per participant against the Day 0 count and the paper's ~25,000) and
results/feature_missingness.csv (share of NaN per feature).
"""
from __future__ import annotations

import csv
import sys

import numpy as np
import pandas as pd

from src.data.loader import CACHE_DIR, PARTICIPANTS, REPO_ROOT, load_participant
from src.features.epoch import (EPOCH, HRV_NAMES, STATS, activity_bouts, circadian, eda_peaks, hrv, rolling,
                                summary_stats, wake_time)
from src.features.food import eating_events, food_features

VERSION = "2026-10-25a"      # bump when any feature definition changes; the cache is keyed on it
CHANNELS_REQUIRED = ("ACC", "EDA", "TEMP", "HR")

FEATURES = (
    ["Biological Sex", "HbA1c"]
    + [f"{ch}_{s}" for ch in ("EDA", "HR", "TEMP", "ACC") for s in STATS]
    + ["PeakEDA", "PeakEDA2hr_sum", "PeakEDA2hr_mean"]
    + list(HRV_NAMES)
    + [f"{k}{w}" for w in ("2hr", "8hr", "24hr") for k in ("calories", "protein", "sugar", "carbs")]
    + ["Eat", "Eatcnt2hr", "Eatcnt8hr", "Eatcnt24hr", "Eatmean2hr", "Eatmean8hr", "Eatmean24hr"]
    + ["WakeTime", "Minfrommid", "Hourfrommid", "ACC_mean_2hrs", "ACC_max_2hrs", "Activity_bouts", "Activity24", "Activity1hr"]
    + ["ID"]
)
assert len(FEATURES) == 69, len(FEATURES)

E4_FEATURES = tuple(f for f in FEATURES if f.startswith(("EDA_", "HR_", "TEMP_", "ACC_", "PeakEDA")) or f in HRV_NAMES
                    or f in ("WakeTime", "Activity_bouts", "Activity24", "Activity1hr"))
FOOD_FEATURES = tuple(f for f in FEATURES if f.startswith(("calories", "protein", "sugar", "carbs", "Eat")))
USER_MODEL_FEATURES = ("Biological Sex", "HbA1c", "ID")
CLOCK_FEATURES = ("Minfrommid", "Hourfrommid")
assert len(E4_FEATURES) == 45 and len(FOOD_FEATURES) == 19, (len(E4_FEATURES), len(FOOD_FEATURES))
assert set(E4_FEATURES) | set(FOOD_FEATURES) | set(USER_MODEL_FEATURES) | set(CLOCK_FEATURES) == set(FEATURES)


def _slice(ts: np.ndarray, values: np.ndarray, t0: np.datetime64, t1: np.datetime64) -> np.ndarray:
    """Samples with t0 <= ts < t1 (ts sorted)."""
    i, j = np.searchsorted(ts, t0, side="left"), np.searchsorted(ts, t1, side="left")
    return values[i:j]


def epoch_table(rec) -> pd.DataFrame:
    """One row per Dexcom reading: the per-epoch statistics, PeakEDA, the HRV metrics, the
    sample counts per channel and `usable`. Rolling features are added by `build_matrix`."""
    cgm = rec.channels["Dexcom"]
    targets = cgm.ts.astype("datetime64[ns]")
    acc_ts = rec.channels["ACC"].ts.astype("datetime64[ns]")
    acc_mag = np.linalg.norm(rec.channels["ACC"].values, axis=1) if rec.channels["ACC"].values.ndim == 2 else rec.channels["ACC"].values
    series = {"ACC": (acc_ts, acc_mag)}
    for ch in ("EDA", "TEMP", "HR", "IBI"):
        c = rec.channels[ch]
        series[ch] = (c.ts.astype("datetime64[ns]"), np.asarray(c.values, dtype=float))
    rows = []
    e = EPOCH.to_timedelta64()
    for T, g in zip(targets, cgm.values):
        t0 = T - e
        row = {"t": T, "glucose": float(g)}
        for ch in ("EDA", "HR", "TEMP", "ACC"):
            x = _slice(*series[ch], t0, T)
            row[f"n_{ch}"] = len(x)
            for s, v in summary_stats(x).items():
                row[f"{ch}_{s}"] = v
        eda = _slice(*series["EDA"], t0, T)
        row["PeakEDA"] = float(eda_peaks(eda)) if len(eda) else np.nan
        ibi = _slice(*series["IBI"], t0, T)
        row["n_IBI"] = len(ibi)
        row.update(hrv(ibi))
        rows.append(row)
    df = pd.DataFrame(rows)
    df["usable"] = (df[[f"n_{c}" for c in CHANNELS_REQUIRED]] > 0).all(axis=1)
    return df


def build_matrix(rec, use_cache: bool = True) -> pd.DataFrame:
    """The 69 features plus t, glucose, participant and the per-channel sample counts, on the
    participant's usable epochs, indexed 0..n-1 in time order."""
    pq = CACHE_DIR / "features" / f"{rec.participant}.{VERSION}.parquet"
    if use_cache and pq.exists():
        return pd.read_parquet(pq)
    tab = epoch_table(rec)
    df = tab[tab["usable"]].drop(columns=["usable"]).reset_index(drop=True)
    idx = pd.DatetimeIndex(df["t"])
    s = lambda col: pd.Series(df[col].to_numpy(), index=idx)
    df["PeakEDA2hr_sum"] = rolling(s("PeakEDA"), "2h", "sum").to_numpy()
    df["PeakEDA2hr_mean"] = rolling(s("PeakEDA"), "2h", "mean").to_numpy()
    df["ACC_mean_2hrs"] = rolling(s("ACC_Mean"), "2h", "mean").to_numpy()
    df["ACC_max_2hrs"] = rolling(s("ACC_Max"), "2h", "max").to_numpy()
    df["Activity_bouts"] = activity_bouts(df["ACC_Mean"].to_numpy(), df["HR_Mean"].to_numpy())
    df["Activity24"] = rolling(s("Activity_bouts"), "24h", "mean").to_numpy()
    df["Activity1hr"] = rolling(s("Activity_bouts"), "1h", "sum").to_numpy()
    df["WakeTime"] = wake_time(idx, df["HR_Mean"], df["HR_Std"], df["ACC_Mean"], df["ACC_Std"])
    df["Minfrommid"], df["Hourfrommid"] = circadian(idx)
    ev = eating_events(rec.food_log)
    ff = food_features(ev, idx)
    for c in ff.columns:
        df[c] = ff[c].to_numpy()
    for w in ("2hr", "8hr", "24hr"):
        df[f"Eatmean{w}"] = rolling(s("Eat"), w.replace("hr", "h"), "mean").to_numpy()
    df["Biological Sex"] = 1.0 if str(rec.gender).strip().upper() == "MALE" else 0.0
    df["HbA1c"] = float(rec.hba1c)
    df["ID"] = float(int(rec.participant))
    df["participant"] = rec.participant
    df.attrs.update({"food_rows": ev.attrs.get("rows", 0), "food_rows_missing_nutrient": ev.attrs.get("rows_missing_nutrient", 0),
                     "food_rows_no_time": ev.attrs.get("dropped_no_time", 0), "readings": int(len(tab)), "unusable": int((~tab["usable"]).sum())})
    cols = ["participant", "t", "glucose"] + FEATURES + [c for c in df.columns if c.startswith("n_")]
    df = df[cols]
    if use_cache:
        pq.parent.mkdir(parents=True, exist_ok=True)
        meta = df.attrs.copy()
        df.to_parquet(pq, index=False)
        df.attrs.update(meta)
    return df


def load_all(use_cache: bool = True) -> pd.DataFrame:
    """All sixteen participants' matrices, concatenated."""
    return pd.concat([build_matrix(load_participant(p)[0], use_cache) for p in PARTICIPANTS], ignore_index=True)


def main() -> None:
    day0 = {r["participant"]: int(r["readings_with_complete_e4_window"]) for r in csv.DictReader(open(REPO_ROOT / "results" / "coverage.csv"))}
    rows, mats = [], []
    for pid in PARTICIPANTS:
        rec, _ = load_participant(pid)
        tab = epoch_table(rec)
        df = build_matrix(rec, use_cache=False)
        ev = eating_events(rec.food_log)
        n, usable = len(tab), int(tab["usable"].sum())
        hrv_ok = int(df[list(HRV_NAMES)].notna().all(axis=1).sum())
        complete = int(df[FEATURES].notna().all(axis=1).sum())
        half = len(df) // 2
        rows.append(dict(participant=pid, readings=n, usable_epochs=usable, share_usable=round(usable / n, 3),
                         unusable_missing_ACC=int((tab["n_ACC"] == 0).sum()), unusable_missing_EDA=int((tab["n_EDA"] == 0).sum()),
                         unusable_missing_TEMP=int((tab["n_TEMP"] == 0).sum()), unusable_missing_HR=int((tab["n_HR"] == 0).sum()),
                         epochs_with_hrv=hrv_ok, share_with_hrv=round(hrv_ok / max(usable, 1), 3),
                         complete_rows_all_69=complete, share_complete=round(complete / max(usable, 1), 3),
                         day0_complete_10min_bvp_window=day0.get(pid, ""),
                         first_half_n=half, first_half_boundary=str(pd.Timestamp(df["t"].iloc[half]).round("min")) if len(df) > half else "",
                         food_events=len(ev), food_rows=ev.attrs["rows"], food_rows_missing_nutrient=ev.attrs["rows_missing_nutrient"],
                         food_rows_no_time=ev.attrs["dropped_no_time"], wake_times_found=int(df["WakeTime"].dropna().nunique())))
        mats.append(df)
        print(f"  {pid}: {usable}/{n} usable ({usable / n:.0%}), HRV in {hrv_ok / max(usable, 1):.0%}, all 69 present in {complete / max(usable, 1):.0%}; "
              f"{len(ev)} eating events from {ev.attrs['rows']} rows; wake times {rows[-1]['wake_times_found']}", flush=True)
    allm = pd.concat(mats, ignore_index=True)
    with open(REPO_ROOT / "results" / "epochs.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    miss = []
    per = allm.groupby("participant")[FEATURES].apply(lambda g: g.isna().mean())
    for i, feat in enumerate(FEATURES, 1):
        miss.append(dict(feature=feat, n=i, share_missing_pooled=round(float(allm[feat].isna().mean()), 4),
                         share_missing_min=round(float(per[feat].min()), 4), share_missing_max=round(float(per[feat].max()), 4),
                         participants_with_any_missing=int((per[feat] > 0).sum())))
    with open(REPO_ROOT / "results" / "feature_missingness.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(miss[0])); w.writeheader(); w.writerows(miss)
    tot_u, tot_n = sum(r["usable_epochs"] for r in rows), sum(r["readings"] for r in rows)
    print(f"\n{tot_u:,} usable epochs of {tot_n:,} readings ({tot_u / tot_n:.1%}); Day 0 complete-10-min-window count {sum(day0.values()):,}; "
          f"paper: ~25,000. HRV present in {sum(r['epochs_with_hrv'] for r in rows):,}; all 69 present in {sum(r['complete_rows_all_69'] for r in rows):,}.")
    print("wrote results/epochs.csv, results/feature_missingness.csv")


if __name__ == "__main__":
    sys.exit(main())
