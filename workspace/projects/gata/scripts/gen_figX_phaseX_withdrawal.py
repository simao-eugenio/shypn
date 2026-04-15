"""
gen_figX_phaseX_withdrawal.py
==============================
Generate Phase X cytokine-withdrawal figure for the GATA1/PU.1 manuscript.

Data: workspace/projects/gata/data/EPO=1-500s-EPO=0.csv
  Single mean trajectory: EPO=1.0 mM for 0–500s, then EPO=0 (environment event).
  Total duration: 3600 s.

Figure shows:
  – GATA1_Protein_nuc (mM) over 0–3600 s  [blue]
  – PU1_Protein_nuc (mM)  over 0–3600 s  [red]
  – Vertical dashed line at t=500s (EPO withdrawal)
  – Annotated events: priming crossover (~490s), full reversal (~2000s)
"""

import warnings
warnings.filterwarnings('ignore')

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_FILE = "/home/simao/projetos/shypn/workspace/projects/gata/data/EPO=1-500s-EPO=0.csv"
FIGDIR    = "/home/simao/projetos/shypn/workspace/projects/gata/figures"
os.makedirs(FIGDIR, exist_ok=True)

# ── Style (matches generate_figures.py) ───────────────────────────────────────
ERYTHROID_BLUE = '#1a3a6b'
MYELOID_RED    = '#8b0000'

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
    'lines.linewidth':    1.8,
})

# ── Load data ─────────────────────────────────────────────────────────────────
df = pd.read_csv(DATA_FILE)
# Normalise column names (strip surrounding spaces)
df.columns = [c.strip() for c in df.columns]

t      = df['Time (s)'].values
gata1  = df['GATA1_Protein_nuc (mM)'].values
pu1    = df['PU1_Protein_nuc (mM)'].values

# ── Figure ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(5.5, 3.5))

ax.plot(t, gata1, color=ERYTHROID_BLUE, label='GATA1$_\\mathrm{nuc}$', lw=1.8)
ax.plot(t, pu1,   color=MYELOID_RED,    label='PU.1$_\\mathrm{nuc}$',  lw=1.8)

# EPO withdrawal line
ax.axvline(500, color='#555555', lw=1.2, ls='--', zorder=5)
ax.text(510, ax.get_ylim()[1] * 0.97 if ax.get_ylim()[1] > 0 else 11,
        'EPO\nwithdrawn\n$t=500$~s',
        fontsize=7.5, va='top', ha='left', color='#555555')

# Shade withdrawal period
ax.axvspan(500, 3600, color='#eeeeee', alpha=0.45, zorder=0)

# Annotate reversal
# Find approximate time of GATA1/PU1 crossover after 500s (reversal)
post_mask = t > 500
cross_idx = np.where(pu1[post_mask] > gata1[post_mask])[0]
if len(cross_idx) > 0:
    t_cross = t[post_mask][cross_idx[0]]
    ax.axvline(t_cross, color='#777777', lw=0.9, ls=':', zorder=4)
    ax.text(t_cross + 30, 5.5, f'Fate reversal\n$t\\approx{int(t_cross)}$~s',
            fontsize=7, va='top', ha='left', color='#555555')

ax.set_xlabel('Time (s)')
ax.set_ylabel('Concentration (mM)')
ax.set_xlim(0, 3600)
ax.set_ylim(bottom=0)
ax.legend(loc='upper right', fontsize=8, frameon=False)

# ─ y-axis auto-range fix after text annotations ─
ymax = max(gata1.max(), pu1.max()) * 1.12
ax.set_ylim(0, ymax)

# Re-place withdrawal text with correct ymax
for txt in ax.texts:
    if 'EPO' in txt.get_text():
        txt.set_y(ymax * 0.97)
        break

ax.set_title('Phase X: EPO withdrawal reverses erythroid commitment', fontsize=10, pad=6)

plt.tight_layout()

# ── Save ─────────────────────────────────────────────────────────────────────
for ext in ('pdf', 'png'):
    fig.savefig(os.path.join(FIGDIR, f'fig10_phaseX_withdrawal.{ext}'),
                bbox_inches='tight', dpi=300)
plt.close(fig)
print("✓  fig10_phaseX_withdrawal.pdf  +  .png")
