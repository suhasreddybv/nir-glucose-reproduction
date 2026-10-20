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


def test_food_log_reader_handles_the_three_schemas(tmp_path):
    from src.data.loader import FOOD_COLUMNS, read_food_log
    std = tmp_path / "a.csv"; std.write_text("date,time,time_begin,time_end,logged_food,amount,unit,searched_food,calorie,total_carb,dietary_fiber,sugar,protein,total_fat\n"
                                            "2020-02-13,18:00:00,2020-02-13 18:00:00,,Berry Smoothie,20.0,fluid ounce,Strawberry Smoothie,456.0,85.0,1.7,83.0,16.0,3.3\n")
    tod = tmp_path / "b.csv"; tod.write_text(std.read_text().replace("date,time,", "date,time_of_day,"))
    nohdr = tmp_path / "c.csv"; nohdr.write_text("2020-02-22,10:30:00,2020-02-22 10:30:00,Chicken Nuggets,8.0,piece,Chicken Nuggets,393.0,19.0,0.1,20.0\n")
    a, b, c = read_food_log(std), read_food_log(tod), read_food_log(nohdr)
    for df in (a, b, c):
        assert list(df.columns) == list(FOOD_COLUMNS) and df["time_begin"].notna().all()
    assert a.attrs["schema"] == "standard" and b.attrs["schema"] == "time_of_day" and c.attrs["schema"] == "headerless_11_columns"
    assert float(a["total_carb"][0]) == 85.0 and float(b["total_carb"][0]) == 85.0
    assert float(c["total_carb"][0]) == 19.0 and float(c["sugar"][0]) == 0.1 and float(c["protein"][0]) == 20.0
    assert np.isnan(c["dietary_fiber"][0]) and np.isnan(c["total_fat"][0])


def test_out_of_order_recordings_are_sorted_and_counted():
    from src.data.loader import in_time_order
    t0 = np.datetime64("2020-07-05T15:11:13", "ns")
    block_a = t0 + np.timedelta64(19, "D") + (np.arange(100) * int(1e9 / 64)).astype("timedelta64[ns]")   # later block first
    block_b = t0 + (np.arange(100) * int(1e9 / 64)).astype("timedelta64[ns]")
    ts = np.concatenate([block_a, block_b, block_b[:3]])                                  # plus three exact duplicates
    vals = np.arange(len(ts), dtype=float)
    ts2, v2, back, dup = in_time_order(ts, vals)
    assert back == 2 and dup == 3 and len(ts2) == 203, "two backward steps (the junction and the appended block); nothing dropped"
    assert np.all(np.diff(ts2.astype(np.int64)) >= 0) and ts2[0] == block_b[0] and v2[0] == 100.0
    ts3, _, back3, dup3 = in_time_order(block_b, np.zeros(100))
    assert back3 == 0 and dup3 == 0 and np.array_equal(ts3, block_b)


def test_minute_resolution_hr_stamps_are_expanded_to_seconds():
    from src.data.loader import expand_minute_stamps
    m = np.datetime64("2020-02-13T15:29", "ns")
    ts = np.array([m] * 60 + [m + np.timedelta64(60, "s")] * 60)
    out = expand_minute_stamps(ts, 1.0)
    assert len(np.unique(out)) == 120 and out[0] == m and out[59] == m + np.timedelta64(59, "s") and out[60] == m + np.timedelta64(60, "s")
