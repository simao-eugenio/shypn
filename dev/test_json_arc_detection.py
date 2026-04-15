#!/usr/bin/env python3
"""Test arc detection with model that has arcs loaded from JSON structure."""

import sys
import os
sys.path.insert(0, os.path.abspath('src'))

import json
import tempfile
from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.adaptive_hybrid_behavior import AdaptiveHybridBehavior

def test_json_arc_detection():
    print("Testing Arc Detection with JSON-loaded Model\n")
    print("=" * 70)
    
    # Create a minimal model structure as JSON
    model_json = {
        "name": "Test Model",
        "description": "Test adaptive arc detection",
        "places": [
            {
                "id": "P1",
                "name": "Substrate",
                "x": 100,
                "y": 100,
                "tokens": 100,
                "compartment_volume": 0.5,
                "signal_type": "spatial"
            },
            {
                "id": "P2",
                "name": "Product",
                "x": 300,
                "y": 100,
                "tokens": 0,
                "compartment_volume": 100.0,
                "signal_type": "spatial"
            }
        ],
        "transitions": [
            {
                "id": "T1",
                "name": "active_transport",
                "x": 200,
                "y": 100,
                "transition_type": "adaptive",
                "rate": 5.0,
                "properties": {
                    "volume_threshold": 1.0,
                    "rate_function": "5.0",
                    "max_burst": 8,
                    "adaptive_filter": "inputs_only"
                }
            }
        ],
        "arcs": [
            {
                "id": "A1",
                "name": "A1",
                "source_id": "P1",
                "source_type": "place",
                "target_id": "T1",
                "target_type": "transition",
                "weight": 1.0,
                "arc_type": "normal"
            },
            {
                "id": "A2",
                "name": "A2",
                "source_id": "T1",
                "source_type": "transition",
                "target_id": "P2",
                "target_type": "place",
                "weight": 1.0,
                "arc_type": "normal"
            }
        ]
    }
    
    # Save to temp file and load
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(model_json, f, indent=2)
        temp_file = f.name
    
    try:
        print("1. Loading model from JSON...")
        model = DocumentModel.load_from_file(temp_file)
        print(f"   Loaded: {len(model.places)} places, {len(model.transitions)} transitions, {len(model.arcs)} arcs")
        
        print("\n2. Inspecting arc structure:")
        if isinstance(model.arcs, dict):
            arcs = list(model.arcs.values())
        else:
            arcs = list(model.arcs)
        
        for arc in arcs:
            print(f"\n   Arc: {arc.name}")
            print(f"     source type: {type(arc.source)}")
            print(f"     source value: {arc.source}")
            print(f"     target type: {type(arc.target)}")
            print(f"     target value: {arc.target}")
            
            # Try to access source_id and target_id properties
            try:
                print(f"     arc.source_id: {arc.source_id}")
            except Exception as e:
                print(f"     arc.source_id ERROR: {e}")
            
            try:
                print(f"     arc.target_id: {arc.target_id}")
            except Exception as e:
                print(f"     arc.target_id ERROR: {e}")
        
        print("\n3. Testing adaptive behavior:")
        transition = list(model.transitions.values())[0] if isinstance(model.transitions, dict) else model.transitions[0]
        print(f"   Transition: {transition.name} (id={transition.id})")
        
        behavior = AdaptiveHybridBehavior(transition, model)
        
        # Try to get connected places
        print(f"\n4. Getting connected places:")
        places = behavior._get_connected_places()
        print(f"   Number of places found: {len(places)}")
        
        if not places:
            print("\n   ❌ NO PLACES FOUND - Arc detection failed!")
            print("\n   5. Manual arc detection test:")
            
            # Manually try to find arcs
            input_count = 0
            output_count = 0
            
            for arc in arcs:
                print(f"\n   Checking arc {arc.name}:")
                print(f"     Transition ID: {transition.id}")
                print(f"     Arc target: {arc.target}, type={type(arc.target)}")
                print(f"     Arc source: {arc.source}, type={type(arc.source)}")
                
                # Try comparisons
                if isinstance(arc.target, str):
                    target_match = (arc.target == transition.id)
                    print(f"     String comparison (target == trans.id): {target_match}")
                    if target_match:
                        input_count += 1
                elif hasattr(arc.target, 'id'):
                    target_match = (arc.target.id == transition.id)
                    print(f"     Object comparison (target.id == trans.id): {target_match}")
                    if target_match:
                        input_count += 1
                else:
                    print(f"     Cannot compare target")
                
                if isinstance(arc.source, str):
                    source_match = (arc.source == transition.id)
                    print(f"     String comparison (source == trans.id): {source_match}")
                    if source_match:
                        output_count += 1
                elif hasattr(arc.source, 'id'):
                    source_match = (arc.source.id == transition.id)
                    print(f"     Object comparison (source.id == trans.id): {source_match}")
                    if source_match:
                        output_count += 1
                else:
                    print(f"     Cannot compare source")
            
            print(f"\n   Manual detection results:")
            print(f"     Input arcs: {input_count}")
            print(f"     Output arcs: {output_count}")
        else:
            print("   ✓ Places found!")
            for place in places:
                print(f"     - {place.name}")
        
    finally:
        os.unlink(temp_file)


if __name__ == "__main__":
    test_json_arc_detection()
