#!/usr/bin/env python3
"""
Analyze signal flow arcs in E. coli core model and suggest signal place annotations.

This script:
1. Identifies which places are sources of signal_flow arcs
2. Analyzes their role in the network
3. Suggests appropriate signal_type annotations
4. Creates an annotated version ready for hierarchical exploration
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Set
from collections import defaultdict


def analyze_signal_flow_arcs():
    """Analyze signal flow arcs in E. coli core model."""
    
    print("=" * 80)
    print("E. coli Core - Signal Flow Arc Analysis")
    print("=" * 80)
    print()
    
    # Load model
    model_path = Path(__file__).parent.parent / "workspace/projects/My_Project/models/e_coli_core.shy"
    
    with open(model_path, 'r') as f:
        data = json.load(f)
    
    places = {p['id']: p for p in data['places']}
    transitions = {t['id']: t for t in data['transitions']}
    arcs = data['arcs']
    
    # Find signal_flow arcs
    signal_flow_arcs = [a for a in arcs if a.get('arc_type') == 'signal_flow']
    
    print(f"Total arcs: {len(arcs)}")
    print(f"Signal flow arcs: {len(signal_flow_arcs)}")
    print()
    
    # Analyze sources of signal_flow arcs
    signal_sources: Dict[str, List[str]] = defaultdict(list)
    
    for arc in signal_flow_arcs:
        source_id = arc.get('source_id')
        target_id = arc.get('target_id')
        
        if source_id in places:
            signal_sources[source_id].append(target_id)
    
    print(f"Unique places as signal sources: {len(signal_sources)}")
    print()
    
    # Categorize by metabolite type
    energy_metabolites = ['atp', 'adp', 'amp', 'gtp', 'gdp', 'gmp', 'ctp', 'cdp', 'utp', 'udp']
    redox_metabolites = ['nadh', 'nad', 'nadph', 'nadp', 'fad', 'fadh']
    cofactors = ['coa', 'accoa', 'pep', 'pi']
    
    categories = {
        'ENERGY': [],
        'METABOLIC': [],
        'COFACTOR': [],
        'OTHER': []
    }
    
    print("=" * 80)
    print("Signal Source Places (Top 20 by outgoing signal arcs)")
    print("=" * 80)
    print()
    
    # Sort by number of outgoing signal arcs
    sorted_sources = sorted(signal_sources.items(), key=lambda x: len(x[1]), reverse=True)
    
    for i, (place_id, targets) in enumerate(sorted_sources[:20]):
        place = places[place_id]
        name = place.get('name', place_id).lower()
        label = place.get('label', name)
        
        # Categorize
        category = 'OTHER'
        if any(em in name for em in energy_metabolites):
            category = 'ENERGY'
            categories['ENERGY'].append(place_id)
        elif any(rm in name for rm in redox_metabolites):
            category = 'METABOLIC'
            categories['METABOLIC'].append(place_id)
        elif any(cf in name for cf in cofactors):
            category = 'COFACTOR'
            categories['COFACTOR'].append(place_id)
        else:
            categories['OTHER'].append(place_id)
        
        print(f"{i+1:2d}. {place_id} ({label})")
        print(f"    Outgoing signals: {len(targets)}")
        print(f"    Suggested type: {category}")
        print()
    
    # Summary by category
    print("=" * 80)
    print("Suggested Signal Place Annotations")
    print("=" * 80)
    print()
    
    for category, place_ids in categories.items():
        if place_ids:
            print(f"{category} Signals ({len(place_ids)} places):")
            for pid in place_ids[:10]:
                place = places[pid]
                label = place.get('label', pid)
                print(f"  - {pid}: {label}")
            if len(place_ids) > 10:
                print(f"  ... and {len(place_ids) - 10} more")
            print()
    
    # Generate recommendations
    print("=" * 80)
    print("Recommendations for Hierarchical Exploration")
    print("=" * 80)
    print()
    
    print("To enable hierarchical exploration on this model:")
    print()
    print("1. Annotate key energy metabolites as ENERGY signals:")
    energy_candidates = [pid for pid in categories['ENERGY'][:5]]
    for pid in energy_candidates:
        label = places[pid].get('label', pid)
        print(f"   - {pid} ({label})")
    print()
    
    print("2. Annotate redox carriers as METABOLIC signals:")
    metabolic_candidates = [pid for pid in categories['METABOLIC'][:5]]
    for pid in metabolic_candidates:
        label = places[pid].get('label', pid)
        print(f"   - {pid} ({label})")
    print()
    
    print("3. The 173 existing signal_flow arcs will define layer dependencies")
    print()
    
    print("Expected hierarchy:")
    print("  Layer 0: Energy metabolites (ATP, GTP, etc.)")
    print("  Layer 2: Redox state (NADH, NADPH)")
    print("  Layer 3: Other regulatory metabolites")
    print()
    
    print("This will enable compositional state space exploration:")
    print("  - Explore energy states first (baseline metabolism)")
    print("  - For each stable energy state, explore redox states")
    print("  - For each stable redox state, explore downstream regulation")
    print()
    
    return {
        'total_arcs': len(arcs),
        'signal_flow_arcs': len(signal_flow_arcs),
        'signal_source_places': len(signal_sources),
        'categories': {k: len(v) for k, v in categories.items()},
        'recommendations': {
            'energy': energy_candidates,
            'metabolic': metabolic_candidates
        }
    }


if __name__ == "__main__":
    results = analyze_signal_flow_arcs()
    
    print("=" * 80)
    print("Analysis complete!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  Signal flow arcs: {results['signal_flow_arcs']}")
    print(f"  Potential signal places: {results['signal_source_places']}")
    print(f"  Energy candidates: {len(results['recommendations']['energy'])}")
    print(f"  Metabolic candidates: {len(results['recommendations']['metabolic'])}")
