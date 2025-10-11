#!/usr/bin/env python3
"""Analyze how compounds appear to be connected visually."""

import sys
sys.path.insert(0, 'src')

from shypn.importer.kegg.api_client import KEGGAPIClient
from shypn.importer.kegg.kgml_parser import KGMLParser

# Fetch pathway
client = KEGGAPIClient()
pathway_id = 'hsa00010'

print(f"Fetching pathway {pathway_id}...")
kgml_data = client.fetch_kgml(pathway_id)
parser = KGMLParser()
pathway = parser.parse(kgml_data)

# Get all compound entries with their positions
compounds = [(entry_id, entry) for entry_id, entry in pathway.entries.items() 
             if entry.type == 'compound']

print(f"\nTotal compounds: {len(compounds)}")

# Find compounds that are visually close (might appear connected)
print(f"\n=== Compounds positioned close together ===")

# Focus on the C06186-C06188 area
target_compounds = {}
for entry_id, entry in compounds:
    if 'C06186' in entry.name or 'C06187' in entry.name or 'C06188' in entry.name:
        target_compounds[entry.name] = entry
        print(f"\n{entry.name}:")
        if entry.graphics:
            print(f"  Position: ({entry.graphics.x}, {entry.graphics.y})")
            print(f"  Label: {entry.graphics.name}")

# Check if any reactions connect to nearby positions
print(f"\n=== Checking reactions near these positions ===")
for reaction in pathway.reactions:
    # Get involved entries
    involved_entries = set()
    for substrate in reaction.substrates:
        involved_entries.add(substrate.name)
    for product in reaction.products:
        involved_entries.add(product.name)
    
    # Check positions
    positions = []
    for entry_id, entry in pathway.entries.items():
        if entry.name in involved_entries and entry.graphics:
            positions.append((entry.graphics.x, entry.graphics.y, entry.name))
    
    # Check if any position is near our target compounds (within 150 pixels)
    for pos in positions:
        x, y, name = pos
        for target_name, target_entry in target_compounds.items():
            if target_entry.graphics:
                tx, ty = target_entry.graphics.x, target_entry.graphics.y
                distance = ((x - tx)**2 + (y - ty)**2)**0.5
                
                if distance < 150:
                    print(f"\nReaction {reaction.name} is near {target_name}:")
                    print(f"  Substrates: {', '.join(s.name for s in reaction.substrates)}")
                    print(f"  Products: {', '.join(p.name for p in reaction.products)}")
                    break

# Check the actual KGML structure for "maplink" or other connections
print(f"\n=== Checking entry details ===")
for target_name, entry in target_compounds.items():
    print(f"\n{target_name}:")
    print(f"  Type: {entry.type}")
    print(f"  Link: {entry.link}")
    if entry.graphics:
        print(f"  Graphics type: {entry.graphics.type}")

