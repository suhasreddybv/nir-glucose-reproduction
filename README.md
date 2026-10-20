# nir-glucose-reproduction

A reproduction of Bent, Cho, Henriquez et al. (2021), *Engineering digital biomarkers of interstitial glucose from noninvasive smartwatches* (npj Digital Medicine 4:89), on the dataset they released: what replicates under the paper's own evaluation, what survives a time-blocked split, and the baselines the paper did not report.

**Result.** _Pending — nothing has been fitted. The evaluation protocol ([docs/protocol.md](docs/protocol.md)) is being frozen first: the paper's claims, inputs, windowing, models, split and metrics are transcribed from the paper and its companion code before any model runs, and the baselines and the second split regime are fixed now, independent of what the paper says. The headline goes here once the protocol is hashed and the baselines are run against it._

## What is fixed before anything is fitted

- **Four baselines the paper did not report** (protocol §8): population mean; per-participant mean over the training period; persistence, for any model that uses lagged glucose; a per-participant linear model on the paper's own features. A published model that does not beat them has not demonstrated sensing.
- **Two split regimes, always side by side** (§9): the paper's, exactly as it describes it, and a time-blocked split — train on the first part of each participant's record, test on the last, no test window sharing time with its training set. If the paper's split is random within participant, the gap between the two is the reproduction's headline.
- **Evaluation** (§10): real CGM readings only; the clinical scorer and the iCGM analogue module vendored unchanged from [`cgm-forecast-conformal`](https://github.com/suhasreddybv/cgm-forecast-conformal) with their tests; per participant with n; bootstrap over 16 participants, wide and stated.

## The data

BIG IDEAs Lab Glycemic Variability and Wearable Device Data, PhysioNet v1.1.3 ([data/README.md](data/README.md)): 16 participants with HbA1c 5.3–6.4% — a high-normal cohort — wearing an Empatica E4 (BVP 64 Hz, ACC 32 Hz, EDA and TEMP 4 Hz, Empatica-derived HR and IBI) with a Dexcom G6 every five minutes and a food log, 8–10 days each. Open Data Commons Attribution licence; this repository's own policy keeps every raw file, cache and per-participant trace out of the tree regardless (D-002).

Every file is verified against the dataset's `SHA256SUMS.txt` before it is read, and the loader asserts what the protocol rests on rather than assuming it: the accelerometer is in 1/64 g (median raw magnitude ≈ 64, ≈ 1 g after scaling), BVP is zero-centred, the Dexcom stream is strictly increasing and censored to 40–400 mg/dL, and each participant's date-shifted E4 and Dexcom files overlap (D-005). The coverage and glucose-distribution tables are added here once the full dataset has verified.

## Reproduce

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pre-commit install && pre-commit install --hook-type pre-push
pytest                              # data-free tests run without the dataset; the rest skip
python -m src.data.coverage         # results/coverage.csv, glucose_distribution.csv
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
