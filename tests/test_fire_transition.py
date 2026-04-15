#!/usr/bin/env python3
"""Test actual transition firing with test arc."""

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.immediate_behavior import ImmediateBehavior

print("=" * 60)
print("Loading and firing test.shy model")
print("=" * 60)

# Load the model
model_path = "workspace/projects/My_Project/models/test.shy"
with open(model_path, 'r') as f:
    import json
    data = json.load(f)

# Create document from dict
document = DocumentModel.from_dict(data)

# Get transition T2
transition = None
for t in document.transitions:
    if t.id == 'T2':
        transition = t
        break

# Get arc A3 (test arc)
test_arc = None
for arc in document.arcs:
    if arc.id == 'A3':
        test_arc = arc
        break

print(f"\nTransition: {transition.id}")
print(f"  Type: {transition.transition_type}")

# Create behavior instance (needed to get arcs)
behavior = ImmediateBehavior(transition, document)

input_arcs = behavior.get_input_arcs()
output_arcs = behavior.get_output_arcs()

print(f"  Input arcs: {len(input_arcs)}")
print(f"  Output arcs: {len(output_arcs)}")

print(f"\nTest Arc A3:")
print(f"  Class: {type(test_arc).__name__}")
print(f"  arc_type: {test_arc.arc_type}")
print(f"  consumes_tokens(): {test_arc.consumes_tokens()}")

# Check place tokens BEFORE
p3 = document.places[0]
p4 = document.places[1]
print(f"\nBEFORE firing:")
print(f"  P3: {p3.tokens} tokens")
print(f"  P4: {p4.tokens} tokens")

# Check enablement
enabled = behavior.is_enabled()
print(f"\nTransition enabled: {enabled}")

if enabled:
    # Get input/output arcs
    input_arcs = behavior.get_input_arcs()
    output_arcs = behavior.get_output_arcs()
    
    print(f"\nInput arcs: {len(input_arcs)}")
    for arc in input_arcs:
        print(f"  {arc.id}: {type(arc).__name__}, consumes={arc.consumes_tokens()}")
    
    print(f"\nOutput arcs: {len(output_arcs)}")
    for arc in output_arcs:
        print(f"  {arc.id}: {type(arc).__name__}")
    
    # Fire the transition
    print("\n" + "=" * 60)
    print("FIRING TRANSITION")
    print("=" * 60)
    
    success, result = behavior.fire(input_arcs, output_arcs)
    
    print(f"\nFire result: {success}")
    if success:
        print(f"Consumed: {result.get('consumed', {})}")
        print(f"Produced: {result.get('produced', {})}")
    else:
        print(f"Error: {result}")
    
    # Check place tokens AFTER
    print(f"\nAFTER firing:")
    print(f"  P3: {p3.tokens} tokens")
    print(f"  P4: {p4.tokens} tokens")
    
    print("\n" + "=" * 60)
    print("ANALYSIS")
    print("=" * 60)
    
    if p3.tokens == 25:
        print("✓ CORRECT: P3 tokens unchanged (test arc did NOT consume)")
    else:
        print("✗ BUG: P3 tokens changed from 25 to", p3.tokens)
        print("  Test arc CONSUMED tokens (should not!)")
    
    if p4.tokens == 1:
        print("✓ CORRECT: P4 gained 1 token")
    else:
        print("✗ ERROR: P4 should have 1 token, has", p4.tokens)
else:
    print("\nTransition NOT enabled - cannot fire")
