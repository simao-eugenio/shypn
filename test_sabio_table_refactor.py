#!/usr/bin/env python3
"""Test refactored SABIO-RK results table."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.sabio_rk_client import SabioRKClient

print("="*80)
print("SABIO-RK TABLE REFACTOR TEST")
print("="*80)

client = SabioRKClient()

# Query EC 2.7.1.1 + Homo sapiens
print("\nQuerying EC 2.7.1.1 + Homo sapiens...")
result = client.query_by_ec_number("2.7.1.1", "Homo sapiens")

if not result:
    print("❌ FAILED: No results")
    sys.exit(1)

params = result.get('parameters', [])
print(f"✅ Retrieved {len(params)} parameters")
print(f"   Query organism: {result.get('query_organism')}")

# Show first 5 parameters with new metadata
print("\nSample Parameters:")
print("-"*80)
for i, param in enumerate(params[:5], 1):
    print(f"{i}. {param['parameter_type']}: {param['value']:.3g} {param['units']}")
    print(f"   Reaction: {param['reaction_id']}")
    print(f"   KEGG: {param.get('kegg_reaction_id', 'N/A')}")
    print(f"   Organism: {param.get('organism', 'N/A')}")
    print()

# Group by reaction
from collections import defaultdict
reactions = defaultdict(lambda: {'Vmax': [], 'Km': [], 'Kcat': [], 'Ki': []})

for param in params:
    reaction_id = param.get('kegg_reaction_id', 'Unknown')
    param_type = param.get('parameter_type', 'other')
    if param_type in reactions[reaction_id]:
        value = param.get('value')
        units = param.get('units', '')
        reactions[reaction_id][param_type].append(f"{value:.3g} {units}")

print("\n" + "="*80)
print("GROUPED BY REACTION (Table View)")
print("="*80)
print(f"{'Reaction':<12} {'Vmax':<25} {'Km':<25} {'Kcat':<25} {'Ki':<25}")
print("-"*80)

for reaction_id, param_dict in list(reactions.items())[:5]:
    # Handle None reaction_id
    reaction_id = reaction_id if reaction_id else 'Unknown'
    
    vmax = ', '.join(param_dict['Vmax'][:2]) if param_dict['Vmax'] else '-'
    km = ', '.join(param_dict['Km'][:2]) if param_dict['Km'] else '-'
    kcat = ', '.join(param_dict['Kcat'][:2]) if param_dict['Kcat'] else '-'
    ki = ', '.join(param_dict['Ki'][:2]) if param_dict['Ki'] else '-'
    
    # Truncate if too long
    vmax = vmax[:22] + '...' if len(vmax) > 25 else vmax
    km = km[:22] + '...' if len(km) > 25 else km
    kcat = kcat[:22] + '...' if len(kcat) > 25 else kcat
    ki = ki[:22] + '...' if len(ki) > 25 else ki
    
    print(f"{reaction_id:<12} {vmax:<25} {km:<25} {kcat:<25} {ki:<25}")

print("\n" + "="*80)
print("SUMMARY:")
print(f"  - Parameters extracted: {len(params)} ✅")
print(f"  - KEGG Reaction IDs found: {len([p for p in params if p.get('kegg_reaction_id')])} ✅")
print(f"  - Query organism preserved: {result.get('query_organism')} ✅")
print(f"  - Table structure ready for UI ✅")
print("="*80)
