#!/usr/bin/env python3
"""Test script for new Dynamic Analyses Panel architecture.

This script tests the new OOP-based Dynamic Analyses panel with:
- 3 CategoryFrame expanders (Transitions, Places, Diagnostics)
- No GtkNotebook tabs
- Same functionality as before but cleaner structure
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Add src to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.ui.panels.dynamic_analyses import DynamicAnalysesPanel


def test_panel_creation():
    """Test creating the panel without model or data collector."""
    print("=" * 60)
    print("TEST 1: Panel Creation (No Model/Data Collector)")
    print("=" * 60)
    
    try:
        panel = DynamicAnalysesPanel()
        print("✓ Panel created successfully")
        print(f"  - Type: {type(panel)}")
        print(f"  - Categories: {len(panel.categories)}")
        for i, cat in enumerate(panel.categories, 1):
            print(f"    {i}. {cat.category_frame.title}")
        return panel
    except Exception as e:
        print(f"✗ Failed to create panel: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_panel_in_window(panel):
    """Test displaying panel in a window."""
    print("\n" + "=" * 60)
    print("TEST 2: Display Panel in Window")
    print("=" * 60)
    
    if not panel:
        print("✗ No panel to test")
        return None
    
    try:
        window = Gtk.Window(title="Dynamic Analyses Panel Test")
        window.set_default_size(400, 600)
        window.connect("destroy", Gtk.main_quit)
        
        window.add(panel)
        window.show_all()
        
        print("✓ Panel displayed in window")
        print("  - Press Ctrl+C or close window to exit")
        return window
    except Exception as e:
        print(f"✗ Failed to display panel: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_report_integration(panel):
    """Test report panel integration features."""
    print("\n" + "=" * 60)
    print("TEST 3: Report Panel Integration")
    print("=" * 60)
    
    if not panel:
        print("✗ No panel to test")
        return
    
    try:
        # Test setting callback
        def mock_callback():
            print("  → Report panel would refresh here")
        
        panel.set_report_refresh_callback(mock_callback)
        print("✓ Report refresh callback set")
        
        # Test generating summary
        summary = panel.generate_summary_for_report_panel()
        print("✓ Generated summary for report panel:")
        print(f"  - Category: {summary['category']}")
        print(f"  - Status: {summary['status']}")
        print(f"  - Summary lines: {len(summary['summary_lines'])}")
        for line in summary['summary_lines']:
            print(f"    • {line}")
        
        # Test notification
        panel.notify_report_panel()
        print("✓ Report panel notification sent")
        
    except Exception as e:
        print(f"✗ Report integration test failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("DYNAMIC ANALYSES PANEL - ARCHITECTURE TEST")
    print("=" * 60)
    print()
    
    # Test 1: Create panel
    panel = test_panel_creation()
    
    if panel:
        # Test 2: Report integration (before showing window)
        test_report_integration(panel)
        
        # Test 3: Display in window
        window = test_panel_in_window(panel)
        
        if window:
            print("\n" + "=" * 60)
            print("ALL TESTS PASSED - Starting GTK main loop")
            print("=" * 60)
            Gtk.main()
        else:
            print("\n" + "=" * 60)
            print("WINDOW TEST FAILED")
            print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("PANEL CREATION FAILED")
        print("=" * 60)


if __name__ == '__main__':
    main()
