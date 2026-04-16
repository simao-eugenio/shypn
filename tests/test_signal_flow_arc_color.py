#!/usr/bin/env python3
"""Test SignalFlowArc color persistence.

This test verifies that SignalFlowArcs maintain their light gray color
(0.7, 0.7, 0.7) after being saved and reloaded from JSON.
"""

import json
import tempfile
from pathlib import Path


def test_signal_flow_arc_color_persistence():
    """Test that SignalFlowArc color persists correctly."""
    from shypn.netobjs.place import Place
    from shypn.netobjs.transition import Transition
    from shypn.netobjs.signal_flow_arc import SignalFlowArc
    
    print("\n" + "="*70)
    print("Testing SignalFlowArc Color Persistence")
    print("="*70)
    
    # Create signal place
    signal_place = Place(
        x=100,
        y=100,
        id="P1",
        name="P1",
        label="ATP"
    )
    signal_place.is_signal_place = True
    signal_place.tokens = 10
    
    # Create transition
    transition = Transition(
        x=200,
        y=100,
        id="T1",
        name="T1",
        label="Reaction"
    )
    
    # Create signal flow arc
    arc = SignalFlowArc(
        source=signal_place,
        target=transition,
        id="A1",
        name="A1",
        weight=1.0
    )
    
    print(f"\n1. Created SignalFlowArc")
    print(f"   Initial color: {arc.color}")
    print(f"   Expected: (0.7, 0.7, 0.7)")
    assert arc.color == (0.7, 0.7, 0.7), f"Initial color should be light gray, got {arc.color}"
    print("   ✓ Initial color is correct")
    
    # Serialize to dict
    arc_data = arc.to_dict()
    print(f"\n2. Serialized to dict")
    print(f"   arc_type: {arc_data.get('arc_type')}")
    print(f"   color: {arc_data.get('color')}")
    assert arc_data.get('arc_type') == 'signal_flow', f"arc_type should be 'signal_flow', got {arc_data.get('arc_type')}"
    assert arc_data.get('color') == [0.7, 0.7, 0.7], f"Serialized color should be [0.7, 0.7, 0.7], got {arc_data.get('color')}"
    print("   ✓ Serialized color is correct")
    
    # Save to JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(arc_data, f, indent=2)
        temp_file = f.name
    
    print(f"\n3. Saved to temporary file: {temp_file}")
    
    # Load from JSON file
    with open(temp_file, 'r') as f:
        loaded_data = json.load(f)
    
    print(f"\n4. Loaded from file")
    print(f"   arc_type: {loaded_data.get('arc_type')}")
    print(f"   color: {loaded_data.get('color')}")
    assert loaded_data.get('color') == [0.7, 0.7, 0.7], f"Loaded color should be [0.7, 0.7, 0.7], got {loaded_data.get('color')}"
    print("   ✓ Loaded color is correct")
    
    # Deserialize back to SignalFlowArc
    places = {"P1": signal_place}
    transitions = {"T1": transition}
    
    # Use Arc.from_dict which handles subclass creation
    from shypn.netobjs.arc import Arc
    restored_arc = Arc.from_dict(loaded_data, places, transitions)
    
    print(f"\n5. Deserialized back to object")
    print(f"   Type: {type(restored_arc).__name__}")
    print(f"   arc_type: {restored_arc.arc_type}")
    print(f"   color: {restored_arc.color}")
    
    # Verify type
    assert isinstance(restored_arc, SignalFlowArc), f"Should be SignalFlowArc, got {type(restored_arc).__name__}"
    print("   ✓ Type is correct (SignalFlowArc)")
    
    # Verify color
    assert restored_arc.color == (0.7, 0.7, 0.7), f"Restored color should be (0.7, 0.7, 0.7), got {restored_arc.color}"
    print("   ✓ Restored color is correct")
    
    # Cleanup
    Path(temp_file).unlink()
    
    print("\n" + "="*70)
    print("✓ All tests passed!")
    print("="*70 + "\n")


if __name__ == '__main__':
    test_signal_flow_arc_color_persistence()
