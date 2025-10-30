#!/usr/bin/env python3
"""Visual integration test for Pathway Operations panel.

This script launches the application and verifies the Pathway Operations
panel is accessible and displays correctly in the UI.

Usage:
    python3 test_pathway_operations_integration.py
    
Expected behavior:
    1. Application window opens
    2. Pathway Operations panel is in left dock
    3. All three categories (KEGG, SBML, BRENDA) are visible
    4. Categories can be expanded/collapsed
    5. UI elements are interactive
"""
import os
import sys
import time

# Suppress Wayland warnings
os.environ['G_MESSAGES_DEBUG'] = ''

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print(f'ERROR: GTK3 not available: {e}', file=sys.stderr)
    sys.exit(1)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_integration():
    """Test that panel integrates correctly."""
    print("=" * 70)
    print("PATHWAY OPERATIONS PANEL - INTEGRATION TEST")
    print("=" * 70)
    print()
    print("This test verifies the Pathway Operations panel is properly")
    print("integrated into the main application.")
    print()
    print("Instructions:")
    print("1. Application window will open")
    print("2. Look for 'Pathway Operations' in the left panel dock")
    print("3. Verify three categories are visible:")
    print("   - KEGG (import from KEGG database)")
    print("   - SBML (import from SBML files/BioModels)")
    print("   - BRENDA (enrich with kinetic parameters)")
    print("4. Try expanding/collapsing each category")
    print("5. Window will close automatically after 10 seconds")
    print()
    print("Press Ctrl+C to cancel, or wait for test to start...")
    print()
    
    try:
        time.sleep(2)
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
        return
    
    # Import main application
    from shypn import create_main_window
    
    print("✓ Loading main application...")
    
    # Create window
    window = create_main_window()
    
    if not window:
        print("✗ Failed to create main window")
        sys.exit(1)
    
    print("✓ Main window created")
    print()
    print("=" * 70)
    print("VISUAL INSPECTION")
    print("=" * 70)
    print()
    print("Please verify:")
    print("  ☐ Pathway Operations panel visible in left dock")
    print("  ☐ KEGG category present")
    print("  ☐ SBML category present")
    print("  ☐ BRENDA category present")
    print("  ☐ Categories expand/collapse correctly")
    print()
    print("Window will close in 10 seconds...")
    print()
    
    # Show window
    window.show()
    
    # Auto-close after 10 seconds
    def auto_close():
        print("\n✓ Integration test complete")
        print()
        print("If you saw all three categories in the Pathway Operations panel,")
        print("the integration was successful!")
        Gtk.main_quit()
        return False
    
    GLib.timeout_add_seconds(10, auto_close)
    
    # Run GTK main loop
    Gtk.main()

if __name__ == '__main__':
    test_integration()
