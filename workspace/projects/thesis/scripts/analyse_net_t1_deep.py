#!/usr/bin/env python3
"""NET-T1 deep trajectory analysis — G5 tier.

Run from ~/shypn/ with .venv activated:
  python3 workspace/projects/thesis/scripts/analyse_net_t1_deep.py
"""
import csv
import json
import math
import pathlib
import sys

RUN = pathlib.Path(
    "workspace/projects/thesis/experiments/results/run_20260704_181236"
)

CONDITIONS = {
    10:  "condition_[param]_SIGMA_HALFLIFE_MIN_eq_10",
    20:  "condition_[param]_SIGMA_HALFLIFE_MIN_eq_20",
    30:  "condition_[param]_SIGMA_HALFLIFE_MIN_eq_30",
    60:  "condition_[param]_SIGMA_HALFLIFE_MIN_eq_60",
    90:  "condition_[param]_SIGMA_HALFLIFE_MIN_eq_90",
    120: "condition_Baseline",
    150: "condition_[param]_SIGMA_HALFLIFE_MIN_eq_150",
    200: "condition_[param]_SIGMA_HALFLIFE_MIN_eq_200",
    300: "condition_[param]_SIGMA_HALFLIFE_MIN_eq_300",
}


def _mean(lst):
    return sum(lst) / len(lst) if lst else float("nan")


def _std(lst):
    if len(lst) < 2:
        return 0.0
    m = _mean(lst)
    return math.sqrt(sum((x - m) ** 2 for x in lst) / (len(lst) - 1))


def _cv(lst):
    m = _mean(lst)
    return _std(lst) / m if m else float("nan")


def analyse_condition(hl, cname):
    cdir = RUN / cname
    rows = list(csv.DictReader(open(cdir / "replicates.csv")))
    traj_files = sorted((cdir / "replicates_trajectories").glob("run_*.csv"))
    spore_mask = [float(r.get("Mature_spore_final", 0)) > 0.5 for r in rows]
    n_spore = sum(spore_mask)
    n = len(rows)

    atp_dip_t, atp_dip_v = [], []
    sh_peak_t, sh_peak_v = [], []
    sinr_cross_t = []
    t_septum = []
    atp_cv_at_sh_peak = []   # ATP variability at the moment σH peaks
    sh_rise_rate = []        # µM/min during first rising phase

    for i, traj_f in enumerate(traj_files):
        with open(traj_f) as fh:
            lines = [l for l in fh if not l.startswith("#")]
        traj = list(csv.DictReader(lines))
        if not traj:
            continue
        times = [float(r["time"]) / 60 for r in traj]   # → minutes
        atp   = [float(r.get("ATP_pool", 0)) for r in traj]
        sigh  = [float(r.get("SigmaH", 0)) for r in traj]
        sinr  = [float(r.get("SinR", 8)) for r in traj]
        sept  = [float(r.get("Septum", 0)) for r in traj]

        if spore_mask[i]:
            # ATP minimum time (commitment dip)
            min_atp = min(atp)
            idx_dip = atp.index(min_atp)
            atp_dip_t.append(times[idx_dip])
            atp_dip_v.append(min_atp)

            # σH peak time and value
            max_sh = max(sigh)
            idx_sh = sigh.index(max_sh)
            sh_peak_t.append(times[idx_sh])
            sh_peak_v.append(max_sh)

            # σH rise rate: slope from t=0 to peak (µM/min)
            if idx_sh > 0:
                rate = (sigh[idx_sh] - sigh[0]) / max(times[idx_sh] - times[0], 1e-3)
                sh_rise_rate.append(rate)

            # SinR first crossing below 7.5 µM
            cross = [t for t, s in zip(times, sinr) if s < 7.5]
            sinr_cross_t.append(cross[0] if cross else float("nan"))

            # Septum first fired
            s_t = [t for t, s in zip(times, sept) if s > 0.5]
            t_septum.append(s_t[0] if s_t else float("nan"))

    # For non-sporulating: σH trajectory — does it plateau or decline?
    veg_sh_max, veg_sh_final, veg_atp_final = [], [], []
    for i, traj_f in enumerate(traj_files):
        if spore_mask[i]:
            continue
        with open(traj_f) as fh:
            lines = [l for l in fh if not l.startswith("#")]
        traj = list(csv.DictReader(lines))
        if not traj:
            continue
        sigh  = [float(r.get("SigmaH", 0)) for r in traj]
        atp   = [float(r.get("ATP_pool", 0)) for r in traj]
        veg_sh_max.append(max(sigh))
        veg_sh_final.append(sigh[-1])
        veg_atp_final.append(atp[-1])

    # Covariance: find strongest correlations in final marking
    cov_data = json.loads(open(cdir / "covariance.json").read())

    print(f"\n{'='*65}")
    print(f"  HL={hl} min  |  {n_spore}/{n} sporulated  ({100*n_spore/n:.0f}%)")
    print(f"{'='*65}")

    if atp_dip_t:
        valid_sinr = [t for t in sinr_cross_t if not math.isnan(t)]
        valid_sept = [t for t in t_septum if not math.isnan(t)]
        print(f"  [SPORULATING replicates — n={n_spore}]")
        print(f"  ATP dip:       t={_mean(atp_dip_t):.1f} ± {_std(atp_dip_t):.1f} min   val={_mean(atp_dip_v):.0f} µM")
        print(f"  σH peak:       t={_mean(sh_peak_t):.1f} ± {_std(sh_peak_t):.1f} min   peak={_mean(sh_peak_v):.3f} µM")
        if sh_rise_rate:
            print(f"  σH rise rate:  {_mean(sh_rise_rate):.4f} ± {_std(sh_rise_rate):.4f} µM/min   CV={_cv(sh_rise_rate):.2f}")
        if valid_sinr:
            print(f"  SinR < 7.5:    t={_mean(valid_sinr):.1f} ± {_std(valid_sinr):.1f} min   ({len(valid_sinr)}/{n_spore})")
        if valid_sept:
            print(f"  Septum fires:  t={_mean(valid_sept):.1f} ± {_std(valid_sept):.1f} min   ({len(valid_sept)}/{n_spore})")
        if valid_sinr and valid_sept:
            lag = [b - a for a, b in zip(valid_sinr[:len(valid_sept)], valid_sept[:len(valid_sinr)])]
            print(f"  SinR→Septum lag: {_mean(lag):.1f} ± {_std(lag):.1f} min")

    if veg_sh_max:
        print(f"  [VEGETATIVE replicates — n={len(veg_sh_max)}]")
        print(f"  σH max: {_mean(veg_sh_max):.3f} µM   σH final: {_mean(veg_sh_final):.3f} µM")
        print(f"  ATP final (veg): {_mean(veg_atp_final):.0f} µM = {_mean(veg_atp_final)/1000:.3f} mM")

    # Covariance structure
    if isinstance(cov_data, dict):
        keys_available = list(cov_data.keys())
        if "place_names" in cov_data and "matrix" in cov_data:
            names = cov_data["place_names"]
            mat = cov_data["matrix"]
            # Find top off-diagonal correlations
            pairs = []
            n_p = len(names)
            for a in range(n_p):
                for b in range(a+1, n_p):
                    var_a = mat[a][a] if mat[a][a] > 0 else 1e-30
                    var_b = mat[b][b] if mat[b][b] > 0 else 1e-30
                    corr = mat[a][b] / math.sqrt(var_a * var_b)
                    pairs.append((abs(corr), corr, names[a], names[b]))
            pairs.sort(reverse=True)
            print(f"  Top 5 correlations in final marking:")
            for _, corr, na, nb in pairs[:5]:
                print(f"    {na} × {nb}: r={corr:.3f}")
        else:
            print(f"  Covariance keys: {keys_available[:6]}")


# ── main ─────────────────────────────────────────────────────────────────────
print("NET-T1 DEEP ANALYSIS — G5 tier trajectories + covariance")
print(f"Run: {RUN.name}")

for hl in sorted(CONDITIONS):
    cname = CONDITIONS[hl]
    cdir = RUN / cname
    if cdir.exists():
        analyse_condition(hl, cname)
    else:
        print(f"\nHL={hl}: directory not found ({cname})")

print("\nDone.")
