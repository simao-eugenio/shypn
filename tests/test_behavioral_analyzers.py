#!/usr/bin/env python3
"""Test behavioral analyzers with simple P-T-P model."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.topology.behavioral.throughput import ThroughputAnalyzer
from shypn.topology.behavioral.response_time import ResponseTimeAnalyzer
from shypn.topology.behavioral.coverability import CoverabilityAnalyzer


def test_throughput():
    """Test throughput analyzer with P-T-P model."""
    print("\n" + "="*70)
    print("🔍 TESTING THROUGHPUT ANALYZER")
    print("="*70)
    
    # Create simple P-T-P model
    doc = DocumentModel()
    p1 = doc.create_place(x=100, y=100, label="P1")
    t1 = doc.create_transition(x=200, y=100, label="T1")
    p2 = doc.create_place(x=300, y=100, label="P2")
    
    arc1 = doc.create_arc(p1, t1)
    arc2 = doc.create_arc(t1, p2)
    
    # Set initial marking (P1 has 1 token)
    p1.tokens = 1
    p2.tokens = 0
    
    print(f"\n  Model structure:")
    print(f"    Places: {len(doc.places)} - {[p.id for p in doc.places]}")
    print(f"    Transitions: {len(doc.transitions)} - {[t.id for t in doc.transitions]}")
    print(f"    Arcs: {len(doc.arcs)}")
    print(f"    Initial marking: P1={p1.tokens}, P2={p2.tokens}")
    
    # Run analyzer
    print(f"\n  Running throughput analyzer...")
    analyzer = ThroughputAnalyzer(doc)
    
    try:
        result = analyzer.analyze(max_steps=1000, max_time=5.0)
        
        if result.success:
            print(f"  ✅ Analysis successful!")
            print(f"\n  Results:")
            print(f"    Total steps: {result.data.get('statistics', {}).get('total_steps', 'N/A')}")
            print(f"    Total firings: {result.data.get('statistics', {}).get('total_firings', 'N/A')}")
            print(f"    Computation time: {result.metadata.get('computation_time', 'N/A'):.3f}s")
            
            firing_rates = result.data.get('firing_rates', {})
            print(f"\n  Firing rates:")
            for trans_id, rate in firing_rates.items():
                print(f"    {trans_id}: {rate:.4f}")
            
            throughput = result.data.get('throughput', 'N/A')
            print(f"\n  System throughput: {throughput}")
            
            if result.warnings:
                print(f"\n  ⚠️  Warnings:")
                for warning in result.warnings:
                    print(f"    - {warning}")
            
            return True
        else:
            print(f"  ❌ Analysis failed")
            if result.errors:
                for error in result.errors:
                    print(f"    Error: {error}")
            return False
            
    except Exception as e:
        print(f"  ❌ Exception during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_response_time():
    """Test response time analyzer with P-T-P model."""
    print("\n" + "="*70)
    print("🔍 TESTING RESPONSE TIME ANALYZER")
    print("="*70)
    
    # Create simple P-T-P model
    doc = DocumentModel()
    p1 = doc.create_place(x=100, y=100, label="P1")
    t1 = doc.create_transition(x=200, y=100, label="T1")
    p2 = doc.create_place(x=300, y=100, label="P2")
    
    arc1 = doc.create_arc(p1, t1)
    arc2 = doc.create_arc(t1, p2)
    
    # Set initial marking
    p1.tokens = 1
    p2.tokens = 0
    
    print(f"\n  Model structure:")
    print(f"    Places: {len(doc.places)}")
    print(f"    Transitions: {len(doc.transitions)}")
    print(f"    Initial marking: P1={p1.tokens}, P2={p2.tokens}")
    
    # Run analyzer
    print(f"\n  Running response time analyzer...")
    analyzer = ResponseTimeAnalyzer(doc)
    
    try:
        result = analyzer.analyze(max_steps=1000, max_time=5.0)
        
        if result.success:
            print(f"  ✅ Analysis successful!")
            print(f"\n  Results:")
            print(f"    Total steps: {result.data.get('statistics', {}).get('total_steps', 'N/A')}")
            print(f"    Computation time: {result.metadata.get('computation_time', 'N/A'):.3f}s")
            
            inter_firing = result.data.get('inter_firing_times', {})
            if inter_firing:
                print(f"\n  Inter-firing times:")
                for trans_id, avg_time in inter_firing.items():
                    print(f"    {trans_id}: avg={avg_time:.2f} steps")
            
            if result.warnings:
                print(f"\n  ⚠️  Warnings:")
                for warning in result.warnings:
                    print(f"    - {warning}")
            
            return True
        else:
            print(f"  ❌ Analysis failed")
            if result.errors:
                for error in result.errors:
                    print(f"    Error: {error}")
            return False
            
    except Exception as e:
        print(f"  ❌ Exception during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_coverability():
    """Test coverability analyzer with P-T-P model."""
    print("\n" + "="*70)
    print("🔍 TESTING COVERABILITY ANALYZER")
    print("="*70)
    
    # Create simple P-T-P model
    doc = DocumentModel()
    p1 = doc.create_place(x=100, y=100, label="P1")
    t1 = doc.create_transition(x=200, y=100, label="T1")
    p2 = doc.create_place(x=300, y=100, label="P2")
    
    arc1 = doc.create_arc(p1, t1)
    arc2 = doc.create_arc(t1, p2)
    
    # Set initial marking
    p1.tokens = 1
    p2.tokens = 0
    
    print(f"\n  Model structure:")
    print(f"    Places: {len(doc.places)}")
    print(f"    Transitions: {len(doc.transitions)}")
    print(f"    Initial marking: P1={p1.tokens}, P2={p2.tokens}")
    
    # Run analyzer
    print(f"\n  Running coverability analyzer...")
    analyzer = CoverabilityAnalyzer(doc)
    
    try:
        result = analyzer.analyze(max_nodes=1000)
        
        if result.success:
            print(f"  ✅ Analysis successful!")
            print(f"\n  Results:")
            print(f"    Total nodes: {result.data.get('statistics', {}).get('total_nodes', 'N/A')}")
            print(f"    Computation time: {result.metadata.get('computation_time', 'N/A'):.3f}s")
            
            unbounded = result.data.get('unbounded_places', [])
            if unbounded:
                print(f"\n  Unbounded places: {unbounded}")
            else:
                print(f"\n  No unbounded places (net is bounded)")
            
            if result.warnings:
                print(f"\n  ⚠️  Warnings:")
                for warning in result.warnings:
                    print(f"    - {warning}")
            
            return True
        else:
            print(f"  ❌ Analysis failed")
            if result.errors:
                for error in result.errors:
                    print(f"    Error: {error}")
            return False
            
    except Exception as e:
        print(f"  ❌ Exception during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*70)
    print("🧪 BEHAVIORAL ANALYZERS TEST SUITE")
    print("="*70)
    
    results = {
        'Throughput': test_throughput(),
        'Response Time': test_response_time(),
        'Coverability': test_coverability()
    }
    
    print("\n" + "="*70)
    print("📋 SUMMARY")
    print("="*70)
    
    for analyzer, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {analyzer}")
    
    passed = sum(1 for s in results.values() if s)
    total = len(results)
    print(f"\n🎯 Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 SUCCESS! All behavioral analyzers work correctly!")
        return 0
    else:
        print(f"\n⚠️  WARNING: {total - passed} test(s) failed.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
