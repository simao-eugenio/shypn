#!/usr/bin/env python3
"""Test LocalityDetector with catalysts and dual-role places."""

import sys
sys.path.insert(0, 'src')

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.test_arc import TestArc
from shypn.diagnostic.locality_detector import LocalityDetector


class SimpleModel:
    """Simple model container for testing."""
    def __init__(self):
        self.places = []
        self.transitions = []
        self.arcs = []


def test_pure_catalyst():
    """Test locality detection with pure catalyst (test arc only)."""
    print("\n" + "=" * 70)
    print("TEST 1: Pure Catalyst Detection")
    print("=" * 70)
    
    model = SimpleModel()
    
    # Places
    substrate = Place(x=0, y=0, id=1, name="Glucose")
    enzyme = Place(x=100, y=0, id=2, name="Hexokinase")
    product = Place(x=200, y=0, id=3, name="Glucose-6-P")
    
    model.places = [substrate, enzyme, product]
    
    # Transition
    reaction = Transition(x=100, y=100, id=1, name="Phosphorylation")
    model.transitions = [reaction]
    
    # Arcs
    arc1 = Arc(substrate, reaction, 1, "A1", weight=1.0)  # Substrate (normal)
    arc2 = TestArc(enzyme, reaction, 2, "TA1", weight=1.0)  # Catalyst (test arc)
    arc3 = Arc(reaction, product, 3, "A2", weight=1.0)  # Product (normal)
    
    model.arcs = [arc1, arc2, arc3]
    
    # Detect locality
    detector = LocalityDetector(model)
    locality = detector.get_locality_for_transition(reaction)
    
    print(f"\nLocality for {reaction.name}:")
    print(f"  Valid: {locality.is_valid}")
    print(f"  Type: {locality.locality_type}")
    print(f"  Input places: {[p.name for p in locality.input_places]}")
    print(f"  Output places: {[p.name for p in locality.output_places]}")
    print(f"  Catalyst places: {[p.name for p in locality.catalyst_places]}")
    print(f"  Dual-role places: {[p.name for p in locality.dual_role_places]}")
    print(f"  Summary: {locality.get_summary()}")
    
    # Verify
    success = (
        len(locality.input_places) == 1 and
        len(locality.output_places) == 1 and
        len(locality.catalyst_places) == 1 and
        len(locality.dual_role_places) == 0 and
        enzyme in locality.catalyst_places
    )
    
    if success:
        print("\n✅ SUCCESS: Pure catalyst detected correctly!")
        return 0
    else:
        print("\n❌ FAILURE: Catalyst detection incorrect")
        return 1


def test_dual_role_place():
    """Test locality detection with dual-role place (catalyst + substrate)."""
    print("\n" + "=" * 70)
    print("TEST 2: Dual-Role Place Detection (Catalyst + Substrate)")
    print("=" * 70)
    print("Biological Example: AMP in yeast glycolysis")
    print("  - Reaction 1 (PFK): AMP acts as ACTIVATOR (test arc)")
    print("  - Reaction 2 (AK):  AMP acts as SUBSTRATE (normal arc)")
    
    model = SimpleModel()
    
    # Places
    f6p = Place(x=0, y=0, id=1, name="F6P")
    atp = Place(x=0, y=50, id=2, name="ATP")
    amp = Place(x=0, y=100, id=3, name="AMP")  # DUAL ROLE!
    fbp = Place(x=200, y=0, id=4, name="FBP")
    adp = Place(x=200, y=50, id=5, name="ADP")
    
    model.places = [f6p, atp, amp, fbp, adp]
    
    # Transitions
    pfk = Transition(x=100, y=25, id=1, name="PFK")  # Phosphofructokinase
    ak = Transition(x=100, y=100, id=2, name="AK")   # Adenylate kinase
    
    model.transitions = [pfk, ak]
    
    # PFK reaction: F6P + ATP --[activator: AMP]--> FBP + ADP
    arc1 = Arc(f6p, pfk, 1, "A1", weight=1.0)       # F6P substrate
    arc2 = Arc(atp, pfk, 2, "A2", weight=1.0)       # ATP substrate
    arc3 = TestArc(amp, pfk, 3, "TA1", weight=1.0)  # AMP activator (TEST ARC)
    arc4 = Arc(pfk, fbp, 4, "A3", weight=1.0)       # FBP product
    arc5 = Arc(pfk, adp, 5, "A4", weight=1.0)       # ADP product
    
    # AK reaction: ATP + AMP --> 2 ADP
    arc6 = Arc(atp, ak, 6, "A5", weight=1.0)        # ATP substrate
    arc7 = Arc(amp, ak, 7, "A6", weight=1.0)        # AMP substrate (NORMAL ARC)
    arc8 = Arc(ak, adp, 8, "A7", weight=2.0)        # ADP product
    
    model.arcs = [arc1, arc2, arc3, arc4, arc5, arc6, arc7, arc8]
    
    # Detect locality for PFK
    detector = LocalityDetector(model)
    locality_pfk = detector.get_locality_for_transition(pfk)
    
    print(f"\nLocality for {pfk.name} (Phosphofructokinase):")
    print(f"  Valid: {locality_pfk.is_valid}")
    print(f"  Type: {locality_pfk.locality_type}")
    print(f"  Input places: {[p.name for p in locality_pfk.input_places]}")
    print(f"  Output places: {[p.name for p in locality_pfk.output_places]}")
    print(f"  Catalyst places: {[p.name for p in locality_pfk.catalyst_places]}")
    print(f"  Dual-role places: {[p.name for p in locality_pfk.dual_role_places]}")
    print(f"  Summary: {locality_pfk.get_summary()}")
    
    # Detect locality for AK
    locality_ak = detector.get_locality_for_transition(ak)
    
    print(f"\nLocality for {ak.name} (Adenylate Kinase):")
    print(f"  Valid: {locality_ak.is_valid}")
    print(f"  Type: {locality_ak.locality_type}")
    print(f"  Input places: {[p.name for p in locality_ak.input_places]}")
    print(f"  Output places: {[p.name for p in locality_ak.output_places]}")
    print(f"  Catalyst places: {[p.name for p in locality_ak.catalyst_places]}")
    print(f"  Dual-role places: {[p.name for p in locality_ak.dual_role_places]}")
    print(f"  Summary: {locality_ak.get_summary()}")
    
    # Now check for dual-role globally
    print(f"\n🔍 Dual-Role Analysis:")
    print(f"  AMP appears in:")
    print(f"    - PFK locality as: {'CATALYST' if amp in locality_pfk.catalyst_places else 'NOT catalyst'}")
    print(f"    - AK locality as:  {'SUBSTRATE' if amp in locality_ak.input_places else 'NOT substrate'}")
    
    # For proper dual-role detection, we need to check if the SAME place
    # has both a test arc and a normal arc TO THE SAME TRANSITION
    # In this example, AMP has test arc to PFK and normal arc to AK (different transitions)
    # So it's NOT dual-role in a single reaction, but dual-role across the model
    
    print(f"\n  Note: In this model, AMP has dual roles ACROSS DIFFERENT reactions:")
    print(f"    - Catalyst in PFK (not consumed)")
    print(f"    - Substrate in AK (consumed)")
    print(f"    This is biochemically valid!")
    
    # Verify PFK has AMP as catalyst (not dual-role in same reaction)
    success = (
        len(locality_pfk.catalyst_places) == 1 and
        amp in locality_pfk.catalyst_places and
        len(locality_pfk.dual_role_places) == 0  # No dual-role in single reaction
    )
    
    if success:
        print("\n✅ SUCCESS: Catalyst detection works correctly!")
        return 0
    else:
        print("\n❌ FAILURE: Catalyst detection incorrect")
        return 1


def test_true_dual_role():
    """Test with a place that is BOTH catalyst AND substrate in SAME reaction."""
    print("\n" + "=" * 70)
    print("TEST 3: True Dual-Role in Same Reaction")
    print("=" * 70)
    print("Unusual case: Same species acts as both catalyst and substrate")
    
    model = SimpleModel()
    
    # Places
    substrate = Place(x=0, y=0, id=1, name="Substrate")
    mixed = Place(x=50, y=50, id=2, name="MixedRole")  # Catalyst AND substrate!
    product = Place(x=200, y=0, id=3, name="Product")
    
    model.places = [substrate, mixed, product]
    
    # Transition
    reaction = Transition(x=100, y=50, id=1, name="UnusualReaction")
    model.transitions = [reaction]
    
    # Arcs - MixedRole has BOTH test arc (catalyst) and normal arc (substrate)
    arc1 = Arc(substrate, reaction, 1, "A1", weight=1.0)      # Substrate
    arc2 = TestArc(mixed, reaction, 2, "TA1", weight=1.0)     # Catalyst role
    arc3 = Arc(mixed, reaction, 3, "A2", weight=1.0)          # Substrate role (SAME PLACE!)
    arc4 = Arc(reaction, product, 4, "A3", weight=1.0)        # Product
    
    model.arcs = [arc1, arc2, arc3, arc4]
    
    # Detect locality
    detector = LocalityDetector(model)
    locality = detector.get_locality_for_transition(reaction)
    
    print(f"\nLocality for {reaction.name}:")
    print(f"  Valid: {locality.is_valid}")
    print(f"  Input places: {[p.name for p in locality.input_places]}")
    print(f"  Output places: {[p.name for p in locality.output_places]}")
    print(f"  Catalyst places: {[p.name for p in locality.catalyst_places]}")
    print(f"  Dual-role places: {[p.name for p in locality.dual_role_places]}")
    print(f"  Summary: {locality.get_summary()}")
    
    # Verify
    success = (
        len(locality.catalyst_places) == 1 and
        len(locality.dual_role_places) == 1 and
        mixed in locality.catalyst_places and
        mixed in locality.input_places and
        mixed in locality.dual_role_places
    )
    
    if success:
        print("\n✅ SUCCESS: Dual-role place detected correctly!")
        print(f"   {mixed.name} is both catalyst AND substrate in same reaction")
        return 0
    else:
        print("\n❌ FAILURE: Dual-role detection incorrect")
        return 1


def test_multiple_catalysts():
    """Test with multiple catalysts."""
    print("\n" + "=" * 70)
    print("TEST 4: Multiple Catalysts")
    print("=" * 70)
    
    model = SimpleModel()
    
    # Places
    substrate = Place(x=0, y=0, id=1, name="Substrate")
    enzyme1 = Place(x=0, y=50, id=2, name="Enzyme1")
    cofactor = Place(x=0, y=100, id=3, name="Cofactor")
    product = Place(x=200, y=0, id=4, name="Product")
    
    model.places = [substrate, enzyme1, cofactor, product]
    
    # Transition
    reaction = Transition(x=100, y=50, id=1, name="ComplexReaction")
    model.transitions = [reaction]
    
    # Arcs - Multiple test arcs
    arc1 = Arc(substrate, reaction, 1, "A1", weight=1.0)
    arc2 = TestArc(enzyme1, reaction, 2, "TA1", weight=1.0)   # Catalyst 1
    arc3 = TestArc(cofactor, reaction, 3, "TA2", weight=1.0)  # Catalyst 2
    arc4 = Arc(reaction, product, 4, "A2", weight=1.0)
    
    model.arcs = [arc1, arc2, arc3, arc4]
    
    # Detect locality
    detector = LocalityDetector(model)
    locality = detector.get_locality_for_transition(reaction)
    
    print(f"\nLocality for {reaction.name}:")
    print(f"  Valid: {locality.is_valid}")
    print(f"  Input places: {[p.name for p in locality.input_places]}")
    print(f"  Output places: {[p.name for p in locality.output_places]}")
    print(f"  Catalyst places: {[p.name for p in locality.catalyst_places]}")
    print(f"  Catalyst count: {locality.catalyst_count}")
    print(f"  Summary: {locality.get_summary()}")
    
    # Verify
    success = (
        len(locality.catalyst_places) == 2 and
        locality.catalyst_count == 2 and
        enzyme1 in locality.catalyst_places and
        cofactor in locality.catalyst_places
    )
    
    if success:
        print("\n✅ SUCCESS: Multiple catalysts detected correctly!")
        return 0
    else:
        print("\n❌ FAILURE: Multiple catalyst detection incorrect")
        return 1


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("TESTING LOCALITY DETECTOR - CATALYST & DUAL-ROLE DETECTION")
    print("=" * 70)
    
    results = []
    results.append(("Pure Catalyst", test_pure_catalyst()))
    results.append(("Dual-Role Across Reactions", test_dual_role_place()))
    results.append(("True Dual-Role Same Reaction", test_true_dual_role()))
    results.append(("Multiple Catalysts", test_multiple_catalysts()))
    
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    
    for test_name, result in results:
        status = "✅ PASS" if result == 0 else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    total_passed = sum(1 for _, r in results if r == 0)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    sys.exit(0 if total_passed == len(results) else 1)
