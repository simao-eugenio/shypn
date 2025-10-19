#!/usr/bin/env python3
"""
Compare KEGG Pathway Topology

Compares old vs new KEGG import to identify topology changes.
"""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.canvas.document_model import DocumentModel

print("=" * 80)
print("KEGG Pathway Topology Comparison")
print("=" * 80)

# Load old file (existing)
old_file = "workspace/Test_flow/model/Glycolysis_Gluconeogenesis.shy"
new_file = "workspace/Test_flow/model/Glycolysis_topology_Gluconeogenesis.shy"

print(f"\nOLD: {old_file}")
print(f"NEW: {new_file}")
print("-" * 80)

# Load both files
print("\nLoading files...")
try:
    old_doc = DocumentModel.load_from_file(old_file)
    print(f"✅ Old file loaded: {len(old_doc.places)} places, {len(old_doc.transitions)} transitions")
except Exception as e:
    print(f"✗ Error loading old file: {e}")
    sys.exit(1)

try:
    new_doc = DocumentModel.load_from_file(new_file)
    print(f"✅ New file loaded: {len(new_doc.places)} places, {len(new_doc.transitions)} transitions")
except Exception as e:
    print(f"✗ Error loading new file: {e}")
    sys.exit(1)

# Compare counts
print("\n" + "=" * 80)
print("Element Counts")
print("=" * 80)

print(f"\n{'Element':<20} {'Old':<10} {'New':<10} {'Change':<10}")
print("-" * 50)
print(f"{'Places':<20} {len(old_doc.places):<10} {len(new_doc.places):<10} {len(new_doc.places) - len(old_doc.places):+d}")
print(f"{'Transitions':<20} {len(old_doc.transitions):<10} {len(new_doc.transitions):<10} {len(new_doc.transitions) - len(old_doc.transitions):+d}")
print(f"{'Arcs':<20} {len(old_doc.arcs):<10} {len(new_doc.arcs):<10} {len(new_doc.arcs) - len(old_doc.arcs):+d}")

# Check if topology changed
topology_changed = (
    len(old_doc.places) != len(new_doc.places) or
    len(old_doc.transitions) != len(new_doc.transitions) or
    len(old_doc.arcs) != len(new_doc.arcs)
)

if topology_changed:
    print("\n⚠️  TOPOLOGY HAS CHANGED!")
else:
    print("\n✅ Topology counts match")

# Compare transition types
print("\n" + "=" * 80)
print("Transition Types")
print("=" * 80)

def get_type_counts(transitions):
    counts = {}
    for t in transitions:
        t_type = t.transition_type if hasattr(t, 'transition_type') else 'unknown'
        counts[t_type] = counts.get(t_type, 0) + 1
    return counts

old_types = get_type_counts(old_doc.transitions)
new_types = get_type_counts(new_doc.transitions)

all_types = set(old_types.keys()) | set(new_types.keys())

print(f"\n{'Type':<20} {'Old':<10} {'New':<10} {'Change':<10}")
print("-" * 50)
for t_type in sorted(all_types):
    old_count = old_types.get(t_type, 0)
    new_count = new_types.get(t_type, 0)
    change = new_count - old_count
    change_str = f"{change:+d}" if change != 0 else "="
    print(f"{t_type:<20} {old_count:<10} {new_count:<10} {change_str:<10}")

# Check if all transitions are stochastic in new
if new_types.get('stochastic', 0) == len(new_doc.transitions) and len(new_doc.transitions) > 0:
    print("\n⚠️  WARNING: ALL transitions in new file are STOCHASTIC!")
    print("   This suggests kinetics enhancement may not be working.")

# Compare place labels
print("\n" + "=" * 80)
print("Place Comparison")
print("=" * 80)

old_place_labels = {p.label for p in old_doc.places}
new_place_labels = {p.label for p in new_doc.places}

added_places = new_place_labels - old_place_labels
removed_places = old_place_labels - new_place_labels

if added_places:
    print(f"\nAdded places ({len(added_places)}):")
    for label in sorted(added_places)[:10]:
        print(f"  + {label}")
    if len(added_places) > 10:
        print(f"  ... and {len(added_places) - 10} more")

if removed_places:
    print(f"\nRemoved places ({len(removed_places)}):")
    for label in sorted(removed_places)[:10]:
        print(f"  - {label}")
    if len(removed_places) > 10:
        print(f"  ... and {len(removed_places) - 10} more")

if not added_places and not removed_places:
    print("\n✅ Same places in both files")

# Compare transition labels
print("\n" + "=" * 80)
print("Transition Comparison")
print("=" * 80)

old_trans_labels = {t.label for t in old_doc.transitions}
new_trans_labels = {t.label for t in new_doc.transitions}

added_trans = new_trans_labels - old_trans_labels
removed_trans = old_trans_labels - new_trans_labels

if added_trans:
    print(f"\nAdded transitions ({len(added_trans)}):")
    for label in sorted(added_trans)[:10]:
        print(f"  + {label}")
    if len(added_trans) > 10:
        print(f"  ... and {len(added_trans) - 10} more")

if removed_trans:
    print(f"\nRemoved transitions ({len(removed_trans)}):")
    for label in sorted(removed_trans)[:10]:
        print(f"  - {label}")
    if len(removed_trans) > 10:
        print(f"  ... and {len(removed_trans) - 10} more")

if not added_trans and not removed_trans:
    print("\n✅ Same transitions in both files")

# Sample transition details
print("\n" + "=" * 80)
print("Sample Transitions (First 5 from each)")
print("=" * 80)

print("\nOLD FILE:")
for i, t in enumerate(old_doc.transitions[:5], 1):
    t_type = t.transition_type if hasattr(t, 'transition_type') else 'unknown'
    rate = t.rate_function if hasattr(t, 'rate_function') else 'none'
    print(f"{i}. {t.label}")
    print(f"   Type: {t_type}, Rate: {rate}")

print("\nNEW FILE:")
for i, t in enumerate(new_doc.transitions[:5], 1):
    t_type = t.transition_type if hasattr(t, 'transition_type') else 'unknown'
    rate = t.rate_function if hasattr(t, 'rate_function') else 'none'
    metadata = getattr(t, 'metadata', {})
    
    print(f"{i}. {t.label}")
    print(f"   Type: {t_type}, Rate: {rate}")
    if metadata:
        if 'ec_numbers' in metadata:
            print(f"   EC: {metadata['ec_numbers']}")
        if 'kinetics_confidence' in metadata:
            print(f"   Confidence: {metadata['kinetics_confidence']}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if topology_changed:
    print("\n⚠️  TOPOLOGY CHANGED - Different number of elements")
    print("\nPossible causes:")
    print("  1. Different KEGG source data (pathway updated)")
    print("  2. Different conversion options (filter settings)")
    print("  3. Bug in pathway conversion")
else:
    print("\n✅ Topology preserved - Same number of elements")

if new_types.get('stochastic', 0) == len(new_doc.transitions):
    print("\n⚠️  ALL NEW TRANSITIONS ARE STOCHASTIC")
    print("\nThis is NOT expected! Should have:")
    print("  - Continuous (Michaelis-Menten) for enzymatic reactions")
    print("  - Stochastic for simple reactions")
    print("\nLikely cause: Kinetics enhancement not working correctly")

print("\n" + "=" * 80)
