#!/usr/bin/env python3
"""NET-T2 deep trajectory analysis — G5 tier.
Run from ~/shypn/ with .venv activated:
  python3 workspace/projects/thesis/scripts/analyse_net_t2_deep.py
"""
import csv, json, math, pathlib, re

RUN = pathlib.Path(
    "workspace/projects/thesis/experiments/results/run_20260704_201120"
)

FOCUS = {
    100:  "condition_[param]_INITIAL_NUTRIENTS_eq_100",
    900:  "condition_[param]_INITIAL_NUTRIENTS_eq_900",
    1200: "condition_[param]_INITIAL_NUTRIENTS_eq_1200",
    1440: "condition_Baseline",
    1600: "condition_[param]_INITIAL_NUTRIENTS_eq_1600",
    1800: "condition_[param]_INITIAL_NUTRIENTS_eq_1800",
    2000: "condition_[param]_INITIAL_NUTRIENTS_eq_2000",
}

def mean(v): return sum(v)/len(v) if v else float("nan")
def std(v):
    if len(v)<2: return 0.0
    m=mean(v); return math.sqrt(sum((x-m)**2 for x in v)/(len(v)-1))
def cv(v): m=mean(v); return std(v)/m if m else float("nan")

def read_traj(path):
    with open(path) as fh:
        lines = [l for l in fh if not l.startswith("#")]
    return list(csv.DictReader(lines))

def first_crossing(times, vals, threshold, above_to_below=True):
    for t, v in zip(times, vals):
        if above_to_below and v < threshold:
            return t
        if not above_to_below and v > threshold:
            return t
    return float("nan")

def atp_trajectory_shape(times_min, atp_mM):
    """Classify ATP trajectory shape."""
    t_min = min(range(len(atp_mM)), key=lambda i: atp_mM[i])
    atp_final = atp_mM[-1]
    atp_min   = atp_mM[t_min]
    atp_init  = atp_mM[0]
    drop      = atp_init - atp_min
    recovery  = atp_final - atp_min
    if drop < 0.05:
        return "flat"
    if recovery > 0.5 * drop:
        return "dip-recover"
    return "monotone-drop"


print("NET-T2 DEEP TRAJECTORY ANALYSIS")
print("Run:", RUN.name)
print("="*70)

for n0, cname in sorted(FOCUS.items()):
    cdir = RUN / cname
    if not cdir.exists():
        print(f"\nN0={n0}: directory missing")
        continue

    rows = list(csv.DictReader(open(cdir/"replicates.csv")))
    traj_files = sorted((cdir/"replicates_trajectories").glob("run_*.csv"))
    spore = [float(r.get("Mature_spore_final",0)) > 0.5 for r in rows]
    n_s = sum(spore); n = len(rows)

    # Per-replicate trajectory metrics
    atp_min_t, atp_min_v = [], []
    sh_peak_t, sh_peak_v = [], []
    sept_t = []
    sini_max, sinr_min = [], []
    spoa_peak = []
    shapes_spor, shapes_veg = [], []
    # Commitment timing relative to nutrient depletion
    nut_depl_t = []  # when Nutrients first = 0

    for i, traj_f in enumerate(traj_files):
        traj = read_traj(traj_f)
        if not traj: continue
        times  = [float(r["time"])/60 for r in traj]   # min
        atp    = [float(r.get("ATP_pool",5000))/1000 for r in traj]
        sigh   = [float(r.get("SigmaH",0)) for r in traj]
        sinr   = [float(r.get("SinR",8)) for r in traj]
        sini   = [float(r.get("SinI",0)) for r in traj]
        sept   = [float(r.get("Septum",0)) for r in traj]
        spoa   = [float(r.get("Spo0A_P",0)) for r in traj]
        nuts   = [float(r.get("Nutrients",0)) for r in traj]

        # ATP shape
        shape = atp_trajectory_shape(times, atp)
        if spore[i]: shapes_spor.append(shape)
        else:         shapes_veg.append(shape)

        # Nutrient depletion time
        nt = first_crossing(times, nuts, 1.0)
        nut_depl_t.append(nt)

        if spore[i]:
            idx_min = min(range(len(atp)), key=lambda k: atp[k])
            atp_min_t.append(times[idx_min]); atp_min_v.append(atp[idx_min])
            idx_sh = max(range(len(sigh)), key=lambda k: sigh[k])
            sh_peak_t.append(times[idx_sh]); sh_peak_v.append(sigh[idx_sh])
            sini_max.append(max(sini))
            sinr_min.append(min(sinr))
            spoa_peak.append(max(spoa))
            s_t = first_crossing(times, sept, 0.5, above_to_below=False)
            sept_t.append(s_t)

    # Covariance — find strongest cross-correlations
    cov_data = json.loads(open(cdir/"covariance.json").read())
    top_corr = []
    if "place_names" in cov_data and "covariance" in cov_data:
        names = cov_data["place_names"]
        mat   = cov_data["covariance"]
        n_p   = len(names)
        for a in range(n_p):
            for b in range(a+1, n_p):
                va = mat[a][a]; vb = mat[b][b]
                if va > 1e-15 and vb > 1e-15:
                    r_ab = mat[a][b] / math.sqrt(va*vb)
                    top_corr.append((abs(r_ab), r_ab, names[a], names[b]))
        top_corr.sort(reverse=True)

    # Nutrient depletion stats
    valid_depl = [t for t in nut_depl_t if not math.isnan(t)]
    depl_str = ("%.0f±%.0f min (%d/%d)" % (
        mean(valid_depl), std(valid_depl), len(valid_depl), n)
        if valid_depl else "never depleted")

    print(f"\nN0={n0} µM  |  {n_s}/{n} sporulated ({100*n_s/n:.0f}%)")
    print(f"  Nutrient depletion: {depl_str}")

    if atp_min_t:
        shape_count = {}
        for s in shapes_spor: shape_count[s] = shape_count.get(s,0)+1
        print(f"  [SPOR n={n_s}] ATP shape: " +
              ", ".join(f"{k}:{v}" for k,v in shape_count.items()))
        print(f"    ATP dip:    t={mean(atp_min_t):.0f}±{std(atp_min_t):.0f} min  val={mean(atp_min_v)*1000:.0f} µM")
        print(f"    σH peak:    t={mean(sh_peak_t):.0f}±{std(sh_peak_t):.0f} min  val={mean(sh_peak_v):.3f} µM")
        print(f"    Spo0A~P pk: {mean(spoa_peak):.2f} µM  SinI max: {mean(sini_max):.4f} µM")
        print(f"    SinR min:   {mean(sinr_min):.3f} µM  Septum t: {mean(sept_t):.0f}±{std(sept_t):.0f} min")
        if valid_depl and atp_min_t:
            lag = [atp_min_t[i] - valid_depl[i] for i in range(min(len(atp_min_t), len(valid_depl)))]
            print(f"    Depl→ATP dip lag: {mean(lag):.0f}±{std(lag):.0f} min")

    if n-n_s > 0:
        shape_count = {}
        for s in shapes_veg: shape_count[s] = shape_count.get(s,0)+1
        print(f"  [VEG  n={n-n_s}] ATP shape: " +
              ", ".join(f"{k}:{v}" for k,v in shape_count.items()))

    if top_corr:
        print(f"  Top correlations (final marking covariance):")
        for _, r_ab, na, nb in top_corr[:4]:
            sign = "+" if r_ab > 0 else "-"
            print(f"    {sign}{abs(r_ab):.3f}  {na} × {nb}")

print("\nDone.")
