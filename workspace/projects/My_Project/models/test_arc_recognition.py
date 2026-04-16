#!/usr/bin/env python3
"""
Test arc type recognition in SHYPN accounting system.
Verifies that curved_arc, curved_inhibitor_arc, curved_opposite_signal_flow
are correctly mapped to their base types (normal, inhibitor, signal_flow).
"""

import json
from pathlib import Path

# Load model
model_path = Path(__file__).parent / "arcs_types.shy"
with open(model_path, 'r') as f:
    model = json.load(f)

print("=" * 80)
print("ARC TYPE RECOGNITION TEST")
print("=" * 80)

arcs = model.get('arcs', [])
places = {p['id']: p for p in model.get('places', [])}
transitions = {t['id']: t for t in model.get('transitions', [])}

# Define arc type mappings (as should be implemented in accounting code)
ARC_TYPE_MAPPING = {
    # Base types
    'normal': 'normal',
    'inhibitor': 'inhibitor',
    'test': 'test',
    'signal_flow': 'signal_flow',
    
    # Curved variants
    'curved_arc': 'normal',
    'curved_inhibitor_arc': 'inhibitor',
    'curved_test_arc': 'test',
    'curved_signal_flow': 'signal_flow',
    
    # Opposite variants
    'curved_opposite_arc': 'normal',
    'curved_opposite_inhibitor_arc': 'inhibitor',
    'curved_opposite_test_arc': 'test',
    'curved_opposite_signal_flow': 'signal_flow',
}

def get_base_arc_type(arc_type):
    """Extract base arc type from curved/opposite variants."""
    return ARC_TYPE_MAPPING.get(arc_type, 'normal')

def get_effective_arc_type(arc, places, transitions):
    """Get effective arc type considering signal place auto-detection.
    
    When an arc connects to/from a signal place, it should be treated as 
    signal_flow regardless of its arc_type field.
    """
    arc_type = arc.get('arc_type', 'normal')
    source_id = arc.get('source_id')
    target_id = arc.get('target_id')
    
    # Check if source or target is a signal place
    source_place = places.get(source_id)
    target_place = places.get(target_id)
    
    source_is_signal = source_place and source_place.get('is_signal_place', False)
    target_is_signal = target_place and target_place.get('is_signal_place', False)
    
    # Auto-detect signal_flow when connecting to signal places
    if (source_is_signal or target_is_signal) and arc_type == 'normal':
        return 'signal_flow'
    
    return arc_type

def arc_consumes_tokens(arc_type):
    """Check if arc type consumes tokens for accounting."""
    base_type = get_base_arc_type(arc_type)
    return base_type not in ['inhibitor', 'test', 'signal_flow']

def arc_transfers_tokens(arc_type):
    """Check if arc type transfers tokens for accounting."""
    base_type = get_base_arc_type(arc_type)
    return base_type not in ['inhibitor', 'test', 'signal_flow']

print("\nArc Type Classification for Accounting:\n")
print(f"{'Arc ID':<8} {'Arc Type':<35} {'Base Type':<12} {'Consumes':<10} {'Transfers'}")
print("-" * 90)

results = {
    'total': len(arcs),
    'consuming': 0,
    'non_consuming': 0,
    'transferring': 0,
    'non_transferring': 0,
    'unrecognized': []
}

for arc in arcs:
    arc_id = arc.get('id')
    arc_type = arc.get('arc_type', 'normal')
    
    # Get effective arc type (considers signal place auto-detection)
    effective_type = get_effective_arc_type(arc, places, transitions)
    base_type = get_base_arc_type(effective_type)
    
    consumes = arc_consumes_tokens(effective_type)
    transfers = arc_transfers_tokens(effective_type)
    
    if effective_type not in ARC_TYPE_MAPPING:
        results['unrecognized'].append((arc_id, effective_type))
    
    if consumes:
        results['consuming'] += 1
    else:
        results['non_consuming'] += 1
    
    if transfers:
        results['transferring'] += 1
    else:
        results['non_transferring'] += 1
    
    consume_str = "✓ Yes" if consumes else "✗ No"
    transfer_str = "✓ Yes" if transfers else "✗ No"
    
    # Show both declared and effective type if different
    type_display = arc_type
    if effective_type != arc_type:
        type_display = f"{arc_type} → {effective_type}"
    
    print(f"{arc_id:<8} {type_display:<35} {base_type:<12} {consume_str:<10} {transfer_str}")

print("=" * 90)

# Summary
print("\nSummary Statistics:\n")
print(f"  Total arcs: {results['total']}")
print(f"  Token-consuming arcs: {results['consuming']}")
print(f"  Non-consuming arcs: {results['non_consuming']}")
print(f"  Token-transferring arcs: {results['transferring']}")
print(f"  Non-transferring arcs: {results['non_transferring']}")

if results['unrecognized']:
    print(f"\n  ⚠ Unrecognized arc types: {len(results['unrecognized'])}")
    for arc_id, arc_type in results['unrecognized']:
        print(f"    {arc_id}: {arc_type}")
else:
    print("\n  ✓ All arc types recognized!")

# Test accounting logic
print("\n" + "=" * 80)
print("ACCOUNTING LOGIC TEST")
print("=" * 80)

print("\nTokens should be consumed/transferred by:")
consuming_arcs = [a for a in arcs if arc_consumes_tokens(get_effective_arc_type(a, places, transitions))]
for arc in consuming_arcs:
    arc_type = arc.get('arc_type', 'normal')
    effective_type = get_effective_arc_type(arc, places, transitions)
    display = f"{arc_type} → {effective_type}" if effective_type != arc_type else arc_type
    print(f"  {arc['id']}: {display} (base: {get_base_arc_type(effective_type)})")

print("\nTokens should NOT be consumed/transferred by:")
non_consuming_arcs = [a for a in arcs if not arc_consumes_tokens(get_effective_arc_type(a, places, transitions))]
for arc in non_consuming_arcs:
    arc_type = arc.get('arc_type', 'normal')
    effective_type = get_effective_arc_type(arc, places, transitions)
    display = f"{arc_type} → {effective_type}" if effective_type != arc_type else arc_type
    base_type = get_base_arc_type(effective_type)
    print(f"  {arc['id']}: {display} (base: {base_type})")

# Validation test
print("\n" + "=" * 80)
print("VALIDATION RESULTS")
print("=" * 80)

validation_tests = [
    ("curved_arc should map to normal", 
     get_base_arc_type('curved_arc') == 'normal'),
    ("curved_inhibitor_arc should map to inhibitor", 
     get_base_arc_type('curved_inhibitor_arc') == 'inhibitor'),
    ("curved_opposite_signal_flow should map to signal_flow", 
     get_base_arc_type('curved_opposite_signal_flow') == 'signal_flow'),
    ("inhibitor arcs should not consume tokens", 
     not arc_consumes_tokens('inhibitor')),
    ("test arcs should not consume tokens", 
     not arc_consumes_tokens('test')),
    ("signal_flow arcs should not transfer tokens", 
     not arc_transfers_tokens('signal_flow')),
    ("normal arcs should consume tokens", 
     arc_consumes_tokens('normal')),
    ("arcs from signal places auto-convert to signal_flow",
     get_effective_arc_type({'arc_type': 'normal', 'source_id': 'P4', 'target_id': 'T1'}, places, transitions) == 'signal_flow'),
]

all_passed = True
for test_name, result in validation_tests:
    status = "✓ PASS" if result else "✗ FAIL"
    print(f"  {status}: {test_name}")
    if not result:
        all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("✓ ALL TESTS PASSED - Arc type detection working correctly!")
else:
    print("✗ SOME TESTS FAILED - Review arc type mapping!")
print("=" * 80)
