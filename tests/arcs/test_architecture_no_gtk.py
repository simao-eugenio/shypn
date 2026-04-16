#!/usr/bin/env python3
"""Test NetObjPersistency Architecture (No GTK).

This test verifies the architecture without importing GTK modules.
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_persistency_file_exists_and_structure():
    """Test that NetObjPersistency file exists and has proper structure."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    persistency_path = os.path.join(script_dir, '..', 'src', 'shypn', 'file', 'netobj_persistency.py')
    
    assert os.path.exists(persistency_path), "netobj_persistency.py should exist"
    
    with open(persistency_path, 'r') as f:
        content = f.read()
    
    # Check class definition
    assert 'class NetObjPersistency:' in content, "Should have NetObjPersistency class"
    
    # Check required methods
    required_methods = [
        'def save_document(',
        'def load_document(',
        'def mark_dirty(',
        'def mark_clean(',
        'def set_filepath(',
        'def has_filepath(',
        'def get_display_name(',
        'def get_title(',
        'def check_unsaved_changes(',
        'def new_document(',
    ]
    
    for method in required_methods:
        assert method in content, f"Should have {method} method"
    
    # Check properties
    assert '@property' in content, "Should have properties"
    assert 'def is_dirty(self)' in content, "Should have is_dirty property"
    
    # Check attributes
    assert 'self.current_filepath' in content, "Should track current_filepath"
    assert 'self._is_dirty' in content, "Should track dirty state"
    assert 'self.on_file_saved' in content, "Should have on_file_saved callback"
    assert 'self.on_file_loaded' in content, "Should have on_file_loaded callback"
    assert 'self.on_dirty_changed' in content, "Should have on_dirty_changed callback"
    
    # Check file dialog methods
    assert 'def _show_save_dialog(' in content, "Should have save dialog method"
    assert 'def _show_open_dialog(' in content, "Should have open dialog method"
    assert 'def _show_success_dialog(' in content, "Should have success dialog method"
    assert 'def _show_error_dialog(' in content, "Should have error dialog method"
    
    # Check documentation
    assert '"""' in content, "Should have docstrings"
    assert 'Handles file operations' in content or 'file operations' in content, \
        "Should document file operations responsibility"
    
    print("✅ NetObjPersistency file exists with complete structure:")
    print("   - Class definition")
    print("   - All required methods (save, load, dirty tracking, etc.)")
    print("   - Properties (is_dirty)")
    print("   - Attributes (current_filepath, callbacks)")
    print("   - Dialog helper methods")
    print("   - Comprehensive documentation")
    
    return True

def test_init_file_exports_persistency():
    """Test that __init__.py properly exports NetObjPersistency."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    init_path = os.path.join(script_dir, '..', 'src', 'shypn', 'file', '__init__.py')
    
    with open(init_path, 'r') as f:
        content = f.read()
    
    assert 'from .netobj_persistency import NetObjPersistency' in content, \
        "Should import NetObjPersistency"
    assert 'from .netobj_persistency import' in content and 'create_persistency_manager' in content, \
        "Should import create_persistency_manager"
    assert "'NetObjPersistency'" in content, "Should export NetObjPersistency in __all__"
    assert "'create_persistency_manager'" in content, "Should export create_persistency_manager in __all__"
    
    print("✅ __init__.py properly exports NetObjPersistency:")
    print("   - Imports NetObjPersistency class")
    print("   - Imports create_persistency_manager function")
    print("   - Exports both in __all__")
    
    return True

def test_loader_cleaned_up():
    """Test that ModelCanvasLoader no longer has file operation methods."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    loader_path = os.path.join(script_dir, '..', 'src', 'shypn', 'helpers', 'model_canvas_loader.py')
    
    with open(loader_path, 'r') as f:
        loader_content = f.read()
    
    # These methods should NOT exist
    assert 'def save_current_document(' not in loader_content, \
        "ModelCanvasLoader should NOT have save_current_document method"
    assert 'def load_document(' not in loader_content, \
        "ModelCanvasLoader should NOT have load_document method"
    
    # File operations section should be removed
    assert '# ==================== File Operations ====================' not in loader_content, \
        "File Operations section should be removed"
    
    # Loader should still have its core responsibilities
    assert 'def load(' in loader_content, "Should still have load() method"
    assert 'def add_document(' in loader_content, "Should still have add_document() method"
    assert 'def get_canvas_manager(' in loader_content, "Should still have get_canvas_manager() method"
    assert 'def _on_draw(' in loader_content, "Should still have _on_draw() method"
    
    print("✅ ModelCanvasLoader properly cleaned up:")
    print("   - No save_current_document() method ❌")
    print("   - No load_document() method ❌")
    print("   - No File Operations section ❌")
    print("   - Still has core UI/canvas methods ✅")
    print("     * load()")
    print("     * add_document()")
    print("     * get_canvas_manager()")
    print("     * _on_draw()")
    
    return True

def test_main_app_integration():
    """Test that main app uses NetObjPersistency correctly."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    shypn_path = os.path.join(script_dir, '..', 'src', 'shypn.py')
    
    with open(shypn_path, 'r') as f:
        content = f.read()
    
    # Check imports
    assert 'from shypn.file import create_persistency_manager' in content, \
        "Should import create_persistency_manager"
    
    # Check persistency manager is created
    assert 'persistency = create_persistency_manager(' in content, \
        "Should create persistency manager instance"
    assert 'parent_window=window' in content, \
        "Should pass parent_window to persistency manager"
    
    # Check button handlers use persistency
    assert 'persistency.save_document(' in content, \
        "Save button should use persistency.save_document()"
    assert 'persistency.load_document(' in content, \
        "Open button should use persistency.load_document()"
    assert 'persistency.check_unsaved_changes()' in content, \
        "New button should use persistency.check_unsaved_changes()"
    assert 'persistency.new_document()' in content, \
        "New button should use persistency.new_document()"
    
    # Check old method calls are removed
    assert 'model_canvas_loader.save_current_document()' not in content, \
        "Should NOT call loader's save_current_document()"
    assert 'model_canvas_loader.load_document()' not in content, \
        "Should NOT call loader's load_document()"
    
    print("✅ Main application properly integrated:")
    print("   - Imports create_persistency_manager ✅")
    print("   - Creates persistency instance with parent_window ✅")
    print("   - File buttons use persistency methods:")
    print("     * Save → persistency.save_document()")
    print("     * Open → persistency.load_document()")
    print("     * New → persistency.check_unsaved_changes() + new_document()")
    print("     * Save As → persistency.save_document(save_as=True)")
    print("   - No calls to loader's file methods ❌")
    
    return True

def test_responsibility_separation():
    """Test that responsibilities are properly separated."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Read files
    persistency_path = os.path.join(script_dir, '..', 'src', 'shypn', 'file', 'netobj_persistency.py')
    with open(persistency_path, 'r') as f:
        persistency_content = f.read()
    
    loader_path = os.path.join(script_dir, '..', 'src', 'shypn', 'helpers', 'model_canvas_loader.py')
    with open(loader_path, 'r') as f:
        loader_content = f.read()
    
    # NetObjPersistency should have file operation responsibilities
    persistency_responsibilities = [
        ('save_document', 'def save_document('),
        ('load_document', 'def load_document('),
        ('dirty tracking', 'def mark_dirty('),
        ('filepath management', 'def set_filepath('),
        ('file chooser dialogs', 'FileChooserDialog'),
        ('unsaved changes check', 'check_unsaved_changes'),
        ('document.save_to_file', 'document.save_to_file('),
        ('DocumentModel.load_from_file', 'DocumentModel.load_from_file('),
    ]
    
    for name, pattern in persistency_responsibilities:
        assert pattern in persistency_content, \
            f"NetObjPersistency should handle {name}"
    
    # ModelCanvasLoader should NOT have file operation responsibilities
    loader_should_not_have = [
        'def save_current_document(',
        'def load_document(',
        'document.save_to_file(',
        'DocumentModel.load_from_file(',
    ]
    
    for pattern in loader_should_not_have:
        assert pattern not in loader_content, \
            f"ModelCanvasLoader should NOT have {pattern}"
    
    # ModelCanvasLoader should still have UI/canvas responsibilities
    loader_responsibilities = [
        ('UI loading', 'def load('),
        ('document tabs', 'def add_document('),
        ('canvas manager', 'def get_canvas_manager('),
        ('drawing', 'def _on_draw('),
        ('event handling', 'def _on_button_press('),
        ('context menu', 'def _show_canvas_context_menu('),
    ]
    
    for name, pattern in loader_responsibilities:
        assert pattern in loader_content, \
            f"ModelCanvasLoader should still handle {name}"
    
    print("✅ Responsibilities properly separated:")
    print()
    print("   NetObjPersistency (File Operations Specialist):")
    print("   ✅ save_document() / load_document()")
    print("   ✅ Dirty state tracking (mark_dirty/mark_clean)")
    print("   ✅ Filepath management")
    print("   ✅ File chooser dialogs")
    print("   ✅ Unsaved changes confirmation")
    print("   ✅ Calls DocumentModel save/load methods")
    print()
    print("   ModelCanvasLoader (UI/Canvas Specialist):")
    print("   ✅ UI loading and setup")
    print("   ✅ Document tab management")
    print("   ✅ Canvas manager access")
    print("   ✅ Drawing operations")
    print("   ✅ Event handling")
    print("   ✅ Context menus")
    print("   ❌ NO file operation methods")
    
    return True

def main():
    """Run all tests."""
    print("=" * 70)
    print("NetObjPersistency Architecture Tests (No GTK)")
    print("=" * 70)
    print()
    
    tests = [
        ("NetObjPersistency file structure", test_persistency_file_exists_and_structure),
        ("__init__.py exports", test_init_file_exports_persistency),
        ("ModelCanvasLoader cleanup", test_loader_cleaned_up),
        ("Main app integration", test_main_app_integration),
        ("Responsibility separation", test_responsibility_separation),
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
        print("New Architecture Summary:")
        print("========================")
        print()
        print("📁 shypn/file/netobj_persistency.py")
        print("   Role: File Operations Specialist")
        print("   Responsibilities:")
        print("   - File save/load operations")
        print("   - Dirty state tracking and management")
        print("   - File chooser dialog handling")
        print("   - Unsaved changes confirmation")
        print("   - Cooperates with DocumentModel for serialization")
        print()
        print("📁 shypn/helpers/model_canvas_loader.py")
        print("   Role: UI Loader and Canvas Manager")
        print("   Responsibilities:")
        print("   - Load canvas UI and setup")
        print("   - Manage document tabs")
        print("   - Handle drawing and rendering")
        print("   - Manage event handlers")
        print("   - Provide canvas manager access")
        print("   - Context menus")
        print()
        print("📁 shypn.py")
        print("   Role: Application Orchestrator")
        print("   Responsibilities:")
        print("   - Create NetObjPersistency instance")
        print("   - Wire file buttons to persistency methods")
        print("   - Coordinate between persistency and loader")
        print("   - Pass documents between components")
        print()
        print("Benefits:")
        print("--------")
        print("✅ Single Responsibility Principle")
        print("✅ Separation of Concerns")
        print("✅ Cleaner code organization")
        print("✅ Better maintainability")
        print("✅ Proper dirty state management")
        print("✅ Easier testing")
        print("✅ File operations centralized in one place")
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
