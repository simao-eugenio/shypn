#!/usr/bin/env python3
"""NET-T4 analysis — Critical exponents at the commitment bifurcation.
Run from ~/shypn/ with .venv activated:
  python3 workspace/projects/thesis/scripts/analyse_net_t4.py
"""
import csv, math, pathlib, re

RUN = pathlib.Path(
    "workspace/projects/thesis/experiments/results/run_20260706_190903"
)
Nc = 1370.0  # critical N0 from FUJITA-4

def mean(v): return sum(v)/len(v) if v else float("nan")
def var(v):
    if len(v)<2: return 0.0
    m=mean(v); return sum((x-m)**2 for x in v)/(len(v)-1)

# ── collect per-condition stats ───────────────────────────────────────────────
results = {}
for cdir in sorted(RUN.glob("condition_*")):
    m = re.search(r"INITIAL_NUTRIENTS_eq_(\d+)", cdir.name)
    n0 = int(m.group(1)) if m else 1440
    rows = list(csv.DictReader(open(cdir/"replicates.csv")))
    n    = len(rows)
    spore_bin = [float(r.get("Mature_spore_final",0))>0.5 for r in rows]
    ms_vals   = [float(r.get("Mature_spore_final",0)) for r in rows]
    sf = sum(spore_bin)/n

    # CV² of binary sporulation count (Bernoulli)
    if sf > 0 and sf < 1:
        cv2_bin = (1-sf)/sf   # = Var/Mean² for Bernoulli
    else:
        cv2_bin = float("nan")

    # CV² of continuous Mature_spore_final
    ms_mean = mean(ms_vals)
    ms_var  = var(ms_vals)
    cv2_cont = ms_var/(ms_mean**2) if ms_mean > 1e-9 else float("nan")

    results[n0] = {"sf":sf,"n":n,"cv2_bin":cv2_bin,"cv2_cont":cv2_cont,
                   "ms_mean":ms_mean,"ms_var":ms_var}

# ── print table ───────────────────────────────────────────────────────────────
print("NET-T4 ANALYSIS -- Critical Exponents")
print("Run:", RUN.name, "  Nc=%.0f uM" % Nc)
print("="*70)
print("N0      Spore%   CV2_bin    CV2_cont   dist_to_Nc  side")
print("-"*65)
for n0 in sorted(results):
    r = results[n0]
    dist = abs(n0 - Nc)
    side = "sub" if n0 < Nc else "sup"
    print("%6d  %5.0f%%  %9.3f  %11.3f  %10.0f  %s" % (
        n0, 100*r["sf"], r["cv2_bin"], r["cv2_cont"], dist, side))

# ── power-law fit ─────────────────────────────────────────────────────────────
print()
print("--- POWER-LAW FIT: CV2_bin ~ |N0 - Nc|^(-gamma) ---")
print("Using binary CV2 (Bernoulli), excluding N0 where sf=0 or sf=1")

sub_pts = [(abs(n0-Nc), r["cv2_bin"]) for n0,r in results.items()
           if n0 < Nc and not math.isnan(r["cv2_bin"]) and r["cv2_bin"] > 0]
sup_pts = [(abs(n0-Nc), r["cv2_bin"]) for n0,r in results.items()
           if n0 > Nc and not math.isnan(r["cv2_bin"]) and r["cv2_bin"] > 0]

def power_law_fit(pts):
    """Log-log OLS: log(CV2) = a - gamma*log(dist). Returns (gamma, R2, N)."""
    if len(pts) < 2: return float("nan"), float("nan"), len(pts)
    lx = [math.log(d) for d,_ in pts]
    ly = [math.log(v) for _,v in pts]
    n = len(lx)
    mx = mean(lx); my = mean(ly)
    ssxx = sum((x-mx)**2 for x in lx)
    ssxy = sum((x-mx)*(y-my) for x,y in zip(lx,ly))
    if ssxx < 1e-15: return float("nan"), float("nan"), n
    slope = ssxy/ssxx    # slope = -gamma
    intercept = my - slope*mx
    # R2
    y_pred = [intercept + slope*x for x in lx]
    ss_res = sum((a-b)**2 for a,b in zip(ly,y_pred))
    ss_tot = sum((y-my)**2 for y in ly)
    r2 = 1 - ss_res/ss_tot if ss_tot > 1e-15 else float("nan")
    return -slope, r2, n   # gamma = -slope

gamma_sub, r2_sub, n_sub = power_law_fit(sub_pts)
gamma_sup, r2_sup, n_sup = power_law_fit(sup_pts)

print()
print("Sub-critical (N0 < Nc=%d): gamma_sub = %.3f  R2=%.4f  n=%d pts" % (Nc, gamma_sub, r2_sub, n_sub))
print("  Sub-critical points (|N0-Nc|, CV2):", [(round(d,0), round(v,3)) for d,v in sorted(sub_pts)])
print()
print("Super-critical (N0 > Nc=%d): gamma_sup = %.3f  R2=%.4f  n=%d pts" % (Nc, gamma_sup, r2_sup, n_sup))
print("  Super-critical points:", [(round(d,0), round(v,3)) for d,v in sorted(sup_pts)])
print()
print("Mean-field prediction: gamma = 1.0 on both sides")
if not math.isnan(gamma_sub):
    mf_dev_sub = (gamma_sub - 1.0) / 0.3  # rough sigma based on typical uncertainty
    print("Sub-critical departure from MF: %.1f sigma" % mf_dev_sub)
if not math.isnan(gamma_sup):
    mf_dev_sup = (gamma_sup - 1.0) / 1.5
    print("Super-critical departure from MF: %.1f sigma" % mf_dev_sup)
