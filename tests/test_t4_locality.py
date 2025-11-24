#!/usr/bin/env python3
"""Test T4 locality detection with catalyst support."""
import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.diagnostic.locality_detector import LocalityDetector

# Load model
print("Loading BIOMD0000000010.shy...")
model_path = '/home/simao/projetos/shypn/workspace/projects/My_Project/models/BIOMD0000000010.shy'
document = DocumentModel.load_from_file(model_path)

print(f"Loaded: {len(document.places)} places, {len(document.transitions)} transitions\n")

# Find T4
t4 = next((t for t in document.transitions if t.id == 'T4'), None)
if not t4:
    print("ERROR: T4 not found!")
    sys.exit(1)

print(f"T4: {t4.label}")
print(f"  ID: {t4.id}")
print(f"  Position: ({t4.x}, {t4.y})")

# Check arcs connected to T4
print(f"\nArcs connected to T4:")
incoming_arcs = [a for a in document.arcs if a.target.id == t4.id]
outgoing_arcs = [a for a in document.arcs if a.source.id == t4.id]

print(f"  Incoming arcs ({len(incoming_arcs)}):")
for arc in incoming_arcs:
    arc_type = getattr(arc, 'arc_type', 'normal')
    consumes = arc.consumes_tokens() if hasattr(arc, 'consumes_tokens') else True
    print(f"    {arc.source.id} ({arc.source.label}) --[{arc_type}, consumes={consumes}]--> T4")

print(f"  Outgoing arcs ({len(outgoing_arcs)}):")
for arc in outgoing_arcs:
    arc_type = getattr(arc, 'arc_type', 'normal')
    print(f"    T4 --[{arc_type}]--> {arc.target.id} ({arc.target.label})")

# Create a minimal model manager wrapper
class MinimalManager:
    def __init__(self, document):
        self.places = document.places
        self.transitions = document.transitions
        self.arcs = document.arcs

manager = MinimalManager(document)

# Detect locality
print(f"\n{'='*60}")
print("LOCALITY DETECTION:")
print('='*60)
detector = LocalityDetector(manager)
locality = detector.get_locality_for_transition(t4)

print(f"\nLocality for T4:")
print(f"  Is valid: {locality.is_valid}")
print(f"  Place count: {locality.place_count}")
print(f"  Catalyst count: {locality.catalyst_count}")
print(f"  Dual-role count: {locality.dual_role_count}")

print(f"\n  Input places ({len(locality.input_places)}):")
for p in locality.input_places:
    print(f"    - {p.id} ({p.label})")

print(f"\n  Output places ({len(locality.output_places)}):")
for p in locality.output_places:
    print(f"    - {p.id} ({p.label})")

print(f"\n  Catalyst places ({len(locality.catalyst_places)}):")
for p in locality.catalyst_places:
    print(f"    - {p.id} ({p.label})")

print(f"\n  Dual-role places ({len(locality.dual_role_places)}):")
for p in locality.dual_role_places:
    print(f"    - {p.id} ({p.label})")

print(f"\n{'='*60}")
print("EXPECTED IN UI:")
print('='*60)
print("Transition Panel should show:")
print(f"  • T4 ({t4.label})")
for p in locality.input_places:
    print(f"    ← Input: {p.label}")
for p in locality.catalyst_places:
    print(f"    ⋯ Catalyst: {p.label}")
for p in locality.output_places:
    print(f"    → Output: {p.label}")

print("\nPlaces Panel should show:")
all_places = set(locality.input_places) | set(locality.catalyst_places) | set(locality.output_places)
for p in all_places:
    print(f"  • {p.id} ({p.label})")

print(f"\n{'='*60}")
print(f"Total places in locality: {len(all_places)}")
print('='*60)
