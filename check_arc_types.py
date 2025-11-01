#!/usr/bin/env python3
"""
Check if test arcs are loaded as TestArc instances in the saved file.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.netobjs.net import Net

# Load the model
model_path = "workspace/projects/Interactive/models/hsa00010.shy"
print(f"Loading model: {model_path}\n")

net = Net.load(model_path)

print(f"📊 MODEL: {net.name}")
print(f"   Places: {len(net.places)}")
print(f"   Transitions: {len(net.transitions)}")
print(f"   Arcs: {len(net.arcs)}\n")

# Check test arcs
test_arcs = []
for arc in net.arcs:
    # Check if it's a TestArc instance
    arc_type = type(arc).__name__
    has_consumes_method = hasattr(arc, 'consumes_tokens')
    
    if arc_type == 'TestArc':
        test_arcs.append(arc)
    elif has_consumes_method:
        consumes = arc.consumes_tokens()
        if not consumes:
            test_arcs.append(arc)
            print(f"⚠️  Found non-TestArc with consumes_tokens()=False: {arc_type}")

print(f"🔍 FOUND {len(test_arcs)} TEST ARCS:\n")

for i, arc in enumerate(test_arcs[:5], 1):  # Show first 5
    arc_type = type(arc).__name__
    has_method = hasattr(arc, 'consumes_tokens')
    consumes = arc.consumes_tokens() if has_method else "N/A (missing method)"
    
    source_name = arc.source.name if arc.source else "Unknown"
    target_name = arc.target.name if arc.target else "Unknown"
    
    print(f"{i}. {arc.name or 'unnamed'}")
    print(f"   Source: {source_name}")
    print(f"   Target: {target_name}")
    print(f"   Type: {arc_type}")
    print(f"   Has consumes_tokens(): {has_method}")
    print(f"   consumes_tokens() returns: {consumes}")
    print()

if len(test_arcs) > 5:
    print(f"   ... and {len(test_arcs) - 5} more test arcs\n")

# Check if any regular arcs exist
regular_arcs = [arc for arc in net.arcs if type(arc).__name__ == 'Arc']
print(f"📌 Regular Arc instances: {len(regular_arcs)}")
print(f"📌 TestArc instances: {len(test_arcs)}")
print(f"📌 Other arc types: {len(net.arcs) - len(regular_arcs) - len(test_arcs)}")

# Verify the fix worked
if len(test_arcs) > 0 and all(type(arc).__name__ == 'TestArc' for arc in test_arcs):
    print("\n✅ SUCCESS: All test arcs loaded as TestArc instances!")
else:
    print("\n❌ PROBLEM: Test arcs not loaded correctly")
