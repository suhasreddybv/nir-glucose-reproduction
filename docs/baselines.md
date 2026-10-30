# Baselines the paper did not report, and the labels

Decision-log entries D-011 and D-012; every table is generated from `results/` and pinned by `tests/test_results_baselines.py`. *B0* is the population mean; *B1* the participant's own mean over their training portion (first half, or first 70 % under the time-blocked regime); *B2* a linear model on HbA1c and sex; *B3* a per-participant ridge regression on the 45 wrist (E4) features.

Protocol §8, run before any model exists (D-012). The paper says both of its XGBoost models "outperformed the naïve models (mean and median)" and gives no number for them. These are those numbers, per participant with n, under the paper's own two regimes and under the time-blocked one. Every figure is read from `results/baselines_summary.csv` and `results/baselines_per_participant.csv` by the test that pins this section.

| Regime | Baseline | Participants | Rows | RMSE mean ± SD [95 % CI over participants] | MAPE | "Accuracy" (100 − MAPE) | Clarke A+B | Paper's model |
|---|---|---|---|---|---|---|---|---|
| Paper's population regime: leave-one-person-out | B0 population mean | 16 | 28,964 | **22.47** ± 4.12 [20.44, 24.49] | 15.20 % | 84.80 % | 99.2 % | 21.22 ± 4.14 (XGBoost, LOPO) |
| Paper's population regime: leave-one-person-out | B2 linear on HbA1c + sex | 16 | 28,964 | **21.47** ± 3.94 [19.49, 23.40] | 14.41 % | 85.59 % | 99.2 % | 21.22 ± 4.14 (XGBoost, LOPO) |
| Paper's personalised regime: first half → second half | B0 population mean | 16 | 14,486 | **22.22** ± 5.65 [19.48, 25.02] | 14.33 % | 85.67 % | 99.2 % | 21.10 ± 4.50 (XGBoost, personalised) |
| Paper's personalised regime: first half → second half | B1 per-participant mean (own training portion) | 16 | 14,486 | **20.99** ± 4.17 [19.04, 23.08] | 13.03 % | 86.97 % | 99.2 % | 21.10 ± 4.50 (XGBoost, personalised) |
| Paper's personalised regime: first half → second half | B2 linear on HbA1c + sex | 16 | 14,486 | **21.38** ± 4.69 [19.18, 23.77] | 13.48 % | 86.52 % | 99.2 % | 21.10 ± 4.50 (XGBoost, personalised) |
| Paper's personalised regime: first half → second half | B3 per-participant linear on the 45 E4 features | 16 | 13,096 | **22.00** ± 4.66 [19.77, 24.35] | 13.55 % | 86.45 % | 99.4 % | 21.10 ± 4.50 (XGBoost, personalised) |
| Paper's personalised regime: first half → second half | B1 on B3's rows | 16 | 13,096 | **20.83** ± 4.18 [18.89, 22.93] | 12.74 % | 87.26 % | 99.2 % | 21.10 ± 4.50 (XGBoost, personalised) |
| Time-blocked: first 70 % → last 30 %, 24-h exclusion zones | B0 population mean | 15 | 4,826 | **22.77** ± 8.52 [18.76, 27.20] | 14.66 % | 85.34 % | 98.9 % | — |
| Time-blocked: first 70 % → last 30 %, 24-h exclusion zones | B1 per-participant mean (own training portion) | 15 | 4,826 | **21.15** ± 7.44 [17.63, 25.17] | 12.67 % | 87.33 % | 98.9 % | — |
| Time-blocked: first 70 % → last 30 %, 24-h exclusion zones | B2 linear on HbA1c + sex | 15 | 4,826 | **21.22** ± 7.52 [17.63, 25.25] | 13.04 % | 86.97 % | 98.9 % | — |
| Time-blocked: first 70 % → last 30 %, 24-h exclusion zones | B3 per-participant linear on the 45 E4 features | 15 | 4,364 | **23.57** ± 7.73 [19.91, 27.70] | 13.68 % | 86.32 % | 99.1 % | — |
| Time-blocked: first 70 % → last 30 %, 24-h exclusion zones | B1 on B3's rows | 15 | 4,364 | **20.98** ± 7.63 [17.39, 25.04] | 12.37 % | 87.63 % | 99.0 % | — |

**Read it this way.** A constant per participant — the mean of that participant's own first half — scores an RMSE of 20.99 ± 4.17 mg/dL and an "accuracy" of 86.97 % where the paper's personalised XGBoost scored 21.10 ± 4.50 and 86.74 %. Across participants, a two-number linear model on HbA1c and sex scores 21.47 ± 3.94 where the paper's population XGBoost scored 21.22 ± 4.14. The per-participant linear model on the 45 wrist features (B3) is **worse** than the per-participant mean on the same rows under both within-participant regimes (22.00 vs 20.83; 23.57 vs 20.98): on this cohort the wrist features add error to a constant. Under the time-blocked regime the ordering is the same and every interval is wider, because 8,081 of the 28,964 epochs fall inside the 24-h exclusion zones and participant 015's record has nothing beyond its zone (15 participants).

| Participant | Second-half n | B1 RMSE | B1 MAPE | B1 "accuracy" | B2 RMSE (LOPO) | B3 RMSE (n) | B1 on B3's rows |
|---|---|---|---|---|---|---|---|
| 001 | 1,031 | 19.01 | 12.07 % | 87.93 % | 16.42 | 19.75 (1,007) | 19.09 |
| 002 | 941 | 19.55 | 12.67 % | 87.33 % | 23.62 | 19.96 (932) | 19.54 |
| 003 | 699 | 15.67 | 11.55 % | 88.44 % | 18.36 | 16.65 (602) | 15.07 |
| 004 | 682 | 20.24 | 12.16 % | 87.84 % | 19.46 | 24.13 (606) | 19.85 |
| 005 | 1,197 | 15.54 | 13.22 % | 86.78 % | 15.90 | 14.22 (1,127) | 15.42 |
| 006 | 822 | 25.87 | 13.84 % | 86.16 % | 28.78 | 25.67 (675) | 26.61 |
| 007 | 1,036 | 22.04 | 19.26 % | 80.74 % | 22.44 | 21.49 (987) | 22.03 |
| 008 | 1,075 | 19.47 | 11.00 % | 89.00 % | 19.00 | 18.74 (996) | 18.55 |
| 009 | 1,048 | 25.49 | 14.96 % | 85.04 % | 24.21 | 28.34 (943) | 25.55 |
| 010 | 1,016 | 31.45 | 18.97 % | 81.03 % | 28.36 | 34.29 (813) | 30.28 |
| 011 | 1,085 | 23.01 | 13.89 % | 86.11 % | 25.34 | 20.66 (993) | 23.23 |
| 012 | 969 | 16.24 | 8.67 % | 91.33 % | 19.09 | 22.04 (764) | 15.85 |
| 013 | 941 | 23.52 | 11.25 % | 88.75 % | 23.52 | 25.36 (857) | 23.34 |
| 014 | 780 | 23.03 | 13.43 % | 86.57 % | 21.34 | 21.72 (670) | 23.11 |
| 015 | 249 | 17.98 | 10.40 % | 89.60 % | 15.74 | 18.38 (248) | 18.00 |
| 016 | 915 | 17.71 | 11.20 % | 88.80 % | 21.99 | 20.57 (876) | 17.83 |

**P1a, P2a and P4 were judged here before any model existed**; the full verdict table, with P1b, P2b, P3 and P5, is on the [front page](../README.md#the-five-predictions).

**The labels** (`results/labels.csv`, `results/label_distribution.csv`, `results/balanced_set.csv`, D-011). PersHigh / PersLow / PersNorm from the trailing 24-h mean ± 1 SD of each participant's own CGM (protocol cell 7 d) label 36,722 of 36,898 readings (all labelled readings, usable epoch or not): PersLow 5,206 (14.2%), PersNorm 25,854 (70.4%), PersHigh 5,662 (15.4%). The three class distributions land on the paper's Table 1: PersNorm 111.8 ± 14.6 mg/dL (paper 112.4 ± 14.5), PersHigh 148.5 ± 25.7 (149.9 ± 24.4), PersLow 91.0 ± 11.6 (90.8 ± 11.1). Undersampling every class to the smallest on the 25,644 complete labelled epochs gives a balanced set of **N = 10,230** (3 × 3,410) against the paper's 8,666; the difference is the size of the complete set, not the rule.
