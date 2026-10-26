# nir-glucose-reproduction

A reproduction of Bent, Cho, Henriquez et al. (2021), *Engineering digital biomarkers of interstitial glucose from noninvasive smartwatches* (npj Digital Medicine 4:89), on the dataset they released: what replicates under the paper's own evaluation, what survives a time-blocked split, and the baselines the paper did not report.

**Result.** _Regression judged; classification (Wednesday) pending. **The paper's regression numbers reproduce — 21.29 against 21.22 mg/dL under leave-one-person-out — and they are the numbers a constant achieves on this cohort.** A linear model on HbA1c and sex alone scores 21.47 across participants and the per-participant first-half mean scores 20.99 within; the 69-feature XGBoost beats the first by 0.19 mg/dL [−0.63, +1.12] and loses to the second by 1.36 [−3.34, +0.46]. Every ablation is worse than the baselines; the wrist features alone are the worst of all. The feature-importance ranking reproduces (14 of the paper's top 15). Five of the six pre-registered verdicts are in (P1a/b, P2a/b, P4 held; P5 measured both ways); P3 waits for the classification. Protocol frozen at `7860469db2e059bd` and verified before any fit._

## What is fixed before anything is fitted

- **The paper's own design, transcribed** (protocol §1–§7): three-class PersHigh / PersLow / PersNorm classification by a decision tree under a repeated stratified 10-fold × 3 split **of windows, not of participants and not of time**; XGBoost regression under leave-one-person-out (population) and first-half / second-half (personalised). The inputs are the wrist (ACC, EDA, TEMP, Empatica HR and IBI), the **food log** (19 of the 69 features), HbA1c, sex and a participant-ID feature; **lagged glucose is never an input**, so the models estimate glucose from non-glucose signals and persistence is not a comparator.
- **Four baselines the paper did not report** (§8): population mean; per-participant mean over the training half; an HbA1c-and-sex linear model; a per-participant linear model on the E4 features alone. The paper says its models beat the naive mean and median predictors and gives no number for them.
- **Three split regimes, always side by side** (§9): the paper's; participant-grouped folds; time-blocked within participant with no window within 24 h of the boundary, because the classification label is a 24-h rolling statistic.
- **Five predictions written before any number** (§11, D-009), judged against their frozen wording: the per-participant mean lands within 3 mg/dL of the paper's personalised RMSE and the model beats it by less than 3 (P1); likewise the population mean or the HbA1c-and-sex model against the LOPO RMSE (P2); the classification reproduces within 3 points under the paper's split and falls by more than 15 under the other two (P3); the per-participant mean's "accuracy" exceeds 84 % from a constant (P4); and whether the food log or the wrist costs more when removed (P5, a measurement).
- **Evaluation** (§10): real CGM readings only; no feature uses a CGM value or any sample at or after the target, and a test perturbs everything from the target onward to prove it; the clinical scorer and the iCGM analogue module vendored unchanged from [`cgm-forecast-conformal`](https://github.com/suhasreddybv/cgm-forecast-conformal) with their tests; per participant with n; bootstrap over 16 participants, wide and stated.

## The data

BIG IDEAs Lab Glycemic Variability and Wearable Device Data, PhysioNet v1.1.3 ([data/README.md](data/README.md)): 16 participants with HbA1c 5.3–6.4% — a high-normal cohort — wearing an Empatica E4 (BVP 64 Hz, ACC 32 Hz, EDA and TEMP 4 Hz, Empatica-derived HR and IBI) with a Dexcom G6 every five minutes and a food log, 8–10 days each. Open Data Commons Attribution licence; this repository's own policy keeps every raw file, cache and per-participant trace out of the tree regardless (D-002).

Every file is verified against the dataset's `SHA256SUMS.txt` before it is read, and the loader asserts what the protocol rests on rather than assuming it: the accelerometer is in 1/64 g (median raw magnitude ≈ 64, ≈ 1 g after scaling), BVP is zero-centred, the Dexcom stream is strictly increasing and censored to 40–400 mg/dL, and each participant's date-shifted E4 and Dexcom files overlap (D-005). All 130 files verified against the dataset's checksum list. Three things the description does not say were found on the way in: participant 015's E4 files are two recordings concatenated out of order (sorted, counted, nothing dropped); participant 001's HR file carries timestamps to the minute only (expanded to seconds by file order); and the food logs come in three schemas, one of them headerless with inferred columns (D-005).

**Coverage and the glucose distribution** (`results/coverage.csv`, `results/glucose_distribution.csv`). **28,592 of 36,898 Dexcom readings have a complete 10-minute E4 window before them**, over 3078 h of E4–Dexcom overlap. **Pooled, 0.57% of readings are below 70 mg/dL and 1.78% above 180**; participant means run 93–130 mg/dL with SDs of 15–29. That narrowness is the central fact of the reproduction: a per-participant mean is within one SD of almost every reading, and a pooled regression metric on this cohort is driven by the spread of participant means rather than by excursions — which is what a within-participant random split lets a model learn and read back (D-006).

**The epochs and the 69 features** (`results/epochs.csv`, `results/feature_missingness.csv`, D-010). Under the frozen rule — the five minutes before each reading, with ACC, EDA, TEMP and HR each present — **28,964 of 36,898 readings have a usable epoch, and all 69 features are present on 25,644 of them**, against the paper's "over 25,000". An unusable epoch is the watch being off, not one channel dropping out: the four channels' missing counts agree within one epoch in every participant. The HRV metrics are missing on 8.9 % of usable epochs (fewer than two Empatica inter-beat intervals), the wake-time feature on 2.5 % (before a day's first confirmed wake); the four skews and HR_Std on under 2 %; the other 55 features are never missing.

| Participant | HbA1c | E4 worn (h) | Dexcom readings (coverage) | Overlap (h) | Readings with a complete 10-min E4 window | Glucose mean ± SD | min–max | < 70 | > 180 |
|---|---|---|---|---|---|---|---|---|---|
| 001 | 5.5 | 176 | 2,561 (99%) | 216 | 2,041 (80%) | 106 ± 16 | 46–155 | 0.9% | 0.0% |
| 002 | 5.6 | 175 | 2,119 (93%) | 190 | 1,859 (88%) | 130 ± 21 | 83–200 | 0.0% | 1.5% |
| 003 | 5.9 | 116 | 2,302 (100%) | 185 | 1,374 (60%) | 108 ± 18 | 60–197 | 0.7% | 0.8% |
| 004 | 6.4 | 125 | 2,164 (96%) | 188 | 1,332 (62%) | 113 ± 18 | 58–189 | 0.2% | 0.7% |
| 005 | 5.7 | 202 | 2,558 (100%) | 214 | 2,350 (92%) | 105 ± 15 | 70–181 | 0.0% | 0.0% |
| 006 | 5.8 | 139 | 2,847 (100%) | 237 | 1,622 (57%) | 125 ± 29 | 79–222 | 0.0% | 7.3% |
| 007 | 5.3 | 180 | 2,207 (97%) | 190 | 2,042 (92%) | 93 ± 18 | 46–192 | 4.0% | 0.4% |
| 008 | 5.6 | 185 | 2,505 (98%) | 214 | 2,126 (85%) | 111 ± 18 | 40–180 | 1.3% | 0.0% |
| 009 | 6.1 | 176 | 2,306 (100%) | 192 | 2,074 (90%) | 128 ± 24 | 77–237 | 0.0% | 4.3% |
| 010 | 6.0 | 181 | 2,148 (94%) | 190 | 2,007 (93%) | 112 ± 29 | 49–261 | 1.6% | 4.4% |
| 011 | 6.0 | 184 | 2,843 (100%) | 238 | 2,139 (75%) | 120 ± 25 | 71–209 | 0.0% | 2.2% |
| 012 | 5.6 | 166 | 2,169 (98%) | 184 | 1,923 (89%) | 122 ± 20 | 75–193 | 0.0% | 1.5% |
| 013 | 5.7 | 194 | 1,979 (100%) | 165 | 1,856 (94%) | 128 ± 23 | 83–235 | 0.0% | 2.9% |
| 014 | 5.5 | 131 | 2,240 (100%) | 156 | 1,540 (69%) | 116 ± 21 | 70–220 | 0.0% | 1.2% |
| 015 | 5.5 | 97 | 1,673 (75%) | 138 | 491 (29%) | 109 ± 15 | 42–177 | 0.4% | 0.0% |
| 016 | 5.5 | 155 | 2,277 (99%) | 180 | 1,816 (80%) | 106 ± 17 | 63–175 | 0.3% | 0.0% |


## Baselines the paper did not report

Protocol §8, run before any model exists (D-012). The paper says both of its XGBoost models "outperformed the naïve models (mean and median)" and gives no number for them. These are those numbers, per participant with n, under the paper's own two regimes and under the time-blocked one. Every figure is read from `results/baselines_summary.csv` and `results/baselines_per_participant.csv` by the test that pins this section.

| Regime | Baseline | Participants | Rows | RMSE mean ± SD [95 % CI over participants] | MAPE | "Accuracy" (100 − MAPE) | Clarke A+B | Paper's model |
|---|---|---|---|---|---|---|---|---|
| Paper's population regime: leave-one-person-out | B0 population mean | 16 | 28,964 | **22.47** ± 4.12 [20.44, 24.49] | 15.20 % | 84.80 % | 99.2 % | 21.22 ± 4.14 (XGBoost, LOPO) |
| Paper's population regime: leave-one-person-out | B2 linear on HbA1c + sex | 16 | 28,964 | **21.47** ± 3.94 [19.49, 23.40] | 14.41 % | 85.59 % | 99.2 % | 21.22 ± 4.14 (XGBoost, LOPO) |
| Paper's personalised regime: first half → second half | B0 population mean | 16 | 14,486 | **22.22** ± 5.65 [19.48, 25.02] | 14.33 % | 85.67 % | 99.2 % | 21.10 ± 4.50 (XGBoost, personalised) |
| Paper's personalised regime: first half → second half | B1 per-participant mean (training half) | 16 | 14,486 | **20.99** ± 4.17 [19.04, 23.08] | 13.03 % | 86.97 % | 99.2 % | 21.10 ± 4.50 (XGBoost, personalised) |
| Paper's personalised regime: first half → second half | B2 linear on HbA1c + sex | 16 | 14,486 | **21.38** ± 4.69 [19.18, 23.77] | 13.48 % | 86.52 % | 99.2 % | 21.10 ± 4.50 (XGBoost, personalised) |
| Paper's personalised regime: first half → second half | B3 per-participant linear on the 45 E4 features | 16 | 13,096 | **22.00** ± 4.66 [19.77, 24.35] | 13.55 % | 86.45 % | 99.4 % | 21.10 ± 4.50 (XGBoost, personalised) |
| Paper's personalised regime: first half → second half | B1 on B3's rows | 16 | 13,096 | **20.83** ± 4.18 [18.89, 22.93] | 12.74 % | 87.26 % | 99.2 % | 21.10 ± 4.50 (XGBoost, personalised) |
| Time-blocked: first 70 % → last 30 %, 24-h exclusion zones | B0 population mean | 15 | 4,826 | **22.77** ± 8.52 [18.76, 27.20] | 14.66 % | 85.34 % | 98.9 % | — |
| Time-blocked: first 70 % → last 30 %, 24-h exclusion zones | B1 per-participant mean (training half) | 15 | 4,826 | **21.15** ± 7.44 [17.63, 25.17] | 12.67 % | 87.33 % | 98.9 % | — |
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

**P1a, P2a and P4 were judged here before any model existed**; the full verdict table, with P1b, P2b, P3 and P5, is in the model section below.

**The labels** (`results/labels.csv`, `results/label_distribution.csv`, `results/balanced_set.csv`, D-011). PersHigh / PersLow / PersNorm from the trailing 24-h mean ± 1 SD of each participant's own CGM (protocol cell 7 d) label 36,722 of 36,898 readings: PersLow 5,206 (14.2%), PersNorm 25,854 (70.4%), PersHigh 5,662 (15.4%). The three class distributions land on the paper's Table 1: PersNorm 111.8 ± 14.6 mg/dL (paper 112.4 ± 14.5), PersHigh 148.5 ± 25.7 (149.9 ± 24.4), PersLow 91.0 ± 11.6 (90.8 ± 11.1). Undersampling every class to the smallest on the 25,644 complete labelled epochs gives a balanced set of **N = 10,230** (3 × 3,410) against the paper's 8,666; the difference is the size of the complete set, not the rule.

## The paper's model, reproduced and set against the baselines

Protocol cell 4 and §9, run after the baselines (D-014): XGBoost with max depth 6, 100 estimators and learning rate 0.1, after a 1,000-tree random-forest selection at the 0.005 importance cut-off inside each training fold, under the paper's two regimes and the time-blocked one, with five ablations. Every model is scored on exactly the rows the baselines were, and the last two columns are the paired per-participant RMSE difference against the baseline the regime makes available (B2 across participants, B1 within), with the 16-participant bootstrap. Generated from `results/models_summary.csv` and `results/paired_deltas.csv`.

| Regime | Model | Participants | Rows | RMSE mean ± SD [95 % CI] | MAPE | "Accuracy" | Features kept (mean) | Baseline − model RMSE, mean [95 % CI] | Participants where the model is better | Paper |
|---|---|---|---|---|---|---|---|---|---|---|
| LOPO (paper's population regime) | full model, 69 features | 16 | 28,964 | **21.29** ± 4.00 [19.33, 23.16] | 14.34 % | 85.66 % | 45.1 | B2: +0.19 [-0.63, +1.12] | 6 / 16 | 21.22 ± 4.14 |
| LOPO (paper's population regime) | minus the food log (50) | 16 | 28,964 | **22.50** ± 3.99 [20.52, 24.48] | 15.06 % | 84.94 % | 47.7 | B2: -1.03 [-1.75, -0.32] | 3 / 16 |  |
| LOPO (paper's population regime) | minus sex, HbA1c, ID (66) | 16 | 28,964 | **21.39** ± 3.80 [19.58, 23.20] | 14.41 % | 85.59 % | 43.8 | B2: +0.08 [-1.01, +1.27] | 7 / 16 |  |
| LOPO (paper's population regime) | minus all E4 features (24) | 16 | 28,964 | **22.93** ± 3.69 [21.16, 24.68] | 15.65 % | 84.35 % | 21.9 | B2: -1.45 [-2.66, -0.20] | 6 / 16 |  |
| LOPO (paper's population regime) | E4 features + clock only (47) | 16 | 28,964 | **23.22** ± 3.39 [21.58, 24.88] | 15.72 % | 84.28 % | 45.0 | B2: -1.75 [-2.59, -0.78] | 3 / 16 |  |
| LOPO (paper's population regime) | food log + clock only (21) | 16 | 28,964 | **22.50** ± 4.14 [20.52, 24.52] | 15.37 % | 84.63 % | 19.0 | B2: -1.02 [-2.31, +0.26] | 6 / 16 |  |
| first half → second half (paper's personalised regime) | full model, 69 features | 16 | 14,486 | **22.35** ± 3.86 [20.44, 24.17] | 13.68 % | 86.33 % | 33.9 | B1: -1.36 [-3.34, +0.46] | 9 / 16 | 21.10 ± 4.50 |
| first half → second half (paper's personalised regime) | minus the food log (50) | 16 | 14,486 | **22.72** ± 4.34 [20.64, 24.79] | 14.25 % | 85.75 % | 32.5 | B1: -1.73 [-3.46, -0.13] | 5 / 16 |  |
| first half → second half (paper's personalised regime) | minus sex, HbA1c, ID (66) | 16 | 14,486 | **22.27** ± 3.84 [20.40, 24.07] | 13.59 % | 86.41 % | 33.9 | B1: -1.28 [-3.25, +0.52] | 9 / 16 |  |
| first half → second half (paper's personalised regime) | minus all E4 features (24) | 16 | 14,486 | **22.52** ± 2.82 [21.20, 23.88] | 14.18 % | 85.82 % | 16.1 | B1: -1.53 [-3.15, -0.02] | 6 / 16 |  |
| first half → second half (paper's personalised regime) | E4 features + clock only (47) | 16 | 14,486 | **22.65** ± 4.15 [20.64, 24.63] | 14.18 % | 85.82 % | 32.5 | B1: -1.66 [-3.42, -0.08] | 5 / 16 |  |
| first half → second half (paper's personalised regime) | food log + clock only (21) | 16 | 14,486 | **22.48** ± 2.80 [21.17, 23.85] | 14.15 % | 85.84 % | 16.1 | B1: -1.50 [-3.13, +0.01] | 6 / 16 |  |
| time-blocked, 24-h exclusion zones | full model, 69 features | 15 | 4,826 | **22.53** ± 7.21 [19.22, 26.34] | 13.91 % | 86.09 % | 35.6 | B1: -1.38 [-3.50, +0.71] | 6 / 15 | — |
| time-blocked, 24-h exclusion zones | minus the food log (50) | 15 | 4,826 | **22.85** ± 5.89 [20.00, 25.98] | 14.71 % | 85.30 % | 32.3 | B1: -1.71 [-3.67, +0.24] | 4 / 15 |  |
| time-blocked, 24-h exclusion zones | minus sex, HbA1c, ID (66) | 15 | 4,826 | **22.43** ± 7.12 [19.18, 26.15] | 13.89 % | 86.11 % | 35.3 | B1: -1.28 [-3.42, +0.80] | 6 / 15 |  |
| time-blocked, 24-h exclusion zones | minus all E4 features (24) | 15 | 4,826 | **22.67** ± 7.40 [19.36, 26.91] | 14.06 % | 85.94 % | 17.5 | B1: -1.52 [-2.65, -0.38] | 4 / 15 |  |
| time-blocked, 24-h exclusion zones | E4 features + clock only (47) | 15 | 4,826 | **22.87** ± 5.87 [20.01, 26.05] | 14.77 % | 85.23 % | 32.2 | B1: -1.72 [-3.68, +0.22] | 4 / 15 |  |
| time-blocked, 24-h exclusion zones | food log + clock only (21) | 15 | 4,826 | **22.63** ± 7.45 [19.29, 26.86] | 14.05 % | 85.95 % | 17.5 | B1: -1.48 [-2.62, -0.35] | 4 / 15 |  |

**Read it this way.** Under leave-one-person-out the full model lands on the paper: **21.29 ± 4.00 against the paper's 21.22 ± 4.14**, with 45 of 69 features kept on average. Its paired advantage over the two-number HbA1c-and-sex model is **+0.19 mg/dL [−0.63, +1.12]**, better in 6 of 16 participants: the 67 other features, 45 of them from the wrist, add nothing to a constant per participant that the bootstrap can see. Under the paper's personalised regime the full model scores **22.35 against the paper's 21.10** and is **worse than its own participant's first-half mean by 1.36 mg/dL [−3.34, +0.46]**; under the time-blocked regime, worse by 1.38 [−3.50, +0.71]. Every ablation is worse than the baseline under every regime; the model with E4 features and the clock alone is the worst of all under LOPO (23.22, −1.75 [−2.59, −0.78] against B2). Removing the food log costs 1.22 mg/dL under LOPO and removing the wrist costs 1.64; within participant the two costs are 0.37 and 0.17 — the P5 measurement goes one way across participants and the other within, and both are small beside the 4-mg/dL spread between participants.

| Participant | LOPO n | B2 RMSE | XGBoost RMSE | Δ | Second-half n | B1 RMSE | personalised XGBoost RMSE | Δ | Time-blocked n | B1 RMSE | XGBoost RMSE | Δ |
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

**All five predictions are judged** (`results/predictions.csv`):

| Prediction | Statement | Value | Reference | Verdict |
|---|---|---|---|---|
| P1a | B1 under the personalised regime lands within 3 mg/dL of the paper's 21.10 | 20.99 | 21.1 | **held** |
| P1b | the personalised XGBoost beats B1 by less than 3 mg/dL | model 22.35; B1 - model -1.36 [-3.342, 0.464] | 20.99 | **held** |
| P2a | B0 or B2 under LOPO lands within 3 mg/dL of the paper's 21.22 | B0 22.467; B2 21.473 | 21.22 | **held** |
| P2b | the population XGBoost beats B2 by less than 3 | model 21.285; B2 - model 0.188 [-0.633, 1.117] | 21.473 | **held** |
| P3 | classification reproduces within 3 points under R1 (84.3%) and falls by more than 15 points under R2 and R3 | — | 84.3 | **pending** |
| P4 | B1's accuracy (100 - MAPE) is above 84%, from a constant | 86.966 | 84.0 | **held** |
| P5 | measurement: removing the food log costs more RMSE than removing all E4 features | LOPO: minus food +1.215, minus E4 +1.642; halves: minus food +0.368, minus E4 +0.171 | — | **E4 costs more (LOPO); food costs more (halves)** |

## Reproduce

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pre-commit install && pre-commit install --hook-type pre-push
pytest                              # 159 tests; 17 need the dataset and skip without it
python -m src.data.coverage         # results/coverage.csv, glucose_distribution.csv
python -m src.features.build        # the 69 features per epoch (cached outside the tree); results/epochs.csv, feature_missingness.csv
python -m src.eval.label_counts     # results/labels.csv, label_distribution.csv, balanced_set.csv
python -m src.eval.baselines        # results/baselines_*.csv, predictions.csv (P1a, P2a, P4 judged)
python -m src.eval.models_run       # results/models_*.csv, paired_deltas*.csv, selected_features.csv (P1b, P2b, P5 judged; ~2 h)
```

Data: see [data/README.md](data/README.md). No data is included in this repository.

## Limitations and failure cases

_Written as they are found. Known before any fit: the cohort is high-normal (HbA1c 5.3–6.4%), so the glucose range any model has to span is narrow and a per-participant mean is a strong baseline; the reference is a CGM, not a laboratory measurement; HR and IBI are Empatica-derived, not raw; sixteen participants make every bootstrap interval wide._

## References

- Bent, B., Cho, P. J., Henriquez, M., Wittmann, A., Thacker, C., Feinglos, M., Crowley, M. J., & Dunn, J. P. (2021). Engineering digital biomarkers of interstitial glucose from noninvasive smartwatches. *npj Digital Medicine*, 4, 89. https://doi.org/10.1038/s41746-021-00465-w
- Cho, P., Kim, J., Bent, B., & Dunn, J. (2023). BIG IDEAs Lab Glycemic Variability and Wearable Device Data (version 1.1.3). *PhysioNet*. https://doi.org/10.13026/aw6y-fc44
- Goldberger, A. L., et al. (2000). PhysioBank, PhysioToolkit, and PhysioNet. *Circulation*, 101(23), e215–e220.

## Licence

MIT (code). Data: ODC-BY v1.0, see [data/README.md](data/README.md).
