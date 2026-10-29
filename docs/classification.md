# Classification: the paper's excursion classes under three splits

Protocol cells 1, 4 and 5 and §9; decision-log entries D-015 and D-016. Every number below is generated from `results/classification_*.csv` by `src/eval/write_docs.py` and pinned by `tests/test_results_classification.py`.

**The pipeline, fixed before the run** (`src/classify.py`). The class-balanced set of D-011 (N = 10,230: 3,410 each of PersLow, PersNorm and PersHigh, undersampled with seed 0 from the 25,644 complete labelled epochs). In each training fold, recursive feature elimination to 20 features with a decision tree as the estimator (the estimator the paper reports winning its comparison), then a scikit-learn decision tree with default settings and `random_state = 0`. The paper's 70/30 decision tree and 70/30 logistic regression run through the same RFE-20 step; the paper does not say whether they did, so that was decided before any number existed. Metrics as the paper's Methods name them, R² on the class codes thresholded at zero as Table 2's footnote says.

| Regime | Folds | Test windows (all folds) | Balanced accuracy, mean ± SD [95 % CI] | Weighted F1 | R² | Paper |
|---|---|---|---|---|---|---|
| Paper's split: random windows, repeated stratified 10-fold × 3 | 30 | 30,690 | **78.18 %** ± 1.12 [77.77, 78.57] | 78.07 % | 0.545 | 84.3 ± 1.3; R² 0.505 |
| Paper's 70/30 random-window split, decision tree | 1 | 3,069 | **73.44 %** | 73.23 % | 0.448 | 82.0; R² 0.455 |
| Paper's 70/30 split, logistic regression | 1 | 3,069 | **55.39 %** | 55.21 % | 0.000 | 52.0; R² 0 |
| Participant-grouped 10-fold × 3 | 30 | 30,690 | **40.15 %** ± 4.97 [38.45, 41.94] | 39.30 % | 0.000 | — |
| Time-blocked within participant, 24-h exclusion zones | 1 | 1,732 | **47.10 %** | 47.11 % | 0.000 | — |

**Read it this way.** Under the paper's own split the tree scores **78.18 %** against the paper's 84.3 %: 6.1 points short. That is inside the brief's 10-point stop rule, so the other regimes were run, and outside P3's 3-point margin, so **P3 is judged failed** on its own words (R1 78.18; R2 40.15 (drop 38.03); R3 47.1 (drop 31.08)). The second half of P3 — a fall of more than 15 points once windows of one person cannot sit on both sides of a fold — held by more than twice the margin: **40.15 %** with participants grouped and **47.10 %** time-blocked, against chance at 33.3 %. The R² reproduces more closely than the accuracy (0.545 against 0.505), and so does the logistic regression (55.4 % against 52.0 %); the 70/30 tree is 8.6 points short (73.4 % against 82.0 %). The 6.1-point shortfall under the paper's split is not explained here, and nothing was changed to close it. The differences that can be named are a larger balanced set (10,230 against 8,666, which would, if anything, help a window-level split), the wake-time rule and the first-day label window of D-008, and library versions.

**Why the split decides the result** (`results/classification_neighbours.csv`). Under the paper's split, **66.7 % of test windows have a training window from the same participant within 5 minutes**, 88.7 % within 15 minutes and 99.5 % within an hour. The label is a 24-hour rolling statistic and a third of the features are rolling sums, means or maxima over 2 to 24 hours, so a test window's nearest training neighbour carries almost the same features and, usually, the same label. RFE kept the participant ID in 29 of 30 folds; the features kept in every fold were ACC_Std, ACC_mean_2hrs, Activity24, Minfrommid, WakeTime, carbs2hr. With participants grouped, no test window has a same-participant training window at all; time-blocked, the median gap is 67 hours. What survives that separation is 40.1–47.1 % balanced accuracy, 7–14 points above chance.

**What the balanced set hides.** PersNorm is 71.8 % of the complete labelled epochs, PersLow 13.3 % and PersHigh 14.9 %. The positive predictive value below is what each call would be worth on that real stream, from each regime's per-class recall and the true prevalence. Under the paper's own split a PersHigh call would be right about half the time; with participants grouped, about one time in five.

| Regime | Recall PersLow | Recall PersNorm | Recall PersHigh | PPV PersLow at true prevalence | PPV PersNorm | PPV PersHigh |
|---|---|---|---|---|---|---|
| Paper's split: random windows, repeated stratified 10-fold × 3 | 82.5 % | 68.9 % | 83.1 % | 47.6 % | 93.1 % | 52.0 % |
| Paper's 70/30 random-window split, decision tree | 77.9 % | 61.0 % | 81.4 % | 41.5 % | 91.1 % | 45.0 % |
| Paper's 70/30 split, logistic regression | 63.0 % | 46.6 % | 56.6 % | 24.6 % | 84.5 % | 32.0 % |
| Participant-grouped 10-fold × 3 | 30.0 % | 56.6 % | 34.1 % | 17.1 % | 75.3 % | 22.4 % |
| Time-blocked within participant, 24-h exclusion zones | 37.7 % | 59.0 % | 44.6 % | 23.3 % | 77.2 % | 28.1 % |

## Confusion matrices

**Paper's split: random windows, repeated stratified 10-fold × 3** (rows true, columns predicted, summed over folds)

| | PersLow | PersNorm | PersHigh |
|---|---|---|---|
| PersLow | 8,444 | 1,356 | 430 |
| PersNorm | 1,632 | 7,047 | 1,551 |
| PersHigh | 438 | 1,291 | 8,501 |

**Paper's 70/30 random-window split, decision tree** (rows true, columns predicted, summed over folds)

| | PersLow | PersNorm | PersHigh |
|---|---|---|---|
| PersLow | 797 | 168 | 58 |
| PersNorm | 198 | 624 | 201 |
| PersHigh | 47 | 143 | 833 |

**Paper's 70/30 split, logistic regression** (rows true, columns predicted, summed over folds)

| | PersLow | PersNorm | PersHigh |
|---|---|---|---|
| PersLow | 644 | 184 | 195 |
| PersNorm | 327 | 477 | 219 |
| PersHigh | 188 | 256 | 579 |

**Participant-grouped 10-fold × 3** (rows true, columns predicted, summed over folds)

| | PersLow | PersNorm | PersHigh |
|---|---|---|---|
| PersLow | 3,066 | 5,037 | 2,127 |
| PersNorm | 2,328 | 5,790 | 2,112 |
| PersHigh | 2,076 | 4,665 | 3,489 |

**Time-blocked within participant, 24-h exclusion zones** (rows true, columns predicted, summed over folds)

| | PersLow | PersNorm | PersHigh |
|---|---|---|---|
| PersLow | 208 | 254 | 90 |
| PersNorm | 118 | 343 | 120 |
| PersHigh | 76 | 256 | 267 |
