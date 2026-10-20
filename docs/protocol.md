# Evaluation protocol — draft, not yet frozen

Target: Bent, B., Cho, P. J., Henriquez, M., et al. (2021). Engineering digital biomarkers of interstitial glucose from noninvasive smartwatches. *npj Digital Medicine*, 4, 89. https://doi.org/10.1038/s41746-021-00465-w

Data: BIG IDEAs Lab Glycemic Variability and Wearable Device Data, PhysioNet v1.1.3, https://doi.org/10.13026/aw6y-fc44 (ODC-BY v1.0). Companion code: the Duke Digital Biomarker Discovery Pipeline repositories — read for underspecified choices, cited, not copied.

**Nothing is fitted until this file is frozen and hashed.** Cells 1–7 are filled from the paper and the companion code by Suhas (20 Oct, evening); cells 8–11 are fixed now, independent of what the paper says. Where the prose is vague and the code resolved it, the cell says "from code" and names the file.

## 1. The claims to reproduce

| Claim | Exact number | Unit of analysis (window, participant, pooled) | Table / figure |
|---|---|---|---|
| | | | |

## 2. Inputs

| Question | Answer | Source (paper §, figure, or code file) |
|---|---|---|
| Which E4 channels (ACC, BVP, EDA, TEMP) | | |
| Were the Empatica-derived HR / IBI used? | | |
| Was the food log (carbohydrates, calories, timing) an input? | | |
| Was lagged glucose (any prior CGM reading) ever an input? | | |
| Demographics (gender, HbA1c) as inputs? | | |

*Why each matters: a model using the food log is not sensing glucose from the wrist; a model using lagged CGM is a forecaster, not a sensor.*

## 3. Windowing

| Window length | Features per window | Aggregation | Source |
|---|---|---|---|
| | | | |

## 4. Models

| Family | Personalised per participant, population, or both | Hyperparameters and how chosen | Source |
|---|---|---|---|
| | | | |

## 5. Split — the single most consequential cell

| Question | Answer | Source |
|---|---|---|
| Random windows within participant, or time-blocked? | | |
| By participant (held-out subjects) or within? | | |
| Folds / repeats; how the headline aggregates them | | |

## 6. Metrics

| Task | Metric(s) | Aggregation level (window / participant / pooled) | Source |
|---|---|---|---|
| Regression (glucose value) | | | |
| Classification (excursion classes) | | | |

## 7. Underspecified choices

| Choice | What the paper says | What the code does | Resolved as |
|---|---|---|---|
| | | | |

---

*From here on, fixed on 20 October 2026 regardless of the paper's answers.*

## 8. Baselines, pre-registered

Every one reported under both split regimes of §9, per participant with n and pooled:

1. **Population mean** — predict the training set's mean glucose for every window.
2. **Per-participant mean** — predict that participant's mean glucose over their training period only.
3. **Persistence** — the last CGM reading at the window's end, for any model family that uses lagged glucose (if no model does, persistence is reported once as the forecaster's floor and labelled as not comparable).
4. **Per-participant linear model** on the same features the paper's models use, fitted on the training period only.

A published model that does not beat baseline 2 under the paper's split, or baseline 4 under the time-blocked split, has not demonstrated sensing.

## 9. Two split regimes, always side by side

- **The paper's split**, exactly as §5 records it.
- **A time-blocked split**: train on the first part of each participant's record, test on the last; no test window shares any time with its training set, and no feature window straddles the boundary. The fraction is fixed before the first fit (default: last 30% of each participant's overlapping E4–Dexcom record) and recorded here.

If the paper's split is random within participant, the gap between the two regimes is the reproduction's headline, because within-participant random splits let a model learn a participant's glucose trajectory and read it back.

## 10. Evaluation

- Real CGM readings only; nothing interpolated is ever a target.
- The clinical scorer vendored from `cgm-forecast-conformal` (Clarke and Parkes grids from the papers, MARD with the reference as denominator, time-in-range agreement, hypoglycaemia sensitivity with the censoring flag); the iCGM analogues labelled as analogues throughout (`docs/icgm_criteria.md`).
- Every per-participant figure carries its n; every pooled figure its total.
- Bootstrap over participants, n = 16; the intervals will be wide and are stated.
- Dexcom G6 values are censored to 40–400 mg/dL; floored and ceilinged targets are counted.
- No trace of any participant's glucose or wearable signal appears in a figure (repository policy; the licence permits it, the policy does not).

## 11. Freeze

Hashed (SHA-256 prefix recorded in the decision log) before the first fit. Any later change is a dated section with its reason; results under the old protocol are re-run or struck.
