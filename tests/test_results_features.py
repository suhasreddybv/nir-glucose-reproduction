"""results/epochs.csv and results/feature_missingness.csv: internal consistency, and the numbers the
README and the decision log quote from them."""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _rows(name):
    with open(ROOT / "results" / name) as f:
        return list(csv.DictReader(f))


def test_epochs_table_is_internally_consistent():
    rows = _rows("epochs.csv")
    assert [r["participant"] for r in rows] == [f"{i:03d}" for i in range(1, 17)]
    for r in rows:
        n, u, h, c = (int(r[k]) for k in ("readings", "usable_epochs", "epochs_with_hrv", "complete_rows_all_69"))
        assert c <= h <= u <= n
        assert int(r["first_half_n"]) == u // 2
        assert abs(u / n - float(r["share_usable"])) < 1e-3
        # an unusable epoch is the E4 being off: the four channels' missing counts agree to within one
        miss = [int(r[f"unusable_missing_{ch}"]) for ch in ("ACC", "EDA", "TEMP", "HR")]
        assert max(miss) - min(miss) <= 1 and n - u <= max(miss)


def test_the_quoted_totals_match_the_table():
    rows = _rows("epochs.csv")
    assert sum(int(r["readings"]) for r in rows) == 36898
    assert sum(int(r["usable_epochs"]) for r in rows) == 28964
    assert sum(int(r["complete_rows_all_69"]) for r in rows) == 25644
    assert sum(int(r["day0_complete_10min_bvp_window"]) for r in rows) == 28592
    for text in ((ROOT / "README.md").read_text(), (ROOT / "docs" / "decisions.md").read_text()):
        assert "28,964" in text and "25,644" in text


def test_missingness_table_covers_the_69_features_in_order():
    rows = _rows("feature_missingness.csv")
    from src.features.build import FEATURES
    assert [r["feature"] for r in rows] == list(FEATURES)
    for r in rows:
        lo, hi, pooled = (float(r[k]) for k in ("share_missing_min", "share_missing_max", "share_missing_pooled"))
        assert 0 <= lo <= pooled + 1e-9 and pooled <= hi + 1e-9 <= 1
    never = [r["feature"] for r in rows if int(r["participants_with_any_missing"]) == 0]
    assert len(never) == 55          # 14 have some: the four skews, HR_Std, the eight HRV metrics, WakeTime
    hrv = [r for r in rows if r["feature"] in ("maxHRV", "minHRV", "medianHRV", "meanHRV", "SDNN", "NN50", "pNN50", "RMSSD")]
    assert len({r["share_missing_pooled"] for r in hrv}) == 1 and float(hrv[0]["share_missing_pooled"]) == 0.0887
