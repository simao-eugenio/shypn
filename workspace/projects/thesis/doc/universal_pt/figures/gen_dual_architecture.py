#!/usr/bin/env python3
"""
gen_dual_architecture.py
Two-panel figure bridging the Waddington metaphor (slide "O Problema")
to the SHPN formal dual-architecture (slide "A Dupla Arquitetura").

Left  : static double-well  U(φ)  — two attractors, commitment saddle θ_eff
Right : G_E ⊥ G_s schematic — substrate flow (bottom band) + signal DAG
        (top band) + Ψ bridge node aligned in both layers
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, RegularPolygon, FancyBboxPatch
from matplotlib.lines import Line2D
from pathlib import Path

# ── palette ────────────────────────────────────────────────────────────────
BG      = '#FAFAFA'
DARK    = '#1A1A2E'
GRAY    = '#6B7280'
SIGNAL  = '#DBEAFE'     # light-blue hexagons (Ψ signal places)
TRANS   = '#374151'     # dark rectangles (transitions)
ACCENT  = '#2563EB'     # inter-panel arrow
C_L     = '#3B82F6'     # left well  / B_pre
C_R     = '#059669'     # right well / B_pos
C_S     = '#DC2626'     # saddle / θ_eff
C_BRDG  = '#BFDBFE'     # bridge-node fill (ψ_0 shared by both graphs)

# ── double-well ─────────────────────────────────────────────────────────────
phi  = np.linspace(-1.55, 1.55, 500)
asym = 0.25
U    = (phi**2 - 1)**2 + asym * phi

i_mid = 250
phi_L = phi[:i_mid][np.argmin(U[:i_mid])]
phi_R = phi[i_mid:][np.argmin(U[i_mid:])]
U_L   = (phi_L**2 - 1)**2 + asym * phi_L
U_R   = (phi_R**2 - 1)**2 + asym * phi_R

window = (phi > -0.35) & (phi < 0.35)
phi_S  = phi[window][np.argmax(U[window])]
U_S    = (phi_S**2 - 1)**2 + asym * phi_S

# ── figure layout ────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(13, 5.2), facecolor=BG)
gs  = fig.add_gridspec(1, 3, width_ratios=[1, 0.10, 1.15],
                        left=0.05, right=0.97, top=0.90, bottom=0.13,
                        wspace=0.0)
ax_L = fig.add_subplot(gs[0])
ax_M = fig.add_subplot(gs[1])
ax_R = fig.add_subplot(gs[2])

# ═══════════════════════ LEFT PANEL ═════════════════════════════════════════
ax_L.set_facecolor(BG)
ax_L.plot(phi, U, color=DARK, lw=2.2, zorder=3)

mask_l = phi < phi_S
mask_r = phi > phi_S
ax_L.fill_between(phi[mask_l], U[mask_l], 1.30, color=C_L, alpha=0.13, zorder=1)
ax_L.fill_between(phi[mask_r], U[mask_r], 1.30, color=C_R, alpha=0.13, zorder=1)

ax_L.scatter([phi_L], [U_L], s=70, color=C_L, zorder=5, ec=DARK, lw=1.0)
ax_L.scatter([phi_R], [U_R], s=70, color=C_R, zorder=5, ec=DARK, lw=1.0)
ax_L.scatter([phi_S], [U_S], s=90, color=C_S, zorder=6, ec=DARK, lw=1.0, marker='^')

# cell ball (about to commit)
phi_ball = phi_L + 0.28
U_ball   = (phi_ball**2 - 1)**2 + asym * phi_ball
ax_L.add_patch(Circle((phi_ball, U_ball + 0.10), 0.07,
                       fc='#FCD34D', ec=DARK, lw=1.5, zorder=8))

ax_L.text(phi_L + 0.22, U_L + 0.06,
          r'$\mathcal{B}_\mathrm{pre}$' + '\nvegetativo',
          ha='left', va='center', fontsize=9, color=C_L, fontweight='bold',
          bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor='none', alpha=0.70))
ax_L.text(phi_R, U_R - 0.14,
          r'$\mathcal{B}_\mathrm{pos}$' + '\nesporo',
          ha='center', va='top', fontsize=9, color=C_R, fontweight='bold')
ax_L.text(phi_S, U_S + 0.14,
          r'$\theta_{\mathrm{eff}}$',
          ha='center', va='bottom', fontsize=9.5, color=C_S, fontweight='bold')

ax_L.set_xlim(-1.65, 1.65)
ax_L.set_ylim(-0.45, 1.35)
ax_L.set_xlabel(r'$\varphi$  (parâmetro de ordem da esporulação)', fontsize=10, color=DARK)
ax_L.set_ylabel(r'$U(\varphi)$  (potencial epigenético)', fontsize=10, color=DARK)
ax_L.set_title('A metáfora: paisagem de Waddington',
               fontsize=11, color=DARK, fontweight='bold', pad=6)
ax_L.tick_params(labelsize=8, colors=GRAY)
ax_L.spines[['top', 'right']].set_visible(False)
ax_L.spines[['left', 'bottom']].set_color(GRAY)

# ═══════════════════════ MIDDLE ARROW ═══════════════════════════════════════
ax_M.set_facecolor(BG)
ax_M.axis('off')
ax_M.annotate('', xy=(0.88, 0.50), xytext=(0.12, 0.50),
              xycoords='axes fraction', textcoords='axes fraction',
              arrowprops=dict(arrowstyle='->', color=ACCENT, lw=3.5,
                              mutation_scale=20))
ax_M.text(0.50, 0.64, 'SHPN', ha='center', va='bottom', fontsize=9,
          color=ACCENT, fontweight='bold', transform=ax_M.transAxes)
ax_M.text(0.50, 0.35, 'torna\ncomputável', ha='center', va='top',
          fontsize=7.5, color=ACCENT, transform=ax_M.transAxes,
          linespacing=1.3)

# ═══════════════════════ RIGHT PANEL ════════════════════════════════════════
ax_R.set_facecolor(BG)
ax_R.set_xlim(0, 10)
ax_R.set_ylim(0, 8.8)
ax_R.axis('off')
ax_R.set_title(r'O mecanismo: $G_E \perp G_s$',
               fontsize=11, color=DARK, fontweight='bold', pad=6)

# ── drawing helpers ──────────────────────────────────────────────────────────
def circ(ax, x, y, r=0.40, fc='white', ec=DARK, lw=1.6, z=4):
    ax.add_patch(Circle((x, y), r, fc=fc, ec=ec, lw=lw, zorder=z))

def hexa(ax, x, y, r=0.44, fc=SIGNAL, ec='#1D4ED8', lw=1.8, z=4):
    ax.add_patch(RegularPolygon((x, y), 6, radius=r, orientation=np.pi/6,
                                fc=fc, ec=ec, lw=lw, zorder=z))

def rect(ax, x, y, w=0.52, h=0.52, fc=TRANS, ec=DARK, lw=1.5, z=4):
    ax.add_patch(FancyBboxPatch((x - w/2, y - h/2), w, h,
                                boxstyle='square,pad=0',
                                fc=fc, ec=ec, lw=lw, zorder=z))

def arr(ax, x1, y1, x2, y2, color=DARK, lw=1.5, ls='-', rad=0.0):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                linestyle=ls,
                                connectionstyle=f'arc3,rad={rad}'))

def signal_arr(ax, x1, y1, x2, y2, color='#9CA3AF', lw=1.8, rad=0.0):
    # Double-stroke arrowhead to visually distinguish signal arcs.
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                linestyle='--',
                                connectionstyle=f'arc3,rad={rad}'))
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                linestyle='--',
                                mutation_scale=7,
                                connectionstyle=f'arc3,rad={rad}'))

# ── band backgrounds ─────────────────────────────────────────────────────────
ax_R.axhspan(5.30, 8.80, color='#EFF6FF', alpha=0.55, zorder=0)   # G_s band
ax_R.axhspan(0.00, 5.30, color='#ECFDF5', alpha=0.40, zorder=0)   # G_E band

# band labels
ax_R.text(0.25, 8.45, r'$G_s$ — grafo de sinal  (decisório)',
          fontsize=9.5, color='#1D4ED8', fontweight='bold', va='center')
ax_R.text(0.25, 5.00, r'$G_E$ — grafo de substrato  (execução)',
          fontsize=9.5, color='#065F46', fontweight='bold', va='center')

# ── G_s nodes  (ψ_0 at x=5.0 to align with bridge; ψ_1 at x=8.0) ────────────
Y_S = 7.2
hexa(ax_R, 5.0, Y_S)    # ψ_0  λ=0  (bridge — also in G_E)
hexa(ax_R, 8.0, Y_S)    # ψ_1  λ=1

ax_R.text(5.0, Y_S,  r'$\psi_0$', ha='center', va='center',
          fontsize=9, color=DARK, zorder=5)
ax_R.text(8.0, Y_S,  r'$\psi_1$', ha='center', va='center',
          fontsize=9, color=DARK, zorder=5)
ax_R.text(5.0, Y_S + 0.62, r'$\lambda=0$', ha='center',
          fontsize=7.5, color=GRAY)
ax_R.text(8.0, Y_S + 0.62, r'$\lambda=1$', ha='center',
          fontsize=7.5, color=GRAY)

# F_s arc ψ_0 → ψ_1 (horizontal, dashed, light-gray, double arrowhead)
signal_arr(ax_R, 5.44, Y_S, 7.56, Y_S)
ax_R.text(6.50, Y_S + 0.28, r'$F_s$', ha='center', fontsize=8, color='#6B7280')

# F_s arc ψ_1 → t_commit (down, dashed, light-gray, double arrowhead)
signal_arr(ax_R, 8.0, Y_S - 0.44, 7.0, 3.78, rad=0.25)
ax_R.text(8.35, 5.55, r'$F_s$, $\theta_{\mathrm{eff}}$',
          ha='center', fontsize=8, color='#6B7280')

# ── G_E nodes  ───────────────────────────────────────────────────────────────
Y_E = 3.5
circ(ax_R, 1.5, Y_E)          # p_1  (substrate place)
rect(ax_R, 3.5, Y_E)          # t_1  (upstream transition)
hexa(ax_R, 5.0, Y_E, fc=C_BRDG, ec='#1D4ED8', lw=2.0)  # ψ_0 bridge node
rect(ax_R, 7.0, Y_E)          # t_commit

ax_R.text(1.5, Y_E,  r'$p_1$',   ha='center', va='center',
          fontsize=9, color=DARK, zorder=5)
ax_R.text(3.5, Y_E,  r'$t_1$',   ha='center', va='center',
          fontsize=9, color='white', zorder=5)
ax_R.text(5.0, Y_E,  r'$\psi_0$', ha='center', va='center',
          fontsize=9, color='#1D4ED8', fontweight='bold', zorder=5)
ax_R.text(7.0, Y_E,  r'$t_c$',   ha='center', va='center',
          fontsize=9, color='white', zorder=5)

# F arcs in G_E
arr(ax_R, 1.90, Y_E, 3.24, Y_E, color=DARK, lw=1.5)
arr(ax_R, 3.76, Y_E, 4.56, Y_E, color=DARK, lw=1.5)
arr(ax_R, 5.44, Y_E, 6.74, Y_E, color=DARK, lw=1.5)
ax_R.text(2.57, Y_E + 0.28, r'$F$', ha='center', fontsize=8, color=DARK)
ax_R.text(4.16, Y_E + 0.28, r'$F$', ha='center', fontsize=8, color=DARK)
ax_R.text(6.09, Y_E + 0.28, r'$F$', ha='center', fontsize=8, color=DARK)

# ── Bridge: vertical dotted line  ψ_0 (G_s, y=7.2) ↔ ψ_0 (G_E, y=3.5) ──────
ax_R.plot([5.0, 5.0], [Y_S - 0.44, Y_E + 0.44],
          linestyle=':', color='#1D4ED8', lw=2.0, zorder=2)
ax_R.text(5.42, 5.35, r'$\Psi$  (ponte)', fontsize=9, color='#1D4ED8',
          style='italic', ha='left', va='center')

# ── legend ───────────────────────────────────────────────────────────────────
LY = 1.6
circ(ax_R, 0.55, LY, r=0.26, fc='white')
ax_R.text(0.90, LY, 'lugar substrato', va='center', fontsize=7.5, color=DARK)

hexa(ax_R, 3.30, LY, r=0.28, fc=SIGNAL)
ax_R.text(3.70, LY, r'lugar sinal $\Psi$', va='center', fontsize=7.5, color=DARK)

rect(ax_R, 6.40, LY, w=0.38, h=0.38, fc=TRANS)
ax_R.text(6.72, LY, 'transição', va='center', fontsize=7.5, color=DARK)

ax_R.annotate('', xy=(9.10, LY), xytext=(8.30, LY),
              arrowprops=dict(arrowstyle='->', color=DARK, lw=1.4))
ax_R.text(9.25, LY, r'$F$', va='center', fontsize=7.5, color=DARK)

ax_R.plot([0.30, 0.82], [0.75, 0.75], '--', color='#9CA3AF', lw=1.8)
ax_R.add_line(Line2D([0.70, 0.82], [0.79, 0.75], color='#9CA3AF', lw=1.8))
ax_R.add_line(Line2D([0.70, 0.82], [0.71, 0.75], color='#9CA3AF', lw=1.8))
ax_R.text(0.97, 0.75, r'arco $F_s$', va='center', fontsize=7.5, color=DARK)

ax_R.plot([3.05, 3.57], [0.75, 0.75], ':', color='#1D4ED8', lw=2.0)
ax_R.text(3.72, 0.75, r'ponte $\Psi$', va='center', fontsize=7.5, color='#1D4ED8')

# ── save ─────────────────────────────────────────────────────────────────────
out_dir = Path(__file__).resolve().parent
for name in ('fig_dual_architecture.pdf', 'fig_dual_architecture.png'):
    path = out_dir / name
    dpi  = 300 if name.endswith('.pdf') else 200
    plt.savefig(str(path), dpi=dpi, bbox_inches='tight', facecolor=BG)
    print(f'✓ {path.name}')
plt.close()
