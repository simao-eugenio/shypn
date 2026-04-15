#!/usr/bin/env python3
"""Load the actual test.shy model and inspect the arc."""

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs.test_arc import TestArc

print("=" * 60)
print("Loading test.shy model")
print("=" * 60)

# Load the model
model_path = "workspace/projects/My_Project/models/test.shy"
with open(model_path, 'r') as f:
    import json
    data = json.load(f)

# Create document from dict
document = DocumentModel.from_dict(data)

print(f"\nLoaded {len(document.places)} places, {len(document.transitions)} transitions, {len(document.arcs)} arcs")

# Inspect each arc
print("\n" + "=" * 60)
print("Arc Inspection")
print("=" * 60)

for arc in document.arcs:
    print(f"\nArc: {arc.id}")
    print(f"  Class: {type(arc).__name__}")
    print(f"  arc_type property: {arc.arc_type}")
    print(f"  Is TestArc instance: {isinstance(arc, TestArc)}")
    print(f"  Has consumes_tokens: {hasattr(arc, 'consumes_tokens')}")
    if hasattr(arc, 'consumes_tokens'):
        print(f"  consumes_tokens(): {arc.consumes_tokens()}")
    print(f"  Source: {arc.source.id} ({type(arc.source).__name__})")
    print(f"  Target: {arc.target.id} ({type(arc.target).__name__})")
    print(f"  Weight: {arc.weight}")
    
    # Check if this is the test arc from P3->T2
    if arc.source_id == 'P3' and arc.target_id == 'T2':
        print("\n  *** THIS IS THE TEST ARC ***")
        print(f"  Will it be skipped during consumption? {not arc.consumes_tokens()}")

print("\n" + "=" * 60)
print("Test places initial state")
print("=" * 60)

for place in document.places:
    print(f"Place {place.id}: {place.tokens} tokens")

print("\n" + "=" * 60)
print("CONCLUSION")
print("=" * 60)

test_arc = None
for arc in document.arcs:
    if arc.source_id == 'P3' and arc.target_id == 'T2':
        test_arc = arc
        break

if test_arc:
    if isinstance(test_arc, TestArc) and not test_arc.consumes_tokens():
        print("✓ Test arc is correctly loaded as TestArc instance")
        print("✓ consumes_tokens() returns False")
        print("✓ Should NOT consume tokens during firing")
    else:
        print("✗ PROBLEM FOUND:")
        if not isinstance(test_arc, TestArc):
            print(f"  Arc is {type(test_arc).__name__}, not TestArc")
        if test_arc.consumes_tokens():
            print(f"  consumes_tokens() returns True (should be False)")
