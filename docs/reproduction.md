# Reproduction of Bent et al. 2021: what replicated, what did not, and what would settle it

**A constant — each participant's mean glucose over the first half of their own record — scores the paper's personalised RMSE to within 0.11 mg/dL (20.99 against 21.10). The paper's personalised model, rebuilt from its Methods, does not beat it on the mean: 22.35 mg/dL, worse by 1.36 with a 95 % CI of [-0.46, 3.34] that spans zero.** Per participant the picture is mixed: the model is better for 9 of 16 (median paired gain +0.30 mg/dL), and the mean is pulled down by 3 participants (015, 012, 003) for whom it is 7.4–10.5 mg/dL worse. Either way the model and a constant cannot be told apart. That was prediction P1, registered before any number existed, and it is the decisive one. The paper's population number reproduces; its personalised number does not; and both are what a cohort this narrow gives anything that knows who the participant is.

Target: Bent, Cho, Henriquez et al. (2021), *Engineering digital biomarkers of interstitial glucose from noninvasive smartwatches*, npj Digital Medicine 4:89, on the data they released (BIG IDEAs Lab, PhysioNet v1.1.3; 16 participants, HbA1c 5.3–6.4 % against a recruitment range of 5.2–6.4, Empatica E4 with Dexcom G6 for 8–10 days, and a food log). The protocol (`docs/protocol.md`; its sections are numbered cells 1–7 for what was transcribed from the paper and §8–§11 for what was fixed independently) was transcribed from the paper and its companion code, verified against the paper, and frozen by hash (`7860469db2e059bd`) before any fit. Four predictions (P1–P4, with P1 and P2 in two parts each) and one measurement (P5) were registered with it. Every number here is generated from `results/` by `src/eval/write_docs.py`.

**Key.** *B0–B3* are the four pre-registered baselines: B0 the population mean, B1 the participant's own mean over their training portion, B2 a linear model on HbA1c and sex, B3 a per-participant linear model on the 45 wrist (E4) features. *LOPO* is leave one person out. The three split regimes: the paper's (LOPO for the population model, first half → second half for the personalised one, random windows for the classifier); participant-grouped folds; and time-blocked within participant, with 24-hour exclusion zones either side of the boundary. *PersLow / PersNorm / PersHigh* label a reading below, within or above one SD of the participant's trailing 24-hour mean. *MAPE* is mean absolute percentage error, and the paper's "accuracy" is 100 − MAPE. *E4* is the Empatica E4 wristband.

## What replicated

- **The population regression, to within 0.07 mg/dL.** XGBoost with the paper's hyperparameters and in-fold random-forest selection, LOPO: **RMSE 21.29 ± 4.00 mg/dL against the paper's 21.22 ± 4.14**; MAPE 14.34 against 14.33 % (`docs/models.md`).
- **The labels.** PersLow / PersNorm / PersHigh from the trailing 24-hour mean ± 1 SD land on the paper's Table 1: PersNorm 111.8 ± 14.6 mg/dL (paper 112.4 ± 14.5), PersHigh 148.5 ± 25.7 (149.9 ± 24.4), PersLow 91.0 ± 11.6 (90.8 ± 11.1) (`docs/baselines.md`).
- **The feature importance.** 14 of the paper's 15 most important features (Table 3) are in this reproduction's top 15, minutes from midnight first in both.
- **Half of the naive-model claim.** The paper says both models "outperformed the naïve models (mean and median)". Across participants that is true: the population model beats the population mean by 1.18 mg/dL [0.16, 2.13] and the population median by 1.22 (`results/naive_claim.csv`, a supplementary check added after the pre-registered numbers, D-016).

Not counted as replicated, by the same 3-point yardstick that failed P3: the paper's logistic-regression comparator (55.4 % against 52.0 %). The classification R² (0.545 against 0.505) is reported because the paper reports it, but R² on three nominal class codes is not a meaningful target and is not used as evidence here.

## What did not

- **The personalised model.** 22.35 against the paper's 21.10, and on the mean behind the participant's own first-half mean (20.99) and median (21.51); per participant, better for 9 of 16. The other half of the naive-model claim does not hold here.
- **Anything beyond a two-number baseline, across participants.** A linear model on HbA1c and sex scores 21.47; the 69-feature model beats it by 0.19 mg/dL on the mean, with a CI of [-0.63, 1.12] that spans zero, and is better for 6 of 16 participants. The two are statistically indistinguishable.
- **The wrist on its own.** With the wrist features and the clock alone the model scores 23.22 under LOPO, the worst configuration; a per-participant linear model on the 45 wrist features is worse than the participant's mean on the same rows (22.00 against 20.83).
- **The classification headline, by 6.1 points.** The decision tree under the paper's own random-window split scores 78.18 % balanced accuracy against 84.3 % (P3's 3-point margin fails; the pre-registered 10-point stop rule, protocol §11, does not trigger), and the 70/30 tree 73.4 % against 82.0 %. The shortfall is not explained, and nothing was changed to close it (`docs/classification.md`).
- **The classification once windows are grouped by participant (40.15 %) or separated in time by at least 24 hours (47.10 %),** against chance at 33.3 %. Under the paper's split, 66.7 % of test windows have a training window from the same participant within 5 minutes, and 99.5 % within an hour; the label is a 24-hour rolling statistic. At the real class prevalence a PersHigh call would be right about 52 % of the time under the paper's split and about 22 % with participants grouped.

## The predictions, judged against their frozen words

| Prediction | Statement | Value | Reference | Verdict |
|---|---|---|---|---|
| P1a | B1 under the personalised regime lands within 3 mg/dL of the paper's 21.10 | 20.99 | 21.1 | **held** |
| P1b | the personalised XGBoost beats B1 by less than 3 mg/dL | model 22.35; B1 - model -1.36 [-3.342, 0.464] | 20.99 | **held** |
| P2a | B0 or B2 under LOPO lands within 3 mg/dL of the paper's 21.22 | B0 22.467; B2 21.473 | 21.22 | **held** |
| P2b | the population XGBoost beats B2 by less than 3 | model 21.285; B2 - model 0.188 [-0.633, 1.117] | 21.473 | **held** |
| P3 | classification reproduces within 3 points under R1 (84.3%) and falls by more than 15 points under R2 and R3 | R1 78.18; R2 40.15 (drop 38.03); R3 47.1 (drop 31.08) | 84.3 | **failed** |
| P4 | B1's accuracy (100 - MAPE) is above 84%, from a constant | 86.966 | 84.0 | **held** |
| P5 | measurement: removing the food log costs more RMSE than removing all E4 features | LOPO: minus food +1.215, minus E4 +1.642; halves: minus food +0.368, minus E4 +0.171 | — | **E4 costs more (LOPO); food costs more (halves)** |

In the table, a *value* such as "B1 - model -1.36" means baseline minus model, so negative means the model is worse. P1b "held" because the prediction was that the model would beat B1 by less than 3 mg/dL, and it did not beat it at all. P4's 84 % threshold is the classification figure in the paper's abstract ("up to 84% and 87% accuracy"), and P4 restates P1 in the paper's own "accuracy" unit, so it is not independent evidence. P5 is a measurement: removing the food log costs 1.22 mg/dL across participants and removing every wrist feature costs 1.64; within participant the costs are 0.37 and 0.17. Both are small beside the 4-mg/dL spread of RMSE between participants. Of the 15 ablated models, 14 are worse than the baseline on the mean; the exception is the model without sex, HbA1c and ID under LOPO (21.39 against B2's 21.47, a difference of 0.08 [-1.01, 1.27]).

## What data would settle it

1. **A cohort that leaves the normal range.** 97.6 % of these readings sit inside 70–180 mg/dL and participant means span 93–130; a constant per person is within one SD of almost every reading. A cohort with type 2 or type 1 diabetes, or with provoked excursions spanning 60–300 mg/dL, is the only test in which a wrist signal has room to beat a constant.
2. **A participant-grouped or time-blocked evaluation.** LOPO for regression is already in the paper; the classification needs the same, and every within-person evaluation needs a gap at least as long as the longest rolling window in its features or labels (24 hours here).
3. **The naive baselines reported beside every model.** The per-participant mean, an HbA1c-and-sex model, and the wrist-only model, under the same split and on the same rows, with paired per-participant differences and an interval. The companion paper made that comparison for its HbA1c model, and reported that it did not beat the mean; this paper did not make it.

Also, smaller: a laboratory glucose reference rather than a CGM, which is itself a ±15–20 % instrument at these levels; more than 16 participants, since every interval here is a bootstrap over 16; and raw PPG rather than the Empatica-derived heart rate and inter-beat intervals.

## Limitations of this reproduction

- **The reference is a CGM.** Every RMSE here is against Dexcom G6 interstitial glucose, as the paper's is.
- **n = 16.** Every interval is a bootstrap over participants and is wide; the time-blocked regime has 15, because participant 015's record has nothing beyond its 24-hour exclusion zone.
- **A high-normal cohort.** 0.57 % of readings are below 70 mg/dL and 1.78 % above 180; nothing here speaks to hypoglycaemia or diabetes-range glucose.
- **Self-reported food.** 19 of the 69 features come from a hand-written food diary logged by the participants, with timings to the minute.
- **Manufacturer-derived wrist signals.** Heart rate and inter-beat intervals are Empatica's own outputs; the raw BVP was not used, as in the paper.
- **Analogues.** The Clarke and Parkes grids carried from the author's earlier CGM-forecasting repository, [`cgm-forecast-conformal`](https://github.com/suhasreddybv/cgm-forecast-conformal), are applied to an estimator they were not written for and are labelled as analogues; on this cohort every method scores 98.9–99.4 % in Clarke A + B and the grid separates nothing.
- **Deviations from the frozen protocol, all logged in D-017.** Five ablations were run where §9 named four: "E4 only" kept the two clock features, "minus all E4" was added because P5 needs it, and "minus sex, HbA1c and ID" was added. The class-balanced set was drawn from the 25,644 complete labelled epochs, not from all labelled readings as cell 7 c says. Regression runs on all 28,964 usable epochs (XGBoost takes missing features); classification uses the complete epochs only.
- **Resolved from code against guessed.** From the DBDP code: EDA peak detection, the HRV definitions, activity bouts, the circadian features, the MAPE and SD conventions, in-fold selection. Decided without code (D-008): the epoch placement, the usable-epoch rule, class balancing, the first-day label window, "first half" by count, the wake-time rule (a trailing 24-hour mean in place of the calendar day's, which would read the future), the participant-ID and sex coding, the food-log parsing. The labels reproducing Table 1 and 14 of 15 top features reproducing are evidence that those choices are close; the 6.1-point classification shortfall is evidence that something is not.
