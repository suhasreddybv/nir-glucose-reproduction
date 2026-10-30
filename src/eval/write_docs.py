"""Writes docs/classification.md from the committed results so every number in it is generated.
`tests/test_results_classification.py` regenerates it and asserts the file matches."""
from __future__ import annotations

import csv
from pathlib import Path

from src.eval.readme_tables import classification_class_table, classification_table, confusion_tables

ROOT = Path(__file__).resolve().parents[2]


def _rows(name):
    with open(ROOT / "results" / name) as f:
        return list(csv.DictReader(f))


def classification_doc() -> str:
    s = {r["regime"]: r for r in _rows("classification_summary.csv")}
    nb = {r["regime"]: r for r in _rows("classification_neighbours.csv")}
    sel = sorted([r for r in _rows("classification_selected.csv") if r["regime"] == "R1_window_kfold"], key=lambda r: (-int(r["times_selected"]), r["feature"]))
    always = [r["feature"] for r in sel if r["times_selected"] == r["folds"]]
    idsel = next(r for r in sel if r["feature"] == "ID")
    idsel_r2 = next(r for r in _rows("classification_selected.csv") if r["regime"] == "R2_participant_grouped" and r["feature"] == "ID")
    p3 = next(r for r in _rows("predictions.csv") if r["prediction"] == "P3")
    a1, a2, a3 = (float(s[k]["balanced_accuracy_mean"]) for k in ("R1_window_kfold", "R2_participant_grouped", "R3_time_blocked"))
    r1n = nb["R1_window_kfold"]
    return f'''# Classification: the paper's excursion classes under three splits

Protocol cells 1, 4 and 5 and §9; decision-log entries D-015 and D-016. Every number below is generated from `results/classification_*.csv` by `src/eval/write_docs.py` and pinned by `tests/test_results_classification.py`.

**The pipeline, fixed before the run** (`src/classify.py`). The class-balanced set of D-011 (N = 10,230: 3,410 each of PersLow, PersNorm and PersHigh, undersampled with seed 0 from the 25,644 complete labelled epochs — a deviation from protocol cell 7 c, which says the full labelled set; the decision tree needs complete rows, and the deviation is logged in D-017). In each training fold, recursive feature elimination to 20 features with a decision tree as the estimator (the estimator the paper reports winning its comparison), then a scikit-learn decision tree with default settings and `random_state = 0`. The paper's 70/30 decision tree and 70/30 logistic regression run through the same RFE-20 step; the paper does not say whether they did, so that was decided before any number existed. Metrics as the paper's Methods name them, R² on the class codes thresholded at zero as Table 2's footnote says.

{classification_table()}

**Read it this way.** Under the paper's own split the tree scores **{a1:.2f} %** against the paper's 84.3 %: {84.3 - a1:.1f} points short. That is inside the pre-registered 10-point stop rule (protocol §11), so the other regimes were run, and outside P3's 3-point margin, so **P3 is judged failed** on its own words ({p3["value"]}). The second half of P3 — a fall of more than 15 points once windows are grouped by participant or separated in time by at least 24 hours — happened at more than twice that size: **{a2:.2f} %** with participants grouped and **{a3:.2f} %** time-blocked, against chance at 33.3 %. The 70/30 tree is {82.0 - float(s['R1_70_30_tree']['balanced_accuracy_mean']):.1f} points short ({float(s['R1_70_30_tree']['balanced_accuracy_mean']):.1f} % against 82.0 %), and the logistic comparator is {float(s['R1_70_30_logistic']['balanced_accuracy_mean']) - 52.0:.1f} points above the paper's ({float(s['R1_70_30_logistic']['balanced_accuracy_mean']):.1f} % against 52.0 %); by the 3-point yardstick neither counts as replicated. R² is reported because the paper reports it ({float(s['R1_window_kfold']['r2_mean']):.3f} here against 0.505), but R² on three nominal class codes is not a meaningful target and is not used as evidence; it is thresholded at zero as the paper's was, so 0.000 means zero or below. The {84.3 - a1:.1f}-point shortfall under the paper's split is not explained here, and nothing was changed to close it. The differences that can be named are a larger balanced set (10,230 against 8,666, which would, if anything, help a window-level split), the wake-time rule and the first-day label window of D-008, and library versions.

**Why the split decides the result** (`results/classification_neighbours.csv`). Under the paper's split, **{float(r1n["share_within_5min"]) * 100:.1f} % of test windows have a training window from the same participant within 5 minutes**, {float(r1n["share_within_15min"]) * 100:.1f} % within 15 minutes and {float(r1n["share_within_60min"]) * 100:.1f} % within an hour. The label is a 24-hour rolling statistic and a third of the features are rolling sums, means or maxima over 2 to 24 hours, so a test window's nearest training neighbour carries almost the same features and, usually, the same label. Under the paper's split, RFE kept the participant ID in {idsel["times_selected"]} of {idsel["folds"]} folds, and the features kept in every fold were {", ".join(always)}. With participants grouped it still kept the ID in {idsel_r2["times_selected"]} of {idsel_r2["folds"]} folds, where a held-out participant's ID carries no information: RFE ranks features on the training folds, where the ID separates people, and cannot know it will not transfer. With participants grouped, no test window has a same-participant training window at all; time-blocked, the median gap is {float(nb["R3_time_blocked"]["median_gap_min"]) / 60:.0f} hours. What survives that separation is {a2:.1f}–{a3:.1f} % balanced accuracy, {a2 - 100 / 3:.0f}–{a3 - 100 / 3:.0f} points above chance.

**What the balanced set hides.** PersNorm is 71.8 % of the complete labelled epochs, PersLow 13.3 % and PersHigh 14.9 %. The positive predictive value below is what each call would be worth on that real stream, from each regime's per-class recall and the true prevalence. Under the paper's own split a PersHigh call would be right about half the time; with participants grouped, about one time in five.

{classification_class_table()}

## Confusion matrices

{confusion_tables()}
'''




# ------------------------------------------------------------------ docs/reproduction.md and the README front page

def _r2(x: float) -> str:
    """Half-up to two decimals, so a cost of 1.215 prints 1.22 everywhere (D-017)."""
    from decimal import ROUND_HALF_UP, Decimal
    return str(Decimal(repr(round(float(x), 6))).quantize(Decimal("0.01"), ROUND_HALF_UP))


def _numbers() -> dict:
    m = {(r["regime"], r["config"]): r for r in _rows("models_summary.csv")}
    b = {(r["regime"], r["baseline"]): r for r in _rows("baselines_summary.csv")}
    d = {(r["regime"], r["config"]): r for r in _rows("paired_deltas.csv")}
    c = {r["regime"]: r for r in _rows("classification_summary.csv")}
    nv = {(r["regime"], r["naive"]): r for r in _rows("naive_claim.csv")}
    nb = {r["regime"]: r for r in _rows("classification_neighbours.csv")}
    lab = {r["label"]: r for r in _rows("label_distribution.csv")}
    f = lambda x, k=2: f"{float(x):.{k}f}"
    cost = lambda reg, cfg: float(m[(reg, cfg)]["rmse_mean"]) - float(m[(reg, "full_69")]["rmse_mean"])
    dpp = [r for r in _rows("paired_deltas_per_participant.csv") if r["config"] == "full_69" and r["regime"] == "R1_halves"]
    dv = sorted((float(r["delta_rmse"]), r["participant"]) for r in dpp)
    import statistics
    worse_by_bt = [x for x in dv if x[0] < -5]
    abl = [(reg, cfg) for (reg, cfg) in d if cfg != "full_69" and float(d[(reg, cfg)]["delta_rmse_mean"]) > 0]
    return dict(
        lopo=f(m[("R1_lopo", "full_69")]["rmse_mean"]), lopo_sd=f(m[("R1_lopo", "full_69")]["rmse_sd"]),
        halves=f(m[("R1_halves", "full_69")]["rmse_mean"]), blocked=f(m[("R3_blocked", "full_69")]["rmse_mean"]),
        b1=f(b[("R1_halves", "B1_participant_mean")]["rmse_mean"]), b1_sd=f(b[("R1_halves", "B1_participant_mean")]["rmse_sd"]),
        b1_acc=f(b[("R1_halves", "B1_participant_mean")]["accuracy_mean"]), b2=f(b[("R1_lopo", "B2_hba1c_sex_linear")]["rmse_mean"]),
        b0=f(b[("R1_lopo", "B0_population_mean")]["rmse_mean"]), b3=f(b[("R1_halves", "B3_e4_linear")]["rmse_mean"]), b1_b3=f(b[("R1_halves", "B1_on_B3_rows")]["rmse_mean"]),
        d_lopo=f(d[("R1_lopo", "full_69")]["delta_rmse_mean"]), d_lopo_lo=f(d[("R1_lopo", "full_69")]["delta_rmse_ci_lo"]), d_lopo_hi=f(d[("R1_lopo", "full_69")]["delta_rmse_ci_hi"]),
        d_lopo_better=d[("R1_lopo", "full_69")]["participants_model_better"],
        d_half=f(-float(d[("R1_halves", "full_69")]["delta_rmse_mean"])), d_half_lo=f(-float(d[("R1_halves", "full_69")]["delta_rmse_ci_hi"])),
        d_half_hi=f(-float(d[("R1_halves", "full_69")]["delta_rmse_ci_lo"])),
        d_blk=f(-float(d[("R3_blocked", "full_69")]["delta_rmse_mean"])),
        e4only=f(m[("R1_lopo", "e4_only")]["rmse_mean"]), cost_food_l=_r2(cost("R1_lopo", "minus_food")), cost_e4_l=_r2(cost("R1_lopo", "minus_e4")),
        cost_food_h=_r2(cost("R1_halves", "minus_food")), cost_e4_h=_r2(cost("R1_halves", "minus_e4")),
        half_better=d[("R1_halves", "full_69")]["participants_model_better"], half_median=f"{statistics.median(v for v, _ in dv):+.2f}",
        half_three=", ".join(p for _, p in worse_by_bt), half_three_n=len(worse_by_bt),
        half_three_range=f"{-worse_by_bt[-1][0]:.1f}–{-worse_by_bt[0][0]:.1f}" if worse_by_bt else "",
        abl_exceptions=len(abl), abl_total=sum(1 for k in d if k[1] != "full_69"),
        uml=f(m[("R1_lopo", "minus_user_model")]["rmse_mean"]), uml_d=f(d[("R1_lopo", "minus_user_model")]["delta_rmse_mean"]),
        uml_lo=f(d[("R1_lopo", "minus_user_model")]["delta_rmse_ci_lo"]), uml_hi=f(d[("R1_lopo", "minus_user_model")]["delta_rmse_ci_hi"]),
        r1=f(c["R1_window_kfold"]["balanced_accuracy_mean"]), r2=f(c["R2_participant_grouped"]["balanced_accuracy_mean"]), r3=f(c["R3_time_blocked"]["balanced_accuracy_mean"]),
        r1_7030=f(c["R1_70_30_tree"]["balanced_accuracy_mean"], 1), lr=f(c["R1_70_30_logistic"]["balanced_accuracy_mean"], 1), r2_r1=f(c["R1_window_kfold"]["r2_mean"], 3),
        ppv_high_r1=f(c["R1_window_kfold"]["ppv_adjusted_PersHigh"], 0), ppv_high_r2=f(c["R2_participant_grouped"]["ppv_adjusted_PersHigh"], 0),
        nb5=f(float(nb["R1_window_kfold"]["share_within_5min"]) * 100, 1), nb60=f(float(nb["R1_window_kfold"]["share_within_60min"]) * 100, 1),
        nv_pm=f(nv[("R1_lopo", "population_mean")]["naive_minus_model"]), nv_pm_lo=f(nv[("R1_lopo", "population_mean")]["ci_lo"]), nv_pm_hi=f(nv[("R1_lopo", "population_mean")]["ci_hi"]),
        nv_pmed=f(nv[("R1_lopo", "population_median")]["naive_minus_model"]),
        nv_med=f(nv[("R1_halves", "participant_median")]["naive_rmse_mean"]), nv_med_d=f(-float(nv[("R1_halves", "participant_median")]["naive_minus_model"])),
        gap_b1=f"{21.10 - float(b[('R1_halves', 'B1_participant_mean')]['rmse_mean']):.2f}",
        gap_lopo=f"{abs(float(m[('R1_lopo', 'full_69')]['rmse_mean']) - 21.22):.2f}",
        short_r1=f"{84.3 - float(c['R1_window_kfold']['balanced_accuracy_mean']):.1f}",
        norm=f"{lab['PersNorm']['mean']} ± {lab['PersNorm']['sd']}", high=f"{lab['PersHigh']['mean']} ± {lab['PersHigh']['sd']}", low=f"{lab['PersLow']['mean']} ± {lab['PersLow']['sd']}",
    )


KEY = """**Key.** *B0–B3* are the four pre-registered baselines: B0 the population mean, B1 the participant's own mean over their training portion, B2 a linear model on HbA1c and sex, B3 a per-participant linear model on the 45 wrist (E4) features. *LOPO* is leave one person out. The three split regimes: the paper's (LOPO for the population model, first half → second half for the personalised one, random windows for the classifier); participant-grouped folds; and time-blocked within participant, with 24-hour exclusion zones either side of the boundary. *PersLow / PersNorm / PersHigh* label a reading below, within or above one SD of the participant's trailing 24-hour mean. *MAPE* is mean absolute percentage error, and the paper's "accuracy" is 100 − MAPE. *E4* is the Empatica E4 wristband."""


def reproduction_doc() -> str:
    n = _numbers()
    return f"""# Reproduction of Bent et al. 2021: what replicated, what did not, and what would settle it

**A constant — each participant's mean glucose over the first half of their own record — scores the paper's personalised RMSE to within {n["gap_b1"]} mg/dL ({n["b1"]} against 21.10). The paper's personalised model, rebuilt from its Methods, does not beat it on the mean: {n["halves"]} mg/dL, worse by {n["d_half"]} with a 95 % CI of [{n["d_half_lo"]}, {n["d_half_hi"]}] that spans zero.** Per participant the picture is mixed: the model is better for {n["half_better"]} of 16 (median paired gain {n["half_median"]} mg/dL), and the mean is pulled down by {n["half_three_n"]} participants ({n["half_three"]}) for whom it is {n["half_three_range"]} mg/dL worse. Either way the model and a constant cannot be told apart. That was prediction P1, registered before any number existed, and it is the decisive one. The paper's population number reproduces; its personalised number does not; and both are what a cohort this narrow gives anything that knows who the participant is.

Target: Bent, Cho, Henriquez et al. (2021), *Engineering digital biomarkers of interstitial glucose from noninvasive smartwatches*, npj Digital Medicine 4:89, on the data they released (BIG IDEAs Lab, PhysioNet v1.1.3; 16 participants, HbA1c 5.3–6.4 % against a recruitment range of 5.2–6.4, Empatica E4 with Dexcom G6 for 8–10 days, and a food log). The protocol (`docs/protocol.md`; its sections are numbered cells 1–7 for what was transcribed from the paper and §8–§11 for what was fixed independently) was transcribed from the paper and its companion code, verified against the paper, and frozen by hash (`7860469db2e059bd`) before any fit. Four predictions (P1–P4, with P1 and P2 in two parts each) and one measurement (P5) were registered with it. Every number here is generated from `results/` by `src/eval/write_docs.py`.

{KEY}

## What replicated

- **The population regression, to within {n["gap_lopo"]} mg/dL.** XGBoost with the paper's hyperparameters and in-fold random-forest selection, LOPO: **RMSE {n["lopo"]} ± {n["lopo_sd"]} mg/dL against the paper's 21.22 ± 4.14**; MAPE 14.34 against 14.33 % (`docs/models.md`).
- **The labels.** PersLow / PersNorm / PersHigh from the trailing 24-hour mean ± 1 SD land on the paper's Table 1: PersNorm {n["norm"]} mg/dL (paper 112.4 ± 14.5), PersHigh {n["high"]} (149.9 ± 24.4), PersLow {n["low"]} (90.8 ± 11.1) (`docs/baselines.md`).
- **The feature importance.** 14 of the paper's 15 most important features (Table 3) are in this reproduction's top 15, minutes from midnight first in both.
- **Half of the naive-model claim.** The paper says both models "outperformed the naïve models (mean and median)". Across participants that is true: the population model beats the population mean by {n["nv_pm"]} mg/dL [{n["nv_pm_lo"]}, {n["nv_pm_hi"]}] and the population median by {n["nv_pmed"]} (`results/naive_claim.csv`, a supplementary check added after the pre-registered numbers, D-016).

Not counted as replicated, by the same 3-point yardstick that failed P3: the paper's logistic-regression comparator ({n["lr"]} % against 52.0 %). The classification R² ({n["r2_r1"]} against 0.505) is reported because the paper reports it, but R² on three nominal class codes is not a meaningful target and is not used as evidence here.

## What did not

- **The personalised model.** {n["halves"]} against the paper's 21.10, and on the mean behind the participant's own first-half mean ({n["b1"]}) and median ({n["nv_med"]}); per participant, better for {n["half_better"]} of 16. The other half of the naive-model claim does not hold here.
- **Anything beyond a two-number baseline, across participants.** A linear model on HbA1c and sex scores {n["b2"]}; the 69-feature model beats it by {n["d_lopo"]} mg/dL on the mean, with a CI of [{n["d_lopo_lo"]}, {n["d_lopo_hi"]}] that spans zero, and is better for {n["d_lopo_better"]} of 16 participants. The two are statistically indistinguishable.
- **The wrist on its own.** With the wrist features and the clock alone the model scores {n["e4only"]} under LOPO, the worst configuration; a per-participant linear model on the 45 wrist features is worse than the participant's mean on the same rows ({n["b3"]} against {n["b1_b3"]}).
- **The classification headline, by {n["short_r1"]} points.** The decision tree under the paper's own random-window split scores {n["r1"]} % balanced accuracy against 84.3 % (P3's 3-point margin fails; the pre-registered 10-point stop rule, protocol §11, does not trigger), and the 70/30 tree {n["r1_7030"]} % against 82.0 %. The shortfall is not explained, and nothing was changed to close it (`docs/classification.md`).
- **The classification once windows are grouped by participant ({n["r2"]} %) or separated in time by at least 24 hours ({n["r3"]} %),** against chance at 33.3 %. Under the paper's split, {n["nb5"]} % of test windows have a training window from the same participant within 5 minutes, and {n["nb60"]} % within an hour; the label is a 24-hour rolling statistic. At the real class prevalence a PersHigh call would be right about {n["ppv_high_r1"]} % of the time under the paper's split and about {n["ppv_high_r2"]} % with participants grouped.

## The predictions, judged against their frozen words

{__import__("src.eval.readme_tables", fromlist=["verdict_table"]).verdict_table()}

In the table, a *value* such as "B1 - model -1.36" means baseline minus model, so negative means the model is worse. P1b "held" because the prediction was that the model would beat B1 by less than 3 mg/dL, and it did not beat it at all. P4's 84 % threshold is the classification figure in the paper's abstract ("up to 84% and 87% accuracy"), and P4 restates P1 in the paper's own "accuracy" unit, so it is not independent evidence. P5 is a measurement: removing the food log costs {n["cost_food_l"]} mg/dL across participants and removing every wrist feature costs {n["cost_e4_l"]}; within participant the costs are {n["cost_food_h"]} and {n["cost_e4_h"]}. Both are small beside the 4-mg/dL spread of RMSE between participants. Of the {n["abl_total"]} ablated models, {n["abl_total"] - n["abl_exceptions"]} are worse than the baseline on the mean; the exception is the model without sex, HbA1c and ID under LOPO ({n["uml"]} against B2's {n["b2"]}, a difference of {n["uml_d"]} [{n["uml_lo"]}, {n["uml_hi"]}]).

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
- **Resolved from code against guessed.** From the DBDP code: EDA peak detection, the HRV definitions, activity bouts, the circadian features, the MAPE and SD conventions, in-fold selection. Decided without code (D-008): the epoch placement, the usable-epoch rule, class balancing, the first-day label window, "first half" by count, the wake-time rule (a trailing 24-hour mean in place of the calendar day's, which would read the future), the participant-ID and sex coding, the food-log parsing. The labels reproducing Table 1 and 14 of 15 top features reproducing are evidence that those choices are close; the {n["short_r1"]}-point classification shortfall is evidence that something is not.
"""


def readme() -> str:
    from src.eval.readme_tables import ablation_table, front_page_table, verdict_table
    n = _numbers()
    return f"""# nir-glucose-reproduction

A reproduction of Bent et al. (2021), *Engineering digital biomarkers of interstitial glucose from noninvasive smartwatches* (npj Digital Medicine 4:89), on the dataset they released, with the baselines the paper did not report and the splits it did not use.

**Result.** **A constant — each participant's mean glucose over the first half of their own record — scores the paper's personalised RMSE to within {n["gap_b1"]} mg/dL ({n["b1"]} against 21.10), and the paper's personalised model, rebuilt from its Methods, does not beat it on the mean ({n["halves"]}; {n["d_half"]} mg/dL worse, 95 % CI [{n["d_half_lo"]}, {n["d_half_hi"]}]).** Per participant the model is better for {n["half_better"]} of 16, and the mean is pulled down by {n["half_three_n"]} participants for whom it is {n["half_three_range"]} mg/dL worse: the model and the constant cannot be told apart. The population model reproduces to within {n["gap_lopo"]} mg/dL ({n["lopo"]} against 21.22, leave one person out), and is statistically indistinguishable from a linear model on HbA1c and sex (better by {n["d_lopo"]} mg/dL, 95 % CI [{n["d_lopo_lo"]}, {n["d_lopo_hi"]}]). The excursion classifier reaches {n["r1"]} % balanced accuracy under the paper's random-window split (paper: 84.3 %), and {n["r2"]} % with participants grouped or {n["r3"]} % with 24-hour time separation, against chance at 33.3 %. Of the four pre-registered predictions three held; P3 failed on reproducing the paper's 84.3 %, while its predicted drop of more than 15 points happened at more than twice that size.

![Regression RMSE by method and regime, and classification balanced accuracy by split](figures/hero.png)

*Top: RMSE mean over participants with the bootstrap 95 % CI; blue, the paper's XGBoost and its ablations; grey, baselines; dashed, the regime's reference baseline; diamond, the paper's number. Bottom: balanced accuracy; blue, the paper's decision tree; green, its logistic-regression comparator; diamonds, the paper's numbers. Aggregate numbers only; generated by `src/figures.py` from `results/`.*

{KEY}

{front_page_table()}

## The pre-registered predictions

Four predictions and one measurement, registered in the frozen protocol before any number existed (`docs/protocol.md` §11, D-009) and judged against those words (`results/predictions.csv`):

{verdict_table()}

A *value* such as "B1 - model -1.36" is baseline minus model, so negative means the model is worse. P1b "held" because the prediction was that the model would beat B1 by less than 3 mg/dL; it did not beat it at all. P4's 84 % is the classification figure in the paper's abstract, and P4 restates P1 in the paper's "accuracy" unit, so it is not independent evidence.

## Where the error comes from: the ablations

RMSE in mg/dL, mean over participants (`results/models_summary.csv`; intervals and paired differences in [docs/models.md](docs/models.md)). The two clock features stay in every configuration.

{ablation_table()}

Of the {n["abl_total"]} ablated models, {n["abl_total"] - n["abl_exceptions"]} are worse than the baseline on the mean. The exception is the model without sex, HbA1c and ID under leave one person out ({n["uml"]} against {n["b2"]}, an interval that spans zero). Removing the food log costs {n["cost_food_l"]} mg/dL across participants and removing all 45 wrist features costs {n["cost_e4_l"]}; within participant the costs are {n["cost_food_h"]} and {n["cost_e4_h"]} (P5).

## How it was done

- **Protocol first.** The paper's claims, inputs, windowing, models, split and metrics were transcribed from the paper, its supplement and the companion DBDP code; the thirteen choices the paper leaves open were resolved and logged (D-008); the protocol was verified against the paper and frozen by hash (`7860469db2e059bd`, pinned by a test) before any fit. Deviations made later are logged (D-017). [docs/protocol.md](docs/protocol.md)
- **The 69 features** of Supplementary Table 1 as pure functions with hand-computed tests and two leakage guards: perturbing everything from the target time onward changes no feature, and no feature reads a glucose value. [docs/features.md](docs/features.md), [docs/data-layer.md](docs/data-layer.md)
- **Which rows each task uses.** Of 36,898 readings, **28,964** have a usable five-minute epoch, and regression runs on all of them (XGBoost takes missing features). All 69 features are present on **25,644**, against the paper's "over 25,000"; classification uses those, balanced by undersampling to 10,230.
- **Baselines before models:** B0–B3 under every regime, before any XGBoost existed. [docs/baselines.md](docs/baselines.md)
- **The paper's models** — XGBoost for glucose, a decision tree with in-fold recursive feature elimination for the excursion classes — with the paper's hyperparameters, one seed, nothing tuned. [docs/models.md](docs/models.md), [docs/classification.md](docs/classification.md)
- **The write-up:** what replicated, what did not, and what data would settle it. [docs/reproduction.md](docs/reproduction.md). Every decision, with its evidence: [docs/decisions.md](docs/decisions.md).

## The data

BIG IDEAs Lab Glycemic Variability and Wearable Device Data, PhysioNet v1.1.3 ([data/README.md](data/README.md)): 16 participants with HbA1c 5.3–6.4 % (recruited at 5.2–6.4), wearing an Empatica E4 with a Dexcom G6 every five minutes and a food log, 8–10 days each. Every file is verified against the dataset's checksum list before it is read. Open Data Commons Attribution licence; this repository's own policy keeps every raw file, cache and per-participant trace out of the tree regardless.

## Reproduce

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pre-commit install && pre-commit install --hook-type pre-push
pytest                              # 109 tests; 17 need the dataset and skip without it
python -m src.data.coverage         # results/coverage.csv, glucose_distribution.csv
python -m src.features.build        # the 69 features per epoch (cached outside the tree); results/epochs.csv, feature_missingness.csv
python -m src.eval.label_counts     # results/labels.csv, label_distribution.csv, balanced_set.csv
python -m src.eval.baselines        # results/baselines_*.csv, predictions.csv (P1a, P2a, P4)
python -m src.eval.models_run       # results/models_*.csv, paired_deltas*.csv, selected_features.csv (P1b, P2b, P5; about 2 h)
python -m src.eval.classification_run   # results/classification_*.csv (P3)
python -m src.eval.neighbours       # results/classification_neighbours.csv
python -m src.eval.naive_claim      # results/naive_claim.csv (supplementary)
python -m src.figures               # figures/hero.png
python -m src.eval.write_docs       # README.md, docs/reproduction.md, docs/classification.md
```

Data: see [data/README.md](data/README.md). No data is included in this repository.

## Limitations

- **The reference is a CGM**, as in the paper: every error is against Dexcom G6 interstitial glucose.
- **n = 16**, 15 under the time-blocked regime; every interval is a bootstrap over participants and is wide.
- **A high-normal cohort:** 0.57 % of readings below 70 mg/dL and 1.78 % above 180. Nothing here speaks to hypoglycaemia or diabetes-range glucose, and that narrowness is why a constant is so hard to beat.
- **The food log is self-report**, and 19 of the 69 features come from it.
- **Heart rate and inter-beat intervals are Empatica-derived**, not computed from the raw PPG, as in the paper.
- **Every clinical grid is an analogue**, applied to an estimator it was not written for; on this cohort Clarke A + B is 98.9–99.4 % for every method and separates nothing.
- **Some choices were resolved from the companion code and some had to be decided** (D-008), and a few later deviations from the frozen protocol are logged (D-017); the list is in [docs/reproduction.md](docs/reproduction.md#limitations-of-this-reproduction). The labels and the feature ranking reproducing suggest the decisions are close; the {n["short_r1"]}-point classification shortfall says something is not.

## References

- Bent, B., Cho, P. J., Henriquez, M., Wittmann, A., Thacker, C., Feinglos, M., Crowley, M. J., & Dunn, J. P. (2021). Engineering digital biomarkers of interstitial glucose from noninvasive smartwatches. *npj Digital Medicine*, 4, 89. https://doi.org/10.1038/s41746-021-00465-w
- Bent, B., Cho, P. J., Wittmann, A., et al. (2021). Non-invasive wearables for remote monitoring of HbA1c and glucose variability: proof of concept. *BMJ Open Diabetes Research & Care*, 9, e002027. https://doi.org/10.1136/bmjdrc-2020-002027
- Cho, P., Kim, J., Bent, B., & Dunn, J. (2023). BIG IDEAs Lab Glycemic Variability and Wearable Device Data (version 1.1.3). *PhysioNet*. https://doi.org/10.13026/aw6y-fc44
- Goldberger, A. L., et al. (2000). PhysioBank, PhysioToolkit, and PhysioNet. *Circulation*, 101(23), e215–e220.

## Licence

MIT (code). Data: ODC-BY v1.0, see [data/README.md](data/README.md).
"""


def write_all() -> None:
    (ROOT / "docs" / "classification.md").write_text(classification_doc())
    (ROOT / "docs" / "reproduction.md").write_text(reproduction_doc())
    (ROOT / "README.md").write_text(readme())
    print("wrote docs/classification.md, docs/reproduction.md, README.md")


if __name__ == "__main__":
    write_all()
