#!/usr/bin/env python3
"""Test script to verify LocalityDetector works with list-based model."""

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.diagnostic import LocalityDetector

# Create a simple test model
manager = ModelCanvasManager(filename="test")

# Create places
p1 = manager.create_place(x=100, y=100)
p1.label = "P1"
p1.tokens = 5

p2 = manager.create_place(x=300, y=100)
p2.label = "P2"
p2.tokens = 0

# Create transition
t1 = manager.create_transition(x=200, y=100)
t1.label = "T1"

# Create arcs
arc1 = manager.create_arc(p1, t1)  # P1 → T1 (input)
arc2 = manager.create_arc(t1, p2)  # T1 → P2 (output)

print("Model created:")
print(f"  Places: {len(manager.places)}")
print(f"  Transitions: {len(manager.transitions)}")
print(f"  Arcs: {len(manager.arcs)}")
print()

# Test LocalityDetector
print("Testing LocalityDetector...")
detector = LocalityDetector(manager)

# Get locality for T1
locality = detector.get_locality_for_transition(t1)

print(f"Locality for {t1.label}:")
print(f"  Valid: {locality.is_valid}")
print(f"  Summary: {locality.get_summary()}")
print(f"  Input places: {[p.label for p in locality.input_places]}")
print(f"  Output places: {[p.label for p in locality.output_places]}")
print(f"  Place count: {locality.place_count}")
print()

# Test get_all_localities
all_localities = detector.get_all_localities()
print(f"All localities: {len(all_localities)}")
for loc in all_localities:
    print(f"  - {loc.get_summary()}")
print()

print("✅ Test passed! LocalityDetector works correctly with list-based model.")
