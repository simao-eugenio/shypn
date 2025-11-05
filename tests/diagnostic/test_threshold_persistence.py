#!/usr/bin/env python3
"""Test that arc threshold values are saved and loaded correctly."""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.inhibitor_arc import InhibitorArc


def test_arc_threshold_persistence():
    """Test that threshold is saved and restored correctly."""
    print("Testing Arc Threshold Persistence...")
    print("=" * 60)
    
    # Create objects
    p1 = Place(0, 0, id="1", name="P1", label="Source")
    p2 = Place(100, 0, id="2", name="P2", label="Target")
    t1 = Transition(50, 0, id="1", name="T1", label="Process")
    
    # Create arc with threshold
    arc = Arc(p1, t1, id="1", name="A1", weight=5)
    arc.threshold = 10  # Set threshold different from weight
    
    print(f"\n1. Created Arc:")
    print(f"   - ID: {arc.id}, Name: {arc.name}")
    print(f"   - Weight: {arc.weight}")
    print(f"   - Threshold: {arc.threshold}")
    print(f"   - Source: {arc.source.name} → Target: {arc.target.name}")
    
    # Serialize
    places_dict = {"1": p1, "2": p2}
    transitions_dict = {"1": t1}
    
    data = arc.to_dict()
    print(f"\n2. Serialized to dict:")
    print(f"   {json.dumps(data, indent=3)}")
    
    # Check threshold is in serialized data
    if "threshold" in data:
        print(f"\n   ✅ PASS: 'threshold' found in serialized data")
        print(f"   Value: {data['threshold']}")
    else:
        print(f"\n   ❌ FAIL: 'threshold' NOT found in serialized data")
        return False
    
    # Deserialize
    restored_arc = Arc.from_dict(data, places_dict, transitions_dict)
    
    print(f"\n3. Restored Arc:")
    print(f"   - ID: {restored_arc.id}, Name: {restored_arc.name}")
    print(f"   - Weight: {restored_arc.weight}")
    print(f"   - Threshold: {restored_arc.threshold}")
    
    # Verify restoration
    if restored_arc.threshold == 10:
        print(f"\n   ✅ PASS: Threshold correctly restored (10)")
    else:
        print(f"\n   ❌ FAIL: Threshold not restored correctly")
        print(f"   Expected: 10, Got: {restored_arc.threshold}")
        return False
    
    # Test with None threshold
    arc2 = Arc(p1, t1, id="2", name="A2", weight=5)
    arc2.threshold = None
    
    print(f"\n4. Testing None threshold:")
    print(f"   - Arc threshold: {arc2.threshold}")
    
    data2 = arc2.to_dict()
    if "threshold" in data2 and data2["threshold"] is None:
        print(f"   ✅ PASS: None threshold saved correctly")
    else:
        print(f"   ❌ FAIL: None threshold not handled correctly")
        return False
    
    restored_arc2 = Arc.from_dict(data2, places_dict, transitions_dict)
    if restored_arc2.threshold is None:
        print(f"   ✅ PASS: None threshold restored correctly")
    else:
        print(f"   ❌ FAIL: None threshold not restored correctly")
        return False
    
    # Test inhibitor arc
    print(f"\n5. Testing InhibitorArc with threshold:")
    inhib_arc = InhibitorArc(p2, t1, id="3", name="A3", weight=3)
    inhib_arc.threshold = 15
    
    print(f"   - Weight: {inhib_arc.weight}")
    print(f"   - Threshold: {inhib_arc.threshold}")
    
    inhib_data = inhib_arc.to_dict()
    if "threshold" in inhib_data and inhib_data["threshold"] == 15:
        print(f"   ✅ PASS: InhibitorArc threshold saved")
    else:
        print(f"   ❌ FAIL: InhibitorArc threshold not saved")
        return False
    
    restored_inhib = InhibitorArc.from_dict(inhib_data, places_dict, transitions_dict)
    if restored_inhib.threshold == 15:
        print(f"   ✅ PASS: InhibitorArc threshold restored")
    else:
        print(f"   ❌ FAIL: InhibitorArc threshold not restored")
        return False
    
    print(f"\n" + "=" * 60)
    print(f"✅ ALL TESTS PASSED - Threshold persistence working!")
    print(f"=" * 60)
    return True


if __name__ == "__main__":
    success = test_arc_threshold_persistence()
    sys.exit(0 if success else 1)
