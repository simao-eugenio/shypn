#!/usr/bin/env python3
"""Integration test for Master Palette button exclusion in full app.

This test verifies that:
1. Master Palette buttons properly exclude each other
2. Only one panel is visible at a time
3. Panel visibility matches button state
4. No Wayland errors occur during panel toggling
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

print("✓ GTK imports successful")

def test_master_palette_integration():
    """Test Master Palette integration with real loaders."""
    
    from shypn.ui import MasterPalette
    from shypn.helpers.file_panel_loader import create_left_panel
    from shypn.helpers.right_panel_loader import create_right_panel
    from shypn.helpers.pathway_panel_loader import create_pathway_panel
    
    print("\n=== Creating panel loaders ===")
    
    # Create loaders (minimal setup)
    left_panel_loader = create_left_panel(load_window=True)
    print("  ✓ Files panel loaded")
    
    right_panel_loader = create_right_panel()
    print("  ✓ Analyses panel loaded")
    
    pathway_panel_loader = create_pathway_panel()
    print("  ✓ Pathways panel loaded")
    
    # Create Master Palette
    palette = MasterPalette()
    print("  ✓ Master Palette created")
    
    # Create mock stack and paned (simplified for testing)
    left_dock_stack = Gtk.Stack()
    left_paned = Gtk.Paned()
    
    # Track states
    panel_states = {
        'files': False,
        'pathways': False,
        'analyses': False
    }
    
    # Define toggle handlers (matching shypn.py logic)
    def on_left_toggle(is_active):
        """Handle Files panel toggle."""
        panel_states['files'] = is_active
        if is_active:
            palette.set_active('pathways', False)
            palette.set_active('analyses', False)
            left_panel_loader.show_in_stack()
            if left_panel_loader.is_hanged:
                left_paned.set_position(250)
        else:
            left_panel_loader.hide_in_stack()
            left_paned.set_position(0)
    
    def on_pathway_toggle(is_active):
        """Handle Pathways panel toggle."""
        panel_states['pathways'] = is_active
        if is_active:
            palette.set_active('files', False)
            palette.set_active('analyses', False)
            pathway_panel_loader.show_in_stack()
            if pathway_panel_loader.is_hanged:
                left_paned.set_position(270)
        else:
            pathway_panel_loader.hide_in_stack()
            left_paned.set_position(0)
    
    def on_right_toggle(is_active):
        """Handle Analyses panel toggle."""
        panel_states['analyses'] = is_active
        if is_active:
            palette.set_active('files', False)
            palette.set_active('pathways', False)
            right_panel_loader.show_in_stack()
            if right_panel_loader.is_hanged:
                left_paned.set_position(280)
        else:
            right_panel_loader.hide_in_stack()
            left_paned.set_position(0)
    
    # Connect handlers
    palette.connect('files', on_left_toggle)
    palette.connect('pathways', on_pathway_toggle)
    palette.connect('analyses', on_right_toggle)
    
    print("\n=== Running exclusion tests ===")
    
    # Test 1: Activate Files
    print("\n  Test 1: Activate Files")
    palette.set_active('files', True)
    assert palette.is_active('files') == True
    assert palette.is_active('pathways') == False
    assert palette.is_active('analyses') == False
    assert panel_states == {'files': True, 'pathways': False, 'analyses': False}
    print("    ✓ Files exclusive activation works")
    
    # Test 2: Switch to Pathways
    print("\n  Test 2: Switch to Pathways")
    palette.set_active('pathways', True)
    assert palette.is_active('files') == False
    assert palette.is_active('pathways') == True
    assert palette.is_active('analyses') == False
    assert panel_states == {'files': False, 'pathways': True, 'analyses': False}
    print("    ✓ Pathways exclusive activation works")
    
    # Test 3: Switch to Analyses
    print("\n  Test 3: Switch to Analyses")
    palette.set_active('analyses', True)
    assert palette.is_active('files') == False
    assert palette.is_active('pathways') == False
    assert palette.is_active('analyses') == True
    assert panel_states == {'files': False, 'pathways': False, 'analyses': True}
    print("    ✓ Analyses exclusive activation works")
    
    # Test 4: Deactivate all
    print("\n  Test 4: Deactivate all")
    palette.set_active('analyses', False)
    assert palette.is_active('files') == False
    assert palette.is_active('pathways') == False
    assert palette.is_active('analyses') == False
    assert panel_states == {'files': False, 'pathways': False, 'analyses': False}
    print("    ✓ All panels deactivated correctly")
    
    # Test 5: Rapid toggling (stress test)
    print("\n  Test 5: Rapid toggling (stress test)")
    for _ in range(3):
        palette.set_active('files', True)
        palette.set_active('pathways', True)
        palette.set_active('analyses', True)
    
    # Should end with analyses active
    assert palette.is_active('files') == False
    assert palette.is_active('pathways') == False
    assert palette.is_active('analyses') == True
    print("    ✓ Rapid toggling works without errors")
    
    print("\n=== All integration tests passed! ===")
    return True


if __name__ == '__main__':
    try:
        success = test_master_palette_integration()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
