#!/usr/bin/env python3
"""Test document-level persistence (save/load to file)."""

import sys
import os
import tempfile
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.data.canvas.document_model import DocumentModel


def test_document_to_dict():
    """Test serializing document to dictionary."""
    print("\n🔍 Testing Document.to_dict()...")
    
    # Create document with objects
    doc = DocumentModel()
    
    p1 = doc.create_place(100.0, 200.0, label="Input")
    p1.set_tokens(3)
    
    t1 = doc.create_transition(200.0, 200.0, label="Process")
    
    p2 = doc.create_place(300.0, 200.0, label="Output")
    
    a1 = doc.create_arc(p1, t1, weight=2)
    a2 = doc.create_arc(t1, p2, weight=1)
    
    # Serialize
    data = doc.to_dict()
    
    print("✅ Serialized document:")
    print(f"   Version: {data['version']}")
    print(f"   Places: {len(data['places'])}")
    print(f"   Transitions: {len(data['transitions'])}")
    print(f"   Arcs: {len(data['arcs'])}")
    
    # Verify structure
    assert data["version"] == "2.0", "Version should be 2.0"
    assert len(data["places"]) == 2, f"Expected 2 places, got {len(data['places'])}"
    assert len(data["transitions"]) == 1, f"Expected 1 transition, got {len(data['transitions'])}"
    assert len(data["arcs"]) == 2, f"Expected 2 arcs, got {len(data['arcs'])}"
    
    print("✅ Document serialization verified")
    return True


def test_document_from_dict():
    """Test deserializing document from dictionary."""
    print("\n🔍 Testing Document.from_dict()...")
    
    # Create original document
    doc1 = DocumentModel()
    p1 = doc1.create_place(100.0, 200.0, label="Input")
    p1.set_tokens(3)
    t1 = doc1.create_transition(200.0, 200.0, label="Process")
    p2 = doc1.create_place(300.0, 200.0, label="Output")
    a1 = doc1.create_arc(p1, t1, weight=2)
    a2 = doc1.create_arc(t1, p2, weight=1)
    
    # Serialize
    data = doc1.to_dict()
    
    # Deserialize
    doc2 = DocumentModel.from_dict(data)
    
    # Verify counts
    assert len(doc2.places) == 2, f"Expected 2 places, got {len(doc2.places)}"
    assert len(doc2.transitions) == 1, f"Expected 1 transition, got {len(doc2.transitions)}"
    assert len(doc2.arcs) == 2, f"Expected 2 arcs, got {len(doc2.arcs)}"
    
    # Verify place properties
    p1_restored = doc2.places[0]
    assert p1_restored.name == "P1", f"Place name should be P1, got {p1_restored.name}"
    assert p1_restored.label == "Input", f"Place label should be Input, got {p1_restored.label}"
    assert p1_restored.tokens == 3, f"Place should have 3 tokens, got {p1_restored.tokens}"
    assert p1_restored.x == 100.0, f"Place x should be 100.0, got {p1_restored.x}"
    
    # Verify arc connectivity
    a1_restored = doc2.arcs[0]
    assert a1_restored.source.name == "P1", f"Arc source should be P1, got {a1_restored.source.name}"
    assert a1_restored.target.name == "T1", f"Arc target should be T1, got {a1_restored.target.name}"
    assert a1_restored.weight == 2, f"Arc weight should be 2, got {a1_restored.weight}"
    
    print("✅ Document deserialization verified")
    print(f"   Restored: {len(doc2.places)} places, {len(doc2.transitions)} transitions, {len(doc2.arcs)} arcs")
    return True


def test_save_and_load_file():
    """Test saving and loading document to/from file."""
    print("\n🔍 Testing Document.save_to_file() and load_from_file()...")
    
    # Create document
    doc1 = DocumentModel()
    p1 = doc1.create_place(100.0, 200.0, label="Start")
    p1.set_tokens(5)
    t1 = doc1.create_transition(200.0, 200.0, label="Action")
    p2 = doc1.create_place(300.0, 200.0, label="End")
    a1 = doc1.create_arc(p1, t1, weight=3)
    a2 = doc1.create_arc(t1, p2, weight=2)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        # Save
        doc1.save_to_file(temp_path)
        print(f"✅ Saved to {temp_path}")
        
        # Verify file exists and is valid JSON
        assert os.path.exists(temp_path), "File should exist"
        with open(temp_path, 'r') as f:
            data = json.load(f)
            print(f"✅ File is valid JSON: {len(data)} keys")
        
        # Load
        doc2 = DocumentModel.load_from_file(temp_path)
        
        # Verify loaded document matches original
        assert len(doc2.places) == len(doc1.places), "Place count should match"
        assert len(doc2.transitions) == len(doc1.transitions), "Transition count should match"
        assert len(doc2.arcs) == len(doc1.arcs), "Arc count should match"
        
        # Verify specific properties
        p1_loaded = doc2.places[0]
        assert p1_loaded.tokens == 5, f"Tokens should be 5, got {p1_loaded.tokens}"
        assert p1_loaded.label == "Start", f"Label should be Start, got {p1_loaded.label}"
        
        a1_loaded = doc2.arcs[0]
        assert a1_loaded.weight == 3, f"Weight should be 3, got {a1_loaded.weight}"
        
        print("✅ File save/load verified")
        
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
            print(f"✅ Cleaned up temp file")
    
    return True


def test_empty_document():
    """Test serializing and deserializing empty document."""
    print("\n🔍 Testing Empty Document...")
    
    # Create empty document
    doc1 = DocumentModel()
    
    # Serialize
    data = doc1.to_dict()
    
    # Verify empty
    assert len(data["places"]) == 0, "Should have no places"
    assert len(data["transitions"]) == 0, "Should have no transitions"
    assert len(data["arcs"]) == 0, "Should have no arcs"
    
    # Deserialize
    doc2 = DocumentModel.from_dict(data)
    
    # Verify still empty
    assert doc2.is_empty(), "Restored document should be empty"
    
    print("✅ Empty document handled correctly")
    return True


def test_complex_network():
    """Test complex network with multiple connections."""
    print("\n🔍 Testing Complex Network...")
    
    # Create complex network
    doc1 = DocumentModel()
    
    # Create 3 places and 2 transitions
    p1 = doc1.create_place(100.0, 100.0, label="P1")
    p1.set_tokens(2)
    p2 = doc1.create_place(100.0, 200.0, label="P2")
    p2.set_tokens(1)
    p3 = doc1.create_place(300.0, 150.0, label="P3")
    
    t1 = doc1.create_transition(200.0, 100.0, label="T1")
    t2 = doc1.create_transition(200.0, 200.0, label="T2")
    
    # Create arcs (complex connectivity)
    a1 = doc1.create_arc(p1, t1, weight=2)
    a2 = doc1.create_arc(p2, t2, weight=1)
    a3 = doc1.create_arc(t1, p3, weight=1)
    a4 = doc1.create_arc(t2, p3, weight=2)
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        doc1.save_to_file(temp_path)
        doc2 = DocumentModel.load_from_file(temp_path)
        
        # Verify structure
        assert len(doc2.places) == 3, f"Should have 3 places, got {len(doc2.places)}"
        assert len(doc2.transitions) == 2, f"Should have 2 transitions, got {len(doc2.transitions)}"
        assert len(doc2.arcs) == 4, f"Should have 4 arcs, got {len(doc2.arcs)}"
        
        # Verify all objects have unique IDs
        place_ids = [p.id for p in doc2.places]
        transition_ids = [t.id for t in doc2.transitions]
        arc_ids = [a.id for a in doc2.arcs]
        
        assert len(place_ids) == len(set(place_ids)), "Place IDs should be unique"
        assert len(transition_ids) == len(set(transition_ids)), "Transition IDs should be unique"
        assert len(arc_ids) == len(set(arc_ids)), "Arc IDs should be unique"
        
        # Verify connectivity is preserved
        arc_connections = [(a.source.name, a.target.name, a.weight) for a in doc2.arcs]
        expected_connections = [("P1", "T1", 2), ("P2", "T2", 1), ("T1", "P3", 1), ("T2", "P3", 2)]
        
        for expected in expected_connections:
            assert expected in arc_connections, f"Expected connection {expected} not found"
        
        print("✅ Complex network preserved correctly")
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    return True


def main():
    """Run all document persistence tests."""
    print("=" * 60)
    print("🔄 DOCUMENT PERSISTENCE TESTS")
    print("=" * 60)
    
    tests = [
        test_document_to_dict,
        test_document_from_dict,
        test_save_and_load_file,
        test_empty_document,
        test_complex_network
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ TEST FAILED: {test.__name__}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total: {len(tests)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
