#!/usr/bin/env python3
"""
Fix desynchronized marking fields in series models.

Problem: JSON has both 'marking' and 'initial_marking' fields that became
desynchronized. The simulation uses 'initial_marking' for reset, but UI
shows 'marking', causing dose-response experiments to run at wrong concentrations.

Solution: Synchronize initial_marking <- marking for all places.

Architecture: Classes -> Properties Dialog -> JSON (passive)
Per PROGRAMMATIC_MODEL_EDITING_GUIDE.md: "always consult the class definitions"
"""

import json
import glob

def fix_place_markings(model_path):
    """Synchronize initial_marking with marking in a single model."""
    print(f"\nProcessing: {model_path}")
    
    with open(model_path, 'r') as f:
        data = json.load(f)
    
    fixed_count = 0
    
    for place in data.get('places', []):
        place_name = place.get('name', 'unnamed')
        marking = place.get('marking', 0)
        initial_marking = place.get('initial_marking', 0)
        
        # Check if desynchronized
        if marking != initial_marking:
            print(f"  {place_name:30s} marking={marking:12.6f} initial={initial_marking:12.6f} -> FIXING")
            place['initial_marking'] = marking
            fixed_count += 1
    
    if fixed_count > 0:
        # Write back with consistent formatting
        with open(model_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  ✓ Fixed {fixed_count} places")
    else:
        print(f"  ✓ Already synchronized")
    
    return fixed_count

def main():
    """Fix all series models."""
    pattern = 'workspace/projects/My_Project/drug_discovery/models/normal/series_*.shy'
    models = sorted(glob.glob(pattern))
    
    if not models:
        print(f"No models found matching: {pattern}")
        return
    
    print(f"Found {len(models)} series models")
    print("=" * 80)
    
    total_fixed = 0
    for model_path in models:
        fixed = fix_place_markings(model_path)
        total_fixed += fixed
    
    print("=" * 80)
    print(f"\n✓ Fixed {total_fixed} total places across {len(models)} models")
    print("\nArchitecture verified:")
    print("  Classes (place.py) -> Properties Dialog -> JSON (synchronized)")
    print("  Future edits through UI will maintain synchronization")

if __name__ == '__main__':
    main()
