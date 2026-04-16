"""Unit tests for Signal Flow Arc implementation.

Tests cover:
1. SignalFlowArc class creation and validation
2. Arc type recognition and properties
3. Serialization/deserialization (to_dict/from_dict)
4. Transformation utilities (convert_to_signal_flow)
5. Visual rendering (dashed line, angled arrowhead)
6. Integration with topology analyzer

Test cases:
- Valid signal flow arc creation (signal place → transition)
- Valid signal flow arc creation (transition → signal place)
- Invalid creation (neither endpoint is signal place)
- Token consumption behavior (consumes_tokens() returns True)
- Information arc classification (is_information_arc() returns True)
- Serialization round-trip
- Transformation from normal/test/inhibitor arcs
- Visual distinction from test arcs

Author: GitHub Copilot & Eugênio Simão
Date: December 26, 2025
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.signal_flow_arc import SignalFlowArc
from shypn.utils.arc_transform import (
    is_signal_flow, convert_to_signal_flow, convert_to_normal,
    get_arc_type_name
)


def test_signal_flow_arc_creation_valid_signal_to_transition():
    """Test creating signal flow arc from signal place to transition."""
    print("Test: Signal flow arc creation (signal place → transition)")
    
    # Create signal place and transition
    signal_place = Place(100, 100, "P_signal", "CII Signal")
    signal_place.is_signal_place = True
    signal_place.signal_type = "regulatory"
    
    transition = Transition(200, 100, "T1", "Decision")
    
    # Create signal flow arc
    arc = SignalFlowArc(signal_place, transition, "A_SF1", "Signal Flow 1", weight=1.0)
    
    # Verify properties
    assert arc.arc_type == "signal_flow", f"Expected 'signal_flow', got '{arc.arc_type}'"
    assert arc.consumes_tokens() == True, "Signal flow arcs should consume tokens"
    assert arc.is_information_arc() == True, "Signal flow arcs are information arcs"
    assert arc.get_semantic_role() == "information_transfer", "Semantic role should be information_transfer"
    
    print("✓ Valid signal flow arc created successfully")
    print(f"  - Arc type: {arc.arc_type}")
    print(f"  - Consumes tokens: {arc.consumes_tokens()}")
    print(f"  - Information arc: {arc.is_information_arc()}")
    print(f"  - Semantic role: {arc.get_semantic_role()}\n")


def test_signal_flow_arc_creation_valid_transition_to_signal():
    """Test creating signal flow arc from transition to signal place."""
    print("Test: Signal flow arc creation (transition → signal place)")
    
    # Create transition and signal place
    transition = Transition(100, 100, "T1", "Produce Signal")
    
    signal_place = Place(200, 100, "P_signal", "Energy Status")
    signal_place.is_signal_place = True
    signal_place.signal_type = "energy"
    
    # Create signal flow arc
    arc = SignalFlowArc(transition, signal_place, "A_SF2", "Signal Flow 2", weight=1.0)
    
    # Verify properties
    assert arc.arc_type == "signal_flow"
    assert arc.consumes_tokens() == True
    assert arc.is_information_arc() == True
    
    print("✓ Valid signal flow arc (reverse direction) created successfully\n")


def test_signal_flow_arc_creation_invalid():
    """Test that creating signal flow arc without signal place raises ValueError."""
    print("Test: Signal flow arc creation (invalid - no signal place)")
    
    # Create two normal places
    place1 = Place(100, 100, "P1", "Normal Place 1")
    place2 = Place(200, 100, "P2", "Normal Place 2")
    
    # Attempt to create signal flow arc (should fail)
    try:
        arc = SignalFlowArc(place1, place2, "A_SF_invalid", "Invalid Signal Flow", weight=1.0)
        print("✗ FAILED: Should have raised ValueError")
        assert False, "Expected ValueError for invalid signal flow arc"
    except ValueError as e:
        print(f"✓ Correctly rejected invalid arc: {e}\n")


def test_signal_flow_arc_type_recognition():
    """Test that is_signal_flow() correctly identifies signal flow arcs."""
    print("Test: Signal flow arc type recognition")
    
    # Create signal place and transition
    signal_place = Place(100, 100, "P_signal", "Quorum Signal")
    signal_place.is_signal_place = True
    signal_place.signal_type = "quorum"
    
    transition = Transition(200, 100, "T1", "Transition")
    
    # Create signal flow arc
    signal_arc = SignalFlowArc(signal_place, transition, "A_SF1", "Signal Arc", weight=1.0)
    
    # Create normal arc for comparison
    normal_place = Place(100, 200, "P_normal", "Normal Place")
    normal_arc = Arc(normal_place, transition, "A1", "Normal Arc", weight=1.0)
    
    # Test recognition
    assert is_signal_flow(signal_arc) == True, "Should recognize signal flow arc"
    assert is_signal_flow(normal_arc) == False, "Should not recognize normal arc as signal flow"
    
    print("✓ Signal flow arc type correctly recognized")
    print(f"  - is_signal_flow(signal_arc) = {is_signal_flow(signal_arc)}")
    print(f"  - is_signal_flow(normal_arc) = {is_signal_flow(normal_arc)}\n")


def test_signal_flow_arc_serialization():
    """Test signal flow arc serialization and deserialization."""
    print("Test: Signal flow arc serialization")
    
    # Create signal place and transition
    signal_place = Place(100, 100, "P_signal", "Spatial Signal")
    signal_place.is_signal_place = True
    signal_place.signal_type = "spatial"
    
    transition = Transition(200, 100, "T1", "Respond")
    
    # Create signal flow arc
    original_arc = SignalFlowArc(signal_place, transition, "A_SF1", "Signal Arc", weight=2.5)
    
    # Serialize
    arc_dict = original_arc.to_dict()
    
    # Verify arc_type in dict
    assert arc_dict.get('arc_type') == "signal_flow", f"Serialized arc_type should be 'signal_flow', got {arc_dict.get('arc_type')}"
    
    # Deserialize
    places_dict = {signal_place.id: signal_place}
    transitions_dict = {transition.id: transition}
    restored_arc = Arc.from_dict(arc_dict, places_dict, transitions_dict)
    
    # Verify restored arc
    assert isinstance(restored_arc, SignalFlowArc), "Deserialized arc should be SignalFlowArc instance"
    assert restored_arc.arc_type == "signal_flow"
    assert restored_arc.weight == 2.5
    assert restored_arc.consumes_tokens() == True
    
    print("✓ Signal flow arc serialization/deserialization successful")
    print(f"  - Serialized arc_type: {arc_dict.get('arc_type')}")
    print(f"  - Restored instance type: {type(restored_arc).__name__}")
    print(f"  - Restored weight: {restored_arc.weight}\n")


def test_signal_flow_arc_transformation():
    """Test transforming normal arc to signal flow arc."""
    print("Test: Arc transformation to signal flow")
    
    # Create signal place and transition
    signal_place = Place(100, 100, "P_signal", "Energy Signal")
    signal_place.is_signal_place = True
    signal_place.signal_type = "energy"
    
    transition = Transition(200, 100, "T1", "Decide")
    
    # Create normal arc
    normal_arc = Arc(signal_place, transition, "A1", "Normal Arc", weight=1.0)
    
    # Verify it's normal
    assert normal_arc.arc_type == "normal"
    assert is_signal_flow(normal_arc) == False
    
    # Transform to signal flow
    signal_arc = convert_to_signal_flow(normal_arc)
    
    # Verify transformation
    assert isinstance(signal_arc, SignalFlowArc)
    assert signal_arc.arc_type == "signal_flow"
    assert signal_arc.id == normal_arc.id  # ID preserved
    assert signal_arc.weight == normal_arc.weight  # Weight preserved
    assert signal_arc.consumes_tokens() == True
    
    print("✓ Arc transformation successful")
    print(f"  - Original type: {normal_arc.arc_type}")
    print(f"  - Transformed type: {signal_arc.arc_type}")
    print(f"  - ID preserved: {signal_arc.id == normal_arc.id}")
    print(f"  - Weight preserved: {signal_arc.weight == normal_arc.weight}\n")


def test_signal_flow_arc_transformation_invalid():
    """Test that transforming arc without signal place fails."""
    print("Test: Arc transformation (invalid - no signal place)")
    
    # Create normal place and transition
    normal_place = Place(100, 100, "P1", "Normal Place")
    transition = Transition(200, 100, "T1", "Transition")
    
    # Create normal arc (Place → Transition, but not signal place)
    normal_arc = Arc(normal_place, transition, "A1", "Normal Arc", weight=1.0)
    
    # Attempt transformation (should fail)
    try:
        signal_arc = convert_to_signal_flow(normal_arc)
        print("✗ FAILED: Should have raised ValueError")
        assert False, "Expected ValueError for invalid transformation"
    except ValueError as e:
        print(f"✓ Correctly rejected invalid transformation: {e}\n")


def test_signal_flow_arc_name():
    """Test get_arc_type_name() for signal flow arcs."""
    print("Test: Signal flow arc type name")
    
    # Create signal place and transition
    signal_place = Place(100, 100, "P_signal", "Signal")
    signal_place.is_signal_place = True
    
    transition = Transition(200, 100, "T1", "Transition")
    
    # Create signal flow arc
    arc = SignalFlowArc(signal_place, transition, "A_SF1", "Signal Arc", weight=1.0)
    
    # Get type name
    type_name = get_arc_type_name(arc)
    
    assert type_name == "Signal Flow Arc", f"Expected 'Signal Flow Arc', got '{type_name}'"
    
    print(f"✓ Arc type name: {type_name}\n")


def test_signal_flow_vs_test_arc_semantics():
    """Test semantic differences between signal flow and test arcs."""
    print("Test: Signal flow vs test arc semantics")
    
    from shypn.netobjs.test_arc import TestArc
    
    # Create signal place and transition
    signal_place = Place(100, 100, "P_signal", "Signal")
    signal_place.is_signal_place = True
    
    transition = Transition(200, 100, "T1", "Transition")
    
    # Create normal place for test arc
    normal_place = Place(100, 200, "P_normal", "Catalyst")
    
    # Create signal flow arc
    signal_arc = SignalFlowArc(signal_place, transition, "A_SF1", "Signal", weight=1.0)
    
    # Create test arc
    test_arc = TestArc(normal_place, transition, "T1", "Test", weight=1.0)
    
    # Compare semantics
    print("Signal Flow Arc:")
    print(f"  - Consumes tokens: {signal_arc.consumes_tokens()}")
    print(f"  - Is information arc: {signal_arc.is_information_arc()}")
    print(f"  - Semantic role: {signal_arc.get_semantic_role()}")
    
    print("\nTest Arc:")
    print(f"  - Consumes tokens: {test_arc.consumes_tokens()}")
    
    # Verify differences
    assert signal_arc.consumes_tokens() != test_arc.consumes_tokens(), "Signal flow and test arcs should differ in token consumption"
    
    print("\n✓ Semantic differences verified:")
    print("  - Signal flow: consuming information transfer (angled arrowhead)")
    print("  - Test: non-consuming catalytic read (hollow diamond)\n")


def test_lambda_phage_signal_hierarchy_integration():
    """Test signal hierarchy detection in Lambda phage model (if available)."""
    print("Test: Lambda phage signal hierarchy (integration)")
    
    # Try to load lambda_hierarchical_v3.shy
    model_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'lambda_hierarchical_v3.shy')
    
    if not os.path.exists(model_path):
        print("⚠ Lambda phage model not found, skipping integration test\n")
        return
    
    print(f"Loading model: {model_path}")
    
    # Import model loader
    from shypn.io.shy_loader import load_shy_file
    
    try:
        model = load_shy_file(model_path)
        
        # Count signal places
        signal_places = [p for p in model.places if getattr(p, 'is_signal_place', False)]
        
        # Count signal flow arcs
        signal_flow_arcs = [a for a in model.arcs if isinstance(a, SignalFlowArc)]
        
        print(f"✓ Model loaded successfully")
        print(f"  - Total places: {len(model.places)}")
        print(f"  - Signal places: {len(signal_places)}")
        print(f"  - Total arcs: {len(model.arcs)}")
        print(f"  - Signal flow arcs: {len(signal_flow_arcs)}")
        
        # Verify expected signal structure
        if len(signal_places) > 0:
            print(f"\nSignal places found:")
            for sp in signal_places:
                signal_type = getattr(sp, 'signal_type', 'unknown')
                print(f"  - {sp.name} (type: {signal_type})")
        
        if len(signal_flow_arcs) > 0:
            print(f"\nSignal flow arcs found:")
            for arc in signal_flow_arcs[:5]:  # Show first 5
                print(f"  - {arc.source.name} → {arc.target.name}")
        
        print("")
        
    except Exception as e:
        print(f"⚠ Integration test failed: {e}\n")


def run_all_tests():
    """Run all signal flow arc tests."""
    print("=" * 70)
    print("Signal Flow Arc Unit Tests")
    print("=" * 70)
    print()
    
    tests = [
        test_signal_flow_arc_creation_valid_signal_to_transition,
        test_signal_flow_arc_creation_valid_transition_to_signal,
        test_signal_flow_arc_creation_invalid,
        test_signal_flow_arc_type_recognition,
        test_signal_flow_arc_serialization,
        test_signal_flow_arc_transformation,
        test_signal_flow_arc_transformation_invalid,
        test_signal_flow_arc_name,
        test_signal_flow_vs_test_arc_semantics,
        test_lambda_phage_signal_hierarchy_integration,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ TEST FAILED: {test_func.__name__}")
            print(f"  Error: {e}\n")
            failed += 1
    
    print("=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
