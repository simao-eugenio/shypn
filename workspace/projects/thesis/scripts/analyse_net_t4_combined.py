#!/usr/bin/env python3
"""NET-T4 combined analysis: original wide sweep + dense sub-critical supplement.
Pools data from both runs to compute gamma_sub and gamma_sup with full N0 coverage.
Run from ~/shypn/ with .venv activated:
  python3 workspace/projects/thesis/scripts/analyse_net_t4_combined.py
"""
import csv, math, pathlib, re

RUN_WIDE  = pathlib.Path("workspace/projects/thesis/experiments/results/run_20260706_190903")
RUN_DENSE = pathlib.Path("workspace/projects/thesis/experiments/results/run_20260707_134537")

def mean(v): return sum(v)/len(v) if v else 0.0
def std(v):
    if len(v)<2: return 0.0
    m=mean(v); return math.sqrt(sum((x-m)**2 for x in v)/(len(v)-1))

def load_cond(cdir):
    rows = list(csv.DictReader(open(cdir/"replicates.csv")))
    n = len(rows)
    spore = [float(r.get("Mature_spore_final",0))>0.5 for r in rows]
    sf = sum(spore)/n
    # Bernoulli CV² = (1-p)/p — proper for binary commitment outcome
    cv2_bin = (1-sf)/sf if 0 < sf < 1 else float("nan")
    return {"sf":sf, "n":n, "ns":sum(spore), "cv2":cv2_bin}

# ── Load all conditions ───────────────────────────────────────────────────────
all_data = {}
for run in [RUN_WIDE, RUN_DENSE]:
    for cdir in sorted(run.glob("condition_*")):
        m = re.search(r"INITIAL_NUTRIENTS_eq_(\d+)", cdir.name)
        if not m: continue
        n0 = int(m.group(1))
        if n0 not in all_data:   # dense run takes precedence for overlapping N0
            all_data[n0] = load_cond(cdir)

# ── N_c from 50% crossing ─────────────────────────────────────────────────────
above = [(n0,d["sf"]) for n0,d in sorted(all_data.items()) if d["sf"]>=0.50]
below = [(n0,d["sf"]) for n0,d in sorted(all_data.items()) if d["sf"]<0.50 and d["sf"]>0]
na,pa = above[-1]; nb,pb = below[0]
Nc = na + (pa-0.5)/(pa-pb)*(nb-na)

print("NET-T4 COMBINED ANALYSIS (wide + dense sub-critical)")
print("N_c = %.1f uM  (linear interpolation: %d@%.1f%% -> %d@%.1f%%)" % (
    Nc, na, 100*pa, nb, 100*pb))
print()

# ── Full sporulation table ────────────────────────────────────────────────────
print("N0      Spore%   CV2_bin   dist_Nc    side    source")
print("-"*60)
for n0 in sorted(all_data):
    d = all_data[n0]
    dist = abs(n0-Nc)
    side = "sub" if n0 < Nc else "sup"
    src  = "dense" if any(n0==int(re.search(r"_eq_(\d+)",c.name).group(1))
                          for c in RUN_DENSE.glob("condition_[p*")
                          if re.search(r"_eq_(\d+)",c.name)) else "wide"
    cv2s = "%.3f" % d["cv2"] if not math.isnan(d["cv2"]) else "---"
    bar  = chr(9608)*int(d["sf"]*20)
    print("%6d  %5.0f%%   %-8s  %7.0f    %-4s    %s" % (
        n0, 100*d["sf"], cv2s, dist, side, src))

# ── Power-law fit ─────────────────────────────────────────────────────────────
def fit_gamma(pts):
    if len(pts)<3: return float("nan"),float("nan"),float("nan"),len(pts)
    lx=[math.log(d) for d,_ in pts]; ly=[math.log(v) for _,v in pts]
    n=len(lx); mx=mean(lx); my=mean(ly)
    ssxx=sum((x-mx)**2 for x in lx); ssxy=sum((x-mx)*(y-my) for x,y in zip(lx,ly))
    if ssxx<1e-15: return float("nan"),float("nan"),float("nan"),n
    slope=ssxy/ssxx; inter=my-slope*mx
    yp=[inter+slope*x for x in lx]
    ss_res=sum((a-b)**2 for a,b in zip(ly,yp)); ss_tot=sum((y-my)**2 for y in ly)
    r2=1-ss_res/ss_tot if ss_tot>1e-15 else float("nan")
    # Standard error of slope
    s2=(ss_res/(n-2)) if n>2 else 0.0
    se_slope=math.sqrt(s2/ssxx) if ssxx>0 else float("nan")
    return -slope, se_slope, r2, n

sub_pts=[(abs(n0-Nc), d["cv2"]) for n0,d in all_data.items()
          if n0<Nc and not math.isnan(d["cv2"]) and d["sf"]<0.98 and d["sf"]>0.05]
sup_pts=[(abs(n0-Nc), d["cv2"]) for n0,d in all_data.items()
          if n0>Nc and not math.isnan(d["cv2"]) and d["sf"]>0.02 and d["sf"]<0.95]

g_sub,se_sub,r2_sub,n_sub = fit_gamma(sorted(sub_pts))
g_sup,se_sup,r2_sup,n_sup = fit_gamma(sorted(sup_pts))

print()
print("="*60)
print("POWER-LAW FIT: CV2_bin ~ |N0 - N_c|^(-gamma)")
print("N_c = %.1f uM" % Nc)
print()
print("Sub-critical  (N0 < N_c): gamma = %.3f +/- %.3f  R2=%.4f  n=%d pts" % (
    g_sub, se_sub, r2_sub, n_sub))
print("  Data:", sorted([(round(d,1), round(v,3)) for d,v in sub_pts]))
print()
print("Super-critical (N0 > N_c): gamma = %.3f +/- %.3f  R2=%.4f  n=%d pts" % (
    g_sup, se_sup, r2_sup, n_sup))
print("  Data:", sorted([(round(d,1), round(v,3)) for d,v in sup_pts]))
print()
print("Mean-field (Landau) prediction: gamma = 1.0 on both sides")
if not math.isnan(g_sub) and not math.isnan(se_sub):
    sigma_mf = abs(g_sub-1.0)/se_sub
    print("Sub-critical departure from MF: %.1f sigma" % sigma_mf)
if not math.isnan(g_sup) and not math.isnan(se_sup):
    sigma_mf = abs(g_sup-1.0)/se_sup
    print("Super-critical departure from MF: %.1f sigma" % sigma_mf)
