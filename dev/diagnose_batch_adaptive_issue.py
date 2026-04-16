#!/usr/bin/env python3
"""Diagnose why adaptive transitions lose arc connections in batch mode.

Tests:
1. Object identity vs ID equality for arc.target == transition
2. Whether signal_flow arcs exist in model.arcs
3. Whether places can be looked up by ID
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shypn.data.canvas.document_model import DocumentModel


def diagnose_adaptive_connections(model_path):
    """Check if adaptive transitions can find their input places."""
    
    print(f"Loading model: {model_path}")
    document = DocumentModel.load_from_file(model_path)
    
    # Find adaptive transitions
    adaptive_transitions = [
        t for t in document.transitions 
        if hasattr(t, 'transition_type') and t.transition_type == 'adaptive'
    ]
    
    print(f"\nFound {len(adaptive_transitions)} adaptive transitions:")
    for t in adaptive_transitions:
        adaptive_filter = getattr(t, 'adaptive_filter', 'all_places')
        has_attr = hasattr(t, 'adaptive_filter')
        print(f"  - {t.name} (filter={adaptive_filter}, hasattr={has_attr})")
    
    # Check arc connectivity for each adaptive transition
    for transition in adaptive_transitions:
        print(f"\n{'='*60}")
        print(f"Transition: {transition.name} (ID: {transition.id})")
        print(f"Adaptive filter: {getattr(transition, 'adaptive_filter', 'all_places')}")
        print(f"Object ID: {id(transition)}")
        
        # Method 1: Object reference comparison (current implementation)
        input_arcs_by_ref = [arc for arc in document.arcs if arc.target == transition]
        print(f"\nMethod 1 - Object reference (arc.target == transition):")
        print(f"  Found {len(input_arcs_by_ref)} input arcs")
        for arc in input_arcs_by_ref:
            print(f"    - {arc.id}: {arc.source.name} → {arc.target.name} [{arc.arc_type}]")
        
        # Method 2: ID comparison (alternative)
        input_arcs_by_id = [arc for arc in document.arcs if arc.target_id == transition.id]
        print(f"\nMethod 2 - ID comparison (arc.target_id == transition.id):")
        print(f"  Found {len(input_arcs_by_id)} input arcs")
        for arc in input_arcs_by_id:
            print(f"    - {arc.id}: {arc.source.name} → {arc.target.name} [{arc.arc_type}]")
            print(f"        arc.target == transition: {arc.target == transition}")
            print(f"        arc.target is transition: {arc.target is transition}")
            print(f"        id(arc.target): {id(arc.target)}, id(transition): {id(transition)}")
        
        # Check if target objects match by value (==) vs identity (is)
        if len(input_arcs_by_id) > 0 and len(input_arcs_by_ref) == 0:
            print(f"\n⚠️  WARNING: Object reference equality FAILS but ID equality WORKS")
            print(f"    This suggests arc.target and transition are different objects!")
            
        # Method 3: Check signal_flow arcs specifically
        signal_flow_arcs = [
            arc for arc in document.arcs 
            if arc.arc_type == 'signal_flow' and arc.target_id == transition.id
        ]
        print(f"\nMethod 3 - Signal flow arcs only:")
        print(f"  Found {len(signal_flow_arcs)} signal_flow input arcs")
        for arc in signal_flow_arcs:
            place = arc.source
            print(f"    - {arc.id}: {place.name} (ID: {place.id})")
            print(f"        is_signal_place: {getattr(place, 'is_signal_place', False)}")
            print(f"        signal_type: {getattr(place, 'signal_type', None)}")
            print(f"        compartment_volume: {getattr(place, 'compartment_volume', None)} fL")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY:")
    print(f"  Model has {len(document.transitions)} transitions")
    print(f"  Model has {len(document.places)} places")
    print(f"  Model has {len(document.arcs)} arcs")


if __name__ == "__main__":
    model_path = "/home/simao/projetos/shypn/workspace/projects/My_Project/drug_discovery/models/normal/macrocycle_transport_normal_nme_0_thermo.shy"
    diagnose_adaptive_connections(model_path)
