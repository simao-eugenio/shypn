"""
generate_figures.py
====================
Generate all 6 publication figures for the GATA1/PU.1 manuscript.

Data source: Phase B sweep run_20260228_212629
  – 8 EPO conditions (0.430–0.460 mM), N=50 replicates each, t=3600 s
  – Each experiment: results.csv (mean + std trajectories), mean_final_state.csv

Figures:
  fig1_waddington.pdf/png   – approximate 2-well potential landscape
  fig2_p_erythroid.pdf/png  – P(erythroid) flat across EPO range
  fig3_divergence.pdf/png   – stochastic divergence (mean ± SD envelope)
  fig4_mean_trajectory.pdf/png – full t=0–3600 s GATA1 vs PU.1
  fig5_ratchet.pdf/png      – execution ratchet, t=0–400 s zoom
  fig6_receptors.pdf/png    – receptor hierarchy bar chart

Usage:
  python workspace/projects/gata/scripts/generate_figures.py
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from io import StringIO
from scipy import stats

warnings.filterwarnings('ignore')

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE   = "/home/simao/projetos/shypn/workspace/projects/gata/experiments/results/run_20260228_212629"
FIGDIR = "/home/simao/projetos/shypn/workspace/projects/gata/figures"
os.makedirs(FIGDIR, exist_ok=True)

# ── ID → species name mapping ─────────────────────────────────────────────────
ID_TO_NAME = {
    'P1':  'EPO_external',
    'P2':  'GCSF_external',
    'P3':  'EPOR_free',
    'P4':  'EPOR_bound',
    'P5':  'EPOR_internalized',
    'P6':  'GCSFR_free',
    'P7':  'GCSFR_bound',
    'P8':  'GCSFR_internalized',
    'P9':  'GATA1_Gene',
    'P10': 'PU1_Gene',
    'P11': 'GATA1_mRNA_nuc',
    'P12': 'PU1_mRNA_nuc',
    'P13': 'GATA1_mRNA_cyto',
    'P14': 'PU1_mRNA_cyto',
    'P15': 'GATA1_Protein_cyto',
    'P16': 'PU1_Protein_cyto',
    'P17': 'GATA1_Protein_nuc',
    'P18': 'PU1_Protein_nuc',
    'P19': 'ATP',
    'P20': 'ADP',
    'P21': 'GTP',
    'P22': 'GDP',
    'P23': 'Pi',
    'P24': 'pH_cytoplasm',
    'P25': 'pH_nucleus',
    'P26': 'Mg_cytoplasm',
    'P27': 'Temperature',
    'P28': 'pGATA1_nuc',
}

# ── Matplotlib style ──────────────────────────────────────────────────────────
ERYTHROID_BLUE = '#1a3a6b'
MYELOID_RED    = '#8b0000'
PGATA1_VIOLET  = '#4b0082'
ACCENT_RED     = '#cc2200'

plt.rcParams.update({
    'font.family':        'DejaVu Sans',
    'font.size':          9,
    'axes.titlesize':     10,
    'axes.labelsize':     9,
    'xtick.labelsize':    8,
    'ytick.labelsize':    8,
    'figure.dpi':         150,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'lines.linewidth':    1.6,
})


# ── I/O helpers ───────────────────────────────────────────────────────────────
def find_experiments(base):
    """Return {epo_value: path} for all EPO sweep directories."""
    exps = {}
    for d in sorted(os.listdir(base)):
        if d.startswith('experiment_EPO_external='):
            epo = float(d.split('=')[1].split('_')[0])
            exps[epo] = os.path.join(base, d)
    return exps


def _parse_csv_block(lines, start_idx, end_idx=None):
    """Parse a contiguous CSV block from a list of text lines."""
    chunk = lines[start_idx:end_idx]
    data_str = "".join(chunk)
    df = pd.read_csv(StringIO(data_str), low_memory=False)
    # Keep only rows where Time is numeric (drops any stray header/comment rows)
    df = df[pd.to_numeric(df['Time'], errors='coerce').notna()].copy()
    df = df.apply(pd.to_numeric, errors='coerce')
    df.rename(columns=ID_TO_NAME, inplace=True)
    return df


def read_mean_and_std(path):
    """
    Parse results.csv → (mean_df, std_df).
    results.csv has three sections:
      1. Mean trajectories  (after "Species Statistics - Mean Trajectories")
      2. Std trajectories   (after "Species Statistics - Standard Deviations")
      3. Replicate metadata (after "Trajectory Summary")
    """
    with open(os.path.join(path, 'results.csv')) as f:
        lines = f.readlines()

    # Locate section boundaries (line index of the CSV header row for each block)
    mean_label_idx = next(i for i, l in enumerate(lines) if 'Mean Trajectories' in l)
    mean_hdr_idx   = next(i for i, l in enumerate(lines)
                          if i > mean_label_idx and l.startswith('Time,'))

    std_label_idx  = next(i for i, l in enumerate(lines) if 'Standard Deviations' in l)
    std_hdr_idx    = next(i for i, l in enumerate(lines)
                          if i > std_label_idx and l.startswith('Time,'))

    traj_summary_idx = next(i for i, l in enumerate(lines) if 'Trajectory Summary' in l)

    mean_df = _parse_csv_block(lines, mean_hdr_idx, std_label_idx)
    std_df  = _parse_csv_block(lines, std_hdr_idx,  traj_summary_idx)

    return mean_df, std_df


def read_final_states(path):
    """Read mean_final_state.csv → DataFrame indexed by species name."""
    df = pd.read_csv(os.path.join(path, 'mean_final_state.csv'), comment='#')
    return df.set_index('name')


# ── Save helper ───────────────────────────────────────────────────────────────
def save_fig(fig, name):
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(FIGDIR, f'{name}.{ext}'),
                    bbox_inches='tight', dpi=300)
    plt.close(fig)
    print(f"  ✓  {name}.pdf  +  .png")


def _add_title(fig, text, fontsize=12):
    """Bold suptitle with a 3 pt gap between text bottom and axes top.

    Strategy: call tight_layout() first so axes positions are final, then
    compute the true horizontal midpoint of all axes (accounts for ylabel
    label space pushing axes off-centre) and place the suptitle over that
    midpoint.  Finally, subplots_adjust(top=...) sets an exact pt gap.
    """
    fig.tight_layout()
    # Centre title over the actual axes area (not the whole figure width)
    axes = fig.get_axes()
    if axes:
        lefts  = [ax.get_position().x0 for ax in axes]
        rights = [ax.get_position().x0 + ax.get_position().width for ax in axes]
        x_center = (min(lefts) + max(rights)) / 2
    else:
        x_center = 0.5
    fig.suptitle(text, fontsize=fontsize, fontweight='bold',
                 x=x_center, ha='center', y=1.0, va='top')
    h_pt = fig.get_size_inches()[1] * 72          # figure height in points
    fig.subplots_adjust(top=1.0 - (fontsize + 8.0) / h_pt)


# ═══════════════════════════════════════════════════════════════════════════════
# Fig 1 – Approximate Waddington potential landscape
# ═══════════════════════════════════════════════════════════════════════════════
def fig1_waddington(exps):
    """
    Approximate 2-well Waddington landscape using a Gaussian-mixture density
    on the GATA1_nuc × PU.1_nuc plane.

    Attractor positions are estimated from the EPO=0.449 final-state statistics:
      erythroid basin: GATA1 high, PU.1 low
      myeloid   basin: GATA1 low,  PU.1 high
    Well widths are proportional to the observed std_final values.
    """
    fs = read_final_states(exps[0.449])

    mu_g  = fs.loc['GATA1_Protein_nuc', 'mean_final']
    sig_g = fs.loc['GATA1_Protein_nuc', 'std_final']
    min_g = fs.loc['GATA1_Protein_nuc', 'min_final']
    max_g = fs.loc['GATA1_Protein_nuc', 'max_final']

    mu_p  = fs.loc['PU1_Protein_nuc', 'mean_final']
    sig_p = fs.loc['PU1_Protein_nuc', 'std_final']
    min_p = fs.loc['PU1_Protein_nuc', 'min_final']
    max_p = fs.loc['PU1_Protein_nuc', 'max_final']

    # Attractor positions (inferred from mean ± spread)
    g_ery = mu_g + 0.55 * sig_g       # erythroid: high GATA1
    p_ery = max(0.0, mu_p - 0.55 * sig_p)   # erythroid: low PU.1
    g_mye = max(0.0, mu_g - 0.45 * sig_g)   # myeloid:   low GATA1
    p_mye = mu_p + 0.45 * sig_p       # myeloid:   high PU.1

    # Well widths (half the marginal std)
    sg = sig_g * 0.4
    sp = sig_p * 0.4

    # Grid
    gx = np.linspace(max(0.0, min_g - 0.05), max_g + 0.05, 350)
    py = np.linspace(max(0.0, min_p - 0.02), max_p + 0.02, 350)
    GX, PY = np.meshgrid(gx, py)

    # Gaussian mixture: ~65% erythroid, ~35% myeloid
    Z_ery = 0.65 * np.exp(-((GX-g_ery)**2/(2*sg**2) + (PY-p_ery)**2/(2*sp**2)))
    Z_mye = 0.35 * np.exp(-((GX-g_mye)**2/(2*sg**2) + (PY-p_mye)**2/(2*sp**2)))
    density  = Z_ery + Z_mye + 1e-9
    potential = -np.log(density)
    potential -= potential.min()

    # Custom blue-cream-red colormap (deep blue = low energy = basin)
    cmap = LinearSegmentedColormap.from_list(
        'waddington', ['#1a3a6b', '#e8dfc8', '#8b0000'], N=256)

    fig, ax = plt.subplots(figsize=(4.5, 3.8))
    ax.contourf(GX, PY, potential, levels=22, cmap=cmap, alpha=0.9)
    ax.contour( GX, PY, potential, levels=14, colors='white',
                linewidths=0.35, alpha=0.45)

    # Well markers
    ax.plot(g_ery, p_ery, 'o', ms=8, mew=1.8,
            color=ERYTHROID_BLUE, markerfacecolor='white', zorder=5)
    ax.plot(g_mye, p_mye, 's', ms=8, mew=1.8,
            color=MYELOID_RED, markerfacecolor='white', zorder=5)

    # Population mean dot
    ax.plot(mu_g, mu_p, 'D', ms=5, color='#ffd700', zorder=6)

    # Basin labels (no legend)
    ax.text(g_ery + 0.03, p_ery + 0.01, 'Erythroid',
            color='white', fontsize=7.5, fontweight='bold', zorder=7)
    ax.text(g_mye + 0.03, p_mye + 0.01, 'Myeloid',
            color='white', fontsize=7.5, fontweight='bold', zorder=7)

    ax.set_xlabel('GATA1$_{nuc}$ (mM)')
    ax.set_ylabel('PU.1$_{nuc}$ (mM)')

    _add_title(fig, 'Erythroid and myeloid basins of attraction')
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Fig 2 – P(erythroid) micro-clouds on a Waddington landscape background
# ═══════════════════════════════════════════════════════════════════════════════
def fig2_p_erythroid(exps):
    """
    Probability trajectory immersed in noise micro-clouds, rendered on a
    Waddington-landscape background.

    The vertical axis IS the potential landscape projected onto probability space:
      P = 1  (top)   → erythroid basin        (deep blue, low energy)
      P = 0  (bottom)→ myeloid basin          (deep red,  low energy)
      P = 0.5 (mid)  → unstable saddle ridge  (bright cream, high energy)

    Background:  vertical gradient U(p) = −log[ p^α (1−p)^(1−α) ] normalised,
    rendered as a smooth imshow with the basin/ridge topology.
    Streamlines: faint vertical arrows at random x positions showing landscape
    "gravity" — cells flow away from the saddle toward either basin.
    Micro-clouds: 600 MC-sampled cells per EPO condition, coloured by P.
    Trajectory: white-haloed blue line through the ensemble means.
    """
    rng     = np.random.default_rng(42)
    N_CLOUD = 700

    epo_vals    = sorted(exps.keys())
    epo_arr     = np.array(epo_vals)
    epo_spacing = np.diff(epo_arr).min()
    jitter_w    = epo_spacing * 0.30

    x_lo = epo_arr[0]  - epo_spacing * 0.55
    x_hi = epo_arr[-1] + epo_spacing * 0.65

    # ── Waddington background ────────────────────────────────────────────────
    # Potential U(p): symmetric double-well, minima at p→0 and p→1,
    # maximum (saddle) at p=0.5.
    # U(p) = (2p − 1)^2  gives a smooth valley profile:
    #   U(0)=1, U(0.5)=0, U(1)=1  → invert so basins are dark, saddle is bright
    p_vals = np.linspace(0, 1, 512)
    U = (2 * p_vals - 1) ** 2          # 0 at saddle, 1 at basins

    # Build a 2-column image (same at every x), coloured with basin topology:
    # basin blue at p=1, basin red at p=0, cream at p=0.5 saddle
    # Blend: base colour by p (blue↔red), lightened toward saddle by (1-U)
    img_rgb = np.zeros((512, 1, 3))
    blue = np.array([0x1a/255, 0x3a/255, 0x6b/255])
    red  = np.array([0x8b/255, 0x00/255, 0x00/255])
    cream = np.array([0xf5/255, 0xf0/255, 0xe4/255])

    for i, (p, u) in enumerate(zip(p_vals, U)):
        base = p * blue + (1 - p) * red           # interpolate blue↔red by p
        col  = u * base + (1 - u) * cream         # blend toward cream at saddle
        img_rgb[i, 0, :] = np.clip(col, 0, 1)

    # imshow: origin='lower' so p=0 at bottom, p=1 at top; extent covers axes
    fig, ax = plt.subplots(figsize=(5.4, 3.8))
    ax.imshow(img_rgb,
              extent=[x_lo, x_hi, 0, 1],
              origin='lower', aspect='auto', zorder=0, alpha=0.82)

    # ── Potential contours (faint iso-U lines) ────────────────────────────────
    x_cont = np.array([x_lo, x_hi])
    for u_level in [0.1, 0.3, 0.55, 0.78]:
        # U = (2p-1)^2 = u_level  → p = 0.5 ± √u/2
        for p_line in [0.5 - np.sqrt(u_level)/2, 0.5 + np.sqrt(u_level)/2]:
            if 0 < p_line < 1:
                ax.plot(x_cont, [p_line, p_line],
                        color='white', lw=0.5, alpha=0.25, zorder=1)

    # ── Streamlines (landscape gravity, flows away from saddle) ──────────────
    n_streams = 18
    for xs in rng.uniform(x_lo, x_hi, n_streams):
        # Upper half: arrows pointing upward (toward erythroid basin)
        p_s = rng.uniform(0.52, 0.82)
        ax.annotate('', xy=(xs, p_s + 0.06), xytext=(xs, p_s),
                    arrowprops=dict(arrowstyle='->', color='white',
                                   lw=0.55, alpha=0.22),
                    zorder=1)
        # Lower half: arrows pointing downward (toward myeloid basin)
        p_s2 = rng.uniform(0.18, 0.48)
        ax.annotate('', xy=(xs, p_s2 - 0.06), xytext=(xs, p_s2),
                    arrowprops=dict(arrowstyle='->', color='white',
                                   lw=0.55, alpha=0.22),
                    zorder=1)

    # ── Saddle ridge label ────────────────────────────────────────────────────
    ax.text(x_lo + 0.0005, 0.502, 'saddle',
            fontsize=6.5, color='white', alpha=0.55, va='bottom', zorder=2)
    ax.axhline(0.5, color='white', lw=0.6, ls=(0, (4,4)), alpha=0.35, zorder=2)

    # ── Basin labels ──────────────────────────────────────────────────────────
    ax.text(x_hi - 0.0005, 0.87, 'erythroid basin',
            fontsize=7, color='white', alpha=0.7, va='center', ha='right',
            fontweight='bold', zorder=2)
    ax.text(x_lo + 0.0005, 0.03, 'myeloid basin',
            fontsize=7, color='white', alpha=0.7, va='bottom',
            fontweight='bold', zorder=2)

    # ── Micro-basins of attraction ────────────────────────────────────────────
    # At each EPO condition, the ensemble noise defines a local effective
    # potential well centred on the mean P value.  Width in P-space is the
    # empirical std of P(erythroid) across MC replicates (= φ(z)·σ_d/d_std in
    # closed form).  Rendered as nested filled ellipses — topographic contours
    # of a small Waddington micro-well — deepening to a bright highlight at
    # the basin centre.
    from matplotlib.patches import Ellipse

    # Colour helpers: blend two RGB tuples
    def _blend(c1, c2, t):
        return tuple(c1[i] * (1-t) + c2[i] * t for i in range(3))

    # Basin-centre highlight colour (bright cream, high contrast on landscape)
    centre_rgb = (0.97, 0.94, 0.88)

    # Landscape colour at a given p (same formula as the background image)
    blue_rgb  = (0x1a/255, 0x3a/255, 0x6b/255)
    red_rgb   = (0x8b/255, 0x00/255, 0x00/255)
    cream_rgb = (0xf5/255, 0xf0/255, 0xe4/255)
    def _landscape_rgb(p):
        u    = (2*p - 1)**2
        base = tuple(p*blue_rgb[i] + (1-p)*red_rgb[i] for i in range(3))
        return tuple(u*base[i] + (1-u)*cream_rgb[i] for i in range(3))

    N_RINGS   = 7        # concentric contour levels per basin
    sigma_x_v = jitter_w * 0.85   # visual x half-width (≈ EPO spacing / 3)

    p_mean_arr = []

    for epo in epo_vals:
        fs    = read_final_states(exps[epo])
        mu_g  = fs.loc['GATA1_Protein_nuc', 'mean_final']
        mu_p  = fs.loc['PU1_Protein_nuc',   'mean_final']
        s_g   = fs.loc['GATA1_Protein_nuc', 'std_final']
        s_p   = fs.loc['PU1_Protein_nuc',   'std_final']
        d_std = np.sqrt(s_g**2 + s_p**2)

        # Monte Carlo to get empirical σ_P in probability space
        g_s  = np.maximum(0, rng.normal(mu_g, s_g, N_CLOUD))
        p_s  = np.maximum(0, rng.normal(mu_p, s_p, N_CLOUD))
        p_cells = stats.norm.cdf((g_s - p_s) / d_std)
        sigma_p_v = float(np.std(p_cells))   # basin half-width in P-space

        p_mean = float(stats.norm.cdf((mu_g - mu_p) / d_std))
        p_mean_arr.append(p_mean)

        landscape_col = _landscape_rgb(p_mean)

        # Draw rings from outermost (faint, landscape colour) to centre
        # (bright highlight).  Each ring is a filled Ellipse; later rings
        # overwrite earlier ones, creating the nested bowl effect.
        for k in range(N_RINGS, 0, -1):
            t      = 1.0 - (k - 1) / (N_RINGS - 1)   # 0 (outer) → 1 (centre)
            radius = k / N_RINGS                        # 1 → 1/N_RINGS
            colour = _blend(landscape_col, centre_rgb, t**1.6)
            alpha  = 0.30 + 0.55 * t                   # more opaque at centre
            e = Ellipse(
                xy=(epo, p_mean),
                width=2 * sigma_x_v * radius,
                height=2 * sigma_p_v * radius * 1.4,   # slight vertical stretch
                facecolor=colour,
                edgecolor='white',
                linewidth=0.25 * (1 - t*0.6),
                alpha=alpha,
                zorder=3,
            )
            ax.add_patch(e)

        # Central dot: single bright spot at basin bottom
        ax.plot(epo, p_mean, 'o', ms=3.2, color='white',
                alpha=0.9, zorder=4, mew=0)

        # Faint shadow scatter inside basin (shows stochastic population)
        x_j = rng.uniform(epo - sigma_x_v, epo + sigma_x_v, N_CLOUD // 5)
        p_j = rng.normal(p_mean, sigma_p_v * 0.6, N_CLOUD // 5)
        p_j = np.clip(p_j, 0, 1)
        ax.scatter(x_j, p_j, s=1.8, color='white', alpha=0.10,
                   linewidths=0, zorder=3)

    p_mean_arr = np.array(p_mean_arr)

    # ── Mean trajectory ───────────────────────────────────────────────────────
    ax.plot(epo_arr, p_mean_arr, '-', color='white', lw=5.0, zorder=4, alpha=0.9)
    ax.plot(epo_arr, p_mean_arr, 'o-', color=ERYTHROID_BLUE,
            ms=7, lw=2.4, zorder=5, mec='white', mew=1.4)

    # 60–70 % band annotation
    ax.text(x_hi - 0.0005, 0.645, '60–70%',
            va='center', ha='right', fontsize=7.5,
            color='white', alpha=0.85, zorder=6)

    ax.set_xlabel('EPO$_{ext}$ (mM)')
    ax.set_ylabel('P(erythroid commitment)')
    ax.set_ylim(0, 1)
    ax.set_xlim(x_lo, x_hi)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
    # Tick colours visible on dark background
    ax.tick_params(colors='#333')

    _add_title(fig, 'P(erythroid) across EPO dose')
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Fig 3 – Stochastic divergence: mean ± 1 SD envelopes
# ═══════════════════════════════════════════════════════════════════════════════
def fig3_divergence(exps):
    """
    GATA1_nuc and PU.1_nuc mean trajectories with ±1 SD shaded envelopes
    (EPO = 0.449 mM). The envelope width represents stochastic spread across
    the N=50 replicate ensemble, revealing divergent cell fates.
    """
    mean_df, std_df = read_mean_and_std(exps[0.449])

    t      = mean_df['Time'].values
    g_mean = mean_df['GATA1_Protein_nuc'].values
    g_std  = std_df ['GATA1_Protein_nuc'].values
    p_mean = mean_df['PU1_Protein_nuc'].values
    p_std  = std_df ['PU1_Protein_nuc'].values

    fig, ax = plt.subplots(figsize=(5.5, 3.5))

    # GATA1 envelope (blue)
    ax.fill_between(t, np.maximum(0, g_mean - g_std), g_mean + g_std,
                    color=ERYTHROID_BLUE, alpha=0.14)
    ax.plot(t, g_mean, color=ERYTHROID_BLUE, lw=2.0)

    # PU.1 envelope (red)
    ax.fill_between(t, np.maximum(0, p_mean - p_std), p_mean + p_std,
                    color=MYELOID_RED, alpha=0.14)
    ax.plot(t, p_mean, color=MYELOID_RED, lw=2.0)

    # Right-side species labels (avoids legend)
    ax.text(3700, g_mean[-1], 'GATA1$_{nuc}$',
            color=ERYTHROID_BLUE, va='center', fontsize=8.5)
    ax.text(3700, p_mean[-1], 'PU.1$_{nuc}$',
            color=MYELOID_RED,   va='center', fontsize=8.5)

    # ±1 SD callout arrow — placed on PU.1 envelope at t=1800
    # (open space below GATA1, text to the left of the arrow)
    x_ann = 1800
    idx = np.argmin(np.abs(t - x_ann))
    ax.annotate('',
        xy=(x_ann, p_mean[idx] + p_std[idx]),
        xytext=(x_ann, np.maximum(0, p_mean[idx] - p_std[idx])),
        arrowprops=dict(arrowstyle='<->', color=MYELOID_RED,
                        lw=0.9, alpha=0.7))
    ax.text(x_ann - 60, p_mean[idx], '±1 SD', fontsize=7,
            color=MYELOID_RED, va='center', ha='right')

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Concentration (mM)')
    ax.set_xlim(0, 4000)
    ax.set_ylim(bottom=0)

    _add_title(fig, 'Stochastic divergence (mean \u00b11\u2009SD envelopes)')
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Fig 4 – Full mean trajectory: GATA1 rise, PU.1 erosion
# ═══════════════════════════════════════════════════════════════════════════════
def fig4_mean_trajectory(exps):
    """
    EPO overlay: mean GATA1_nuc and PU.1_nuc trajectories for all 8 EPO
    conditions plotted as overlapping bundles.

    GATA1 lines: blue gradient (pale → deep, low → high EPO dose).
    PU.1  lines: red  gradient (pale → deep, low → high EPO dose).

    All 8 curves collapse onto one another — the bundle width is the
    EPO sensitivity of the dynamics, which is visually ≈ 0.  The figure
    directly complements Fig 2's flat P(erythroid): not only does the
    *outcome* not depend on EPO, neither do the *trajectories*.
    """
    epo_vals = sorted(exps.keys())
    n = len(epo_vals)

    # Colour ramps: pale → saturated for each species
    blue_lo = np.array([0.72, 0.80, 0.92])   # pale blue
    blue_hi = np.array([0x1a/255, 0x3a/255, 0x6b/255])  # deep blue
    red_lo  = np.array([0.95, 0.72, 0.72])   # pale red
    red_hi  = np.array([0x8b/255, 0x00/255, 0x00/255])  # deep red

    fig, ax = plt.subplots(figsize=(5.5, 3.2))

    for i, epo in enumerate(epo_vals):
        t_frac = i / (n - 1)                  # 0 (lowest EPO) → 1 (highest)
        c_blue = tuple(blue_lo * (1 - t_frac) + blue_hi * t_frac)
        c_red  = tuple(red_lo  * (1 - t_frac) + red_hi  * t_frac)

        mean_df, _ = read_mean_and_std(exps[epo])
        t     = mean_df['Time'].values
        gata1 = mean_df['GATA1_Protein_nuc'].values
        pu1   = mean_df['PU1_Protein_nuc'].values

        lw    = 1.0 + 0.6 * t_frac            # thicker for higher EPO
        alpha = 0.55 + 0.40 * t_frac

        ax.plot(t, gata1, color=c_blue, lw=lw, alpha=alpha)
        ax.plot(t, pu1,   color=c_red,  lw=lw, alpha=alpha)

    # Right-side labels on the outermost (highest EPO = most saturated) line
    mean_hi, _ = read_mean_and_std(exps[epo_vals[-1]])
    t_hi = mean_hi['Time'].values
    ax.text(3700, mean_hi['GATA1_Protein_nuc'].values[-1],
            'GATA1$_{nuc}$', color=tuple(blue_hi), va='center', fontsize=8.5)
    ax.text(3700, mean_hi['PU1_Protein_nuc'].values[-1],
            'PU.1$_{nuc}$',  color=tuple(red_hi),  va='center', fontsize=8.5)

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Concentration (mM)')
    ax.set_xlim(0, 4200)
    ax.set_ylim(bottom=0)

    _add_title(fig, 'Mean trajectory: GATA1 rise, PU.1 erosion')
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Fig 5 – Execution-layer ratchet (t = 0–400 s zoom)
# ═══════════════════════════════════════════════════════════════════════════════
def fig5_ratchet(exps):
    """
    pGATA1_nuc (violet) and PU.1_nuc (dark red) over the first 400 s.
    Vertical markers identify ratchet events:
      t = 48 s  → ubiquitin first fires
      t = 77 s  → pGATA1_nuc peaks
      t = 146 s → pGATA1_nuc > PU.1_nuc (irreversible ratchet)
    """
    mean_df, _ = read_mean_and_std(exps[0.449])

    t = mean_df['Time'].values
    mask   = t <= 400
    t_z    = t[mask]
    pgata1 = mean_df['pGATA1_nuc'].values[mask]
    pu1    = mean_df['PU1_Protein_nuc'].values[mask]

    fig, ax = plt.subplots(figsize=(5.5, 3.2))

    ax.plot(t_z, pgata1, color=PGATA1_VIOLET, lw=2.2)
    ax.plot(t_z, pu1,    color=ACCENT_RED,    lw=2.2)

    # Y limits (set before computing label positions)
    ymax = max(pgata1.max(), pu1.max()) * 1.18
    ax.set_ylim(0, ymax)

    # Timing markers — staircase ascending on y axis (mirrors commitment progression)
    #   t=48s  : low zone   (ubiquitin fires)
    #   t=77s  : mid zone   (pGATA1 peak)
    #   t=146s : top zone   (ratchet crossing)
    events = [
        (48,  't = 48 s',  0.40),
        (77,  't = 77 s',  0.65),
        (146, 't = 146 s', 0.90),
    ]
    for tx, label, yfrac in events:
        ax.axvline(tx, ls='--', lw=0.9, color='#555', alpha=0.65)
        ax.text(tx + 3, ymax * yfrac, label,
                fontsize=7, color='#444', va='center', ha='left')

    # Right-side labels
    ax.text(410, pgata1[-1], 'pGATA1$_{nuc}$',
            color=PGATA1_VIOLET, va='center', fontsize=8.5)
    ax.text(410, pu1[-1],    'PU.1$_{nuc}$',
            color=ACCENT_RED,   va='center', fontsize=8.5)

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Concentration (mM)')
    ax.set_xlim(0, 430)

    _add_title(fig, 'Execution-layer ratchet (t\u2009=\u20090\u2013400\u2009s)')
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Fig 6 – Receptor occupancy donut + ratio inset
# ═══════════════════════════════════════════════════════════════════════════════
def fig6_receptors(exps):
    """
    Two-panel figure:
      Main: donut chart for EPO=0.449 mM showing EPOR_bound vs GCSFR_bound as
            proportional arcs.  The pre-partitioned 4:1 erythroid bias is
            immediately visible as a dominant blue arc.
      Inset: EPOR/GCSFR ratio across all 8 EPO conditions — flat line at ~4.1×,
             showing the hierarchy is invariant to EPO dose.
    """
    # ── Collect data for all conditions ──────────────────────────────────────
    epo_vals = sorted(exps.keys())
    epo_arr  = np.array(epo_vals)
    epor_m, gcsfr_m = [], []
    epor_s, gcsfr_s = [], []

    for epo in epo_vals:
        fs = read_final_states(exps[epo])
        epor_m.append(fs.loc['EPOR_bound',  'mean_final'])
        gcsfr_m.append(fs.loc['GCSFR_bound', 'mean_final'])
        epor_s.append(fs.loc['EPOR_bound',  'std_final'])
        gcsfr_s.append(fs.loc['GCSFR_bound', 'std_final'])

    epor_m  = np.array(epor_m);  epor_s  = np.array(epor_s)
    gcsfr_m = np.array(gcsfr_m); gcsfr_s = np.array(gcsfr_s)
    ratios  = epor_m / gcsfr_m

    # Representative condition: EPO = 0.449
    rep_idx = epo_vals.index(0.449)
    e_val   = epor_m[rep_idx]
    g_val   = gcsfr_m[rep_idx]
    total   = e_val + g_val
    e_frac  = e_val / total
    g_frac  = g_val / total

    # ── Main donut ────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(4.8, 4.2))
    ax.set_aspect('equal')
    ax.axis('off')

    r_out, r_in = 1.0, 0.52

    def _donut_arc(ax, theta_start_deg, theta_end_deg, r_out, r_in, color, alpha):
        """Fill a donut arc between two radii over an angular range."""
        n   = 400
        t   = np.linspace(np.radians(theta_start_deg), np.radians(theta_end_deg), n)
        xo  = r_out * np.cos(t);  yo = r_out * np.sin(t)
        xi  = r_in  * np.cos(t[::-1])
        yi  = r_in  * np.sin(t[::-1])
        xs  = np.concatenate([xo, xi, [xo[0]]])
        ys  = np.concatenate([yo, yi, [yo[0]]])
        ax.fill(xs, ys, color=color, alpha=alpha, zorder=2)
        # white separators at gap edges
        for r in (r_out, r_in):
            ax.plot(r * np.cos(t[[0, -1]]),
                    r * np.sin(t[[0, -1]]),
                    color='white', lw=0)
        ax.plot(np.append(xo, xo[0]), np.append(yo, yo[0]),
                color='white', lw=1.1, zorder=3)
        ax.plot(np.append(xi[::-1], xi[-1]), np.append(yi[::-1], yi[-1]),
                color='white', lw=1.1, zorder=3)

    # EPOR arc: clockwise from 90°  → 90° − e_frac*360°
    start_epor = 90
    end_epor   = 90 - e_frac * 360
    _donut_arc(ax, end_epor, start_epor, r_out, r_in, ERYTHROID_BLUE, alpha=0.88)

    # GCSFR arc: continuing clockwise
    end_gcsfr = end_epor - g_frac * 360   # ≈ 90° − 360° = −270°
    _donut_arc(ax, end_gcsfr, end_epor, r_out, r_in, MYELOID_RED, alpha=0.85)

    # Centre annotation
    ax.text(0,  0.13, f'{ratios[rep_idx]:.1f}×',
            ha='center', va='center', fontsize=22,
            color=ERYTHROID_BLUE, fontweight='bold')
    ax.text(0, -0.17, 'EPOR / GCSFR',
            ha='center', va='center', fontsize=8, color='#555')

    # Arc labels at arc midpoints
    mid_epor_deg  = (start_epor + end_epor)  / 2
    mid_gcsfr_deg = (end_epor   + end_gcsfr) / 2
    r_label = 1.20
    ax.text(r_label * np.cos(np.radians(mid_epor_deg)),
            r_label * np.sin(np.radians(mid_epor_deg)),
            f'EPOR$_{{bound}}$\n{e_frac*100:.0f}%',
            ha='center', va='center', fontsize=8.5,
            color=ERYTHROID_BLUE, fontweight='bold')
    ax.text(r_label * np.cos(np.radians(mid_gcsfr_deg)),
            r_label * np.sin(np.radians(mid_gcsfr_deg)),
            f'GCSFR$_{{bound}}$\n{g_frac*100:.0f}%',
            ha='center', va='center', fontsize=8.5,
            color=MYELOID_RED, fontweight='bold')

    ax.set_xlim(-1.55, 1.55)
    ax.set_ylim(-1.55, 1.55)

    # ── Inset: ratio flatline ─────────────────────────────────────────────────
    # Place inset in lower-right quadrant using figure-level add_axes
    ax_ins = fig.add_axes([0.58, 0.08, 0.36, 0.28])

    ax_ins.fill_between(epo_arr,
                        ratios - epor_s / gcsfr_m,
                        ratios + epor_s / gcsfr_m,
                        color=ERYTHROID_BLUE, alpha=0.15)
    ax_ins.plot(epo_arr, ratios, 'o-', color=ERYTHROID_BLUE,
                lw=1.6, ms=4, mec='white', mew=0.8)
    ax_ins.axhline(4.0, color='#aaa', lw=0.7, ls=':')
    ax_ins.set_ylim(0, ratios.max() * 1.45)
    ax_ins.set_xlabel('EPO$_{ext}$ (mM)', fontsize=6.5)
    ax_ins.set_ylabel('Ratio', fontsize=6.5)
    ax_ins.tick_params(labelsize=6)
    ax_ins.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f'{x:.2f}'))
    for sp in ('top', 'right'):
        ax_ins.spines[sp].set_visible(False)

    _add_title(fig, 'Receptor occupancy hierarchy (EPO\u2009=\u20090.449\u2009mM)')
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Fig 7 – Signal hierarchy preemption cascade
# ═══════════════════════════════════════════════════════════════════════════════
def fig7_preemption_cascade(exps):
    """
    Four-panel cascade showing sequential activation of each signal layer
    in the EPO/GATA1 model (t = 0–400 s, EPO = 0.449 mM):

      λ₀  EPO_external        — cytokine supply (flat forcing)
      λ₁  EPOR_bound          — receptor occupancy (rises with binding)
      λ₂  pGATA1_nuc          — commitment signal (peaks then consumed)
      λ₃  GATA1 / PU.1_nuc   — execution layer (irreversible divergence)

    Downward preemption chevrons on the right link each panel to the next,
    symbolising that λₖ is the enabling condition for λₖ₊₁.
    """
    mean_df, _ = read_mean_and_std(exps[0.449])

    # Species column names in results.csv
    L0_id  = 'EPO_external'
    L1_id  = 'EPOR_bound'
    L2_id  = 'pGATA1_nuc'
    L3a_id = 'GATA1_Protein_nuc'
    L3b_id = 'PU1_Protein_nuc'

    time   = mean_df['Time'].values
    mask   = time <= 400
    t      = time[mask]

    s0  = mean_df[L0_id].values[mask]
    s1  = mean_df[L1_id].values[mask]
    s2  = mean_df[L2_id].values[mask]
    s3a = mean_df[L3a_id].values[mask]
    s3b = mean_df[L3b_id].values[mask]

    # Layer palette
    C0 = '#c05a00'   # burnt orange  – cytokine
    C1 = '#007070'   # teal          – receptor
    C2 = PGATA1_VIOLET
    C3a = ERYTHROID_BLUE
    C3b = ACCENT_RED

    layer_labels = [
        r'$\lambda_0$  cytokine',
        r'$\lambda_1$  receptor',
        r'$\lambda_2$  commitment',
        r'$\lambda_3$  execution',
    ]

    # ── Build figure ─────────────────────────────────────────────────────────
    fig, axes = plt.subplots(4, 1, figsize=(5.2, 6.4),
                             sharex=True,
                             gridspec_kw={'hspace': 0.10})

    def _panel(ax, t, y, color, label, ylabel_unit='mM'):
        ax.fill_between(t, 0, y, color=color, alpha=0.12, lw=0)
        ax.plot(t, y, '-', color=color, lw=2.0)
        ax.set_ylabel(ylabel_unit, fontsize=7.5)
        ax.set_ylim(bottom=0)
        # Layer tag on upper-left
        ax.text(0.02, 0.88, label,
                transform=ax.transAxes,
                fontsize=8.5, va='top', ha='left',
                color=color, fontweight='bold')
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
        ax.tick_params(labelsize=7.5)

    _panel(axes[0], t, s0,  C0,  layer_labels[0])
    _panel(axes[1], t, s1,  C1,  layer_labels[1])
    _panel(axes[2], t, s2,  C2,  layer_labels[2])

    # Layer 3: two species on same axes
    axes[3].fill_between(t, 0, s3a, color=C3a, alpha=0.10, lw=0)
    axes[3].fill_between(t, 0, s3b, color=C3b, alpha=0.10, lw=0)
    axes[3].plot(t, s3a, '-', color=C3a, lw=2.0)
    axes[3].plot(t, s3b, '-', color=C3b, lw=2.0)
    axes[3].set_ylabel('mM', fontsize=7.5)
    axes[3].set_ylim(bottom=0)
    axes[3].text(0.02, 0.88, layer_labels[3],
                 transform=axes[3].transAxes,
                 fontsize=8.5, va='top', ha='left',
                 color='#333', fontweight='bold')
    # Species labels inside panel 3
    t_end   = t[-1]
    axes[3].text(t_end * 0.92, s3a[-1], 'GATA1',
                 color=C3a, fontsize=7.5, va='bottom', ha='right')
    axes[3].text(t_end * 0.92, s3b[-1], 'PU.1',
                 color=C3b, fontsize=7.5, va='top',    ha='right')
    for sp in ('top', 'right'):
        axes[3].spines[sp].set_visible(False)
    axes[3].tick_params(labelsize=7.5)

    axes[3].set_xlabel('Time (s)', fontsize=9)
    axes[3].set_xlim(0, 400)

    # ── Preemption chevrons between panels ───────────────────────────────────
    chevron_colors = [C0, C1, C2]
    for i in range(3):
        ax_upper = axes[i]
        ax_lower = axes[i + 1]
        # Arrow in figure coordinates linking top panel bottom-right
        # to bottom panel top-right
        x_fig = 0.945
        y_top_ax    = ax_upper.get_position().y0
        y_bottom_ax = ax_lower.get_position().y1
        y_mid = (y_top_ax + y_bottom_ax) / 2
        arrow = plt.matplotlib.patches.FancyArrowPatch(
            (x_fig, y_top_ax - 0.005),
            (x_fig, y_bottom_ax + 0.005),
            transform=fig.transFigure,
            arrowstyle='-|>',
            mutation_scale=10,
            color=chevron_colors[i],
            lw=1.4,
            zorder=10,
            clip_on=False,
        )
        fig.patches.append(arrow)
        # "preempts" text beside arrow
        fig.text(x_fig + 0.025, y_mid, 'preempts',
                 fontsize=6.5, va='center', ha='left',
                 color=chevron_colors[i], rotation=-90,
                 transform=fig.transFigure)

    _add_title(fig, 'Signal hierarchy preemption cascade')
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("Loading experiments …")
    exps = find_experiments(BASE)
    print(f"  {len(exps)} conditions: {sorted(exps.keys())}\n")

    print("Fig 1  Waddington landscape …")
    save_fig(fig1_waddington(exps),     'fig1_waddington')

    print("Fig 2  P(erythroid) …")
    save_fig(fig2_p_erythroid(exps),    'fig2_p_erythroid')

    print("Fig 3  Stochastic divergence …")
    save_fig(fig3_divergence(exps),     'fig3_divergence')

    print("Fig 4  Mean trajectory …")
    save_fig(fig4_mean_trajectory(exps), 'fig4_mean_trajectory')

    print("Fig 5  Execution ratchet …")
    save_fig(fig5_ratchet(exps),        'fig5_ratchet')

    print("Fig 6  Receptor hierarchy …")
    save_fig(fig6_receptors(exps),      'fig6_receptors')

    print("Fig 7  Preemption cascade …")
    save_fig(fig7_preemption_cascade(exps), 'fig7_preemption_cascade')

    print(f"\nAll figures saved to  {FIGDIR}/")
