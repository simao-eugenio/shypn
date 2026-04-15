#!/usr/bin/env python3
"""Test loading hsa00010.shy and verify A67 and A17 are SignalFlowArcs with light gray color."""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs.signal_flow_arc import SignalFlowArc

# Load the file
model_path = Path(__file__).parent.parent / 'workspace' / 'projects' / 'My_Project' / 'models' / 'hsa00010.shy'

print(f"Loading: {model_path}")
document = DocumentModel.load_from_file(str(model_path))

print(f"\nLoaded model:")
print(f"  Places: {len(document.places)}")
print(f"  Transitions: {len(document.transitions)}")
print(f"  Arcs: {len(document.arcs)}")

# Find arcs A67 and A17
arc_a67 = None
arc_a17 = None

for arc in document.arcs:
    if arc.id == "A67":
        arc_a67 = arc
    elif arc.id == "A17":
        arc_a17 = arc

print(f"\n{'='*70}")
print("Arc A67 (T31 → P18 acetyl-CoA):")
if arc_a67:
    print(f"  Type: {arc_a67.__class__.__name__}")
    print(f"  Is SignalFlowArc: {isinstance(arc_a67, SignalFlowArc)}")
    print(f"  Color: {arc_a67.color}")
    print(f"  Expected: (0.7, 0.7, 0.7) light gray")
    if arc_a67.color == (0.7, 0.7, 0.7):
        print(f"  ✅ CORRECT COLOR!")
    else:
        print(f"  ❌ WRONG COLOR!")
else:
    print("  ❌ Arc A67 not found!")

print(f"\n{'='*70}")
print("Arc A17 (P18 acetyl-CoA → T7):")
if arc_a17:
    print(f"  Type: {arc_a17.__class__.__name__}")
    print(f"  Is SignalFlowArc: {isinstance(arc_a17, SignalFlowArc)}")
    print(f"  Color: {arc_a17.color}")
    print(f"  Expected: (0.7, 0.7, 0.7) light gray")
    if arc_a17.color == (0.7, 0.7, 0.7):
        print(f"  ✅ CORRECT COLOR!")
    else:
        print(f"  ❌ WRONG COLOR!")
else:
    print("  ❌ Arc A17 not found!")

# Find P18
place_p18 = None
for place in document.places:
    if place.id == "P18":
        place_p18 = place
        break

if place_p18:
    print(f"\n{'='*70}")
    print("Place P18 (acetyl-CoA):")
    print(f"  Name: {place_p18.name}")
    print(f"  is_signal_place: {getattr(place_p18, 'is_signal_place', False)}")
    print(f"  is_energy_signal: {place_p18.metadata.get('is_energy_signal', False)}")
    print(f"  signal_type: {place_p18.metadata.get('signal_type', 'N/A')}")
    print(f"  Border color: {place_p18.border_color}")

# Count all SignalFlowArcs
signal_arcs = [arc for arc in document.arcs if isinstance(arc, SignalFlowArc)]
print(f"\n{'='*70}")
print(f"Total SignalFlowArcs in model: {len(signal_arcs)}")

# Summary
print(f"\n{'='*70}")
print("RESULT:")
if arc_a67 and arc_a17:
    if isinstance(arc_a67, SignalFlowArc) and isinstance(arc_a17, SignalFlowArc):
        if arc_a67.color == (0.7, 0.7, 0.7) and arc_a17.color == (0.7, 0.7, 0.7):
            print("✅ PASS: Both arcs are SignalFlowArcs with correct light gray color!")
            sys.exit(0)
        else:
            print("❌ FAIL: Arcs are SignalFlowArcs but have wrong colors!")
            sys.exit(1)
    else:
        print("❌ FAIL: Arcs are not SignalFlowArcs!")
        sys.exit(1)
else:
    print("❌ FAIL: Could not find arcs A67 and/or A17!")
    sys.exit(1)
