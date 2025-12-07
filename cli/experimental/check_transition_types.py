#!/usr/bin/env python3
"""Check transition types in a model."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from _fix_imports import *
from _sbml_loader import load_sbml_model


def check_transition_types(sbml_path: str):
    """Check transition types in model."""
    print(f"Loading model: {sbml_path}")
    model = load_sbml_model(sbml_path)
    
    print(f"\nModel: {len(model.places)} places, {len(model.transitions)} transitions\n")
    
    # Count by type
    types = {}
    for t in model.transitions:
        ttype = t.transition_type
        types[ttype] = types.get(ttype, 0) + 1
    
    print("Transition Types:")
    for ttype, count in sorted(types.items()):
        print(f"  {ttype}: {count}")
    
    # List stochastic transitions
    stochastic = [t for t in model.transitions if t.transition_type == 'stochastic']
    print(f"\nStochastic Transitions ({len(stochastic)}):")
    for t in stochastic[:10]:  # Show first 10
        print(f"  - {t.name} (ID: {t.id})")
    if len(stochastic) > 10:
        print(f"  ... and {len(stochastic) - 10} more")
    
    # Check if any have initial tokens in input places
    print(f"\nChecking enablement at t=0:")
    enabled_count = 0
    for t in stochastic[:5]:
        # Find input arcs
        input_arcs = [arc for arc in model.arcs if arc.target == t and hasattr(arc, 'source')]
        if not input_arcs:
            print(f"  {t.name}: SOURCE (always enabled)")
            enabled_count += 1
            continue
        
        # Check tokens
        enabled = True
        for arc in input_arcs:
            if arc.source and hasattr(arc.source, 'tokens'):
                required = arc.weight
                available = arc.source.tokens
                if available < required:
                    enabled = False
                    print(f"  {t.name}: DISABLED (need {required} {arc.source.name}, have {available})")
                    break
        
        if enabled:
            print(f"  {t.name}: ENABLED")
            enabled_count += 1
    
    print(f"\n{enabled_count} of {min(5, len(stochastic))} checked transitions initially enabled")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Check transition types in SBML model'
    )
    parser.add_argument(
        'sbml_file',
        help='Path to SBML file'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.sbml_file):
        print(f"Error: File not found: {args.sbml_file}")
        sys.exit(1)
    
    check_transition_types(args.sbml_file)
