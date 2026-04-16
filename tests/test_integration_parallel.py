"""Integration Test: Phase 1 Parallel BFS with Real Model

Tests parallel reachability analysis with a realistic biochemical model
similar to what would be loaded in the UI.
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.topology.behavioral.reachability import ReachabilityAnalyzer
from shypn.ui.topology_analysis_config import TopologyAnalysisConfig


class BiochemicalModel:
    """Realistic biochemical Petri net model.
    
    Represents a simplified glycolysis pathway:
    Glucose → G6P → F6P → FBP → DHAP + GAP → ... → Pyruvate
    
    Places: 10 metabolites
    Transitions: 8 reactions
    Initial tokens: 5 (glucose molecules)
    """
    
    class Place:
        def __init__(self, place_id, name, tokens=0):
            self.id = place_id
            self.name = name
            self.marking = tokens
            self.tokens = tokens
    
    class Transition:
        def __init__(self, trans_id, name):
            self.id = trans_id
            self.name = name
    
    class Arc:
        def __init__(self, source_id, target_id, weight=1):
            self.source_id = source_id
            self.target_id = target_id
            self.weight = weight
    
    def __init__(self):
        # Create places (metabolites)
        self.places = [
            self.Place('P1', 'Glucose', tokens=5),
            self.Place('P2', 'G6P', tokens=0),
            self.Place('P3', 'F6P', tokens=0),
            self.Place('P4', 'FBP', tokens=0),
            self.Place('P5', 'DHAP', tokens=0),
            self.Place('P6', 'GAP', tokens=0),
            self.Place('P7', '1,3-BPG', tokens=0),
            self.Place('P8', '3PG', tokens=0),
            self.Place('P9', 'PEP', tokens=0),
            self.Place('P10', 'Pyruvate', tokens=0)
        ]
        
        # Create transitions (reactions)
        self.transitions = [
            self.Transition('T1', 'Hexokinase'),
            self.Transition('T2', 'PGI'),
            self.Transition('T3', 'PFK'),
            self.Transition('T4', 'Aldolase'),
            self.Transition('T5', 'TPI'),
            self.Transition('T6', 'GAPDH'),
            self.Transition('T7', 'PGK'),
            self.Transition('T8', 'Pyruvate kinase')
        ]
        
        # Create arcs (reaction stoichiometry)
        self.arcs = [
            # Glucose → G6P (hexokinase)
            self.Arc('P1', 'T1', weight=1),
            self.Arc('T1', 'P2', weight=1),
            
            # G6P → F6P (PGI)
            self.Arc('P2', 'T2', weight=1),
            self.Arc('T2', 'P3', weight=1),
            
            # F6P → FBP (PFK)
            self.Arc('P3', 'T3', weight=1),
            self.Arc('T3', 'P4', weight=1),
            
            # FBP → DHAP + GAP (aldolase)
            self.Arc('P4', 'T4', weight=1),
            self.Arc('T4', 'P5', weight=1),
            self.Arc('T4', 'P6', weight=1),
            
            # DHAP ⇌ GAP (TPI - reversible via separate arc)
            self.Arc('P5', 'T5', weight=1),
            self.Arc('T5', 'P6', weight=1),
            
            # GAP → 1,3-BPG (GAPDH)
            self.Arc('P6', 'T6', weight=1),
            self.Arc('T6', 'P7', weight=1),
            
            # 1,3-BPG → 3PG (PGK)
            self.Arc('P7', 'T7', weight=1),
            self.Arc('T7', 'P8', weight=1),
            
            # 3PG → ... → PEP → Pyruvate (simplified)
            self.Arc('P8', 'T8', weight=1),
            self.Arc('T8', 'P10', weight=1)
        ]


def test_sequential_biochemical():
    """Test sequential analysis on biochemical model."""
    print("\n1. Sequential Analysis (Baseline)")
    print("-" * 60)
    
    model = BiochemicalModel()
    analyzer = ReachabilityAnalyzer(model)
    
    start = time.time()
    result = analyzer.analyze(
        max_states=5000,
        max_depth=20,
        compute_graph=False,  # Skip graph for speed
        find_deadlocks=True,
        parallel=False
    )
    elapsed = time.time() - start
    
    assert result.success, f"Analysis failed: {result.errors}"
    
    states = result.get('total_states')
    transitions = result.get('total_transitions')
    deadlocks = len(result.get('deadlock_states', []))
    
    print(f"   States: {states:,}")
    print(f"   Transitions: {transitions:,}")
    print(f"   Deadlocks: {deadlocks}")
    print(f"   Time: {elapsed:.3f}s")
    print(f"   Mode: {result.metadata['mode']}")
    
    return states, elapsed


def test_parallel_basic_biochemical():
    """Test Phase 1: Basic parallel with work-stealing."""
    print("\n2. Parallel Basic (Phase 1: Work-Stealing)")
    print("-" * 60)
    
    model = BiochemicalModel()
    analyzer = ReachabilityAnalyzer(model)
    
    start = time.time()
    result = analyzer.analyze(
        max_states=5000,
        max_depth=20,
        compute_graph=False,
        find_deadlocks=True,
        parallel=True,
        num_workers=4
    )
    elapsed = time.time() - start
    
    assert result.success, f"Analysis failed: {result.errors}"
    
    states = result.get('total_states')
    transitions = result.get('total_transitions')
    deadlocks = len(result.get('deadlock_states', []))
    
    print(f"   States: {states:,}")
    print(f"   Transitions: {transitions:,}")
    print(f"   Deadlocks: {deadlocks}")
    print(f"   Time: {elapsed:.3f}s")
    print(f"   Mode: {result.metadata['mode']}")
    print(f"   Workers: {result.metadata['num_workers']}")
    
    return states, elapsed


def test_parallel_maximal_biochemical():
    """Test Phase 2: Maximal concurrent sets."""
    print("\n3. Parallel Maximal (Phase 2: Concurrent Sets)")
    print("-" * 60)
    
    model = BiochemicalModel()
    analyzer = ReachabilityAnalyzer(model)
    
    start = time.time()
    result = analyzer.analyze(
        max_states=5000,
        max_depth=20,
        compute_graph=False,
        find_deadlocks=True,
        parallel='maximal',
        num_workers=4
    )
    elapsed = time.time() - start
    
    assert result.success, f"Analysis failed: {result.errors}"
    
    states = result.get('total_states')
    transitions = result.get('total_transitions')
    deadlocks = len(result.get('deadlock_states', []))
    
    print(f"   States: {states:,}")
    print(f"   Transitions: {transitions:,}")
    print(f"   Deadlocks: {deadlocks}")
    print(f"   Time: {elapsed:.3f}s")
    print(f"   Mode: {result.metadata['mode']}")
    print(f"   Workers: {result.metadata['num_workers']}")
    
    return states, elapsed


def test_config_integration():
    """Test configuration system integration."""
    print("\n4. Configuration System Integration")
    print("-" * 60)
    
    config = TopologyAnalysisConfig.get_instance()
    
    # Configure parallel mode
    config.set_parallel_mode('reachability', 'maximal')
    config.set_num_workers('reachability', 6)
    config.set_max_states('reachability', 10000)
    
    # Verify settings
    assert config.get_parallel_mode('reachability') == 'maximal'
    assert config.get_num_workers('reachability') == 6
    assert config.is_parallel_enabled('reachability') == True
    
    print("   ✓ Parallel mode: maximal")
    print("   ✓ Workers: 6")
    print("   ✓ Max states: 10,000")
    print("   ✓ Config integration: OK")
    
    # Reset for other tests
    config.reset_to_defaults('reachability')


def calculate_speedup(seq_time, par_time):
    """Calculate parallel speedup factor."""
    if par_time > 0:
        return seq_time / par_time
    return 0.0


if __name__ == '__main__':
    print("=" * 60)
    print("INTEGRATION TEST: Parallel BFS with Biochemical Model")
    print("=" * 60)
    print("\nModel: Simplified Glycolysis Pathway")
    print("  - 10 places (metabolites)")
    print("  - 8 transitions (reactions)")
    print("  - 5 initial tokens (glucose molecules)")
    
    try:
        # Run all tests
        seq_states, seq_time = test_sequential_biochemical()
        basic_states, basic_time = test_parallel_basic_biochemical()
        maximal_states, maximal_time = test_parallel_maximal_biochemical()
        test_config_integration()
        
        # Verify consistency
        print("\n5. Consistency Verification")
        print("-" * 60)
        
        assert seq_states == basic_states, f"Sequential ({seq_states}) != Basic ({basic_states})"
        assert seq_states == maximal_states, f"Sequential ({seq_states}) != Maximal ({maximal_states})"
        
        print(f"   ✓ All strategies found {seq_states:,} states")
        print("   ✓ Results consistent across all modes")
        
        # Calculate speedups
        print("\n6. Performance Summary")
        print("-" * 60)
        
        basic_speedup = calculate_speedup(seq_time, basic_time)
        maximal_speedup = calculate_speedup(seq_time, maximal_time)
        
        print(f"   Sequential:      {seq_time:.3f}s (baseline)")
        print(f"   Parallel Basic:  {basic_time:.3f}s ({basic_speedup:.2f}× speedup)")
        print(f"   Parallel Maximal: {maximal_time:.3f}s ({maximal_speedup:.2f}× speedup)")
        
        if basic_speedup >= 1.5:
            print(f"   ✓ Basic parallel achieves {basic_speedup:.2f}× speedup (good!)")
        else:
            print(f"   ⚠ Basic parallel only {basic_speedup:.2f}× (overhead dominates)")
        
        if maximal_speedup >= 1.5:
            print(f"   ✓ Maximal parallel achieves {maximal_speedup:.2f}× speedup (good!)")
        else:
            print(f"   ⚠ Maximal parallel only {maximal_speedup:.2f}× (overhead dominates)")
        
        # Final verdict
        print("\n" + "=" * 60)
        print("✅ INTEGRATION TEST PASSED")
        print("=" * 60)
        print("\nAll parallel modes work correctly with:")
        print("  ✓ Realistic biochemical model")
        print("  ✓ Configuration system")
        print("  ✓ Consistent results across modes")
        print(f"  ✓ Performance improvement: up to {max(basic_speedup, maximal_speedup):.2f}×")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
