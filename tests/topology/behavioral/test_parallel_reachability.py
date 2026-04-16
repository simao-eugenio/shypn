"""Tests for parallel reachability analysis.

Validates that parallel exploration produces identical results to sequential
exploration while providing measurable speedup on multi-core systems.

Test Categories:
1. **Correctness**: Parallel results match sequential BFS
2. **Completeness**: All reachable states discovered
3. **Thread Safety**: No race conditions in concurrent state discovery
4. **Performance**: Speedup measurements across core counts

Test Models:
- Small nets (5-10 places): Overhead dominates, minimal speedup expected
- Medium nets (20-50 places): Sweet spot for parallelism
- Large nets (100+ places): Maximum speedup potential
"""

import pytest
import time
from typing import Dict, Any

from shypn.topology.behavioral.reachability import ReachabilityAnalyzer
from shypn.topology.behavioral.parallel_reachability import ParallelReachabilityAnalyzer


class TestParallelReachabilityCorrectness:
    """Test that parallel exploration matches sequential results."""
    
    def test_simple_net_correctness(self, simple_model):
        """Verify parallel gives same states as sequential for simple net."""
        # Sequential exploration
        seq_analyzer = ReachabilityAnalyzer(simple_model)
        seq_result = seq_analyzer.analyze(max_states=1000)
        
        # Parallel exploration
        par_analyzer = ParallelReachabilityAnalyzer(simple_model, num_workers=2)
        par_result = par_analyzer.analyze(max_states=1000, parallel=True)
        
        # Results should match
        assert par_result.success == seq_result.success
        assert par_result.get('total_states') == seq_result.get('total_states')
        
        # State sets should be identical
        seq_states = self._extract_states(seq_result)
        par_states = self._extract_states(par_result)
        assert seq_states == par_states
    
    def test_medium_net_correctness(self, medium_model):
        """Verify parallel correctness for medium-sized network."""
        seq_analyzer = ReachabilityAnalyzer(medium_model)
        par_analyzer = ParallelReachabilityAnalyzer(medium_model, num_workers=4)
        
        seq_result = seq_analyzer.analyze(max_states=5000)
        par_result = par_analyzer.analyze(max_states=5000, parallel=True)
        
        assert par_result.get('total_states') == seq_result.get('total_states')
        assert par_result.get('max_depth_reached') == seq_result.get('max_depth_reached')
    
    def test_deadlock_detection_matches(self, deadlock_model):
        """Verify deadlock states found by both approaches."""
        seq_analyzer = ReachabilityAnalyzer(deadlock_model)
        par_analyzer = ParallelReachabilityAnalyzer(deadlock_model, num_workers=2)
        
        seq_result = seq_analyzer.analyze(find_deadlocks=True)
        par_result = par_analyzer.analyze(find_deadlocks=True, parallel=True)
        
        seq_deadlocks = len(seq_result.get('deadlock_states', []))
        par_deadlocks = len(par_result.get('deadlock_states', []))
        
        assert par_deadlocks == seq_deadlocks
    
    def _extract_states(self, result: Any) -> set:
        """Extract set of marking tuples from result."""
        if not result.success:
            return set()
        
        graph = result.get('reachability_graph')
        if not graph:
            return set()
        
        states = set()
        for node in graph['nodes']:
            marking = node['marking']
            marking_tuple = tuple(sorted(marking.items()))
            states.add(marking_tuple)
        
        return states


class TestParallelReachabilityThreadSafety:
    """Test thread safety of concurrent state discovery."""
    
    def test_no_duplicate_states(self, concurrent_model):
        """Verify workers don't create duplicate states."""
        analyzer = ParallelReachabilityAnalyzer(concurrent_model, num_workers=8)
        result = analyzer.analyze(max_states=10000, parallel=True)
        
        # All state IDs should be unique
        graph = result.get('reachability_graph')
        if graph:
            state_ids = [node['id'] for node in graph['nodes']]
            assert len(state_ids) == len(set(state_ids))  # No duplicates
    
    def test_race_condition_stress(self, race_prone_model):
        """Stress test for race conditions in state discovery.
        
        Run multiple times to catch non-deterministic failures.
        """
        analyzer = ParallelReachabilityAnalyzer(race_prone_model, num_workers=8)
        
        results = []
        for _ in range(5):  # Run 5 times
            result = analyzer.analyze(max_states=5000, parallel=True)
            results.append(result.get('total_states'))
        
        # All runs should discover same number of states
        assert len(set(results)) == 1  # All identical


class TestParallelReachabilityPerformance:
    """Test parallel speedup characteristics."""
    
    def test_medium_net_speedup(self, medium_model):
        """Measure speedup for medium network."""
        # Sequential baseline
        seq_analyzer = ReachabilityAnalyzer(medium_model)
        start = time.time()
        seq_result = seq_analyzer.analyze(max_states=10000)
        seq_time = time.time() - start
        
        # Parallel with 4 workers
        par_analyzer = ParallelReachabilityAnalyzer(medium_model, num_workers=4)
        start = time.time()
        par_result = par_analyzer.analyze(max_states=10000, parallel=True)
        par_time = time.time() - start
        
        # Verify both complete successfully
        assert seq_result.success
        assert par_result.success
        assert par_result.get('total_states') == seq_result.get('total_states')
        
        # Report speedup (may be negative due to Lock overhead in Phase 1)
        speedup = seq_time / par_time
        print(f"Speedup: {speedup:.2f}× (sequential: {seq_time:.3f}s, parallel: {par_time:.3f}s)")
        print(f"Note: Lock overhead dominates in Phase 1. Phase 2 will improve performance.")
    
    def test_scaling_with_workers(self, large_model):
        """Test that parallel mode works with varying worker counts."""
        times = {}
        states = {}
        
        for num_workers in [1, 2, 4, 8]:
            analyzer = ParallelReachabilityAnalyzer(large_model, num_workers=num_workers)
            start = time.time()
            result = analyzer.analyze(max_states=20000, parallel=(num_workers > 1))
            times[num_workers] = time.time() - start
            states[num_workers] = result.get('total_states')
            assert result.success
        
        # All worker counts should find the same states
        assert len(set(states.values())) == 1, f"Inconsistent state counts: {states}"
        
        print(f"Scaling: 1w={times[1]:.3f}s, 2w={times[2]:.3f}s, 4w={times[4]:.3f}s, 8w={times[8]:.3f}s")
        print(f"States found: {states[1]} (consistent across all worker counts)")
    
    @pytest.mark.slow
    def test_large_net_performance(self, genome_scale_model):
        """Benchmark on genome-scale network."""
        analyzer = ParallelReachabilityAnalyzer(genome_scale_model, num_workers=8)
        
        start = time.time()
        result = analyzer.analyze(max_states=50000, parallel=True)
        elapsed = time.time() - start
        
        states_per_second = result.get('total_states') / elapsed
        print(f"Throughput: {states_per_second:.0f} states/sec")
        
        # Should explore at least 100 states/sec on modern hardware
        assert states_per_second >= 100


class TestParallelReachabilityFallback:
    """Test fallback to sequential mode."""
    
    def test_single_worker_fallback(self, simple_model):
        """With 1 worker, should use sequential algorithm."""
        analyzer = ParallelReachabilityAnalyzer(simple_model, num_workers=1)
        result = analyzer.analyze(parallel=True)
        
        # Should succeed (falls back to sequential)
        assert result.success
        # Sequential mode doesn't add parallelization_stats
        assert 'parallelization_stats' not in result.data
    
    def test_parallel_disabled(self, simple_model):
        """With parallel=False, should use sequential."""
        analyzer = ParallelReachabilityAnalyzer(simple_model, num_workers=4)
        result = analyzer.analyze(parallel=False)
        
        assert result.success
        # No parallel stats if sequential mode
        assert 'parallelization_stats' not in result.data


# ==============================================================================
# FIXTURES: Test Models
# ==============================================================================

def create_mock_place(place_id, name, marking=0):
    """Helper to create mock place."""
    from unittest.mock import Mock
    place = Mock()
    place.id = place_id
    place.name = name
    place.marking = marking
    place.tokens = marking  # ReachabilityAnalyzer uses 'tokens' attribute
    return place


def create_mock_transition(trans_id, name):
    """Helper to create mock transition."""
    from unittest.mock import Mock
    trans = Mock()
    trans.id = trans_id
    trans.name = name
    return trans


def create_mock_arc(source_id, target_id, weight=1):
    """Helper to create mock arc."""
    from unittest.mock import Mock
    arc = Mock()
    arc.source_id = source_id
    arc.target_id = target_id
    arc.weight = weight
    return arc


@pytest.fixture
def simple_model():
    """Simple model for correctness testing.
    
    Linear chain: P1 -> T1 -> P2 -> T2 -> P3
    Expected states: 3 (tokens move through chain)
    """
    from unittest.mock import Mock
    
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 1)
    p2 = create_mock_place('p2', 'P2', 0)
    p3 = create_mock_place('p3', 'P3', 0)
    t1 = create_mock_transition('t1', 'T1')
    t2 = create_mock_transition('t2', 'T2')
    
    model.places = [p1, p2, p3]
    model.transitions = [t1, t2]
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p2'),
        create_mock_arc('p2', 't2'),
        create_mock_arc('t2', 'p3')
    ]
    
    return model

@pytest.fixture
def medium_model():
    """Medium model for speedup testing.
    
    Multiple parallel paths creating moderate branching.
    Expected states: ~20-30
    """
    from unittest.mock import Mock
    
    model = Mock()
    places = []
    transitions = []
    arcs = []
    
    # Create 5 parallel chains
    for i in range(5):
        p_start = create_mock_place(f'p{i}_start', f'P{i}_Start', 1)
        p_mid = create_mock_place(f'p{i}_mid', f'P{i}_Mid', 0)
        p_end = create_mock_place(f'p{i}_end', f'P{i}_End', 0)
        t1 = create_mock_transition(f't{i}_1', f'T{i}_1')
        t2 = create_mock_transition(f't{i}_2', f'T{i}_2')
        
        places.extend([p_start, p_mid, p_end])
        transitions.extend([t1, t2])
        arcs.extend([
            create_mock_arc(f'p{i}_start', f't{i}_1'),
            create_mock_arc(f't{i}_1', f'p{i}_mid'),
            create_mock_arc(f'p{i}_mid', f't{i}_2'),
            create_mock_arc(f't{i}_2', f'p{i}_end')
        ])
    
    model.places = places
    model.transitions = transitions
    model.arcs = arcs
    
    return model

@pytest.fixture
def large_model():
    """Large model for scaling tests.
    
    Grid structure with many places and transitions.
    Expected states: 50+ states.
    """
    from unittest.mock import Mock
    
    model = Mock()
    places = []
    transitions = []
    arcs = []
    
    # Create 5×5 grid (smaller to avoid state explosion guard)
    grid_size = 5
    for i in range(grid_size):
        for j in range(grid_size):
            p = create_mock_place(f'p{i}_{j}', f'P{i}_{j}', 
                                 1 if i == 0 and j == 0 else 0)
            places.append(p)
    
    # Create transitions (simplified - just horizontal and vertical)
    for i in range(grid_size):
        for j in range(grid_size):
            # Right transition
            if j < grid_size - 1:
                t = create_mock_transition(f't{i}_{j}_r', f'T{i}_{j}_R')
                transitions.append(t)
                arcs.append(create_mock_arc(f'p{i}_{j}', f't{i}_{j}_r'))
                arcs.append(create_mock_arc(f't{i}_{j}_r', f'p{i}_{j+1}'))
            
            # Down transition
            if i < grid_size - 1:
                t = create_mock_transition(f't{i}_{j}_d', f'T{i}_{j}_D')
                transitions.append(t)
                arcs.append(create_mock_arc(f'p{i}_{j}', f't{i}_{j}_d'))
                arcs.append(create_mock_arc(f't{i}_{j}_d', f'p{i+1}_{j}'))
    
    model.places = places
    model.transitions = transitions
    model.arcs = arcs
    
    return model

@pytest.fixture
def deadlock_model():
    """Model with known deadlock states.
    
    Linear chain that terminates (deadlocks at end).
    """
    from unittest.mock import Mock
    
    model = Mock()
    p1 = create_mock_place('p1', 'P1', 1)
    p2 = create_mock_place('p2', 'P2', 0)
    t1 = create_mock_transition('t1', 'T1')
    
    model.places = [p1, p2]
    model.transitions = [t1]
    model.arcs = [
        create_mock_arc('p1', 't1'),
        create_mock_arc('t1', 'p2')
    ]
    
    return model

@pytest.fixture
def concurrent_model():
    """Model with high concurrency for stress testing.
    
    Independent parallel chains that can execute simultaneously.
    """
    from unittest.mock import Mock
    
    model = Mock()
    places = []
    transitions = []
    arcs = []
    
    # Create 6 independent chains
    for chain_id in range(6):
        p_start = create_mock_place(f'p{chain_id}_start', f'P{chain_id}_Start', 1)
        p_mid = create_mock_place(f'p{chain_id}_mid', f'P{chain_id}_Mid', 0)
        p_end = create_mock_place(f'p{chain_id}_end', f'P{chain_id}_End', 0)
        
        t1 = create_mock_transition(f't{chain_id}_1', f'T{chain_id}_1')
        t2 = create_mock_transition(f't{chain_id}_2', f'T{chain_id}_2')
        
        places.extend([p_start, p_mid, p_end])
        transitions.extend([t1, t2])
        arcs.extend([
            create_mock_arc(f'p{chain_id}_start', f't{chain_id}_1'),
            create_mock_arc(f't{chain_id}_1', f'p{chain_id}_mid'),
            create_mock_arc(f'p{chain_id}_mid', f't{chain_id}_2'),
            create_mock_arc(f't{chain_id}_2', f'p{chain_id}_end')
        ])
    
    model.places = places
    model.transitions = transitions
    model.arcs = arcs
    
    return model

@pytest.fixture
def race_prone_model():
    """Model designed to expose race conditions.
    
    Diamond structure with reconvergent paths.
    """
    from unittest.mock import Mock
    
    model = Mock()
    p_start = create_mock_place('p_start', 'P_Start', 2)
    p_mid1 = create_mock_place('p_mid1', 'P_Mid1', 0)
    p_mid2 = create_mock_place('p_mid2', 'P_Mid2', 0)
    p_end = create_mock_place('p_end', 'P_End', 0)
    
    t_split1 = create_mock_transition('t_split1', 'T_Split1')
    t_split2 = create_mock_transition('t_split2', 'T_Split2')
    t_join1 = create_mock_transition('t_join1', 'T_Join1')
    t_join2 = create_mock_transition('t_join2', 'T_Join2')
    
    model.places = [p_start, p_mid1, p_mid2, p_end]
    model.transitions = [t_split1, t_split2, t_join1, t_join2]
    model.arcs = [
        create_mock_arc('p_start', 't_split1'),
        create_mock_arc('t_split1', 'p_mid1'),
        create_mock_arc('p_start', 't_split2'),
        create_mock_arc('t_split2', 'p_mid2'),
        create_mock_arc('p_mid1', 't_join1'),
        create_mock_arc('t_join1', 'p_end'),
        create_mock_arc('p_mid2', 't_join2'),
        create_mock_arc('t_join2', 'p_end')
    ]
    
    return model

@pytest.fixture
def genome_scale_model():
    """Large-scale model for performance benchmarking.
    
    Simulates metabolic network with many places and reactions.
    """
    from unittest.mock import Mock
    
    model = Mock()
    places = []
    transitions = []
    arcs = []
    
    # Create 80 metabolite places
    num_metabolites = 80
    for i in range(num_metabolites):
        p = create_mock_place(f'met{i}', f'Metabolite{i}', 
                             1 if i < 5 else 0)
        places.append(p)
    
    # Create reactions connecting metabolites
    num_reactions = 100
    for i in range(num_reactions):
        t = create_mock_transition(f'rxn{i}', f'Reaction{i}')
        transitions.append(t)
        
        # Each reaction consumes 1-2 metabolites and produces 1-2
        input1_idx = i % num_metabolites
        input2_idx = (i + 1) % num_metabolites
        output1_idx = (i + 2) % num_metabolites
        output2_idx = (i + 3) % num_metabolites
        
        arcs.extend([
            create_mock_arc(f'met{input1_idx}', f'rxn{i}'),
            create_mock_arc(f'met{input2_idx}', f'rxn{i}'),
            create_mock_arc(f'rxn{i}', f'met{output1_idx}'),
            create_mock_arc(f'rxn{i}', f'met{output2_idx}')
        ])
    
    model.places = places
    model.transitions = transitions
    model.arcs = arcs
    
    return model
