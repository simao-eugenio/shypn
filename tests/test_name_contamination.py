#!/usr/bin/env python3
"""Test if SBML names are contaminated with KEGG codes."""

from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter
from shypn.data.canvas.document_model import DocumentModel

# Parse SBML
parser = SBMLParser()
pathway = parser.parse_file('examples/biomodels/BIOMD0000000061.xml')

print("=== ORIGINAL SBML SPECIES (first 5) ===")
for i, sp in enumerate(pathway.species[:5]):
    kegg = sp.kegg_id if hasattr(sp, 'kegg_id') and sp.kegg_id else 'None'
    chebi = sp.chebi_id if hasattr(sp, 'chebi_id') and sp.chebi_id else 'None'
    print(f"{i+1}. ID='{sp.id:10s}' Name='{sp.name:30s}' kegg_id={kegg:10s} chebi_id={chebi}")

# Post-process
postprocessor = PathwayPostProcessor()
processed_pathway = postprocessor.process(pathway)

# Convert to Petri net
document = DocumentModel()
converter = PathwayConverter(processed_pathway, document)
converter.convert()

print("\n=== AFTER CONVERSION (first 5 places) ===")
for i, place in enumerate(list(document.places)[:5]):
    label = place.label if hasattr(place, 'label') else 'None'
    print(f"{i+1}. Place ID={place.id:3d} name='{place.name:15s}' label='{label}'")

# Check if any place has KEGG-like names
print("\n=== CHECKING FOR KEGG CONTAMINATION ===")
import re
kegg_pattern = re.compile(r'^C\d{5}$')
contaminated = []
for place in document.places:
    if kegg_pattern.match(place.name):
        contaminated.append((place.name, place.label))

if contaminated:
    print(f"❌ FOUND {len(contaminated)} places with KEGG compound codes as names:")
    for name, label in contaminated[:5]:
        print(f"   {name} (label: {label})")
else:
    print("✓ No KEGG contamination found - all place names are original SBML IDs")
