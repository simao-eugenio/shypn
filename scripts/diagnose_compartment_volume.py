#!/usr/bin/env python3
"""
Diagnose compartment_volume issue for adaptive transitions.
Analyzes which places are connected to T5/T6 and their compartment_volume values.
"""

import json

model_path = "workspace/projects/My_Project/drug_discovery/models/normal/macrocycle_transport_normal_nme_0_thermo.shy"

with open(model_path, 'r') as f:
    model =json.load(f)

print("=== COMPARTMENT_VOLUME DIAGNOSIS ===\n")

# Find T5 and T6
transitions = {t['id']: t for t in model['transitions']}
places = {p['id']: p for p in model['places']}
arcs = model['arcs']

print("=== ADAPTIVE TRANSITIONS ===")
for tid in ['T5', 'T6']:
    t = transitions[tid]
    print(f"\n{tid}: {t['name']}")
    print(f"  transition_type (root): {t.get('transition_type', 'NOT_SET')}")
    print(f"  transition_type (attrs): {t.get('attrs', {}).get('transition_type', 'NOT_SET')}")
    print(f"  is_adaptive (root): {t.get('is_adaptive', 'NOT_SET')}")
    print(f"  is_adaptive (attrs): {t.get('attrs', {}).get('is_adaptive', 'NOT_SET')}")

print("\n\n=== ARCS CONNECTED TO T5 ===")
t5_input_places = set()
t5_test_places = set()
for arc in arcs:
    if arc['attrs']['target_id'] == 'T5':
        source_id = arc['attrs']['source_id']
        arc_type = arc['attrs']['arc_type']
        if arc_type == 'test':
            t5_test_places.add(source_id)
        elif arc_type in ('normal', 'inhibitor'):
            t5_input_places.add(source_id)
        print(f"  {arc['id']}: {source_id} --{arc_type}--> T5 (weight={arc['attrs']['weight']})")

print("\n\n=== ARCS CONNECTED TO T6 ===")
t6_input_places = set()
t6_test_places = set()
for arc in arcs:
    if arc['attrs']['target_id'] == 'T6':
        source_id = arc['attrs']['source_id']
        arc_type = arc['attrs']['arc_type']
        if arc_type == 'test':
            t6_test_places.add(source_id)
        elif arc_type in ('normal', 'inhibitor'):
            t6_input_places.add(source_id)
        print(f"  {arc['id']}: {source_id} --{arc_type}--> T6 (weight={arc['attrs']['weight']})")

print("\n\n=== T5 INPUT PLACES (consuming arcs) ===")
if not t5_input_places:
    print("  NO INPUT PLACES - T5 will check test/signal arcs for compartment_volume")
for pid in t5_input_places:
    p = places[pid]
    cv_root = p.get('compartment_volume', 'NOT_AT_ROOT')
    cv_attrs = p.get('attrs', {}).get('compartment_volume', 'NOT_IN_ATTRS')
    print(f"  {pid} ({p['name']}): compartment_volume(root)={cv_root}, compartment_volume(attrs)={cv_attrs}")

print("\n\n=== T5 TEST/SIGNAL PLACES ===")
for pid in t5_test_places:
    p = places[pid]
    cv_root = p.get('compartment_volume', 'NOT_AT_ROOT')
    cv_attrs = p.get('attrs', {}).get('compartment_volume', 'NOT_IN_ATTRS')
    is_signal = p.get('is_signal_place', False)
    signal_type = p.get('signal_type', None)
    print(f"  {pid} ({p['name']}): compartment_volume(root)={cv_root}, compartment_volume(attrs)={cv_attrs}")
    print(f"    is_signal_place={is_signal}, signal_type={signal_type}")

print("\n\n=== T6 INPUT PLACES (consuming arcs) ===")
if not t6_input_places:
    print("  NO INPUT PLACES - T6 will check test/signal arcs for compartment_volume")
for pid in t6_input_places:
    p = places[pid]
    cv_root = p.get('compartment_volume', 'NOT_AT_ROOT')
    cv_attrs = p.get('attrs', {}).get('compartment_volume', 'NOT_IN_ATTRS')
    print(f"  {pid} ({p['name']}): compartment_volume(root)={cv_root}, compartment_volume(attrs)={cv_attrs}")

print("\n\n=== T6 TEST/SIGNAL PLACES ===")
for pid in t6_test_places:
    p = places[pid]
    cv_root = p.get('compartment_volume', 'NOT_AT_ROOT')
    cv_attrs = p.get('attrs', {}).get('compartment_volume', 'NOT_IN_ATTRS')
    is_signal = p.get('is_signal_place', False)
    signal_type = p.get('signal_type', None)
    print(f"  {pid} ({p['name']}): compartment_volume(root)={cv_root}, compartment_volume(attrs)={cv_attrs}")
    print(f"    is_signal_place={is_signal}, signal_type={signal_type}")

print("\n\n=== ALL PLACES WITH COMPARTMENT_VOLUME ===")
for pid, p in places.items():
    cv_root = p.get('compartment_volume', None)
    cv_attrs = p.get('attrs', {}).get('compartment_volume', None)
    if cv_root is not None or cv_attrs is not None:
        print(f"  {pid} ({p['name']}): compartment_volume(root)={cv_root}, compartment_volume(attrs)={cv_attrs}")

print("\n\n=== SOLUTION ===")
print("The issue: compartment_volume is in 'attrs' but NOT at root level for places.")
print("The from_dict() method DOES merge attrs into root during deserialization.")
print("However, if a place has compartment_volume=null in attrs, it's still null after loading.")
print("\nFor adaptive transitions to work, connected places need NON-NULL compartment_volume.")
print("Check which places are connected to T5/T6 and ensure they have valid compartment_volume values.")
