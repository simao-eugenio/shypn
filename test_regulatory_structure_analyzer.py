#!/usr/bin/env python3
"""
Test suite for Regulatory Structure Analyzer.

Tests detection and analysis of:
1. Test arcs (catalysts)
2. Shared catalysts (multi-substrate enzymes)
3. Regulatory patterns
4. Validation of regulatory structure

Author: GitHub Copilot
Date: October 31, 2025
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.test_arc import TestArc
from shypn.topology.biological.regulatory_structure import RegulatoryStructureAnalyzer


# Simple mock model
class MockModel:
    """Mock model for testing."""
    def __init__(self):
        self.places = {}
        self.transitions = {}
        self.arcs = {}
    
    def add_place(self, place):
        self.places[place.id] = place
    
    def add_transition(self, transition):
        self.transitions[transition.id] = transition
    
    def add_arc(self, arc):
        self.arcs[arc.id] = arc


def create_place(id, name, x, y, tokens=0):
    """Helper to create a place with tokens."""
    p = Place(x=x, y=y, id=id, name=name)
    p.tokens = tokens
    return p


def create_transition(id, name, x, y):
    """Helper to create a transition."""
    return Transition(x=x, y=y, id=id, name=name)


def test_no_catalysts():
    """Test model with no catalysts (classical PN)."""
    print("\n" + "="*70)
    print("TEST 1: No Catalysts (Classical Petri Net)")
    print("="*70)
    
    model = MockModel()
    
    # Simple pathway without catalysts: P1 → T1 → P2
    p1 = create_place(1, "Input", 100, 100, tokens=10)
    p2 = create_place(2, "Output", 300, 100, tokens=0)
    t1 = create_transition(1, "Reaction", 200, 100)
    
    model.add_place(p1)
    model.add_place(p2)
    model.add_transition(t1)
    model.add_arc(Arc(p1, t1, 1, "A1", weight=1))
    model.add_arc(Arc(t1, p2, 2, "A2", weight=1))
    
    print("Model structure:")
    print("  Input (P1) → Reaction (T1) → Output (P2)")
    print("  (No test arcs, no catalysts)\n")
    
    # Analyze
    analyzer = RegulatoryStructureAnalyzer(model)
    result = analyzer.analyze()
    
    print(f"Analysis result: {result.success}")
    print(f"Summary: {result.summary}\n")
    
    stats = result.data['statistics']
    print(f"Total test arcs: {stats['total_test_arcs']}")
    print(f"Total catalysts: {stats['total_catalysts']}")
    print(f"Catalyzed transitions: {stats['catalyzed_transitions']}")
    
    # Verify
    assert result.success, "Analysis should succeed"
    assert stats['total_test_arcs'] == 0, "Should have 0 test arcs"
    assert stats['total_catalysts'] == 0, "Should have 0 catalysts"
    assert stats['catalyzed_transitions'] == 0, "Should have 0 catalyzed transitions"
    
    print("\n✓ TEST PASSED: Correctly detected no catalysts")


def test_single_catalyst():
    """Test model with single catalyst (enzyme-catalyzed reaction)."""
    print("\n" + "="*70)
    print("TEST 2: Single Catalyst (Enzyme-Catalyzed Reaction)")
    print("="*70)
    
    model = MockModel()
    
    # Enzyme-catalyzed reaction: Substrate + [Enzyme] → Product
    substrate = create_place(1, "Substrate", 100, 100, tokens=10)
    enzyme = create_place(2, "Enzyme", 100, 200, tokens=5)
    product = create_place(3, "Product", 300, 100, tokens=0)
    t1 = create_transition(1, "Reaction", 200, 100)
    
    model.add_place(substrate)
    model.add_place(enzyme)
    model.add_place(product)
    model.add_transition(t1)
    
    model.add_arc(Arc(substrate, t1, 1, "A1", weight=1))
    model.add_arc(TestArc(enzyme, t1, 2, "TA1", weight=1))  # Test arc (catalyst)
    model.add_arc(Arc(t1, product, 3, "A3", weight=1))
    
    print("Model structure:")
    print("  Substrate (P1) → Reaction (T1) → Product (P3)")
    print("  Enzyme (P2) --[test arc]--> Reaction (T1)")
    print("  (Enzyme catalyzes reaction without being consumed)\n")
    
    # Analyze
    analyzer = RegulatoryStructureAnalyzer(model)
    result = analyzer.analyze()
    
    print(f"Analysis result: {result.success}")
    print(f"Summary: {result.summary}\n")
    
    stats = result.data['statistics']
    print(f"Total test arcs: {stats['total_test_arcs']}")
    print(f"Total catalysts: {stats['total_catalysts']}")
    print(f"Catalyzed transitions: {stats['catalyzed_transitions']}")
    print(f"Shared catalysts: {stats['shared_catalysts']}")
    
    # Verify
    assert result.success, "Analysis should succeed"
    assert stats['total_test_arcs'] == 1, "Should have 1 test arc"
    assert stats['total_catalysts'] == 1, "Should have 1 catalyst"
    assert stats['catalyzed_transitions'] == 1, "Should have 1 catalyzed transition"
    assert stats['shared_catalysts'] == 0, "Should have 0 shared catalysts"
    
    # Check validation
    validation = result.data['validation']
    assert validation['valid'], "Structure should be valid"
    
    print("\n✓ TEST PASSED: Correctly detected single catalyst")


def test_shared_catalyst():
    """Test model with shared catalyst (multi-substrate enzyme)."""
    print("\n" + "="*70)
    print("TEST 3: Shared Catalyst (Multi-Substrate Enzyme)")
    print("="*70)
    
    model = MockModel()
    
    # Hexokinase catalyzes both glucose and fructose phosphorylation
    glucose = create_place(1, "Glucose", 100, 100, tokens=10)
    fructose = create_place(2, "Fructose", 100, 200, tokens=10)
    hexokinase = create_place(3, "Hexokinase", 100, 300, tokens=5)
    g6p = create_place(4, "G6P", 300, 100, tokens=0)
    f6p = create_place(5, "F6P", 300, 200, tokens=0)
    
    t1 = create_transition(1, "GlucosePhosphorylation", 200, 100)
    t2 = create_transition(2, "FructosePhosphorylation", 200, 200)
    
    model.add_place(glucose)
    model.add_place(fructose)
    model.add_place(hexokinase)
    model.add_place(g6p)
    model.add_place(f6p)
    model.add_transition(t1)
    model.add_transition(t2)
    
    # Reaction 1: Glucose + [Hexokinase] → G6P
    model.add_arc(Arc(glucose, t1, 1, "A1", weight=1))
    model.add_arc(TestArc(hexokinase, t1, 2, "TA1", weight=1))
    model.add_arc(Arc(t1, g6p, 3, "A3", weight=1))
    
    # Reaction 2: Fructose + [Hexokinase] → F6P
    model.add_arc(Arc(fructose, t2, 4, "A4", weight=1))
    model.add_arc(TestArc(hexokinase, t2, 5, "TA2", weight=1))  # Same enzyme!
    model.add_arc(Arc(t2, f6p, 6, "A6", weight=1))
    
    print("Model structure:")
    print("  Reaction 1: Glucose + [Hexokinase] → G6P")
    print("  Reaction 2: Fructose + [Hexokinase] → F6P")
    print("  (Same enzyme catalyzes both reactions)\n")
    
    # Analyze
    analyzer = RegulatoryStructureAnalyzer(model)
    result = analyzer.analyze()
    
    print(f"Analysis result: {result.success}")
    print(f"Summary: {result.summary}\n")
    
    stats = result.data['statistics']
    print(f"Total test arcs: {stats['total_test_arcs']}")
    print(f"Total catalysts: {stats['total_catalysts']}")
    print(f"Catalyzed transitions: {stats['catalyzed_transitions']}")
    print(f"Shared catalysts: {stats['shared_catalysts']}")
    
    # Check shared catalysts
    shared = result.data['shared_catalysts']
    if shared:
        print(f"\nShared catalysts detected:")
        for catalyst in shared:
            print(f"  - {catalyst['catalyst_name']}: catalyzes {catalyst['num_transitions']} reactions")
            print(f"    Reactions: {', '.join([t['transition_name'] for t in catalyst['transitions']])}")
    
    # Verify
    assert result.success, "Analysis should succeed"
    assert stats['total_test_arcs'] == 2, "Should have 2 test arcs"
    assert stats['total_catalysts'] == 1, "Should have 1 unique catalyst"
    assert stats['catalyzed_transitions'] == 2, "Should have 2 catalyzed transitions"
    assert stats['shared_catalysts'] == 1, "Should have 1 shared catalyst"
    
    # Check patterns
    patterns = result.data['patterns']
    multi_substrate = [p for p in patterns if p['type'] == 'multi_substrate_enzyme']
    assert len(multi_substrate) == 1, "Should detect 1 multi-substrate enzyme pattern"
    assert multi_substrate[0]['num_reactions'] == 2, "Should catalyze 2 reactions"
    
    print("\n✓ TEST PASSED: Correctly detected shared catalyst")
    print("  (This is CORRECT biological behavior - enzyme reuse)")


def test_interpretation():
    """Test interpretation generation."""
    print("\n" + "="*70)
    print("TEST 4: Interpretation Generation")
    print("="*70)
    
    model = MockModel()
    
    # Complex model with shared catalyst
    s1 = create_place(1, "Glucose", 100, 100, tokens=10)
    s2 = create_place(2, "Fructose", 100, 200, tokens=10)
    enzyme = create_place(3, "Hexokinase", 100, 300, tokens=5)
    p1 = create_place(4, "G6P", 300, 100, tokens=0)
    p2 = create_place(5, "F6P", 300, 200, tokens=0)
    
    t1 = create_transition(1, "GlucosePhosphorylation", 200, 100)
    t2 = create_transition(2, "FructosePhosphorylation", 200, 200)
    
    model.add_place(s1)
    model.add_place(s2)
    model.add_place(enzyme)
    model.add_place(p1)
    model.add_place(p2)
    model.add_transition(t1)
    model.add_transition(t2)
    
    model.add_arc(Arc(s1, t1, 1, "A1", weight=1))
    model.add_arc(TestArc(enzyme, t1, 2, "TA1", weight=1))
    model.add_arc(Arc(t1, p1, 3, "A3", weight=1))
    
    model.add_arc(Arc(s2, t2, 4, "A4", weight=1))
    model.add_arc(TestArc(enzyme, t2, 5, "TA2", weight=1))
    model.add_arc(Arc(t2, p2, 6, "A6", weight=1))
    
    print("Model: Hexokinase catalyzes two reactions\n")
    
    # Analyze
    analyzer = RegulatoryStructureAnalyzer(model)
    result = analyzer.analyze()
    
    print("="*70)
    print("INTERPRETATION")
    print("="*70)
    print(result.data['interpretation'])
    print("="*70)
    
    # Verify interpretation contains key elements
    interpretation = result.data['interpretation']
    assert "REGULATORY STRUCTURE ANALYSIS" in interpretation
    assert "SHARED CATALYSTS" in interpretation
    assert "WEAK INDEPENDENCE" in interpretation
    assert "KEY INSIGHT" in interpretation
    
    print("\n✓ TEST PASSED: Interpretation generated correctly")


def run_all_tests():
    """Run all regulatory structure analyzer tests."""
    print("\n" + "="*70)
    print("REGULATORY STRUCTURE ANALYZER TEST SUITE")
    print("="*70)
    print("\nTesting detection and analysis of:")
    print("  1. Test arcs (catalysts)")
    print("  2. Shared catalysts (multi-substrate enzymes)")
    print("  3. Regulatory patterns")
    print("  4. Interpretation generation")
    
    try:
        test_no_catalysts()
        test_single_catalyst()
        test_shared_catalyst()
        test_interpretation()
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED! ✅")
        print("="*70)
        print("\nRegulatory Structure Analyzer is CORRECT:")
        print("  ✓ Detects test arcs (catalysts)")
        print("  ✓ Identifies shared catalysts (enzyme reuse)")
        print("  ✓ Detects regulatory patterns")
        print("  ✓ Generates biological interpretation")
        print("\nThis analyzer complements Dependency & Coupling analyzer!")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
