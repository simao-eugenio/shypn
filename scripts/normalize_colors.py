#!/usr/bin/env python3
"""
Normalize color scheme for SHYpn (2025-12-31):
1. All net objects: Black by default (0.0, 0.0, 0.0)
2. Signal places: Hexagonal shape with black border (not blue/orange)
3. Test arcs: Blue (0.0, 0.0, 1.0) - ONLY colored element
4. Inhibitor arcs: Black (0.0, 0.0, 0.0)

This script updates models to use the minimalist black-and-blue color scheme.
Visual distinction is through SHAPE (hexagons) not COLOR.
"""

import json
import sys
from pathlib import Path

def normalize_model_colors(input_file):
    """Normalize colors in a model file to black-and-blue scheme."""
    print(f"\nNormalizing colors in {input_file.name}...")
    
    with open(input_file, 'r') as f:
        model = json.load(f)
    
    changes = {
        'signal_places': 0,
        'inhibitor_arcs': 0,
        'test_arcs': 0,
        'other_arcs': 0
    }
    
    # Normalize signal place border colors: Any color → Black
    BLACK_BORDER = [0.0, 0.0, 0.0]
    
    for place in model.get('places', []):
        if place.get('is_signal_place'):
            # Signal places should have black borders (hexagon distinguishes them)
            if place.get('border_color') != BLACK_BORDER:
                place['border_color'] = BLACK_BORDER
                changes['signal_places'] += 1
    
    # Normalize arc colors
    BLACK_COLOR = [0.0, 0.0, 0.0]
    BLUE_COLOR = [0.0, 0.0, 1.0]  # Test arcs
    LIGHT_GRAY_COLOR = [0.7, 0.7, 0.7]  # Signal flow arcs
    
    for arc in model.get('arcs', []):
        arc_type = arc.get('arc_type', 'normal')
        
        if arc_type == 'test':
            # Test arcs should be blue
            if arc.get('color') != BLUE_COLOR:
                arc['color'] = BLUE_COLOR
                changes['test_arcs'] += 1
        elif arc_type == 'signal_flow':
            # Signal flow arcs should be light gray
            if arc.get('color') != LIGHT_GRAY_COLOR:
                arc['color'] = LIGHT_GRAY_COLOR
                changes['test_arcs'] += 1  # Count with test arcs as colored elements
        elif arc_type == 'inhibitor':
            # Inhibitor arcs should be black
            if arc.get('color') != BLACK_COLOR:
                arc['color'] = BLACK_COLOR
                changes['inhibitor_arcs'] += 1
        else:
            # All other arcs (normal, signal from enzymes) should be black
            if arc.get('color') != BLACK_COLOR:
                arc['color'] = BLACK_COLOR
                changes['other_arcs'] += 1
    
    # Write updated model
    with open(input_file, 'w') as f:
        json.dump(model, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ Updated {changes['signal_places']} signal place borders → black")
    print(f"  ✓ Updated {changes['test_arcs']} test arcs → blue")
    print(f"  ✓ Updated {changes['inhibitor_arcs']} inhibitor arcs → black")
    print(f"  ✓ Updated {changes['other_arcs']} other arcs → black")
    
    return changes
 (2025-12-31)")
    print("="*60)
    print("\nChanges:")
    print("  - All objects → Black (0.0, 0.0, 0.0)")
    print("  - Signal places → Black hexagonal borders (shape distinguishes)")
    print("  - Test arcs → Blue (0.0, 0.0, 1.0)")
    print("  - Signal flow arcs → Light gray (0.7, 0.7, 0.7)")
    print("  - Inhibitor arcs → Black")
    print("  - Normal/Signal arcs → Black
    normal_file = workspace / "vfischeri_comprehensive_normal.shy"
    stress_file = workspace / "vfischeri_comprehensive_stress.shy"
    
    if not normal_file.exists(): (2025-12-31)")
    print("="*60)
    print("\nSummary:")
    print(f"  Normal model:")
    print(f"    - {changes_normal['signal_places']} signal places → black borders")
    print(f"    - {changes_normal['test_arcs']} test arcs → blue")
    print(f"    - {changes_normal['inhibitor_arcs']} inhibitor arcs → black")
    print(f"    - {changes_normal['other_arcs']} other arcs → black")
    print(f"  Stress model:")
    print(f"    - {changes_stress['signal_places']} signal places → black borders")
    print(f"    - {changes_stress['test_arcs']} test arcs → blue")
    print(f"    - {changes_stress['inhibitor_arcs']} inhibitor arcs → black")
    print(f"    - {changes_stress['other_arcs']} other arcs → black")
    print("\nVisualization:")
    print("  • Signal places (Ψ): Black hexagons (shape distinguishes)")
    print("  • Test arcs: Blue dashed lines with diamonds")
    print("  • Signal flow arcs: Light gray dashed lines with angles")
    print("  • Inhibitor arcs: Black lines with hollow circles")
    print("  • Normal arcs: Black lines with arrows")
    print("  • All other elements: Black")
    print("\nSee doc/COLOR_NORMALIZATION.md for details.
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
