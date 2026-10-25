# nir-glucose-reproduction

A reproduction of Bent, Cho, Henriquez et al. (2021), *Engineering digital biomarkers of interstitial glucose from noninvasive smartwatches* (npj Digital Medicine 4:89), on the dataset they released: what replicates under the paper's own evaluation, what survives a time-blocked split, and the baselines the paper did not report.

**Result.** _Pending — nothing has been fitted. The evaluation protocol ([docs/protocol.md](docs/protocol.md)) is frozen (D-009, SHA-256 prefix `7860469db2e059bd`, pinned by a test): the paper's claims, inputs, windowing, models, split and metrics are transcribed from the paper and its companion code, the thirteen choices the paper leaves open are resolved and logged (D-008), and the baselines, the three split regimes and five predictions are registered before any number exists (§8–§11). The 69 features of Supplementary Table 1 are implemented as pure functions with hand-computed tests and two mechanical leakage guards ([docs/features.md](docs/features.md)). The headline goes here once the baselines are run against the frozen protocol._

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


## Reproduce

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pre-commit install && pre-commit install --hook-type pre-push
pytest                              # 133 tests; 17 need the dataset and skip without it
python -m src.data.coverage         # results/coverage.csv, glucose_distribution.csv
python -m src.features.build        # the 69 features per epoch (cached outside the tree); results/epochs.csv, feature_missingness.csv
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
