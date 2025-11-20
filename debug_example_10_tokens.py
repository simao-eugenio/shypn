#!/usr/bin/env python3
"""Debug why tokens aren't moving in Example 10."""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

import json

# Load Example 10
model_path = '/home/simao/projetos/shypn/workspace/projects/Biochemical-Examples/10_Citric_Acid_Cycle/model.shy'
with open(model_path, 'r') as f:
    data = json.load(f)

print("=" * 80)
print("EXAMPLE 10 TOKEN MOVEMENT DEBUG")
print("=" * 80)

# Check each transition
print("\nTRANSITIONS:")
for t_data in data['transitions']:
    print(f"\n{t_data['id']} - {t_data['name']}:")
    print(f"  Type: {t_data.get('transition_type', 'immediate')}")
    rate = t_data.get('rate')
    rate_fwd = t_data.get('rate_forward')
    rate_rev = t_data.get('rate_reverse')
    
    if rate_fwd or rate_rev:
        print(f"  Rate Forward: {rate_fwd}")
        print(f"  Rate Reverse: {rate_rev}")
    elif rate:
        print(f"  Rate: {rate}")
    else:
        print(f"  ⚠️  NO RATE DEFINED!")
    
    # Count input/output arcs
    input_count = sum(1 for a in data['arcs'] if a['target_id'] == t_data['id'])
    output_count = sum(1 for a in data['arcs'] if a['source_id'] == t_data['id'])
    print(f"  Input arcs: {input_count}, Output arcs: {output_count}")

print("\n" + "=" * 80)
print("PLACE CONCENTRATIONS:")
print("=" * 80)
for p_data in data['places']:
    print(f"{p_data['id']} - {p_data['name']}: {p_data['marking']} mM")

print("\n" + "=" * 80)
print("CHECKING FOR ISSUES:")
print("=" * 80)

# Check for transitions with no rate
no_rate = [t for t in data['transitions'] if not t.get('rate') and not t.get('rate_forward') and not t.get('rate_reverse')]
if no_rate:
    print(f"\n⚠️  {len(no_rate)} transitions have NO RATE:")
    for t in no_rate:
        print(f"   - {t['id']} ({t['name']})")

# Check for places with zero tokens
zero_tokens = [p for p in data['places'] if p['marking'] == 0]
if zero_tokens:
    print(f"\n⚠️  {len(zero_tokens)} places have ZERO tokens:")
    for p in zero_tokens:
        print(f"   - {p['id']} ({p['name']})")

# Check for disconnected transitions
for t_data in data['transitions']:
    input_count = sum(1 for a in data['arcs'] if a['target_id'] == t_data['id'])
    output_count = sum(1 for a in data['arcs'] if a['source_id'] == t_data['id'])
    if input_count == 0 or output_count == 0:
        print(f"\n⚠️  {t_data['id']} ({t_data['name']}) is disconnected:")
        print(f"   - Input arcs: {input_count}, Output arcs: {output_count}")

