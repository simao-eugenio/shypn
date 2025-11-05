#!/usr/bin/env python3
"""
Comprehensive diagnostic of KEGG model catalyst behavior.

This tests the ACTUAL loaded model to verify:
1. Arcs are loaded as TestArc objects
2. Catalysts have initial_marking=1
3. Tokens are properly initialized
4. Transitions can be enabled
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs.test_arc import TestArc
from shypn.engine.immediate_behavior import ImmediateBehavior

print("=" * 80)
print("DIAGNOSTIC: KEGG Model Catalyst Behavior")
print("=" * 80)

# Load the FIXED model
model_path = '/home/simao/projetos/shypn/workspace/projects/models/hsa00010_FIXED.shy'
print(f"\nLoading model: {model_path}")

# load_from_file is a classmethod that RETURNS a new document
document = DocumentModel.load_from_file(model_path)

print(f"\n✓ Model loaded successfully")
print(f"  Places: {len(document.places)}")
print(f"  Transitions: {len(document.transitions)}")
print(f"  Arcs: {len(document.arcs)}")

# Count catalysts
catalysts = [p for p in document.places if getattr(p, 'is_catalyst', False)]
print(f"  Catalysts: {len(catalysts)}")

# Count test arcs
test_arcs = [a for a in document.arcs if isinstance(a, TestArc)]
print(f"  TestArc objects: {len(test_arcs)}")

# Check if test arcs are actually TestArc instances
print("\n" + "=" * 80)
print("ARC TYPE VERIFICATION")
print("=" * 80)

arc_types = {}
for arc in document.arcs:
    arc_class = type(arc).__name__
    arc_types[arc_class] = arc_types.get(arc_class, 0) + 1

for arc_class, count in sorted(arc_types.items()):
    print(f"  {arc_class}: {count}")

if len(test_arcs) == 0:
    print("\n❌ PROBLEM: No TestArc objects found!")
    print("   Test arcs may have been loaded as regular Arc objects")
    
    # Check arc_type attribute
    test_type_arcs = [a for a in document.arcs if getattr(a, 'arc_type', None) == 'test']
    print(f"\n   Arcs with arc_type='test': {len(test_type_arcs)}")
    
    if len(test_type_arcs) > 0:
        sample = test_type_arcs[0]
        print(f"\n   Sample arc with arc_type='test':")
        print(f"     Class: {type(sample).__name__}")
        print(f"     ID: {sample.id}")
        print(f"     arc_type: {getattr(sample, 'arc_type', 'N/A')}")
        print(f"     consumes_tokens(): {sample.consumes_tokens() if hasattr(sample, 'consumes_tokens') else 'N/A'}")
        print(f"     is_test_arc(): {sample.is_test_arc() if hasattr(sample, 'is_test_arc') else 'N/A'}")
else:
    print("\n✅ TestArc objects loaded correctly")
    
    # Sample a test arc
    sample = test_arcs[0]
    print(f"\nSample TestArc:")
    print(f"  ID: {sample.id}")
    print(f"  Source: {sample.source.id if sample.source else 'None'} ({type(sample.source).__name__})")
    print(f"  Target: {sample.target.id if sample.target else 'None'} ({type(sample.target).__name__})")
    print(f"  Weight: {sample.weight}")
    print(f"  consumes_tokens(): {sample.consumes_tokens()}")

# Check catalyst tokens
print("\n" + "=" * 80)
print("CATALYST TOKEN VERIFICATION")
print("=" * 80)

catalyst_token_dist = {}
for cat in catalysts:
    tokens = cat.tokens
    initial = cat.initial_marking
    key = (tokens, initial)
    catalyst_token_dist[key] = catalyst_token_dist.get(key, 0) + 1

print("\nCatalyst token distribution:")
for (tokens, initial), count in sorted(catalyst_token_dist.items()):
    status = "✅" if tokens >= 1 else "❌"
    print(f"  tokens={tokens}, initial_marking={initial}: {count} catalysts {status}")

# Check transition enablement
print("\n" + "=" * 80)
print("TRANSITION ENABLEMENT VERIFICATION")
print("=" * 80)

enabled_transitions = []
disabled_transitions = []

for transition in document.transitions:
    # Get transition type
    trans_type = getattr(transition, 'type', 'immediate')
    
    # Create appropriate behavior
    if trans_type == 'immediate':
        behavior = ImmediateBehavior(transition, document)
    else:
        print(f"  Skipping {transition.id} (type={trans_type})")
        continue
    
    # Check if enabled
    enabled = behavior.is_enabled()
    
    if enabled:
        enabled_transitions.append(transition.id)
    else:
        disabled_transitions.append(transition.id)

print(f"\nEnablement status:")
print(f"  Enabled: {len(enabled_transitions)}/{len(document.transitions)}")
print(f"  Disabled: {len(disabled_transitions)}/{len(document.transitions)}")

# Analyze disabled transitions
if len(disabled_transitions) > 0:
    print(f"\n  Analyzing first disabled transition...")
    
    trans_id = disabled_transitions[0]
    # Find transition in list
    transition = next((t for t in document.transitions if t.id == trans_id), None)
    
    if transition:
        print(f"\n  Transition {trans_id} ({transition.label}):")
        
        # Get input arcs
        input_arcs = [a for a in document.arcs if a.target == transition]
        print(f"    Input arcs: {len(input_arcs)}")
    
    for arc in input_arcs:
        source_place = arc.source
        is_test = isinstance(arc, TestArc)
        arc_type_str = "TestArc" if is_test else type(arc).__name__
        
        print(f"      {arc.id}: {source_place.id} -> {transition.id}")
        print(f"        Type: {arc_type_str}")
        print(f"        Weight: {arc.weight}")
        print(f"        Source tokens: {source_place.tokens}")
        print(f"        Source is_catalyst: {getattr(source_place, 'is_catalyst', False)}")
        
        # Check if this arc blocks the transition
        if is_test:
            blocked = source_place.tokens < arc.weight
            status = "❌ BLOCKS" if blocked else "✅ OK"
            print(f"        Status: {status} (test arc needs tokens >= {arc.weight})")
        else:
            blocked = source_place.tokens < arc.weight
            status = "❌ BLOCKS" if blocked else "✅ OK"
            print(f"        Status: {status} (needs tokens >= {arc.weight})")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

issues = []

if len(test_arcs) == 0:
    issues.append("❌ No TestArc objects loaded (test arcs loaded as regular Arc)")

if any(tokens < 1 for tokens, _ in catalyst_token_dist.keys()):
    issues.append("❌ Some catalysts have tokens < 1 (will block transitions)")

if len(disabled_transitions) == len(document.transitions):
    issues.append("❌ ALL transitions disabled (simulation cannot execute)")

if len(issues) == 0:
    print("\n✅ ALL CHECKS PASSED!")
    print("\nThe model is correctly configured:")
    print("  - TestArc objects loaded properly")
    print("  - Catalysts have sufficient tokens")
    print("  - Some transitions are enabled")
    print("\nThe model should simulate correctly.")
else:
    print("\n⚠️  ISSUES FOUND:")
    for issue in issues:
        print(f"  {issue}")
    print("\nThese issues will prevent proper simulation.")

print("=" * 80)
