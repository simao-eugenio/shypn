#!/usr/bin/env python3
"""
Test script for source/sink markers on transitions.

Tests:
1. Create transition with source/sink markers
2. Serialize to dict
3. Deserialize from dict
4. Verify properties preserved
"""

import sys
import os

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from shypn.netobjs.transition import Transition


def test_source_sink_serialization():
    """Test that source/sink properties serialize and deserialize correctly."""
    print("Testing source/sink marker serialization...")
    
    # Create a transition with source marker
    t1 = Transition(x=100, y=100, id=1, name="T1", label="Source Transition")
    t1.is_source = True
    t1.is_sink = False
    
    # Serialize
    data1 = t1.to_dict()
    print(f"\nOriginal transition T1:")
    print(f"  is_source: {t1.is_source}")
    print(f"  is_sink: {t1.is_sink}")
    print(f"  Serialized: is_source={data1.get('is_source')}, is_sink={data1.get('is_sink')}")
    
    # Deserialize
    t1_restored = Transition.from_dict(data1)
    print(f"  Restored: is_source={t1_restored.is_source}, is_sink={t1_restored.is_sink}")
    
    assert t1_restored.is_source == True, "Source marker not restored!"
    assert t1_restored.is_sink == False, "Sink marker incorrect!"
    print("  ✓ Source transition serialization OK")
    
    # Create a transition with sink marker
    t2 = Transition(x=200, y=100, id=2, name="T2", label="Sink Transition")
    t2.is_source = False
    t2.is_sink = True
    
    # Serialize
    data2 = t2.to_dict()
    print(f"\nOriginal transition T2:")
    print(f"  is_source: {t2.is_source}")
    print(f"  is_sink: {t2.is_sink}")
    print(f"  Serialized: is_source={data2.get('is_source')}, is_sink={data2.get('is_sink')}")
    
    # Deserialize
    t2_restored = Transition.from_dict(data2)
    print(f"  Restored: is_source={t2_restored.is_source}, is_sink={t2_restored.is_sink}")
    
    assert t2_restored.is_source == False, "Source marker incorrect!"
    assert t2_restored.is_sink == True, "Sink marker not restored!"
    print("  ✓ Sink transition serialization OK")
    
    # Create a transition with both markers
    t3 = Transition(x=300, y=100, id=3, name="T3", label="Source+Sink Transition")
    t3.is_source = True
    t3.is_sink = True
    
    # Serialize
    data3 = t3.to_dict()
    print(f"\nOriginal transition T3:")
    print(f"  is_source: {t3.is_source}")
    print(f"  is_sink: {t3.is_sink}")
    print(f"  Serialized: is_source={data3.get('is_source')}, is_sink={data3.get('is_sink')}")
    
    # Deserialize
    t3_restored = Transition.from_dict(data3)
    print(f"  Restored: is_source={t3_restored.is_source}, is_sink={t3_restored.is_sink}")
    
    assert t3_restored.is_source == True, "Source marker not restored!"
    assert t3_restored.is_sink == True, "Sink marker not restored!"
    print("  ✓ Source+Sink transition serialization OK")
    
    # Create a transition with default (no markers)
    t4 = Transition(x=400, y=100, id=4, name="T4", label="Normal Transition")
    
    # Serialize
    data4 = t4.to_dict()
    print(f"\nOriginal transition T4:")
    print(f"  is_source: {t4.is_source}")
    print(f"  is_sink: {t4.is_sink}")
    print(f"  Serialized: is_source={data4.get('is_source')}, is_sink={data4.get('is_sink')}")
    
    # Deserialize
    t4_restored = Transition.from_dict(data4)
    print(f"  Restored: is_source={t4_restored.is_source}, is_sink={t4_restored.is_sink}")
    
    assert t4_restored.is_source == False, "Source marker should be False!"
    assert t4_restored.is_sink == False, "Sink marker should be False!"
    print("  ✓ Normal transition serialization OK")
    
    print("\n✅ All serialization tests passed!")


def test_backward_compatibility():
    """Test that old files without source/sink still load correctly."""
    print("\nTesting backward compatibility (old file format)...")
    
    # Simulate old file format (no is_source/is_sink fields)
    old_data = {
        "type": "transition",
        "id": 5,
        "name": "T5",
        "label": "Old Transition",
        "x": 500,
        "y": 100,
        "width": 50.0,
        "height": 25.0,
        "horizontal": True,
        "enabled": True,
        "fill_color": [0.0, 0.0, 0.0],
        "border_color": [0.0, 0.0, 0.0],
        "border_width": 3.0,
        "transition_type": "immediate",
        "priority": 0
        # Note: no is_source or is_sink fields
    }
    
    # Load old format
    t5 = Transition.from_dict(old_data)
    print(f"  Loaded old format transition:")
    print(f"    is_source: {t5.is_source}")
    print(f"    is_sink: {t5.is_sink}")
    
    # Should default to False
    assert t5.is_source == False, "Old format should default is_source to False!"
    assert t5.is_sink == False, "Old format should default is_sink to False!"
    print("  ✓ Backward compatibility OK")


if __name__ == '__main__':
    test_source_sink_serialization()
    test_backward_compatibility()
    print("\n🎉 All tests passed! Source/Sink markers are working correctly.")
