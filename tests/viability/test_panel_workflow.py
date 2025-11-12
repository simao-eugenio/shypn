#!/usr/bin/env python3
"""End-to-end workflow test for Viability Panel.

Tests the complete user workflow:
1. Add transitions to list
2. Select transitions  
3. Click Diagnose
4. View results in category expanders
5. Apply suggestions

Author: Simão Eugénio
Date: November 12, 2025
"""

import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

def run_manual_test():
    """Run manual end-to-end test of viability panel workflow."""
    
    print("\n" + "=" * 70)
    print("VIABILITY PANEL - END-TO-END WORKFLOW TEST")
    print("=" * 70)
    print()
    print("This test will verify the complete viability panel workflow:")
    print("  1. Add transitions to localities list")
    print("  2. Select transitions with checkboxes")
    print("  3. Click 'Diagnose Selected' button")
    print("  4. View results in category expanders")
    print("  5. Verify TreeView displays suggestions")
    print()
    print("Press ENTER to continue or Ctrl+C to cancel...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nTest cancelled")
        return False
    
    # Import application
    print("\n✓ Loading Shypn application...")
    try:
        import os
        os.chdir('/home/simao/projetos/shypn')
        sys.path.insert(0, '/home/simao/projetos/shypn/src')
        
        from shypn import create_main_window
    except Exception as e:
        print(f"\n✗ Failed to load application: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("✓ Application loaded")
    
    # Create window
    print("✓ Creating main window...")
    try:
        window = create_main_window()
    except Exception as e:
        print(f"\n✗ Failed to create window: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("✓ Main window created")
    
    # Show instructions
    print()
    print("=" * 70)
    print("MANUAL TEST INSTRUCTIONS")
    print("=" * 70)
    print()
    print("STEP 1: Load a Model")
    print("  ☐ Click Files panel (folder icon)")
    print("  ☐ Open a model from data/biomodels_test/")
    print()
    print("STEP 2: Open Viability Panel")
    print("  ☐ Click Viability button in Master Palette")
    print("  ☐ Verify panel appears with:")
    print("     - 'Selected Localities' frame (empty)")
    print("     - 'Diagnose Selected' button (disabled)")
    print("     - 4 collapsed expanders (Summary, Structural, Biological, Kinetic)")
    print()
    print("STEP 3: Add Transitions to List")
    print("  ☐ Right-click a transition on canvas")
    print("  ☐ Select 'Add to Viability Analysis'")
    print("  ☐ Verify transition appears in localities list with checkbox")
    print("  ☐ Verify 'Diagnose Selected' button becomes enabled")
    print("  ☐ Add 2-3 more transitions")
    print()
    print("STEP 4: Run Diagnosis")
    print("  ☐ Ensure checkboxes are checked for transitions to analyze")
    print("  ☐ Click 'Diagnose Selected' button")
    print("  ☐ Wait for analysis to complete")
    print()
    print("STEP 5: Verify Results Display")
    print("  ☐ 'Diagnosis Summary' expander auto-expands")
    print("  ☐ Summary shows:")
    print("     - Timestamp")
    print("     - Number of transitions analyzed")
    print("     - Issues found count")
    print("     - Suggestions count")
    print("     - Health bars (Structural, Biological, Kinetic)")
    print()
    print("STEP 6: Verify Suggestion Categories")
    print("  ☐ Click 'Structural Suggestions' expander")
    print("  ☐ Verify TreeView shows columns:")
    print("     - Priority")
    print("     - Issue")
    print("     - Suggestion")
    print("     - Confidence")
    print("  ☐ Verify suggestions are displayed (if any found)")
    print("  ☐ Repeat for Biological and Kinetic expanders")
    print()
    print("STEP 7: Test List Management")
    print("  ☐ Uncheck some transitions")
    print("  ☐ Click 'Diagnose Selected' again")
    print("  ☐ Verify only checked transitions are analyzed")
    print("  ☐ Click 'Clear All' button")
    print("  ☐ Verify list is cleared")
    print("  ☐ Verify 'Diagnose Selected' button becomes disabled")
    print()
    print("STEP 8: Test Expander Behavior")
    print("  ☐ Click expander headers to collapse/expand")
    print("  ☐ Verify smooth expand/collapse animation")
    print("  ☐ Verify content is preserved when collapsed")
    print()
    print("=" * 70)
    print()
    print("The window will remain open for testing.")
    print("Close the window when done.")
    print()
    
    # Show window
    window.show()
    
    # Run GTK main loop
    try:
        Gtk.main()
    except KeyboardInterrupt:
        print("\nTest interrupted")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print()
    print("Please report any issues found during testing.")
    print()
    
    return True

if __name__ == '__main__':
    success = run_manual_test()
    sys.exit(0 if success else 1)
