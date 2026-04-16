#!/usr/bin/env python3
"""
Example: Compare direct JSON editing vs DTO-based editing.

This script demonstrates why DTO-based editing is superior.
"""

import sys
import json
from pathlib import Path

# Add shypn to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.data.canvas.document_model import DocumentModel


def direct_json_approach(model_path: str):
    """❌ WRONG: Direct JSON manipulation (what we did before)."""
    print("="*70)
    print("❌ APPROACH 1: Direct JSON Manipulation (OLD WAY)")
    print("="*70)
    
    # Load JSON directly
    with open(model_path) as f:
        data = json.load(f)
    
    print("\nProblems with this approach:")
    print("  1. Must manually find transition in list")
    print("  2. Must update BOTH rate_function locations")
    print("  3. No type validation")
    print("  4. No EventBus notification → cache NOT invalidated")
    print("  5. Bypasses DTO logic")
    
    # Find transition
    for t in data['transitions']:
        if t['name'] == 'GATA1_transcription':
            print(f"\n  Old rate_function: {t['rate_function'][:50]}...")
            
            # Must update BOTH locations manually
            new_rate = "0.08 * (modified)"
            t['rate_function'] = new_rate  # Top-level
            if 'properties' in t:
                t['properties']['rate_function'] = new_rate  # In dict too!
            
            print(f"  New rate_function: {t['rate_function']}")
            print("\n  ⚠️  Had to update 2 locations manually!")
            break
    
    # Save directly (NO event emission)
    with open(model_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print("\n  ⚠️  Saved WITHOUT EventBus notification")
    print("  ⚠️  ModelRepository cache NOT invalidated")
    print("  ⚠️  GUI will still show old values!")
    print()


def dto_based_approach(model_path: str):
    """✅ CORRECT: DTO-based editing (new recommended way)."""
    print("="*70)
    print("✅ APPROACH 2: DTO-Based Editing (NEW WAY)")
    print("="*70)
    
    # Load using DTO
    model = DocumentModel.load_from_file(model_path)
    
    print("\nBenefits of this approach:")
    print("  1. Pythonic object access (for transition in model.transitions)")
    print("  2. Single property setter updates BOTH locations")
    print("  3. Type validation via @property decorator")
    print("  4. EventBus 'file.saved' notification → cache invalidated")
    print("  5. Uses DTO serialization logic (to_dict/from_dict)")
    
    # Find transition using Pythonic iteration
    for transition in model.transitions:
        if transition.name == 'GATA1_transcription':
            print(f"\n  Old rate_function: {transition.rate_function[:50]}...")
            
            # Single property setter (handles _properties dict automatically)
            new_rate = "0.08 * (modified via DTO)"
            transition.rate_function = new_rate
            
            print(f"  New rate_function: {transition.rate_function[:50]}...")
            print("\n  ✅ Single property setter updated both locations!")
            break
    
    # Save using DTO (emits EventBus event)
    model.save_to_file(model_path)
    
    print("\n  ✅ Saved WITH EventBus 'file.saved' notification")
    print("  ✅ ModelRepository cache invalidated automatically")
    print("  ✅ GUI will show updated values on next access")
    print()


def compare_approaches(model_path: str):
    """Compare both approaches side-by-side."""
    print("\n" + "="*70)
    print("COMPARISON: Direct JSON vs DTO-Based Editing")
    print("="*70)
    
    print("\n┌─────────────────────────────────┬──────────────┬──────────────┐")
    print("│ Feature                         │ Direct JSON  │ DTO-Based    │")
    print("├─────────────────────────────────┼──────────────┼──────────────┤")
    print("│ Type Safety                     │ ❌ None      │ ✅ Validated │")
    print("│ Property Validation             │ ❌ None      │ ✅ Yes       │")
    print("│ Dual-location Updates           │ ❌ Manual    │ ✅ Automatic │")
    print("│ EventBus Notification           │ ❌ No        │ ✅ Yes       │")
    print("│ Cache Invalidation              │ ❌ No        │ ✅ Yes       │")
    print("│ Legacy Format Migration         │ ❌ No        │ ✅ Yes       │")
    print("│ Pythonic Access                 │ ❌ No        │ ✅ Yes       │")
    print("│ Error Detection                 │ ❌ Runtime   │ ✅ Edit-time │")
    print("└─────────────────────────────────┴──────────────┴──────────────┘")
    
    print("\n" + "="*70)
    print("RECOMMENDATION: Always use DTO-based editing!")
    print("="*70)
    
    print("\nRecommended Tool:")
    print("  python tools/update_model_parameters.py <model.shy>")
    
    print("\nOr in Python code:")
    print("  from tools.update_model_parameters import ModelParameterEditor")
    print("  editor = ModelParameterEditor('model.shy')")
    print("  editor.update_transition_rate_function('T1', '0.5 * substrate')")
    print("  editor.save()")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("This script demonstrates the difference between:")
        print("  ❌ Direct JSON manipulation (old way)")
        print("  ✅ DTO-based editing (correct way)")
        print("\nUsage:")
        print("  python compare_editing_approaches.py <model.shy>")
        print("\nExample:")
        print("  python compare_editing_approaches.py workspace/projects/gata/models/phase3a_spatial_clean.shy")
        sys.exit(1)
    
    model_path = sys.argv[1]
    
    # Just show comparison (don't actually modify)
    compare_approaches(model_path)
