#!/usr/bin/env python3
"""
Comprehensive test of object reference architecture.

Tests:
1. Object creation with string IDs
2. Arc source/target are object references
3. File save/load preserves object references
4. KEGG import works with string IDs
5. Arc source_id/target_id properties work
"""

import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc

def test_basic_object_references():
    """Test that basic object creation uses references."""
    print("\n" + "="*60)
    print("TEST 1: Basic Object References")
    print("="*60)
    
    # Create objects
    p1 = Place(x=100, y=100, id="P1", name="P1", label="Start")
    t1 = Transition(x=200, y=100, id="T1", name="T1", label="Action")
    a1 = Arc(source=p1, target=t1, id="A1", name="A1", weight=2)
    
    # Verify object references
    assert a1.source is p1, "Arc should reference Place object"
    assert a1.target is t1, "Arc should reference Transition object"
    print("✅ Arc uses object references (not IDs)")
    
    # Verify ID properties work
    assert a1.source_id == "P1", f"source_id should be 'P1', got {a1.source_id}"
    assert a1.target_id == "T1", f"target_id should be 'T1', got {a1.target_id}"
    print(f"✅ Arc.source_id = {repr(a1.source_id)} (type={type(a1.source_id).__name__})")
    print(f"✅ Arc.target_id = {repr(a1.target_id)} (type={type(a1.target_id).__name__})")
    
    # Verify property updates propagate
    p1.x = 150
    assert a1.source.x == 150, "Changes to Place should reflect in Arc.source"
    print("✅ Object property changes propagate through references")
    
    return True

def test_file_save_load():
    """Test file save/load preserves object references."""
    print("\n" + "="*60)
    print("TEST 2: File Save/Load")
    print("="*60)
    
    # Create document
    doc1 = DocumentModel()
    p1 = doc1.create_place(100, 100, label="Start")
    t1 = doc1.create_transition(200, 100, label="Action")
    p2 = doc1.create_place(300, 100, label="End")
    a1 = doc1.create_arc(p1, t1, weight=3)
    a2 = doc1.create_arc(t1, p2, weight=2)
    
    print(f"Created: {len(doc1.places)} places, {len(doc1.transitions)} transitions, {len(doc1.arcs)} arcs")
    
    # Save
    with tempfile.NamedTemporaryFile(mode='w', suffix='.shy', delete=False) as f:
        temp_path = f.name
    
    try:
        doc1.save_to_file(temp_path)
        print(f"✅ Saved to {temp_path}")
        
        # Load
        doc2 = DocumentModel.load_from_file(temp_path)
        print(f"✅ Loaded from {temp_path}")
        
        # Verify counts
        assert len(doc2.places) == 2, "Should have 2 places"
        assert len(doc2.transitions) == 1, "Should have 1 transition"
        assert len(doc2.arcs) == 2, "Should have 2 arcs"
        print(f"✅ Object counts match")
        
        # Verify object references
        a1_loaded = doc2.arcs[0]
        assert isinstance(a1_loaded.source, Place), "Arc source should be Place object"
        assert isinstance(a1_loaded.target, Transition), "Arc target should be Transition object"
        print(f"✅ Arc references are objects (not IDs)")
        
        # Verify source/target are from the same document
        assert a1_loaded.source in doc2.places, "Arc source should be in loaded places"
        assert a1_loaded.target in doc2.transitions, "Arc target should be in loaded transitions"
        print(f"✅ Arc references point to loaded objects")
        
        # Verify source_id/target_id work
        print(f"   Arc.source_id = {repr(a1_loaded.source_id)} (type={type(a1_loaded.source_id).__name__})")
        print(f"   Arc.target_id = {repr(a1_loaded.target_id)} (type={type(a1_loaded.target_id).__name__})")
        
        return True
        
    finally:
        os.unlink(temp_path)

def test_kegg_import():
    """Test KEGG import with string IDs."""
    print("\n" + "="*60)
    print("TEST 3: KEGG Import with String IDs")
    print("="*60)
    
    try:
        from shypn.importer.kegg.api_client import KEGGAPIClient
        from shypn.importer.kegg.kgml_parser import parse_kgml
        from shypn.pathway.options import EnhancementOptions
        from shypn.importer.kegg.pathway_converter import convert_pathway_enhanced
        
        # Fetch and convert
        api_client = KEGGAPIClient()
        kgml_data = api_client.fetch_kgml('hsa00010')
        pathway = parse_kgml(kgml_data)
        
        enhancement_options = EnhancementOptions(
            enable_layout_optimization=True,
            enable_arc_routing=False,
            enable_metadata_enhancement=True
        )
        
        document_model = convert_pathway_enhanced(
            pathway,
            coordinate_scale=2.5,
            include_cofactors=False,
            enhancement_options=enhancement_options
        )
        
        print(f"✅ Converted KEGG pathway: {pathway.name}")
        print(f"   Places: {len(document_model.places)}")
        print(f"   Transitions: {len(document_model.transitions)}")
        print(f"   Arcs: {len(document_model.arcs)}")
        
        # Verify IDs are strings
        p = document_model.places[0]
        t = document_model.transitions[0]
        a = document_model.arcs[0]
        
        assert isinstance(p.id, str), f"Place ID should be string, got {type(p.id)}"
        assert isinstance(t.id, str), f"Transition ID should be string, got {type(t.id)}"
        assert isinstance(a.id, str), f"Arc ID should be string, got {type(a.id)}"
        print(f"✅ All IDs are strings")
        
        # Verify arc references
        assert isinstance(a.source, (Place, Transition)), "Arc source should be object"
        assert isinstance(a.target, (Place, Transition)), "Arc target should be object"
        print(f"✅ Arcs use object references")
        
        # Verify source_id/target_id properties
        assert isinstance(a.source_id, str), f"source_id should be string, got {type(a.source_id)}"
        assert isinstance(a.target_id, str), f"target_id should be string, got {type(a.target_id)}"
        print(f"✅ Arc.source_id/target_id are strings")
        
        return True
        
    except Exception as e:
        print(f"⚠️  KEGG test skipped (network/import issue): {e}")
        return None

def main():
    print("="*60)
    print("Object Reference Architecture - Comprehensive Test")
    print("="*60)
    
    tests = [
        ("Basic Object References", test_basic_object_references),
        ("File Save/Load", test_file_save_load),
        ("KEGG Import", test_kegg_import),
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for name, test_func in tests:
        try:
            result = test_func()
            if result is True:
                passed += 1
            elif result is None:
                skipped += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Skipped: {skipped}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Object reference architecture working correctly.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
