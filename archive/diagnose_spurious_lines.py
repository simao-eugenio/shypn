#!/usr/bin/env python3
"""
Diagnose the source of non-interactive spurious lines.

This script helps identify what's drawing lines that:
- Appear in the GUI
- Are NOT selectable
- Don't respond to context menu
- Are NOT Arc objects
"""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

print("=" * 80)
print("SPURIOUS LINE DIAGNOSTIC")
print("=" * 80)

print("\n📋 INSTRUCTIONS:")
print("1. Launch the GUI: python3 src/shypn.py")
print("2. Import a KEGG pathway where you see spurious lines")
print("3. Save the file as 'test_spurious.shypn'")
print("4. Run this script again")
print("\nThis script will analyze the saved file to find non-Arc visual elements.")

import os
if not os.path.exists('test_spurious.shypn'):
    print("\n⚠️  File 'test_spurious.shypn' not found!")
    print("Please follow the instructions above and try again.")
    sys.exit(0)

print("\n" + "=" * 80)
print("ANALYZING SAVED FILE")
print("=" * 80)

# Load the file
import json
with open('test_spurious.shypn', 'r') as f:
    data = json.load(f)

print(f"\n📊 Document structure:")
print(f"   Keys in file: {list(data.keys())}")

# Check for unexpected visual elements
standard_keys = {'places', 'transitions', 'arcs', 'metadata', 'version', 'name'}
extra_keys = set(data.keys()) - standard_keys

if extra_keys:
    print(f"\n⚠️  UNEXPECTED KEYS FOUND: {extra_keys}")
    for key in extra_keys:
        print(f"\n   Content of '{key}':")
        print(f"   {data[key]}")
else:
    print(f"\n   ✅ Only standard keys found")

# Analyze arcs
print(f"\n🔍 Arc Analysis:")
arcs = data.get('arcs', [])
print(f"   Total arcs: {len(arcs)}")

place_ids = {p['id'] for p in data.get('places', [])}
transition_ids = {t['id'] for t in data.get('transitions', [])}

print(f"   Place IDs: {sorted(place_ids)[:10]}{'...' if len(place_ids) > 10 else ''}")
print(f"   Transition IDs: {sorted(transition_ids)[:10]}{'...' if len(transition_ids) > 10 else ''}")

# Check for invalid arcs
invalid_arcs = []
place_to_place = []
trans_to_trans = []

for arc in arcs:
    src_id = arc['source_id']
    tgt_id = arc['target_id']
    
    src_is_place = src_id in place_ids
    src_is_trans = src_id in transition_ids
    tgt_is_place = tgt_id in place_ids
    tgt_is_trans = tgt_id in transition_ids
    
    if not (src_is_place or src_is_trans):
        invalid_arcs.append(f"{arc['id']}: source '{src_id}' not found")
    if not (tgt_is_place or tgt_is_trans):
        invalid_arcs.append(f"{arc['id']}: target '{tgt_id}' not found")
    
    if src_is_place and tgt_is_place:
        place_to_place.append(f"{arc['id']}: {src_id} → {tgt_id}")
    elif src_is_trans and tgt_is_trans:
        trans_to_trans.append(f"{arc['id']}: {src_id} → {tgt_id}")

if invalid_arcs:
    print(f"\n   ⚠️  INVALID ARCS (endpoints missing):")
    for msg in invalid_arcs[:10]:
        print(f"      {msg}")
else:
    print(f"   ✅ All arcs have valid endpoints")

if place_to_place:
    print(f"\n   🐛 PLACE-TO-PLACE ARCS FOUND: {len(place_to_place)}")
    for msg in place_to_place[:10]:
        print(f"      {msg}")
else:
    print(f"   ✅ No place-to-place arcs")

if trans_to_trans:
    print(f"\n   🐛 TRANSITION-TO-TRANSITION ARCS: {len(trans_to_trans)}")
    for msg in trans_to_trans[:10]:
        print(f"      {msg}")
else:
    print(f"   ✅ No transition-to-transition arcs")

# Check for custom rendering attributes
print(f"\n🎨 Custom Rendering Attributes:")
for arc in arcs[:5]:  # Sample first 5 arcs
    custom_attrs = {k: v for k, v in arc.items() if k not in 
                   ['id', 'source_id', 'target_id', 'weight', 'control_points', 'metadata']}
    if custom_attrs:
        print(f"   Arc {arc['id']}: {custom_attrs}")

# Check place/transition for unusual attributes
print(f"\n🔍 Checking objects for custom rendering:")
for place in data.get('places', [])[:3]:
    unusual = {k for k in place.keys() if k not in 
              ['id', 'name', 'label', 'x', 'y', 'radius', 'tokens', 'initial_marking',
               'border_color', 'border_width', 'metadata']}
    if unusual:
        print(f"   Place {place['id']} has unusual keys: {unusual}")

for trans in data.get('transitions', [])[:3]:
    unusual = {k for k in trans.keys() if k not in 
              ['id', 'name', 'label', 'x', 'y', 'width', 'height', 'horizontal',
               'border_color', 'border_width', 'metadata']}
    if unusual:
        print(f"   Transition {trans['id']} has unusual keys: {unusual}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if place_to_place or trans_to_trans or extra_keys:
    print("\n🐛 POTENTIAL SOURCES OF SPURIOUS LINES FOUND!")
    if place_to_place:
        print(f"   - {len(place_to_place)} place-to-place arcs (should not exist!)")
    if trans_to_trans:
        print(f"   - {len(trans_to_trans)} transition-to-transition arcs (should not exist!)")
    if extra_keys:
        print(f"   - Extra data keys: {extra_keys} (may contain visual elements)")
else:
    print("\n✅ No obvious data-level issues found")
    print("\n💡 HYPOTHESIS: Lines are drawn by rendering code, not stored data")
    print("   Possible causes:")
    print("   1. KEGG relation visualization (protein-protein, gene expression)")
    print("   2. Legacy rendering code still active")
    print("   3. Transition size issue (transitions too small to see)")
    print("\n   Next steps:")
    print("   - Check if GUI has 'Show Relations' option enabled")
    print("   - Try zooming in to see if tiny transitions exist")
    print("   - Check for any KEGG-specific rendering toggles")
