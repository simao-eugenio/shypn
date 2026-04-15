#!/usr/bin/env python3
"""Diagnostic script for T5 and T6 not firing in enhanced drug discovery model."""

import sys
import json
from pathlib import Path

# Add shypn to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.document_model import DocumentModel
from shypn.engine.simulation.settings import SimulationSettings
from shypn.engine.simulation.controller import SimulationController

def main():
    model_path = "workspace/projects/My_Project/drug_discovery/models/manuscript/macrocycle_transport_normal_nme_0_enhanced.shy"
    
    print("="*70)
    print("DIAGNOSTIC: T5 and T6 Not Firing Issue")
    print("="*70)
    
    # Load model
    print(f"\nLoading model: {model_path}")
    with open(model_path, 'r') as f:
        data = json.load(f)
    
    model = DocumentModel()
    model.from_json_data(data)
    
    # Find T5 and T6
    t5 = None
    t6 = None
    for t in model.transitions:
        if t.name == 'chameleon_fold':
            t5 = t
        elif t.name == 'chameleon_unfold':
            t6 = t
    
    if not t5 or not t6:
        print("\n❌ ERROR: Could not find T5 or T6!")
        return
    
    print(f"\n{'='*70}")
    print("TRANSITION T5 (chameleon_fold)")
    print(f"{'='*70}")
    print(f"  Type: {t5.transition_type}")
    print(f"  Rate: {t5.rate}")
    print(f"  Properties: {getattr(t5, 'properties', {})}")
    print(f"  Enabled: {t5.enabled}")
    
    print(f"\n{'='*70}")
    print("TRANSITION T6 (chameleon_unfold)")
    print(f"{'='*70}")
    print(f"  Type: {t6.transition_type}")
    print(f"  Rate: {t6.rate}")
    print(f"  Properties: {getattr(t6, 'properties', {})}")
    print(f"  Enabled: {t6.enabled}")
    
    # Find connected places
    print(f"\n{'='*70}")
    print("CONNECTED PLACES")
    print(f"{'='*70}")
    
    for trans_name, trans in [("T5", t5), ("T6", t6)]:
        print(f"\n{trans_name} connections:")
        
        input_places = []
        output_places = []
        
        for arc in model.arcs:
            if arc.target == trans:
                place = arc.source
                input_places.append(place)
                print(f"  INPUT: {place.name}")
                print(f"    Tokens: {place.tokens}")
                print(f"    Compartment volume: {getattr(place, 'compartment_volume', 'NOT SET')}")
                print(f"    Is spatial signal: {getattr(place, 'is_signal_place', False)}")
            elif arc.source == trans:
                place = arc.target
                output_places.append(place)
                print(f"  OUTPUT: {place.name}")
                print(f"    Tokens: {place.tokens}")
                print(f"    Compartment volume: {getattr(place, 'compartment_volume', 'NOT SET')}")
    
    # Check behavior
    print(f"\n{'='*70}")
    print("CHECKING ADAPTIVE BEHAVIOR")
    print(f"{'='*70}")
    
    from shypn.engine.behavior_factory import BehaviorFactory
    factory = BehaviorFactory(model)
    
    for trans_name, trans in [("T5", t5), ("T6", t6)]:
        print(f"\n{trans_name} behavior:")
        behavior = factory.create_behavior(trans)
        print(f"  Behavior class: {behavior.__class__.__name__}")
        
        if hasattr(behavior, 'get_adaptive_info'):
            info = behavior.get_adaptive_info()
            print(f"  Volume threshold: {info.get('volume_threshold')} fL")
            print(f"  Place filter: {info.get('place_filter')}")
            print(f"  Current mode: {info.get('current_mode')}")
            
            # Try to select mode
            if hasattr(behavior, '_select_mode'):
                mode = behavior._select_mode()
                print(f"  Selected mode: {mode}")
                
                if hasattr(behavior, '_last_volume_check'):
                    volume_info = behavior._last_volume_check
                    print(f"  Volume check details:")
                    print(f"    Recommendation: {volume_info.get('recommendation')}")
                    print(f"    Reason: {volume_info.get('reason')}")
                    print(f"    Min volume: {volume_info.get('min_volume')} fL")
                    print(f"    Volumes: {volume_info.get('volumes')}")
        
        # Check enablement
        can_fire, reason = behavior.can_fire()
        print(f"  Can fire: {can_fire}")
        print(f"  Reason: {reason}")
    
    # Try simulation
    print(f"\n{'='*70}")
    print("RUNNING SHORT SIMULATION (10 seconds)")
    print(f"{'='*70}")
    
    # Record initial tokens
    p3 = model.get_place_by_name('Drug_extended')
    p4 = model.get_place_by_name('Drug_compact')
    
    print(f"\nInitial state:")
    print(f"  Drug_extended (P3): {p3.tokens:.2f} tokens (volume={getattr(p3, 'compartment_volume', 'N/A')} fL)")
    print(f"  Drug_compact (P4): {p4.tokens:.2f} tokens (volume={getattr(p4, 'compartment_volume', 'N/A')} fL)")
    
    # Simulate
    settings = SimulationSettings()
    settings.set_duration(10.0)
    settings.dt = 0.1
    
    controller = SimulationController(model, settings)
    
    print("\nRunning simulation...")
    controller.run()
    
    print(f"\nFinal state (t=10s):")
    print(f"  Drug_extended (P3): {p3.tokens:.2f} tokens")
    print(f"  Drug_compact (P4): {p4.tokens:.2f} tokens")
    
    # Check firing counts
    print(f"\n{'='*70}")
    print("FIRING STATISTICS")
    print(f"{'='*70}")
    
    t5_firings = getattr(t5, 'firing_count', 0)
    t6_firings = getattr(t6, 'firing_count', 0)
    
    print(f"  T5 (fold): {t5_firings} firings")
    print(f"  T6 (unfold): {t6_firings} firings")
    
    if t5_firings == 0 and t6_firings == 0:
        print("\n❌ CONFIRMED: T5 and T6 did not fire during simulation!")
        print("\nPOSSIBLE CAUSES:")
        print("  1. Compartment volumes < 1.0 fL → stochastic mode selected")
        print("  2. Stochastic behavior not executing correctly")
        print("  3. Enablement not being checked properly")
        print("  4. Scheduling issue in simulation controller")
    else:
        print("\n✅ Transitions fired successfully!")

if __name__ == '__main__':
    main()
