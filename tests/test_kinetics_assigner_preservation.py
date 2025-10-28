"""
Test kinetics assigner preservation logic with new metadata.

Verifies that KineticsAssigner respects the new structured metadata
and doesn't overwrite SBML or manual kinetics.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.netobjs.transition import Transition
from shypn.data.kinetics import SBMLKineticMetadata, ManualKineticMetadata
from shypn.heuristic.metadata import KineticsMetadata


def test_assigner_respects_sbml_metadata():
    """Test that kinetics assigner respects SBML metadata."""
    print("=" * 70)
    print("Test: Kinetics Assigner Preservation Logic")
    print("=" * 70)
    
    # Test 1: Transition with SBML kinetics should NOT be enhanced
    print("\n1. Test SBML kinetics preservation")
    transition_sbml = Transition(100, 100, "T1", "T1")
    transition_sbml.kinetic_metadata = SBMLKineticMetadata(
        source_file="test.sbml",
        rate_type="michaelis_menten",
        formula="Vmax * S / (Km + S)",
        parameters={"Vmax": 10.0, "Km": 0.5}
    )
    
    should_enhance = KineticsMetadata.should_enhance(transition_sbml)
    assert should_enhance is False, "SBML kinetics should be preserved"
    print(f"   ✓ SBML kinetics preserved: should_enhance = {should_enhance}")
    print(f"   ✓ Source: {transition_sbml.kinetic_metadata.source.value}")
    print(f"   ✓ Locked: {transition_sbml.kinetic_metadata.locked}")
    
    # Test 2: Transition with manual kinetics should NOT be enhanced
    print("\n2. Test manual kinetics preservation")
    transition_manual = Transition(100, 100, "T2", "T2")
    transition_manual.kinetic_metadata = ManualKineticMetadata(
        rate_type="mass_action",
        formula="k * A * B",
        parameters={"k": 2.0},
        entered_by="user1",
        rationale="Experimental data"
    )
    
    should_enhance = KineticsMetadata.should_enhance(transition_manual)
    assert should_enhance is False, "Manual kinetics should be preserved"
    print(f"   ✓ Manual kinetics preserved: should_enhance = {should_enhance}")
    print(f"   ✓ Source: {transition_manual.kinetic_metadata.source.value}")
    print(f"   ✓ Confidence: {transition_manual.kinetic_metadata.confidence.value}")
    
    # Test 3: Transition with locked metadata should NOT be enhanced
    print("\n3. Test locked metadata preservation")
    transition_locked = Transition(100, 100, "T3", "T3")
    from shypn.data.kinetics import DatabaseKineticMetadata
    transition_locked.kinetic_metadata = DatabaseKineticMetadata(
        ec_number="2.7.1.1",
        rate_type="michaelis_menten",
        formula="Vmax * S / (Km + S)",
        parameters={"Vmax": 5.0, "Km": 0.3}
    )
    transition_locked.kinetic_metadata.locked = True
    
    should_enhance = KineticsMetadata.should_enhance(transition_locked)
    assert should_enhance is False, "Locked kinetics should be preserved"
    print(f"   ✓ Locked kinetics preserved: should_enhance = {should_enhance}")
    print(f"   ✓ Locked: {transition_locked.kinetic_metadata.locked}")
    
    # Test 4: Transition without metadata SHOULD be enhanced
    print("\n4. Test transition without metadata (should enhance)")
    transition_empty = Transition(100, 100, "T4", "T4")
    
    should_enhance = KineticsMetadata.should_enhance(transition_empty)
    assert should_enhance is True, "Empty transition should be enhanced"
    print(f"   ✓ Empty transition can be enhanced: should_enhance = {should_enhance}")
    
    # Test 5: Transition with low-confidence heuristic SHOULD be enhanced
    print("\n5. Test low-confidence metadata (should enhance)")
    transition_heuristic = Transition(100, 100, "T5", "T5")
    from shypn.data.kinetics import HeuristicKineticMetadata
    transition_heuristic.kinetic_metadata = HeuristicKineticMetadata(
        rate_type="mass_action",
        formula="k * A",
        parameters={"k": 1.0},
        heuristic_method="structure_based"
    )
    transition_heuristic.kinetic_metadata.locked = False  # Not locked
    
    should_enhance = KineticsMetadata.should_enhance(transition_heuristic)
    assert should_enhance is True, "Heuristic kinetics can be enhanced"
    print(f"   ✓ Heuristic kinetics can be enhanced: should_enhance = {should_enhance}")
    print(f"   ✓ Confidence: {transition_heuristic.kinetic_metadata.confidence.value}")
    print(f"   ✓ Locked: {transition_heuristic.kinetic_metadata.locked}")
    
    # Test 6: Legacy metadata still works
    print("\n6. Test legacy metadata compatibility")
    transition_legacy = Transition(100, 100, "T6", "T6")
    transition_legacy.metadata = {
        'kinetics_source': 'explicit',
        'kinetics_confidence': 'high'
    }
    
    should_enhance = KineticsMetadata.should_enhance(transition_legacy)
    assert should_enhance is False, "Legacy explicit source should be preserved"
    print(f"   ✓ Legacy metadata respected: should_enhance = {should_enhance}")
    print(f"   ✓ Legacy source: {transition_legacy.metadata.get('kinetics_source')}")
    
    print("\n" + "=" * 70)
    print("✓ All Preservation Tests PASSED!")
    print("=" * 70)
    print("\nSummary:")
    print("  ✓ SBML kinetics: PRESERVED (definitive confidence)")
    print("  ✓ Manual kinetics: PRESERVED (high confidence)")
    print("  ✓ Locked metadata: PRESERVED (explicit lock)")
    print("  ✓ Empty transitions: CAN BE ENHANCED")
    print("  ✓ Heuristic kinetics: CAN BE ENHANCED (medium confidence)")
    print("  ✓ Legacy metadata: STILL WORKS (backward compatible)")
    return True


if __name__ == '__main__':
    try:
        success = test_assigner_respects_sbml_metadata()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
