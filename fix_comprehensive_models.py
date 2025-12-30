#!/usr/bin/env python3
"""
Fix comprehensive V. fischeri models to load in SHYpn GUI.

Main issues found:
1. Version "2.4.6" should be "2.0"
2. Transitions use "orientation" but GUI might expect consistency
3. Need to verify arc structure matches working models
"""

import json
import sys
from pathlib import Path

def fix_model(input_file):
    """Fix model file to match working model format."""
    print(f"\nFixing {input_file.name}...")
    
    with open(input_file, 'r') as f:
        model = json.load(f)
    
    # Fix 1: Update version
    old_version = model.get("version", "unknown")
    model["version"] = "2.0"
    print(f"  ✓ Updated version: {old_version} → 2.0")
    
    # Fix 2: Ensure view_state has transformations (if needed)
    if "view_state" not in model:
        model["view_state"] = {}
    if "transformations" not in model["view_state"]:
        model["view_state"]["transformations"] = []
    
    # Fix 3: Verify all arcs have complete structure
    arc_fixes = 0
    for arc in model.get("arcs", []):
        # Ensure all required fields exist
        if "name" not in arc:
            arc["name"] = arc.get("id", "")
            arc_fixes += 1
        if "object_type" not in arc:
            arc["object_type"] = "arc"
            arc_fixes += 1
        if "label" not in arc and "name" in arc:
            arc["label"] = ""
            arc_fixes += 1
        if "source_type" not in arc:
            arc["source_type"] = "place" if arc.get("source_id", "").startswith("P") else "transition"
            arc_fixes += 1
        if "target_type" not in arc:
            arc["target_type"] = "transition" if arc.get("target_id", "").startswith("T") else "place"
            arc_fixes += 1
        if "threshold" not in arc:
            # Add threshold for test/inhibitor arcs, null for others
            if arc.get("arc_type") in ["test", "inhibitor"]:
                arc["threshold"] = arc.get("weight", 1)
            else:
                arc["threshold"] = None
            arc_fixes += 1
    
    if arc_fixes > 0:
        print(f"  ✓ Fixed {arc_fixes} arc field issues")
    
    # Fix 4: Ensure all places have consistent float values
    for place in model.get("places", []):
        # Convert x, y, radius to floats consistently
        if "x" in place:
            place["x"] = float(place["x"])
        if "y" in place:
            place["y"] = float(place["y"])
        if "radius" in place:
            place["radius"] = float(place["radius"])
    
    # Fix 5: Ensure transitions have consistent structure
    transition_fixes = 0
    for trans in model.get("transitions", []):
        # Convert dimensions to floats
        if "width" in trans:
            trans["width"] = float(trans["width"])
        if "height" in trans:
            trans["height"] = float(trans["height"])
        if "x" in trans:
            trans["x"] = float(trans["x"])
        if "y" in trans:
            trans["y"] = float(trans["y"])
        
        # Ensure transitions have properties dict with guard_function
        if "properties" in trans:
            if "guard_function" not in trans["properties"]:
                trans["properties"]["guard_function"] = trans.get("guard", "1")
                transition_fixes += 1
    
    if transition_fixes > 0:
        print(f"  ✓ Fixed {transition_fixes} transition property issues")
    
    # Write fixed model
    output_file = input_file.parent / f"{input_file.stem}_fixed{input_file.suffix}"
    with open(output_file, 'w') as f:
        json.dump(model, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ Saved fixed model to: {output_file.name}")
    
    # Statistics
    print(f"\n  Model statistics:")
    print(f"    Places: {len(model.get('places', []))}")
    print(f"    Transitions: {len(model.get('transitions', []))}")
    print(f"    Arcs: {len(model.get('arcs', []))}")
    signal_places = [p for p in model.get('places', []) if p.get('is_signal_place')]
    print(f"    Signal places: {len(signal_places)}")
    arc_types = {}
    for arc in model.get('arcs', []):
        atype = arc.get('arc_type', 'unknown')
        arc_types[atype] = arc_types.get(atype, 0) + 1
    print(f"    Arc types: {arc_types}")
    
    return output_file

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
    print("FIXING V. FISCHERI COMPREHENSIVE MODELS")
    print("="*60)
    
    # Fix both models
    fixed_normal = fix_model(normal_file)
    fixed_stress = fix_model(stress_file)
    
    print("\n" + "="*60)
    print("FIX COMPLETE")
    print("="*60)
    print("\nFixed files created:")
    print(f"  - {fixed_normal}")
    print(f"  - {fixed_stress}")
    print("\nNext steps:")
    print("  1. Open SHYpn GUI")
    print("  2. File → Open → vfischeri_comprehensive_normal_fixed.shy")
    print("  3. Verify model loads and displays correctly")
    print("  4. Repeat for stress model")
    print("  5. If successful, replace original files with fixed versions")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
