"""
Test Kinetics Assignment System

Tests the new OOP kinetics assignment architecture.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.netobjs.transition import Transition
from shypn.netobjs.place import Place
from shypn.heuristic import (
    KineticsAssigner,
    KineticsMetadata,
    AssignmentSource,
    ConfidenceLevel
)


def test_simple_mass_action():
    """Test simple mass action assignment."""
    print("\n=== Test 1: Simple Mass Action ===")
    
    # Create simple transition
    t = Transition(0, 0, "T1", "T1")
    
    # Create mock reaction (simple A → B)
    class MockReaction:
        name = "R1"
        id = "R1"
        reactants = [("A", 1)]
        products = [("B", 1)]
        ec_numbers = []
        enzyme = None
    
    reaction = MockReaction()
    
    # Create substrate/product places
    substrate_places = [Place(0, 0, "P1", "A")]
    product_places = [Place(0, 0, "P2", "B")]
    
    # Assign kinetics
    assigner = KineticsAssigner()
    result = assigner.assign(
        t, reaction, substrate_places, product_places, source='kegg'
    )
    
    print(f"Success: {result.success}")
    print(f"Type: {t.transition_type}")
    print(f"Rate: {t.rate}")
    print(f"Confidence: {result.confidence.value}")
    print(f"Source: {result.source.value}")
    print(f"Rule: {result.rule}")
    print(f"Message: {result.message}")
    
    # Verify
    assert result.success
    assert t.transition_type == "stochastic"
    assert result.confidence == ConfidenceLevel.LOW
    assert result.rule == "simple_mass_action"
    
    print("✓ PASSED")


def test_enzymatic_reaction():
    """Test enzymatic reaction (Michaelis-Menten)."""
    print("\n=== Test 2: Enzymatic Reaction ===")
    
    # Create transition
    t = Transition(0, 0, "T2", "T2")
    
    # Create mock reaction with EC number
    class MockReaction:
        name = "R2"
        id = "R2"
        reactants = [("Glucose", 1)]
        products = [("G6P", 1)]
        ec_numbers = ["2.7.1.1"]  # Hexokinase
        enzyme = "Hexokinase"
    
    reaction = MockReaction()
    
    # Create places
    substrate_places = [Place(0, 0, "P1", "Glucose")]
    substrate_places[0].tokens = 10.0  # Initial concentration
    product_places = [Place(0, 0, "P2", "G6P")]
    
    # Assign kinetics
    assigner = KineticsAssigner()
    result = assigner.assign(
        t, reaction, substrate_places, product_places, source='kegg'
    )
    
    print(f"Success: {result.success}")
    print(f"Type: {t.transition_type}")
    print(f"Rate Function: {t.properties.get('rate_function', 'N/A')}")
    print(f"Confidence: {result.confidence.value}")
    print(f"Source: {result.source.value}")
    print(f"Rule: {result.rule}")
    print(f"Message: {result.message}")
    
    # Verify
    assert result.success
    assert t.transition_type == "continuous"
    assert 'rate_function' in t.properties
    assert 'michaelis_menten' in t.properties['rate_function']
    assert result.confidence == ConfidenceLevel.MEDIUM
    assert result.rule == "enzymatic_mm"
    
    print("✓ PASSED")


def test_respect_user_configuration():
    """Test that user configurations are not overridden."""
    print("\n=== Test 3: Respect User Configuration ===")
    
    # Create transition with user configuration
    t = Transition(0, 0, "T3", "T3")
    t.transition_type = "stochastic"
    t.rate = 5.0
    
    # Mark as user-configured
    t.metadata = {
        'kinetics_source': 'user',
        'kinetics_confidence': 'high'
    }
    
    # Try to enhance
    class MockReaction:
        name = "R3"
        id = "R3"
        ec_numbers = ["2.7.1.1"]
        enzyme = "Test"
    
    assigner = KineticsAssigner()
    result = assigner.assign(t, MockReaction(), source='kegg')
    
    print(f"Success: {result.success}")
    print(f"Type: {t.transition_type}")
    print(f"Rate: {t.rate}")
    print(f"Message: {result.message}")
    
    # Verify NOT changed
    assert not result.success  # Enhancement skipped
    assert t.transition_type == "stochastic"  # Still user's choice
    assert t.rate == 5.0  # Still user's value
    
    print("✓ PASSED - User configuration respected!")


def test_metadata_tracking():
    """Test metadata tracking."""
    print("\n=== Test 4: Metadata Tracking ===")
    
    t = Transition(0, 0, "T4", "T4")
    
    class MockReaction:
        name = "R4"
        id = "R4"
        reactants = [("A", 1)]
        products = [("B", 1)]
        ec_numbers = []
        enzyme = None
    
    substrate_places = [Place(0, 0, "P1", "A")]
    product_places = [Place(0, 0, "P2", "B")]
    
    assigner = KineticsAssigner()
    assigner.assign(t, MockReaction(), substrate_places, product_places)
    
    # Check metadata
    source = KineticsMetadata.get_source(t)
    confidence = KineticsMetadata.get_confidence(t)
    rule = KineticsMetadata.get_rule(t)
    
    print(f"Source: {source.value}")
    print(f"Confidence: {confidence.value}")
    print(f"Rule: {rule}")
    print(f"Display: {KineticsMetadata.format_for_display(t)}")
    
    assert source == AssignmentSource.HEURISTIC
    assert confidence == ConfidenceLevel.LOW
    assert rule == "simple_mass_action"
    
    print("✓ PASSED")


def test_rollback():
    """Test rollback to original state."""
    print("\n=== Test 5: Rollback ===")
    
    # Create transition with initial state
    t = Transition(0, 0, "T5", "T5")
    t.transition_type = "continuous"
    t.rate = 1.0
    
    print(f"Original type: {t.transition_type}, rate: {t.rate}")
    
    # Enhance
    class MockReaction:
        name = "R5"
        id = "R5"
        reactants = [("A", 1)]
        products = [("B", 1)]
        ec_numbers = []
        enzyme = None
    
    substrate_places = [Place(0, 0, "P1", "A")]
    product_places = [Place(0, 0, "P2", "B")]
    
    assigner = KineticsAssigner()
    assigner.assign(t, MockReaction(), substrate_places, product_places)
    
    print(f"After enhancement: type={t.transition_type}, rate={t.rate}")
    
    # Rollback
    success = KineticsMetadata.restore_original(t)
    
    print(f"After rollback: type={t.transition_type}, rate={t.rate}")
    print(f"Rollback success: {success}")
    
    assert success
    assert t.transition_type == "continuous"
    assert t.rate == 1.0
    
    print("✓ PASSED")


if __name__ == '__main__':
    print("=" * 60)
    print("Testing Kinetics Assignment System")
    print("=" * 60)
    
    try:
        test_simple_mass_action()
        test_enzymatic_reaction()
        test_respect_user_configuration()
        test_metadata_tracking()
        test_rollback()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
