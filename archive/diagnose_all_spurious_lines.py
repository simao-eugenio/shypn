#!/usr/bin/env python3
"""
Comprehensive diagnostic for spurious lines issue.

This script checks multiple possible sources:
1. Invalid place-to-place arcs in data model
2. KEGG relations being drawn
3. Tiny invisible transitions
4. Visual/test arcs
"""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

print("=" * 80)
print("SPURIOUS LINES COMPREHENSIVE DIAGNOSTIC")
print("=" * 80)

print("\n📋 HOW TO USE THIS SCRIPT:")
print("\n1. Launch GUI: python3 src/shypn.py")
print("2. Import a KEGG pathway where you see spurious lines")
print("3. Take note of a compound ID that has spurious lines (e.g., C01451)")
print("4. Save the file (anywhere)")
print("5. Run: python3 diagnose_all_spurious_lines.py <path_to_file>\n")

# Step 1: Get file path from argument or look for default
import os

# Check for command line argument
if len(sys.argv) > 1:
    filepath = sys.argv[1]
else:
    # Look for file in common locations
    search_paths = [
        'test_spurious.shypn',
        'workspace/projects/diagnose_all_spurious.shypn.shyn',
        'workspace/projects/*.shyn',
        'workspace/projects/*.shypn'
    ]
    
    import glob
    filepath = None
    for pattern in search_paths:
        matches = glob.glob(pattern)
        if matches:
            filepath = matches[0]
            print(f"📁 Found file: {filepath}")
            break
    
    if not filepath:
        print("⚠️  No spurious line test file found!")
        print("\nUsage:")
        print("  python3 diagnose_all_spurious_lines.py <path_to_saved_file>")
        print("\nOr save a file as 'test_spurious.shypn' in the project root")
        sys.exit(0)

if not os.path.exists(filepath):
    print(f"❌ File not found: {filepath}")
    sys.exit(1)

print("=" * 80)
print(f"ANALYZING SAVED FILE: {filepath}")
print("=" * 80)

# Load saved file
import json
with open(filepath, 'r') as f:
    data = json.load(f)

places = {p['id']: p for p in data.get('places', [])}
transitions = {t['id']: t for t in data.get('transitions', [])}
arcs = data.get('arcs', [])

print(f"\n📊 Model Statistics:")
print(f"   Places: {len(places)}")
print(f"   Transitions: {len(transitions)}")
print(f"   Arcs: {len(arcs)}")

# Check 1: Invalid arcs (place-to-place, transition-to-transition)
print(f"\n" + "=" * 80)
print("CHECK 1: INVALID ARCS IN DATA MODEL")
print("=" * 80)

place_to_place = []
trans_to_trans = []

for arc in arcs:
    src_id = arc['source_id']
    tgt_id = arc['target_id']
    
    src_is_place = src_id in places
    tgt_is_place = tgt_id in places
    
    if src_is_place and tgt_is_place:
        place_to_place.append((arc['id'], src_id, tgt_id, arc))

    src_is_trans = src_id in transitions
    tgt_is_trans = tgt_id in transitions
    
    if src_is_trans and tgt_is_trans:
        trans_to_trans.append((arc['id'], src_id, tgt_id, arc))

if place_to_place:
    print(f"\n🐛 FOUND {len(place_to_place)} PLACE-TO-PLACE ARCS!")
    print(f"   This IS the bug - these should not exist!\n")
    for arc_id, src_id, tgt_id, arc_data in place_to_place[:10]:
        src_place = places[src_id]
        tgt_place = places[tgt_id]
        src_label = src_place.get('label', src_id)
        tgt_label = tgt_place.get('label', tgt_id)
        print(f"   Arc {arc_id}: {src_label} ({src_id}) → {tgt_label} ({tgt_id})")
else:
    print(f"\n✅ No place-to-place arcs in data model")

if trans_to_trans:
    print(f"\n🐛 FOUND {len(trans_to_trans)} TRANSITION-TO-TRANSITION ARCS!")
    for arc_id, src_id, tgt_id, _ in trans_to_trans[:5]:
        print(f"   Arc {arc_id}: {src_id} → {tgt_id}")
else:
    print(f"✅ No transition-to-transition arcs")

# Check 2: Tiny transitions
print(f"\n" + "=" * 80)
print("CHECK 2: TRANSITION SIZES")
print("=" * 80)

tiny_transitions = []
small_transitions = []

for t_id, t_data in transitions.items():
    width = t_data.get('width', 10)
    height = t_data.get('height', 10)
    area = width * height
    
    if area < 50:
        tiny_transitions.append((t_id, width, height))
    elif area < 150:
        small_transitions.append((t_id, width, height))

print(f"\n   Invisible (<50 sq px): {len(tiny_transitions)}")
print(f"   Tiny (50-150 sq px): {len(small_transitions)}")
print(f"   Normal (>150 sq px): {len(transitions) - len(tiny_transitions) - len(small_transitions)}")

if tiny_transitions:
    print(f"\n⚠️  {len(tiny_transitions)} transitions are too small to see!")
    for t_id, w, h in tiny_transitions[:5]:
        t_label = transitions[t_id].get('label', t_id)
        print(f"   {t_id} ({t_label}): {w:.1f} × {h:.1f} = {w*h:.0f} sq px")
    print(f"\n   💡 These create the illusion of place-to-place lines!")

# Check 3: Arc types
print(f"\n" + "=" * 80)
print("CHECK 3: ARC TYPES")
print("=" * 80)

arc_types = {}
for arc in arcs:
    arc_type = arc.get('arc_type', 'normal')
    arc_types.setdefault(arc_type, []).append(arc)

print(f"\n   Arc types found:")
for arc_type, type_arcs in arc_types.items():
    print(f"   - {arc_type}: {len(type_arcs)} arcs")

if 'test' in arc_types:
    print(f"\n⚠️  FOUND TEST ARCS!")
    print(f"   Test arcs might be rendered as non-interactive lines")
    for arc in arc_types['test'][:5]:
        print(f"   {arc['id']}: {arc['source_id']} → {arc['target_id']}")

# Check 4: Check specific compound (user should specify)
print(f"\n" + "=" * 80)
print("CHECK 4: SPECIFIC COMPOUND CONNECTIONS")
print("=" * 80)

# Ask user for compound to check
print(f"\n💡 Enter a compound ID that has spurious lines (e.g., C01451)")
print(f"   Or press Enter to skip this check")
compound_to_check = input("   Compound ID: ").strip()

if compound_to_check:
    # Find place with this label
    matching_places = [p for p in places.values() if compound_to_check in p.get('label', '')]
    
    if matching_places:
        for place in matching_places:
            place_id = place['id']
            print(f"\n🔍 Analyzing {place['label']} ({place_id}):")
            
            # Find all arcs connected to this place
            connected_arcs = [a for a in arcs if a['source_id'] == place_id or a['target_id'] == place_id]
            print(f"   Connected arcs in data: {len(connected_arcs)}")
            
            for arc in connected_arcs:
                if arc['source_id'] == place_id:
                    # Outgoing
                    target_id = arc['target_id']
                    if target_id in places:
                        print(f"   ⚠️  {place_id} → {target_id} (PLACE-TO-PLACE!)")
                    else:
                        target = transitions.get(target_id, {})
                        print(f"   ✅ {place_id} → {target_id} ({target.get('label', 'transition')})")
                else:
                    # Incoming
                    source_id = arc['source_id']
                    if source_id in places:
                        print(f"   ⚠️  {source_id} → {place_id} (PLACE-TO-PLACE!)")
                    else:
                        source = transitions.get(source_id, {})
                        print(f"   ✅ {source_id} ({source.get('label', 'transition')}) → {place_id}")
    else:
        print(f"   ⚠️  No place found with label containing '{compound_to_check}'")

# Final summary
print(f"\n" + "=" * 80)
print("DIAGNOSTIC SUMMARY")
print("=" * 80)

if place_to_place:
    print(f"\n🐛 ROOT CAUSE FOUND: Place-to-place arcs in data model!")
    print(f"   {len(place_to_place)} invalid arcs found")
    print(f"   These arcs should NOT exist in the data")
    print(f"   Likely cause: Bug in KEGG importer creating invalid arcs")
elif tiny_transitions:
    print(f"\n💡 LIKELY CAUSE: Tiny invisible transitions")
    print(f"   {len(tiny_transitions)} transitions < 50 sq px")
    print(f"   Solution: Increase minimum transition size (already fixed)")
    print(f"   Re-import the pathway to apply the fix")
elif 'test' in arc_types:
    print(f"\n💡 POSSIBLE CAUSE: Test arcs being rendered")
    print(f"   {len(arc_types['test'])} test arcs found")
else:
    print(f"\n✅ No obvious data-level issues found")
    print(f"   The spurious lines might be:")
    print(f"   1. Rendering artifacts (code draws extra lines)")
    print(f"   2. KEGG relations visualization (not in data model)")
    print(f"   3. Legacy rendering code still active")

print(f"\n📝 NEXT STEPS:")
if place_to_place:
    print(f"   1. Check KEGG importer code for place-to-place arc creation")
    print(f"   2. Add validation to prevent these arcs")
    print(f"   3. Re-import pathways with fixed code")
elif tiny_transitions:
    print(f"   1. Re-import the pathway (fix already applied)")
    print(f"   2. Verify transitions are now visible")
else:
    print(f"   1. Search for rendering code that draws lines")
    print(f"   2. Check if KEGG relations are being visualized")
    print(f"   3. Look for 'draw_connections' or similar functions")

print("\n" + "=" * 80)
