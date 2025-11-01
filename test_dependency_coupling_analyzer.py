#!/usr/bin/env python3
"""
Test suite for Dependency & Coupling Analyzer.

Tests the refined locality theory classification:
1. Strongly Independent (no shared places)
2. Competitive (shared inputs → conflict)
3. Convergent (shared outputs → coupling OK)
4. Regulatory (shared catalysts → coupling OK)

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
from shypn.topology.biological.dependency_coupling import DependencyAndCouplingAnalyzer


# Simple mock model with dictionary structure
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


def test_strongly_independent():
    """Test detection of strongly independent transitions."""
    print("\n" + "="*70)
    print("TEST 1: Strongly Independent Transitions")
    print("="*70)
    
    model = MockModel()
    
    # Two independent pathways: P1 → T1 → P2  and  P3 → T2 → P4
    p1 = Place(id=1, name="P1", x=100, y=100)
    p2 = Place(id=2, name="P2", x=300, y=100)
    p3 = Place(id=3, name="P3", x=100, y=200)
    p4 = Place(id=4, name="P4", x=300, y=200)
    
    t1 = Transition(id=1, name="T1", x=200, y=100)
    t2 = Transition(id=2, name="T2", x=200, y=200)
    
    model.add_place(p1)
    model.add_place(p2)
    model.add_place(p3)
    model.add_place(p4)
    model.add_transition(t1)
    model.add_transition(t2)
    
    model.add_arc(Arc(p1, t1, 1, "A1", weight=1))
    model.add_arc(Arc(t1, p2, 2, "A2", weight=1))
    model.add_arc(Arc(p3, t2, 3, "A3", weight=1))
    model.add_arc(Arc(t2, p4, 4, "A4", weight=1))
    
    print("Model structure:")
    print("  Pathway 1: P1 → T1 → P2")
    print("  Pathway 2: P3 → T2 → P4")
    print("  (No shared places)\n")
    
    # Analyze
    analyzer = DependencyAndCouplingAnalyzer(model)
    result = analyzer.analyze()
    
    print(f"Analysis result: {result.success}")
    print(f"Summary: {result.summary}\n")
    
    stats = result.data['statistics']
    print(f"Strongly Independent: {stats['strongly_independent_count']}")
    print(f"Competitive: {stats['competitive_count']}")
    print(f"Convergent: {stats['convergent_count']}")
    print(f"Regulatory: {stats['regulatory_count']}")
    
    # Verify
    assert result.success, "Analysis should succeed"
    assert stats['strongly_independent_count'] == 1, "Should have 1 strongly independent pair"
    assert stats['competitive_count'] == 0, "Should have 0 competitive pairs"
    
    print("\n✓ TEST PASSED: Correctly identified strongly independent transitions")


def test_competitive_conflict():
    """Test detection of competitive (conflicting) transitions."""
    print("\n" + "="*70)
    print("TEST 2: Competitive Transitions (True Conflict)")
    print("="*70)
    
    model = MockModel()
    
    # Two transitions competing for same substrate
    # P1 → T1 → P2
    # P1 → T2 → P3  (T1 and T2 both consume from P1)
    p1 = Place(id=1, name="Substrate", x=100, y=150)
    p2 = Place(id=2, name="Product1", x=300, y=100)
    p3 = Place(id=3, name="Product2", x=300, y=200)
    
    t1 = Transition(id=1, name="Reaction1", x=200, y=100)
    t2 = Transition(id=2, name="Reaction2", x=200, y=200)
    
    model.add_place(p1)
    model.add_place(p2)
    model.add_place(p3)
    model.add_transition(t1)
    model.add_transition(t2)
    
    model.add_arc(Arc(p1, t1, 1, "A1", weight=1))  # Both consume from P1
    model.add_arc(Arc(p1, t2, 2, "A2", weight=1))  # Conflict!
    model.add_arc(Arc(t1, p2, 3, "A3", weight=1))
    model.add_arc(Arc(t2, p3, 4, "A4", weight=1))
    
    print("Model structure:")
    print("  Reaction 1: Substrate (P1) → T1 → Product1 (P2)")
    print("  Reaction 2: Substrate (P1) → T2 → Product2 (P3)")
    print("  (Both compete for P1 - resource competition)\n")
    
    # Analyze
    analyzer = DependencyAndCouplingAnalyzer(model)
    result = analyzer.analyze()
    
    print(f"Analysis result: {result.success}")
    print(f"Summary: {result.summary}\n")
    
    stats = result.data['statistics']
    print(f"Strongly Independent: {stats['strongly_independent_count']}")
    print(f"Competitive: {stats['competitive_count']}")
    print(f"Convergent: {stats['convergent_count']}")
    print(f"Regulatory: {stats['regulatory_count']}")
    
    # Verify
    assert result.success, "Analysis should succeed"
    assert stats['competitive_count'] == 1, "Should have 1 competitive pair"
    assert stats['strongly_independent_count'] == 0, "Should have 0 strongly independent pairs"
    
    print("\n✓ TEST PASSED: Correctly identified competitive conflict")


def test_convergent_coupling():
    """Test detection of convergent (valid coupling) transitions."""
    print("\n" + "="*70)
    print("TEST 3: Convergent Transitions (Valid Coupling)")
    print("="*70)
    
    model = MockModel()
    
    # Two pathways producing same product (metabolite convergence)
    # P1 → T1 → P3
    # P2 → T2 → P3  (Both produce to P3)
    p1 = Place(id=1, name="Source1", x=100, y=100)
    p2 = Place(id=2, name="Source2", x=100, y=200)
    p3 = Place(id=3, name="Product", x=300, y=150)
    
    t1 = Transition(id=1, name="Pathway1", x=200, y=100)
    t2 = Transition(id=2, name="Pathway2", x=200, y=200)
    
    model.add_place(p1)
    model.add_place(p2)
    model.add_place(p3)
    model.add_transition(t1)
    model.add_transition(t2)
    
    model.add_arc(Arc(p1, t1, 1, "A1", weight=1))
    model.add_arc(Arc(t1, p3, 2, "A2", weight=1))  # Both produce to P3
    model.add_arc(Arc(p2, t2, 3, "A3", weight=1))
    model.add_arc(Arc(t2, p3, 4, "A4", weight=1))  # Convergence!
    
    print("Model structure:")
    print("  Pathway 1: Source1 (P1) → T1 → Product (P3)")
    print("  Pathway 2: Source2 (P2) → T2 → Product (P3)")
    print("  (Multiple pathways producing same metabolite)\n")
    
    # Analyze
    analyzer = DependencyAndCouplingAnalyzer(model)
    result = analyzer.analyze()
    
    print(f"Analysis result: {result.success}")
    print(f"Summary: {result.summary}\n")
    
    stats = result.data['statistics']
    print(f"Strongly Independent: {stats['strongly_independent_count']}")
    print(f"Competitive: {stats['competitive_count']}")
    print(f"Convergent: {stats['convergent_count']}")
    print(f"Regulatory: {stats['regulatory_count']}")
    
    # Verify
    assert result.success, "Analysis should succeed"
    assert stats['convergent_count'] == 1, "Should have 1 convergent pair"
    assert stats['competitive_count'] == 0, "Should have 0 competitive pairs (no input competition)"
    
    print("\n✓ TEST PASSED: Correctly identified convergent coupling")
    print("  (This is CORRECT biological behavior - rates superpose)")


def test_regulatory_coupling():
    """Test detection of regulatory (catalyst shared) transitions."""
    print("\n" + "="*70)
    print("TEST 4: Regulatory Transitions (Shared Catalyst)")
    print("="*70)
    
    model = MockModel()
    
    # Two reactions sharing same enzyme (catalyst)
    # P1 --[Enzyme]--> T1 --> P3
    # P2 --[Enzyme]--> T2 --> P4  (Same enzyme catalyzes both)
    p1 = Place(id=1, name="Substrate1", x=100, y=100)
    p2 = Place(id=2, name="Substrate2", x=100, y=200)
    enzyme = Place(id=3, name="Enzyme", x=100, y=300)
    p3 = Place(id=4, name="Product1", x=300, y=100)
    p4 = Place(id=5, name="Product2", x=300, y=200)
    
    t1 = Transition(id=1, name="Reaction1", x=200, y=100)
    t2 = Transition(id=2, name="Reaction2", x=200, y=200)
    
    model.add_place(p1)
    model.add_place(p2)
    model.add_place(enzyme)
    model.add_place(p3)
    model.add_place(p4)
    model.add_transition(t1)
    model.add_transition(t2)
    
    model.add_arc(Arc(p1, t1, 1, "A1", weight=1))
    model.add_arc(TestArc(enzyme, t1, 2, "TA1", weight=1))  # Test arc (catalyst)
    model.add_arc(Arc(t1, p3, 3, "A3", weight=1))
    
    model.add_arc(Arc(p2, t2, 4, "A4", weight=1))
    model.add_arc(TestArc(enzyme, t2, 5, "TA2", weight=1))  # Test arc (catalyst)
    model.add_arc(Arc(t2, p4, 6, "A6", weight=1))
    
    print("Model structure:")
    print("  Reaction 1: Substrate1 (P1) --[Enzyme]--> T1 --> Product1 (P3)")
    print("  Reaction 2: Substrate2 (P2) --[Enzyme]--> T2 --> Product2 (P4)")
    print("  (Same enzyme catalyzes both reactions - test arcs)\n")
    
    # Analyze
    analyzer = DependencyAndCouplingAnalyzer(model)
    result = analyzer.analyze()
    
    print(f"Analysis result: {result.success}")
    print(f"Summary: {result.summary}\n")
    
    stats = result.data['statistics']
    print(f"Strongly Independent: {stats['strongly_independent_count']}")
    print(f"Competitive: {stats['competitive_count']}")
    print(f"Convergent: {stats['convergent_count']}")
    print(f"Regulatory: {stats['regulatory_count']}")
    
    # Verify
    assert result.success, "Analysis should succeed"
    assert stats['regulatory_count'] == 1, "Should have 1 regulatory pair"
    assert stats['competitive_count'] == 0, "Should have 0 competitive pairs (enzyme not consumed)"
    
    print("\n✓ TEST PASSED: Correctly identified regulatory coupling")
    print("  (This is CORRECT biological behavior - shared enzyme)")


def test_mixed_scenario():
    """Test complex scenario with multiple dependency types."""
    print("\n" + "="*70)
    print("TEST 5: Mixed Scenario (Multiple Dependency Types)")
    print("="*70)
    
    model = MockModel()
    
    # Complex biological network
    # Independent: T1, T4
    # Competitive: T1, T2 (share P1)
    # Convergent: T2, T3 (both produce P4)
    # Regulatory: T3, T4 (share enzyme P5)
    
    p1 = Place(id=1, name="Substrate", x=100, y=100)
    p2 = Place(id=2, name="P2", x=300, y=100)
    p3 = Place(id=3, name="P3", x=100, y=200)
    p4 = Place(id=4, name="Product", x=300, y=200)
    enzyme = Place(id=5, name="Enzyme", x=100, y=300)
    p6 = Place(id=6, name="P6", x=100, y=400)
    p7 = Place(id=7, name="P7", x=300, y=400)
    
    t1 = Transition(id=1, name="T1", x=200, y=100)
    t2 = Transition(id=2, name="T2", x=200, y=150)
    t3 = Transition(id=3, name="T3", x=200, y=250)
    t4 = Transition(id=4, name="T4", x=200, y=400)
    
    model.add_place(p1)
    model.add_place(p2)
    model.add_place(p3)
    model.add_place(p4)
    model.add_place(enzyme)
    model.add_place(p6)
    model.add_place(p7)
    model.add_transition(t1)
    model.add_transition(t2)
    model.add_transition(t3)
    model.add_transition(t4)
    
    # T1: P1 → T1 → P2
    model.add_arc(Arc(p1, t1, 1, "A1", weight=1))
    model.add_arc(Arc(t1, p2, 2, "A2", weight=1))
    
    # T2: P1 → T2 → P4 (competes with T1 for P1, produces to P4)
    model.add_arc(Arc(p1, t2, 3, "A3", weight=1))
    model.add_arc(Arc(t2, p4, 4, "A4", weight=1))
    
    # T3: P3 --[Enzyme]--> T3 --> P4 (shares enzyme with T4, converges with T2)
    model.add_arc(Arc(p3, t3, 5, "A5", weight=1))
    model.add_arc(TestArc(enzyme, t3, 6, "TA1", weight=1))
    model.add_arc(Arc(t3, p4, 7, "A7", weight=1))
    
    # T4: P6 --[Enzyme]--> T4 --> P7 (shares enzyme with T3, independent of others)
    model.add_arc(Arc(p6, t4, 8, "A8", weight=1))
    model.add_arc(TestArc(enzyme, t4, 9, "TA2", weight=1))
    model.add_arc(Arc(t4, p7, 10, "A10", weight=1))
    
    print("Model structure:")
    print("  T1: P1 → T1 → P2")
    print("  T2: P1 → T2 → P4  (competes with T1, converges with T3)")
    print("  T3: P3 --[Enzyme]--> T3 → P4  (shares enzyme with T4, converges with T2)")
    print("  T4: P6 --[Enzyme]--> T4 → P7  (shares enzyme with T3)\n")
    
    # Analyze
    analyzer = DependencyAndCouplingAnalyzer(model)
    result = analyzer.analyze()
    
    print(f"Analysis result: {result.success}")
    print(f"Summary: {result.summary}\n")
    
    stats = result.data['statistics']
    print(f"Strongly Independent: {stats['strongly_independent_count']}")
    print(f"Competitive: {stats['competitive_count']}")
    print(f"Convergent: {stats['convergent_count']}")
    print(f"Regulatory: {stats['regulatory_count']}")
    print(f"\nValid Couplings: {stats['valid_couplings_count']} ({stats['valid_couplings_pct']:.1f}%)")
    print(f"True Conflicts: {stats['competitive_count']} ({stats['competitive_pct']:.1f}%)")
    
    # Print interpretation
    print(f"\n{result.data['interpretation']}")
    
    # Verify
    assert result.success, "Analysis should succeed"
    assert stats['competitive_count'] == 1, f"Should have 1 competitive pair (T1, T2), got {stats['competitive_count']}"
    assert stats['convergent_count'] == 1, f"Should have 1 convergent pair (T2, T3), got {stats['convergent_count']}"
    assert stats['regulatory_count'] >= 1, f"Should have at least 1 regulatory pair (T3, T4), got {stats['regulatory_count']}"
    
    print("\n✓ TEST PASSED: Correctly classified mixed scenario")


def run_all_tests():
    """Run all dependency & coupling tests."""
    print("\n" + "="*70)
    print("DEPENDENCY & COUPLING ANALYZER TEST SUITE")
    print("="*70)
    print("\nTesting refined locality theory classification:")
    print("  1. Strongly Independent (no shared places)")
    print("  2. Competitive (shared inputs → conflict)")
    print("  3. Convergent (shared outputs → coupling OK)")
    print("  4. Regulatory (shared catalysts → coupling OK)")
    
    try:
        test_strongly_independent()
        test_competitive_conflict()
        test_convergent_coupling()
        test_regulatory_coupling()
        test_mixed_scenario()
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED! ✅")
        print("="*70)
        print("\nDependency & Coupling Analyzer is CORRECT:")
        print("  ✓ Identifies strongly independent transitions")
        print("  ✓ Detects true conflicts (competitive)")
        print("  ✓ Recognizes valid convergent coupling")
        print("  ✓ Recognizes valid regulatory coupling (test arcs)")
        print("\nThis validates the refined locality theory!")
        
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
