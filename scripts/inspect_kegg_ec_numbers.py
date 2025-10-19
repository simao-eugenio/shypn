#!/usr/bin/env python3
"""Inspect KEGG reactions to see if EC numbers are available."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.importer.kegg.api_client import fetch_pathway
from shypn.importer.kegg.kgml_parser import parse_kgml

# Fetch Glycolysis
print("Fetching KEGG Glycolysis pathway...")
kgml = fetch_pathway('hsa00010')
pathway = parse_kgml(kgml)

print(f"\nPathway: {pathway.name}")
print(f"Total reactions: {len(pathway.reactions)}")

# Inspect first few reactions
print("\n" + "="*70)
print("Reaction Details:")
print("="*70)

for i, reaction in enumerate(pathway.reactions[:5], 1):
    print(f"\n{i}. Reaction: {reaction.name}")
    print(f"   Type: {reaction.type}")
    
    # Check for EC numbers
    if hasattr(reaction, 'ec_numbers'):
        if reaction.ec_numbers:
            print(f"   EC numbers: {reaction.ec_numbers}")
        else:
            print(f"   EC numbers: None")
    else:
        print(f"   EC numbers attribute: NOT FOUND")
    
    # Check all attributes
    print(f"   Attributes: {dir(reaction)}")
    
    # Check entries
    if hasattr(reaction, 'entries'):
        print(f"   Entries: {len(reaction.entries)}")
        for entry in reaction.entries[:2]:
            print(f"     - {entry.name}: {entry.type}")
            if hasattr(entry, 'ec_number'):
                print(f"       EC: {entry.ec_number}")

print("\n" + "="*70)
print("Checking entry types...")
print("="*70)

enzyme_entries = [e for e in pathway.entries if e.type == 'enzyme']
print(f"\nEnzyme entries: {len(enzyme_entries)}")

if enzyme_entries:
    print("\nFirst 5 enzyme entries:")
    for e in enzyme_entries[:5]:
        print(f"  - {e.name}: {e.type}")
        if hasattr(e, 'ec_number'):
            print(f"    EC: {e.ec_number}")
        # Check graphics for name
        if hasattr(e, 'graphics') and e.graphics:
            print(f"    Graphics name: {e.graphics[0].name if e.graphics else 'N/A'}")
