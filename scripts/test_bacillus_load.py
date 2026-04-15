#!/usr/bin/env python3
"""
Quick test: Load Bacillus model and verify structure

This script validates that the model can be loaded by SHYPN's
document loader and that all key components are accessible.
"""

import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / 'src'))

from shypn.data.canvas.document_model import DocumentModel


def test_load_bacillus():
    """Load and inspect Bacillus sporulation model."""
    
    model_path = repo_root / 'workspace/projects/My_Project/thermodynamics/bacillus_sporulation.shy'
    
    print("=" * 80)
    print("BACILLUS SUBTILIS MODEL - LOAD TEST")
    print("=" * 80)
    print(f"\nLoading: {model_path}")
    
    try:
        # Load model
        doc = DocumentModel.load_from_file(str(model_path))
        
        print("✅ Model loaded successfully!")
        
        # Extract components
        print("\n" + "-" * 80)
        print("MODEL COMPONENTS")
        print("-" * 80)
        
        places = doc.places
        transitions = doc.transitions
        arcs = doc.arcs
        
        print(f"Places: {len(places)}")
        print(f"Transitions: {len(transitions)}")
        print(f"Arcs: {len(arcs)}")
        
        # Check signal places by layer
        print("\n" + "-" * 80)
        print("SIGNAL HIERARCHY")
        print("-" * 80)
        
        signal_places = [p for p in places if p.is_signal_place]
        print(f"Signal places: {len(signal_places)}")
        
        layers = {}
        for place in signal_places:
            layer = place.metadata.get('hierarchy_layer')
            if layer is not None:
                if layer not in layers:
                    layers[layer] = []
                layers[layer].append(place.name)
        
        for layer in sorted(layers.keys()):
            print(f"\n  Layer {layer}: {len(layers[layer])} places")
            for name in sorted(layers[layer])[:3]:  # Show first 3
                print(f"    - {name}")
            if len(layers[layer]) > 3:
                print(f"    ... and {len(layers[layer]) - 3} more")
        
        # Check energy places
        print("\n" + "-" * 80)
        print("ENERGY BUDGET")
        print("-" * 80)
        
        atp = next((p for p in places if 'ATP_pool' in p.name), None)
        gtp = next((p for p in places if 'GTP_pool' in p.name), None)
        
        if atp:
            print(f"ATP pool: {atp.initial_marking} tokens (id={atp.id})")
        if gtp:
            print(f"GTP pool: {gtp.initial_marking} tokens (id={gtp.id})")
        
        # Check signal flow arcs
        print("\n" + "-" * 80)
        print("SIGNAL FLOW ARCS")
        print("-" * 80)
        
        arc_types = {}
        for arc in arcs:
            arc_type = arc.arc_type
            arc_types[arc_type] = arc_types.get(arc_type, 0) + 1
        
        for arc_type, count in sorted(arc_types.items()):
            print(f"  {arc_type}: {count}")
        
        # Check energy consumption
        if atp:
            energy_arcs = [
                arc for arc in arcs
                if arc.source_id == atp.id and arc.arc_type == 'signal_flow'
            ]
            print(f"\nSignal flow arcs from ATP: {len(energy_arcs)}")
        
        if gtp:
            gtp_arcs = [
                arc for arc in arcs
                if arc.source_id == gtp.id and arc.arc_type == 'signal_flow'
            ]
            print(f"Signal flow arcs from GTP: {len(gtp_arcs)}")
        
        # Summary
        print("\n" + "=" * 80)
        print("✅ LOAD TEST PASSED - Model structure verified")
        print("=" * 80)
        print("\nReady for simulation!")
        print("Next step: Open in SHYPN GUI and run scenario tests")
        
        return True
        
    except Exception as e:
        print(f"\n❌ LOAD TEST FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_load_bacillus()
    sys.exit(0 if success else 1)
