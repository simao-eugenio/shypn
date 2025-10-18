#!/usr/bin/env python3
"""
Test script for Phase 5 side effect fixes.

Tests all four issues reported:
1. ✅ SBML import - Working
2. ❌ KEGG import - "invalid literal for int()" error
3. ❌ File open - Loads but doesn't render
4. ❌ Double-click file - Same as #3

This script tests #1 and #2 programmatically.
#3 and #4 require manual GUI testing.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_kegg_parser():
    """Test KEGG KGML parser directly"""
    print("=" * 60)
    print("TEST 1: KEGG KGML Parser")
    print("=" * 60)
    
    try:
        from shypn.importer.kegg.kgml_parser import parse_kgml
        import urllib.request
        
        pathway_id = 'hsa00010'
        url = f'http://rest.kegg.jp/get/{pathway_id}/kgml'
        
        print(f"Fetching {pathway_id}...")
        with urllib.request.urlopen(url, timeout=10) as response:
            xml_data = response.read().decode('utf-8')
        
        print("Parsing KGML...")
        document = parse_kgml(xml_data)
        
        print(f"✅ Parser SUCCESS")
        print(f"   Name: {document.name}")
        print(f"   Entries: {len(document.entries)}")
        print(f"   Relations: {len(document.relations)}")
        print(f"   Reactions: {len(document.reactions)}")
        
        # Check entry IDs
        print(f"\n   Sample entry IDs (first 5):")
        for i, entry in enumerate(list(document.entries.values())[:5]):
            print(f"     {i+1}. ID='{entry.id}' (type={type(entry.id).__name__})")
        
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ Parser FAILED")
        print(f"\nFull traceback:")
        print(traceback.format_exc())
        return False

def test_kegg_converter():
    """Test KEGG to Petri net conversion"""
    print("\n" + "=" * 60)
    print("TEST 2: KEGG to Petri Net Conversion")
    print("=" * 60)
    
    try:
        from shypn.importer.kegg.kgml_parser import parse_kgml
        from shypn.importer.kegg.pathway_converter import PathwayConverter
        import urllib.request
        
        pathway_id = 'hsa00010'
        url = f'http://rest.kegg.jp/get/{pathway_id}/kgml'
        
        print(f"Fetching {pathway_id}...")
        with urllib.request.urlopen(url, timeout=10) as response:
            xml_data = response.read().decode('utf-8')
        
        print("Parsing KGML...")
        document = parse_kgml(xml_data)
        
        print("Converting to Petri net...")
        converter = PathwayConverter(document)
        pn_document = converter.convert()
        
        print(f"✅ Conversion SUCCESS")
        print(f"   Places: {len(pn_document.places)}")
        print(f"   Transitions: {len(pn_document.transitions)}")
        print(f"   Arcs: {len(pn_document.arcs)}")
        
        # Check object IDs
        if pn_document.places:
            p = list(pn_document.places.values())[0]
            print(f"\n   Sample Place:")
            print(f"     ID: '{p.id}' (type={type(p.id).__name__})")
            print(f"     Name: '{p.name}'")
        
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ Conversion FAILED")
        print(f"\nFull traceback:")
        print(traceback.format_exc())
        return False

def test_sbml_import():
    """Test SBML import (should work)"""
    print("\n" + "=" * 60)
    print("TEST 3: SBML Import (Sanity Check)")
    print("=" * 60)
    
    try:
        # Find an SBML test file
        test_files = [
            'data/biomodels_test/BIOMD0000000001.xml',
            'examples/simple_sbml.xml',
        ]
        
        sbml_file = None
        for f in test_files:
            full_path = os.path.join(os.path.dirname(__file__), '..', f)
            if os.path.exists(full_path):
                sbml_file = full_path
                break
        
        if not sbml_file:
            print("⚠️  No SBML test file found - skipping")
            return None
        
        print(f"Testing with: {os.path.basename(sbml_file)}")
        
        from shypn.importer.sbml.sbml_importer import SBMLImporter
        
        importer = SBMLImporter(sbml_file)
        document = importer.import_model()
        
        print(f"✅ SBML Import SUCCESS")
        print(f"   Places: {len(document.places)}")
        print(f"   Transitions: {len(document.transitions)}")
        print(f"   Arcs: {len(document.arcs)}")
        
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ SBML Import FAILED")
        print(f"\nFull traceback:")
        print(traceback.format_exc())
        return False

def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║         Phase 5 Side Effects - Automated Tests           ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    results = {}
    
    # Test KEGG parser
    results['kegg_parser'] = test_kegg_parser()
    
    # Test KEGG converter
    results['kegg_converter'] = test_kegg_converter()
    
    # Test SBML (sanity check)
    results['sbml_import'] = test_sbml_import()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️  SKIP"
        print(f"{status}  {test_name}")
    
    print("\n" + "=" * 60)
    print("MANUAL TESTS REQUIRED")
    print("=" * 60)
    print("""
Test #3: File Open
  1. Start app: python3 src/shypn.py
  2. File → Open → Select any .shy file
  3. Verify: Objects visible and centered with padding
  
Test #4: Double-Click File
  1. In file explorer panel, double-click a .shy file
  2. Verify: Same as Test #3
  
Expected: Both should show objects centered with ~15% padding
Fix Status: ✅ Implemented (commit 66724c4)
""")
    
    # Exit code
    failed = [k for k, v in results.items() if v is False]
    if failed:
        print(f"\n⚠️  {len(failed)} test(s) failed")
        return 1
    else:
        print(f"\n✅ All automated tests passed")
        return 0

if __name__ == '__main__':
    sys.exit(main())
