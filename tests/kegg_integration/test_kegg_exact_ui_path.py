#!/usr/bin/env python3
"""
Exact replication of KEGG import UI path to find int() error.

This script replicates exactly what kegg_import_panel.py does
when the user clicks Import.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_kegg_import_full_path():
    """Replicate exact KEGG import path from UI"""
    print("=" * 70)
    print("KEGG Import - Full UI Path Replication")
    print("=" * 70)
    
    try:
        # Step 1: Fetch KGML
        print("\n[1] Fetching KGML from KEGG API...")
        from shypn.importer.kegg.api_client import KEGGAPIClient
        api_client = KEGGAPIClient()
        pathway_id = 'hsa00010'
        kgml_data = api_client.fetch_kgml(pathway_id)
        print(f"    ✓ Fetched {len(kgml_data)} bytes")
        
        # Step 2: Parse KGML
        print("\n[2] Parsing KGML...")
        from shypn.importer.kegg.kgml_parser import parse_kgml
        pathway = parse_kgml(kgml_data)
        print(f"    ✓ Parsed: {pathway.name}")
        print(f"      Entries: {len(pathway.entries)}")
        print(f"      Reactions: {len(pathway.reactions)}")
        print(f"      Relations: {len(pathway.relations)}")
        
        # Step 3: Create enhancement options (UI defaults)
        print("\n[3] Creating enhancement options...")
        from shypn.pathway.options import EnhancementOptions
        enhancement_options = EnhancementOptions(
            enable_layout_optimization=True,
            enable_arc_routing=True,
            enable_metadata_enhancement=True
        )
        print(f"    ✓ Options created")
        
        # Step 4: Convert with enhancements (this is where UI fails)
        print("\n[4] Converting pathway to Petri net with enhancements...")
        from shypn.importer.kegg.pathway_converter import convert_pathway_enhanced
        
        document_model = convert_pathway_enhanced(
            pathway,
            coordinate_scale=2.5,
            include_cofactors=False,  # UI default
            enhancement_options=enhancement_options
        )
        
        print(f"    ✓ Conversion SUCCESS!")
        print(f"      Places: {len(document_model.places)}")
        print(f"      Transitions: {len(document_model.transitions)}")
        print(f"      Arcs: {len(document_model.arcs)}")
        
        # Step 5: Verify object types
        print("\n[5] Verifying object references...")
        
        # DocumentModel stores as lists, not dicts
        if document_model.places:
            p = document_model.places[0]
            print(f"    Place: {p.name}")
            print(f"      - has .id attribute: {hasattr(p, 'id')}")
            print(f"      - has .name attribute: {hasattr(p, 'name')}")
            if hasattr(p, 'id'):
                print(f"      - id type: {type(p.id).__name__}")
                print(f"      - id value: '{p.id}'")
        
        if document_model.transitions:
            t = document_model.transitions[0]
            print(f"    Transition: {t.name}")
            print(f"      - has .id attribute: {hasattr(t, 'id')}")
            print(f"      - has .name attribute: {hasattr(t, 'name')}")
            if hasattr(t, 'id'):
                print(f"      - id type: {type(t.id).__name__}")
                print(f"      - id value: '{t.id}'")
        
        if document_model.arcs:
            a = document_model.arcs[0]
            print(f"    Arc: {a.name}")
            print(f"      - has .id attribute: {hasattr(a, 'id')}")
            print(f"      - has .source attribute: {hasattr(a, 'source')}")
            print(f"      - has .target attribute: {hasattr(a, 'target')}")
            if hasattr(a, 'id'):
                print(f"      - id type: {type(a.id).__name__}")
                print(f"      - id value: '{a.id}'")
            if hasattr(a, 'source'):
                print(f"      - source type: {type(a.source).__name__}")
                print(f"      - source value: {a.source.name if hasattr(a.source, 'name') else a.source}")
            if hasattr(a, 'target'):
                print(f"      - target type: {type(a.target).__name__}")
                print(f"      - target value: {a.target.name if hasattr(a.target, 'name') else a.target}")
        
        print("\n" + "=" * 70)
        print("✅ ALL STEPS PASSED - No int() error found!")
        print("=" * 70)
        return True
        
    except Exception as e:
        import traceback
        print(f"\n{'='*70}")
        print(f"❌ ERROR FOUND!")
        print(f"{'='*70}")
        print(f"\nError: {type(e).__name__}: {e}")
        print(f"\nFull traceback:")
        print(traceback.format_exc())
        print(f"\n{'='*70}")
        return False

if __name__ == '__main__':
    success = test_kegg_import_full_path()
    sys.exit(0 if success else 1)
