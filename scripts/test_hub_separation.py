#!/usr/bin/env python3
"""Test Hub Separation - Measure transition-to-transition distances after layout."""

import sys
sys.path.insert(0, 'src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.layout.sscc.solar_system_layout_engine import SolarSystemLayoutEngine
import math


def test_hub_separation():
    """Test that transition hubs are properly separated."""
    
    print("="*80)
    print("HUB SEPARATION TEST (Transition-to-Transition Distances)")
    print("="*80)
    print()
    
    # Load model
    model_path = "workspace/Test_flow/model/hub_constellation.shy"
    print(f"Loading: {model_path}")
    
    document = DocumentModel.load_from_file(model_path)
    places = document.places
    transitions = document.transitions
    arcs = document.arcs
    
    print(f"  Places: {len(places)}")
    print(f"  Transitions: {len(transitions)}")
    print(f"  Arcs: {len(arcs)}")
    print()
    
    # Show initial transition positions
    print("Initial Transition Positions:")
    print("-"*80)
    for t in sorted(transitions, key=lambda x: x.id):
        print(f"  {t.label} (ID {t.id}): x={t.x:.1f}, y={t.y:.1f}")
    print()
    
    # Calculate initial distances
    print("Initial Transition-to-Transition Distances:")
    print("-"*80)
    initial_distances = []
    for i, t1 in enumerate(transitions):
        for t2 in list(transitions)[i+1:]:
            dist = math.sqrt((t2.x - t1.x)**2 + (t2.y - t1.y)**2)
            initial_distances.append((t1.label, t2.label, dist))
            print(f"  {t1.label} ↔ {t2.label}: {dist:.1f} units")
    print()
    
    # Apply Solar System Layout
    print("Applying Solar System Layout (with PROXIMITY_CONSTANT = 2,000,000)...")
    print("-"*80)
    
    engine = SolarSystemLayoutEngine()
    new_positions = engine.apply_layout(places, transitions, arcs)
    
    print(f"✓ Layout calculated: {len(new_positions)} positions")
    print()
    
    # Show final transition positions
    print("Final Transition Positions:")
    print("-"*80)
    for t in sorted(transitions, key=lambda x: x.id):
        x, y = new_positions[t.id]
        print(f"  {t.label} (ID {t.id}): x={x:.1f}, y={y:.1f}")
    print()
    
    # Calculate final distances
    print("Final Transition-to-Transition Distances:")
    print("-"*80)
    final_distances = []
    for i, t1 in enumerate(transitions):
        for t2 in list(transitions)[i+1:]:
            x1, y1 = new_positions[t1.id]
            x2, y2 = new_positions[t2.id]
            dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            final_distances.append((t1.label, t2.label, dist))
            print(f"  {t1.label} ↔ {t2.label}: {dist:.1f} units")
    print()
    
    # Show improvement
    print("="*80)
    print("COMPARISON:")
    print("="*80)
    print()
    
    avg_initial = sum(d[2] for d in initial_distances) / len(initial_distances)
    avg_final = sum(d[2] for d in final_distances) / len(final_distances)
    min_initial = min(d[2] for d in initial_distances)
    min_final = min(d[2] for d in final_distances)
    max_initial = max(d[2] for d in initial_distances)
    max_final = max(d[2] for d in final_distances)
    
    print(f"  Initial hub separation: {min_initial:.1f} - {max_initial:.1f} units (avg={avg_initial:.1f})")
    print(f"  Final hub separation:   {min_final:.1f} - {max_final:.1f} units (avg={avg_final:.1f})")
    print()
    
    improvement = (avg_final - avg_initial) / avg_initial * 100
    if improvement > 50:
        print(f"  ✅ EXCELLENT: {improvement:.0f}% improvement in hub separation!")
    elif improvement > 20:
        print(f"  ✅ GOOD: {improvement:.0f}% improvement in hub separation")
    elif improvement > 0:
        print(f"  ⚠️ MODEST: {improvement:.0f}% improvement in hub separation")
    else:
        print(f"  ❌ NO IMPROVEMENT: Hub separation decreased by {-improvement:.0f}%")
    print()
    
    # Target assessment
    TARGET_MIN_SEPARATION = 300.0  # We want hubs at least 300 units apart
    
    if min_final >= TARGET_MIN_SEPARATION:
        print(f"  ✅ TARGET MET: Minimum separation {min_final:.1f} >= {TARGET_MIN_SEPARATION} units")
    else:
        needed = TARGET_MIN_SEPARATION - min_final
        print(f"  ⚠️ TARGET NOT MET: Minimum separation {min_final:.1f} < {TARGET_MIN_SEPARATION} units")
        print(f"     Need {needed:.1f} more units. Try increasing PROXIMITY_CONSTANT further.")
    
    print()
    print("="*80)


if __name__ == '__main__':
    test_hub_separation()
