"""The protocol freeze, pinned mechanically (protocol §11).

`docs/decisions.md` records the SHA-256 prefix of `docs/protocol.md` at the freeze. If the
file changes, this test fails until a dated revision section is added to the protocol and a
new entry records the new hash - the change is then visible, not silent.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs" / "protocol.md"
LOG = ROOT / "docs" / "decisions.md"
PIN = re.compile(r"\*\*Protocol hash:\*\* `([0-9a-f]{16})`")


def protocol_hash() -> str:
    return hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()[:16]


def test_the_protocol_hash_in_the_log_matches_the_file():
    pins = PIN.findall(LOG.read_text())
    assert pins, "no `**Protocol hash:** `...`` line in docs/decisions.md"
    assert pins[-1] == protocol_hash(), (
        f"docs/protocol.md hashes to {protocol_hash()} but the latest pin is {pins[-1]}: "
        "add a dated revision section to the protocol and a new log entry with the new hash")


def test_the_five_predictions_are_in_the_protocol_verbatim():
    text = PROTOCOL.read_text()
    for p in ("**P1.** The per-participant mean (B1) under the personalised regime lands within 3 mg/dL of the paper's 21.10; the personalised XGBoost beats B1 by less than 3 mg/dL.",
              "**P2.** B0 or B2 under LOPO lands within 3 mg/dL of the paper's 21.22; the population XGBoost beats B2 by less than 3.",
              "**P3.** The classification result reproduces within 3 points under R1 (84.3 %) and falls by more than 15 points under R2 and R3.",
              "**P4.** B1's \"accuracy\" (100 − MAPE) is above 84 %, i.e. inside the paper's headline range, from a constant.",
              "**P5** (measurement, not prediction). Removing the food log costs more RMSE than removing all E4 features. Report which way it goes."):
        assert p in text, f"prediction text changed or missing: {p[:40]}..."


def test_no_protocol_cell_is_left_blank():
    text = PROTOCOL.read_text()
    assert not re.search(r"^\|(\s*\|){2,}\s*$", text, re.M), "an empty table row remains in the protocol"
    assert "draft, not yet frozen" not in text
