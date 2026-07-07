#!/usr/bin/env python3
"""NET-T4 deep analysis — G5 tier trajectories + covariance.
Computes composite order parameter phi and proper critical exponent fits.
Run from ~/shypn/ with .venv activated:
  python3 workspace/projects/thesis/scripts/analyse_net_t4_deep.py
"""
import csv, json, math, pathlib, re

RUN = pathlib.Path(
    "workspace/projects/thesis/experiments/results/run_20260706_190903"
)

def mean(v): return sum(v)/len(v) if v else 0.0
def std(v):
    if len(v)<2: return 0.0
    m=mean(v); return math.sqrt(sum((x-m)**2 for x in v)/(len(v)-1))
def cv2(v): m=mean(v); return (std(v)/m)**2 if m>1e-9 else float("nan")

def read_traj(path):
    with open(path) as fh:
        lines = [l for l in fh if not l.startswith("#")]
    return list(csv.DictReader(lines))

print("NET-T4 DEEP ANALYSIS -- Composite Order Parameter + Critical Exponents")
print("Run:", RUN.name)
print("="*72)

# ── Per-condition analysis ───────────────────────────────────────────────────
results = {}
for cdir in sorted(RUN.glob("condition_*")):
    m = re.search(r"INITIAL_NUTRIENTS_eq_(\d+)", cdir.name)
    n0 = int(m.group(1)) if m else 1440

    rows = list(csv.DictReader(open(cdir/"replicates.csv")))
    traj_files = sorted((cdir/"replicates_trajectories").glob("run_*.csv"))
    n = len(rows)
    spore_mask = [float(r.get("Mature_spore_final",0))>0.5 for r in rows]
    n_s = sum(spore_mask)

    # ── Composite order parameter φ = (Spo0A_P + SigmaH + Septum) normalised ─
    # Compute per-trajectory φ_max (peak value during trajectory)
    phi_max_vals = []
    commit_times = []
    atp_commit_vals = []    # ATP at commitment (Septum first fires)
    sinr_min_vals = []
    sigh_peak_vals = []
    spoa_peak_vals = []

    for i, traj_f in enumerate(traj_files):
        traj = read_traj(traj_f)
        if not traj: continue
        times  = [float(r["time"])/60 for r in traj]
        spoa_p = [float(r.get("Spo0A_P",0)) for r in traj]
        sigh   = [float(r.get("SigmaH",0)) for r in traj]
        sept   = [float(r.get("Septum",0)) for r in traj]
        sinr   = [float(r.get("SinR",8)) for r in traj]
        atp    = [float(r.get("ATP_pool",5000))/1000 for r in traj]

        # Composite phi (raw, un-normalised — will normalise by global max later)
        phi_raw = [spoa_p[k]+sigh[k]+sept[k] for k in range(len(traj))]
        phi_max_vals.append(max(phi_raw))

        sigh_peak_vals.append(max(sigh))
        spoa_peak_vals.append(max(spoa_p))
        sinr_min_vals.append(min(sinr))

        # Commitment time = first Septum > 0
        s_t = [times[k] for k in range(len(sept)) if sept[k]>0.5]
        commit_times.append(s_t[0] if s_t else float("nan"))

        # ATP at commitment
        if s_t:
            idx = next(k for k in range(len(sept)) if sept[k]>0.5)
            atp_commit_vals.append(atp[idx])

    # Covariance — top correlations
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

    valid_ct = [t for t in commit_times if not math.isnan(t)]
    results[n0] = {
        "sf": n_s/n, "n": n, "ns": n_s,
        "phi_max_mean": mean(phi_max_vals),
        "phi_max_std":  std(phi_max_vals),
        "phi_cv2":      cv2(phi_max_vals),
        "sigh_peak":    mean(sigh_peak_vals),
        "spoa_peak":    mean(spoa_peak_vals),
        "sinr_min":     mean(sinr_min_vals),
        "commit_t_mean": mean(valid_ct) if valid_ct else float("nan"),
        "commit_t_std":  std(valid_ct) if valid_ct else float("nan"),
        "atp_commit":   mean(atp_commit_vals) if atp_commit_vals else float("nan"),
        "top_corr":     top_corr[:3],
    }

# ── Summary table ────────────────────────────────────────────────────────────
print()
print("%-6s  %-6s  %-8s  %-8s  %-8s  %-8s  %-6s  %-8s" % (
    "N0", "Spore%", "phi_mean", "phi_CV2", "SigH_pk", "SpoA_pk", "SinRmin", "t_commit"))
print("-"*72)
for n0 in sorted(results):
    r = results[n0]
    print("%-6d  %-5.0f%%  %-8.2f  %-8.3f  %-8.3f  %-8.2f  %-6.3f  %-8s" % (
        n0, 100*r["sf"], r["phi_max_mean"], r["phi_cv2"],
        r["sigh_peak"], r["spoa_peak"], r["sinr_min"],
        "%.1f±%.1f" % (r["commit_t_mean"], r["commit_t_std"])
        if not math.isnan(r["commit_t_mean"]) else "---"))

# ── Refined N_c from phi_CV2 peak ────────────────────────────────────────────
print()
valid_cv2 = {n0: r["phi_cv2"] for n0,r in results.items()
             if not math.isnan(r["phi_cv2"]) and r["phi_cv2"] > 0}
if valid_cv2:
    nc_cv2 = max(valid_cv2, key=valid_cv2.get)
    print("phi_CV2 peak at N0=%d uM (CV2=%.3f) -> N_c candidate from composite order param" % (
        nc_cv2, valid_cv2[nc_cv2]))

# ── N_c from 50%% crossing ────────────────────────────────────────────────────
above = [(n0,r["sf"]) for n0,r in sorted(results.items()) if r["sf"]>=0.50]
below = [(n0,r["sf"]) for n0,r in sorted(results.items()) if r["sf"]<0.50]
if above and below:
    na,pa = above[-1]; nb,pb = below[0]
    nc_interp = na + (pa-0.5)/(pa-pb)*(nb-na)
    print("N_c (50%% crossing, linear interpolation): %.1f uM  [%d@%.0f%% -> %d@%.0f%%]" % (
        nc_interp, na, 100*pa, nb, 100*pb))

# ── Power-law fit on phi_CV2 ─────────────────────────────────────────────────
print()
print("--- POWER-LAW FIT: phi_CV2 ~ |N0 - N_c|^(-gamma) ---")
Nc = nc_interp if above and below else 1340.0

def fit_gamma(pts):
    if len(pts)<3: return float("nan"), float("nan"), len(pts)
    lx=[math.log(d) for d,_ in pts]; ly=[math.log(v) for _,v in pts]
    n=len(lx); mx=mean(lx); my=mean(ly)
    ssxx=sum((x-mx)**2 for x in lx); ssxy=sum((x-mx)*(y-my) for x,y in zip(lx,ly))
    if ssxx<1e-15: return float("nan"),float("nan"),n
    slope=ssxy/ssxx; intercept=my-slope*mx
    yp=[intercept+slope*x for x in lx]
    ss_res=sum((a-b)**2 for a,b in zip(ly,yp)); ss_tot=sum((y-my)**2 for y in ly)
    r2=1-ss_res/ss_tot if ss_tot>1e-15 else float("nan")
    return -slope, r2, n

sub_pts=[(abs(n0-Nc),r["phi_cv2"]) for n0,r in results.items()
          if n0<Nc and not math.isnan(r["phi_cv2"]) and r["phi_cv2"]>0 and r["sf"]<0.98]
sup_pts=[(abs(n0-Nc),r["phi_cv2"]) for n0,r in results.items()
          if n0>Nc and not math.isnan(r["phi_cv2"]) and r["phi_cv2"]>0 and r["sf"]>0.02]

g_sub,r2_sub,n_sub = fit_gamma(sub_pts)
g_sup,r2_sup,n_sup = fit_gamma(sup_pts)
print("Sub-critical:  gamma=%.3f  R2=%.4f  n=%d pts" % (g_sub, r2_sub, n_sub))
print("Super-critical: gamma=%.3f  R2=%.4f  n=%d pts" % (g_sup, r2_sup, n_sup))
print("Mean-field prediction: gamma=1.0 on both sides")

# ── Top covariance at N_c ─────────────────────────────────────────────────────
print()
nc_n0 = min(results.keys(), key=lambda x: abs(x-Nc))
print("Top correlations at N0=%d (closest to N_c):" % nc_n0)
for _,r_ab,na,nb in results[nc_n0]["top_corr"]:
    sign="+" if r_ab>0 else "-"
    print("  %s%.3f  %s x %s" % (sign, abs(r_ab), na, nb))
