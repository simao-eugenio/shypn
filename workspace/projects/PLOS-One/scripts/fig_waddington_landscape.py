#!/usr/bin/env python3
"""
Figure 1 — Waddington epigenetic potential landscape (v9, data-driven)

Style: matches doc/universal_pt/figures/fig_waddington_basin_2d.png
  X axis  : Time (min)
  Y axis  : φ  sporulation order parameter [0,1]
  Colour  : U(φ,t) = −ln P(φ,t) from per-replicate KDE at each time slice
            dark-blue = attractor basin  |  white ridge = separatrix  |  dark-red = barrier
  White line : mean φ(t) across all 50 replicates (smoothed)
  Dashed red : median σH-crossing time (commitment clock)
  Yellow ●   : commitment point (φ_mean at t_commit)
  Green  ★   : mature-spore formation point

Data source:  run_20260614_123652  ·  N0=1440 µM, dose=0, SinR=12
"""

import json, re, csv
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.ndimage import uniform_filter1d
from scipy.interpolate import interp1d
from matplotlib.colors import LinearSegmentedColormap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ──────────────────────────────────────────────────────────────────────────────
PROJECT = Path(__file__).resolve().parents[1]
RUN_DIR = PROJECT / "experiments/results/run_20260614_123652"
FIG_DIR = PROJECT / "doc/review/figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

SPOR_THRESHOLD = 0.50

# ──────────────────────────────────────────────────────────────────────────────
# Locate natural condition directory
# ──────────────────────────────────────────────────────────────────────────────
def find_cond(N0, sinr_m0, dose):
    for d in RUN_DIR.iterdir():
        if not d.is_dir() or d.name == "condition_Baseline":
            continue
        m = {k: re.search(p, d.name) for k, p in [
            ("N0",   r"INITIAL_NUTRIENTS_eq_([\d.]+)"),
            ("sinr", r"SinR_eq_([\d.]+)"),
            ("dose", r"LOADING_DOSE_eq_([\d.]+)")]}
        if (m["N0"] and abs(float(m["N0"].group(1)) - N0) < 1 and
                m["sinr"] and abs(float(m["sinr"].group(1)) - sinr_m0) < 1 and
                m["dose"] and abs(float(m["dose"].group(1)) - dose) < 1):
            return d
    return None

nat_dir = find_cond(1440, 12, 0)
assert nat_dir, "Natural condition not found"
print(f"Condition: {nat_dir.name}")

# ──────────────────────────────────────────────────────────────────────────────
# Load all 50 replicate trajectories
# ──────────────────────────────────────────────────────────────────────────────
print("Loading trajectories...")
trajs = []
for f in sorted((nat_dir / "replicates_trajectories").glob("run_*.csv")):
    rows, hdr = [], None
    with open(f) as fh:
        for line in fh:
            if line.startswith("#"): continue
            if hdr is None: hdr = line.strip().split(","); continue
            rows.append(line.strip().split(","))
    if hdr and rows:
        df = pd.DataFrame(rows, columns=hdr).astype(float)
        df["time_min"] = df["time"] / 60.0
        trajs.append(df)
reps = pd.read_csv(nat_dir / "replicates.csv")
print(f"  {len(trajs)} trajectories, {len(trajs[0])} time points each")

# ──────────────────────────────────────────────────────────────────────────────
# Order parameter φ(t) for each replicate
# Same weighted composite as gen_waddington_basin_2d.py
# ──────────────────────────────────────────────────────────────────────────────
WEIGHTS = {
    "Spo0A_P":     0.10,
    "SigmaH":      0.10,
    "SigmaF":      0.15,
    "SigmaE":      0.15,
    "SigmaG":      0.15,
    "SigmaK":      0.10,
    "Forespore":   0.15,
    "Mature_spore":0.10,
}

# Normalise each species by its maximum across all replicates & time
maxima = {sp: max(t[sp].max() for t in trajs if sp in t.columns) + 1e-9
          for sp in WEIGHTS}

n_rep = len(trajs)
n_tp  = min(len(t) for t in trajs)      # common length

phi_mat = np.zeros((n_rep, n_tp))       # [replicate, time]
for i, traj in enumerate(trajs):
    phi_raw = sum(w * traj[sp].values[:n_tp] / maxima[sp]
                  for sp, w in WEIGHTS.items() if sp in traj.columns)
    phi_mat[i] = phi_raw / max(phi_raw.max(), 1e-9)

time_min = trajs[0]["time_min"].values[:n_tp]

# Mean φ trajectory (smoothed for overlay)
phi_mean = phi_mat.mean(axis=0)
phi_smooth = uniform_filter1d(phi_mean, size=max(1, n_tp // 80))

# Fate masks
spor_mask = reps["Mature_spore_final"].astype(float).values > SPOR_THRESHOLD

# ──────────────────────────────────────────────────────────────────────────────
# Key events from data  (must precede U construction — t_commit feeds the well)
# ──────────────────────────────────────────────────────────────────────────────
# Commitment time: median σH crossing in sporulating replicates
sigma_h_trajs = [trajs[i]["SigmaH"].values[:n_tp] for i in range(n_rep)]
sigma_h_mat   = np.vstack(sigma_h_trajs)
SEPARATRIX = 1.60  # µM

commit_times = []
for i in np.where(spor_mask)[0]:
    cross = np.searchsorted(sigma_h_mat[i], SEPARATRIX)
    if cross < n_tp:
        commit_times.append(float(time_min[cross]))
t_commit = float(np.median(commit_times)) if commit_times else 300.0
print(f"  t_commit (median σH crossing) = {t_commit:.0f} min")

# Trajectory interpolator (used for markers)
phi_mean_interp = interp1d(time_min, phi_smooth, kind="linear",
                            bounds_error=False, fill_value=(phi_smooth[0], phi_smooth[-1]))
phi_at_commit = float(phi_mean_interp(t_commit))

# Mature spore time: when mean Mature_spore > 0.1
mature_mean = np.mean(
    np.vstack([t["Mature_spore"].values[:n_tp] for t in trajs]), axis=0)
spore_idx  = np.searchsorted(mature_mean, 0.1)
t_spore    = float(time_min[spore_idx]) if spore_idx < n_tp else float(time_min[-1])
phi_at_spore = float(phi_mean_interp(t_spore))
print(f"  t_spore (mean Mature_spore>0.1) = {t_spore:.0f} min")

# ──────────────────────────────────────────────────────────────────────────────
# Analytic pseudo-potential  U(φ, t) — quartic double-well
# Calibrated to v9: t_commit from data, ~48% sporulation (near-symmetric)
#
#   U = a·φ_c⁴  −  b(t)·φ_c²  +  c(t)·φ_c     where φ_c = φ − 0.5
#
#   s = (t − t_commit) / 60     [dimensionless time offset]
#   b(s) : barrier height grows after commitment  (tanh transition)
#   c(s) : slight vegetative tilt (c > 0 → φ=0 basin lower)  for 48% spor.
# ──────────────────────────────────────────────────────────────────────────────
print("Building analytic quasi-potential U(φ,t)...")

T_MAX    = 360.0
t_grid   = np.linspace(0, T_MAX, 220)
phi_grid = np.linspace(-0.05, 1.05, 300)
T_mesh, PHI = np.meshgrid(t_grid, phi_grid)

s = (T_mesh - t_commit) / 60.0          # normalised, centred on commitment

a = 4.0
b = 2.5 + 0.8 * np.tanh(s * 1.2)       # ~1.7 early → ~3.3 late
# c > 0  →  vegetative basin (φ_c < 0) is lower
# Ramp from large positive (single veg. well) to near-zero (48% spor. → symmetric)
c = 1.0 * (1.0 - np.tanh(s * 1.5))     # ~2.0 early → ~0.04 late

phi_c = PHI - 0.5
U = a * phi_c**4 - b * phi_c**2 + c * phi_c

# Soft walls to keep landscape bounded at edges
U += 3.0 * np.maximum(0, -PHI)**2
U += 3.0 * np.maximum(0, PHI - 1.0)**2

print(f"  U range: [{U.min():.3f}, {U.max():.3f}]")

# ──────────────────────────────────────────────────────────────────────────────
# Plot
# ──────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 5.5))

# Colormap: dark-blue (low U, basin) → white (ridge) → dark-red (high U, barrier)
cmap_colors = [
    "#000033", "#001a4d", "#003399", "#0055cc",
    "#3388ee", "#88bbff", "#ccddff", "#ffffff",
    "#ffddcc", "#ffaa88", "#ee6633",
    "#cc3300", "#991a00", "#660000", "#440000",
]
cmap_basin = LinearSegmentedColormap.from_list("basin", cmap_colors, N=256)

u_min = float(U.min())
u_max = float(U.max())
levels = np.linspace(u_min, u_max, 45)
cf = ax.contourf(t_grid, phi_grid, U, levels=levels,
                 cmap=cmap_basin, extend="both")
ax.contour(t_grid, phi_grid, U,
           levels=np.linspace(u_min, u_max, 18),
           colors="k", linewidths=0.25, alpha=0.30)

# Colorbar
cbar = fig.colorbar(cf, ax=ax, label=r"$U(\varphi, t)$", pad=0.015,
                    fraction=0.035)
cbar.ax.tick_params(labelsize=8)

# Mean φ trajectory
t_traj  = np.linspace(0, min(T_MAX, time_min[-1]), 600)
phi_t   = phi_mean_interp(t_traj)
ax.plot(t_traj, phi_t, color="white",     lw=2.5, alpha=0.95, zorder=5)
ax.plot(t_traj, phi_t, color="black",     lw=0.8, alpha=0.35, zorder=5)

# Commitment vertical dashed line
ax.axvline(t_commit, color="#ff4444", lw=1.8, ls="--", alpha=0.85, zorder=4)

# Markers
ax.scatter([t_commit], [phi_at_commit],
           color="#ffcc00", s=160, marker="o", edgecolors="black",
           linewidths=1.5, zorder=10)
ax.scatter([t_spore], [phi_at_spore],
           color="#00cc44", s=220, marker="*", edgecolors="black",
           linewidths=1.0, zorder=10)

# Annotations
ax.text(t_commit + 4, 0.97, f"$t_{{\\rm commit}}={t_commit:.0f}$ min",
        color="#ff6666", fontsize=9, va="top", ha="left")
# "Vegetative" — bottom-left, directly over the deep blue well
ax.text(130, 0.07, "Vegetative",
        color="white", fontsize=10, fontstyle="italic", fontweight="bold",
        ha="center", va="bottom", zorder=15)
# "Sporulation" — top-right, over the forming upper attractor
ax.text(335, 0.88, "Sporulation",
        color="#003380", fontsize=10, fontstyle="italic", fontweight="bold",
        ha="center", va="top", zorder=15)
ax.text(t_commit - 3, 0.50, r"$\sigma_H$ separatrix",
        color="#ffee88", fontsize=8, ha="right", va="center", rotation=90)

ax.set_xlabel("Time (min)", fontsize=12)
ax.set_ylabel(r"$\varphi$  (sporulation order parameter)", fontsize=12)
ax.set_title(
    r"Epigenetic Potential Landscape $-$ $\it{B.\/subtilis}$ Sporulation"
    "\n"
    r"Analytic double-well  $U(\varphi,t) = a\,\phi_c^4 - b(t)\,\phi_c^2 + c(t)\,\phi_c$"
    f"  ·  mean $\\varphi(t)$ from 50 replicates",
    fontsize=11
)
ax.set_xlim(0, T_MAX)
ax.set_ylim(-0.02, 1.02)

ax.get_legend().remove() if ax.get_legend() else None

plt.tight_layout()

# ── Save two language variants from the same rendered figure ─────────────────
THESIS_FIG_DIR = PROJECT / "doc/universal_pt/figures"
THESIS_FIG_DIR.mkdir(parents=True, exist_ok=True)

_LABELS = {
    "pt": {
        "xlabel": "Tempo (min)",
        "ylabel": r"$\varphi$  (parâmetro de ordem da esporulação)",
        "title": (
            r"Paisagem de Potencial Epigenético $-$ $\it{B.\/subtilis}$ Esporulação"
            "\n"
            r"Poço duplo analítico  $U(\varphi,t) = a\,\phi_c^4 - b(t)\,\phi_c^2 + c(t)\,\phi_c$"
            f"  ·  $\\varphi(t)$ médio de 50 réplicas"
        ),
        "veg": "Vegetativo",
        "spo": "Esporulação",
        "sep": r"separatriz $\sigma_H$",
    },
    "en": {
        "xlabel": "Time (min)",
        "ylabel": r"$\varphi$  (sporulation order parameter)",
        "title": (
            r"Epigenetic Potential Landscape $-$ $\it{B.\/subtilis}$ Sporulation"
            "\n"
            r"Analytic double-well  $U(\varphi,t) = a\,\phi_c^4 - b(t)\,\phi_c^2 + c(t)\,\phi_c$"
            f"  ·  mean $\\varphi(t)$ from 50 replicates"
        ),
        "veg": "Vegetative",
        "spo": "Sporulation",
        "sep": r"$\sigma_H$ separatrix",
    },
}

_OUTPUTS = {
    "pt": [
        (THESIS_FIG_DIR / "fig_waddington_basin_2d.pdf", {}),
    ],
    "en": [
        (FIG_DIR / "fig_waddington_landscape.pdf", {}),
        (FIG_DIR / "fig_waddington_landscape.png", {"dpi": 200}),
    ],
}

# Find the annotation Text objects added above so we can swap them per language
_veg_txt  = next(t for t in ax.texts if "Vegetat" in t.get_text() or "Vegetati" in t.get_text())
_spo_txt  = next(t for t in ax.texts if "Sporulat" in t.get_text() or "Esporula" in t.get_text())
_sep_txt  = next(t for t in ax.texts if "separatr" in t.get_text() or "sigma_H" in t.get_text().lower() or r"\sigma_H" in t.get_text())

saved = []
for lang, lbl in _LABELS.items():
    ax.set_xlabel(lbl["xlabel"], fontsize=12)
    ax.set_ylabel(lbl["ylabel"], fontsize=12)
    ax.set_title(lbl["title"], fontsize=11)
    _veg_txt.set_text(lbl["veg"])
    _spo_txt.set_text(lbl["spo"])
    _sep_txt.set_text(lbl["sep"])
    fig.canvas.draw()   # re-render text
    for path, kw in _OUTPUTS[lang]:
        kw2 = dict(bbox_inches="tight", **kw)
        fig.savefig(path, **kw2)
        saved.append(path)

plt.close(fig)
print("\nSaved:")
for p in saved:
    print(f"  {p}")
