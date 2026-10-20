# Data

**BIG IDEAs Lab Glycemic Variability and Wearable Device Data**, version 1.1.3, PhysioNet. https://doi.org/10.13026/aw6y-fc44

**Licence: Open Data Commons Attribution License v1.0** — attribution required; redistribution of the data and of derived data permitted. This repository's own policy is stricter: no raw data, no caches and no per-participant time series are committed (`docs/decisions.md`, D-002).

**Required citations** (PhysioNet):

- Cho, P., Kim, J., Bent, B., & Dunn, J. (2023). BIG IDEAs Lab Glycemic Variability and Wearable Device Data (version 1.1.3). *PhysioNet*. https://doi.org/10.13026/aw6y-fc44
- Goldberger, A., Amaral, L., Glass, L., Hausdorff, J., Ivanov, P. C., Mark, R., Mietus, J. E., Moody, G. B., Peng, C. K., & Stanley, H. E. (2000). PhysioBank, PhysioToolkit, and PhysioNet: Components of a new research resource for complex physiologic signals. *Circulation*, 101(23), e215–e220.

`data/` is gitignored except this file; the dataset is reached through a symlink or `BIG_IDEAS_ROOT`, never copied into the tree.

**Expected local layout** (outside the tracked tree; `data/big-ideas-glycemic-wearable` is a symlink or `BIG_IDEAS_ROOT` points at it):

```
big-ideas-glycemic-wearable/1.1.3/
  SHA256SUMS.txt
  Demographics.csv
  001/ ACC_001.csv BVP_001.csv Dexcom_001.csv EDA_001.csv HR_001.csv IBI_001.csv TEMP_001.csv Food_Log_001.csv
  ...
  016/
```

Every file is verified against `SHA256SUMS.txt` before the loader reads it; a file that fails is not used.

**Obtaining it:** `curl -L -C - -o big-ideas-1.1.3.zip https://physionet.org/static/published-projects/big-ideas-glycemic-wearable/big-ideas-lab-glycemic-variability-and-wearable-device-data-1.1.3.zip` (4.7 GB; ~34 GB unzipped), or `wget -r -N -c -np https://physionet.org/files/big-ideas-glycemic-wearable/1.1.3/`.
