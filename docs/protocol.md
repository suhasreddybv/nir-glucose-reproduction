# Evaluation protocol

Target: Bent, B., Cho, P. J., Henriquez, M., et al. (2021). Engineering digital biomarkers of interstitial glucose from noninvasive smartwatches. *npj Digital Medicine*, 4, 89. https://doi.org/10.1038/s41746-021-00465-w — main text, Supplementary Information (Supplementary Table 1: the 69 features; Supplementary Table 2: demographics) and the Reporting Summary.

Data: BIG IDEAs Lab Glycemic Variability and Wearable Device Data, PhysioNet v1.1.3, https://doi.org/10.13026/aw6y-fc44 (ODC-BY v1.0). Companion code: the Duke Digital Biomarker Discovery Pipeline repositories (github.com/DigitalBiomarkerDiscoveryPipeline), read on 25 October 2026 at the commits named in cell 7 — read to resolve what the paper leaves open, cited, never copied.

**Nothing is fitted until this file is frozen and hashed.** Cells 1–7 are transcribed from the paper and the companion code (25 October 2026); each cell names where in the paper to look so the transcription can be checked against it. Cells 8–11 are fixed independently of what the paper says: drafted on 20 October, revised on 25 October before the freeze (the revision and its reason are in §8). The freeze hash is recorded in `docs/decisions.md` and pinned by `tests/test_protocol.py`.

## 1. The claims to reproduce

| Claim | Exact number | Unit of analysis | Where in the paper |
|---|---|---|---|
| Three-class PersHigh / PersLow / PersNorm classification, decision tree, repeated stratified k-fold (10 splits × 3 repeats) on a class-balanced set of N = 8,666 windows | balanced accuracy **84.3 ± 1.3 %** (Table 2 prints "84.3 ± 0.013%"); weighted recall 84.3, precision 84.5, F1 84.3; R² 0.505 ± 0.050 | window; mean ± SD over the 30 folds | Results "Glucose excursion classification"; Table 2; Methods "Classification of glucose excursions" |
| Same model, 70/30 train/test split | balanced accuracy **82.0 %**; per-class accuracy PersHigh 82.6, PersNorm 81.3, PersLow 82.1 | window | Results, same section; Fig. 4 |
| Logistic regression, 70/30 split | **52.0 %** | window | Table 2 |
| Regression, population XGBoost, leave-one-person-out | RMSE **21.22 ± 4.14 mg/dL**, MAPE **14.33 ± 3.25 %**, "accuracy" (100 − MAPE) **85.67 %** | participant (one fold each); mean ± SD over 16 | Results "Glucose prediction"; Methods "Glucose prediction" |
| Regression, personalised XGBoost, first contiguous half → second half | RMSE **21.10 ± 4.50 mg/dL**, MAPE **13.26 ± 3.94 %**, "accuracy" **86.74 %** | participant; mean ± SD over 16 | Results "Glucose prediction" |
| "Both the personalized model and the traditional population model outperformed the naïve models (mean and median)" | no number is given anywhere in the paper or the supplement | — | Results "Glucose prediction", last sentences |

The cohort: 16 participants, HbA1c 5.2–6.4 % by the recruitment criterion, 35–65 years, "over 25,000 interstitial glucose point measurements and 25,000 5-min epochs", "an average of 1500 glucose measurements per participant" (Methods "Dataset" and "Glucose prediction"). The Reporting Summary states "No data was excluded from these analyses."

## 2. Inputs

| Question | Answer | Source |
|---|---|---|
| Which E4 channels | ACC (vector magnitude of the three axes), EDA, TEMP, and heart rate; **BVP itself is not used** — the paper's "photoplethysmography (optical heart rate)" enters only through the Empatica HR and IBI outputs | Methods "Dataset" ("Heart rate was recorded once per second (calculated from photoplethysmography sampled at 64 Hz)"); "Feature engineering" (summary statistics "for heart rate, accelerometry (vector magnitude of the three axes), electrodermal activity, and skin temperature") |
| Empatica-derived HR / IBI used? | **Yes, both.** HR: the seven per-epoch summary statistics and the activity-bout and wake-time rules. IBI: the eight HRV metrics "derived from the PPG" | Methods "Feature engineering", stress paragraphs; Supplementary Table 1 (HR_*, maxHRV … RMSSD) |
| Food log an input? | **Yes.** Rolling 2 h / 8 h / 24 h sums of calories, protein, carbohydrates, sugar; a binary "Eat"; rolling 2/8/24 h counts and means of eating events — 19 of the 69 features; the food category carried 37.0 % of the random-forest importance and sugar (24 h) is the second most important feature | Methods "Feature engineering", diet paragraphs; Results "Exploring feature importance"; Table 3; Supplementary Table 1 |
| Lagged glucose ever an input? | **No.** "All features used in modeling were historical (5 min to 24 h prior to the measurement being predicted)" and none of the 69 is derived from CGM. The models are glucose *estimators* from non-glucose inputs, not forecasters: persistence is not a competing method (§8) | Methods "Feature engineering"; Supplementary Table 1 (no CGM-derived row) |
| Demographics as inputs? | **Yes:** biological sex and HbA1c ("user input"), plus a participant-ID "personalization" feature ("model") | Methods "Feature engineering" second paragraph; Supplementary Table 1 |

Sex and HbA1c come from the dataset's `Demographics.csv`. **A discrepancy to record:** the file lists 9 female and 7 male participants; the paper's Supplementary Table 2 and Reporting Summary say 8 and 8. The file is used as released. HbA1c in the file runs 5.3–6.4 %.

*Why each matters: a model using the food log is not sensing glucose from the wrist; a model using lagged CGM would be a forecaster, not a sensor. Here the first is true and the second is not.*

## 3. Windowing

| Window | Features per window | Aggregation | Source |
|---|---|---|---|
| A 5-minute epoch per Dexcom reading; the target is the reading itself ("interstitial glucose at every 5-min interval") | 69 (Supplementary Table 1; listed with their formulas in `docs/features.md`) | Per-epoch summary statistics over the epoch's samples; rolling trailing windows of 1 h, 2 h, 3 h, 8 h and 24 h over epochs or over food-log events, "computed every 5 min on a rolling basis"; all historical, "5 min to 24 h prior to the measurement being predicted" | Methods "Feature engineering" first paragraph and each domain paragraph |

The epoch's exact placement relative to the reading, and what counts as a usable epoch, are not stated and are resolved in cell 7 (a, b). The paper used "25,000 5-min epochs"; this repository's usable count under the resolved rule is reported in `results/epochs.csv` with the Day 0 count (28,592 readings with a complete 10-minute BVP window) and the difference stated.

## 4. Models

| Family | Personalised, population, or both | Hyperparameters and how chosen | Source |
|---|---|---|---|
| Classification: decision tree (scikit-learn), with recursive feature elimination to the 20 most important features **inside each fold**; the RFE estimator chosen among logistic regression, perceptron, decision tree, random forest and gradient boosting by accuracy — decision tree won | population (windows pooled across participants) | 20 features by RFE; no other tree hyperparameters are stated (defaults assumed, cell 7 i) | Methods "Classification of glucose excursions" |
| Classification: logistic regression, 70/30 split | population | none stated | Methods, same section; Table 2 |
| Regression: XGBoost | both — population (LOPO) and personalised (one model per participant) | max depth 6, 100 estimators, learning rate 0.1, "tuned hyperparameters for all models" (how is not stated); feature selection by a random-forest regressor (1,000 trees), impurity importance cutoff 0.005, **per LOPO fold** | Methods "Glucose prediction" |
| Random forest regression (1,000 trees), LOPO — used for the feature-importance analysis only | population | 1,000 trees | Methods "Analysis of features" |

## 5. Split — the single most consequential cell

| Question | Answer | Source |
|---|---|---|
| Random windows within participant, or time-blocked? | **Classification: random windows.** Repeated stratified k-fold (10 splits, 3 repeats) on the class-balanced N = 8,666 windows, stratified by class, not grouped by participant and not blocked in time; the 70/30 split likewise random. Adjacent 5-minute windows of the same participant land on both sides of every fold | Methods "Classification of glucose excursions" ("repeated stratified k-fold cross validation schema with 10 splits and 3 repeats") |
| By participant or within? | **Regression, population: by participant** — leave-one-person-out, 16 folds. **Regression, personalised: within participant, temporal** — "trained on the first contiguous half (50%) of the participant's data and tested on the remaining half". Classification: within (see above) | Methods "Glucose prediction", last paragraph |
| Folds / repeats; how the headline aggregates them | Classification: 30 folds, mean ± SD of each metric. Regression: 16 LOPO folds and 16 personalised test halves, "mean and standard deviation over the population" | Methods "Classification …", last paragraph; "Glucose prediction", last paragraph |

## 6. Metrics

| Task | Metric(s) | Aggregation level | Source |
|---|---|---|---|
| Regression (glucose value) | RMSE; MAPE = mean of \|y − ŷ\| / y × 100; "accuracy" = 100 − MAPE. No Clarke or Parkes grid, no MARD, no per-participant table, no naive-baseline number | per participant (one LOPO fold or one test half each), then mean ± SD over the 16 | Methods "Glucose prediction", last paragraph; DBDP `Model-Development/loocvRF/loocvRF.py` (MAPE as above; the SD is `np.std`, population) |
| Classification (excursion classes) | balanced accuracy, weighted precision, weighted recall, weighted F1 (scikit-learn), R² "thresholded at zero" | per fold, mean ± SD over the 30 folds; the 70/30 split once | Methods "Classification …", last paragraph; Table 2 footnote |

## 7. Underspecified choices

Each resolved before the freeze. "Code" means the DBDP repositories as read on 25 October 2026: `wearablecompute` at `4e20fda` (the first author's feature package: `e4import`, `HRV`, `SDNN`, `RMSSD`, `NNx`, `PeaksEDA`, `exercisepts`, `crhythm`), `Heart-Rate-Variability` at `5d29f58`, `Model-Development` at `6f8bfa4` (`loocvRF.py`). The study's own modelling scripts are not in any DBDP repository (the DBDP holds the general-purpose functions the Methods cite), so every choice below that the functions do not settle is a decision, logged as D-008.

| | Choice | What the paper says | What the code does | Resolved as |
|---|---|---|---|---|
| a | Epoch placement relative to the reading | features are "historical (5 min to 24 h prior to the measurement being predicted)" | `e4import` resamples to clock-aligned 5-min bins; the join to the CGM is not in the code | the epoch is the 5 minutes **ending at the reading**, [T − 5 min, T); every rolling window ends at T — epochs enter a window by their end time (T − W < t ≤ T; their samples are all before T), food-log events by their start time (T − W ≤ t < T); no sample or event at or after T is ever used |
| b | Which epochs are usable (missing E4 within an epoch) | "25,000 5-min epochs"; "No data was excluded" | `resample().mean()` gives a value whenever the bin has ≥ 1 sample | an epoch is usable when **ACC, EDA, TEMP and HR each have ≥ 1 sample in it**; HRV features are NaN when the epoch has < 2 IBI; XGBoost takes NaN natively; the decision tree and the linear baselines receive rows with NaN **dropped**, and the dropped count is reported |
| c | Class balancing to N = 8,666 | "We balanced our classes … because the entire dataset was highly imbalanced" | absent | random undersampling of every class to the smallest class's count, seed 0, done once on the full labelled set before any split; the resulting N is reported beside 8,666 and not tuned towards it |
| d | The rolling 24-h mean ± SD in the first 24 h of a record | "the mean for the last 24 h" | absent | pandas time-based trailing 24-h window over the participant's CGM including the current reading, SD with ddof = 1, **minimum 12 readings (1 h)**; readings before that are unlabelled and excluded from classification only |
| e | "First contiguous half" | "the first contiguous half (50%) of the participant's data" | absent | by **count of usable epochs** in time order (`iloc[:n // 2]`); the time of the boundary is reported per participant |
| f | EDA peaks: raw or filtered; HRV from Empatica IBI | peaks by SciPy with distance 1 s and prominence 0.3 µS; HRV "utilized open source code available in the DBDP" | `PeaksEDA`: `find_peaks(height=0, distance=4, prominence=0.3)` on the raw EDA series, no filtering; `wearablecompute` HRV functions on IBI × 1000 ms: max/min/mean/median of the raw intervals, SDNN with ddof = 1, NN50 = count of \|Δ\| > 50 ms, pNN50 in percent, RMSSD over all successive differences in the epoch with no gap check (Empatica has already dropped the beats it did not trust) | **as the code**: raw EDA, `find_peaks` with those arguments on the epoch's samples; the `wearablecompute` HRV definitions. The `Heart-Rate-Variability` repository's `DBDP.py` smooths the IBI with a 10-beat rolling mean before max/min/mean/median/SDNN — rejected, because Supplementary Table 1's formulas are on the intervals themselves and the first author's package implements them that way |
| g | The "prior average" in activity bouts | "compared it to the average of the prior historical data from the individual" | `exercisepts`: epoch z is a bout when `acc[z] > mean(acc[0:z])` and `hr[z] > mean(hr[0:z])` — an expanding mean over all earlier epochs, exclusive | **as the code**: expanding mean of the participant's earlier usable epochs; the first epoch is never a bout |
| h | Wake-time rule | four quantities "less than the average for that day"; "when two of the four … we assigned that interval a '0'"; averaged over 3 h rolling; wake time "when the slope of this data sharply changed and remained consistently higher 25 and 75 min after" (Supplementary Table 1 says "points > 2 → 1" — the two descriptions disagree on the threshold) | absent | an epoch is sleep-like (0) when **at least 2 of 4** (HR_Mean, HR_Std, ACC_Mean, ACC_Std) are below the **trailing 24-h mean** of the same quantity, awake-like (1) otherwise — the trailing mean replaces the calendar-day mean because the day's mean uses samples after the target (§10 forbids it); the indicator is averaged over a trailing 3-h window; the "sharp change" is taken as a rising edge of that 3-h average — the first epoch of a calendar day whose first difference is positive after a non-positive one — kept as that day's wake time only if the average is higher at +25 and +75 min than at the edge (a brief night waking makes an edge but fails this check; a day's largest slope cannot be used online, since it is not known until the day ends); the feature at epoch T is the most recent **confirmed** wake time (confirmed means T ≥ candidate + 75 min), in minutes from midnight, NaN until the first confirmation. Nothing after T is used |
| i | Participant ID: integer or one-hot; sex coding; tree defaults | "a unique number"; nothing on sex coding or tree hyperparameters | `loocvRF.py` carries the id as a string and drops it; the paper kept it (importance 0.029) | ID as the **integer** 1–16; sex MALE = 1, FEMALE = 0; scikit-learn decision tree defaults (unlimited depth, Gini), `random_state = 0`; logistic regression defaults with `max_iter = 1000` |
| j | Food-log parsing | sums of calories, protein, carbohydrates, sugar; an eating event per "unique meal, snack, or caloric beverage" | absent | the dataset's own nutrient columns (`calorie`, `total_carb`, `sugar`, `protein`) are used as logged; the free-text `amount` / `unit` are not parsed (the nutrients are already per logged amount); an eating event is one distinct `time_begin` per participant (rows sharing a time are one meal); a missing nutrient contributes 0 to a sum and the count of such rows is reported; 003's headerless file lacks only `time_end`, `dietary_fiber` and `total_fat`, none of which the paper's features use, so 003 is complete for this purpose (D-005) |
| k | Per-epoch statistics: SD and skew conventions; units | σ = √(Σ(x − μ)² / N); skew = Σ(x − x̄)³ / ((N − 1) σ³) | `e4import` uses pandas `resample().std()` (ddof = 1) | pandas conventions: `std(ddof = 1)`, pandas `skew` (adjusted Fisher–Pearson), quartiles by linear interpolation; ACC magnitude in g (the paper's raw 1/64-g units differ by a constant factor, to which every model and baseline here is invariant) |
| l | Circadian features | "minutes from midnight" and "hours from midnight" | `crhythm`: minutes = 60 h + m + round(s / 60); hours = round(minutes / 60), an integer | **as the code** |
| m | Rolling windows over epochs when epochs are missing | "rolling window" | pandas rolling over whatever rows exist | time-based trailing windows over the participant's usable epochs: sums are over the epochs present, means are NaN-skipping; the number of epochs in the window is not a feature |

---

*Fixed independently of the paper. Drafted 20 October 2026; revised 25 October 2026 before the freeze, once cell 2 established that no model uses lagged glucose (so persistence is not a competing method here) and that the paper's own classification split is random within participant.*

## 8. Baselines, pre-registered

All reported before any model, under every regime of §9 that applies, per participant with n and with the 16-participant bootstrap, with every metric of §10:

- **B0 — population mean:** the training participants' mean glucose, predicted for every window.
- **B1 — per-participant mean from the training portion** (personalised regime): that participant's mean over their own training half. The number that matters most: Day 0 measured within-participant SDs of 15–29 mg/dL.
- **B2 — HbA1c-and-sex-adjusted mean:** a two-feature linear model (LOPO) — what the user-input features alone buy.
- **B3 — per-participant linear model on the E4 features only** (no food log, no demographics, no ID).

*Revision of the 20 October draft:* persistence is dropped — no model here uses any prior CGM reading (cell 2), so a forecaster's floor is not a comparator; B2 is added because HbA1c and sex are two of the 69 inputs and carry 10.8 % of the paper's importance.

## 9. Split regimes, always side by side

- **R1 — the paper's**, exactly as cell 5 records it: window-level repeated stratified 10-fold × 3 (classification); LOPO and first-half / second-half (regression).
- **R2 — participant-grouped k-fold** (classification): the same folds grouped so that no participant's windows are split across train and test.
- **R3 — time-blocked within participant** (classification and personalised regression): train on the first 70 % of each participant's usable epochs, test on the last 30 %, and **no window within 24 h of the boundary on either side** — the classification label is a 24-h rolling statistic, so a window nearer than that shares its label's history with the other side.

Ablations on the full regression model, under R1 and R3: minus the food log; minus sex, HbA1c and ID; E4 features only; food log only.

## 10. Evaluation

- Real CGM readings only; nothing interpolated is ever a target. No feature uses any CGM value and no feature uses any sample at or after the target time (a violation is a bug, not a result).
- The paper's metrics (RMSE, MAPE, 100 − MAPE; balanced accuracy and the weighted scores) and, beside them, the clinical scorer vendored from `cgm-forecast-conformal`: Clarke A + B and Parkes, MARD with the reference as denominator, time-in-range agreement; the iCGM analogues labelled as analogues throughout (`docs/icgm_criteria.md`). Confusion matrices per regime, per-class accuracy, and the prevalence-adjusted positive predictive value, because the balanced set hides that PersNorm is the large majority.
- Every per-participant figure carries its n; every pooled figure its total. Bootstrap over participants, n = 16; the intervals will be wide and are stated.
- No number is chosen on a test fold. No calibration or threshold is set on a test target.
- Dexcom G6 values are censored to 40–400 mg/dL; floored and ceilinged targets are counted (Day 0: one reading at the floor, none at the ceiling).
- No trace of any participant's glucose or wearable signal appears in a figure (repository policy; the licence permits it, the policy does not).

## 11. Pre-registered predictions, and the freeze

Written before any number exists, judged later against these words, each failure reported as a failure. The write-up's first sentence is whichever of P1–P4 was decisive.

- **P1.** The per-participant mean (B1) under the personalised regime lands within 3 mg/dL of the paper's 21.10; the personalised XGBoost beats B1 by less than 3 mg/dL. Rationale: Day 0 measured within-participant SD at 15–29 mg/dL.
- **P2.** B0 or B2 under LOPO lands within 3 mg/dL of the paper's 21.22; the population XGBoost beats B2 by less than 3.
- **P3.** The classification result reproduces within 3 points under R1 (84.3 %) and falls by more than 15 points under R2 and R3. Rationale: adjacent 5-min windows share a participant, an hour and a rolling-24-h label.
- **P4.** B1's "accuracy" (100 − MAPE) is above 84 %, i.e. inside the paper's headline range, from a constant.
- **P5** (measurement, not prediction). Removing the food log costs more RMSE than removing all E4 features. Report which way it goes.

Stop condition carried from the brief: classification under R1 more than 10 points from 84.3 % → stop and report before building on it.

**Freeze.** This file's SHA-256 prefix is recorded in `docs/decisions.md` and pinned by `tests/test_protocol.py` before the first fit. Any later change is a dated section with its reason; results under the old protocol are re-run or struck.
