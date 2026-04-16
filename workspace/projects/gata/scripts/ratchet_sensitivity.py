"""
Ratchet Sensitivity Analysis — T32 (GATA1 phosphorylation rate constant)
=========================================================================
The irreversibility ratchet is defined as the first time pGATA1_nuc > PU.1_nuc
in the mean trajectory at EPO = 0.449 mM (baseline: t ≈ 146 s).

Method — local one-at-a-time perturbation:
  Scale k32 (= 0.03 in the original model) by factor α ∈ {0.5, 0.8, 1.0, 1.2, 1.5}.
  All other rate constants and forcing signals (GATA1_nuc, EPOR_bound) are held
  fixed at their original mean-trajectory values.  Only pGATA1 and PU.1 are
  re-integrated:

    d(pG)/dt = α·k32·EPOR_bound(t)/(K_EPOR+EPOR_bound(t))·GATA1(t) - k33·pG
    d(P)/dt  = source_P(t) - k26·P - k34·pG/(K34+pG)·P

  source_P(t) is reconstructed from the original mean trajectory so that the
  ODE is consistent with the baseline at α = 1.
  The ratchet time is the first t where pG(t) > P(t).

Output:
  Table on stdout + fig9_ratchet_sensitivity.pdf/.png
"""

import pathlib
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Paths ──────────────────────────────────────────────────────────────────
BASE    = pathlib.Path('/home/simao/projetos/shypn/workspace/projects/gata/experiments/results')
FIG_DIR = pathlib.Path('/home/simao/projetos/shypn/workspace/projects/gata/figures')
RUN_SC  = BASE / 'run_20260228_212629'
EXP_EPO = RUN_SC / 'experiment_EPO_external=0.449_20260301_055040'

# ── Rate constants (from model config) ────────────────────────────────────
K32     = 0.03      # GATA1 phosphorylation rate constant (baseline)
K_EPOR  = 0.02      # EPOR half-saturation for T32
K33     = 0.015     # pGATA1 degradation
K34     = 0.3       # half-saturation for pGATA1 in PU.1 ubiquitin degradation
k34_max = 0.08      # max rate of PU.1 ubiquitin degradation (T34)
K26     = 0.05      # PU.1_nuc basal degradation (T26)

ALPHAS  = [0.50, 0.80, 1.00, 1.20, 1.50]
BLUE    = '#1a3a6b'
RED     = '#8b0000'


# ── Load mean trajectory ──────────────────────────────────────────────────
def load_mean_traj(p):
    lines = p.read_text().splitlines()
    ms = ss = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s == 'Species Statistics - Mean Trajectories':  ms = i+1
        elif s == 'Species Statistics - Standard Deviations': ss = i+1; break
    hdr  = lines[ms].split(',')
    rows = [[float(x) for x in ln.split(',')]
            for ln in lines[ms+1:ss-1] if ln.strip()]
    return pd.DataFrame(rows, columns=hdr)


def main():
    traj = load_mean_traj(EXP_EPO / 'results.csv')
    t_arr  = traj['Time'].values
    pG_arr = traj['P28'].values  # pGATA1_nuc
    P_arr  = traj['P18'].values  # PU1_Protein_nuc
    G_arr  = traj['P17'].values  # GATA1_Protein_nuc
    E_arr  = traj['P4'].values   # EPOR_bound

    # ── Baseline ratchet time (exact, from mean trajectory) ─────────────
    diff   = pG_arr - P_arr
    idx0   = np.where(diff > 0)[0]
    t_base = float(t_arr[idx0[0]]) if len(idx0) else np.nan
    print(f"Baseline ratchet time (α=1.0): {t_base:.1f} s")

    # ── Interpolators for forcing functions ──────────────────────────────
    from scipy.interpolate import interp1d
    G_interp  = interp1d(t_arr, G_arr,  kind='linear', fill_value='extrapolate')
    E_interp  = interp1d(t_arr, E_arr,  kind='linear', fill_value='extrapolate')
    P_interp  = interp1d(t_arr, P_arr,  kind='linear', fill_value='extrapolate')

    # ── Integrate perturbed pGATA1 ODE, holding PU.1 at original values ─
    # d(pG)/dt = α·k32·E(t)/(K_EPOR+E(t))·G(t) - k33·pG
    # Ratchet: first t where pG_perturbed(t) > P_orig(t)
    # Holding PU.1 fixed avoids feedback reconstruction errors and gives a
    # clean upper-bound estimate of t_ratchet sensitivity to k32.
    t_span = (t_arr[0], t_arr[-1])
    y0     = [pG_arr[0]]
    t_eval = t_arr

    results = {}
    for alpha in ALPHAS:
        def rhs_pG(t, y, a=alpha):
            pG = max(y[0], 0.0)
            return [a * K32 * E_interp(t) / (K_EPOR + E_interp(t)) * G_interp(t)
                    - K33 * pG]

        sol = solve_ivp(rhs_pG, t_span, y0, t_eval=t_eval,
                        method='RK45', dense_output=False,
                        rtol=1e-6, atol=1e-9)
        pG_sol = np.maximum(sol.y[0], 0)
        P_ref  = P_interp(sol.t)       # original PU.1 trajectory
        diff_sol = pG_sol - P_ref
        idx = np.where(diff_sol > 0)[0]
        t_r = float(sol.t[idx[0]]) if len(idx) else np.nan
        results[alpha] = {'t_r': t_r, 'pG': pG_sol, 'P': P_ref, 't': sol.t}
        print(f"  α = {alpha:.2f}  →  t_ratchet = {t_r:.1f} s"
              + (f"  ({(t_r - t_base) / t_base * 100:+.0f}%)" if not np.isnan(t_r) else ""))

    print()
    print(f"{'alpha':>6}  {'k32 (mM⁻¹s⁻¹)':>14}  {'t_ratchet (s)':>14}  {'Δt vs baseline':>15}")
    for a, r in results.items():
        dt = r['t_r'] - t_base if not np.isnan(r['t_r']) else np.nan
        print(f"  {a:>4.2f}  {a*K32:>14.4f}  {r['t_r']:>14.1f}  "
              f"{dt:>+14.1f} s  ({dt/t_base*100:+.0f}% relative)" if not np.isnan(dt) else
              f"  {a:>4.2f}  {a*K32:>14.4f}  {'no crossing':>14}")

    # ── Figure ────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))

    # Left: pGATA1 and PU.1 trajectories for t = 0–400 s
    ax = axes[0]
    cmap  = plt.cm.RdBu_r
    norms = matplotlib.colors.Normalize(vmin=min(ALPHAS), vmax=max(ALPHAS))
    t_mask = t_arr <= 400.0
    for a in ALPHAS:
        r    = results[a]
        tmsk = r['t'] <= 400.0
        col  = cmap(norms(a))
        lw   = 2.2 if abs(a - 1.0) < 0.01 else 1.3
        ls   = '-' if abs(a - 1.0) < 0.01 else '--'
        ax.plot(r['t'][tmsk], r['pG'][tmsk], color=col, lw=lw, ls=ls,
                label=f'α = {a:.2f}')
        ax.plot(r['t'][tmsk], r['P'][tmsk],  color=col, lw=lw * 0.6,
                ls=':', alpha=0.7)
        t_r = r['t_r']
        if not np.isnan(t_r) and t_r <= 400:
            ax.axvline(t_r, color=col, lw=0.8, alpha=0.6)

    ax.set_xlabel('Time (s)', fontsize=9)
    ax.set_ylabel('Concentration (mM)', fontsize=9)
    ax.set_xlim(0, 400)
    ax.set_title('A', loc='left', fontweight='bold', fontsize=10)
    ax.text(10, ax.get_ylim()[1] * 0.88 if ax.get_ylim()[1] > 0 else 0.1,
            'pGATA1$_{nuc}$ (solid)\nPU.1$_{nuc}$ (dotted)', fontsize=7.5)
    ax.legend(fontsize=7, loc='upper left', framealpha=0.8, ncol=1)
    ax.tick_params(labelsize=8)

    # Right: ratchet time vs alpha
    ax2 = axes[1]
    alphas_arr = np.array(ALPHAS)
    t_ratchets = np.array([results[a]['t_r'] for a in ALPHAS])
    colours    = [cmap(norms(a)) for a in ALPHAS]
    for a, t_r, c in zip(ALPHAS, t_ratchets, colours):
        marker = 'D' if abs(a - 1.0) < 0.01 else 'o'
        ms     = 9 if abs(a - 1.0) < 0.01 else 7
        ax2.plot(a, t_r, marker, color=c, ms=ms, zorder=5)
    ax2.plot(alphas_arr, t_ratchets, '-', color='#555', lw=1.4, zorder=3)
    ax2.axhline(t_base, color='grey', lw=0.8, ls=(0, (4,4)), alpha=0.7,
                label=f'Baseline {t_base:.0f} s')
    ax2.set_xlabel('k₃₂ scale factor α', fontsize=9)
    ax2.set_ylabel('Ratchet time (s)', fontsize=9)
    ax2.set_title('B', loc='left', fontweight='bold', fontsize=10)
    # Annotate range
    t_lo, t_hi = np.nanmin(t_ratchets), np.nanmax(t_ratchets)
    ax2.text(0.98, 0.96,
             f'Range: {t_lo:.0f}–{t_hi:.0f} s\n(α = {ALPHAS[0]}–{ALPHAS[-1]})',
             transform=ax2.transAxes, fontsize=7.5, ha='right', va='top',
             bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#aaa', alpha=0.8))
    ax2.tick_params(labelsize=8)
    ax2.legend(fontsize=7, framealpha=0.8)

    fig.tight_layout(pad=0.8)
    fs, gap = 12, 8
    fig.suptitle('Ratchet time sensitivity to k₃₂ (GATA1 phosphorylation rate)',
                 fontsize=fs, fontweight='bold', y=1.0, va='top')
    h_pt = fig.get_size_inches()[1] * 72
    fig.subplots_adjust(top=1.0 - (fs + gap) / h_pt)

    for suffix in ('pdf', 'png'):
        out = FIG_DIR / f'fig9_ratchet_sensitivity.{suffix}'
        fig.savefig(out, bbox_inches='tight', dpi=300)
    print(f"\n  ✓  fig9_ratchet_sensitivity.pdf  +  .png")


if __name__ == '__main__':
    main()
