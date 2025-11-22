#!/usr/bin/env python3
"""
Diagnose why all transitions get the same Vmax=70, Km=0.1 values.

This tool analyzes a pathway document to understand why heuristics
aren't differentiating between transitions.
"""

import sys
sys.path.insert(0, 'src')

from shypn.crossfetch.inference.heuristic_engine import HeuristicInferenceEngine
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def diagnose_pathway(document):
    """Analyze why transitions get uniform kinetic parameters."""
    
    engine = HeuristicInferenceEngine()
    
    print("=" * 80)
    print("HEURISTIC UNIFORMITY DIAGNOSIS")
    print("=" * 80)
    print()
    
    # Get all transitions
    transitions = document.transitions if hasattr(document, 'transitions') else []
    
    if not transitions:
        print("ERROR: No transitions found in document")
        return
    
    print(f"Found {len(transitions)} transitions")
    print()
    
    # Analyze first 10 transitions
    print("─" * 80)
    print("Analyzing first 10 transitions:")
    print("─" * 80)
    print()
    
    for i, transition in enumerate(transitions[:10], 1):
        print(f"{i}. Transition: {transition.id}")
        print(f"   Label: '{transition.label}'")
        print(f"   Name: '{transition.name}'")
        
        # Check EC number
        ec = getattr(transition, 'ec_number', None)
        print(f"   EC number: {ec or 'None'}")
        
        # Check reaction ID
        rxn = getattr(transition, 'reaction_id', None)
        print(f"   Reaction ID: {rxn or 'None'}")
        
        # Check substrates
        if hasattr(transition, 'input_arcs') and transition.input_arcs:
            substrates = []
            for arc in transition.input_arcs[:3]:  # First 3
                if hasattr(arc, 'source'):
                    place = arc.source
                    name = getattr(place, 'label', None) or getattr(place, 'name', None)
                    if name:
                        substrates.append(name)
            print(f"   Substrates: {', '.join(substrates) if substrates else 'None'}")
        else:
            print(f"   Substrates: None")
        
        # Infer parameters
        result = engine.infer_parameters(transition, organism='Homo sapiens')
        params = result.parameters
        
        # Check if continuous
        if hasattr(params, 'vmax'):
            print(f"   → Vmax: {params.vmax:.3g}, Km: {params.km:.3g}")
            print(f"   → Confidence: {params.confidence_score:.2f}")
            print(f"   → Source: {params.source}")
        else:
            print(f"   → Type: {params.transition_type.value} (not continuous)")
        
        print()
    
    # Check for patterns
    print("─" * 80)
    print("Pattern Analysis:")
    print("─" * 80)
    print()
    
    vmax_values = []
    km_values = []
    has_ec_count = 0
    has_substrates_count = 0
    enriched_substrates_count = 0
    
    for transition in transitions:
        result = engine.infer_parameters(transition, organism='Homo sapiens')
        params = result.parameters
        
        if hasattr(params, 'vmax'):
            vmax_values.append(params.vmax)
            km_values.append(params.km)
        
        # Check EC numbers
        if hasattr(transition, 'ec_number') and transition.ec_number:
            has_ec_count += 1
        
        # Check substrates
        if hasattr(transition, 'input_arcs') and transition.input_arcs:
            has_substrates_count += 1
            
            # Check if enriched (not KEGG codes)
            for arc in transition.input_arcs:
                if hasattr(arc, 'source'):
                    place = arc.source
                    name = getattr(place, 'label', None) or getattr(place, 'name', None)
                    if name and not (name.startswith('C') and len(name) == 6 and name[1:].isdigit()):
                        enriched_substrates_count += 1
                        break
    
    print(f"Transitions with EC numbers: {has_ec_count}/{len(transitions)}")
    print(f"Transitions with substrates: {has_substrates_count}/{len(transitions)}")
    print(f"Transitions with enriched substrates: {enriched_substrates_count}/{len(transitions)}")
    print()
    
    if vmax_values:
        print(f"Vmax range: {min(vmax_values):.3g} - {max(vmax_values):.3g}")
        print(f"Km range: {min(km_values):.3g} - {max(km_values):.3g}")
        
        # Check uniformity
        unique_vmax = len(set(vmax_values))
        unique_km = len(set(km_values))
        print(f"Unique Vmax values: {unique_vmax}")
        print(f"Unique Km values: {unique_km}")
        
        if unique_vmax <= 3 and unique_km <= 3:
            print()
            print("⚠️  WARNING: Very low parameter diversity!")
            print()
            print("Possible causes:")
            print("  1. All transitions have similar labels (no enzyme names)")
            print("  2. EC numbers not present or not parsed")
            print("  3. Substrates not enriched (still KEGG codes)")
            print("  4. All falling back to generic defaults")
    
    print()


def main():
    """Run diagnosis on loaded pathway."""
    
    print()
    print("To use this diagnostic:")
    print("  1. Load a pathway in Shypn GUI")
    print("  2. In Python console, run:")
    print("     from dev.diagnose_heuristic_uniformity import diagnose_pathway")
    print("     diagnose_pathway(document_model)  # Use your document variable")
    print()
    print("Or provide document model as argument to this script")
    print()


if __name__ == '__main__':
    main()
