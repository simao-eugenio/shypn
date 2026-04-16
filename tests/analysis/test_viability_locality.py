#!/usr/bin/env python3
"""Test viability panel locality detection."""

import sys
from pathlib import Path

# This is a script-style test intended to be run directly (not via pytest).
if __name__ != '__main__':
    import pytest
    pytest.skip('Script-style test, run directly: python3 tests/analysis/test_viability_locality.py',
                allow_module_level=True)

# Get repo root (parent of tests directory)
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / 'src'))

from shypn.loaders import load_model
from shypn.diagnostic import LocalityDetector
from shypn.knowledge import KnowledgeBase

# Load a model - Note: BIOMD0000000003.xml not in fixtures, using BIOMD0000000001.xml
model_path = repo_root / 'tests/fixtures/BIOMD0000000001.xml'
print(f"Loading model: {model_path}")
model = load_model(model_path)

if not model:
    print("ERROR: Failed to load model")
    sys.exit(1)

print(f"Model loaded: {len(model.places)} places, {len(model.transitions)} transitions, {len(model.arcs)} arcs")

# Build KB
kb = KnowledgeBase(model)

# Get a transition
if not model.transitions:
    print("ERROR: No transitions in model")
    sys.exit(1)

transition = model.transitions[0]
print(f"\nTesting transition: {transition.id}")

# Use LocalityDetector
detector = LocalityDetector(model)
diagnostic_locality = detector.get_locality_for_transition(transition)

print(f"\nDiagnostic Locality:")
print(f"  Type: {type(diagnostic_locality)}")
print(f"  Transition: {diagnostic_locality.transition}")
print(f"  Input places: {len(diagnostic_locality.input_places)}")
for p in diagnostic_locality.input_places:
    print(f"    - {p.id} ({type(p).__name__})")
print(f"  Output places: {len(diagnostic_locality.output_places)}")
for p in diagnostic_locality.output_places:
    print(f"    - {p.id} ({type(p).__name__})")
print(f"  Input arcs: {len(diagnostic_locality.input_arcs)}")
for a in diagnostic_locality.input_arcs:
    print(f"    - {a.id} ({type(a).__name__})")
print(f"  Output arcs: {len(diagnostic_locality.output_arcs)}")
for a in diagnostic_locality.output_arcs:
    print(f"    - {a.id} ({type(a).__name__})")

# Convert to investigation Locality
from shypn.ui.panels.viability.investigation import Locality as InvestigationLocality

inv_locality = InvestigationLocality(
    transition_id=transition.id,
    input_places=[p.id for p in diagnostic_locality.input_places],
    output_places=[p.id for p in diagnostic_locality.output_places],
    input_arcs=[a.id for a in diagnostic_locality.input_arcs],
    output_arcs=[a.id for a in diagnostic_locality.output_arcs]
)

print(f"\nInvestigation Locality:")
print(f"  Type: {type(inv_locality)}")
print(f"  Transition ID: {inv_locality.transition_id}")
print(f"  Input places: {inv_locality.input_places}")
print(f"  Output places: {inv_locality.output_places}")
print(f"  Input arcs: {inv_locality.input_arcs}")
print(f"  Output arcs: {inv_locality.output_arcs}")

print("\n✓ Conversion successful!")
