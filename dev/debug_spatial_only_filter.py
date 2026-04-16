#!/usr/bin/env python3
"""Debug the 'spatial_only' filter to understand why it's not working."""

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


def debug_spatial_filter():
    print("Debugging 'spatial_only' Filter\n")
    print("=" * 70)
    
    # Create mock model
    model = MockModel()
    
    # Create spatial places with large volumes
    print("\n1. Creating SPATIAL places with LARGE volumes:")
    
    p2_large_spatial = Place(x=200, y=100, id="P2", name="P2", label="Large Spatial Input")
    p2_large_spatial.signal_type = SignalType.SPATIAL
    p2_large_spatial.compartment_volume = 100.0  # fL - above threshold
    p2_large_spatial.tokens = 10000
    print(f"   P2: volume={p2_large_spatial.compartment_volume} fL, signal_type={p2_large_spatial.signal_type}")
    
    p4_large_spatial_out = Place(x=400, y=150, id="P4", name="P4", label="Large Spatial Output")
    p4_large_spatial_out.signal_type = SignalType.SPATIAL
    p4_large_spatial_out.compartment_volume = 150.0  # fL - above threshold
    p4_large_spatial_out.tokens = 0
    print(f"   P4: volume={p4_large_spatial_out.compartment_volume} fL, signal_type={p4_large_spatial_out.signal_type}")
    
    model.places = {
        "P2": p2_large_spatial,
        "P4": p4_large_spatial_out
    }
    
    # Create transition
    transition = Transition(x=250, y=125, id="T1", name="T1", label="Adaptive")
    transition.transition_type = 'adaptive'
    transition.rate = 5.0
    transition.properties = {
        'adaptive_filter': 'spatial_only',
        'volume_threshold': 1.0,
        'rate_function': '5.0',
        'max_burst': 8
    }
    model.transitions = {"T1": transition}
    
    # Connect places
    arc_in = Arc(source=p2_large_spatial, target=transition, id="A2", name="A2", weight=1.0)
    arc_out = Arc(source=transition, target=p4_large_spatial_out, id="A4", name="A4", weight=1.0)
    model.arcs = [arc_in, arc_out]
    
    print("\n2. Creating adaptive behavior with 'spatial_only' filter:")
    behavior = AdaptiveHybridBehavior(transition, model)
    
    print(f"   Filter mode: {behavior.place_filter}")
    print(f"   Volume threshold: {behavior.volume_threshold} fL")
    
    print("\n3. Getting connected places:")
    places = behavior._get_connected_places()
    print(f"   Number of places found: {len(places)}")
    for place in places:
        volume = getattr(place, 'compartment_volume', None)
        signal_type = getattr(place, 'signal_type', None)
        print(f"   - {place.name}: volume={volume} fL, signal_type={signal_type}")
    
    print("\n4. Checking volume info on places:")
    for place in places:
        has_volume = behavior._has_volume_info(place)
        volume = getattr(place, 'compartment_volume', None)
        print(f"   - {place.name}: has_volume_info={has_volume}, compartment_volume={volume}")
    
    print("\n5. Selecting mode:")
    mode = behavior._select_mode()
    print(f"   Selected mode: {mode}")
    print(f"   Expected: continuous (min volume 100.0 > threshold 1.0)")
    
    if mode == 'continuous':
        print("   ✓ CORRECT!")
    else:
        print("   ✗ WRONG! Should be continuous")
        print("\n6. Investigating volume selector:")
        use_stochastic, details = behavior.volume_selector.analyze_transition(places, [])
        print(f"   use_stochastic: {use_stochastic}")
        print(f"   details: {details}")


if __name__ == "__main__":
    debug_spatial_filter()
