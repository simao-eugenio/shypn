#!/usr/bin/env python3
"""
Compare structural properties of Lambda Phage models.
Analyzes topology, arc types, signal places, and rate functions.
"""

import json
import re
from pathlib import Path
from collections import Counter

def load_model(model_file):
    """Load a .shy model file."""
    with open(model_file, 'r') as f:
        return json.load(f)

def count_arc_types(arcs):
    """Count arcs by type."""
    arc_types = Counter()
    for arc in arcs:
        arc_type = arc.get('arc_type', 'normal')
        arc_types[arc_type] += 1
    return arc_types

def analyze_rate_complexity(rate_str):
    """Analyze rate function complexity."""
    if not rate_str:
        return {'terms': 0, 'operations': 0, 'length': 0}
    
    # Count mathematical operations
    ops = rate_str.count('+') + rate_str.count('-') + rate_str.count('*') + rate_str.count('/')
    
    # Estimate terms (rough heuristic: count + and - at top level)
    terms = rate_str.count('+') + 1
    
    return {
        'terms': terms,
        'operations': ops,
        'length': len(rate_str),
        'formula': rate_str
    }

def extract_signal_places(places):
    """Extract signal places."""
    signal_places = []
    for place in places:
        if place.get('is_signal_place', False):
            signal_places.append({
                'id': place['id'],
                'name': place['name'],
                'signal_type': place.get('signal_type', 'unknown'),
                'border_color': place.get('border_color')
            })
    return signal_places

def find_inhibitor_arcs(arcs, places, transitions):
    """Find and describe inhibitor arcs."""
    inhibitor_arcs = []
    
    # Create lookup maps
    place_map = {p['id']: p['name'] for p in places}
    trans_map = {t['id']: t['name'] for t in transitions}
    
    for arc in arcs:
        if arc.get('arc_type') == 'inhibitor':
            # Handle different arc formats
            source = arc.get('source') or arc.get('from') or arc.get('source_id')
            target = arc.get('target') or arc.get('to') or arc.get('target_id')
            
            if not source or not target:
                continue
            
            source_name = place_map.get(source, source)
            target_name = trans_map.get(target, target)
            
            inhibitor_arcs.append({
                'id': arc.get('id', 'N/A'),
                'source': source,
                'source_name': source_name,
                'target': target,
                'target_name': target_name,
                'threshold': arc.get('threshold', arc.get('weight', 'N/A')),
                'weight': arc.get('hill_coefficient', arc.get('weight', 1.0))
            })
    
    return inhibitor_arcs

def compare_models(model1_file, model2_file, model1_label="Model 1", model2_label="Model 2"):
    """Compare two model structures."""
    
    print("\n" + "="*90)
    print(f"MODEL STRUCTURE COMPARISON: {model1_label} vs {model2_label}")
    print("="*90 + "\n")
    
    # Load models
    print(f"Loading {model1_label}...")
    model1 = load_model(model1_file)
    print(f"Loading {model2_label}...")
    model2 = load_model(model2_file)
    print()
    
    # Basic topology
    print("TOPOLOGY SUMMARY")
    print("-" * 90)
    print(f"{'Component':<30} {model1_label:>25} {model2_label:>25}")
    print("-" * 90)
    print(f"{'Places':<30} {len(model1['places']):>25} {len(model2['places']):>25}")
    print(f"{'Transitions':<30} {len(model1['transitions']):>25} {len(model2['transitions']):>25}")
    print(f"{'Arcs':<30} {len(model1['arcs']):>25} {len(model2['arcs']):>25}")
    print()
    
    # Arc types
    arc_types1 = count_arc_types(model1['arcs'])
    arc_types2 = count_arc_types(model2['arcs'])
    
    print("ARC TYPE DISTRIBUTION")
    print("-" * 90)
    print(f"{'Arc Type':<30} {model1_label:>25} {model2_label:>25}")
    print("-" * 90)
    
    all_arc_types = set(arc_types1.keys()) | set(arc_types2.keys())
    for arc_type in sorted(all_arc_types):
        count1 = arc_types1.get(arc_type, 0)
        count2 = arc_types2.get(arc_type, 0)
        print(f"{arc_type:<30} {count1:>25} {count2:>25}")
    print()
    
    # Signal places
    signal1 = extract_signal_places(model1['places'])
    signal2 = extract_signal_places(model2['places'])
    
    print("SIGNAL PLACES (Ψ)")
    print("-" * 90)
    print(f"{model1_label}: {len(signal1)} signal places")
    if signal1:
        for sp in signal1:
            print(f"  - {sp['id']} ({sp['name']}): {sp.get('signal_type', 'N/A')}")
    else:
        print("  (none)")
    print()
    
    print(f"{model2_label}: {len(signal2)} signal places")
    if signal2:
        for sp in signal2:
            print(f"  - {sp['id']} ({sp['name']}): {sp.get('signal_type', 'N/A')}")
    else:
        print("  (none)")
    print()
    
    # Inhibitor arcs
    inhibitors1 = find_inhibitor_arcs(model1['arcs'], model1['places'], model1['transitions'])
    inhibitors2 = find_inhibitor_arcs(model2['arcs'], model2['places'], model2['transitions'])
    
    print("INHIBITOR ARCS (⊣)")
    print("-" * 90)
    print(f"{model1_label}: {len(inhibitors1)} inhibitor arcs")
    if inhibitors1:
        for inh in inhibitors1:
            print(f"  - {inh['id']}: {inh['source_name']} ⊣ {inh['target_name']} "
                  f"(threshold={inh['threshold']}, hill={inh['weight']})")
    else:
        print("  (none - regulation embedded in rate functions)")
    print()
    
    print(f"{model2_label}: {len(inhibitors2)} inhibitor arcs")
    if inhibitors2:
        for inh in inhibitors2:
            print(f"  - {inh['id']}: {inh['source_name']} ⊣ {inh['target_name']} "
                  f"(threshold={inh['threshold']}, hill={inh['weight']})")
    else:
        print("  (none - regulation embedded in rate functions)")
    print()
    
    # Rate function analysis
    print("RATE FUNCTION COMPLEXITY")
    print("-" * 90)
    
    # Find transcription transitions (T1 CI_Transcription, T6 Cro_Transcription)
    trans_map1 = {t['id']: t for t in model1['transitions']}
    trans_map2 = {t['id']: t for t in model2['transitions']}
    
    key_transitions = ['T1', 'T6']  # CI and Cro transcription
    
    for tid in key_transitions:
        if tid in trans_map1 and tid in trans_map2:
            t1 = trans_map1[tid]
            t2 = trans_map2[tid]
            
            rate1 = t1.get('rate_function', '')
            rate2 = t2.get('rate_function', '')
            
            complexity1 = analyze_rate_complexity(rate1)
            complexity2 = analyze_rate_complexity(rate2)
            
            print(f"\n{tid} ({t1.get('name', tid)}):")
            print(f"  {model1_label}:")
            print(f"    Formula: {rate1[:80]}{'...' if len(rate1) > 80 else ''}")
            print(f"    Length: {complexity1['length']} chars, Operations: {complexity1['operations']}")
            
            print(f"  {model2_label}:")
            print(f"    Formula: {rate2[:80]}{'...' if len(rate2) > 80 else ''}")
            print(f"    Length: {complexity2['length']} chars, Operations: {complexity2['operations']}")
            
            if complexity1['length'] > 0:
                reduction = 100 * (1 - complexity2['length'] / complexity1['length'])
                print(f"  → Complexity reduction: {reduction:.1f}%")
    print()
    
    # Summary
    print("KEY DIFFERENCES")
    print("-" * 90)
    differences = []
    
    if len(signal1) != len(signal2):
        differences.append(f"• Signal places: {len(signal1)} → {len(signal2)}")
    
    if len(inhibitors1) != len(inhibitors2):
        differences.append(f"• Inhibitor arcs: {len(inhibitors1)} → {len(inhibitors2)}")
    
    if len(model1['arcs']) != len(model2['arcs']):
        diff = len(model2['arcs']) - len(model1['arcs'])
        differences.append(f"• Total arcs: {len(model1['arcs'])} → {len(model2['arcs'])} ({diff:+d})")
    
    # Check if mutual repression exists
    if inhibitors2:
        ci_inhibits = any('CI' in i['source_name'] and 'Cro' in i['target_name'] for i in inhibitors2)
        cro_inhibits = any('Cro' in i['source_name'] and 'CI' in i['target_name'] for i in inhibitors2)
        if ci_inhibits and cro_inhibits:
            differences.append("• Mutual repression: Embedded in rates → Explicit inhibitor arcs")
    
    if differences:
        for diff in differences:
            print(diff)
    else:
        print("No structural differences detected")
    print()
    
    # Behavioral equivalence note
    print("EXPECTED BEHAVIOR")
    print("-" * 90)
    print("If models are properly refactored:")
    print("  ✓ Same bistable dynamics (lysogenic vs lytic outcomes)")
    print("  ✓ Same outcome proportions under identical conditions")
    print("  ✓ Same response to UV stress")
    print("  ✓ Chi-square p > 0.05 in batch simulations")
    print()
    
    return {
        'model1': {
            'places': len(model1['places']),
            'transitions': len(model1['transitions']),
            'arcs': len(model1['arcs']),
            'signal_places': len(signal1),
            'inhibitor_arcs': len(inhibitors1)
        },
        'model2': {
            'places': len(model2['places']),
            'transitions': len(model2['transitions']),
            'arcs': len(model2['arcs']),
            'signal_places': len(signal2),
            'inhibitor_arcs': len(inhibitors2)
        }
    }

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python compare_model_structure.py <model1.shy> <model2.shy> [label1] [label2]")
        print()
        print("Example:")
        print("  python compare_model_structure.py model_original.shy model_signal.shy \"Original\" \"Signal Hierarchy\"")
        sys.exit(1)
    
    model1_file = sys.argv[1]
    model2_file = sys.argv[2]
    
    label1 = sys.argv[3] if len(sys.argv) > 3 else "Model 1"
    label2 = sys.argv[4] if len(sys.argv) > 4 else "Model 2"
    
    results = compare_models(model1_file, model2_file, label1, label2)
