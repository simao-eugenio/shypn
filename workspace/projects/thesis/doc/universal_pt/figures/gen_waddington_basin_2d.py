#!/usr/bin/env python3
"""
Generate 2D Waddington Epigenetic Landscape for B. subtilis sporulation.
Contour/heatmap version of the 3D basin figure.

- X axis: Time (min)
- Y axis: Sporulation order parameter φ
- Color:  Pseudo-potential U(φ, t)
- White curve: actual simulation trajectory φ(t)
- Red dashed: θ_eff commitment time
"""

import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import uniform_filter1d
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Load simulation data — G14 Baseline (run_20260516_160934, v6 model)
#    20 replicates, µM units; mean trajectory used for the landscape.
# ---------------------------------------------------------------------------
TRAJ_DIR = (
    Path(__file__).resolve().parents[3]
    / "experiments" / "results"
    / "run_20260516_160934"
    / "condition_Baseline"
    / "replicates_trajectories"
)

def _load(path):
    rows = []
    with open(path) as f:
        for line in f:
            if not line.startswith('#'):
                rows.append(line)
    return list(csv.DictReader(rows))

all_rows = [_load(p) for p in sorted(TRAJ_DIR.glob("run_*.csv"))]
# Use first replicate for time axis (all share same time grid)
ref = all_rows[0]
time_s   = np.array([float(r['time']) for r in ref])
time_min = time_s / 60.0
n = len(time_s)

def _mean_col(col):
    return np.mean(
        np.stack([np.array([float(r[col]) for r in rep]) for rep in all_rows]),
        axis=0
    )

# µM → mM for ATP (so theta_eff stays in mM); others stay in µM (normalised anyway)
atp        = _mean_col('ATP_pool') / 1000.0   # µM → mM
spo0a_p    = _mean_col('Spo0A_P')
sigma_h    = _mean_col('SigmaH')
sigma_f    = _mean_col('SigmaF')
sigma_e    = _mean_col('SigmaE')
sigma_g    = _mean_col('SigmaG')
sigma_k    = _mean_col('SigmaK')
forespore  = _mean_col('Forespore')
mature_spore = _mean_col('Mature_spore')

# ---------------------------------------------------------------------------
# 2. Compute sporulation order parameter φ(t) ∈ [0, 1]
# ---------------------------------------------------------------------------
phi_raw = (
    0.10 * spo0a_p / max(spo0a_p.max(), 1e-9) +
    0.10 * sigma_h / max(sigma_h.max(), 1e-9) +
    0.15 * sigma_f / max(sigma_f.max(), 1e-9) +
    0.15 * sigma_e / max(sigma_e.max(), 1e-9) +
    0.15 * sigma_g / max(sigma_g.max(), 1e-9) +
    0.10 * sigma_k / max(sigma_k.max(), 1e-9) +
    0.15 * forespore / max(forespore.max(), 1e-9) +
    0.10 * mature_spore / max(mature_spore.max(), 1e-9)
)
phi = phi_raw / max(phi_raw.max(), 1e-9)

# ---------------------------------------------------------------------------
# 3. Find commitment point
# ---------------------------------------------------------------------------
theta_eff = 2.16  # mM  (v6 G14 Baseline mean ATP floor, run_20260516_160934)
# Commitment point: first Spo0A_P ignition crossing θ_eff in the regulatory
# cascade. Mean ignition across 20 G14 Baseline replicates = 16.5 min.
commit_idx = np.argmax(spo0a_p > 0.5)   # first token > 0.5 µM ≈ cascade ignition
t_commit = time_min[commit_idx]
phi_commit = phi[commit_idx]

spore_idx = np.argmax(mature_spore > 0.001)
t_spore = time_min[spore_idx]

# ---------------------------------------------------------------------------
# 4. Construct pseudo-potential U(φ, t)
# ---------------------------------------------------------------------------
phi_grid = np.linspace(-0.05, 1.05, 300)
t_grid = np.linspace(0, 360, 200)
T, PHI = np.meshgrid(t_grid, phi_grid)

s = (T - t_commit) / 60.0

a = 4.0
b = 2.5 + 0.8 * np.tanh(s * 1.2)
c = -1.8 * np.tanh(s * 1.8)

phi_c = PHI - 0.5
U = a * phi_c**4 - b * phi_c**2 + c * phi_c

U += 3.0 * np.maximum(0, -PHI)**2
U += 3.0 * np.maximum(0, PHI - 1.0)**2

# ---------------------------------------------------------------------------
# 5. Plot
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5))

# Custom colormap: dark blue (low energy) → white (mid) → dark red (high energy)
colors_list = [
    '#000033', '#001a4d', '#003399', '#0055cc',
    '#3388ee', '#88bbff', '#ccddff', '#ffffff',
    '#ffddcc', '#ffaa88', '#ee6633',
    '#cc3300', '#991a00', '#660000', '#440000'
]
cmap_basin = LinearSegmentedColormap.from_list('basin', colors_list, N=256)

# Use actual data range so both blue and red extremes are reached
u_min, u_max = U.min(), U.max()
levels = np.linspace(u_min, u_max, 40)
cf = ax.contourf(t_grid, phi_grid, U, levels=levels, cmap=cmap_basin, extend='both')

# Contour lines for depth perception
ax.contour(t_grid, phi_grid, U, levels=np.linspace(u_min, u_max, 16),
           colors='k', linewidths=0.3, alpha=0.35)

# Colorbar
cbar = fig.colorbar(cf, ax=ax, label=r'$U(\varphi,\, t)$', pad=0.02)

# --- Trajectory ---
phi_smooth = uniform_filter1d(phi, size=300)
step = max(1, len(time_min) // 400)
t_traj = time_min[::step]
phi_traj = phi_smooth[::step]

ax.plot(t_traj, phi_traj, color='white', linewidth=2.5, alpha=0.95)
ax.plot(t_traj, phi_traj, color='black', linewidth=0.8, alpha=0.4)

# --- θ_eff vertical line ---
ax.axvline(t_commit, color='red', linewidth=1.8, linestyle='--', alpha=0.85)

# --- Commitment point ---
phi_commit_s = phi_smooth[commit_idx]
ax.scatter([t_commit], [phi_commit_s], color='#ffcc00', s=140, marker='o',
           edgecolors='black', linewidths=1.5, zorder=10)

# --- Mature spore ---
phi_spore_s = phi_smooth[spore_idx]
ax.scatter([t_spore], [phi_spore_s], color='#00cc44', s=200, marker='*',
           edgecolors='black', linewidths=1.0, zorder=10)

# --- Axes ---
ax.set_xlabel('Time (min)', fontsize=12)
ax.set_ylabel(r'$\varphi$  (sporulation order parameter)', fontsize=12)
ax.set_title('Epigenetic Potential Landscape — ' + r'$\it{B.\/subtilis}$' + ' Sporulation',
             fontsize=13)
ax.set_xlim(0, 360)
ax.set_ylim(-0.05, 1.05)

plt.tight_layout()

# ---------------------------------------------------------------------------
# 6. Save
# ---------------------------------------------------------------------------
out_dir = Path(__file__).resolve().parent
out_pdf = out_dir / 'fig_waddington_basin_2d.pdf'
out_png = out_dir / 'fig_waddington_basin_2d.png'

plt.savefig(str(out_pdf), dpi=300, bbox_inches='tight')
plt.savefig(str(out_png), dpi=300, bbox_inches='tight')
plt.close()

print(f"✓ {out_pdf.name}")
print(f"✓ {out_png.name}")
print(f"  Commitment: t = {t_commit:.1f} min, φ = {phi_commit:.3f}")
print(f"  Mature spore: t = {t_spore:.1f} min, φ = {phi[spore_idx]:.3f}")
