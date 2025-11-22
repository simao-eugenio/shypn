#!/usr/bin/env python3
"""
Test the heuristic uniformity issue with a real KEGG pathway import.
"""

import sys
sys.path.insert(0, 'src')

from shypn.importer.kegg import fetch_pathway, parse_kgml, convert_pathway_enhanced
import tempfile
import os


def test_heuristic_with_kegg_pathway():
    """Import a KEGG pathway and diagnose heuristic uniformity."""
    
    print("=" * 80)
    print("TESTING HEURISTIC WITH REAL KEGG PATHWAY")
    print("=" * 80)
    print()
    
    # Import hsa00010 (glycolysis)
    print("Step 1: Importing KEGG pathway hsa00010 (glycolysis)...")
    
    kgml_xml = fetch_pathway('hsa00010')
    
    if not kgml_xml:
        print("ERROR: Failed to fetch KEGG pathway")
        return
    
    # Parse KGML
    pathway = parse_kgml(kgml_xml)
    
    # Convert to document
    document = convert_pathway_enhanced(pathway)
    
    print(f"✓ Imported pathway")
    print(f"  Places: {len(document.places)}")
    print(f"  Transitions: {len(document.transitions)}")
    print()
    
    # Now run the diagnosis
    print("Step 2: Running heuristic diagnosis...")
    print()
    
    import importlib.util
    spec = importlib.util.spec_from_file_location("diagnose", "dev/diagnose_heuristic_uniformity.py")
    diagnose_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(diagnose_module)
    diagnose_module.diagnose_pathway(document)


if __name__ == '__main__':
    test_heuristic_with_kegg_pathway()
