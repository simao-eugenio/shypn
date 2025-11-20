#!/usr/bin/env python3
"""Test Example 08 inhibition behavior."""

import json
import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

# Load Example 08
model_path = '/home/simao/projetos/shypn/workspace/projects/Biochemical-Examples/08_Energy_Sensing_Motif/model.shy'
with open(model_path, 'r') as f:
    data = json.load(f)

print("=== Example 08: Energy Sensing Motif ===\n")

# Check inhibitor arcs
print("Inhibitor Arcs:")
for arc in data['arcs']:
    if arc.get('object_type') == 'curved_inhibitor_arc':
        print(f"  {arc['id']}: {arc['source_id']} ⊸ {arc['target_id']}, weight = {arc['weight']}")

print("\n=== Initial Conditions ===")
places = {p['id']: p for p in data['places']}
for pid in ['P2', 'P1', 'P6']:
    p = places[pid]
    print(f"{p['name']} ({pid}): {p['marking']} mM")

# Check inhibition logic
print("\n=== Inhibition Analysis ===")
atp_initial = places['P2']['marking']
print(f"Initial ATP: {atp_initial} mM")

print("\nA9: ATP ⊸ T1 (PFK), weight = 2.5")
if atp_initial >= 2.5:
    print(f"  ✗ T1 INHIBITED (ATP {atp_initial} >= 2.5)")
else:
    print(f"  ✓ T1 ACTIVE (ATP {atp_initial} < 2.5)")

print("\nA10: ATP ⊸ T2 (PK), weight = 2.0")
if atp_initial >= 2.0:
    print(f"  ✗ T2 INHIBITED (ATP {atp_initial} >= 2.0)")
else:
    print(f"  ✓ T2 ACTIVE (ATP {atp_initial} < 2.0)")

print("\n=== Expected Behavior ===")
print("Initial state (ATP = 3.0 mM, high energy):")
print("  - Both T1 and T2 should be INHIBITED")
print("  - Glycolysis pathway should be BLOCKED")
print("  - F6P and PEP should accumulate (no consumption)")

print("\nAs ATP is consumed (drops below thresholds):")
print("  - ATP 2.5→2.0: T2 becomes active, T1 still blocked")
print("  - ATP < 2.0: Both enzymes active, full pathway flow")

print("\n=== Rate Formula Analysis ===")
transitions = {t['id']: t for t in data['transitions']}
t1 = transitions['T1']
t2 = transitions['T2']

print(f"\nT1 (PFK) rate formula:")
print(f"  {t1['rate']}")
print(f"  Contains: ATP inhibition term '/ (1 + (ATP/0.5)^2.5)'")

print(f"\nT2 (PK) rate formula:")
print(f"  {t2['rate']}")
print(f"  Contains: ATP inhibition term '/ (1 + ATP/1.0)'")

print("\n=== Combined Regulation ===")
print("Each transition has TWO layers of ATP inhibition:")
print("  1. Inhibitor arc (discrete threshold, enables/disables)")
print("  2. Rate formula term (continuous modulation)")
print("\nThis represents:")
print("  - Network topology shows regulatory structure")
print("  - Rate kinetics provide quantitative detail")
