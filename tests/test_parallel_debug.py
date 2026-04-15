"""Debug test for parallel exploration issues."""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.topology.behavioral.reachability import ReachabilityAnalyzer


class SimpleModel:
    """Minimal test model."""
    
    class Place:
        def __init__(self, place_id, tokens=0):
            self.id = place_id
            self.marking = tokens
            self.tokens = tokens
    
    class Transition:
        def __init__(self, trans_id):
            self.id = trans_id
    
    class Arc:
        def __init__(self, source_id, target_id, weight=1):
            self.source_id = source_id
            self.target_id = target_id
            self.weight = weight
    
    def __init__(self):
        # Simple: P1(2) -> T1 -> P2
        self.places = [
            self.Place('P1', tokens=2),
            self.Place('P2', tokens=0)
        ]
        self.transitions = [
            self.Transition('T1')
        ]
        self.arcs = [
            self.Arc('P1', 'T1', 1),
            self.Arc('T1', 'P2', 1)
        ]


def test_sequential():
    print("\n=== Sequential Test ===")
    model = SimpleModel()
    analyzer = ReachabilityAnalyzer(model)
    
    result = analyzer.analyze(
        max_states=100,
        max_depth=10,
        compute_graph=False,
        find_deadlocks=False,
        parallel=False
    )
    
    print(f"Success: {result.success}")
    print(f"States: {result.get('total_states')}")
    print(f"Transitions: {result.get('total_transitions')}")


def test_parallel():
    print("\n=== Parallel Test (with timeout) ===")
    model = SimpleModel()
    analyzer = ReachabilityAnalyzer(model)
    
    start = time.time()
    result = analyzer.analyze(
        max_states=100,
        max_depth=10,
        compute_graph=False,
        find_deadlocks=False,
        parallel=True,
        num_workers=2
    )
    elapsed = time.time() - start
    
    print(f"Success: {result.success}")
    print(f"States: {result.get('total_states')}")
    print(f"Transitions: {result.get('total_transitions')}")
    print(f"Time: {elapsed:.2f}s")


if __name__ == '__main__':
    test_sequential()
    test_parallel()
