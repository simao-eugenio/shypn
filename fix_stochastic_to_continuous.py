#!/usr/bin/env python3
"""
Fix stochastic transitions with formulas to be continuous.

This script converts stochastic transitions that have rate_function formulas
to continuous transitions, since formulas can evaluate to negative values
(reversible reactions) which are invalid for stochastic transitions.
"""

import json
import sys
from pathlib import Path


def fix_transitions(filepath: str) -> None:
    """Convert stochastic transitions with formulas to continuous."""
    
    filepath = Path(filepath)
    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    print(f"Loading: {filepath}")
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    transitions = data.get('transitions', [])
    converted_count = 0
    
    for t in transitions:
        t_type = t.get('transition_type', t.get('type', 'unknown'))
        has_formula = 'rate_function' in t.get('properties', {})
        
        # Convert stochastic transitions with formulas to continuous
        if t_type == 'stochastic' and has_formula:
            t['transition_type'] = 'continuous'
            t['type'] = 'continuous'
            
            # Mark for enrichment
            if 'properties' not in t:
                t['properties'] = {}
            t['properties']['needs_enrichment'] = True
            t['properties']['enrichment_reason'] = 'Converted from stochastic (had formula)'
            
            print(f"  ✓ Converted {t.get('name')} from stochastic to continuous")
            converted_count += 1
    
    if converted_count > 0:
        # Save the file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✅ Converted {converted_count} transitions to continuous")
        print(f"File saved: {filepath}")
    else:
        print("\n✓ No stochastic transitions with formulas found")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 fix_stochastic_to_continuous.py <model.shy>")
        print("\nExample:")
        print("  python3 fix_stochastic_to_continuous.py workspace/projects/SBML/models/BIOMD0000000061.shy")
        sys.exit(1)
    
    fix_transitions(sys.argv[1])
