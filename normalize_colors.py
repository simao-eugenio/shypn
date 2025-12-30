#!/usr/bin/env python3
"""
Normalize color scheme for SHYpn:
1. Signal places: Blue border (0.0, 0.4, 0.8) instead of orange
2. Inhibitor arcs: Black (0.0, 0.0, 0.0) instead of red

This script updates the comprehensive V. fischeri models to use the new normalized colors.
"""

import json
import sys
from pathlib import Path

def normalize_model_colors(input_file):
    """Normalize colors in a model file."""
    print(f"\nNormalizing colors in {input_file.name}...")
    
    with open(input_file, 'r') as f:
        model = json.load(f)
    
    changes = {
        'signal_places': 0,
        'inhibitor_arcs': 0
    }
    
    # Normalize signal place border colors: Orange → Blue
    ORANGE_BORDER = [1.0, 0.5, 0.0]
    BLUE_BORDER = [0.0, 0.4, 0.8]
    
    for place in model.get('places', []):
        if place.get('is_signal_place') and place.get('border_color') == ORANGE_BORDER:
            place['border_color'] = BLUE_BORDER
            changes['signal_places'] += 1
    
    # Normalize inhibitor arc colors: Any non-black → Black
    BLACK_COLOR = [0.0, 0.0, 0.0]
    
    for arc in model.get('arcs', []):
        if arc.get('arc_type') == 'inhibitor':
            # Check if color is not already black
            current_color = arc.get('color', BLACK_COLOR)
            if current_color != BLACK_COLOR:
                arc['color'] = BLACK_COLOR
                changes['inhibitor_arcs'] += 1
    
    # Write updated model
    with open(input_file, 'w') as f:
        json.dump(model, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ Updated {changes['signal_places']} signal place border colors (orange → blue)")
    print(f"  ✓ Updated {changes['inhibitor_arcs']} inhibitor arc colors → black")
    
    return changes

def main():
    # Find the comprehensive models
    workspace = Path("/home/simao/projetos/shypn/workspace/projects/My_Project/extended_biopn/model")
    
    normal_file = workspace / "vfischeri_comprehensive_normal.shy"
    stress_file = workspace / "vfischeri_comprehensive_stress.shy"
    
    if not normal_file.exists():
        print(f"ERROR: {normal_file} not found!")
        return 1
    
    if not stress_file.exists():
        print(f"ERROR: {stress_file} not found!")
        return 1
    
    print("="*60)
    print("NORMALIZING COLOR SCHEME")
    print("="*60)
    print("\nChanges:")
    print("  - Signal places: Orange (1.0, 0.5, 0.0) → Blue (0.0, 0.4, 0.8)")
    print("  - Inhibitor arcs: Red → Black (0.0, 0.0, 0.0)")
    
    # Normalize both models
    changes_normal = normalize_model_colors(normal_file)
    changes_stress = normalize_model_colors(stress_file)
    
    print("\n" + "="*60)
    print("COLOR NORMALIZATION COMPLETE")
    print("="*60)
    print("\nSummary:")
    print(f"  Normal model: {changes_normal['signal_places']} signal places, {changes_normal['inhibitor_arcs']} inhibitor arcs")
    print(f"  Stress model: {changes_stress['signal_places']} signal places, {changes_stress['inhibitor_arcs']} inhibitor arcs")
    print("\nVisualization:")
    print("  • Signal places (Ψ): Blue hexagons with thick borders")
    print("  • Inhibitor arcs: Black lines with hollow circles")
    print("  • Test arcs: Blue dashed lines with diamonds")
    print("  • Signal flow arcs: Orange dashed lines with angles")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
