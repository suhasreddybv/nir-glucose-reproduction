"""The BIG IDEAs loader: unit assertions on synthetic inputs, and per-participant checks
that skip without the data."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data import loader
from src.data.loader import (
    ACC_UNITS_PER_G,
    CHANNELS,
    PARTICIPANTS,
    Channel,
    DataValidationError,
    measured_hz,
    validate,
)

have_data = (loader.DATA_ROOT / "SHA256SUMS.txt").exists() and (loader.DATA_ROOT / "001" / "BVP_001.csv").exists()
needs_data = pytest.mark.skipif(not have_data, reason="BIG IDEAs data not present; see data/README.md")


def _synthetic(acc_scale=64.0, bvp_offset=0.0, overlap=True):
    t0 = np.datetime64("2020-02-13T15:28:50", "ns")
    n_h = 30
    def ts(hz, hours): return t0 + (np.arange(int(hz * 3600 * hours)) * (1e9 / hz)).astype("timedelta64[ns]")
    rng = np.random.default_rng(0)
    acc_t = ts(32, n_h); acc = rng.normal(0, 3, (len(acc_t), 3)); acc[:, 2] += acc_scale
    acc[: 32 * 3600] = rng.normal(0, 0.5, (32 * 3600, 3)) + [0, 0, acc_scale]     # a resting hour first
    bvp_t = ts(64, n_h); bvp = rng.normal(bvp_offset, 20, len(bvp_t))
    cgm_t = t0 + (np.arange(n_h * 12) * 300e9).astype("timedelta64[ns]") + (np.timedelta64(0 if overlap else 40 * 24 * 3600, "s"))
    cgm = rng.uniform(70, 160, len(cgm_t))
    ch = {"ACC": Channel("ACC", acc_t, acc, measured_hz=measured_hz(acc_t)), "BVP": Channel("BVP", bvp_t, bvp, measured_hz=64.0),
          "EDA": Channel("EDA", ts(4, n_h), rng.random(int(4 * 3600 * n_h)), measured_hz=4.0),
          "TEMP": Channel("TEMP", ts(4, n_h), rng.random(int(4 * 3600 * n_h)) + 30, measured_hz=4.0),
          "HR": Channel("HR", ts(1, n_h), rng.random(int(3600 * n_h)) + 70, derived=True, measured_hz=1.0),
          "IBI": Channel("IBI", ts(1, n_h), rng.random(int(3600 * n_h)), derived=True),
          "Dexcom": Channel("Dexcom", cgm_t, cgm, measured_hz=1 / 300)}
    return ch


def test_validation_accepts_the_documented_facts():
    facts = validate("000", _synthetic())
    assert 60 < facts["acc_median_magnitude_raw"] < 68
    assert abs(facts["bvp_resting_hour_mean"]) < 0.1 * facts["bvp_resting_hour_sd"]
    assert facts["overlap_hours"] > 24 and facts["cgm_median_interval_s"] == 300.0 and facts["cgm_at_floor"] == 0


def test_validation_rejects_acc_already_in_g():
    with pytest.raises(DataValidationError, match="1/64 g"):
        validate("000", _synthetic(acc_scale=1.0))


def test_validation_rejects_bvp_with_a_dc_component():
    with pytest.raises(DataValidationError, match="zero-centred"):
        validate("000", _synthetic(bvp_offset=50.0))


def test_validation_rejects_inconsistent_date_shifts():
    with pytest.raises(DataValidationError, match="overlap"):
        validate("000", _synthetic(overlap=False))


def test_measured_hz():
    t = np.datetime64("2020-01-01", "ns") + (np.arange(1000) * int(1e9 / 32)).astype("timedelta64[ns]")
    assert abs(measured_hz(t) - 32) < 0.01


def test_constants_match_the_readme():
    assert ACC_UNITS_PER_G == 64.0 and len(PARTICIPANTS) == 16 and "Food_Log" in CHANNELS


@needs_data
def test_checksum_list_covers_every_expected_file():
    exp = loader.checksums()
    for pid in PARTICIPANTS:
        for name in CHANNELS:
            assert f"{pid}/{name}_{pid}.csv" in exp, (pid, name)
    assert "Demographics.csv" in exp


@needs_data
@pytest.mark.parametrize("pid", PARTICIPANTS)
def test_every_participant_verifies_parses_and_validates(pid):
    rec, facts = loader.load_participant(pid)
    assert rec.participant == pid and 5.0 < rec.hba1c < 7.0
    assert 55 < facts["acc_median_magnitude_raw"] < 75 and 0.85 < facts["acc_median_magnitude_g"] < 1.15
    assert facts["overlap_hours"] > 24
    assert rec["HR"].derived and rec["IBI"].derived and not rec["BVP"].derived
