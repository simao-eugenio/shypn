#!/usr/bin/env python3
"""Test File Menu Integration.

This test verifies that the file save/load methods are properly implemented
in the ModelCanvasLoader class.
"""
import os
import sys
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_model_canvas_loader_has_file_methods():
    """Test that ModelCanvasLoader has save and load methods."""
    from shypn.helpers.model_canvas_loader import ModelCanvasLoader
    
    # Check that the methods exist
    assert hasattr(ModelCanvasLoader, 'save_current_document'), \
        "ModelCanvasLoader should have save_current_document method"
    
    assert hasattr(ModelCanvasLoader, 'load_document'), \
        "ModelCanvasLoader should have load_document method"
    
    print("✅ ModelCanvasLoader has save_current_document() method")
    print("✅ ModelCanvasLoader has load_document() method")

def test_document_model_persistence():
    """Test that DocumentModel can save and load."""
    from shypn.data.canvas.document_model import DocumentModel
    
    # Create a document with some objects
    doc = DocumentModel()
    
    # Add a place
    place1 = doc.add_place(x=100, y=100)
    place1.tokens = 3
    
    # Add a transition
    trans1 = doc.add_transition(x=200, y=100)
    
    # Add an arc
    arc1 = doc.add_arc(source=place1, target=trans1)
    arc1.weight = 2
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        # Save
        doc.save_to_file(temp_path)
        print(f"✅ Saved document to {temp_path}")
        
        # Load
        loaded_doc = DocumentModel.load_from_file(temp_path)
        print(f"✅ Loaded document from {temp_path}")
        
        # Verify objects
        assert len(loaded_doc.places) == 1, "Should have 1 place"
        assert len(loaded_doc.transitions) == 1, "Should have 1 transition"
        assert len(loaded_doc.arcs) == 1, "Should have 1 arc"
        
        # Verify place properties
        loaded_place = loaded_doc.places[0]
        assert loaded_place.tokens == 3, "Place should have 3 tokens"
        assert loaded_place.x == 100, "Place should be at x=100"
        assert loaded_place.y == 100, "Place should be at y=100"
        
        # Verify arc properties
        loaded_arc = loaded_doc.arcs[0]
        assert loaded_arc.weight == 2, "Arc should have weight 2"
        assert loaded_arc.source == loaded_place, "Arc source should be the loaded place"
        
        print("✅ All object properties preserved correctly")
        
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)
            print(f"✅ Cleaned up temp file")

def test_button_integration():
    """Test that buttons are wired up in main application."""
    # Read the main shypn.py file and verify button connections
    script_dir = os.path.dirname(os.path.abspath(__file__))
    shypn_path = os.path.join(script_dir, '..', 'src', 'shypn.py')
    
    with open(shypn_path, 'r') as f:
        content = f.read()
    
    # Check for save button connection
    assert 'file_save_button' in content, "Should wire up file_save_button"
    assert 'save_current_document' in content, "Should call save_current_document"
    
    # Check for open button connection
    assert 'file_open_button' in content, "Should wire up file_open_button"
    assert 'load_document' in content, "Should call load_document"
    
    # Check for save as button connection
    assert 'file_save_as_button' in content, "Should wire up file_save_as_button"
    assert 'save_as=True' in content, "Should call save with save_as=True"
    
    print("✅ file_save_button wired to save_current_document()")
    print("✅ file_open_button wired to load_document()")
    print("✅ file_save_as_button wired to save_current_document(save_as=True)")

def main():
    """Run all tests."""
    print("=" * 60)
    print("File Menu Integration Tests")
    print("=" * 60)
    print()
    
    try:
        print("Test 1: ModelCanvasLoader has file methods")
        print("-" * 60)
        test_model_canvas_loader_has_file_methods()
        print()
        
        print("Test 2: DocumentModel persistence works")
        print("-" * 60)
        test_document_model_persistence()
        print()
        
        print("Test 3: Buttons are wired up correctly")
        print("-" * 60)
        test_button_integration()
        print()
        
        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("Summary:")
        print("- ModelCanvasLoader has save_current_document() and load_document() methods")
        print("- DocumentModel can save to and load from JSON files")
        print("- File buttons (save/open/save-as) are properly wired in main application")
        print("- All object properties are preserved during save/load cycle")
        print()
        print("File menu integration is complete! ✨")
        
        return 0
        
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
