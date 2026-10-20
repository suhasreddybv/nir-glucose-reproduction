"""BIG IDEAs Lab Glycemic Variability and Wearable Device Data (PhysioNet v1.1.3): a loader
that verifies every file against SHA256SUMS.txt, asserts what the protocol rests on, and
caches to parquet outside the tracked tree.

File formats, read from the files on 20 Oct 2026 (D-005):
  Dexcom_<id>.csv   a Dexcom Clarity export: 12 metadata/alert rows, then EGV rows with
                    "Timestamp (YYYY-MM-DDThh:mm:ss)" and "Glucose Value (mg/dL)"; no "Low"/
                    "High" strings in any of the 16 files (checked), values censored to 40-400.
  ACC_<id>.csv      "datetime, acc_x, acc_y, acc_z" at 32 Hz, integers in 1/64 g (asserted:
                    median magnitude ~ 64 before scaling, ~ 1 g after)
  BVP_<id>.csv      "datetime, bvp" at 64 Hz, zero-centred (asserted on a resting hour)
  EDA_, TEMP_       "datetime, eda|temp" at 4 Hz
  HR_<id>.csv       "datetime, hr" at 1 Hz but with MINUTE-resolution timestamps ("2/13/20
                    15:29"), Empatica-derived; IBI_<id>.csv irregular, Empatica-derived.
                    Both are flagged derived; whether the paper used them is a protocol cell.
  Food_Log_<id>.csv date, time, logged food, calories, carbohydrate, fibre, sugar, protein, fat
  Demographics.csv  ID, Gender, HbA1c (a high-normal cohort: 5.3-6.4%)
Timestamps are date-shifted per participant; the shift must be consistent across a
participant's files, which the E4-Dexcom overlap assertion checks.

The data are ODC-BY; the repository's policy keeps them out of the tree (D-002).
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.environ.get("BIG_IDEAS_ROOT", REPO_ROOT / "data" / "big-ideas-glycemic-wearable"))
CACHE_DIR = Path(os.environ.get("NIR_CACHE", Path.home() / ".cache" / "nir-glucose-reproduction"))

PARTICIPANTS = tuple(f"{i:03d}" for i in range(1, 17))
CHANNELS = ("ACC", "BVP", "Dexcom", "EDA", "HR", "IBI", "TEMP", "Food_Log")
NOMINAL_HZ = {"ACC": 32.0, "BVP": 64.0, "EDA": 4.0, "TEMP": 4.0, "HR": 1.0}
DERIVED = ("HR", "IBI")             # Empatica-computed, not raw sensor output
ACC_UNITS_PER_G = 64.0              # E4 accelerometer CSVs are in 1/64 g (PhysioNet readme; asserted)
GLUCOSE_RANGE = (40.0, 400.0)       # Dexcom G6 reporting range; values are censored at both ends
CGM_INTERVAL_S = 300


class DataValidationError(ValueError):
    pass


def _fail(pid: str, msg: str) -> None:
    raise DataValidationError(f"{pid}: {msg}")


def sha256(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def checksums() -> dict[str, str]:
    """Relative path -> expected SHA-256, from the dataset's own SHA256SUMS.txt."""
    out = {}
    for line in (DATA_ROOT / "SHA256SUMS.txt").read_text().splitlines():
        if line.strip():
            digest, rel = line.split(maxsplit=1)
            out[rel.strip()] = digest
    return out


def verify(rel: str, expected: dict[str, str] | None = None) -> Path:
    """The file's path, after its SHA-256 matches the list. A failing file is not used."""
    expected = expected or checksums()
    path = DATA_ROOT / rel
    if not path.exists():
        raise FileNotFoundError(f"{path} not found; see data/README.md")
    if rel not in expected:
        raise DataValidationError(f"{rel} is not in SHA256SUMS.txt")
    if sha256(path) != expected[rel]:
        raise DataValidationError(f"{rel} fails its SHA-256; not used")
    return path


@dataclass(frozen=True)
class Channel:
    name: str
    ts: np.ndarray            # datetime64[ns]
    values: np.ndarray        # [n] or [n, 3] for ACC
    derived: bool = False
    measured_hz: float = float("nan")


@dataclass(frozen=True)
class SubjectRecord:
    participant: str
    gender: str
    hba1c: float
    channels: dict[str, Channel]
    food_log: pd.DataFrame
    sha256: dict[str, str] = field(default_factory=dict)

    def __getitem__(self, name: str) -> Channel:
        return self.channels[name]

    @property
    def cgm(self) -> Channel:
        return self.channels["Dexcom"]


# ------------------------------------------------------------------ parsers

def read_dexcom(path: Path) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    egv = df[df["Event Type"] == "EGV"]
    ts = pd.to_datetime(egv["Timestamp (YYYY-MM-DDThh:mm:ss)"]).to_numpy("datetime64[ns]")
    vals = pd.to_numeric(egv["Glucose Value (mg/dL)"], errors="raise").to_numpy(float)
    return ts, vals


def read_e4(path: Path, name: str) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    ts = pd.to_datetime(df["datetime"], format="mixed").to_numpy("datetime64[ns]")
    if name == "ACC":
        vals = df[["acc_x", "acc_y", "acc_z"]].to_numpy(float)
    else:
        vals = df[df.columns[1]].to_numpy(float)
    return ts, vals


def read_food_log(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["time_begin"] = pd.to_datetime(df["time_begin"])
    return df


def measured_hz(ts: np.ndarray) -> float:
    d = np.diff(ts.astype("datetime64[ns]").astype(np.int64)) / 1e9
    d = d[d > 0]
    return float(1.0 / np.median(d)) if len(d) else float("nan")


# ------------------------------------------------------------------ validation

def validate(pid: str, channels: dict[str, Channel]) -> dict:
    """The assertions of D-005, each returning the number it rests on."""
    facts = {}
    acc = channels["ACC"].values
    mag = np.linalg.norm(acc, axis=1)
    facts["acc_median_magnitude_raw"] = float(np.median(mag))
    if not (40 < facts["acc_median_magnitude_raw"] < 90):
        _fail(pid, f"ACC median magnitude {facts['acc_median_magnitude_raw']:.1f} is not ~64 (1/64 g units)")
    bvp = channels["BVP"]
    # a resting hour: the hour of lowest ACC variance
    t_acc = channels["ACC"].ts.astype("datetime64[h]")
    hours, idx = np.unique(t_acc, return_inverse=True)
    var = np.array([mag[idx == k].std() if (idx == k).sum() > 1000 else np.inf for k in range(len(hours))])
    rest = hours[int(np.argmin(var))]
    m = bvp.ts.astype("datetime64[h]") == rest
    facts["bvp_resting_hour_mean"] = float(bvp.values[m].mean()) if m.any() else float("nan")
    facts["bvp_resting_hour_sd"] = float(bvp.values[m].std()) if m.any() else float("nan")
    if m.any() and abs(facts["bvp_resting_hour_mean"]) > 0.1 * facts["bvp_resting_hour_sd"]:
        _fail(pid, f"BVP is not zero-centred on the resting hour: mean {facts['bvp_resting_hour_mean']:.2f}, SD {facts['bvp_resting_hour_sd']:.2f}")
    for name, hz in NOMINAL_HZ.items():
        facts[f"{name}_hz"] = channels[name].measured_hz
        if name != "HR" and abs(channels[name].measured_hz - hz) > 0.05 * hz:
            _fail(pid, f"{name} sampled at {channels[name].measured_hz:.2f} Hz, expected {hz}")
    cgm = channels["Dexcom"]
    if not np.all(np.diff(cgm.ts) > np.timedelta64(0, "s")):
        _fail(pid, "Dexcom timestamps are not strictly increasing")
    lo, hi = cgm.values.min(), cgm.values.max()
    if lo < GLUCOSE_RANGE[0] or hi > GLUCOSE_RANGE[1]:
        _fail(pid, f"Dexcom values {lo}-{hi} outside {GLUCOSE_RANGE}")
    facts["cgm_at_floor"] = int((cgm.values <= GLUCOSE_RANGE[0]).sum()); facts["cgm_at_ceiling"] = int((cgm.values >= GLUCOSE_RANGE[1]).sum())
    d = np.diff(cgm.ts).astype("timedelta64[s]").astype(int)
    facts["cgm_median_interval_s"] = float(np.median(d))
    if abs(facts["cgm_median_interval_s"] - CGM_INTERVAL_S) > 30:
        _fail(pid, f"Dexcom median interval {facts['cgm_median_interval_s']} s, expected ~300")
    # the date shift must be consistent across the participant's files: E4 and Dexcom must overlap
    e4_start, e4_end = channels["BVP"].ts.min(), channels["BVP"].ts.max()
    overlap_start, overlap_end = max(e4_start, cgm.ts.min()), min(e4_end, cgm.ts.max())
    facts["overlap_hours"] = float((overlap_end - overlap_start) / np.timedelta64(1, "h"))
    if facts["overlap_hours"] <= 24:
        _fail(pid, f"E4 and Dexcom overlap only {facts['overlap_hours']:.1f} h: date shifts inconsistent?")
    return facts


# ------------------------------------------------------------------ loading

def load_participant(pid: str, use_cache: bool = True) -> tuple[SubjectRecord, dict]:
    """Verify, parse, validate and cache one participant. Returns (record, measured facts)."""
    if pid not in PARTICIPANTS:
        raise ValueError(f"unknown participant {pid!r}")
    expected = checksums()
    demo = pd.read_csv(DATA_ROOT / "Demographics.csv", encoding="utf-8-sig")
    row = demo[demo["ID"] == int(pid)]
    if len(row) != 1:
        _fail(pid, "missing from Demographics.csv")
    cache = CACHE_DIR / "participants" / pid
    shas = {}
    channels: dict[str, Channel] = {}
    for name in CHANNELS:
        rel = f"{pid}/{name}_{pid}.csv"
        path = verify(rel, expected)
        shas[rel] = expected[rel]
        if name == "Food_Log":
            food = read_food_log(path)
            continue
        pq = cache / f"{name}.parquet"
        if use_cache and pq.exists():
            df = pd.read_parquet(pq)
            ts = df["ts"].to_numpy("datetime64[ns]")
            vals = df[[c for c in df.columns if c != "ts"]].to_numpy(float)
            vals = vals[:, 0] if vals.shape[1] == 1 else vals
        else:
            ts, vals = read_dexcom(path) if name == "Dexcom" else read_e4(path, name)
            if use_cache:
                cache.mkdir(parents=True, exist_ok=True)
                cols = {"ts": ts}
                if vals.ndim == 2:
                    cols.update({f"v{k}": vals[:, k] for k in range(vals.shape[1])})
                else:
                    cols["v0"] = vals
                pd.DataFrame(cols).to_parquet(pq, index=False)
        if name == "ACC":
            vals = vals / ACC_UNITS_PER_G          # to g, after the raw-magnitude assertion below
        channels[name] = Channel(name, ts, vals, derived=name in DERIVED, measured_hz=measured_hz(ts))
    # validation runs on the raw ACC magnitude: undo the scaling for that one check
    raw_acc = Channel("ACC", channels["ACC"].ts, channels["ACC"].values * ACC_UNITS_PER_G, measured_hz=channels["ACC"].measured_hz)
    facts = validate(pid, {**channels, "ACC": raw_acc})
    facts["acc_median_magnitude_g"] = float(np.median(np.linalg.norm(channels["ACC"].values, axis=1)))
    rec = SubjectRecord(pid, str(row["Gender"].iloc[0]), float(row["HbA1c"].iloc[0]), channels, food, shas)
    return rec, facts
