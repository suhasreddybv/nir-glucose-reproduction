# The paper's regression model, reproduced and set against the baselines

Decision-log entries D-013, D-014 and D-017; every table is generated from `results/` and pinned by `tests/test_results_models.py`. *LOPO*: leave one person out. *B1*: the participant's own training mean. *B2*: a linear model on HbA1c and sex. *E4*: the Empatica E4 wristband (the 45 wrist features).

Protocol cell 4 and §9, run after the baselines (D-014): XGBoost with max depth 6, 100 estimators and learning rate 0.1, after a 1,000-tree random-forest selection at the 0.005 importance cut-off inside each training fold, under the paper's two regimes and the time-blocked one, with five ablations — one more than protocol §9 named, and with the two clock features kept in "E4 only" and "food log only" (a deviation logged in D-017). Every model is scored on exactly the rows the baselines were, and the paired columns are baseline − model per participant (positive means the model is better) against the baseline the regime makes available (B2 across participants, B1 within), with a bootstrap over participants (16; 15 under the time-blocked regime). Generated from `results/models_summary.csv` and `results/paired_deltas.csv`.

| Regime | Model | Participants | Rows | RMSE mean ± SD [95 % CI] | MAPE | "Accuracy" | Features kept (mean) | Baseline − model RMSE, mean [95 % CI]; positive = model better | Participants where the model is better | Paper |
|---|---|---|---|---|---|---|---|---|---|---|
| LOPO (paper's population regime) | full model, 69 features | 16 | 28,964 | **21.29** ± 4.00 [19.33, 23.16] | 14.34 % | 85.66 % | 45.1 | B2: +0.19 [-0.63, +1.12] | 6 / 16 | 21.22 ± 4.14 |
| LOPO (paper's population regime) | minus the food log (50) | 16 | 28,964 | **22.50** ± 3.99 [20.52, 24.48] | 15.06 % | 84.94 % | 47.7 | B2: -1.03 [-1.75, -0.32] | 3 / 16 |  |
| LOPO (paper's population regime) | minus sex, HbA1c, ID (66) | 16 | 28,964 | **21.39** ± 3.80 [19.58, 23.20] | 14.41 % | 85.59 % | 43.8 | B2: +0.08 [-1.01, +1.27] | 7 / 16 |  |
| LOPO (paper's population regime) | minus all E4 (wrist) features (24) | 16 | 28,964 | **22.93** ± 3.69 [21.16, 24.68] | 15.65 % | 84.35 % | 21.9 | B2: -1.45 [-2.66, -0.20] | 6 / 16 |  |
| LOPO (paper's population regime) | E4 (wrist) features + clock only (47) | 16 | 28,964 | **23.22** ± 3.39 [21.58, 24.88] | 15.72 % | 84.28 % | 45.0 | B2: -1.75 [-2.59, -0.78] | 3 / 16 |  |
| LOPO (paper's population regime) | food log + clock only (21) | 16 | 28,964 | **22.50** ± 4.14 [20.52, 24.52] | 15.37 % | 84.63 % | 19.0 | B2: -1.02 [-2.31, +0.26] | 6 / 16 |  |
| first half → second half (paper's personalised regime) | full model, 69 features | 16 | 14,486 | **22.35** ± 3.86 [20.44, 24.17] | 13.68 % | 86.33 % | 33.9 | B1: -1.36 [-3.34, +0.46] | 9 / 16 | 21.10 ± 4.50 |
| first half → second half (paper's personalised regime) | minus the food log (50) | 16 | 14,486 | **22.72** ± 4.34 [20.64, 24.79] | 14.25 % | 85.75 % | 32.5 | B1: -1.73 [-3.46, -0.13] | 5 / 16 |  |
| first half → second half (paper's personalised regime) | minus sex, HbA1c, ID (66) | 16 | 14,486 | **22.27** ± 3.84 [20.40, 24.07] | 13.59 % | 86.41 % | 33.9 | B1: -1.28 [-3.25, +0.52] | 9 / 16 |  |
| first half → second half (paper's personalised regime) | minus all E4 (wrist) features (24) | 16 | 14,486 | **22.52** ± 2.82 [21.20, 23.88] | 14.18 % | 85.82 % | 16.1 | B1: -1.53 [-3.15, -0.02] | 6 / 16 |  |
| first half → second half (paper's personalised regime) | E4 (wrist) features + clock only (47) | 16 | 14,486 | **22.65** ± 4.15 [20.64, 24.63] | 14.18 % | 85.82 % | 32.5 | B1: -1.66 [-3.42, -0.08] | 5 / 16 |  |
| first half → second half (paper's personalised regime) | food log + clock only (21) | 16 | 14,486 | **22.48** ± 2.80 [21.17, 23.85] | 14.15 % | 85.84 % | 16.1 | B1: -1.50 [-3.13, +0.01] | 6 / 16 |  |
| time-blocked, 24-h exclusion zones | full model, 69 features | 15 | 4,826 | **22.53** ± 7.21 [19.22, 26.34] | 13.91 % | 86.09 % | 35.6 | B1: -1.38 [-3.50, +0.71] | 6 / 15 | — |
| time-blocked, 24-h exclusion zones | minus the food log (50) | 15 | 4,826 | **22.85** ± 5.89 [20.00, 25.98] | 14.71 % | 85.30 % | 32.3 | B1: -1.71 [-3.67, +0.24] | 4 / 15 |  |
| time-blocked, 24-h exclusion zones | minus sex, HbA1c, ID (66) | 15 | 4,826 | **22.43** ± 7.12 [19.18, 26.15] | 13.89 % | 86.11 % | 35.3 | B1: -1.28 [-3.42, +0.80] | 6 / 15 |  |
| time-blocked, 24-h exclusion zones | minus all E4 (wrist) features (24) | 15 | 4,826 | **22.67** ± 7.40 [19.36, 26.91] | 14.06 % | 85.94 % | 17.5 | B1: -1.52 [-2.65, -0.38] | 4 / 15 |  |
| time-blocked, 24-h exclusion zones | E4 (wrist) features + clock only (47) | 15 | 4,826 | **22.87** ± 5.87 [20.01, 26.05] | 14.77 % | 85.23 % | 32.2 | B1: -1.72 [-3.68, +0.22] | 4 / 15 |  |
| time-blocked, 24-h exclusion zones | food log + clock only (21) | 15 | 4,826 | **22.63** ± 7.45 [19.29, 26.86] | 14.05 % | 85.95 % | 17.5 | B1: -1.48 [-2.62, -0.35] | 4 / 15 |  |

**Read it this way.** Under leave-one-person-out the full model lands on the paper: **21.29 ± 4.00 against the paper's 21.22 ± 4.14**, with 45 of 69 features kept on average. Its paired advantage over the two-number HbA1c-and-sex model is **+0.19 mg/dL [−0.63, +1.12]**, better in 6 of 16 participants: the 67 other features, 45 of them from the wrist, add nothing to a constant per participant that the bootstrap can see. Under the paper's personalised regime the full model scores **22.35 against the paper's 21.10** and is **worse than its own participant's first-half mean by 1.36 mg/dL [−3.34, +0.46]**; under the time-blocked regime, worse by 1.38 [−3.50, +0.71]. Every ablation but one is worse than the baseline on the mean; the exception is the model without sex, HbA1c and ID under LOPO (21.39 against B2's 21.47, +0.08 [−1.01, +1.27]). The model with E4 features and the clock alone is the worst of all under LOPO (23.22, −1.75 [−2.59, −0.78] against B2). Per participant under the personalised regime the full model is better for 9 of 16 (median paired gain +0.30 mg/dL); its mean is pulled down by 015, 012 and 003, for whom it is 7.4–10.5 mg/dL worse. Removing the food log costs 1.22 mg/dL under LOPO and removing the wrist costs 1.64; within participant the two costs are 0.37 and 0.17 — the P5 measurement goes one way across participants and the other within, and both are small beside the 4-mg/dL spread between participants.

| Participant | LOPO n | B2 RMSE | XGBoost RMSE | B2 − model | Second-half n | B1 RMSE | personalised XGBoost RMSE | B1 − model | Time-blocked n | B1 RMSE | XGBoost RMSE | B1 − model |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 001 | 2,062 | 16.42 | 16.71 | -0.29 | 1,031 | 19.01 | 19.71 | -0.70 | 383 | 15.03 | 15.37 | -0.34 |
| 002 | 1,882 | 23.62 | 24.26 | -0.64 | 941 | 19.55 | 19.02 | +0.53 | 286 | 23.74 | 22.44 | +1.30 |
| 003 | 1,398 | 18.36 | 18.86 | -0.49 | 699 | 15.67 | 23.07 | -7.40 | 279 | 15.40 | 18.11 | -2.71 |
| 004 | 1,364 | 19.46 | 18.16 | +1.30 | 682 | 20.24 | 21.82 | -1.58 | 129 | 9.54 | 14.22 | -4.68 |
| 005 | 2,394 | 15.90 | 14.10 | +1.80 | 1,197 | 15.54 | 15.01 | +0.53 | 462 | 17.22 | 14.83 | +2.39 |
| 006 | 1,643 | 28.78 | 23.39 | +5.38 | 822 | 25.87 | 24.70 | +1.17 | 216 | 13.45 | 18.90 | -5.46 |
| 007 | 2,071 | 22.44 | 24.40 | -1.96 | 1,036 | 22.04 | 22.11 | -0.07 | 401 | 26.43 | 24.26 | +2.17 |
| 008 | 2,150 | 19.00 | 17.23 | +1.77 | 1,075 | 19.47 | 17.79 | +1.68 | 449 | 19.34 | 13.91 | +5.43 |
| 009 | 2,095 | 24.21 | 26.60 | -2.39 | 1,048 | 25.49 | 24.71 | +0.78 | 345 | 25.86 | 25.66 | +0.20 |
| 010 | 2,031 | 28.36 | 29.04 | -0.68 | 1,016 | 31.45 | 31.39 | +0.07 | 347 | 41.16 | 43.34 | -2.18 |
| 011 | 2,170 | 25.34 | 24.03 | +1.31 | 1,085 | 23.01 | 20.95 | +2.06 | 411 | 28.13 | 24.19 | +3.94 |
| 012 | 1,937 | 19.09 | 19.50 | -0.41 | 969 | 16.24 | 25.18 | -8.94 | 293 | 16.16 | 25.90 | -9.74 |
| 013 | 1,882 | 23.52 | 22.57 | +0.95 | 941 | 23.52 | 21.81 | +1.71 | 284 | 23.57 | 24.04 | -0.47 |
| 014 | 1,559 | 21.34 | 23.00 | -1.67 | 780 | 23.03 | 20.61 | +2.42 | 275 | 23.38 | 25.77 | -2.39 |
| 015 | 497 | 15.74 | 16.39 | -0.66 | 249 | 17.98 | 28.46 | -10.48 | — | — | — | — |
| 016 | 1,829 | 21.99 | 22.31 | -0.32 | 915 | 17.71 | 21.26 | -3.55 | 266 | 18.81 | 26.96 | -8.16 |

**Feature importance reproduces** (`results/selected_features.csv`): 14 of the paper's 15 most important features (Table 3) are in this reproduction's top 15 by the same random-forest importance averaged over the LOPO folds, with minutes from midnight first in both. The ranking is the paper's; it just does not translate into error below a constant.

| Rank | Feature (this reproduction) | RF importance mean ± SD over 16 LOPO folds | Selected in folds | Paper's Table 3 at this rank |
|---|---|---|---|---|
| 1 | Minfrommid | 0.067 ± 0.005 | 16 / 16 | Minutes from midnight |
| 2 | Biological Sex | 0.063 ± 0.032 | 16 / 16 | Sugar intake (previous 24 h) |
| 3 | HbA1c | 0.062 ± 0.021 | 16 / 16 | Hemoglobin A1c (HbA1c) |
| 4 | carbs2hr | 0.052 ± 0.019 | 16 / 16 | Carbohydrates (previous 2 h) |
| 5 | Activity24 | 0.041 ± 0.004 | 16 / 16 | Biological sex |
| 6 | sugar2hr | 0.041 ± 0.021 | 16 / 16 | Activity (previous 24 h) |
| 7 | sugar24hr | 0.038 ± 0.031 | 16 / 16 | Sugar intake (previous 2 h) |
| 8 | ID | 0.038 ± 0.015 | 16 / 16 | Sugar intake (previous 8 h) |
| 9 | sugar8hr | 0.035 ± 0.006 | 16 / 16 | Accelerometry (mean previous 2 h) |
| 10 | Eatmean24hr | 0.032 ± 0.004 | 16 / 16 | Wake time |
| 11 | PeakEDA2hr_mean | 0.031 ± 0.010 | 16 / 16 | ID |
| 12 | ACC_mean_2hrs | 0.027 ± 0.003 | 16 / 16 | Accelerometry (max previous 2 h) |
| 13 | ACC_max_2hrs | 0.027 ± 0.003 | 16 / 16 | Protein (previous 24 h) |
| 14 | WakeTime | 0.027 ± 0.005 | 16 / 16 | Peak electrodermal activity (mean previous 2 h) |
| 15 | protein24hr | 0.023 ± 0.003 | 16 / 16 | Carbohydrates (previous 24 h) |

The verdicts on all five predictions are on the [front page](../README.md#the-five-predictions).
