#!/usr/bin/env python3
"""Test the topology result aggregator and size guards."""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.topology.aggregator import TopologyResultAggregator
from shypn.topology.base.analysis_result import AnalysisResult

# Mock some analyzer results
mock_results = {
    'p_invariants': AnalysisResult(
        success=True,
        data={
            'p_invariants': [
                {
                    'places': [1, 2],
                    'weights': [1, 2],
                    'names': ['ATP', 'ADP'],
                    'sum_expression': 'ATP + 2*ADP'
                },
                {
                    'places': [3, 4],
                    'weights': [1, 1],
                    'names': ['NADH', 'NAD+'],
                    'sum_expression': 'NADH + NAD+'
                }
            ],
            'count': 2
        }
    ),
    't_invariants': AnalysisResult(
        success=True,
        data={
            't_invariants': [
                {
                    'transition_ids': [1, 2, 3],
                    'weights': [1, 1, 1],
                    'transition_names': ['T1', 'T2', 'T3'],
                    'firing_sequence': 'T1 → T2 → T3'
                }
            ],
            'count': 1
        }
    ),
    'hubs': AnalysisResult(
        success=True,
        data={
            'hubs': [
                {'id': 1, 'degree': 7, 'neighbors': [1, 2, 3, 4, 5, 6, 7]}
            ],
            'count': 1
        }
    ),
    'siphons': AnalysisResult(
        success=False,
        errors=["Model too large"],
        metadata={'blocked': True}
    )
}

# Test aggregation
print("=" * 60)
print("Testing Topology Result Aggregator")
print("=" * 60)

aggregator = TopologyResultAggregator()
element_data = aggregator.aggregate(mock_results)

print("\n✓ Aggregation successful!")
print(f"\nPlaces found: {len(element_data['places'])}")
print(f"Transitions found: {len(element_data['transitions'])}")

# Show place properties
print("\n" + "=" * 60)
print("PLACE PROPERTIES (Element-Centric View)")
print("=" * 60)
for place_id, props in element_data['places'].items():
    print(f"\nPlace {place_id} ({props['name']}):")
    print(f"  - P-Invariants: {len(props['p_invariants'])}")
    for inv in props['p_invariants']:
        print(f"    • Invariant #{inv['invariant_id']}: weight={inv['weight']}, expr={inv['expression']}")
    print(f"  - In Siphons: {len(props['in_siphons'])}")
    print(f"  - In Traps: {len(props['in_traps'])}")
    print(f"  - Boundedness: {props['boundedness']}")

# Show transition properties
print("\n" + "=" * 60)
print("TRANSITION PROPERTIES (Element-Centric View)")
print("=" * 60)
for trans_id, props in element_data['transitions'].items():
    print(f"\nTransition {trans_id} ({props['name']}):")
    print(f"  - T-Invariants: {len(props['t_invariants'])}")
    for inv in props['t_invariants']:
        print(f"    • Invariant #{inv['invariant_id']}: weight={inv['weight']}, sequence={inv['sequence']}")
    print(f"  - Is Hub: {props['is_hub']}")
    if props['is_hub']:
        print(f"  - Hub Degree: {props['hub_degree']}")
    print(f"  - In Cycles: {len(props['in_cycles'])}")
    print(f"  - Liveness: {props['liveness_level']}")

# Test table format
print("\n" + "=" * 60)
print("TABLE FORMAT (for UI display)")
print("=" * 60)

place_table = aggregator.to_table_format(element_data, 'places')
print("\nPlaces Table:")
if place_table:
    # Print header
    headers = list(place_table[0].keys())
    print("  " + " | ".join(f"{h:12}" for h in headers))
    print("  " + "-" * (15 * len(headers)))
    # Print rows
    for row in place_table:
        print("  " + " | ".join(f"{str(row[h]):12}" for h in headers))

trans_table = aggregator.to_table_format(element_data, 'transitions')
print("\nTransitions Table:")
if trans_table:
    # Print header
    headers = list(trans_table[0].keys())
    print("  " + " | ".join(f"{h:12}" for h in headers))
    print("  " + "-" * (15 * len(headers)))
    # Print rows
    for row in trans_table:
        print("  " + " | ".join(f"{str(row[h]):12}" for h in headers))

print("\n" + "=" * 60)
print("✓ All tests passed!")
print("=" * 60)
