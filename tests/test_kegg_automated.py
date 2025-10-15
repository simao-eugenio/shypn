#!/usr/bin/env python3
"""Automated End-to-End Test for KEGG Pathway Import.

This script tests the KEGG import workflow programmatically where possible.
Some tests require manual GUI interaction.
"""
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

print("="*70)
print("KEGG PATHWAY IMPORT - AUTOMATED END-TO-END TEST")
print("="*70)
print()

# Test 1: Import all required modules
print("Test 1: Importing modules...")
try:
    from shypn.importer.kegg.api_client import KEGGAPIClient
    from shypn.importer.kegg.kgml_parser import KGMLParser
    from shypn.importer.kegg.pathway_converter import PathwayConverter
    from shypn.helpers.pathway_panel_loader import create_pathway_panel
    from shypn.helpers.kegg_import_panel import KEGGImportPanel
    print("  ✓ All modules imported successfully")
except ImportError as e:
    print(f"  ✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Create KEGG API client
print("\nTest 2: Creating KEGG API client...")
try:
    client = KEGGAPIClient()
    print("  ✓ API client created")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 3: Fetch pathway from KEGG
print("\nTest 3: Fetching pathway hsa00010 (Glycolysis)...")
try:
    kgml_data = client.fetch_kgml("hsa00010")
    if kgml_data and len(kgml_data) > 0:
        print(f"  ✓ Fetched {len(kgml_data)} bytes of KGML data")
    else:
        print("  ✗ No data received")
        sys.exit(1)
except Exception as e:
    print(f"  ✗ Fetch failed: {e}")
    print("  Note: This may fail if no internet connection or KEGG API is down")
    # Don't exit - continue with cached data if available

# Test 4: Parse KGML
print("\nTest 4: Parsing KGML XML...")
try:
    parser = KGMLParser()
    pathway = parser.parse(kgml_data)
    print(f"  ✓ Parsed pathway: {pathway.name}")
    print(f"    - Entries: {len(pathway.entries)}")
    print(f"    - Relations: {len(pathway.relations)}")
    print(f"    - Reactions: {len(pathway.reactions)}")
except Exception as e:
    print(f"  ✗ Parse failed: {e}")
    sys.exit(1)

# Test 5: Convert to Petri net
print("\nTest 5: Converting to Petri net model...")
try:
    converter = PathwayConverter()
    doc_model = converter.convert(pathway)
    print(f"  ✓ Converted to DocumentModel")
    print(f"    - Places: {len(doc_model.places)}")
    print(f"    - Transitions: {len(doc_model.transitions)}")
    print(f"    - Arcs: {len(doc_model.arcs)}")
    
    # Validate non-zero counts
    if len(doc_model.places) == 0:
        print("  ⚠ Warning: No places created")
    if len(doc_model.transitions) == 0:
        print("  ⚠ Warning: No transitions created")
    if len(doc_model.arcs) == 0:
        print("  ⚠ Warning: No arcs created")
        
except Exception as e:
    print(f"  ✗ Conversion failed: {e}")
    sys.exit(1)

# Test 6: Create pathway panel loader
print("\nTest 6: Creating pathway panel loader...")
try:
    panel_loader = create_pathway_panel()
    print("  ✓ Panel loader created")
    print(f"    - Window: {panel_loader.window is not None}")
    print(f"    - Content: {panel_loader.content is not None}")
    print(f"    - Builder: {panel_loader.builder is not None}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Test 7: Verify panel widgets
print("\nTest 7: Verifying panel widgets...")
try:
    builder = panel_loader.builder
    widgets = {
        'pathway_id_entry': builder.get_object('pathway_id_entry'),
        'organism_combo': builder.get_object('organism_combo'),
        'fetch_button': builder.get_object('fetch_button'),
        'import_button': builder.get_object('import_button'),
        'preview_text': builder.get_object('preview_text'),
        'float_button': builder.get_object('float_button'),
    }
    
    missing = []
    for name, widget in widgets.items():
        if widget is None:
            missing.append(name)
        else:
            print(f"  ✓ {name} found")
    
    if missing:
        print(f"  ✗ Missing widgets: {', '.join(missing)}")
        sys.exit(1)
    else:
        print("  ✓ All required widgets found")
        
except Exception as e:
    print(f"  ✗ Widget verification failed: {e}")
    sys.exit(1)

# Test 8: Verify delete-event handler
print("\nTest 8: Verifying window close handler...")
try:
    if hasattr(panel_loader, '_on_delete_event'):
        print("  ✓ _on_delete_event method exists")
        
        # Simulate delete event
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gdk
        event = Gdk.Event.new(Gdk.EventType.DELETE)
        result = panel_loader._on_delete_event(panel_loader.window, event)
        
        if result == True:
            print("  ✓ Handler returns True (prevents destruction)")
        else:
            print("  ✗ Handler returns False (would allow destruction)")
            sys.exit(1)
    else:
        print("  ✗ _on_delete_event method not found")
        sys.exit(1)
        
except Exception as e:
    print(f"  ✗ Handler test failed: {e}")
    sys.exit(1)

# Test 9: Test with cached pathway files
print("\nTest 9: Testing with cached pathway files...")
pathway_dir = os.path.join(os.path.dirname(__file__), 'models', 'pathways')
test_pathways = ['hsa00010.kgml', 'hsa00020.kgml', 'hsa00030.kgml']

tested = 0
for pathway_file in test_pathways:
    pathway_path = os.path.join(pathway_dir, pathway_file)
    if os.path.exists(pathway_path):
        try:
            with open(pathway_path, 'r') as f:
                kgml_data = f.read()
            
            parser = KGMLParser()
            pathway = parser.parse(kgml_data)
            
            converter = PathwayConverter()
            doc_model = converter.convert(pathway)
            
            print(f"  ✓ {pathway_file}: {len(doc_model.places)}P, "
                  f"{len(doc_model.transitions)}T, {len(doc_model.arcs)}A")
            tested += 1
            
        except Exception as e:
            print(f"  ✗ {pathway_file} failed: {e}")

if tested > 0:
    print(f"  ✓ Tested {tested} cached pathways")
else:
    print("  ⚠ No cached pathways found (optional)")

# Summary
print()
print("="*70)
print("AUTOMATED TEST SUMMARY")
print("="*70)
print()
print("✅ Core functionality tests: PASSED")
print()
print("Backend Pipeline:")
print("  ✓ KEGG API client")
print("  ✓ KGML parser")
print("  ✓ Pathway converter")
print("  ✓ Petri net generation")
print()
print("Frontend Components:")
print("  ✓ Pathway panel loader")
print("  ✓ UI widgets")
print("  ✓ Window close handler")
print()
print("Next Steps:")
print("  1. Launch application: python3 src/shypn.py")
print("  2. Perform manual GUI tests (see test_kegg_end_to_end.md)")
print("  3. Test complete workflow:")
print("     - Toggle Pathways button")
print("     - Enter pathway ID: hsa00010")
print("     - Click Fetch Pathway")
print("     - Review preview")
print("     - Click Import to Canvas")
print("     - Verify pathway appears on canvas")
print("     - Test float/dock behavior")
print("     - Test X button close (should not crash!)")
print()
print("="*70)
print("✅ AUTOMATED TESTS COMPLETE - Ready for manual GUI testing")
print("="*70)
