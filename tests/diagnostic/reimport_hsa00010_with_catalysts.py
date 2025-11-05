#!/usr/bin/env python3
"""
Re-import hsa00010 with catalysts using the fixed code.

This will create a new model with:
- Sequential IDs (P1, P2, T1, T2, etc.)
- Catalyst places with tokens=1 and initial_marking=1
- Test arcs from catalysts to transitions
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.importer.kegg import fetch_pathway, parse_kgml, convert_pathway_enhanced
from shypn.data.canvas.document_model import DocumentModel
from shypn.data.canvas.id_manager import IDManager
from shypn.file.netobj_persistency import NetObjPersistency

print("=" * 80)
print("RE-IMPORTING hsa00010 WITH CATALYSTS")
print("=" * 80)

# Fetch and parse pathway
print("\nFetching hsa00010 from KEGG...")
kgml_xml = fetch_pathway("hsa00010")

print("Parsing KGML...")
pathway = parse_kgml(kgml_xml)

# Convert with catalysts enabled
print("\nConverting to Petri net with catalysts...")

print("\nOptions:")
print(f"  create_enzyme_places: True")
print(f"  enhance_kinetics: False")

document = convert_pathway_enhanced(
    pathway,
    create_enzyme_places=True,  # Enable catalysts
    estimate_kinetics=False,     # Disable for faster import
    include_cofactors=False     # Only main compounds
)

print(f"\n✓ Import complete!")
print(f"  Places: {len(document.places)}")
print(f"  Transitions: {len(document.transitions)}")
print(f"  Arcs: {len(document.arcs)}")

# Count catalysts
catalysts = [p for p in document.places if getattr(p, 'is_catalyst', False)]
print(f"  Catalysts: {len(catalysts)}")

# Count test arcs
test_arcs = [a for a in document.arcs if a.arc_type == 'test']
print(f"  Test arcs: {len(test_arcs)}")

# Check catalyst tokens
catalyst_tokens = {}
for cat in catalysts:
    tokens = cat.tokens
    initial = cat.initial_marking
    key = (tokens, initial)
    catalyst_tokens[key] = catalyst_tokens.get(key, 0) + 1

print("\nCatalyst Token Distribution:")
for (tokens, initial), count in sorted(catalyst_tokens.items()):
    print(f"  tokens={tokens}, initial_marking={initial}: {count} catalysts")

# Save to both locations
output_paths = [
    Path('/home/simao/projetos/shypn/workspace/projects/models/hsa00010_FIXED.shy'),
    Path('/home/simao/projetos/shypn/workspace/projects/Interactive/models/hsa00010_catalysts.shy')
]

for output_path in output_paths:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Use DocumentModel's save method
    document.save_to_file(str(output_path))
    
    print(f"\n✓ Saved to: {output_path}")

print("\n" + "=" * 80)
print("SUCCESS!")
print("=" * 80)
print("\nNext steps:")
print("1. Load hsa00010_FIXED.shy in the application")
print("2. Try to fire transitions")
print("3. Verify that catalysts don't block simulation")
print("=" * 80)
