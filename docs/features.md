# The 69 features, transcribed from Supplementary Table 1

Bent et al. 2021, Supplementary Information, Supplementary Table 1 ("The 69 data-driven and domain-driven features engineered for glucose prediction and classification, the type of feature, the source of the feature, and the calculation/description of the derivation"), transcribed on 25 October 2026 from the PDF (`41746_2021_465_MOESM1_ESM.pdf`, pages 1–5). Names are the table's own, spaces inside names removed (`TEMP _Std` → `TEMP_Std`). The right-hand column is how `src/features/` computes each one; where the table's formula and the DBDP code differ, protocol cell 7 says which was followed and why. Every feature is computed from samples strictly before the target reading's time T; none uses a CGM value.

"N interval" in the table is the 5-minute epoch [T − 5 min, T). Rolling windows are trailing, ending at T, left-open at their start.

## User input and model (3)

| # | Feature | Type | Source | Table's calculation | Computed here |
|---|---|---|---|---|---|
| 1 | Biological Sex | Demographics | User-defined | N/A | `Demographics.csv` Gender: MALE = 1, FEMALE = 0 |
| 2 | HbA1c | Clinical Metrics | User-defined | N/A | `Demographics.csv` HbA1c, % |
| 69 | ID | Personalization | Model | Assigned ID to designate different participants | integer 1–16 |

## Per-epoch summary statistics of the four E4 channels (28)

Seven statistics × EDA, HR, TEMP, ACC. The table's formulas: μ = Σxᵢ/N; σ = √(Σ(xᵢ − μ)²/N); min; max; first quartile; third quartile; skew = Σ(xᵢ − x̄)³ / ((N − 1) σ³). ACC is the vector magnitude √(x² + y² + z²) (Methods "Feature engineering"), here in g.

| # | Feature | Computed here |
|---|---|---|
| 3–9 | EDA_Mean, EDA_Std, EDA_Min, EDA_Max, EDA_Q1G, EDA_Q3G, EDA_Skew | pandas on the EDA samples in the epoch: mean, std (ddof = 1), min, max, quantile 0.25, quantile 0.75, skew (adjusted Fisher–Pearson); std and skew NaN when fewer than 2 / 3 samples |
| 10–16 | HR_Mean … HR_Skew | the same on the Empatica HR samples (1 Hz, derived) |
| 17–23 | TEMP_Mean … TEMP_Skew | the same on the TEMP samples |
| 24–30 | ACC_Mean … ACC_Skew | the same on the ACC vector magnitude |

## Stress: EDA peaks (3) and HRV (8)

| # | Feature | Table's calculation | Computed here |
|---|---|---|---|
| 31 | PeakEDA | Σ peaks over N; "rolling peak detection (height=0, distance=4, prominence=0.3)" | `scipy.signal.find_peaks(eda, height=0, distance=4, prominence=0.3)` on the epoch's raw EDA samples (4 Hz, so distance 4 = 1 s), count |
| 32 | PeakEDA2hr_sum | Σ PeakEDA over 2 hours, rolling | sum of PeakEDA over the usable epochs in (T − 2 h, T] |
| 33 | PeakEDA2hr_mean | Σ PeakEDA / N over 2 hours, rolling | mean of PeakEDA over the same epochs |
| 34 | maxHRV | maximum(IBIᵢ over N) | max of the IBI values (× 1000, ms) whose beat time is in the epoch |
| 35 | minHRV | minimum(IBIᵢ over N) | min, ms |
| 36 | medianHRV | median(IBIᵢ over N) | median, ms |
| 37 | meanHRV | Σ IBIᵢ / N | mean, ms |
| 38 | SDNN | √σ² of IBI over N | standard deviation, ddof = 1 (`wearablecompute.SDNN`), ms |
| 39 | NN50 | Σ when \|IBI[i+1] − IBI[i]\| > 50 | count of successive absolute differences > 50 ms within the epoch (`wearablecompute.NNx`, strict) |
| 40 | pNN50 | NN50 / len(N) | NN50 / number of differences × 100 (percent, as `wearablecompute.NNx` returns it; the table's formula is a proportion — a constant factor) |
| 41 | RMSSD | √(Σ(\|IBI[i+1] − IBI[i]\|)² / len(N)) | √(mean of squared successive differences), ms (`wearablecompute.RMSSD`) |

HRV features are NaN when the epoch has fewer than 2 IBI values (the E4 emits an IBI only when it trusts the beat).

## Diet (19)

Food-log rows with `time_begin` in the window; the nutrient columns as logged (protocol cell 7 j).

| # | Feature | Table's calculation | Computed here |
|---|---|---|---|
| 42–45 | calories2hr, protein2hr, sugar2hr, carbs2hr | Σ xᵢ over 2 hours, rolling | sum of `calorie`, `protein`, `sugar`, `total_carb` over rows with time_begin in [T − 2 h, T) |
| 46–49 | calories8hr, protein8hr, sugar8hr, carbs8hr | Σ over 8 hours | the same, [T − 8 h, T) |
| 50–53 | calories24hr, protein24hr, sugar24hr, carbs24hr | Σ over 24 hours | the same, [T − 24 h, T) |
| 54 | Eat | binary: 0 if not eating currently, 1 if currently eating | 1 if any eating event's time_begin falls in the epoch [T − 5 min, T) |
| 55–57 | Eatcnt2hr, Eatcnt8hr, Eatcnt24hr | Σ xᵢ over 2 / 8 / 24 hours, rolling | number of distinct eating events (distinct time_begin) in [T − W, T) |
| 58–60 | Eatmean2hr, Eatmean8hr, Eatmean24hr | Σ xᵢ / N over 2 / 8 / 24 hours, rolling | mean of Eat over the usable epochs in (T − W, T] |

## Circadian rhythm (3)

| # | Feature | Table's calculation | Computed here |
|---|---|---|---|
| 61 | WakeTime | (1) one point per quantity among HR_Mean, HR_Std, ACC_Mean, ACC_Std below the historical average; (2) binary from the points; (3) averaged over 3 hours rolling; (4) wake time where the slope changes and stays higher 25 and 75 minutes after | protocol cell 7 h: sleep-like when ≥ 2 of 4 are below their trailing 24-h mean; awake indicator averaged over (T − 3 h, T]; a day's wake candidate is the first rising edge of that average in the day (first difference positive after a non-positive one), kept if the average is higher at +25 and +75 min; the feature is the most recent wake time confirmed by T (candidate + 75 min ≤ T), in minutes from midnight |
| 62 | Minfrommid | minutes from midnight | 60 h + m + round(s / 60) of T (`wearablecompute.crhythm`) |
| 63 | Hourfrommid | hours from midnight | round(Minfrommid / 60), an integer (`crhythm`) |

## Activity / exercise (5)

| # | Feature | Table's calculation | Computed here |
|---|---|---|---|
| 64 | ACC_mean_2hrs | Σ x̄ᵢ / N over 2 hours, rolling | mean of ACC_Mean over the usable epochs in (T − 2 h, T] |
| 65 | ACC_max_2hrs | maximum(xᵢ over N = 2 hours) | max of ACC_Max over the same epochs |
| 66 | Activity_bouts | binary: 1 if both ACC_Mean and HR_Mean over N exceed the historical mean | `wearablecompute.exercisepts`: ACC_Mean > mean of all earlier epochs' ACC_Mean **and** HR_Mean > mean of all earlier epochs' HR_Mean (expanding, exclusive); the first epoch is 0 |
| 67 | Activity24 | mean of Activity_bouts over 24 hours, rolling | mean over the usable epochs in (T − 24 h, T] |
| 68 | Activity1hr | Σ Activity_bouts over 1 hour, rolling | sum over the usable epochs in (T − 1 h, T] |

## Groupings used by the ablations (protocol §9)

- **E4 features (45):** 3–30, 31–41, 61 (WakeTime), 64–68.
- **Food log (19):** 42–60.
- **Demographics and model (3):** 1, 2, 69.
- **Circadian clock (2):** 62, 63 — kept in every ablation, since they come from the timestamp alone.

The paper's own categories (Methods "Analysis of features"): food; circadian rhythm; stress (EDA peaks and HRV); activity; temperature; heart rate; electrodermal activity; biological sex; HbA1c; personalization — by source: food log, wearable, user input, model.
