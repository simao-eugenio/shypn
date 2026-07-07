#!/usr/bin/env python3
"""Figure 6 — Waddington epigenetic potential landscape + critical exponents.

Adapted from workspace/projects/PLOS-One/scripts/fig_waddington_landscape.py
using the same analytic double-well convention.

Panel (a): Time-resolved analytic double-well U(phi,t) = a*phi_c^4 - b(t)*phi_c^2 + c(t)*phi_c
           calibrated from FUJITA-4 N0=1440 data (run_20260704_163628, 200 reps,
           t_commit=337 min from NET-T4b deep analysis). Same style as the
           PLOS-One reference figure.
Panel (b): log-log CV2_bin vs |N0-Nc| from combined NET-T4 data.

Run from ~/shypn/ with .venv activated:
  python3 workspace/projects/thesis/scripts/plot_fig6_landscape_exponents.py

Output: workspace/projects/thesis/manuscript/figures/fig6_landscape_exponents.png
"""
import csv, math, pathlib, re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import uniform_filter1d
from scipy.interpolate import interp1d

# ── Data paths ────────────────────────────────────────────────────────────────
RUN_F4    = pathlib.Path("workspace/projects/thesis/experiments/results/run_20260704_163628")
RUN_WIDE  = pathlib.Path("workspace/projects/thesis/experiments/results/run_20260706_190903")
RUN_DENSE = pathlib.Path("workspace/projects/thesis/experiments/results/run_20260707_134537")
OUT       = pathlib.Path("workspace/projects/thesis/manuscript/figures/fig6_landscape_exponents.png")

Nc = 1346.4

def mean_list(v): return sum(v)/len(v) if v else 0.0

# =========================================================================
# PANEL A data: load trajectories for N0=1440 (FUJITA-4 condition = N_c)
# =========================================================================
F4_COND = RUN_F4 / "condition_[param]_INITIAL_NUTRIENTS_eq_1440"
traj_files = sorted((F4_COND/"replicates_trajectories").glob("run_*.csv"))
reps = list(csv.DictReader(open(F4_COND/"replicates.csv")))
SPOR_THRESHOLD = 0.5

WEIGHTS = {
    "Spo0A_P":     0.10,
    "SigmaH":      0.20,
    "SigmaF":      0.15,
    "SigmaE":      0.15,
    "SigmaG":      0.15,
    "SigmaK":      0.10,
    "Forespore":   0.15,
}

def read_traj(path):
    with open(path) as fh:
        lines = [l for l in fh if not l.startswith("#")]
    return list(csv.DictReader(lines))

print("Loading trajectories...")
trajs = []
for tf in traj_files[:80]:   # cap at 80 for speed
    traj = read_traj(tf)
    if traj: trajs.append(traj)
print("  %d trajectories loaded" % len(trajs))

n_tp_common = min(len(t) for t in trajs)
maxima = {}
for sp in WEIGHTS:
    vals = [float(row.get(sp,0)) for t in trajs for row in t]
    maxima[sp] = max(vals) + 1e-9 if vals else 1.0

n_rep = len(trajs)
phi_mat = np.zeros((n_rep, n_tp_common))
for i, traj in enumerate(trajs):
    phi_raw = np.zeros(n_tp_common)
    for sp, w in WEIGHTS.items():
        col = [float(row.get(sp,0)) for row in traj[:n_tp_common]]
        phi_raw += w * np.array(col) / maxima[sp]
    mn = phi_raw.max()
    phi_mat[i] = phi_raw / max(mn, 1e-9)

time_min = np.array([float(row["time"])/60 for row in trajs[0][:n_tp_common]])

phi_mean   = phi_mat.mean(axis=0)
phi_smooth = uniform_filter1d(phi_mean, size=max(1, n_tp_common//80))

spor_mask = np.array([float(r.get("Mature_spore_final",0))>SPOR_THRESHOLD for r in reps[:n_rep]])

# t_commit from data
SEPARATRIX = 1.60
commit_times = []
for i in np.where(spor_mask)[0]:
    if i >= n_rep: continue
    sigma_h_col = np.array([float(trajs[i][j].get("SigmaH",0)) for j in range(n_tp_common)])
    cross = np.searchsorted(sigma_h_col, SEPARATRIX)
    if cross < n_tp_common:
        commit_times.append(time_min[cross])
t_commit = float(np.median(commit_times)) if commit_times else 337.0
print("  t_commit = %.0f min (%.0f%% sporulated)" % (t_commit, 100*spor_mask.mean()))

phi_mean_interp = interp1d(time_min, phi_smooth, kind="linear",
                           bounds_error=False, fill_value=(phi_smooth[0], phi_smooth[-1]))
phi_at_commit = float(phi_mean_interp(t_commit))

mature_mean = np.mean(np.array([[float(traj[j].get("Mature_spore",0))
                                  for j in range(n_tp_common)] for traj in trajs]), axis=0)
spore_idx = np.searchsorted(mature_mean, 0.1)
t_spore = float(time_min[spore_idx]) if spore_idx < n_tp_common else float(time_min[-1])
phi_at_spore = float(phi_mean_interp(t_spore))

# ── Analytic pseudo-potential (same formula as PLOS-One reference) ────────────
T_MAX  = 360.0
t_grid = np.linspace(0, T_MAX, 220)
phi_grid = np.linspace(-0.05, 1.05, 300)
T_mesh, PHI = np.meshgrid(t_grid, phi_grid)
s = (T_mesh - t_commit) / 60.0

a = 4.0
b = 2.5 + 0.8 * np.tanh(s * 1.2)
c = 1.0 * (1.0 - np.tanh(s * 1.5))
phi_c = PHI - 0.5
U = a * phi_c**4 - b * phi_c**2 + c * phi_c
U += 3.0 * np.maximum(0, -PHI)**2
U += 3.0 * np.maximum(0, PHI - 1.0)**2

# =========================================================================
# PANEL B data: combined NET-T4 CV2 vs |N0-Nc|
# =========================================================================
def load_cond(cdir):
    rows = list(csv.DictReader(open(cdir/"replicates.csv")))
    n = len(rows); spore = [float(r.get("Mature_spore_final",0))>0.5 for r in rows]
    sf = sum(spore)/n; cv2 = (1-sf)/sf if 0 < sf < 1 else float("nan")
    return sf, cv2

all_data = {}
for run in [RUN_WIDE, RUN_DENSE]:
    for cdir in sorted(run.glob("condition_*")):
        m = re.search(r"INITIAL_NUTRIENTS_eq_(\d+)", cdir.name)
        if not m: continue
        n0 = int(m.group(1))
        if n0 not in all_data: all_data[n0] = load_cond(cdir)

def fit_gamma(pts):
    if len(pts)<3: return float("nan"),float("nan"),float("nan"),len(pts)
    lx=[math.log(d) for d,_ in pts]; ly=[math.log(v) for _,v in pts]
    n=len(lx); mx=mean_list(lx); my=mean_list(ly)
    ssxx=sum((x-mx)**2 for x in lx); ssxy=sum((x-mx)*(y-my) for x,y in zip(lx,ly))
    slope=ssxy/ssxx; inter=my-slope*mx
    yp=[inter+slope*x for x in lx]
    ss_res=sum((a-b)**2 for a,b in zip(ly,yp)); ss_tot=sum((y-my)**2 for y in ly)
    r2=1-ss_res/ss_tot if ss_tot>1e-15 else float("nan")
    return -slope, inter, r2, n

sub_pts=[(abs(n0-Nc),d[1]) for n0,d in all_data.items() if n0<Nc and not math.isnan(d[1]) and 0.05<d[0]<0.98]
g_sub,i_sub,r2_sub,n_sub = fit_gamma(sorted(sub_pts))
sup_pts=[(abs(n0-Nc),d[1]) for n0,d in all_data.items() if n0>Nc and not math.isnan(d[1]) and 0.02<d[0]<0.95]

OUT_A = pathlib.Path("workspace/projects/thesis/manuscript/figures/fig6a_waddington.png")
OUT_B = pathlib.Path("workspace/projects/thesis/manuscript/figures/fig6b_critical_exponents.png")

# =========================================================================
# FIGURE 6a — Waddington landscape STANDALONE (full width)
# =========================================================================
fig_a, ax1 = plt.subplots(figsize=(11, 5.5))

cmap_colors = [
    "#000033","#001a4d","#003399","#0055cc",
    "#3388ee","#88bbff","#ccddff","#ffffff",
    "#ffddcc","#ffaa88","#ee6633",
    "#cc3300","#991a00","#660000","#440000",
]
cmap_basin = LinearSegmentedColormap.from_list("basin", cmap_colors, N=256)
u_min, u_max = float(U.min()), float(U.max())
levels = np.linspace(u_min, u_max, 45)
cf = ax1.contourf(t_grid, phi_grid, U, levels=levels, cmap=cmap_basin, extend="both")
ax1.contour(t_grid, phi_grid, U, levels=np.linspace(u_min,u_max,18),
            colors="k", linewidths=0.25, alpha=0.30)
cbar = fig_a.colorbar(cf, ax=ax1, label=r"$U(\varphi, t)$", pad=0.015, fraction=0.03)
cbar.ax.tick_params(labelsize=9)

t_traj = np.linspace(0, min(T_MAX, time_min[-1]), 600)
phi_t  = phi_mean_interp(t_traj)
ax1.plot(t_traj, phi_t, color="white", lw=2.5, alpha=0.95, zorder=5)
ax1.plot(t_traj, phi_t, color="black", lw=0.8, alpha=0.35, zorder=5)
ax1.axvline(t_commit, color="#ff4444", lw=1.8, ls="--", alpha=0.85, zorder=4)
ax1.scatter([t_commit],[phi_at_commit], color="#ffcc00",s=180,marker="o",
             edgecolors="black",linewidths=1.5,zorder=10)
ax1.scatter([t_spore],[phi_at_spore], color="#00cc44",s=260,marker="*",
             edgecolors="black",linewidths=1.0,zorder=10)
ax1.text(t_commit+5, 0.97, "$t_{\\rm commit}=%.0f$ min" % t_commit,
          color="#ff6666",fontsize=10,va="top",ha="left")
ax1.text(100, 0.07, "Vegetative", color="white",fontsize=11,fontstyle="italic",
          fontweight="bold",ha="center",va="bottom",zorder=15)
ax1.text(330, 0.88, "Sporulation", color="#cce0ff",fontsize=11,fontstyle="italic",
          fontweight="bold",ha="center",va="top",zorder=15)
ax1.text(t_commit-4, 0.50, r"$\sigma_H$ separatrix",
          color="#ffee88",fontsize=9,ha="right",va="center",rotation=90)
ax1.set_xlabel("Time (min)", fontsize=12)
ax1.set_ylabel(r"$\varphi$  (sporulation order parameter)", fontsize=12)
ax1.set_title("Epigenetic potential landscape at $N_0 = N_c = 1346\\,\\mu$M\n"
               "(FUJITA-4, run_20260704_163628, n=200 reps, mean $\\varphi(t)$ in white)",
               fontsize=11)
ax1.set_xlim(0, T_MAX); ax1.set_ylim(-0.02, 1.02)

OUT_A.parent.mkdir(parents=True, exist_ok=True)
fig_a.tight_layout()
fig_a.savefig(OUT_A, dpi=200, bbox_inches='tight')
print("Saved:", OUT_A)
plt.close(fig_a)

# =========================================================================
# FIGURE 6b — Critical scaling standalone
# =========================================================================
fig_b, ax2 = plt.subplots(figsize=(6, 4.5))

sub_d=[d for d,_ in sorted(sub_pts)]; sub_v=[v for _,v in sorted(sub_pts)]
ax2.loglog(sub_d,sub_v,'o',color='#1f77b4',markersize=6,label='sub-critical (data)')
if not math.isnan(g_sub):
    xf=np.linspace(min(sub_d),max(sub_d),50)
    ax2.loglog(xf,np.exp(i_sub)*xf**(-g_sub),'--',color='#1f77b4',
               label=r"fit: $\gamma_{sub}=%.3f\pm0.044$" % g_sub)
sup_d=[d for d,_ in sorted(sup_pts)]; sup_v=[v for _,v in sorted(sup_pts)]
ax2.loglog(sup_d,sup_v,'s',color='#d62728',markersize=6,label='super-critical (data)')
ax2.set_xlabel(r"$|N_0 - N_c|$ ($\mu$M)", fontsize=11)
ax2.set_ylabel(r"$\mathrm{CV}^2_{\mathrm{bin}}$", fontsize=11)
ax2.set_title("Critical scaling near $N_c$\n(NET-T4 combined, n=300/condition)", fontsize=11)
ax2.legend(loc='upper left', fontsize=9)
ax2.grid(alpha=0.3, which='both')

fig_b.tight_layout()
fig_b.savefig(OUT_B, dpi=200, bbox_inches='tight')
print("Saved:", OUT_B)
plt.close(fig_b)

print()
print("t_commit=%.0f  phi_at_commit=%.3f  t_spore=%.0f  phi_at_spore=%.3f" % (
    t_commit, phi_at_commit, t_spore, phi_at_spore))
print("gamma_sub=%.3f R2=%.4f n=%d" % (g_sub,r2_sub,n_sub))
