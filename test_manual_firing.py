#!/usr/bin/env python3
"""
Manually test if a stochastic source transition can fire.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.immediate_behavior import ImmediateBehavior

model_path = "workspace/projects/Interactive/models/hsa00010.shy"
document = DocumentModel.load_from_file(model_path)

print("🧪 MANUAL FIRING TEST\n")

# Find a source transition (T35)
source_transition = None
for t in document.transitions:
    if t.id == '35':
        source_transition = t
        break

if not source_transition:
    print("❌ Source transition T35 not found!")
    sys.exit(1)

print(f"✅ Found source transition: {source_transition.name or source_transition.id}")

# Get its output arc
output_arcs = [arc for arc in document.arcs if hasattr(arc, 'source') and arc.source == source_transition]
print(f"   Output arcs: {len(output_arcs)}")

if not output_arcs:
    print("❌ No output arcs!")
    sys.exit(1)

target_place = output_arcs[0].target
print(f"   Target place: {target_place.name} (id={target_place.id})")
print(f"   Tokens before: {target_place.tokens}")

# Create behavior and try to fire
behavior = ImmediateBehavior(source_transition, document)

# Check if it can fire
can_fire, reason = behavior.can_fire()
print(f"\n   can_fire(): {can_fire}")
print(f"   Reason: {reason}")

if can_fire:
    # Fire it
    print("\n   🔥 Firing transition...")
    behavior.fire()
    print(f"   Tokens after: {target_place.tokens}")
    
    if target_place.tokens > 0:
        print("\n✅ SUCCESS: Source transition generated token!")
    else:
        print("\n❌ PROBLEM: Token not generated")
else:
    print(f"\n❌ CANNOT FIRE: {reason}")

# Now test a reaction transition that should fire after catalyst has tokens
print("\n\n🧪 TESTING REACTION TRANSITION (R00746 - T3)\n")

reaction = None
for t in document.transitions:
    if t.name == 'R00746' or t.id == 'T3':
        reaction = t
        break

if reaction:
    print(f"✅ Found reaction: {reaction.name} (id={reaction.id})")
    
    # Get input arcs
    input_arcs = [arc for arc in document.arcs if hasattr(arc, 'target') and arc.target == reaction]
    print(f"   Input arcs: {len(input_arcs)}")
    
    for arc in input_arcs:
        arc_type = type(arc).__name__
        source_name = arc.source.name if arc.source else "Unknown"
        source_tokens = arc.source.tokens if arc.source else 0
        has_consumes = hasattr(arc, 'consumes_tokens')
        consumes = arc.consumes_tokens() if has_consumes else "N/A"
        
        print(f"      {arc_type} from {source_name}: {source_tokens} tokens, consumes={consumes}")
    
    # Try to fire (should fail - no substrate tokens yet)
    behavior = ImmediateBehavior(reaction, document)
    can_fire, reason = behavior.can_fire()
    
    print(f"\n   can_fire(): {can_fire}")
    print(f"   Reason: {reason}")
    
    # Now manually add tokens to substrate and try again
    print("\n   💉 Manually adding tokens to substrate...")
    substrate_place = None
    for arc in input_arcs:
        if type(arc).__name__ == 'Arc':  # Regular arc (not test arc)
            substrate_place = arc.source
            break
    
    if substrate_place:
        substrate_place.tokens = 10
        print(f"   Set {substrate_place.name} to 10 tokens")
        
        # Try again
        can_fire2, reason2 = behavior.can_fire()
        print(f"\n   can_fire() after adding substrate: {can_fire2}")
        print(f"   Reason: {reason2}")
        
        if can_fire2:
            print("\n   🔥 Firing reaction...")
            print(f"   Substrate before: {substrate_place.tokens}")
            
            # Find catalyst
            catalyst_place = None
            for arc in input_arcs:
                if type(arc).__name__ == 'TestArc':
                    catalyst_place = arc.source
                    break
            
            if catalyst_place:
                print(f"   Catalyst before: {catalyst_place.tokens}")
            
            behavior.fire()
            
            print(f"   Substrate after: {substrate_place.tokens}")
            if catalyst_place:
                print(f"   Catalyst after: {catalyst_place.tokens}")
            
            if substrate_place.tokens == 9 and (not catalyst_place or catalyst_place.tokens == 1):
                print("\n✅ SUCCESS: Reaction fired correctly!")
                print("   - Substrate consumed (10 → 9)")
                print("   - Catalyst NOT consumed (stays at 1)")
            else:
                print("\n⚠️  Unexpected token counts after firing")
