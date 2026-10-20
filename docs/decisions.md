# Design decisions

An append-only record of the design choices in this repository, the measured evidence behind each, and what was rejected. Entries are dated by when the decision landed in git, with the commit cited. Every number is copied from a committed results file, test or script output, and the source is named. Nothing is quoted from memory. Entries are never rewritten: a changed decision gets a new entry, and the old entry's **Status** line alone is updated to point at it. Corrections stay visible beside what they correct.

Same format and rules as `wrist-ppg-motion-robust-hr` and `cgm-forecast-conformal`; the mechanical guard (`tests/test_decision_log.py`) is in place from the first entry.

---

### D-001 · The target: Bent et al. 2021 on the BIG IDEAs Lab data, and why the alternatives were not chosen
- **Date / commit:** 2026-10-20 · `pending`
- **Status:** adopted
- **Decision:** the paper to reproduce is Bent, Cho, Henriquez et al. (2021), *Engineering digital biomarkers of interstitial glucose from noninvasive smartwatches*, npj Digital Medicine 4:89, on the BIG IDEAs Lab Glycemic Variability and Wearable Device Data (PhysioNet v1.1.3): 16 participants, 8–10 days each, Empatica E4 (BVP 64 Hz, ACC 32 Hz, EDA and TEMP 4 Hz, derived HR and IBI) with Dexcom G6 every five minutes and a food log. The data are public under ODC-BY v1.0 and the companion code is public (Duke DBDP).
- **Rejected:** Zhang et al. — no data release; the institution withheld it. Bhatia et al. — the paper makes no claim specific enough to reproduce.
- **The reproduction's value, stated before anything is fitted:** the baselines the paper did not report (population mean, per-participant mean, persistence where lagged glucose is used, a per-participant linear model) and the split it did; both are pre-registered in `docs/protocol.md` §8–9. If the paper's split is random within participant, the gap to a time-blocked split is the headline. The repository name `nir-glucose-reproduction` predates the choice and stays until the write-up decides otherwise.

### D-002 · The licence, and the repository's own stricter policy
- **Date / commit:** 2026-10-20 · `pending`
- **Status:** adopted
- **Decision:** the data are under the Open Data Commons Attribution Licence v1.0 — attribution required, redistribution permitted — with PhysioNet's two required citations recorded in `data/README.md`. The licence would permit derived data and traces in this repository; **the repository's policy from repo 2 holds anyway**: no raw data, no caches, no per-participant time series in a figure. The participants are time-shifted individuals, and the policy costs nothing the reproduction needs. Raw files live outside the tracked tree (`data/` is gitignored but for its README), the cache at `~/.cache/nir-glucose-reproduction`.

### D-003 · Two split regimes, always reported side by side
- **Date / commit:** 2026-10-20 · `pending`
- **Status:** adopted
- **Decision:** every result is reported under the paper's split, exactly as the protocol records it, and under a time-blocked split — train on the first part of each participant's record, test on the last, no test window sharing time with its training set — with the fraction fixed before the first fit (`docs/protocol.md` §9). Neither regime is dropped because the other looks better. The reason is the one a wearable reviewer would give: a random split of windows within a participant lets a model learn the participant's glucose trajectory and read it back, and that is not sensing.

### D-004 · The baselines the paper did not report, pre-registered
- **Date / commit:** 2026-10-20 · `pending`
- **Status:** adopted
- **Decision:** population mean; per-participant mean over the training period only; persistence for any model that uses lagged glucose; a per-participant linear model on the same features — all under both regimes, per participant with n and pooled, before any published model is fitted (`docs/protocol.md` §8). A published model that does not beat the per-participant mean under the paper's split, or the linear model under the time-blocked split, has not demonstrated sensing. The clinical scorer and the iCGM analogue module are vendored from `cgm-forecast-conformal` with their tests, not rewritten; they carry the commit they came from.

### D-005 · Open — the E4 and Dexcom facts to re-verify before the loader is trusted
- **Date / commit:** 2026-10-20 · `pending`
- **Status:** open — measured in Part C of Day 0 once the files verify against SHA256SUMS.txt
- **Note:** the facts the loader must assert rather than assume, each with the lesson it comes from: E4 accelerometer CSVs are in units of 1/64 g (the PhysioNet readme says so; in `wrist-ppg-motion-robust-hr` a brief said the same and the data were already in g — so it is measured here: median magnitude ≈ 64 before scaling, ≈ 1.0 g after); BVP is zero-centred with the DC removed (mean against SD on a resting hour; perfusion index unavailable, as in repo 1); `HR.csv` and `IBI.csv` are Empatica-derived, not raw, and whether Bent et al. used them is a protocol question; timestamps are date-shifted per participant and the shift must be consistent across a participant's E4 and Dexcom files (overlap asserted); Dexcom G6 values are in mg/dL and censored to 40–400 (floored and ceilinged readings counted, as in repo 2). Each becomes a measured number in the entry that closes this one.
