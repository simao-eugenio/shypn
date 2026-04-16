#!/usr/bin/env python3
"""Test that adaptive transitions find their input places correctly.

This simulates what happens during simulation/batch execution:
1. Load model from file
2. Create adaptive behaviors for transitions
3. Check if they find connected places
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.adaptive_hybrid_behavior import AdaptiveHybridBehavior


def test_adaptive_place_detection(model_path):
    """Test that adaptive transitions can find their input places."""
    
    print(f"Loading model: {model_path}")
    document = DocumentModel.load_from_file(model_path)
    
    # Find adaptive transitions
    adaptive_transitions = [
        t for t in document.transitions 
        if hasattr(t, 'transition_type') and t.transition_type == 'adaptive'
    ]
    
    print(f"\nFound {len(adaptive_transitions)} adaptive transitions\n")
    
    all_passed = True
    
    for transition in adaptive_transitions:
        print(f"{'='*60}")
        print(f"Testing: {transition.name} (ID: {transition.id})")
        
        # Read configuration
        adaptive_filter = getattr(transition, 'adaptive_filter', 'all')
        volume_threshold = getattr(transition, 'volume_threshold', 0.8)
        
        print(f"  Filter: {adaptive_filter}")
        print(f"  Threshold: {volume_threshold} fL")
        
        # Create adaptive behavior (simulates what engine does)
        try:
            behavior = AdaptiveHybridBehavior(transition, document)
            
            # Try to get connected places (this is where the WARNING would occur)
            places = behavior._get_connected_places()
            
            if not places:
                print(f"  ❌ FAIL: No connected places found!")
                all_passed = False
            else:
                print(f"  ✅ PASS: Found {len(places)} connected places:")
                for place in places:
                    volume = getattr(place, 'compartment_volume', None)
                    signal_type = getattr(place, 'signal_type', None)
                    print(f"    - {place.name} (volume={volume} fL, signal_type={signal_type})")
                    
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print(f"\n{'='*60}")
    if all_passed:
        print("✅ ALL TESTS PASSED - No WARNINGs expected during simulation")
    else:
        print("❌ SOME TESTS FAILED - WARNINGs will occur during simulation")
    
    return all_passed


if __name__ == "__main__":
    model_path = "/home/simao/projetos/shypn/workspace/projects/My_Project/drug_discovery/models/normal/macrocycle_transport_normal_nme_0_thermo.shy"
    success = test_adaptive_place_detection(model_path)
    sys.exit(0 if success else 1)
