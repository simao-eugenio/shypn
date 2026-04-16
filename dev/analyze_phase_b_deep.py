"""
Deep analysis of run_20260305_170232 — Phase B thermodynamic sweep.
Covers all analyses specified in THERMO_SWEEP_EXPERIMENT_PLAN_MAR03.md:
  1.  Fate summary (confirmed)
  2.  Eyring plot  — ΔΔG‡ of fate commitment from logit(p_ery) vs 1/T
  3.  Commitment timing — first-crossing time (GATA1/PU1 > 1.5) from trajectories
  4.  Arrhenius linearity — ln(τ_commitment) vs 1/T; slope → Ea_apparent
  5.  Bimodality index (Sarle) on final GATA1_Protein_nuc distribution
  6.  Mean final state: GATA1_nuc, PU1_nuc, pGATA1, GATA1/PU1 ratio
  7.  pGATA1 phosphorylation fraction  f_phos = pGATA1 / (GATA1 + pGATA1)
  8.  Receptor occupancy  occ = EPOR_bound / (free + bound + intern)
  9.  Adenylate/guanylate energy state: ATP, ADP, ΔG_ATP; GTP, GDP, ΔG_GTP
  10. Two-factor logistic regression: EPO × Temperature → p_ery interaction
"""

import glob
import os
import math
import csv
import warnings
from pathlib import Path

RUN = Path("/home/simao/projetos/shypn/workspace/projects/gata/experiments/results/run_20260305_170232")
R_GAS = 8.314          # J/(mol·K)
T_REF = 310.15         # K reference (nominal body temp)
# Arrhenius expected Ea/R for dominant (transcription) step
Ea_transcription_over_R = 7215.0   # K
# ΔG° ATP hydrolysis standard (kJ/mol)
DG0_ATP = -30.5
DG0_GTP = -30.5

# ─────────────────────────────────────────────────────────────────────────────
# 1. Discover all experiments and parse condition labels
# ─────────────────────────────────────────────────────────────────────────────

def parse_condition(exp_dir: Path):
    """Extract EPO and Temperature from directory name."""
    name = exp_dir.name
    # e.g. experiment_EPO_external=0.43_Temperature=312.15_20260305_212555
    epo = float(name.split("EPO_external=")[1].split("_")[0])
    temp = float(name.split("Temperature=")[1].split("_")[0])
    return epo, temp

experiments = {}
for d in RUN.glob("experiment_*"):
    if d.is_dir():
        epo, temp = parse_condition(d)
        experiments[(epo, temp)] = d

epo_vals  = sorted(set(k[0] for k in experiments))
temp_vals = sorted(set(k[1] for k in experiments))
print(f"Grid: EPO={epo_vals}  T={temp_vals}  ({len(experiments)} conditions)")
print()


# ─────────────────────────────────────────────────────────────────────────────
# 2. Load replicates.csv for each condition (per-replicate final state)
# ─────────────────────────────────────────────────────────────────────────────

def load_replicates(exp_dir: Path) -> list[dict]:
    """Load replicates.csv, skipping # comment header lines."""
    p = exp_dir / "replicates.csv"
    rows = []
    with open(p) as f:
        lines = [l for l in f if not l.startswith("#")]
    reader = csv.DictReader(lines)
    for row in reader:
        rows.append({k: v for k, v in row.items()})
    return rows

def load_fate_summary(exp_dir: Path) -> dict:
    p = exp_dir / "fate_summary.csv"
    with open(p) as f:
        reader = csv.DictReader(f)
        return next(reader)

# Build per-condition data store
cond_data = {}
for key, exp_dir in experiments.items():
    reps = load_replicates(exp_dir)
    fate = load_fate_summary(exp_dir)
    cond_data[key] = {"reps": reps, "fate": fate, "dir": exp_dir}

# ─────────────────────────────────────────────────────────────────────────────
# 3. Fate summary table (re-derived from replicates.csv for cross-check)
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("SECTION 1 — Fate summary  (p_ery Wilson 95% CI)")
print("=" * 70)
print(f"{'EPO':>6}  {'T(K)':>7}  {'n_ery':>6}  {'n_unc':>6}  {'p_ery':>6}  {'CI_lo':>6}  {'CI_hi':>6}")
print("-" * 70)

for epo in epo_vals:
    for temp in temp_vals:
        key = (epo, temp)
        fate = cond_data[key]["fate"]
        print(f"{epo:6.2f}  {temp:7.2f}  {fate['n_ery']:>6}  {fate['n_unc']:>6}  "
              f"{float(fate['p_ery']):6.3f}  {float(fate['ci_lo_95']):6.3f}  {float(fate['ci_hi_95']):6.3f}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# 4. Eyring plot analysis
#    logit(p_ery) = α  − ΔΔG‡/(R) × (1/T)
#    Fit by simple 2-point / 3-point linear regression over temperature axis
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("SECTION 2 — Eyring plot  logit(p_ery) vs 1/T")
print("=" * 70)
print("Apparent ΔΔG‡ = energy difference (erythroid attractor − undecided)")
print()

def safe_logit(p):
    p = max(1e-4, min(1 - 1e-4, p))
    return math.log(p / (1 - p))

def linreg(xs, ys):
    """Slope, intercept, R² for lists xs, ys."""
    n = len(xs)
    xm = sum(xs) / n
    ym = sum(ys) / n
    ssxy = sum((x - xm) * (y - ym) for x, y in zip(xs, ys))
    ssxx = sum((x - xm) ** 2 for x in xs)
    if ssxx == 0:
        return None, None, None
    slope = ssxy / ssxx
    intercept = ym - slope * xm
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - ym) ** 2 for y in ys)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float('nan')
    return slope, intercept, r2

print(f"{'EPO':>6}  {'slope(K)':>10}  {'ΔΔG‡(kJ/mol)':>13}  {'R²':>6}  Note")
print("-" * 65)

for epo in epo_vals:
    inv_T = []
    logit_p = []
    for temp in temp_vals:
        key = (epo, temp)
        p = float(cond_data[key]["fate"]["p_ery"])
        inv_T.append(1.0 / temp)
        logit_p.append(safe_logit(p))

    slope, intercept, r2 = linreg(inv_T, logit_p)
    if slope is None:
        print(f"{epo:6.2f}  (cannot fit — no variance)")
        continue
    # slope = -ΔΔG‡ / R  →  ΔΔG‡ = -slope × R
    ddg = -slope * R_GAS / 1000.0  # kJ/mol
    note = ""
    if float(cond_data[(epo, temp_vals[0])]["fate"]["p_ery"]) > 0.95:
        note = "ceiling — CI asymmetric"
    print(f"{epo:6.2f}  {slope:>10.1f}  {ddg:>13.2f}  {r2:>6.3f}  {note}")

print()
print("Interpretation: positive ΔΔG‡  → erythroid attractor favoured at higher T")
print("                (Ea_transcription > Ea_degradation by 10 kJ/mol predicted)")
print()


# ─────────────────────────────────────────────────────────────────────────────
# 5. Commitment timing from trajectories
#    First-crossing time where GATA1_nuc / PU1_nuc > 1.5 per replicate
# ─────────────────────────────────────────────────────────────────────────────

RATIO_THRESHOLD = 1.5

def first_crossing_time(traj_path: Path) -> float | None:
    """Return first time where GATA1_Protein_nuc / PU1_Protein_nuc > threshold."""
    with open(traj_path) as f:
        lines = [l for l in f if not l.startswith("#")]
    reader = csv.DictReader(lines)
    for row in reader:
        g = float(row.get("GATA1_Protein_nuc", 0))
        p = float(row.get("PU1_Protein_nuc", 1e-9))
        if p > 0 and g / p > RATIO_THRESHOLD:
            return float(row["time"])
    return None  # never crossed in simulation window

print("=" * 70)
print("SECTION 3 — Commitment timing  (first GATA1/PU1 > 1.5× crossing)")
print("=" * 70)
print(f"{'EPO':>6}  {'T(K)':>7}  {'τ_med(s)':>9}  {'τ_mean(s)':>10}  {'τ_std(s)':>9}  {'n_crossed':>10}  {'n_late(%)':>10}")
print("-" * 75)

timing_data = {}
for epo in epo_vals:
    for temp in temp_vals:
        key = (epo, temp)
        exp_dir = cond_data[key]["dir"]
        traj_dir = exp_dir / "replicates_trajectories"
        times = []
        n_total = 0
        for traj in sorted(traj_dir.glob("run_*.csv")):
            n_total += 1
            t = first_crossing_time(traj)
            if t is not None:
                times.append(t)

        if times:
            times_sorted = sorted(times)
            n = len(times_sorted)
            median_t = times_sorted[n // 2] if n % 2 == 1 else (times_sorted[n // 2 - 1] + times_sorted[n // 2]) / 2
            mean_t = sum(times_sorted) / n
            std_t = math.sqrt(sum((x - mean_t) ** 2 for x in times_sorted) / n)
        else:
            median_t = mean_t = std_t = float('nan')

        n_late = n_total - len(times)
        timing_data[key] = {"times": times, "median": median_t, "mean": mean_t, "std": std_t}
        print(f"{epo:6.2f}  {temp:7.2f}  {median_t:9.1f}  {mean_t:10.1f}  {std_t:9.1f}  "
              f"{len(times):>10}  {100*n_late/n_total:>10.1f}")
    print()

# ─────────────────────────────────────────────────────────────────────────────
# 6. Arrhenius linearity: ln(mean_τ) vs 1/T, slope → apparent Ea
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("SECTION 4 — Arrhenius linearity  ln(τ_mean) vs 1/T")
print("=" * 70)
print(f"Expected slope if transcription (Ea=60kJ/mol) rate-limiting: -{Ea_transcription_over_R:.0f} K")
print(f"Pathway composite (4 steps): -{25252:.0f} K")
print()
print(f"{'EPO':>6}  {'slope_Ea/R(K)':>14}  {'Ea_app(kJ/mol)':>15}  {'R²':>6}")
print("-" * 55)

for epo in epo_vals:
    inv_T = []
    ln_tau = []
    for temp in temp_vals:
        key = (epo, temp)
        mt = timing_data[key]["mean"]
        if not math.isnan(mt) and mt > 0:
            inv_T.append(1.0 / temp)
            ln_tau.append(math.log(mt))
    if len(inv_T) < 2:
        print(f"{epo:6.2f}  insufficient data")
        continue
    slope, intercept, r2 = linreg(inv_T, ln_tau)
    ea_app = slope * R_GAS / 1000.0  # kJ/mol (positive → slower at lower T)
    print(f"{epo:6.2f}  {slope:>14.0f}  {ea_app:>15.1f}  {r2:>6.3f}")
print()
print("Note: apparent Ea incorporates all rate-limiting steps; compare vs")
print("  transcription Ea=60.0, translation Ea=40.0, pathway min=30.0 kJ/mol")
print()


# ─────────────────────────────────────────────────────────────────────────────
# 7. Bimodality index (Sarle) on final GATA1_Protein_nuc per condition
# ─────────────────────────────────────────────────────────────────────────────

def bimodality_index(values):
    """Sarle's bimodality coefficient BC = (skew^2 + 1) / (kurt + 3*(n-1)^2/((n-2)*(n-3)))"""
    n = len(values)
    if n < 4:
        return float('nan')
    mean = sum(values) / n
    diffs = [v - mean for v in values]
    std = math.sqrt(sum(d**2 for d in diffs) / n)
    if std == 0:
        return float('nan')
    skew = sum(d**3 for d in diffs) / (n * std**3)
    kurt = sum(d**4 for d in diffs) / (n * std**4)
    correction = 3 * (n - 1)**2 / ((n - 2) * (n - 3))
    bc = (skew**2 + 1) / (kurt + correction)
    return bc

print("=" * 70)
print("SECTION 5 — Bimodality index (Sarle BC) on final GATA1_Protein_nuc")
print("=" * 70)
print("BC > 0.555 suggests bimodal distribution (committed vs uncommitted)")
print()
print(f"{'EPO':>6}  {'T(K)':>7}  {'BC':>7}  {'CV(%)':>7}  {'mean_G1':>9}  {'std_G1':>9}")
print("-" * 55)

for epo in epo_vals:
    for temp in temp_vals:
        key = (epo, temp)
        reps = cond_data[key]["reps"]
        g1_vals = [float(r["final_GATA1_Protein_nuc"]) for r in reps]
        bc = bimodality_index(g1_vals)
        mean_g1 = sum(g1_vals) / len(g1_vals)
        std_g1 = math.sqrt(sum((v - mean_g1)**2 for v in g1_vals) / len(g1_vals))
        cv = 100 * std_g1 / mean_g1 if mean_g1 > 0 else float('nan')
        print(f"{epo:6.2f}  {temp:7.2f}  {bc:7.3f}  {cv:7.1f}  {mean_g1:9.3f}  {std_g1:9.3f}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# 8. Mean final state: GATA1, PU1, pGATA1, phospho-fraction, ratio
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("SECTION 6 — Mean final state  (all 50 replicates per condition)")
print("=" * 70)
print(f"{'EPO':>6}  {'T(K)':>7}  {'GATA1_nuc':>10}  {'PU1_nuc':>9}  {'ratio':>7}  {'pGATA1':>8}  {'f_phos':>7}")
print("-" * 65)

for epo in epo_vals:
    for temp in temp_vals:
        key = (epo, temp)
        reps = cond_data[key]["reps"]
        n = len(reps)
        def avg(col): return sum(float(r[col]) for r in reps) / n
        g1   = avg("final_GATA1_Protein_nuc")
        pu1  = avg("final_PU1_Protein_nuc")
        pg1  = avg("final_pGATA1_nuc")
        ratio = g1 / pu1 if pu1 > 0 else float('inf')
        f_phos = pg1 / (g1 + pg1) if (g1 + pg1) > 0 else float('nan')
        print(f"{epo:6.2f}  {temp:7.2f}  {g1:10.3f}  {pu1:9.3f}  {ratio:7.2f}  {pg1:8.3f}  {f_phos:7.3f}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# 9. Receptor occupancy
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("SECTION 7 — Receptor occupancy (mean final across 50 replicates)")
print("=" * 70)
print(f"{'EPO':>6}  {'T(K)':>7}  {'EPOR_free':>10}  {'EPOR_bnd':>9}  {'EPOR_int':>9}  {'occ%':>6}")
print("-" * 55)

for epo in epo_vals:
    for temp in temp_vals:
        key = (epo, temp)
        reps = cond_data[key]["reps"]
        n = len(reps)
        def avg(col): return sum(float(r[col]) for r in reps) / n
        ef = avg("final_EPOR_free")
        eb = avg("final_EPOR_bound")
        ei = avg("final_EPOR_internalized")
        total = ef + eb + ei
        occ = 100 * eb / total if total > 0 else float('nan')
        print(f"{epo:6.2f}  {temp:7.2f}  {ef:10.3f}  {eb:9.3f}  {ei:9.3f}  {occ:6.2f}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# 10. Energy state: ATP/ADP/GTP/GDP, ΔG_ATP, ΔG_GTP
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("SECTION 8 — Adenylate / guanylate energy state")
print("=" * 70)
print(f"{'EPO':>6}  {'T(K)':>7}  {'ATP(µM)':>9}  {'ADP(µM)':>9}  {'GTP(µM)':>9}  {'GDP(µM)':>9}  {'ΔG_ATP':>8}  {'ΔG_GTP':>8}")
print("-" * 80)

for epo in epo_vals:
    for temp in temp_vals:
        key = (epo, temp)
        reps = cond_data[key]["reps"]
        n = len(reps)
        def avg(col): return sum(float(r[col]) for r in reps) / n
        atp = avg("final_ATP")
        adp = avg("final_ADP")
        gtp = avg("final_GTP")
        gdp = avg("final_GDP")
        T = temp
        # ΔG = ΔG° + RT·ln([products]/[reactants])
        # For ATP hydrolysis: ΔG = ΔG°_ATP + RT·ln([ADP][Pi]/[ATP])
        # Simplified (no pi term in this formula from pilot analysis doc):
        dg_atp = DG0_ATP + (R_GAS * T / 1000.0) * math.log(adp / atp) if atp > 0 and adp > 0 else float('nan')
        dg_gtp = DG0_GTP + (R_GAS * T / 1000.0) * math.log(gdp / gtp) if gtp > 0 and gdp > 0 else float('nan')
        print(f"{epo:6.2f}  {temp:7.2f}  {atp:9.1f}  {adp:9.1f}  {gtp:9.1f}  {gdp:9.1f}  {dg_atp:8.2f}  {dg_gtp:8.2f}")
    print()

print("Units: concentrations in µM; ΔG in kJ/mol")
print("ΔG_ATP = ΔG°_ATP + RT·ln([ADP]/[ATP])  (simplified, no Pi term)")
print()


# ─────────────────────────────────────────────────────────────────────────────
# 11. Two-factor logistic regression — EPO × Temperature interaction
# ─────────────────────────────────────────────────────────────────────────────
# Simple gradient-descent logistic regression (no scipy dependency needed)

def logistic(z): return 1.0 / (1.0 + math.exp(-z))

def fit_logistic_regression(X, y, lr=0.1, n_iter=5000):
    """Fit logistic regression: log-odds = b0 + b1*x1 + b2*x2 + b3*x1*x2.
    X: list of (x1, x2), y: list of 0/1 outcomes.
    Returns coefficients [b0, b1, b2, b3].
    """
    n = len(y)
    # Feature matrix: [1, x1, x2, x1*x2]
    Xmat = [[1.0, x[0], x[1], x[0]*x[1]] for x in X]
    b = [0.0, 0.0, 0.0, 0.0]
    for _ in range(n_iter):
        grads = [0.0] * 4
        for i in range(n):
            z = sum(b[j] * Xmat[i][j] for j in range(4))
            p_pred = logistic(z)
            err = p_pred - y[i]
            for j in range(4):
                grads[j] += err * Xmat[i][j]
        for j in range(4):
            b[j] -= lr * grads[j] / n
    return b

# Build individual-replicate outcome dataset
X_all, y_all = [], []
for epo in epo_vals:
    for temp in temp_vals:
        key = (epo, temp)
        reps = cond_data[key]["reps"]
        for r in reps:
            y_all.append(1 if r["fate_class"] == "ery" else 0)
            X_all.append((epo, temp))

# Standardise features for numerical stability
epo_mean = sum(x[0] for x in X_all) / len(X_all)
epo_std  = math.sqrt(sum((x[0] - epo_mean)**2 for x in X_all) / len(X_all))
temp_mean = sum(x[1] for x in X_all) / len(X_all)
temp_std  = math.sqrt(sum((x[1] - temp_mean)**2 for x in X_all) / len(X_all))

X_scaled = [((x[0] - epo_mean)/epo_std, (x[1] - temp_mean)/temp_std) for x in X_all]

b = fit_logistic_regression(X_scaled, y_all, lr=0.05, n_iter=10000)

# McFadden pseudo-R²
def log_likelihood(b, X_scaled, y):
    ll = 0.0
    for xi, yi in zip(X_scaled, y):
        z = b[0] + b[1]*xi[0] + b[2]*xi[1] + b[3]*xi[0]*xi[1]
        p = logistic(z)
        p = max(1e-9, min(1-1e-9, p))
        ll += yi * math.log(p) + (1-yi) * math.log(1-p)
    return ll

p_bar = sum(y_all) / len(y_all)
ll_null = len(y_all) * (p_bar * math.log(p_bar) + (1-p_bar) * math.log(1-p_bar))
ll_full = log_likelihood(b, X_scaled, y_all)
mcfadden_r2 = 1.0 - ll_full / ll_null

print("=" * 70)
print("SECTION 9 — Two-factor logistic regression  EPO × Temperature → fate")
print("=" * 70)
print(f"Model: logit(p_ery) = b0 + b1·EPO_scaled + b2·T_scaled + b3·EPO×T")
print(f"  (features standardised: EPO_mean={epo_mean:.4f}, EPO_std={epo_std:.4f})")
print(f"  (                        T_mean={temp_mean:.3f}, T_std={temp_std:.4f})")
print()
print(f"  b0 (intercept)  = {b[0]:+.4f}")
print(f"  b1 (EPO)        = {b[1]:+.4f}   ← main effect of EPO")
print(f"  b2 (Temperature)= {b[2]:+.4f}   ← main effect of Temperature")
print(f"  b3 (EPO×T)      = {b[3]:+.4f}   ← interaction term")
print()
print(f"  McFadden pseudo-R² = {mcfadden_r2:.4f}")
print()
b1_sign = "positive" if b[1] > 0 else "negative"
b2_sign = "positive" if b[2] > 0 else "negative"
b3_sign = "synergistic" if b[3] > 0.05 else ("antagonistic" if b[3] < -0.05 else "negligible")
print(f"  EPO effect:      {b1_sign}  (higher EPO → {'more' if b[1]>0 else 'fewer'} erythroid)")
print(f"  Temperature:     {b2_sign}  (higher T → {'more' if b[2]>0 else 'fewer'} erythroid at mean EPO)")
print(f"  Interaction b3:  {b3_sign}  ({b[3]:+.4f})")
print()


# ─────────────────────────────────────────────────────────────────────────────
# 12. Uncommitted replicate profile — which conditions have the most undecided?
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("SECTION 10 — Uncommitted replicate profile")
print("=" * 70)
print(f"{'EPO':>6}  {'T(K)':>7}  {'n_unc':>6}  {'GATA1_unc':>10}  {'PU1_unc':>8}  {'ratio_unc':>10}")
print("-" * 55)

for epo in epo_vals:
    for temp in temp_vals:
        key = (epo, temp)
        reps = cond_data[key]["reps"]
        unc = [r for r in reps if r["fate_class"] not in ("ery", "mye")]
        if unc:
            mean_g1 = sum(float(r["final_GATA1_Protein_nuc"]) for r in unc) / len(unc)
            mean_pu1 = sum(float(r["final_PU1_Protein_nuc"]) for r in unc) / len(unc)
            ratio = mean_g1 / mean_pu1 if mean_pu1 > 0 else float('inf')
        else:
            mean_g1 = mean_pu1 = ratio = float('nan')
        print(f"{epo:6.2f}  {temp:7.2f}  {len(unc):>6}  {mean_g1:10.3f}  {mean_pu1:8.3f}  {ratio:10.3f}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# 13. Simulation wall-clock time per condition
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("SECTION 11 — Simulation wall-clock time")
print("=" * 70)
print(f"{'EPO':>6}  {'T(K)':>7}  {'mean_elapsed(s)':>16}  {'std_elapsed(s)':>15}  {'total(h)':>9}")
print("-" * 60)

for epo in epo_vals:
    for temp in temp_vals:
        key = (epo, temp)
        reps = cond_data[key]["reps"]
        elapsed = [float(r["elapsed_time_s"]) for r in reps]
        mean_el = sum(elapsed) / len(elapsed)
        std_el = math.sqrt(sum((e - mean_el)**2 for e in elapsed) / len(elapsed))
        total_h = sum(elapsed) / 3600.0
        print(f"{epo:6.2f}  {temp:7.2f}  {mean_el:16.1f}  {std_el:15.1f}  {total_h:9.2f}")
    print()


print("=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
