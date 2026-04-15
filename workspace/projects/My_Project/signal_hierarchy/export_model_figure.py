#!/usr/bin/env python3
"""Export Lambda hierarchical v3 model as PDF figure for publication.

Renders the actual Petri net model structure from the .shy file, showing:
- Places (circles) at their actual positions
- Transitions (rectangles) at their actual positions
- Arcs (arrows) with actual connections
- Color coding by hierarchical layer
"""
import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch, Arc
from pathlib import Path
import numpy as np

# Place colors by layer
PLACE_COLORS = {
    'Environmental': '#66B3FF',  # Light blue
    'RecA': '#FF9933',           # Orange
    'CII': '#CC99FF',            # Purple
    'CI/Cro': '#FF6666',         # Red
    'Other': '#CCCCCC'           # Gray
}

def load_model(filepath):
    """Load .shy model file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def classify_place(place_name):
    """Classify place by hierarchical role."""
    if any(x in place_name for x in ['ATP', 'Energy', 'Metabolic', 'Health', 'Cycle', 'Cell_Cycle']):
        return 'Environmental'
    elif 'RecA' in place_name:
        return 'RecA'
    elif 'CII' in place_name:
        return 'CII'
    elif any(x in place_name for x in ['CI', 'Cro']) and 'CII' not in place_name:
        return 'CI/Cro'
    else:
        return 'Other'

def export_model_figure(model_path, output_path, figsize=(14, 10), dpi=300):
    """Export actual model structure as PDF."""
    
    # Load model
    model = load_model(model_path)
    places = {p['id']: p for p in model.get('places', [])}
    transitions = {t['id']: t for t in model.get('transitions', [])}
    arcs = model.get('arcs', [])
    
    # Get coordinate bounds for scaling
    x_coords = [p['x'] for p in places.values()] + [t['x'] for t in transitions.values()]
    y_coords = [p['y'] for p in places.values()] + [t['y'] for t in transitions.values()]
    
    x_min, x_max = min(x_coords) - 100, max(x_coords) + 100
    y_min, y_max = min(y_coords) - 100, max(y_coords) + 100
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.invert_yaxis()  # Canvas has Y increasing downward
    
    # Draw arcs first (so they're behind nodes)
    for arc in arcs:
        src_id = arc.get('source')
        tgt_id = arc.get('target')
        arc_type = arc.get('arcType', 'normal')
        
        # Get source and target positions
        src_pos = None
        tgt_pos = None
        
        if src_id in places:
            src_pos = (places[src_id]['x'], places[src_id]['y'])
        elif src_id in transitions:
            src_pos = (transitions[src_id]['x'], transitions[src_id]['y'])
        
        if tgt_id in places:
            tgt_pos = (places[tgt_id]['x'], places[tgt_id]['y'])
        elif tgt_id in transitions:
            tgt_pos = (transitions[tgt_id]['x'], transitions[tgt_id]['y'])
        
        if src_pos and tgt_pos:
            # Arc styling
            if arc_type == 'inhibitor':
                color = 'red'
                linestyle = '--'
                linewidth = 1.5
            elif arc_type == 'test':
                color = 'blue'
                linestyle = ':'
                linewidth = 1.5
            else:
                color = 'black'
                linestyle = '-'
                linewidth = 1.0
            
            arrow = FancyArrowPatch(
                src_pos, tgt_pos,
                arrowstyle='->' if arc_type != 'inhibitor' else '-|',
                connectionstyle='arc3,rad=0.1',
                color=color,
                linestyle=linestyle,
                linewidth=linewidth,
                alpha=0.5,
                mutation_scale=12,
                zorder=1
            )
            ax.add_patch(arrow)
    
    # Draw transitions
    for tid, trans in transitions.items():
        x, y = trans['x'], trans['y']
        width = trans.get('width', 50)
        height = trans.get('height', 30)
        
        rect = Rectangle(
            (x - width/2, y - height/2), width, height,
            facecolor='white',
            edgecolor='black',
            linewidth=2,
            zorder=2
        )
        ax.add_patch(rect)
        
        # Label (abbreviated)
        name = trans.get('name', tid)
        if len(name) > 8:
            name = name[:6] + '...'
        ax.text(x, y, name, fontsize=6, ha='center', va='center', zorder=3)
    
    # Draw places
    for pid, place in places.items():
        x, y = place['x'], place['y']
        radius = place.get('radius', 40)
        
        # Classify and color
        place_type = classify_place(place.get('name', ''))
        color = PLACE_COLORS.get(place_type, PLACE_COLORS['Other'])
        
        circle = Circle(
            (x, y), radius,
            facecolor=color,
            edgecolor='black',
            linewidth=2,
            alpha=0.8,
            zorder=2
        )
        ax.add_patch(circle)
        
        # Label
        name = place.get('name', pid)
        if len(name) > 12:
            name = name[:10] + '...'
        ax.text(x, y, name, fontsize=7, ha='center', va='center', 
               fontweight='bold', zorder=3)
    
    # Title
    title_y = y_min + (y_max - y_min) * 0.02
    ax.text((x_min + x_max) / 2, title_y, 
           'Lambda Phage Hierarchical Model (v3)',
           fontsize=12, fontweight='bold', ha='center')
    
    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=PLACE_COLORS['Environmental'], edgecolor='black', 
                      label='Environmental (ATP, Cycle, Health)'),
        mpatches.Patch(facecolor=PLACE_COLORS['RecA'], edgecolor='black', 
                      label='Hierarchical (RecA - UV sensor)'),
        mpatches.Patch(facecolor=PLACE_COLORS['CII'], edgecolor='black', 
                      label='Integration (CII - Metabolic integrator)'),
        mpatches.Patch(facecolor=PLACE_COLORS['CI/Cro'], edgecolor='black', 
                      label='Decision (CI/Cro - Bistable switch)'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=8, framealpha=0.9)
    
    # Statistics
    stats_text = f"23 places • 36 transitions • 65 arcs"
    stats_y = y_max - (y_max - y_min) * 0.02
    ax.text((x_min + x_max) / 2, stats_y, stats_text,
           fontsize=8, ha='center',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.9))
    
    # Save
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', dpi=dpi, bbox_inches='tight')
    print(f"✓ Model figure exported to: {output_path}")
    plt.close()

if __name__ == '__main__':
    model_path = Path(__file__).parent / 'models' / 'lambda_hierarchical_v3.shy'
    output_path = Path(__file__).parent / 'manuscript' / 'figure1_model_architecture.pdf'
    
    print(f"Exporting model from: {model_path}")
    export_model_figure(model_path, output_path, figsize=(12, 10), dpi=300)
    print(f"Done! Figure saved to: {output_path}")
