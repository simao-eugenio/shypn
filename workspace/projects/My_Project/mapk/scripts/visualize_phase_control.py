#!/usr/bin/env python3
"""
Visualize the Phase Control Architecture for Excitability Model
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

fig, ax = plt.subplots(1, 1, figsize=(12, 10))
ax.set_xlim(0, 10)
ax.set_ylim(0, 12)
ax.axis('off')

# Title
ax.text(5, 11.5, 'Excitability Model: Explicit Phase Control Architecture', 
        ha='center', va='top', fontsize=16, fontweight='bold')

# ============================================================================
# Phase State Machine (Left Side)
# ============================================================================

# Phase places
phases = [
    {'name': 'Phase_Rest', 'pos': (2, 9), 'color': '#33aa33', 'marking': '1'},
    {'name': 'Phase_Pulse', 'pos': (2, 6), 'color': '#cc3333', 'marking': '0'},
    {'name': 'Phase_Recovery', 'pos': (2, 3), 'color': '#3333cc', 'marking': '0'}
]

for phase in phases:
    # Circle for place
    circle = plt.Circle(phase['pos'], 0.4, color=phase['color'], 
                       ec='black', lw=2, alpha=0.7)
    ax.add_patch(circle)
    
    # Place name
    ax.text(phase['pos'][0], phase['pos'][1], phase['marking'],
           ha='center', va='center', fontsize=20, fontweight='bold', color='white')
    ax.text(phase['pos'][0], phase['pos'][1] - 0.7, phase['name'].replace('_', '\n'),
           ha='center', va='top', fontsize=10, fontweight='bold')

# Timed transitions
transitions = [
    {'name': 'Start_Pulse', 'pos': (2, 7.5), 'delay': '10s', 
     'from': (2, 8.6), 'to': (2, 6.4)},
    {'name': 'End_Pulse', 'pos': (2, 4.5), 'delay': '20s',
     'from': (2, 5.6), 'to': (2, 3.4)},
    {'name': 'Reset', 'pos': (0.5, 6), 'delay': '30s',
     'from': (1.7, 3.3), 'to': (1.7, 8.7)}
]

for trans in transitions:
    # Rectangle for transition
    rect = FancyBboxPatch((trans['pos'][0] - 0.35, trans['pos'][1] - 0.15),
                          0.7, 0.3, boxstyle="round,pad=0.05",
                          ec='#cc6600', fc='#ff9933', lw=2)
    ax.add_patch(rect)
    
    # Transition label
    label = f"{trans['name']}\n[delay={trans['delay']}]"
    ax.text(trans['pos'][0] + 0.8, trans['pos'][1], label,
           ha='left', va='center', fontsize=9, style='italic')
    
    # Arrows
    arrow = FancyArrowPatch(trans['from'], trans['to'],
                          arrowstyle='->', lw=2, color='black',
                          mutation_scale=20)
    ax.add_patch(arrow)

# ============================================================================
# GF Control (Middle)
# ============================================================================

# GF place
gf_pos = (5, 6)
circle = plt.Circle(gf_pos, 0.4, color='#0066cc', ec='black', lw=2, alpha=0.7)
ax.add_patch(circle)
ax.text(gf_pos[0], gf_pos[1], 'GF',
       ha='center', va='center', fontsize=14, fontweight='bold', color='white')
ax.text(gf_pos[0], gf_pos[1] - 0.7, 'Growth\nFactor',
       ha='center', va='top', fontsize=10, fontweight='bold')

# GF_Pulse transition (T12)
gf_trans_pos = (3.5, 6)
rect = FancyBboxPatch((gf_trans_pos[0] - 0.15, gf_trans_pos[1] - 0.35),
                      0.3, 0.7, boxstyle="round,pad=0.05",
                      ec='black', fc='black', lw=2)
ax.add_patch(rect)
ax.text(gf_trans_pos[0], gf_trans_pos[1] - 0.8, 'T12:\nGF_Pulse\n(gated)',
       ha='center', va='top', fontsize=9, fontweight='bold')

# Control arc (Phase_Pulse -> GF_Pulse)
control_arrow = FancyArrowPatch((2.4, 6), (3.3, 6),
                               arrowstyle='->', lw=3, color='#cc3333',
                               linestyle='--', mutation_scale=20)
ax.add_patch(control_arrow)
ax.text(2.85, 6.3, 'ENABLE', ha='center', va='bottom',
       fontsize=8, fontweight='bold', color='#cc3333')

# Output arc (GF_Pulse -> GF)
output_arrow = FancyArrowPatch((3.65, 6), (4.6, 6),
                              arrowstyle='->', lw=2, color='black',
                              mutation_scale=20)
ax.add_patch(output_arrow)
ax.text(4.1, 6.2, '100 nM/s', ha='center', va='bottom',
       fontsize=8, style='italic')

# ============================================================================
# MAPK Cascade (Right Side)
# ============================================================================

# Cascade components
cascade_y = 9
cascade_components = ['Raf', 'MEK', 'ERK']
cascade_x = [7, 7, 7]

for i, (name, x) in enumerate(zip(cascade_components, cascade_x)):
    y = cascade_y - i * 2
    circle = plt.Circle((x, y), 0.35, color='#666666', 
                       ec='black', lw=2, alpha=0.5)
    ax.add_patch(circle)
    ax.text(x, y, name, ha='center', va='center',
           fontsize=11, fontweight='bold', color='white')
    
    # Arrows between components
    if i < len(cascade_components) - 1:
        arrow = FancyArrowPatch((x, y - 0.4), (x, y - 1.6),
                              arrowstyle='->', lw=2, color='black',
                              mutation_scale=15)
        ax.add_patch(arrow)

# GF input to cascade
gf_to_raf = FancyArrowPatch((5.4, 6), (6.6, 8.8),
                           arrowstyle='->', lw=2, color='#0066cc',
                           linestyle='--', mutation_scale=15)
ax.add_patch(gf_to_raf)

# Feedback loops
# MKP (negative feedback)
mkp_pos = (8.5, 5)
circle = plt.Circle(mkp_pos, 0.3, color='#cc3333', 
                   ec='black', lw=2, alpha=0.7)
ax.add_patch(circle)
ax.text(mkp_pos[0], mkp_pos[1], 'MKP', ha='center', va='center',
       fontsize=9, fontweight='bold', color='white')

# ERK -> MKP (induction)
erk_to_mkp = FancyArrowPatch((7.3, 5.1), (8.2, 5.1),
                            arrowstyle='->', lw=1.5, color='#cc3333',
                            linestyle=':', mutation_scale=12)
ax.add_patch(erk_to_mkp)
ax.text(7.75, 5.3, 'induce', ha='center', va='bottom',
       fontsize=7, style='italic', color='#cc3333')

# MKP -> ERK (inhibition)
mkp_to_erk = FancyArrowPatch((8.3, 5.3), (7.3, 4.9),
                            arrowstyle='->', lw=1.5, color='#cc3333',
                            mutation_scale=12)
ax.add_patch(mkp_to_erk)
ax.text(7.8, 4.7, 'deactivate', ha='center', va='top',
       fontsize=7, style='italic', color='#cc3333')

# PP2A (weak positive feedback)
pp2a_pos = (8.5, 9)
circle = plt.Circle(pp2a_pos, 0.3, color='#33aa33',
                   ec='black', lw=2, alpha=0.5)
ax.add_patch(circle)
ax.text(pp2a_pos[0], pp2a_pos[1], 'PP2A', ha='center', va='center',
       fontsize=8, fontweight='bold', color='white')

# ============================================================================
# Timeline (Bottom)
# ============================================================================

timeline_y = 1
ax.plot([1, 9], [timeline_y, timeline_y], 'k-', lw=2)

# Time markers
time_points = [
    (1, '0s', 'Rest'),
    (3, '10s', 'Start'),
    (5, '30s', 'End'),
    (7, '60s', 'Reset'),
    (9, '→', '')
]

for x, time, label in time_points:
    ax.plot([x, x], [timeline_y - 0.1, timeline_y + 0.1], 'k-', lw=2)
    ax.text(x, timeline_y - 0.3, time, ha='center', va='top',
           fontsize=9, fontweight='bold')
    if label:
        ax.text(x, timeline_y + 0.3, label, ha='center', va='bottom',
               fontsize=8, style='italic')

# Phase regions
regions = [
    (1, 3, '#33aa33', 'REST'),
    (3, 5, '#cc3333', 'PULSE'),
    (5, 7, '#3333cc', 'RECOVERY'),
]

for x1, x2, color, phase in regions:
    rect = mpatches.Rectangle((x1, timeline_y - 0.05), x2 - x1, 0.1,
                             fc=color, ec='none', alpha=0.3)
    ax.add_patch(rect)
    ax.text((x1 + x2) / 2, timeline_y + 0.7, phase,
           ha='center', va='bottom', fontsize=10,
           fontweight='bold', color=color)

# ============================================================================
# Legend
# ============================================================================

legend_y = 0.2
legend_elements = [
    ('Place (discrete)', '#33aa33', 'circle'),
    ('Transition (timed)', '#ff9933', 'rect'),
    ('Arc (normal)', 'black', 'arrow'),
    ('Arc (signal/control)', '#cc3333', 'dashed_arrow'),
]

for i, (label, color, shape) in enumerate(legend_elements):
    x = 1 + i * 2.5
    if shape == 'circle':
        circle = plt.Circle((x, legend_y), 0.15, color=color, 
                          ec='black', lw=1)
        ax.add_patch(circle)
    elif shape == 'rect':
        rect = mpatches.Rectangle((x - 0.15, legend_y - 0.1), 0.3, 0.2,
                                 fc=color, ec='black', lw=1)
        ax.add_patch(rect)
    elif shape == 'arrow':
        ax.arrow(x - 0.2, legend_y, 0.4, 0, head_width=0.08,
                head_length=0.1, fc=color, ec=color, lw=1.5)
    elif shape == 'dashed_arrow':
        ax.arrow(x - 0.2, legend_y, 0.4, 0, head_width=0.08,
                head_length=0.1, fc=color, ec=color, lw=1.5,
                linestyle='--')
    
    ax.text(x + 0.4, legend_y, label, ha='left', va='center',
           fontsize=8)

# ============================================================================
# Annotations
# ============================================================================

# Annotation box
annotation = """
KEY PRINCIPLE:
• Temporal control via EXPLICIT state machine
• No hidden time-dependent formulas
• Pulse timing visible in Petri net structure
• Timed transitions guarantee precise firing
"""

ax.text(5, 0.7, annotation, ha='center', va='top',
       fontsize=9, family='monospace',
       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('../figures/phase_control_architecture.png', dpi=150, bbox_inches='tight')
plt.savefig('../figures/phase_control_architecture.pdf', bbox_inches='tight')
print("✓ Saved phase_control_architecture.png/pdf")

plt.show()
