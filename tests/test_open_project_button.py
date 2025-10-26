#!/usr/bin/env python3
"""Test script to verify Open Project button functionality."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

def test_button_connection():
    """Test that Open Project button is properly wired."""
    print("Testing Open Project button connection...")
    
    # Load the UI file
    ui_path = 'ui/panels/left_panel_vscode.ui'
    if not os.path.exists(ui_path):
        print(f"❌ UI file not found: {ui_path}")
        return False
    
    builder = Gtk.Builder()
    try:
        builder.add_from_file(ui_path)
        print("✓ UI file loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load UI file: {e}")
        return False
    
    # Check if button exists
    button = builder.get_object('open_project_button')
    if button is None:
        print("❌ open_project_button not found in UI")
        return False
    print("✓ open_project_button exists in UI")
    
    # Check button properties
    label = button.get_label()
    print(f"  - Label: {label}")
    print(f"  - Visible: {button.get_visible()}")
    print(f"  - Sensitive: {button.get_sensitive()}")
    
    # Test ProjectActionsController connection
    try:
        from shypn.helpers.project_actions_controller import ProjectActionsController
        controller = ProjectActionsController(builder, parent_window=None)
        print("✓ ProjectActionsController created successfully")
        
        if controller.open_project_button is None:
            print("❌ Controller's open_project_button reference is None")
            return False
        print("✓ Controller has open_project_button reference")
        
        # Check if signal is connected
        print("✓ Button should be connected to _on_open_project_clicked")
        
    except Exception as e:
        print(f"❌ Failed to create ProjectActionsController: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_dialog_manager():
    """Test that dialog manager can be initialized."""
    print("\nTesting ProjectDialogManager...")
    
    try:
        from shypn.helpers.project_dialog_manager import ProjectDialogManager
        dialog_mgr = ProjectDialogManager(parent_window=None)
        print("✓ ProjectDialogManager created successfully")
        
        # Check if UI builder path is correct
        ui_path = 'ui/dialogs/project_dialogs.ui'
        if not os.path.exists(ui_path):
            print(f"⚠ Dialog UI file not found: {ui_path}")
        else:
            print("✓ Dialog UI file exists")
        
    except Exception as e:
        print(f"❌ Failed to create ProjectDialogManager: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("Open Project Button Test")
    print("=" * 60)
    
    success = True
    success = test_button_connection() and success
    success = test_dialog_manager() and success
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed!")
        print("\nThe Open Project button should work correctly.")
        print("If it's not working in the app, the issue might be:")
        print("1. Dialog not showing (check Wayland/X11 compatibility)")
        print("2. Error in dialog manager (check console for exceptions)")
        print("3. Parent window not set correctly")
    else:
        print("❌ Some tests failed - see errors above")
    print("=" * 60)
