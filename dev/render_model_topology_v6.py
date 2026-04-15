#!/usr/bin/env python3
"""
render_model_topology_v6.py
============================
Render the v6 model topology as a publication-quality PDF figure.

Reads phase3a_spatial_clean_v6.shy (JSON) and renders:
  - Compartment background patches (extracellular, membrane, endosome,
    nucleus, cytoplasm)
  - Places as circles (fill by type; bold ring for signal/energy places)
  - Transitions as rectangles (fill by kinetic type)
  - Arcs as arrows (by arc_type: normal black, test/inhibition blue-cap,
    signal_flow dashed grey)

Output:
    workspace/projects/gata/figures/fig_model_topology_v6.pdf
    workspace/projects/gata/figures/fig_model_topology_v6.png
"""
import json
import sys
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Circle
from matplotlib.collections import PatchCollection
import matplotlib.patheffects as pe

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = os.path.join(os.path.dirname(__file__), '..')
MODEL_PATH = os.path.join(ROOT, 'workspace/projects/gata/models/phase3a_spatial_clean_v6.shy')
OUT_DIR    = os.path.join(ROOT, 'workspace/projects/gata/figures')
OUT_PDF    = os.path.join(OUT_DIR, 'fig_model_topology_v6.pdf')
OUT_PNG    = os.path.join(OUT_DIR, 'fig_model_topology_v6.png')

# ── Load model ────────────────────────────────────────────────────────────────
with open(MODEL_PATH) as f:
    d = json.load(f)

places      = {p['id']: p for p in d['places']}
transitions = {t['id']: t for t in d['transitions']}
arcs        = d['arcs']

# ── Visual parameters ─────────────────────────────────────────────────────────
PLACE_R   = 32   # place circle radius (world units)
T_W, T_H  = 52, 22   # transition box width, height

# Compartment fill colours (RGBA)
COMP_COLORS = {
    'extracellular': '#d0e8f5',   # pale sky blue
    'plasma_membrane': '#fde8c8', # pale orange
    'endosome': '#ffd7b5',        # light salmon
    'nucleus': '#e6d7f0',         # pale lavender
    'cytoplasm': '#d4edda',       # pale green
    '?': '#f5f5f5',               # neutral
}

# Place fill colours by compartment (slightly darker than background)
PLACE_COMP_COLORS = {
    'extracellular': '#90cbe0',
    'plasma_membrane': '#f5c97a',
    'endosome': '#f5a87a',
    'nucleus': '#b39ddb',
    'cytoplasm': '#81c784',
    '?': '#cccccc',
}

# Transition fill by kinetic type
TRANS_COLORS = {
    'continuous': '#5c85d6',
    'adaptive': '#e36f2b',
    'stochastic': '#43a047',
    '?': '#aaaaaa',
}

# Place label shortcuts for display (trim '_' → ' ', remove common suffixes)
def place_label(name: str) -> str:
    n = name.replace('_', '\n')
    return n

def trans_label(name: str) -> str:
    # Just show the core verb to keep boxes readable
    parts = name.split('_')
    if len(parts) >= 2:
        return '_'.join(parts[:3])
    return name

# ── Coordinate helpers ────────────────────────────────────────────────────────
# Matplotlib y increases upward; .shy y increases downward → flip
def mpl_xy(x, y):
    return float(x), -float(y)

# Compute bounding box across all objects
all_x = [p['x'] for p in d['places']] + [t['x'] for t in d['transitions']]
all_y = [-p['y'] for p in d['places']] + [-t['y'] for t in d['transitions']]
xmin, xmax = min(all_x) - 150, max(all_x) + 150
ymin, ymax = min(all_y) - 150, max(all_y) + 150
W = xmax - xmin
H = ymax - ymin

# ── Compartment regions (approximate bounding boxes from place coords) ─────────
# Build approximate compartment hulls from place positions
from collections import defaultdict
comp_places = defaultdict(list)
for p in d['places']:
    comp = p.get('compartment', '?') or '?'
    comp_places[comp].append((p['x'], p['y']))

# ── Figure setup ─────────────────────────────────────────────────────────────
FIG_W = 14   # inches
FIG_H = FIG_W * H / W
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=150)
ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)
ax.set_aspect('equal')
ax.axis('off')
fig.patch.set_facecolor('white')

# ── Draw compartment background patches ─────────────────────────────────────
# Draw compartment bounding boxes with a small margin
MARGIN = 80
for comp, pts in comp_places.items():
    if not pts:
        continue
    cxs = [mx for mx, my in pts]
    cys = [-my for mx, my in pts]    # flipped
    cx0 = min(cxs) - MARGIN
    cy0 = min(cys) - MARGIN
    cw  = max(cxs) - min(cxs) + 2 * MARGIN
    ch  = max(cys) - min(cys) + 2 * MARGIN
    color = COMP_COLORS.get(comp, COMP_COLORS['?'])
    rect = mpatches.FancyBboxPatch(
        (cx0, cy0), cw, ch,
        boxstyle="round,pad=20",
        facecolor=color, edgecolor='#999999',
        linewidth=0.8, linestyle='--', alpha=0.55, zorder=0
    )
    ax.add_patch(rect)
    # Compartment label in upper-left corner
    ax.text(cx0 + 14, cy0 + ch - 14,
            comp.replace('_', ' '),
            fontsize=5.5, color='#555555', va='top', ha='left',
            style='italic', zorder=1)

# ── Build id → (cx, cy) lookup ───────────────────────────────────────────────
place_pos  = {pid: mpl_xy(p['x'], p['y']) for pid, p in places.items()}
trans_pos  = {tid: mpl_xy(t['x'], t['y']) for tid, t in transitions.items()}

# ── Draw arcs first (under nodes) ────────────────────────────────────────────
def get_pos(oid, otype):
    if otype == 'place':
        return place_pos.get(oid)
    return trans_pos.get(oid)

def shrink_to_circle(px, py, tx, ty, r):
    """Return point on circle of radius r centered at (px,py) toward (tx,ty)."""
    dx, dy = tx - px, ty - py
    dist = max(np.hypot(dx, dy), 1e-9)
    return px + r * dx / dist, py + r * dy / dist

def shrink_to_box(tx, ty, bx, by, hw, hh):
    """Return point on box edge of transition centered at (bx,by) toward (tx,ty)."""
    dx, dy = tx - bx, ty - by
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return bx, by
    # clamp to box
    sx = hw / max(abs(dx), 1e-9)
    sy = hh / max(abs(dy), 1e-9)
    s = min(sx, sy)
    return bx + s * dx, by + s * dy

for arc in arcs:
    src_id  = arc['source_id']
    src_type = arc['source_type']
    tgt_id  = arc['target_id']
    tgt_type = arc['target_type']
    atype   = arc.get('arc_type', 'normal')
    cpts    = arc.get('control_points', [])
    color_raw = arc.get('color', [0, 0, 0])
    if isinstance(color_raw, (list, tuple)) and len(color_raw) >= 3:
        arc_color = tuple(float(c) for c in color_raw[:3])
    else:
        arc_color = (0, 0, 0)

    spos = get_pos(src_id, src_type)
    tpos = get_pos(tgt_id, tgt_type)
    if spos is None or tpos is None:
        continue

    sx, sy = spos
    tx, ty = tpos

    # Compute actual start/end points clipped to node boundaries
    if src_type == 'place':
        sx0, sy0 = shrink_to_circle(sx, sy, tx, ty, PLACE_R + 3)
    else:
        sx0, sy0 = shrink_to_box(sx, sy, sx, sy, T_W / 2, T_H / 2)

    if tgt_type == 'place':
        tx0, ty0 = shrink_to_circle(tx, ty, sx, sy, PLACE_R + 3)
    else:
        tx0, ty0 = shrink_to_box(tx, ty, tx, ty, T_W / 2, T_H / 2)

    # Arc style by type
    if atype == 'signal_flow':
        lstyle = 'dashed'
        lw = 0.8
        ac = '#888888'
        arrowhead = dict(arrowstyle='->', color=ac, lw=lw)
    elif atype == 'test':
        lstyle = 'solid'
        lw = 0.9
        ac = '#3333cc'
        arrowhead = dict(arrowstyle='-[', color=ac, lw=lw)
    else:
        lstyle = 'solid'
        lw = 0.9
        ac = '#333333'
        arrowhead = dict(arrowstyle='->', color=ac, lw=lw)

    if cpts:
        # Bezier-like through control points
        pts_x = [sx0] + [mpl_xy(cp[0], cp[1])[0] for cp in cpts] + [tx0]
        pts_y = [sy0] + [mpl_xy(cp[0], cp[1])[1] for cp in cpts] + [ty0]
        ax.plot(pts_x, pts_y, color=ac, lw=lw,
                linestyle=lstyle, zorder=1, alpha=0.7)
        # Arrow tip
        ax.annotate("", xy=(tx0, ty0), xytext=(pts_x[-2], pts_y[-2]),
                    arrowprops=dict(arrowstyle='->', color=ac, lw=lw),
                    zorder=2)
    else:
        ax.annotate("", xy=(tx0, ty0), xytext=(sx0, sy0),
                    arrowprops=dict(arrowstyle='->', color=ac, lw=lw,
                                   linestyle=lstyle),
                    zorder=2)

# ── Draw transitions ──────────────────────────────────────────────────────────
for tid, t in transitions.items():
    cx, cy = trans_pos[tid]
    ttype = t.get('transition_type', '?') or '?'
    fc = TRANS_COLORS.get(ttype, TRANS_COLORS['?'])

    is_horiz = t.get('horizontal', False)
    if is_horiz:
        bw, bh = T_H, T_W
    else:
        bw, bh = T_W, T_H

    rect = mpatches.FancyBboxPatch(
        (cx - bw / 2, cy - bh / 2), bw, bh,
        boxstyle="square,pad=0",
        facecolor=fc, edgecolor='#222222',
        linewidth=0.8, zorder=3
    )
    ax.add_patch(rect)

    # Label — very small, centered
    short_name = t['name'].replace('_', '\n')
    # Use abbreviated label: first word + last word
    parts = t['name'].split('_')
    if len(parts) > 3:
        short = parts[0][:4] + '..' + parts[-1][:4]
    else:
        short = '\n'.join(parts)
    ax.text(cx, cy, short,
            ha='center', va='center',
            fontsize=3.5, color='white', fontweight='bold',
            zorder=4, wrap=True)

# ── Draw places ───────────────────────────────────────────────────────────────
for pid, p in places.items():
    cx, cy = place_pos[pid]
    comp   = p.get('compartment', '?') or '?'
    is_sig = p.get('is_signal_place', False)
    is_en  = p.get('is_energy_place', False)

    fc = PLACE_COMP_COLORS.get(comp, '#cccccc')
    if is_en:
        fc = '#ffe082'   # amber for energy pools
    elif is_sig and not is_en:
        fc = '#ffcc80'   # orange for signal

    ec = '#222222'
    lw = 1.2
    if is_sig or is_en:
        lw = 2.0
        ec = '#555500' if is_en else '#aa3300'

    circle = Circle((cx, cy), PLACE_R, facecolor=fc, edgecolor=ec,
                    linewidth=lw, zorder=3)
    ax.add_patch(circle)

    # Shortened label
    name = p['name']
    parts = name.split('_')
    # Strategy: keep compartment suffix as subscript hint
    if len(parts) > 3:
        short = '\n'.join([parts[0], parts[1], '_'.join(parts[2:])])
    elif len(parts) == 3:
        short = parts[0] + '\n' + parts[1] + '\n' + parts[2]
    else:
        short = '\n'.join(parts)
    ax.text(cx, cy, short,
            ha='center', va='center',
            fontsize=3.8, color='#111111', zorder=4,
            fontweight='semibold' if is_sig else 'normal')

# ── Legend ────────────────────────────────────────────────────────────────────
legend_elements = [
    mpatches.Patch(facecolor=PLACE_COMP_COLORS['extracellular'],  edgecolor='#333', label='Extracellular'),
    mpatches.Patch(facecolor=PLACE_COMP_COLORS['plasma_membrane'],edgecolor='#333', label='Plasma membrane'),
    mpatches.Patch(facecolor=PLACE_COMP_COLORS['endosome'],       edgecolor='#333', label='Endosome'),
    mpatches.Patch(facecolor=PLACE_COMP_COLORS['nucleus'],        edgecolor='#333', label='Nucleus'),
    mpatches.Patch(facecolor=PLACE_COMP_COLORS['cytoplasm'],      edgecolor='#333', label='Cytoplasm'),
    mpatches.Patch(facecolor='#ffe082', edgecolor='#aa7700', lw=1.8, label='Energy pool (signal)'),
    mpatches.Patch(facecolor='#ffcc80', edgecolor='#aa3300', lw=1.8, label='Signal place'),
    mpatches.Patch(facecolor=TRANS_COLORS['continuous'],  edgecolor='#222', label='Continuous transition'),
    mpatches.Patch(facecolor=TRANS_COLORS['adaptive'],    edgecolor='#222', label='Adaptive transition'),
    plt.Line2D([0], [0], color='#333333', lw=0.9, label='Normal arc'),
    plt.Line2D([0], [0], color='#3333cc', lw=0.9, label='Test (read) arc'),
    plt.Line2D([0], [0], color='#888888', lw=0.8, linestyle='--', label='Signal-flow arc'),
]
ax.legend(handles=legend_elements, loc='lower right',
          fontsize=5.5, framealpha=0.85, ncol=2,
          title='Legend', title_fontsize=6,
          borderpad=0.6, labelspacing=0.3, handlelength=1.5)

ax.set_title(
    'GATA1/PU.1 fate-switch model topology (Signal Hierarchical Petri Net, v6)',
    fontsize=8, pad=8, fontweight='bold'
)

plt.tight_layout(pad=0.3)

# ── Save ──────────────────────────────────────────────────────────────────────
os.makedirs(OUT_DIR, exist_ok=True)
fig.savefig(OUT_PDF, format='pdf', dpi=300, bbox_inches='tight')
fig.savefig(OUT_PNG, format='png', dpi=300, bbox_inches='tight')
print(f"Saved:\n  {OUT_PDF}\n  {OUT_PNG}")
plt.close(fig)
