#!/usr/bin/env python3
"""
Test that is_catalyst attribute is properly saved and loaded.
"""

import sys
import json
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.test_arc import TestArc


def test_catalyst_persistence():
    """Test that is_catalyst flag is saved and restored."""
    
    print("=" * 80)
    print("TEST: Catalyst Flag Persistence")
    print("=" * 80)
    
    # Create places - one normal, one catalyst
    substrate = Place(id="P1", name="Substrate", x=100, y=100)
    enzyme = Place(id="P2", name="Enzyme", x=100, y=200)
    enzyme.is_catalyst = True  # Mark as catalyst
    product = Place(id="P3", name="Product", x=300, y=100)
    
    # Create transition
    reaction = Transition(id="T1", name="Reaction", x=200, y=100)
    
    print(f"\n1. Created places:")
    print(f"   Substrate: is_catalyst = {getattr(substrate, 'is_catalyst', False)}")
    print(f"   Enzyme: is_catalyst = {getattr(enzyme, 'is_catalyst', False)}")
    print(f"   Product: is_catalyst = {getattr(product, 'is_catalyst', False)}")
    
    # Serialize to dict
    substrate_data = substrate.to_dict()
    enzyme_data = enzyme.to_dict()
    product_data = product.to_dict()
    
    print(f"\n2. Serialized to dict:")
    print(f"   Substrate: is_catalyst = {substrate_data.get('is_catalyst', 'MISSING')}")
    print(f"   Enzyme: is_catalyst = {enzyme_data.get('is_catalyst', 'MISSING')}")
    print(f"   Product: is_catalyst = {product_data.get('is_catalyst', 'MISSING')}")
    
    # Simulate save/load cycle
    substrate_loaded = Place.from_dict(substrate_data)
    enzyme_loaded = Place.from_dict(enzyme_data)
    product_loaded = Place.from_dict(product_data)
    
    print(f"\n3. Deserialized from dict:")
    print(f"   Substrate: is_catalyst = {getattr(substrate_loaded, 'is_catalyst', 'MISSING')}")
    print(f"   Enzyme: is_catalyst = {getattr(enzyme_loaded, 'is_catalyst', 'MISSING')}")
    print(f"   Product: is_catalyst = {getattr(product_loaded, 'is_catalyst', 'MISSING')}")
    
    # Verify
    success = True
    if getattr(substrate_loaded, 'is_catalyst', None) != False:
        print(f"\n❌ FAIL: Substrate should have is_catalyst=False")
        success = False
    
    if getattr(enzyme_loaded, 'is_catalyst', None) != True:
        print(f"\n❌ FAIL: Enzyme should have is_catalyst=True")
        success = False
    
    if getattr(product_loaded, 'is_catalyst', None) != False:
        print(f"\n❌ FAIL: Product should have is_catalyst=False")
        success = False
    
    if success:
        print(f"\n✅ TEST PASSED!")
        print(f"   is_catalyst flag correctly saved and restored")
        print(f"   Catalyst places will maintain proper layout when file is opened")
    
    return success


if __name__ == '__main__':
    success = test_catalyst_persistence()
    sys.exit(0 if success else 1)
