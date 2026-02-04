#!/usr/bin/env python3
"""Test adaptive transition with volume < 1.0 (stochastic mode)."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.settings import SimulationSettings
from shypn.engine.simulation.controller import SimulationController
from shypn.engine.behavior_factory import create_behavior

def main():
    model_path = "workspace/projects/My_Project/models/p-t-p.shy"
    
    print("="*70)
    print("TEST: Adaptive Transition with Stochastic Mode (volume=0.8 fL)")
    print("="*70)
    
    # Load model
    with open(model_path, 'r') as f:
        data = json.load(f)
    
    model = DocumentModel()
    model.from_json_data(data)
    
    # Get objects
    p1 = model.get_place_by_name('P1')
    p2 = model.get_place_by_name('P2')
    t1 = model.get_transition_by_name('T1')
    
    print(f"\nInitial Configuration:")
    print(f"  P1: {p1.tokens} tokens, volume={getattr(p1, 'compartment_volume', 'N/A')} fL")
    print(f"  P2: {p2.tokens} tokens, volume={getattr(p2, 'compartment_volume', 'N/A')} fL")
    print(f"  T1: type={t1.transition_type}, rate={t1.rate}")
    
    # Check behavior
    behavior = create_behavior(t1, model)
    
    print(f"\nBehavior: {behavior.__class__.__name__}")
    
    if hasattr(behavior, 'get_adaptive_info'):
        info = behavior.get_adaptive_info()
        print(f"  Volume threshold: {info.get('volume_threshold')} fL")
        print(f"  Place filter: {info.get('place_filter')}")
        
        # Select mode
        mode = behavior._select_mode()
        print(f"  Selected mode: {mode}")
        
        volume_check = behavior._last_volume_check
        print(f"\n  Volume Check:")
        print(f"    Recommendation: {volume_check.get('recommendation')}")
        print(f"    Min volume: {volume_check.get('min_volume')} fL")
        print(f"    Threshold: {volume_check.get('threshold')} fL")
        print(f"    Reason: {volume_check.get('reason')}")
    
    # Check enablement
    can_fire, reason = behavior.can_fire()
    print(f"\n  Can fire: {can_fire}")
    print(f"  Reason: {reason}")
    
    # Run simulation
    print("\n" + "="*70)
    print("SIMULATION (10 seconds)")
    print("="*70)
    
    settings = SimulationSettings()
    settings.set_duration(10.0)
    settings.dt = 0.1
    
    print(f"\nBefore: P1={p1.tokens:.2f}, P2={p2.tokens:.2f}")
    
    controller = SimulationController(model, settings)
    controller.run()
    
    print(f"After:  P1={p1.tokens:.2f}, P2={p2.tokens:.2f}")
    print(f"Total:  {p1.tokens + p2.tokens:.2f} tokens")
    
    # Analysis
    p2_change = p2.tokens
    
    print("\n" + "="*70)
    print("RESULT")
    print("="*70)
    
    if p2_change > 0:
        print(f"\n✅ SUCCESS: Transition fired in stochastic mode!")
        print(f"   P2 increased by {p2_change:.2f} tokens")
        print(f"   Expected ~{1.0 * 10.0:.1f} tokens (rate × time)")
        print(f"   Efficiency: {(p2_change / 10.0) * 100:.1f}%")
        
        if abs((p1.tokens + p2.tokens) - 25.0) < 0.01:
            print("\n✅ Mass conservation: Verified")
        else:
            print(f"\n⚠️  Mass conservation: Violation ({p1.tokens + p2.tokens:.2f} vs 25.0)")
    else:
        print(f"\n❌ FAILURE: No tokens transferred!")
        print("   Transition did not fire in stochastic mode")

if __name__ == '__main__':
    main()
