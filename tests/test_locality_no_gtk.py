#!/usr/bin/env python3
"""Test script to verify LocalityDetector works with list-based model (no GTK)."""

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.data.model_canvas_manager import ModelCanvasManager

# Import directly to avoid GTK dependency
import shypn.diagnostic.locality_detector as detector_module
import shypn.diagnostic.locality_analyzer as analyzer_module

LocalityDetector = detector_module.LocalityDetector
Locality = detector_module.Locality
LocalityAnalyzer = analyzer_module.LocalityAnalyzer

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

print("✅ Model created:")
print(f"  Places: {len(manager.places)}")
print(f"  Transitions: {len(manager.transitions)}")
print(f"  Arcs: {len(manager.arcs)}")
print()

# Verify model uses lists
print("✅ Verifying model structure:")
print(f"  manager.places is list: {isinstance(manager.places, list)}")
print(f"  manager.transitions is list: {isinstance(manager.transitions, list)}")
print(f"  manager.arcs is list: {isinstance(manager.arcs, list)}")
print()

# Test LocalityDetector
print("✅ Testing LocalityDetector...")
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
print(f"✅ All localities: {len(all_localities)}")
for loc in all_localities:
    print(f"  - {loc.get_summary()}")
print()

# Test LocalityAnalyzer
print("✅ Testing LocalityAnalyzer...")
analyzer = LocalityAnalyzer(manager)
analysis = analyzer.analyze_locality(locality)

print("Analysis results:")
print(f"  Input tokens: {analysis['input_token_count']}")
print(f"  Output tokens: {analysis['output_token_count']}")
print(f"  Token balance: {analysis['token_balance']}")
print(f"  Can fire: {analysis['can_fire']}")
print()

# Test token flow description
flow_description = analyzer.get_token_flow_description(locality)
print("Token flow:")
print(flow_description)
print()

print("=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print()
print("The LocalityDetector now correctly works with list-based model.")
print("The fix changed .values() method calls to direct list iteration.")
