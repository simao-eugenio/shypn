#!/usr/bin/env python3
"""Re-import BIOMD0000000068 with fixed source transition rates."""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.pathway.pathway_importer import PathwayImporter
from shypn.data.canvas.document_model import DocumentModel

sbml_path = "/home/simao/projetos/shypn/workspace/projects/My_Project/pathways/BIOMD0000000068.xml"
output_path = "/home/simao/projetos/shypn/workspace/projects/My_Project/models/BIOMD0000000068_FIXED.shy"

print("="*80)
print("RE-IMPORTING BIOMD0000000068 WITH FIXED SOURCE RATES")
print("="*80)

print(f"\nImporting from: {sbml_path}")
importer = PathwayImporter()

try:
    document = importer.import_sbml(sbml_path)
    print(f"✅ Import successful")
    
    # Check source transitions
    source_transitions = [t for t in document.transitions if getattr(t, 'is_source', False)]
    print(f"\nSource transitions created: {len(source_transitions)}")
    for t in source_transitions:
        rate = getattr(t, 'rate', None)
        print(f"  {t.label}: rate={rate}")
    
    # Save
    document.save_to_file(output_path)
    print(f"\n✅ Saved to: {output_path}")
    
    print("\n" + "="*80)
    print("SUCCESS!")
    print("="*80)
    print("Open BIOMD0000000068_FIXED.shy in Shypn to use the corrected model.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
