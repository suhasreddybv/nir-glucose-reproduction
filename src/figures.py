"""The README figure, from committed results CSVs only (aggregate numbers; no participant trace).

Top: RMSE mean over participants with the bootstrap 95 % CI, per method, one panel per regime;
the regime's reference baseline (B2 across participants, B1 within) as a dashed line and the
paper's number as a black diamond. Bottom: balanced accuracy of the classification per regime,
with the paper's numbers and chance (33.3 %). Writes figures/hero.png.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
MODEL, BASE, REF = "#2a78d6", "#8d8c87", "#eb6834"      # categorical slot 1, a neutral, slot 2


def _rows(name):
    with open(ROOT / "results" / name) as f:
        return list(csv.DictReader(f))


def main() -> None:
    b = {(r["regime"], r["baseline"]): r for r in _rows("baselines_summary.csv")}
    m = {(r["regime"], r["config"]): r for r in _rows("models_summary.csv")}
    c = {r["regime"]: r for r in _rows("classification_summary.csv")}
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                         "text.color": INK, "font.family": "DejaVu Sans"})
    fig = plt.figure(figsize=(11, 7.6), facecolor=SURFACE)
    gs = fig.add_gridspec(2, 3, height_ratios=[1.35, 1], hspace=0.62, wspace=0.12)
    regimes = [("R1_lopo", "Leave one person out\n(paper's population regime)", "B2_hba1c_sex_linear", "B2 HbA1c + sex", 21.22),
               ("R1_halves", "First half → second half\n(paper's personalised regime)", "B1_participant_mean", "B1 own first-half mean", 21.10),
               ("R3_blocked", "Time-blocked, 24-h exclusion\n(15 participants)", "B1_participant_mean", "B1 own mean", None)]
    methods = [("base", "B0_population_mean", "B0 population mean"), ("base", "B2_hba1c_sex_linear", "B2 HbA1c + sex"),
               ("base", "B1_participant_mean", "B1 own mean"), ("base", "B3_e4_linear", "B3 wrist linear (own)*"),
               ("model", "full_69", "XGBoost, 69 features"), ("model", "minus_food", "− food log"), ("model", "minus_e4", "− wrist"),
               ("model", "e4_only", "wrist + clock only"), ("model", "food_only", "food + clock only")]
    ax0 = None
    for k, (reg, title, ref_key, ref_label, paper) in enumerate(regimes):
        ax = fig.add_subplot(gs[0, k], sharey=ax0); ax0 = ax0 or ax
        ax.set_facecolor(SURFACE)
        ys = []
        for i, (kind, key, label) in enumerate(methods):
            r = (b if kind == "base" else m).get((reg, key))
            if r is None:
                continue
            y = len(methods) - 1 - i; ys.append((y, label))
            mean, lo, hi = float(r["rmse_mean"]), float(r["rmse_ci_lo"]), float(r["rmse_ci_hi"])
            col = MODEL if kind == "model" else BASE
            ax.plot([lo, hi], [y, y], color=col, lw=2, solid_capstyle="round", zorder=2)
            ax.plot(mean, y, "o", ms=8, color=col, mec=SURFACE, mew=2, zorder=3)
        ref = float(b[(reg, ref_key)]["rmse_mean"])
        ax.axvline(ref, color=REF, lw=2, ls=(0, (4, 3)), zorder=1)
        ax.text(ref, len(methods) - 0.35, f" {ref_label} {ref:.2f}", color=INK2, fontsize=8, va="bottom", ha="left")
        if paper is not None:
            yp = len(methods) - 1 - 4
            ax.plot(paper, yp + 0.38, "D", ms=7, color=INK, zorder=4)
            ax.text(paper + 0.25, yp + 0.38, f"paper {paper:.2f}", fontsize=8, va="center", color=INK)
        ax.set_title(title, fontsize=9.5, color=INK, loc="left")
        ax.set_xlim(16.5, 28.5); ax.set_ylim(-0.7, len(methods) + 0.4)
        ax.grid(axis="x", color=GRID, lw=0.8); ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="y", length=0)
        if k == 0:
            ax.set_yticks([len(methods) - 1 - i for i in range(len(methods))]); ax.set_yticklabels([l for _, _, l in methods])
        else:
            plt.setp(ax.get_yticklabels(), visible=False)
        ax.set_xlabel("RMSE, mg/dL (mean over participants, 95 % CI)", fontsize=8.5, color=INK2)
    fig.text(0.125, 0.965, "Regression: the paper's numbers reproduce, and a constant per participant reaches them", fontsize=11.5, color=INK, weight="bold")
    fig.text(0.125, 0.94, "Blue: the paper's XGBoost and its ablations. Grey: baselines. Dashed: the regime's reference baseline. "
             "*B3 on its own rows; paired comparisons in docs/baselines.md.", fontsize=8.5, color=INK2)
    # classification
    ax = fig.add_subplot(gs[1, :]); ax.set_facecolor(SURFACE)
    bars = [("R1_window_kfold", "Paper's split:\nwindows, 10-fold × 3", 84.3), ("R1_70_30_tree", "Paper's 70/30\nwindow split", 82.0),
            ("R1_70_30_logistic", "Logistic regression,\n70/30 (paper's comparator)", 52.0), ("R2_participant_grouped", "Participant-grouped\n10-fold × 3", None),
            ("R3_time_blocked", "Time-blocked within\nparticipant, 24-h zones", None)]
    for i, (key, label, paper) in enumerate(bars):
        r = c[key]; v = float(r["balanced_accuracy_mean"])
        col = MODEL if key != "R1_70_30_logistic" else BASE
        ax.bar(i, v, width=0.56, color=col, zorder=2)
        if r["balanced_accuracy_ci_lo"] not in ("", None):
            ax.plot([i, i], [float(r["balanced_accuracy_ci_lo"]), float(r["balanced_accuracy_ci_hi"])], color=INK, lw=1.5, zorder=3)
        ax.text(i, v + 1.5, f"{v:.1f} %", ha="center", va="bottom", fontsize=9, color=INK)
        if paper is not None:
            ax.plot(i + 0.36, paper, "D", ms=7, color=INK, zorder=4)
            ax.text(i + 0.43, paper, f"paper {paper:.1f}", fontsize=8, va="center", color=INK)
    ax.plot([-0.5, len(bars) - 0.45], [100 / 3, 100 / 3], color=REF, lw=2, ls=(0, (4, 3)), zorder=1)
    ax.set_xlim(-0.5, len(bars) + 0.15)
    ax.text(len(bars) - 0.4, 100 / 3, "chance\n33.3 %", ha="left", va="center", fontsize=8, color=INK2)
    ax.set_xticks(range(len(bars))); ax.set_xticklabels([l for _, l, _ in bars], fontsize=8.5)
    ax.set_ylim(0, 100); ax.set_ylabel("Balanced accuracy, %", fontsize=8.5, color=INK2)
    ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="x", length=0)
    ax.set_title("Classification (PersLow / PersNorm / PersHigh, class-balanced set N = 10,230): the result lives in the split",
                 fontsize=11.5, color=INK, loc="left", weight="bold", pad=10)
    (ROOT / "figures").mkdir(exist_ok=True)
    fig.savefig(ROOT / "figures" / "hero.png", dpi=170, facecolor=SURFACE, bbox_inches="tight")
    print("wrote figures/hero.png")


if __name__ == "__main__":
    main()
