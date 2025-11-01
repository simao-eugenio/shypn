#!/usr/bin/env python3
"""
Diagnose test arcs at runtime by inspecting the actual loaded document.
This checks if Arc.from_dict() fix is working.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load the saved file and check arc types
from shypn.data.canvas.document_model import DocumentModel

model_path = "workspace/projects/Interactive/models/hsa00010.shy"
print(f"Loading model: {model_path}\n")

document = DocumentModel.load_from_file(model_path)

print(f"📊 LOADED DOCUMENT:")
print(f"   Places: {len(document.places)}")
print(f"   Transitions: {len(document.transitions)}")
print(f"   Arcs: {len(document.arcs)}\n")

# Check place tokens
catalyst_places = 0
places_with_tokens = 0
for place in document.places:
    if place.tokens > 0:
        places_with_tokens += 1
        # Check if it's connected to test arcs (catalyst)
        is_catalyst = False
        for arc in document.arcs:
            if hasattr(arc, 'source') and arc.source == place:
                arc_type = type(arc).__name__
                if arc_type == 'TestArc':
                    is_catalyst = True
                    break
        if is_catalyst:
            catalyst_places += 1

print(f"🎯 PLACES WITH TOKENS: {places_with_tokens}")
print(f"   Catalysts with tokens: {catalyst_places}\n")

# Sample a few places with tokens
print("Sample places with tokens:")
count = 0
for place in document.places:
    if place.tokens > 0 and count < 5:
        print(f"  - {place.name}: {place.tokens} tokens (initial_marking={place.initial_marking})")
        count += 1

print()

# Check arc types
arc_types = {}
test_arcs = []

for arc in document.arcs:
    arc_type = type(arc).__name__
    arc_types[arc_type] = arc_types.get(arc_type, 0) + 1
    
    if arc_type == 'TestArc':
        test_arcs.append(arc)
    elif hasattr(arc, 'consumes_tokens') and callable(arc.consumes_tokens):
        if not arc.consumes_tokens():
            test_arcs.append(arc)
            print(f"⚠️  Non-TestArc with consumes_tokens()=False: {arc_type}")

print(f"🔍 ARC TYPE DISTRIBUTION:")
for arc_type, count in sorted(arc_types.items()):
    print(f"   {arc_type}: {count}")

print()
print(f"📌 TEST ARCS: {len(test_arcs)}")

if test_arcs:
    print("\nFirst 3 test arcs:")
    for i, arc in enumerate(test_arcs[:3], 1):
        arc_type = type(arc).__name__
        has_method = hasattr(arc, 'consumes_tokens')
        consumes = arc.consumes_tokens() if has_method else "N/A"
        
        source_name = arc.source.name if arc.source else "Unknown"
        target_name = arc.target.name if arc.target else "Unknown"
        
        print(f"{i}. {arc.name}")
        print(f"   Type: {arc_type}")
        print(f"   Source: {source_name}")
        print(f"   Target: {target_name}")
        print(f"   consumes_tokens(): {consumes}")

    print()
    
    # Verify all are TestArc instances
    all_correct = all(type(arc).__name__ == 'TestArc' for arc in test_arcs)
    if all_correct:
        print("✅ SUCCESS: All test arcs are TestArc instances!")
    else:
        print("❌ PROBLEM: Some test arcs are not TestArc instances")
        wrong_types = [type(arc).__name__ for arc in test_arcs if type(arc).__name__ != 'TestArc']
        print(f"   Wrong types: {set(wrong_types)}")
else:
    print("❌ NO TEST ARCS FOUND!")

print()

# Now check a specific transition to see why it won't fire
print("🔍 CHECKING SPECIFIC TRANSITION (R00746 - T3):")
transition = None
for t in document.transitions:
    if t.name == 'R00746' or t.id == 'T3':
        transition = t
        break

if transition:
    print(f"   Found transition: {transition.name} (id={transition.id})")
    
    # Get input arcs
    input_arcs = [arc for arc in document.arcs if hasattr(arc, 'target') and arc.target == transition]
    print(f"   Input arcs: {len(input_arcs)}")
    
    for arc in input_arcs:
        arc_type = type(arc).__name__
        source_name = arc.source.name if arc.source else "Unknown"
        source_tokens = arc.source.tokens if arc.source else 0
        weight = arc.weight if hasattr(arc, 'weight') else 1
        
        has_consumes = hasattr(arc, 'consumes_tokens')
        consumes = arc.consumes_tokens() if has_consumes else "N/A (no method)"
        
        status = "✅" if source_tokens >= weight else "❌"
        
        print(f"   {status} Arc from {source_name}:")
        print(f"      Type: {arc_type}")
        print(f"      Tokens: {source_tokens} >= {weight}? {source_tokens >= weight}")
        print(f"      consumes_tokens(): {consumes}")
