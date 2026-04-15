#!/usr/bin/env python3
"""Test adaptive hybrid behavior place filtering strategies.

Verifies that different filter modes select appropriate places:
- 'inputs_only': Only checks input (substrate) places
- 'spatial_only': Only checks spatial signal places
- 'inputs_spatial': Only checks input spatial places
- 'all': Checks all connected places
"""

import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from shypn.netobjs.place import Place, BoundaryType, SignalType
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.engine.adaptive_hybrid_behavior import AdaptiveHybridBehavior


class MockModel:
    def __init__(self):
        self.places = {}
        self.transitions = {}
        self.arcs = []
        self.logical_time = 0.0


def test_filter_modes():
    print("Testing Adaptive Hybrid Behavior - Place Filtering\n")
    print("=" * 70)
    
    # Create mock model
    model = MockModel()
    
    # Create places with different characteristics
    print("\n1. Creating diverse place types:")
    print("   " + "-" * 66)
    
    # Small volume, regular place (INPUT)
    p1_small_regular = Place(x=100, y=100, id="P1", name="P1", label="Small Regular Input")
    p1_small_regular.compartment_volume = 0.3  # fL - below threshold
    p1_small_regular.tokens = 50
    print(f"   P1: volume=0.3 fL, type=regular (INPUT)")
    
    # Large volume, spatial signal (INPUT)
    p2_large_spatial = Place(x=200, y=100, id="P2", name="P2", label="Large Spatial Input")
    p2_large_spatial.signal_type = SignalType.SPATIAL
    p2_large_spatial.compartment_volume = 100.0  # fL - above threshold
    p2_large_spatial.tokens = 10000
    print(f"   P2: volume=100.0 fL, type=spatial signal (INPUT)")
    
    # Small volume, regular place (OUTPUT)
    p3_small_regular_out = Place(x=300, y=150, id="P3", name="P3", label="Small Regular Output")
    p3_small_regular_out.compartment_volume = 0.5  # fL - below threshold
    p3_small_regular_out.tokens = 0
    print(f"   P3: volume=0.5 fL, type=regular (OUTPUT)")
    
    # Large volume, spatial signal (OUTPUT)
    p4_large_spatial_out = Place(x=400, y=150, id="P4", name="P4", label="Large Spatial Output")
    p4_large_spatial_out.signal_type = SignalType.SPATIAL
    p4_large_spatial_out.compartment_volume = 150.0  # fL - above threshold
    p4_large_spatial_out.tokens = 0
    print(f"   P4: volume=150.0 fL, type=spatial signal (OUTPUT)")
    
    model.places = {
        "P1": p1_small_regular,
        "P2": p2_large_spatial,
        "P3": p3_small_regular_out,
        "P4": p4_large_spatial_out
    }
    
    # Create transition with all places connected
    transition = Transition(x=250, y=125, id="T1", name="T1", label="Adaptive")
    transition.transition_type = 'adaptive'
    transition.rate = 5.0
    model.transitions = {"T1": transition}
    
    # Connect all places
    arc1 = Arc(source=p1_small_regular, target=transition, id="A1", name="A1", weight=1.0)
    arc2 = Arc(source=p2_large_spatial, target=transition, id="A2", name="A2", weight=1.0)
    arc3 = Arc(source=transition, target=p3_small_regular_out, id="A3", name="A3", weight=1.0)
    arc4 = Arc(source=transition, target=p4_large_spatial_out, id="A4", name="A4", weight=1.0)
    model.arcs = [arc1, arc2, arc3, arc4]
    
    print("\n2. Testing filter: 'inputs_only' (DEFAULT)")
    print("   " + "-" * 66)
    transition.properties = {
        'adaptive_filter': 'inputs_only',
        'volume_threshold': 1.0,
        'rate_function': '5.0',
        'max_burst': 8
    }
    
    behavior1 = AdaptiveHybridBehavior(transition, model)
    mode1 = behavior1._select_mode()
    
    print(f"   Filter: inputs_only")
    print(f"   Checks: P1 (0.3 fL), P2 (100.0 fL)")
    print(f"   Min volume: 0.3 fL")
    print(f"   Selected mode: {mode1}")
    print(f"   Expected: stochastic (smallest input 0.3 < 1.0)")
    assert mode1 == 'stochastic', f"Expected stochastic, got {mode1}"
    print("   ✓ Correct! Uses substrate volumes only")
    
    print("\n3. Testing filter: 'all'")
    print("   " + "-" * 66)
    transition.properties['adaptive_filter'] = 'all'
    
    behavior2 = AdaptiveHybridBehavior(transition, model)
    mode2 = behavior2._select_mode()
    
    print(f"   Filter: all")
    print(f"   Checks: P1 (0.3 fL), P2 (100.0 fL), P3 (0.5 fL), P4 (150.0 fL)")
    print(f"   Min volume: 0.3 fL")
    print(f"   Selected mode: {mode2}")
    print(f"   Expected: stochastic (smallest overall 0.3 < 1.0)")
    assert mode2 == 'stochastic', f"Expected stochastic, got {mode2}"
    print("   ✓ Correct! Checks all places")
    
    print("\n4. Testing filter: 'spatial_only'")
    print("   " + "-" * 66)
    transition.properties['adaptive_filter'] = 'spatial_only'
    
    behavior3 = AdaptiveHybridBehavior(transition, model)
    mode3 = behavior3._select_mode()
    
    print(f"   Filter: spatial_only")
    print(f"   Checks: P2 (100.0 fL), P4 (150.0 fL)")
    print(f"   Min volume: 100.0 fL")
    print(f"   Selected mode: {mode3}")
    print(f"   Expected: continuous (smallest spatial 100.0 > 1.0)")
    assert mode3 == 'continuous', f"Expected continuous, got {mode3}"
    print("   ✓ Correct! Ignores regular places, only spatial signals")
    
    print("\n5. Testing filter: 'inputs_spatial'")
    print("   " + "-" * 66)
    transition.properties['adaptive_filter'] = 'inputs_spatial'
    
    behavior4 = AdaptiveHybridBehavior(transition, model)
    mode4 = behavior4._select_mode()
    
    print(f"   Filter: inputs_spatial")
    print(f"   Checks: P2 (100.0 fL) only")
    print(f"   Min volume: 100.0 fL")
    print(f"   Selected mode: {mode4}")
    print(f"   Expected: continuous (only input spatial 100.0 > 1.0)")
    assert mode4 == 'continuous', f"Expected continuous, got {mode4}"
    print("   ✓ Correct! Only input spatial signals")
    
    print("\n6. Testing biological scenario: inputs_only ignores products")
    print("   " + "-" * 66)
    
    # Scenario: Large input substrate, small output product
    p_substrate = Place(x=100, y=100, id="P5", name="P5", label="Substrate")
    p_substrate.compartment_volume = 50.0  # Large
    p_substrate.tokens = 5000
    
    p_product = Place(x=200, y=100, id="P6", name="P6", label="Product")
    p_product.compartment_volume = 0.2  # Small
    p_product.tokens = 10
    
    model.places["P5"] = p_substrate
    model.places["P6"] = p_product
    
    transition2 = Transition(x=150, y=100, id="T2", name="T2", label="Enzyme")
    transition2.transition_type = 'adaptive'
    transition2.rate = 10.0
    transition2.properties = {
        'adaptive_filter': 'inputs_only',
        'volume_threshold': 1.0,
        'rate_function': '10.0',
        'max_burst': 8
    }
    
    arc_in = Arc(source=p_substrate, target=transition2, id="A5", name="A5", weight=1.0)
    arc_out = Arc(source=transition2, target=p_product, id="A6", name="A6", weight=1.0)
    model.arcs = [arc_in, arc_out]
    
    behavior5 = AdaptiveHybridBehavior(transition2, model)
    mode5 = behavior5._select_mode()
    
    print(f"   Substrate (input): 50.0 fL (many molecules)")
    print(f"   Product (output): 0.2 fL (few molecules)")
    print(f"   With 'inputs_only': Checks substrate only → continuous")
    print(f"   Selected mode: {mode5}")
    assert mode5 == 'continuous', f"Expected continuous, got {mode5}"
    print("   ✓ Correct! Product volume doesn't affect reaction dynamics")
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED!")
    print("\nAdaptive filtering successfully implements:")
    print("  ✓ inputs_only: Substrate-driven mode selection (biologically correct)")
    print("  ✓ spatial_only: Filter by signal type")
    print("  ✓ inputs_spatial: Combined filtering")
    print("  ✓ all: Original behavior (check everything)")
    print("\nDefault 'inputs_only' is RECOMMENDED for biological accuracy!")


if __name__ == '__main__':
    test_filter_modes()
