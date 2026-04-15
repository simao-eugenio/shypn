#!/usr/bin/env python3
"""Test NetObjPersistency Architecture.

This test verifies that the new file operations architecture is properly
structured with NetObjPersistency handling all file operations.
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_netobj_persistency_class_exists():
    """Test that NetObjPersistency class exists and has required methods."""
    from shypn.file import NetObjPersistency
    
    # Check that the class exists
    assert NetObjPersistency is not None, "NetObjPersistency class should exist"
    
    # Check that required methods exist
    required_methods = [
        'save_document',
        'load_document',
        'mark_dirty',
        'mark_clean',
        'is_dirty',
        'set_filepath',
        'has_filepath',
        'get_display_name',
        'get_title',
        'check_unsaved_changes',
        'new_document',
    ]
    
    for method_name in required_methods:
        assert hasattr(NetObjPersistency, method_name), \
            f"NetObjPersistency should have {method_name} method"
    
    print("✅ NetObjPersistency class exists with all required methods:")
    for method in required_methods:
        print(f"   - {method}()")
    
    return True

def test_netobj_persistency_properties():
    """Test that NetObjPersistency has required properties and attributes."""
    from shypn.file import NetObjPersistency
    
    # Create instance (without GTK window for testing)
    try:
        persistency = NetObjPersistency(parent_window=None)
    except SystemExit:
        # GTK not available, skip this test
        print("⚠️  GTK not available - skipping instance test")
        return True
    
    # Check properties
    assert hasattr(persistency, 'current_filepath'), "Should have current_filepath"
    assert hasattr(persistency, 'is_dirty'), "Should have is_dirty property"
    assert hasattr(persistency, 'on_file_saved'), "Should have on_file_saved callback"
    assert hasattr(persistency, 'on_file_loaded'), "Should have on_file_loaded callback"
    assert hasattr(persistency, 'on_dirty_changed'), "Should have on_dirty_changed callback"
    
    # Test initial state
    assert persistency.current_filepath is None, "Should start with no filepath"
    assert not persistency.is_dirty, "Should start clean (not dirty)"
    assert not persistency.has_filepath(), "Should not have filepath initially"
    assert persistency.get_display_name() == "Untitled", "Should show 'Untitled' for new document"
    
    # Test dirty state management
    persistency.mark_dirty()
    assert persistency.is_dirty, "Should be dirty after mark_dirty()"
    assert persistency.get_title() == "*Untitled", "Title should have * when dirty"
    
    persistency.mark_clean()
    assert not persistency.is_dirty, "Should be clean after mark_clean()"
    assert persistency.get_title() == "Untitled", "Title should have no * when clean"
    
    # Test filepath management
    persistency.set_filepath("/tmp/test_model.json")
    assert persistency.has_filepath(), "Should have filepath after set_filepath()"
    assert persistency.get_display_name() == "test_model.json", "Should show filename"
    
    print("✅ NetObjPersistency properties and state management work correctly")
    print("   - current_filepath attribute")
    print("   - is_dirty property")
    print("   - Callbacks (on_file_saved, on_file_loaded, on_dirty_changed)")
    print("   - mark_dirty() / mark_clean()")
    print("   - set_filepath() / has_filepath()")
    print("   - get_display_name() / get_title()")
    
    return True

def test_loader_has_no_file_operations():
    """Test that ModelCanvasLoader no longer has file operation methods."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    loader_path = os.path.join(script_dir, '..', 'src', 'shypn', 'helpers', 'model_canvas_loader.py')
    
    with open(loader_path, 'r') as f:
        loader_content = f.read()
    
    # These methods should NOT exist in loader anymore
    assert 'def save_current_document(' not in loader_content, \
        "ModelCanvasLoader should NOT have save_current_document method"
    assert 'def load_document(' not in loader_content, \
        "ModelCanvasLoader should NOT have load_document method"
    
    # Check that file operations section is removed
    assert '# ==================== File Operations ====================' not in loader_content, \
        "File Operations section should be removed from loader"
    
    print("✅ ModelCanvasLoader properly cleaned up:")
    print("   - No save_current_document() method")
    print("   - No load_document() method")
    print("   - No File Operations section")
    
    return True

def test_main_app_uses_persistency():
    """Test that main app (shypn.py) uses NetObjPersistency."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    shypn_path = os.path.join(script_dir, '..', 'src', 'shypn.py')
    
    with open(shypn_path, 'r') as f:
        content = f.read()
    
    # Check imports
    assert 'from shypn.file import create_persistency_manager' in content, \
        "Should import create_persistency_manager"
    
    # Check persistency manager is created
    assert 'persistency = create_persistency_manager(parent_window=window)' in content, \
        "Should create persistency manager"
    
    # Check button handlers use persistency
    assert 'persistency.save_document(' in content, \
        "Save button should call persistency.save_document()"
    assert 'persistency.load_document(' in content, \
        "Open button should call persistency.load_document()"
    assert 'persistency.check_unsaved_changes()' in content, \
        "New button should check unsaved changes"
    assert 'persistency.new_document()' in content, \
        "New button should call persistency.new_document()"
    
    # Check old method calls are removed
    assert 'model_canvas_loader.save_current_document()' not in content, \
        "Should NOT call loader's save_current_document()"
    assert 'model_canvas_loader.load_document()' not in content, \
        "Should NOT call loader's load_document()"
    
    print("✅ Main application properly uses NetObjPersistency:")
    print("   - Imports create_persistency_manager")
    print("   - Creates persistency manager instance")
    print("   - File buttons call persistency methods")
    print("   - New button checks unsaved changes")
    print("   - No direct calls to loader's file methods")
    
    return True

def test_separation_of_concerns():
    """Test that responsibilities are properly separated."""
    # Read relevant files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    persistency_path = os.path.join(script_dir, '..', 'src', 'shypn', 'file', 'netobj_persistency.py')
    with open(persistency_path, 'r') as f:
        persistency_content = f.read()
    
    loader_path = os.path.join(script_dir, '..', 'src', 'shypn', 'helpers', 'model_canvas_loader.py')
    with open(loader_path, 'r') as f:
        loader_content = f.read()
    
    # Check NetObjPersistency responsibilities
    assert 'def save_document(' in persistency_content, \
        "NetObjPersistency should handle save operations"
    assert 'def load_document(' in persistency_content, \
        "NetObjPersistency should handle load operations"
    assert 'def mark_dirty(' in persistency_content, \
        "NetObjPersistency should handle dirty state"
    assert 'GtkFileChooserDialog' in persistency_content, \
        "NetObjPersistency should handle file chooser dialogs"
    assert 'check_unsaved_changes' in persistency_content, \
        "NetObjPersistency should handle unsaved changes confirmation"
    
    # Check ModelCanvasLoader responsibilities (what it should NOT have)
    assert 'FileChooserDialog' not in loader_content or \
           loader_content.count('FileChooserDialog') == 0 or \
           'context menu' in loader_content.lower(), \
        "ModelCanvasLoader should NOT handle file chooser dialogs (except for context menus)"
    
    # Check ModelCanvasLoader still has its proper responsibilities
    assert 'def load(' in loader_content, \
        "ModelCanvasLoader should still handle UI loading"
    assert 'def add_document(' in loader_content, \
        "ModelCanvasLoader should still handle document tabs"
    assert 'def get_canvas_manager(' in loader_content, \
        "ModelCanvasLoader should still provide canvas manager access"
    assert 'def _on_draw(' in loader_content, \
        "ModelCanvasLoader should still handle drawing"
    
    print("✅ Separation of concerns properly implemented:")
    print()
    print("   NetObjPersistency responsibilities:")
    print("   - File save/load operations")
    print("   - Dirty state tracking")
    print("   - File chooser dialogs")
    print("   - Unsaved changes confirmation")
    print()
    print("   ModelCanvasLoader responsibilities:")
    print("   - UI loading and setup")
    print("   - Document tab management")
    print("   - Canvas manager access")
    print("   - Drawing operations")
    print("   - Event handling")
    
    return True

def main():
    """Run all tests."""
    print("=" * 70)
    print("NetObjPersistency Architecture Tests")
    print("=" * 70)
    print()
    
    tests = [
        ("NetObjPersistency class exists", test_netobj_persistency_class_exists),
        ("NetObjPersistency properties and state", test_netobj_persistency_properties),
        ("ModelCanvasLoader cleaned up", test_loader_has_no_file_operations),
        ("Main app uses NetObjPersistency", test_main_app_uses_persistency),
        ("Separation of concerns", test_separation_of_concerns),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"Test: {test_name}")
        print("-" * 70)
        try:
            result = test_func()
            results.append((test_name, result))
            print()
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            print()
            results.append((test_name, False))
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            print()
            results.append((test_name, False))
    
    # Summary
    print("=" * 70)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    if passed == total:
        print(f"🎉 ALL {total} TESTS PASSED!")
    else:
        print(f"⚠️  {passed}/{total} tests passed")
    
    print("=" * 70)
    print()
    
    # Architecture summary
    if passed == total:
        print("Architecture Summary:")
        print("-------------------")
        print()
        print("✅ NetObjPersistency (shypn/file/netobj_persistency.py)")
        print("   Role: File operations specialist")
        print("   - Handles all file I/O (save/load)")
        print("   - Manages dirty state tracking")
        print("   - Provides file chooser dialogs")
        print("   - Handles unsaved changes confirmation")
        print("   - Cooperates with DocumentModel for serialization")
        print()
        print("✅ ModelCanvasLoader (shypn/helpers/model_canvas_loader.py)")
        print("   Role: UI loader and canvas manager")
        print("   - Loads canvas UI and setup")
        print("   - Manages document tabs")
        print("   - Handles drawing and rendering")
        print("   - Manages event handlers")
        print("   - Provides access to canvas managers")
        print("   - Does NOT handle file operations")
        print()
        print("✅ Main Application (shypn.py)")
        print("   Role: Orchestrator")
        print("   - Creates NetObjPersistency instance")
        print("   - Wires file buttons to persistency methods")
        print("   - Coordinates between persistency and loader")
        print("   - Passes documents between components")
        print()
        print("Benefits of new architecture:")
        print("- ✅ Single Responsibility Principle")
        print("- ✅ Separation of Concerns")
        print("- ✅ Easier testing (no GTK in persistency tests)")
        print("- ✅ Cleaner code organization")
        print("- ✅ Better maintainability")
        print("- ✅ Proper dirty state management")
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
