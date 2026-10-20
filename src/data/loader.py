"""BIG IDEAs Lab Glycemic Variability and Wearable Device Data (PhysioNet v1.1.3) loader.

Written on Day 0 (20 Oct 2026); the validated loader lands once the data is verified
against SHA256SUMS.txt (Part C). Until then this module holds only the paths.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.environ.get("BIG_IDEAS_ROOT", REPO_ROOT / "data" / "big-ideas-glycemic-wearable"))
CACHE_DIR = Path(os.environ.get("NIR_CACHE", Path.home() / ".cache" / "nir-glucose-reproduction"))
