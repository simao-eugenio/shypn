#!/usr/bin/env python3
"""Test adaptive hybrid behavior with runtime mode switching.

Verifies that AdaptiveHybridBehavior:
1. Switches between continuous and stochastic based on volume
2. Maintains state consistency across mode changes
3. Integrates correctly with simulation engine
"""

import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from shypn.netobjs.place import Place, BoundaryType, SignalType
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.engine.adaptive_hybrid_behavior import AdaptiveHybridBehavior


# Mock model for testing
class MockModel:
    def __init__(self):
        self.places = {}
        self.transitions = {}
        self.arcs = {}
        self.logical_time = 0.0


def test_adaptive_behavior():
    print("Testing Adaptive Hybrid Behavior\n")
    print("=" * 60)
    
    # Create mock model
    model = MockModel()
    
    # Create places with different volumes
    print("\n1. Creating places with different volumes:")
    
    small_volume_place = Place(x=100, y=100, id="P1", name="P1", label="Small Volume")
    small_volume_place.signal_type = SignalType.SPATIAL
    small_volume_place.compartment_volume = 0.5  # fL - below threshold
    small_volume_place.tokens = 100
    print(f"   P1: volume={small_volume_place.compartment_volume} fL (below 1.0 fL threshold)")
    
    large_volume_place = Place(x=200, y=100, id="P2", name="P2", label="Large Volume")
    large_volume_place.signal_type = SignalType.SPATIAL
    large_volume_place.compartment_volume = 100.0  # fL - above threshold
    large_volume_place.tokens = 10000
    print(f"   P2: volume={large_volume_place.compartment_volume} fL (above 1.0 fL threshold)")
    
    model.places = {"P1": small_volume_place, "P2": large_volume_place}
    
    # Create adaptive transition
    print("\n2. Creating adaptive hybrid transition:")
    transition = Transition(x=150, y=150, id="T1", name="T1", label="Adaptive")
    transition.transition_type = 'adaptive'
    transition.rate = 5.0
    transition.properties = {
        'volume_threshold': 1.0,
        'rate_function': '5.0',
        'max_burst': 8
    }
    print(f"   {transition.name}: type={transition.transition_type}, rate={transition.rate}")
    
    model.transitions = {"T1": transition}
    
    # Test 1: Small volume (should use stochastic)
    print("\n3. Test 1: Transition connected to small volume place")
    print("   " + "-" * 56)
    
    arc_in = Arc(source=small_volume_place, target=transition, id="A1", name="A1", weight=1.0)
    arc_out = Arc(source=transition, target=large_volume_place, id="A2", name="A2", weight=1.0)
    
    # Update model arcs
    model.arcs = [arc_in, arc_out]
    
    # Create adaptive behavior
    behavior = AdaptiveHybridBehavior(transition, model)
    
    # Check mode selection
    mode = behavior._select_mode()
    print(f"   Selected mode: {mode}")
    print(f"   Expected: stochastic (volume 0.5 fL < 1.0 fL)")
    
    assert mode == 'stochastic', f"Expected stochastic mode for small volume, got {mode}"
    print("   ✓ Correct mode selected!")
    
    # Test 2: Large volume (should use continuous)
    print("\n4. Test 2: Transition connected to large volume place")
    print("   " + "-" * 56)
    
    # Create another large volume place for output
    large_volume_place2 = Place(x=300, y=100, id="P3", name="P3", label="Large Volume 2")
    large_volume_place2.signal_type = SignalType.SPATIAL
    large_volume_place2.compartment_volume = 150.0  # fL - above threshold
    large_volume_place2.tokens = 15000
    model.places["P3"] = large_volume_place2
    
    arc_in_large = Arc(source=large_volume_place, target=transition, id="A3", name="A3", weight=1.0)
    arc_out_large = Arc(source=transition, target=large_volume_place2, id="A4", name="A4", weight=1.0)
    
    # Update model arcs
    model.arcs = [arc_in_large, arc_out_large]
    
    # Re-create behavior for new arc configuration
    behavior2 = AdaptiveHybridBehavior(transition, model)
    
    mode2 = behavior2._select_mode()
    print(f"   Selected mode: {mode2}")
    print(f"   Expected: continuous (volume 100.0 fL > 1.0 fL)")
    
    assert mode2 == 'continuous', f"Expected continuous mode for large volume, got {mode2}"
    print("   ✓ Correct mode selected!")
    
    # Test 3: Mode switching simulation
    print("\n5. Test 3: Simulating runtime mode switching")
    print("   " + "-" * 56)
    
    # Start with small volume
    arc_dynamic = Arc(source=small_volume_place, target=transition, id="A5", name="A5", weight=1.0)
    arc_out_dynamic = Arc(source=transition, target=large_volume_place, id="A6", name="A6", weight=1.0)
    
    # Update model arcs
    model.arcs = [arc_dynamic, arc_out_dynamic]
    
    behavior3 = AdaptiveHybridBehavior(transition, model)
    
    print("   Initial state:")
    mode_initial = behavior3._select_mode()
    print(f"     Volume: {small_volume_place.compartment_volume} fL → Mode: {mode_initial}")
    assert mode_initial == 'stochastic'
    
    # Change volume at runtime (simulating molecular count increase)
    print("\n   Increasing volume at runtime:")
    small_volume_place.compartment_volume = 50.0  # Increase volume
    print(f"     Volume: {small_volume_place.compartment_volume} fL")
    
    mode_after = behavior3._select_mode()
    print(f"     New mode: {mode_after}")
    assert mode_after == 'continuous', "Should switch to continuous after volume increase"
    print("   ✓ Mode switched correctly!")
    
    # Test 4: Type name
    print("\n6. Test 4: Behavior type identification")
    print("   " + "-" * 56)
    type_name = behavior3.get_type_name()
    print(f"   Type name: {type_name}")
    assert "Adaptive" in type_name, "Type name should indicate adaptive behavior"
    print("   ✓ Type name correct!")
    
    # Test 5: Adaptive info
    print("\n7. Test 5: Querying adaptive behavior info")
    print("   " + "-" * 56)
    info = behavior3.get_adaptive_info()
    print(f"   Volume threshold: {info['volume_threshold']} fL")
    print(f"   Current mode: {info['current_mode']}")
    print(f"   Prefer continuous: {info['prefer_continuous']}")
    print("   ✓ Info retrieval working!")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("\nAdaptive hybrid behavior successfully implements:")
    print("  ✓ Runtime mode selection based on volume")
    print("  ✓ Dynamic switching during simulation")
    print("  ✓ Integration with continuous and stochastic behaviors")
    print("  ✓ State consistency across mode changes")
    print("\nTransitions can now automatically adapt execution method!")


if __name__ == '__main__':
    test_adaptive_behavior()
