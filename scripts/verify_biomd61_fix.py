#!/usr/bin/env python3
"""
Verify BIOMD0000000061 simulation fix.

Check that all transitions with rate_function formulas are now continuous type.
"""

import json
import sys
from pathlib import Path


def verify_fix(filepath: str) -> None:
    """Verify all transitions with formulas are continuous."""
    
    filepath = Path(filepath)
    if not filepath.exists():
        print(f"❌ Error: File not found: {filepath}")
        sys.exit(1)
    
    print(f"📖 Loading: {filepath.name}")
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    transitions = data.get('transitions', [])
    total = len(transitions)
    
    print(f"\n📊 Total transitions: {total}")
    
    # Categorize transitions
    stochastic_count = 0
    continuous_count = 0
    stochastic_with_formula = []
    continuous_with_formula = []
    
    for t in transitions:
        t_type = t.get('transition_type', t.get('type', 'unknown'))
        has_formula = 'rate_function' in t.get('properties', {})
        
        if t_type == 'stochastic':
            stochastic_count += 1
            if has_formula:
                stochastic_with_formula.append(t)
        elif t_type == 'continuous':
            continuous_count += 1
            if has_formula:
                continuous_with_formula.append(t)
    
    print(f"\n🔍 Transition Types:")
    print(f"   Continuous: {continuous_count}")
    print(f"   Stochastic: {stochastic_count}")
    print(f"   Other: {total - continuous_count - stochastic_count}")
    
    print(f"\n🧪 Transitions with Formulas:")
    print(f"   Continuous with formula: {len(continuous_with_formula)}")
    print(f"   Stochastic with formula: {len(stochastic_with_formula)}")
    
    # Check for issues
    if stochastic_with_formula:
        print(f"\n⚠️  WARNING: Found {len(stochastic_with_formula)} stochastic transitions with formulas:")
        for t in stochastic_with_formula:
            formula = t['properties']['rate_function']
            has_subtraction = ' - ' in formula
            status = "❌ HAS SUBTRACTION" if has_subtraction else "⚠️  No subtraction"
            print(f"   {status}: {t['name']} ({t.get('label', 'No label')})")
            if has_subtraction:
                print(f"      Formula: {formula[:80]}...")
        print(f"\n💡 These should be converted to continuous type.")
    else:
        print(f"\n✅ No stochastic transitions with formulas found!")
    
    # Check conversions
    converted = [t for t in transitions if t.get('properties', {}).get('enrichment_reason') == 'Converted from stochastic (had formula)']
    if converted:
        print(f"\n🔄 Converted Transitions: {len(converted)}")
        for t in converted:
            print(f"   ✓ {t['name']}: {t.get('label', 'No label')}")
    
    # Summary
    print(f"\n" + "="*70)
    if not stochastic_with_formula:
        print("✅ VERIFICATION PASSED: All transitions with formulas are continuous")
    else:
        print("❌ VERIFICATION FAILED: Some stochastic transitions still have formulas")
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 verify_biomd61_fix.py <model.shy>")
        print("\nExample:")
        print("  python3 verify_biomd61_fix.py workspace/projects/SBML/models/BIOMD0000000061.shy")
        sys.exit(1)
    
    verify_fix(sys.argv[1])
