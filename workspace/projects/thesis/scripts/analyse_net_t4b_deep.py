#!/usr/bin/env python3
"""NET-T4b deep analysis — dense sub-critical G5 tier.
Focused on commitment dynamics right around N_c = 1346 uM.
Run from ~/shypn/ with .venv activated:
  python3 workspace/projects/thesis/scripts/analyse_net_t4b_deep.py
"""
import csv, json, math, pathlib, re

RUN  = pathlib.Path("workspace/projects/thesis/experiments/results/run_20260707_134537")
Nc   = 1346.4  # from combined analysis

def mean(v): return sum(v)/len(v) if v else 0.0
def std(v):
    if len(v)<2: return 0.0
    m=mean(v); return math.sqrt(sum((x-m)**2 for x in v)/(len(v)-1))

def read_traj(path):
    with open(path) as fh:
        lines = [l for l in fh if not l.startswith("#")]
    return list(csv.DictReader(lines))

def first_above(times, vals, thr):
    for t,v in zip(times,vals):
        if v > thr: return t
    return float("nan")

def first_below(times, vals, thr):
    for t,v in zip(times,vals):
        if v < thr: return t
    return float("nan")

print("NET-T4b DEEP ANALYSIS — Dense Sub-Critical G5 Tier")
print("Run:", RUN.name, "  Nc=%.1f uM" % Nc)
print("="*70)

results = {}
for cdir in sorted(RUN.glob("condition_*")):
    m = re.search(r"INITIAL_NUTRIENTS_eq_(\d+)", cdir.name)
    n0 = int(m.group(1)) if m else 1440
    rows = list(csv.DictReader(open(cdir/"replicates.csv")))
    traj_files = sorted((cdir/"replicates_trajectories").glob("run_*.csv"))
    n = len(rows)
    spore_mask = [float(r.get("Mature_spore_final",0))>0.5 for r in rows]
    n_s = sum(spore_mask)
    sf  = n_s/n

    # Per-trajectory detailed timing
    sinr_cross_t   = []   # SinR first < 7.5
    sigh_thresh_t  = []   # SigmaH first > 1.60
    sept_t         = []   # Septum first > 0.5
    atp_dip_t      = []   # ATP minimum time
    atp_dip_v      = []   # ATP minimum value
    sigh_peak      = []   # peak SigmaH
    spoa_peak      = []   # peak Spo0A_P
    commit_mode    = []   # 'A' (passive SinR) or 'B' (SinI/SinR) or 'none'

    for i, traj_f in enumerate(traj_files):
        traj = read_traj(traj_f)
        if not traj: continue
        times = [float(r["time"])/60 for r in traj]
        atp   = [float(r.get("ATP_pool",5000)) for r in traj]
        sigh  = [float(r.get("SigmaH",0)) for r in traj]
        sinr  = [float(r.get("SinR",8)) for r in traj]
        sept  = [float(r.get("Septum",0)) for r in traj]
        spoa  = [float(r.get("Spo0A_P",0)) for r in traj]
        sini  = [float(r.get("SinI",0)) for r in traj]

        sigh_peak.append(max(sigh))
        spoa_peak.append(max(spoa))

        t_sinr = first_below(times, sinr, 7.5)
        t_sigh = first_above(times, sigh, 1.60)
        t_sept = first_above(times, sept, 0.5)
        sinr_cross_t.append(t_sinr)
        sigh_thresh_t.append(t_sigh)
        sept_t.append(t_sept)

        # ATP dip
        min_atp = min(atp); idx = atp.index(min_atp)
        atp_dip_t.append(times[idx]); atp_dip_v.append(min_atp/1000)

        # Classify commitment mode
        if spore_mask[i]:
            max_sini = max(sini)
            if not math.isnan(t_sinr) and t_sinr > 200:
                commit_mode.append('B')   # Late SinR drop = SinI-mediated
            elif not math.isnan(t_sinr) and t_sinr < 10:
                commit_mode.append('A')   # Very early SinR drop = passive
            else:
                commit_mode.append('?')
        else:
            commit_mode.append('veg')

    # Covariance top
    cov_data = json.loads(open(cdir/"covariance.json").read())
    top_corr = []
    if "place_names" in cov_data and "covariance" in cov_data:
        names = cov_data["place_names"]
        mat   = cov_data["covariance"]
        for a in range(len(names)):
            for b in range(a+1,len(names)):
                va=mat[a][a]; vb=mat[b][b]
                if va>1e-15 and vb>1e-15:
                    r_ab=mat[a][b]/math.sqrt(va*vb)
                    top_corr.append((abs(r_ab),r_ab,names[a],names[b]))
        top_corr.sort(reverse=True)

    valid_sept = [t for t in sept_t if not math.isnan(t)]
    valid_sinr = [t for t in sinr_cross_t if not math.isnan(t) and t > 10]
    valid_sigh = [t for t in sigh_thresh_t if not math.isnan(t)]
    mode_A = commit_mode.count('A'); mode_B = commit_mode.count('B')

    results[n0] = {
        "sf":sf,"n":n,"ns":n_s,
        "t_sept_mean": mean(valid_sept), "t_sept_std": std(valid_sept),
        "t_sinr_mean": mean(valid_sinr), "t_sinr_std": std(valid_sinr),
        "t_sigh_mean": mean(valid_sigh), "t_sigh_std": std(valid_sigh),
        "atp_dip_t": mean(atp_dip_t), "atp_dip_v": mean(atp_dip_v),
        "sigh_peak": mean(sigh_peak), "spoa_peak": mean(spoa_peak),
        "mode_A": mode_A, "mode_B": mode_B,
        "top_corr": top_corr[:4],
    }

# ── Summary table ─────────────────────────────────────────────────────────────
print()
print("%-6s %-6s %-10s %-10s %-10s %-12s %-5s %-5s" % (
    "N0","Spore%","t_sept","t_SinR","t_SigH","ATP_dip_t","ModeA","ModeB"))
print("-"*70)
for n0 in sorted(results):
    r = results[n0]
    ts = "%.0f±%.0f" % (r["t_sept_mean"],r["t_sept_std"]) if not math.isnan(r["t_sept_mean"]) else "---"
    tsr = "%.0f±%.0f" % (r["t_sinr_mean"],r["t_sinr_std"]) if valid_sinr else "early"
    tsg = "%.0f±%.0f" % (r["t_sigh_mean"],r["t_sigh_std"]) if not math.isnan(r["t_sigh_mean"]) else "never"
    print("%-6d %-5.0f%%  %-10s %-10s %-10s %-12.0f  %-5d %-5d" % (
        n0, 100*r["sf"], ts, tsr, tsg, r["atp_dip_t"], r["mode_A"], r["mode_B"]))

# ── Near-N_c commitment distribution ─────────────────────────────────────────
print()
print("--- COMMITMENT TIMING NEAR N_c ---")
for n0 in sorted(results):
    r = results[n0]
    dist = n0-Nc
    if not math.isnan(r["t_sept_mean"]):
        print("  N0=%5d (%+6.1f uM):  t_commit=%.1f±%.1f min  SigH_peak=%.3f uM  SpoA_peak=%.2f uM" % (
            n0, dist, r["t_sept_mean"], r["t_sept_std"], r["sigh_peak"], r["spoa_peak"]))

# ── Covariances near N_c ──────────────────────────────────────────────────────
print()
print("--- COVARIANCE AT N_c (N0=1345, dist=1 uM) ---")
nc_cond = min(results.keys(), key=lambda x: abs(x-Nc))
for _, r_ab, na, nb in results[nc_cond]["top_corr"]:
    print("  %+.3f  %s x %s" % (r_ab, na, nb))

print()
print("--- MODE ANALYSIS (sporulating replicates only) ---")
for n0 in sorted(results):
    r = results[n0]
    if r["ns"] > 0:
        total_mode = r["mode_A"] + r["mode_B"]
        pct_A = 100*r["mode_A"]/max(1,total_mode)
        pct_B = 100*r["mode_B"]/max(1,total_mode)
        print("  N0=%5d: %3d sporulated  ModeA=%d(%d%%)  ModeB=%d(%d%%)" % (
            n0, r["ns"], r["mode_A"], pct_A, r["mode_B"], pct_B))

print()
print("--- SIGMA_H THRESHOLD STATISTICS ---")
for n0 in sorted(results):
    r = results[n0]
    dist = n0-Nc
    print("  N0=%5d (%+6.1f uM):  SigH_peak_mean=%.4f uM  SpoA_peak_mean=%.3f uM" % (
        n0, dist, r["sigh_peak"], r["spoa_peak"]))
