# nir-glucose-reproduction

A reproduction of Bent, Cho, Henriquez et al. (2021), *Engineering digital biomarkers of interstitial glucose from noninvasive smartwatches* (npj Digital Medicine 4:89), on the dataset they released: what replicates under the paper's own evaluation, what survives a time-blocked split, and the baselines the paper did not report.

**Result.** _Pending the models (Tuesday and Wednesday); the baselines are in. Under the paper's own personalised regime, **a constant — each participant's mean glucose over their first half — scores RMSE 20.99 ± 4.17 mg/dL and "accuracy" 86.97 %, against the paper's personalised XGBoost at 21.10 ± 4.50 and 86.74 %**; under leave-one-person-out, a linear model on HbA1c and sex alone scores 21.47 ± 3.94 against the paper's 21.22 ± 4.14. Three of five pre-registered predictions are judged and held (P1a, P2a, P4; D-012). The protocol ([docs/protocol.md](docs/protocol.md)) was frozen at `7860469db2e059bd` and verified against the paper before any of this ran._

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

**Three of the five pre-registered predictions are judged** (protocol §11, `results/predictions.csv`); P1b, P2b, P3 and P5 wait for the models.

| Prediction | Statement | Value | Reference | Verdict |
|---|---|---|---|---|
| P1a | B1 under the personalised regime lands within 3 mg/dL of the paper's 21.10 | 20.99 | 21.1 | **held** |
| P1b | the personalised XGBoost beats B1 by less than 3 mg/dL | — | 20.99 | **pending** |
| P2a | B0 or B2 under LOPO lands within 3 mg/dL of the paper's 21.22 | B0 22.467; B2 21.473 | 21.22 | **held** |
| P2b | the population XGBoost beats B2 by less than 3 | — | 21.473 | **pending** |
| P3 | classification reproduces within 3 points under R1 (84.3%) and falls by more than 15 points under R2 and R3 | — | 84.3 | **pending** |
| P4 | B1's accuracy (100 - MAPE) is above 84%, from a constant | 86.966 | 84.0 | **held** |
| P5 | measurement: removing the food log costs more RMSE than removing all E4 features | — | — | **pending** |

**The labels** (`results/labels.csv`, `results/label_distribution.csv`, `results/balanced_set.csv`, D-011). PersHigh / PersLow / PersNorm from the trailing 24-h mean ± 1 SD of each participant's own CGM (protocol cell 7 d) label 36,722 of 36,898 readings: PersLow 5,206 (14.2%), PersNorm 25,854 (70.4%), PersHigh 5,662 (15.4%). The three class distributions land on the paper's Table 1: PersNorm 111.8 ± 14.6 mg/dL (paper 112.4 ± 14.5), PersHigh 148.5 ± 25.7 (149.9 ± 24.4), PersLow 91.0 ± 11.6 (90.8 ± 11.1). Undersampling every class to the smallest on the 25,644 complete labelled epochs gives a balanced set of **N = 10,230** (3 × 3,410) against the paper's 8,666; the difference is the size of the complete set, not the rule.

## Reproduce

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pre-commit install && pre-commit install --hook-type pre-push
pytest                              # 150 tests; 17 need the dataset and skip without it
python -m src.data.coverage         # results/coverage.csv, glucose_distribution.csv
python -m src.features.build        # the 69 features per epoch (cached outside the tree); results/epochs.csv, feature_missingness.csv
python -m src.eval.label_counts     # results/labels.csv, label_distribution.csv, balanced_set.csv
python -m src.eval.baselines        # results/baselines_*.csv, predictions.csv (P1a, P2a, P4 judged)
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
