"""Test parallel with progress tracking."""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.topology.behavioral.reachability import ReachabilityAnalyzer


class BiochemicalModel:
    """Simplified Glycolysis Pathway model."""
    
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
        
        self.arcs = [
            self.Arc('P1', 'T1', weight=1),
            self.Arc('T1', 'P2', weight=1),
            self.Arc('P2', 'T2', weight=1),
            self.Arc('T2', 'P3', weight=1),
            self.Arc('P3', 'T3', weight=1),
            self.Arc('T3', 'P4', weight=1),
            self.Arc('P4', 'T4', weight=1),
            self.Arc('T4', 'P5', weight=1),
            self.Arc('T4', 'P6', weight=1),
            self.Arc('P5', 'T5', weight=1),
            self.Arc('T5', 'P6', weight=1),
            self.Arc('P6', 'T6', weight=1),
            self.Arc('T6', 'P7', weight=1),
            self.Arc('P7', 'T7', weight=1),
            self.Arc('T7', 'P8', weight=1),
            self.Arc('P8', 'T8', weight=1),
            self.Arc('T8', 'P10', weight=1)
        ]


print("\nTesting Parallel Basic with 2 workers...")
model = BiochemicalModel()
analyzer = ReachabilityAnalyzer(model)

start = time.time()
result = analyzer.analyze(
    max_states=5000,
    max_depth=20,
    compute_graph=False,
    find_deadlocks=False,
    parallel=True,
    num_workers=2
)
elapsed = time.time() - start

print(f"\nResult:")
print(f"  Success: {result.success}")
print(f"  States: {result.get('total_states', 'N/A')}")
print(f"  Transitions: {result.get('total_transitions', 'N/A')}")
print(f"  Time: {elapsed:.2f}s")
print(f"  Mode: {result.metadata.get('mode', 'N/A')}")
print(f"  Workers: {result.metadata.get('num_workers', 'N/A')}")

if result.get('total_states') == 2108:
    print("\n✅ CORRECT - Found all 2,108 states")
else:
    print(f"\n❌ WRONG - Expected 2,108 states, got {result.get('total_states')}")
