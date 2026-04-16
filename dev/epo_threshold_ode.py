#!/usr/bin/env python3
"""
EPO Commitment Threshold — Fast ODE Sweep
==========================================
Approximates the GATA1/PU.1 toggle with a deterministic ODE model
calibrated to the existing stochastic shypn runs.

Uses scipy.integrate.solve_ivp for speed (milliseconds per run).
Sweeps EPO concentration and finds the bifurcation threshold.

Outputs:
  - dev/epo_ode_sweep.csv  — full trajectory data
  - Console: commitment probabilities and threshold estimate
  - ASCII phase-portrait of separatrix
"""
import sys
import os
import csv
import numpy as np
from scipy.integrate import solve_ivp

# ── Model calibration from existing shypn CSV runs ───────────────────────────
#
# Variables tracked (concentrations, mM):
#   G  = GATA1_Protein_nuc
#   P  = PU1_Protein_nuc
#   Ge = GATA1_Protein_cyto  (intermediate — cytoplasmic pool)
#   Pe = PU1_Protein_cyto
#   Gm = GATA1_mRNA_cyto
#   Pm = PU1_mRNA_cyto
#   R  = EPOR_bound           (EPO signal)
#   C  = GCSFR_bound          (GCSF signal)
#   E  = EPO_external
#   F  = GCSF_external
#
# Receptor model (calibrated to EPO=50, GCSF=50 run):
#   EPOR_free  ~ 5000
#   GCSF_free  ~ 5000
#   EPO+EPOR  →  EPOR_bound  (k_on=0.002, k_off=0.01, k_in=0.02)
#   GCSF+GCSFR → GCSFR_bound (same)
#
# Toggle transcription (Sharpless & Bhatt Hill kinetics, calibrated):
#   GATA1 transcription:  k_G * R/(K_G + R) * K_rep/(K_rep + P^n)
#   PU1 transcription:    k_P * C/(K_P + C) * K_rep/(K_rep + G^n)
# ─────────────────────────────────────────────────────────────────────────────

# Receptor kinetics (from binding transitions T23/T24 rates in model)
EPOR_TOTAL   = 5000.0   # mM (initial EPOR_free)
GCSFR_TOTAL  = 5000.0
K_ON_EPO     = 0.002    # /mM/s — forward binding
K_OFF_EPO    = 0.01     # /s   — unbinding
K_INT_EPO    = 0.02     # /s   — internalization (from T_EPOR_internalization)
K_REC_EPOR   = 0.005    # /s   — recycling (T30)
K_ON_GCSF    = 0.002
K_OFF_GCSF   = 0.01
K_INT_GCSF   = 0.02
K_REC_GCSFR  = 0.005

# Clearance (EPO_clearance / GCSF_clearance)
K_CL_EPO     = 0.015    # /s
K_CL_GCSF    = 0.015

# Transcription rates (calibrated so steady-state mRNA ~ 500-600 at EPO=50)
K_G_BASE     = 0.6      # /s — basal GATA1 mRNA production
K_P_BASE     = 0.6      # /s — basal PU1 mRNA production
K_G_SIG      = 1.2      # /s — max signal-driven boost
K_P_SIG      = 1.2
K_SIG_HALF   = 1.0      # mM — half-max for receptor signal (Michaelis)
K_G_SELF     = 0.8      # GATA1 self-activation
K_G_SELF_K   = 30.0     # half-max for self-activation

# Mutual repression (Hill)
K_REP        = 40.0     # half-max repression
N_HILL       = 2.0      # Hill coefficient

# mRNA export/degradation
K_EXP        = 0.003    # /s — nuclear export rate
K_DEG_M      = 0.002    # /s — mRNA degradation
K_TRANS      = 0.004    # /s — translation rate
K_DEG_CYT    = 0.002    # /s — cytoplasmic protein degradation
K_IMP        = 0.002    # /s — nuclear import rate
K_DEG_NUC    = 0.001    # /s — nuclear protein degradation

def toggle_ode(t, y, epo0, gcsf0):
    """GATA1/PU.1 toggle ODE system.

    State vector y:
      0: Gm  — GATA1 mRNA cyto
      1: Pm  — PU1 mRNA cyto
      2: Gc  — GATA1 protein cyto
      3: Pc  — PU1 protein cyto
      4: G   — GATA1 protein nuc
      5: P   — PU1 protein nuc
      6: E   — EPO external
      7: F   — GCSF external
      8: R   — EPOR bound
      9: C   — GCSFR bound
     10: Ri  — EPOR internalized
     11: Ci  — GCSFR internalized
     12: Rf  — EPOR free
     13: Cf  — GCSFR free
    """
    Gm, Pm, Gc, Pc, G, P, E, F, R, C, Ri, Ci, Rf, Cf = y

    # --- Receptor dynamics ---
    dR  = K_ON_EPO * E * Rf - (K_OFF_EPO + K_INT_EPO) * R
    dC  = K_ON_GCSF * F * Cf - (K_OFF_GCSF + K_INT_GCSF) * C
    dRi = K_INT_EPO * R - K_REC_EPOR * Ri
    dCi = K_INT_GCSF * C - K_REC_GCSFR * Ci
    dRf = K_OFF_EPO * R + K_REC_EPOR * Ri - K_ON_EPO * E * Rf
    dCf = K_OFF_GCSF * C + K_REC_GCSFR * Ci - K_ON_GCSF * F * Cf
    dE  = -K_CL_EPO * E - K_ON_EPO * E * Rf + K_OFF_EPO * R
    dF  = -K_CL_GCSF * F - K_ON_GCSF * F * Cf + K_OFF_GCSF * C

    # --- Signals (normalised) ---
    sig_G = (R / (K_SIG_HALF + R))           # EPOR signal → GATA1
    sig_P = (C / (K_SIG_HALF + C))           # GCSFR signal → PU1
    self_G = (G**2) / (K_G_SELF_K**2 + G**2) # GATA1 self-activation

    # --- Mutual repression ---
    rep_of_G = K_REP**N_HILL / (K_REP**N_HILL + P**N_HILL)   # P represses G
    rep_of_P = K_REP**N_HILL / (K_REP**N_HILL + G**N_HILL)   # G represses P

    # --- Transcription → mRNA (cyto) ---
    txn_G = (K_G_BASE + K_G_SIG * sig_G + K_G_SELF * self_G) * rep_of_G
    txn_P = (K_P_BASE + K_P_SIG * sig_P) * rep_of_P

    dGm = txn_G - (K_EXP + K_DEG_M) * Gm
    dPm = txn_P - (K_EXP + K_DEG_M) * Pm

    # --- Translation → cyto protein ---
    dGc = K_TRANS * Gm - (K_IMP + K_DEG_CYT) * Gc
    dPc = K_TRANS * Pm - (K_IMP + K_DEG_CYT) * Pc

    # --- Nuclear import/export ---
    dG  = K_IMP * Gc - K_DEG_NUC * G
    dP  = K_IMP * Pc - K_DEG_NUC * P

    return [dGm, dPm, dGc, dPc, dG, dP, dE, dF, dR, dC, dRi, dCi, dRf, dCf]


def run_ode(epo0, gcsf0=50.0, t_end=3600.0):
    """Run one ODE integration and return final (G, P) and trajectory."""
    # Initial conditions (from model IC)
    y0 = [
        10.0,      # Gm  (GATA1 mRNA cyto)
        10.0,      # Pm  (PU1 mRNA cyto)
        25.0,      # Gc  (GATA1 protein cyto)
        25.0,      # Pc  (PU1 protein cyto)
        25.0,      # G   (GATA1 nuc)
        25.0,      # P   (PU1 nuc)
        epo0,      # E   (EPO external)
        gcsf0,     # F   (GCSF external)
        0.0,       # R   (EPOR bound)
        0.0,       # C   (GCSFR bound)
        0.0,       # Ri  (EPOR internalized)
        0.0,       # Ci  (GCSFR internalized)
        EPOR_TOTAL, # Rf (EPOR free)
        GCSFR_TOTAL, # Cf (GCSFR free)
    ]

    sol = solve_ivp(
        toggle_ode,
        [0, t_end],
        y0,
        args=(epo0, gcsf0),
        method='RK45',
        rtol=1e-4, atol=1e-6,
        dense_output=False,
        max_step=10.0,
    )
    G_final = sol.y[4, -1]
    P_final = sol.y[5, -1]
    return sol, G_final, P_final


# ── EPO sweep ─────────────────────────────────────────────────────────────────
EPO_LEVELS = np.logspace(-2, 2, 50)  # 0.01 → 100 mM, 50 points log-spaced
GCSF_LEVEL = 50.0

print("EPO Commitment Threshold Sweep (ODE approximation)")
print(f"GCSF = {GCSF_LEVEL} mM fixed, t_end = 3600s")
print(f"Sweeping {len(EPO_LEVELS)} EPO concentrations: {EPO_LEVELS[0]:.3f} → {EPO_LEVELS[-1]:.1f} mM\n")

results = []
for epo in EPO_LEVELS:
    sol, G, P = run_ode(epo, GCSF_LEVEL)
    ratio = G / P if P > 0 else float('inf')
    fate = "ERYTHROID" if G > P else "MYELOID"
    results.append({"epo": epo, "G_final": G, "P_final": P, "ratio": ratio, "fate": fate})

# ── Print table of key EPO values ─────────────────────────────────────────────
print(f"{'EPO':>10}  {'GATA1_nuc':>10}  {'PU1_nuc':>10}  {'ratio':>8}  {'fate'}")
print("-" * 55)
for r in results:
    epo = r['epo']
    if epo < 0.1 or any(abs(epo - v) < 0.01 for v in [0.1, 0.5, 1, 2, 5, 10, 25, 50]):
        bar = ("█" * int(min(r['ratio'], 3) / 3 * 20)).ljust(20)
        print(f"{r['epo']:>10.3f}  {r['G_final']:>10.2f}  {r['P_final']:>10.2f}  "
              f"{r['ratio']:>8.3f}  {r['fate']:12s}  {bar}")

# ── Find threshold (50% commitment ≈ ratio=1) ─────────────────────────────────
transitions = []
for i in range(1, len(results)):
    if results[i-1]['fate'] != results[i]['fate']:
        epo_lo = results[i-1]['epo']
        epo_hi = results[i]['epo']
        transitions.append((epo_lo, epo_hi, results[i-1]['fate'], results[i]['fate']))

print()
if transitions:
    for lo, hi, f_lo, f_hi in transitions:
        midpoint = np.exp((np.log(lo) + np.log(hi)) / 2)
        print(f"BIFURCATION: {f_lo} → {f_hi} at EPO ≈ {midpoint:.3f} mM")
        print(f"  (between EPO={lo:.3f} [{f_lo}] and EPO={hi:.3f} [{f_hi}])")
else:
    print("No fate transition found in this EPO range")
    print(f"Final fate at EPO={EPO_LEVELS[-1]:.0f}: {results[-1]['fate']}")

# ── EPO depletion kinetics ─────────────────────────────────────────────────────
print("\n── EPO depletion timescale ──────────────────────────────────────")
for epo0 in [0.1, 1.0, 5.0, 10.0, 50.0]:
    sol, G, P = run_ode(epo0, GCSF_LEVEL, t_end=600.0)
    t_depl = None
    E_traj = sol.y[6]
    t_traj = sol.t
    for i, e in enumerate(E_traj):
        if e < 0.001 * epo0:
            t_depl = t_traj[i]
            break
    EPOR_bound_peak = sol.y[8].max()
    print(f"  EPO={epo0:6.1f}: depleted at t≈{t_depl:.0f}s  "
          f"EPOR_bound_peak={EPOR_bound_peak:.2f}  final G/P={G/P if P>0 else 0:.3f}")

# ── Save CSV ───────────────────────────────────────────────────────────────────
outfile = "dev/epo_ode_sweep.csv"
with open(outfile, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["epo", "G_final", "P_final", "ratio", "fate"])
    w.writeheader()
    for r in results:
        w.writerow({k: round(v, 4) if isinstance(v, float) else v for k, v in r.items()})
print(f"\nSaved: {outfile}")

# ── Phase portrait: trajectory in G-P space for key EPO values ────────────────
print("\n── G vs P nuclear at t=3600s for key EPO levels ──────────────────")
print(f"  {'EPO':>8}  {'GATA1':>8}  {'PU1':>8}  {'winner'}")
print("  " + "-" * 40)
for epo0 in [0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0]:
    _, G, P = run_ode(epo0, GCSF_LEVEL)
    winner = "GATA1 ██" if G > P else "PU1   ░░"
    print(f"  {epo0:>8.2f}  {G:>8.2f}  {P:>8.2f}  {winner}")
