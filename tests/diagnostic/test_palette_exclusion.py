#!/usr/bin/env python3
"""Test Master Palette button exclusion behavior in real app."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.ui import MasterPalette


def test_palette_exclusion():
    """Test that Master Palette buttons properly exclude each other."""
    
    palette = MasterPalette()
    
    # Track toggle events
    events = []
    
    def on_files_toggle(active):
        events.append(('files', active))
        print(f"  Files toggled: {active}")
        if active:
            # Deactivate others
            palette.set_active('pathways', False)
            palette.set_active('analyses', False)
            palette.set_active('topology', False)
            palette.set_active('report', False)
    
    def on_pathways_toggle(active):
        events.append(('pathways', active))
        print(f"  Pathways toggled: {active}")
        if active:
            # Deactivate others
            palette.set_active('files', False)
            palette.set_active('analyses', False)
            palette.set_active('topology', False)
            palette.set_active('report', False)
    
    def on_analyses_toggle(active):
        events.append(('analyses', active))
        print(f"  Analyses toggled: {active}")
        if active:
            # Deactivate others
            palette.set_active('files', False)
            palette.set_active('pathways', False)
            palette.set_active('topology', False)
            palette.set_active('report', False)
    
    # Connect handlers
    palette.connect('files', on_files_toggle)
    palette.connect('pathways', on_pathways_toggle)
    palette.connect('analyses', on_analyses_toggle)
    
    # Test 1: Activate Files
    print("\n=== Test 1: Activate Files ===")
    events.clear()
    palette.set_active('files', True)
    
    # Check state
    assert palette.is_active('files') == True, "Files should be active"
    assert palette.is_active('pathways') == False, "Pathways should be inactive"
    assert palette.is_active('analyses') == False, "Analyses should be inactive"
    print("  ✓ Files activated correctly")
    
    # Test 2: Activate Pathways (should deactivate Files)
    print("\n=== Test 2: Activate Pathways ===")
    events.clear()
    palette.set_active('pathways', True)
    
    # Check state
    assert palette.is_active('files') == False, "Files should be inactive"
    assert palette.is_active('pathways') == True, "Pathways should be active"
    assert palette.is_active('analyses') == False, "Analyses should be inactive"
    print("  ✓ Pathways activated, Files deactivated")
    
    # Test 3: Activate Analyses (should deactivate Pathways)
    print("\n=== Test 3: Activate Analyses ===")
    events.clear()
    palette.set_active('analyses', True)
    
    # Check state
    assert palette.is_active('files') == False, "Files should be inactive"
    assert palette.is_active('pathways') == False, "Pathways should be inactive"
    assert palette.is_active('analyses') == True, "Analyses should be active"
    print("  ✓ Analyses activated, Pathways deactivated")
    
    # Test 4: Deactivate current (Analyses)
    print("\n=== Test 4: Deactivate current ===")
    events.clear()
    palette.set_active('analyses', False)
    
    # Check state
    assert palette.is_active('files') == False, "Files should be inactive"
    assert palette.is_active('pathways') == False, "Pathways should be inactive"
    assert palette.is_active('analyses') == False, "Analyses should be inactive"
    print("  ✓ All panels deactivated")
    
    print("\n=== All tests passed! ===")
    return True


if __name__ == '__main__':
    try:
        success = test_palette_exclusion()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
