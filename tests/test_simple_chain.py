"""Debug version with state tracking."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.topology.behavioral.reachability import ReachabilityAnalyzer


class SimpleModel:
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
        # P1(3) -> T1 -> P2 -> T2 -> P3
        self.places = [
            self.Place('P1', tokens=3),
            self.Place('P2', tokens=0),
            self.Place('P3', tokens=0)
        ]
        self.transitions = [
            self.Transition('T1'),
            self.Transition('T2')
        ]
        self.arcs = [
            self.Arc('P1', 'T1', 1),
            self.Arc('T1', 'P2', 1),
            self.Arc('P2', 'T2', 1),
            self.Arc('T2', 'P3', 1)
        ]


print("\n=== Sequential ===")
model = SimpleModel()
analyzer = ReachabilityAnalyzer(model)
result = analyzer.analyze(max_states=100, max_depth=20, compute_graph=False, find_deadlocks=False, parallel=False)
print(f"States: {result.get('total_states')}, Transitions: {result.get('total_transitions')}")

print("\n=== Parallel (2 workers) ===")
model = SimpleModel()
analyzer = ReachabilityAnalyzer(model)
result = analyzer.analyze(max_states=100, max_depth=20, compute_graph=False, find_deadlocks=False, parallel=True, num_workers=2)
print(f"States: {result.get('total_states')}, Transitions: {result.get('total_transitions')}")
print(f"Metadata: {result.metadata}")

if result.get('total_states') == 7:
    print("✅ CORRECT")
else:
    print(f"❌ WRONG - expected 7 states")
