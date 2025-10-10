#!/usr/bin/env python3
"""
Check if KEGG relations are being rendered as visual lines.
"""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.importer.kegg.kgml_parser import KGMLParser
from shypn.importer.kegg.pathway_converter import convert_pathway
from shypn.importer.kegg.converter_base import ConversionOptions

print("=" * 80)
print("KEGG RELATIONS CHECK")
print("=" * 80)

# Test with a KEGG file
print("\n🔍 Looking for KEGG XML files...")
import os
kegg_files = []
for root, dirs, files in os.walk('data'):
    for file in files:
        if file.endswith('.xml'):
            kegg_files.append(os.path.join(root, file))

if not kegg_files:
    print("⚠️  No KEGG XML files found in data/ directory")
    print("Please download a KEGG pathway XML file and try again")
    sys.exit(0)

# Use first file found
pathway_file = kegg_files[0]
print(f"\n📄 Testing with: {pathway_file}")

# Parse KEGG file
parser = KGMLParser()
pathway = parser.parse_file(pathway_file)

if not pathway:
    print(f"❌ Failed to parse {pathway_file}")
    sys.exit(1)

print(f"\n📊 KEGG Pathway Data:")
print(f"   Name: {pathway.name}")
print(f"   Title: {pathway.title}")
print(f"   Entries: {len(pathway.entries)}")
print(f"   Reactions: {len(pathway.reactions)}")
print(f"   Relations: {len(pathway.relations)}")

if pathway.relations:
    print(f"\n🔗 Relations found ({len(pathway.relations)} total):")
    
    # Group by type
    by_type = {}
    for rel in pathway.relations:
        by_type.setdefault(rel.type, []).append(rel)
    
    for rel_type, rels in by_type.items():
        print(f"\n   {rel_type}: {len(rels)} relations")
        # Show first 3 examples
        for rel in rels[:3]:
            subtypes = ', '.join(st.name for st in rel.subtypes)
            print(f"      {rel.entry1} → {rel.entry2} ({subtypes})")
    
    # Check if these connect compounds
    print(f"\n🧪 Checking if relations connect compounds...")
    compound_entries = {e.id for e in pathway.entries if e.is_compound()}
    
    compound_relations = []
    for rel in pathway.relations:
        if rel.entry1 in compound_entries and rel.entry2 in compound_entries:
            compound_relations.append(rel)
    
    if compound_relations:
        print(f"   ⚠️  {len(compound_relations)} relations connect compounds!")
        print(f"   These could be rendered as spurious lines!")
        for rel in compound_relations[:5]:
            e1 = next(e for e in pathway.entries if e.id == rel.entry1)
            e2 = next(e for e in pathway.entries if e.id == rel.entry2)
            print(f"      {e1.name} → {e2.name}")
    else:
        print(f"   ✅ No relations directly connect compounds")

# Convert to Petri net
print(f"\n⚙️  Converting to Petri net...")
options = ConversionOptions()
document = convert_pathway(pathway, options)

print(f"\n📊 Converted Model:")
print(f"   Places: {len(document.places)}")
print(f"   Transitions: {len(document.transitions)}")
print(f"   Arcs: {len(document.arcs)}")

# Check if relations are stored anywhere in the document
print(f"\n🔍 Checking if relations are stored in converted model...")
has_relations = False
for obj in [*document.places, *document.transitions]:
    if hasattr(obj, 'metadata') and 'relations' in obj.metadata:
        has_relations = True
        print(f"   ⚠️  {obj.id} has relations in metadata: {obj.metadata['relations']}")

if not has_relations:
    print(f"   ✅ Relations not stored in converted model")

print("\n" + "=" * 80)
print("HYPOTHESIS")
print("=" * 80)

if pathway.relations:
    print(f"\n💡 This pathway has {len(pathway.relations)} KEGG relations")
    print(f"   These describe interactions (protein-protein, gene expression, etc.)")
    print(f"\n   Current behavior: Relations are NOT converted to arcs")
    print(f"   Possible issue: Some rendering code might draw them anyway!")
    
    if compound_relations:
        print(f"\n   🎯 {len(compound_relations)} relations connect compounds")
        print(f"      These could appear as 'spurious' place-to-place lines!")
else:
    print(f"\n✅ No relations in this pathway")
    print(f"   Spurious lines must have a different cause")
