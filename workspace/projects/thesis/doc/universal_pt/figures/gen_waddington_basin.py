#!/usr/bin/env python3
"""
Generate Waddington Epigenetic Landscape for B. subtilis sporulation.
Uses actual simulation data from simulation_data.csv.

The landscape shows:
- X axis: Sporulation order parameter φ (0=vegetative, 1=committed sporulation)
- Y axis: Time (min) — the developmental "slope" of the Waddington landscape
- Z axis: Pseudo-potential U(φ, t) — constructed from simulation dynamics

The actual simulation trajectory is projected onto the landscape as a ball
rolling from vegetative basin into sporulation basin at the commitment point.
"""

import csv
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path

# Fix mpl_toolkits namespace: venv matplotlib vs system mpl_toolkits conflict
import mpl_toolkits
_venv_mpl = str(Path(matplotlib.__file__).resolve().parent.parent / 'mpl_toolkits')
if _venv_mpl not in mpl_toolkits.__path__:
    mpl_toolkits.__path__.insert(0, _venv_mpl)
from mpl_toolkits.mplot3d import Axes3D
# Re-register the 3d projection in case it was missed during init
from matplotlib.projections import projection_registry
projection_registry.register(Axes3D)

# ---------------------------------------------------------------------------
# 1. Load simulation data
# ---------------------------------------------------------------------------
DATA = Path(__file__).resolve().parent.parent.parent.parent.parent / \
    "My_Project" / "thermodynamics" / "data" / "simulation_data.csv"

with open(DATA) as f:
    rows = list(csv.DictReader(f))

time_s = np.array([float(r['Time (s)']) for r in rows])
time_min = time_s / 60.0

atp = np.array([float(r['ATP_pool (mM)']) for r in rows])
spo0a_p = np.array([float(r['Spo0A_P (mM)']) for r in rows])
sigma_h = np.array([float(r['SigmaH (mM)']) for r in rows])
sigma_f = np.array([float(r['SigmaF (mM)']) for r in rows])
sigma_e = np.array([float(r['SigmaE (mM)']) for r in rows])
sigma_g = np.array([float(r['SigmaG (mM)']) for r in rows])
sigma_k = np.array([float(r['SigmaK (mM)']) for r in rows])
forespore = np.array([float(r['Forespore (mM)']) for r in rows])
mature_spore = np.array([float(r['Mature_spore (mM)']) for r in rows])

# ---------------------------------------------------------------------------
# 2. Compute sporulation order parameter φ(t) ∈ [0, 1]
#    Weighted sum of cascade progress, normalized to [0, 1]
# ---------------------------------------------------------------------------
# Each species contributes proportionally to its cascade depth
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
phi = phi_raw / max(phi_raw.max(), 1e-9)  # normalize to [0, 1]

# ---------------------------------------------------------------------------
# 3. Find commitment point
# ---------------------------------------------------------------------------
theta_eff = 2.21  # mM
commit_idx = np.argmax(atp < theta_eff)
t_commit = time_min[commit_idx]  # 293.9 min
phi_commit = phi[commit_idx]

# Mature spore appearance
spore_idx = np.argmax(mature_spore > 0.001)
t_spore = time_min[spore_idx]  # 334.2 min

# ---------------------------------------------------------------------------
# 4. Construct Waddington pseudo-potential U(φ, t)
#
#    Before commitment: double-well with vegetative basin deeper
#    At commitment: equal wells (bifurcation)
#    After commitment: sporulation basin deeper, vegetative blocked
# ---------------------------------------------------------------------------
phi_grid = np.linspace(-0.1, 1.1, 300)
t_grid = np.linspace(0, 360, 200)
PHI, T = np.meshgrid(phi_grid, t_grid)

# Bifurcation parameter: normalized time through commitment
# s < 0 before commitment, s = 0 at commitment, s > 0 after
s = (T - t_commit) / 60.0  # scaled

# Double-well potential: U = a(s)·φ⁴ - b(s)·φ² + c(s)·φ
# Before commitment (s < 0): minimum at φ ≈ 0 (vegetative)
# After commitment (s > 0): minimum at φ ≈ 1 (sporulation)

# Quartic landscape with time-dependent asymmetry
a = 4.0  # quartic stiffness — deeper valleys
b = 2.5 + 0.8 * np.tanh(s * 1.2)  # barrier evolves
c = -1.8 * np.tanh(s * 1.8)  # asymmetry: tilts toward sporulation

# Center potentials around φ = 0.5
phi_c = PHI - 0.5
U = a * phi_c**4 - b * phi_c**2 + c * phi_c

# Soft confining walls (gentle rise, no hard edges)
U += 3.0 * np.maximum(0, -PHI)**2
U += 3.0 * np.maximum(0, PHI - 1.0)**2

# Clip to reasonable range
U = np.clip(U, -3.0, 5)

# ---------------------------------------------------------------------------
# 5. Plot
# ---------------------------------------------------------------------------
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')

# Custom colormap: deep blue (vegetative) → white (barrier) → dark red (sporulation)
colors_list = [
    '#001a4d', '#003399', '#0055cc', '#3388ee',
    '#88bbff', '#ccddff', '#ffffff',
    '#ffddcc', '#ffaa88', '#ee6633',
    '#cc3300', '#991a00', '#660000'
]
cmap_basin = LinearSegmentedColormap.from_list('basin', colors_list, N=256)

# Plot surface
surf = ax.plot_surface(
    T, PHI, U,
    cmap=cmap_basin, alpha=0.75,
    rstride=2, cstride=2,
    linewidth=0.1, edgecolor='none',
    antialiased=True
)

# --- Overlay the actual trajectory as a smooth curve ---
# Smooth φ with a moving average before plotting
from scipy.ndimage import uniform_filter1d
phi_smooth = uniform_filter1d(phi, size=300)

step = max(1, len(time_min) // 200)
t_traj = time_min[::step]
phi_traj = phi_smooth[::step]

# Compute potential at trajectory points
s_traj = (t_traj - t_commit) / 60.0
phi_c_traj = phi_traj - 0.5
U_traj = a * phi_c_traj**4 - (2.5 + 0.8 * np.tanh(s_traj * 1.2)) * phi_c_traj**2 + \
         (-1.8 * np.tanh(s_traj * 1.8)) * phi_c_traj
U_traj = np.clip(U_traj, -3.0, 5)

# Trajectory on surface (slightly above)
ax.plot(t_traj, phi_traj, U_traj + 0.12,
        color='white', linewidth=2.8, zorder=10, alpha=0.95)

# Commitment point marker — raised well above surface
phi_commit_s = phi_smooth[commit_idx]
s_c = 0.0
phi_c_c = phi_commit_s - 0.5
U_commit = a * phi_c_c**4 - (2.5 + 0.8 * np.tanh(0)) * phi_c_c**2 + \
           (-1.8 * np.tanh(0)) * phi_c_c
ax.scatter([t_commit], [phi_commit_s], [U_commit + 2.0],
           color='#ffcc00', s=220, marker='o', edgecolors='black',
           linewidth=2.0, zorder=100, depthshade=False)
# Vertical stem from trajectory to marker
ax.plot([t_commit, t_commit], [phi_commit_s, phi_commit_s],
        [U_commit + 0.12, U_commit + 2.0],
        color='black', linewidth=1.0, linestyle=':', alpha=0.6, zorder=99)

# Mature spore marker — raised well above surface
phi_spore_s = phi_smooth[spore_idx]
s_sp = (t_spore - t_commit) / 60.0
phi_c_sp = phi_spore_s - 0.5
U_spore = a * phi_c_sp**4 - (2.5 + 0.8 * np.tanh(s_sp * 1.2)) * phi_c_sp**2 + \
          (-1.8 * np.tanh(s_sp * 1.8)) * phi_c_sp
ax.scatter([t_spore], [phi_spore_s], [U_spore + 2.0],
           color='#00cc44', s=280, marker='*', edgecolors='black',
           linewidth=1.2, zorder=100, depthshade=False)
# Vertical stem
ax.plot([t_spore, t_spore], [phi_spore_s, phi_spore_s],
        [U_spore + 0.12, U_spore + 2.0],
        color='black', linewidth=1.0, linestyle=':', alpha=0.6, zorder=99)

# --- θ_eff dashed line — visible from chosen viewing angle ---
# Vertical line on the high-φ wall (front face at this azimuth)
ax.plot([t_commit, t_commit], [1.05, 1.05], [-3.0, 4.5],
        color='red', linewidth=1.8, linestyle='--', alpha=0.8, zorder=50)
# Floor line spanning full φ at t_commit (always visible)
ax.plot([t_commit, t_commit], [-0.05, 1.05], [-3.0, -3.0],
        color='red', linewidth=1.4, linestyle='--', alpha=0.5, zorder=50)
# Label
ax.text(t_commit + 4, 1.07, 3.8, r'$\theta_{\mathrm{eff}}$',
        color='red', fontsize=11, fontweight='bold', zorder=101)

# --- Axes labels only ---
ax.set_xlabel('Time (min)', fontsize=11, labelpad=10)
ax.set_ylabel('φ', fontsize=12, labelpad=10)
ax.set_zlabel('U(φ, t)', fontsize=12, labelpad=8)

ax.set_xlim(0, 360)
ax.set_ylim(-0.05, 1.05)
ax.set_zlim(-3.0, 4.5)

# View angle — adjusted so θ_eff line and both basins are visible
ax.view_init(elev=32, azim=-55)

plt.tight_layout()

# ---------------------------------------------------------------------------
# 6. Save
# ---------------------------------------------------------------------------
out_dir = Path(__file__).resolve().parent
out_pdf = out_dir / 'fig_waddington_basin.pdf'
out_png = out_dir / 'fig_waddington_basin.png'

plt.savefig(str(out_pdf), dpi=300, bbox_inches='tight')
plt.savefig(str(out_png), dpi=200, bbox_inches='tight')
plt.close()

print(f"✓ {out_pdf.name}")
print(f"✓ {out_png.name}")
print(f"  Commitment: t = {t_commit:.1f} min, φ = {phi_commit:.3f}")
print(f"  Mature spore: t = {t_spore:.1f} min, φ = {phi[spore_idx]:.3f}")
print(f"  Δt(commitment → spore) = {t_spore - t_commit:.1f} min")
