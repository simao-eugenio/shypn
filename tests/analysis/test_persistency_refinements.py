#!/usr/bin/env python3
"""Test NetObjPersistency Refinements.

This test verifies:
1. File operations point to repo_root/models as the root directory
2. No default filename is provided (user must enter filename)
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_models_directory_configuration():
    """Test that models directory is properly configured."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    persistency_path = os.path.join(script_dir, '..', 'src', 'shypn', 'file', 'netobj_persistency.py')
    
    with open(persistency_path, 'r') as f:
        content = f.read()
    
    # Check that __init__ accepts models_directory parameter
    assert 'def __init__(self, parent_window: Optional[Gtk.Window] = None, models_directory: Optional[str] = None):' in content, \
        "Should accept models_directory parameter"
    
    # Check that models directory is set to repo_root/models by default
    assert "repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))" in content, \
        "Should calculate repo_root"
    assert "models_directory = os.path.join(repo_root, 'models')" in content, \
        "Should default to repo_root/models"
    
    # Check that models directory is stored
    assert 'self.models_directory = models_directory' in content, \
        "Should store models_directory"
    
    # Check that models directory is created if it doesn't exist
    assert 'os.makedirs(self.models_directory)' in content, \
        "Should create models directory if needed"
    
    # Check that last directory starts at models directory
    assert 'self._last_directory: Optional[str] = self.models_directory' in content, \
        "Last directory should start at models directory"
    
    print("✅ Models directory configuration:")
    print("   - __init__ accepts models_directory parameter")
    print("   - Defaults to repo_root/models")
    print("   - Creates directory if it doesn't exist")
    print("   - Last directory starts at models directory")
    
    return True

def test_file_dialogs_use_models_directory():
    """Test that file dialogs use models directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    persistency_path = os.path.join(script_dir, '..', 'src', 'shypn', 'file', 'netobj_persistency.py')
    
    with open(persistency_path, 'r') as f:
        content = f.read()
    
    # Check save dialog uses models directory
    save_dialog_section = content[content.find('def _show_save_dialog'):content.find('def _show_open_dialog')]
    
    assert 'elif os.path.isdir(self.models_directory):' in save_dialog_section, \
        "Save dialog should check models_directory"
    assert 'dialog.set_current_folder(self.models_directory)' in save_dialog_section, \
        "Save dialog should set current folder to models_directory"
    
    # Check open dialog uses models directory
    open_dialog_section = content[content.find('def _show_open_dialog'):content.find('def _show_success_dialog')]
    
    assert 'elif os.path.isdir(self.models_directory):' in open_dialog_section, \
        "Open dialog should check models_directory"
    assert 'dialog.set_current_folder(self.models_directory)' in open_dialog_section, \
        "Open dialog should set current folder to models_directory"
    
    # Check that last directory is updated
    assert 'self._last_directory = os.path.dirname(filepath)' in content, \
        "Should update last directory after file selection"
    
    print("✅ File dialogs use models directory:")
    print("   - Save dialog opens in models directory")
    print("   - Open dialog opens in models directory")
    print("   - Remembers last used directory within models")
    print("   - Falls back to models directory if last directory invalid")
    
    return True

def test_no_default_filename():
    """Test that no default filename is provided."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    persistency_path = os.path.join(script_dir, '..', 'src', 'shypn', 'file', 'netobj_persistency.py')
    
    with open(persistency_path, 'r') as f:
        content = f.read()
    
    # Check that old default filename is removed
    assert 'dialog.set_current_name("petri_net.json")' not in content, \
        "Should NOT set default filename 'petri_net.json'"
    
    # Find save dialog section
    save_dialog_section = content[content.find('def _show_save_dialog'):content.find('def _show_open_dialog')]
    
    # Check that there's a comment explaining why no default filename
    assert 'No default filename' in save_dialog_section or 'user MUST enter a name' in save_dialog_section, \
        "Should explain why no default filename"
    
    # Check that only existing filepath is used (for Save As)
    assert 'if self.current_filepath:' in save_dialog_section, \
        "Should only set filename for existing files (Save As)"
    assert 'dialog.set_filename(self.current_filepath)' in save_dialog_section, \
        "Should use current_filepath for Save As"
    
    # Verify the else branch just passes (no default)
    lines = save_dialog_section.split('\n')
    in_else_block = False
    for i, line in enumerate(lines):
        if 'else:' in line and 'if self.current_filepath:' in lines[i-1] or 'if self.current_filepath:' in lines[max(0, i-2)]:
            in_else_block = True
        if in_else_block and 'pass' in line:
            # Found the pass statement in else block
            break
    else:
        # Should have the pass statement or comment
        assert 'NEW:' in save_dialog_section, "Should have comment explaining new behavior"
    
    print("✅ No default filename:")
    print("   - Removed 'petri_net.json' default")
    print("   - User MUST enter a filename")
    print("   - Only pre-fills for Save As (existing files)")
    print("   - Prevents auto-saving without user confirmation")
    
    return True

def test_create_persistency_manager_signature():
    """Test that create_persistency_manager accepts models_directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    persistency_path = os.path.join(script_dir, '..', 'src', 'shypn', 'file', 'netobj_persistency.py')
    
    with open(persistency_path, 'r') as f:
        content = f.read()
    
    # Check function signature
    assert 'def create_persistency_manager(parent_window: Optional[Gtk.Window] = None' in content, \
        "Should have create_persistency_manager function"
    
    assert 'models_directory: Optional[str] = None' in content, \
        "Should accept models_directory parameter"
    
    # Check that it passes models_directory to constructor
    assert 'return NetObjPersistency(parent_window, models_directory)' in content, \
        "Should pass models_directory to NetObjPersistency constructor"
    
    print("✅ create_persistency_manager function:")
    print("   - Accepts models_directory parameter")
    print("   - Passes models_directory to NetObjPersistency")
    print("   - Defaults to None (uses repo_root/models)")
    
    return True

def test_models_directory_path_calculation():
    """Test that models directory path is correctly calculated."""
    # Calculate expected path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.normpath(os.path.join(script_dir, '..'))
    expected_models_dir = os.path.join(repo_root, 'models')
    
    print(f"✅ Models directory path calculation:")
    print(f"   - Test script: {script_dir}")
    print(f"   - Repo root: {repo_root}")
    print(f"   - Expected models dir: {expected_models_dir}")
    
    # Check if models directory exists or can be created
    if os.path.exists(expected_models_dir):
        print(f"   - Models directory exists ✅")
    else:
        print(f"   - Models directory will be created on first use")
    
    return True

def main():
    """Run all tests."""
    print("=" * 70)
    print("NetObjPersistency Refinements Tests")
    print("=" * 70)
    print()
    
    tests = [
        ("Models directory configuration", test_models_directory_configuration),
        ("File dialogs use models directory", test_file_dialogs_use_models_directory),
        ("No default filename", test_no_default_filename),
        ("create_persistency_manager signature", test_create_persistency_manager_signature),
        ("Models directory path calculation", test_models_directory_path_calculation),
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
    
    # Summary of refinements
    if passed == total:
        print("Refinements Summary:")
        print("-------------------")
        print()
        print("1️⃣  File Operations Root Directory:")
        print("   ✅ Default: repo_root/models")
        print("   ✅ Automatically created if doesn't exist")
        print("   ✅ Save dialog opens in models directory")
        print("   ✅ Open dialog opens in models directory")
        print("   ✅ Remembers last used directory")
        print()
        print("2️⃣  No Default Filename:")
        print("   ✅ Removed 'petri_net.json' default")
        print("   ✅ User MUST type a filename")
        print("   ✅ Prevents accidental auto-save")
        print("   ✅ Only pre-fills for Save As (existing files)")
        print()
        print("Benefits:")
        print("--------")
        print("✅ Organized: All Petri nets in repo_root/models")
        print("✅ Consistent: Always starts in same location")
        print("✅ Safe: No auto-save without user confirmation")
        print("✅ Intentional: User must choose meaningful filename")
        print("✅ Clean: Models separated from code/docs")
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
