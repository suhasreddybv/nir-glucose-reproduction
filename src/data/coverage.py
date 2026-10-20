"""Day 0 measured output: how much of each participant's record is usable, and what the
glucose looks like (D-006).

Per participant: E4 wear time (BVP present, in hours, counting gaps > 10 min as absent),
Dexcom span and coverage, the overlap between them (the only usable time), the gap
distribution of each, the number of 5-minute Dexcom readings with a complete E4 window of
WINDOW_MIN preceding them (no BVP gap inside the window), and the glucose distribution -
mean, SD, min, max, share below 70 and above 180, readings at the 40 / 400 censoring
edges - because this is a high-normal cohort and the narrowness of that range is the
central fact of the reproduction. Aggregate numbers only.

Writes results/coverage.csv and results/glucose_distribution.csv.
"""
from __future__ import annotations

import csv

import numpy as np

from src.data.loader import CGM_INTERVAL_S, PARTICIPANTS, REPO_ROOT, load_participant

WINDOW_MIN = 10          # the complete-window criterion used here; the paper's own length is a protocol cell
E4_GAP_S = 600           # BVP absence longer than this is a wear gap


def wear_segments(ts: np.ndarray, gap_s: float):
    """[start, end) of contiguous presence, splitting at gaps longer than gap_s."""
    t = ts.astype("datetime64[ns]").astype(np.int64) / 1e9
    cut = np.flatnonzero(np.diff(t) > gap_s)
    starts = np.r_[t[0], t[cut + 1]]; ends = np.r_[t[cut], t[-1]]
    return np.stack([starts, ends], axis=1)


def covered_seconds(segs: np.ndarray, lo: float, hi: float) -> float:
    return float(np.clip(np.minimum(segs[:, 1], hi) - np.maximum(segs[:, 0], lo), 0, None).sum())


def main() -> None:
    rows, glu = [], []
    for pid in PARTICIPANTS:
        rec, facts = load_participant(pid)
        bvp, cgm = rec["BVP"], rec.cgm
        e4 = wear_segments(bvp.ts, E4_GAP_S)
        cg = wear_segments(cgm.ts, CGM_INTERVAL_S + 120)
        lo, hi = max(e4[0, 0], cg[0, 0]), min(e4[-1, 1], cg[-1, 1])
        overlap_h = max(0.0, hi - lo) / 3600
        # readings with a complete E4 window before them
        t_cgm = cgm.ts.astype("datetime64[ns]").astype(np.int64) / 1e9
        complete = 0
        for t in t_cgm:
            w0 = t - WINDOW_MIN * 60
            if covered_seconds(e4, w0, t) >= WINDOW_MIN * 60 - 1:
                complete += 1
        d_e4 = np.diff(bvp.ts).astype("timedelta64[s]").astype(float); d_e4 = d_e4[d_e4 > E4_GAP_S]
        d_cg = np.diff(cgm.ts).astype("timedelta64[s]").astype(float); d_cg = d_cg[d_cg > CGM_INTERVAL_S + 120]
        rows.append(dict(participant=pid, gender=rec.gender, hba1c=rec.hba1c,
                         e4_span_h=round((e4[-1, 1] - e4[0, 0]) / 3600, 1), e4_wear_h=round((e4[:, 1] - e4[:, 0]).sum() / 3600, 1),
                         e4_gaps=len(d_e4), e4_longest_gap_h=round(d_e4.max() / 3600, 2) if len(d_e4) else 0.0,
                         cgm_span_h=round((cg[-1, 1] - cg[0, 0]) / 3600, 1), cgm_readings=len(cgm.values),
                         cgm_coverage=round(len(cgm.values) * CGM_INTERVAL_S / max(1, cg[-1, 1] - cg[0, 0]), 3),
                         cgm_gaps=len(d_cg), cgm_longest_gap_h=round(d_cg.max() / 3600, 2) if len(d_cg) else 0.0,
                         overlap_h=round(overlap_h, 1),
                         readings_with_complete_e4_window=complete, share_with_complete_window=round(complete / len(cgm.values), 3),
                         acc_median_magnitude_raw=round(facts["acc_median_magnitude_raw"], 2), acc_median_magnitude_g=round(facts["acc_median_magnitude_g"], 3),
                         bvp_resting_mean=round(facts["bvp_resting_hour_mean"], 3), bvp_resting_sd=round(facts["bvp_resting_hour_sd"], 2),
                         bvp_hz=round(facts["BVP_hz"], 2), acc_hz=round(facts["ACC_hz"], 2), eda_hz=round(facts["EDA_hz"], 2), temp_hz=round(facts["TEMP_hz"], 2)))
        v = cgm.values
        glu.append(dict(participant=pid, hba1c=rec.hba1c, n=len(v), mean=round(float(v.mean()), 1), sd=round(float(v.std()), 1),
                        min=float(v.min()), max=float(v.max()), p5=round(float(np.percentile(v, 5)), 1), p95=round(float(np.percentile(v, 95)), 1),
                        share_below_70=round(float((v < 70).mean()), 4), share_below_54=round(float((v < 54).mean()), 4),
                        share_above_180=round(float((v > 180).mean()), 4), share_above_250=round(float((v > 250).mean()), 4),
                        at_floor_40=facts["cgm_at_floor"], at_ceiling_400=facts["cgm_at_ceiling"]))
        print(f"  {pid}: E4 {rows[-1]['e4_wear_h']:.0f} h worn of {rows[-1]['e4_span_h']:.0f}, CGM {len(v)} readings ({rows[-1]['cgm_coverage']:.0%}), "
              f"overlap {overlap_h:.0f} h, complete-window readings {complete}; glucose {v.mean():.0f} ± {v.std():.0f}, "
              f"<70 {100 * (v < 70).mean():.1f}%, >180 {100 * (v > 180).mean():.1f}%", flush=True)
    for data, fn in ((rows, "coverage.csv"), (glu, "glucose_distribution.csv")):
        with open(REPO_ROOT / "results" / fn, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0])); w.writeheader(); w.writerows(data)
        print(f"wrote results/{fn}")
    all_v = np.concatenate([np.array([g["mean"]]) for g in glu])
    print(f"\ncohort: {sum(g['n'] for g in glu):,} readings; mean of participant means {all_v.mean():.1f} mg/dL; "
          f"pooled share <70 {sum(g['share_below_70'] * g['n'] for g in glu) / sum(g['n'] for g in glu):.2%}, >180 {sum(g['share_above_180'] * g['n'] for g in glu) / sum(g['n'] for g in glu):.2%}; "
          f"overlap {sum(r['overlap_h'] for r in rows):.0f} h; complete-window readings {sum(r['readings_with_complete_e4_window'] for r in rows):,}")


if __name__ == "__main__":
    main()
