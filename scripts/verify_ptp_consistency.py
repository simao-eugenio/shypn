#!/usr/bin/env python3
"""Verify consistency of simple P-T-P adaptive model."""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def main():
    model_path = "workspace/projects/My_Project/models/p-t-p.shy"
    
    print("="*70)
    print("CONSISTENCY VERIFICATION: Simple P-T-P Adaptive Model")
    print("="*70)
    
    # Load JSON
    print(f"\nLoading: {model_path}")
    with open(model_path, 'r') as f:
        data = json.load(f)
    
    # Analyze structure
    print("\n" + "="*70)
    print("MODEL STRUCTURE")
    print("="*70)
    
    places = data.get('places', [])
    transitions = data.get('transitions', [])
    arcs = data.get('arcs', [])
    
    print(f"\nPlaces: {len(places)}")
    for p in places:
        print(f"  {p['id']} ({p['name']}): {p['marking']} tokens")
        print(f"    compartment_volume: {p.get('compartment_volume')}")
        print(f"    is_signal_place: {p.get('is_signal_place')}")
        print(f"    diffusion_coefficient: {p.get('diffusion_coefficient')}")
        print(f"    boundary_type: {p.get('boundary_type')}")
        print(f"    spatial_position: {p.get('spatial_position')}")
    
    print(f"\nTransitions: {len(transitions)}")
    for t in transitions:
        print(f"  {t['id']} ({t['name']})")
        print(f"    type: {t.get('transition_type')}")
        print(f"    rate: {t.get('rate')}")
        print(f"    enabled: {t.get('enabled')}")
        props = t.get('properties', {})
        print(f"    properties:")
        print(f"      adaptive_filter: {props.get('adaptive_filter')}")
        print(f"      volume_threshold: {props.get('volume_threshold')} fL")
    
    print(f"\nArcs: {len(arcs)}")
    for a in arcs:
        print(f"  {a['id']}: {a['source_id']} → {a['target_id']} (weight={a.get('weight')})")
    
    # Expected behavior analysis
    print("\n" + "="*70)
    print("EXPECTED BEHAVIOR ANALYSIS")
    print("="*70)
    
    print("\nConfiguration:")
    print("  - P1: 25 tokens, compartment_volume=null")
    print("  - P2: 0 tokens, compartment_volume=null")
    print("  - T1: type=adaptive, rate=1.0")
    print("  - T1 properties: adaptive_filter='inputs_only', volume_threshold=1.0 fL")
    
    print("\nExpected Adaptive Behavior:")
    print("  1. T1 is type 'adaptive' → should use AdaptiveHybridBehavior")
    print("  2. adaptive_filter='inputs_only' → checks only P1 (input place)")
    print("  3. P1.compartment_volume=null → VolumeAdaptiveSelector returns continuous")
    print("  4. volume_threshold=1.0 fL → threshold for stochastic vs continuous")
    print("\nMode Selection Logic:")
    print("  - P1 has no compartment_volume set (null)")
    print("  - VolumeAdaptiveSelector.analyze_transition() will find no volumes")
    print("  - Returns: use_stochastic=False, reason='no-volumes-set'")
    print("  - Result: Continuous mode selected (default when no volumes)")
    
    print("\nPrediction:")
    print("  ✓ T1 should execute in CONTINUOUS mode")
    print("  ✓ Smooth token flow from P1 → P2")
    print("  ✓ Rate = 1.0 token/second")
    print("  ✓ After 10s: P1 ≈ 15 tokens, P2 ≈ 10 tokens (assuming dt=0.1)")
    
    # Load and test with actual engine
    print("\n" + "="*70)
    print("RUNTIME VERIFICATION")
    print("="*70)
    
    try:
        from shypn.document.document_model import DocumentModel
        from shypn.engine.simulation.settings import SimulationSettings
        from shypn.engine.simulation.controller import SimulationController
        from shypn.engine.behavior_factory import BehaviorFactory
        
        model = DocumentModel()
        model.from_json_data(data)
        
        print("\nModel loaded successfully")
        
        # Get objects
        p1 = model.get_place_by_name('P1')
        p2 = model.get_place_by_name('P2')
        t1 = model.get_transition_by_name('T1')
        
        print(f"\nPlaces:")
        print(f"  P1: {p1.tokens} tokens, volume={getattr(p1, 'compartment_volume', 'N/A')}")
        print(f"  P2: {p2.tokens} tokens, volume={getattr(p2, 'compartment_volume', 'N/A')}")
        
        # Create behavior
        factory = BehaviorFactory(model)
        behavior = factory.create_behavior(t1)
        
        print(f"\nTransition T1:")
        print(f"  Behavior class: {behavior.__class__.__name__}")
        
        if hasattr(behavior, 'get_adaptive_info'):
            info = behavior.get_adaptive_info()
            print(f"\nAdaptive Info:")
            print(f"  volume_threshold: {info.get('volume_threshold')} fL")
            print(f"  place_filter: {info.get('place_filter')}")
            print(f"  prefer_continuous: {info.get('prefer_continuous')}")
            print(f"  current_mode: {info.get('current_mode')}")
            
            # Try mode selection
            if hasattr(behavior, '_select_mode'):
                mode = behavior._select_mode()
                print(f"\nMode Selection Result: {mode}")
                
                if hasattr(behavior, '_last_volume_check'):
                    volume_check = behavior._last_volume_check
                    print(f"\nVolume Check Details:")
                    print(f"  recommendation: {volume_check.get('recommendation')}")
                    print(f"  reason: {volume_check.get('reason')}")
                    print(f"  volumes: {volume_check.get('volumes')}")
                    print(f"  min_volume: {volume_check.get('min_volume')}")
        
        # Check enablement
        can_fire, reason = behavior.can_fire()
        print(f"\nEnablement Check:")
        print(f"  can_fire: {can_fire}")
        print(f"  reason: {reason}")
        
        # Run simulation
        print("\n" + "="*70)
        print("SIMULATION TEST (10 seconds)")
        print("="*70)
        
        print(f"\nInitial: P1={p1.tokens:.2f}, P2={p2.tokens:.2f}")
        
        settings = SimulationSettings()
        settings.set_duration(10.0)
        settings.dt = 0.1
        
        controller = SimulationController(model, settings)
        controller.run()
        
        print(f"Final:   P1={p1.tokens:.2f}, P2={p2.tokens:.2f}")
        print(f"Total:   {p1.tokens + p2.tokens:.2f} tokens (conservation check)")
        
        # Analysis
        p2_change = p2.tokens - 0  # Initial P2 was 0
        
        print("\n" + "="*70)
        print("CONSISTENCY ASSESSMENT")
        print("="*70)
        
        if p2_change > 0:
            print("\n✅ SUCCESS: T1 fired and transferred tokens")
            print(f"   P2 increased by {p2_change:.2f} tokens")
            
            expected_flow = 1.0 * 10.0  # rate × time
            efficiency = (p2_change / expected_flow) * 100
            
            print(f"\n   Expected flow (rate × time): {expected_flow:.2f} tokens")
            print(f"   Actual transfer: {p2_change:.2f} tokens")
            print(f"   Efficiency: {efficiency:.1f}%")
            
            if efficiency > 95:
                print("\n✅ CONSISTENT: Continuous mode working as expected")
            elif efficiency > 50:
                print("\n⚠️  PARTIAL: Some token transfer but lower than expected")
            else:
                print("\n⚠️  INEFFICIENT: Very low token transfer")
            
            if abs((p1.tokens + p2.tokens) - 25.0) < 0.01:
                print("✅ MASS CONSERVATION: Verified")
            else:
                print("⚠️  MASS CONSERVATION: Violation detected!")
        else:
            print("\n❌ FAILURE: No token transfer occurred")
            print("   Possible issues:")
            print("   - Transition not executing")
            print("   - Wrong behavior selected")
            print("   - Enablement not working")
        
    except ImportError as e:
        print(f"\n⚠️  Cannot test runtime behavior: {e}")
        print("   Run this from SHYPN application context")
    except Exception as e:
        print(f"\n❌ ERROR during runtime test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
