#!/usr/bin/env python3
"""Inspect KEGG reaction data to see EC numbers."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.importer.kegg.api_client import fetch_pathway
from shypn.importer.kegg.kgml_parser import parse_kgml

# Fetch Glycolysis
print("Fetching Glycolysis pathway...")
kgml = fetch_pathway('hsa00010')
pathway = parse_kgml(kgml)

print(f"\nPathway: {pathway.name}")
print(f"Reactions: {len(pathway.reactions)}\n")

# Inspect first 10 reactions
print("Sample reactions (first 10):")
print("=" * 80)

for i, reaction in enumerate(pathway.reactions[:10], 1):
    print(f"\n{i}. Reaction: {reaction.name} (ID: {reaction.id})")
    print(f"   Type: {reaction.type}")
    
    # Check all attributes
    attrs = dir(reaction)
    ec_related = [attr for attr in attrs if 'ec' in attr.lower() or 'enzyme' in attr.lower()]
    
    if ec_related:
        print(f"   EC-related attributes: {ec_related}")
        for attr in ec_related:
            val = getattr(reaction, attr, None)
            if val:
                print(f"     {attr}: {val}")
    
    print(f"   Substrates: {len(reaction.substrates)}")
    for sub in reaction.substrates:
        print(f"     - {sub.id} ({sub.name}) x{sub.stoichiometry}")
    
    print(f"   Products: {len(reaction.products)}")
    for prod in reaction.products:
        print(f"     - {prod.id} ({prod.name}) x{prod.stoichiometry}")
    
    # Check if reversible
    if hasattr(reaction, 'reversible'):
        print(f"   Reversible: {reaction.reversible}")
    if hasattr(reaction, 'is_reversible') and callable(reaction.is_reversible):
        print(f"   Is reversible: {reaction.is_reversible()}")
    
    # Show all attributes for first reaction
    if i == 1:
        print(f"\n   All attributes:")
        for attr in sorted([a for a in dir(reaction) if not a.startswith('_')]):
            try:
                val = getattr(reaction, attr)
                if not callable(val):
                    print(f"     {attr}: {val}")
            except:
                pass

print("\n" + "=" * 80)
