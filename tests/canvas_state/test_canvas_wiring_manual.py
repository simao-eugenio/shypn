#!/usr/bin/env python3
"""
Manual Test Script: Canvas Wiring - All Scenarios

This script provides step-by-step manual testing instructions
for verifying data_collector wiring in all canvas creation scenarios.

Run this script to get interactive testing prompts.

Author: AI Assistant + User
Date: October 24, 2025
"""

import sys


def print_header(title):
    """Print a formatted test header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def print_test_section(number, title):
    """Print a test section header."""
    print(f"\n{'─'*70}")
    print(f"TEST {number}: {title}")
    print(f"{'─'*70}\n")


def wait_for_confirmation():
    """Wait for user to confirm test completion."""
    response = input("Did the test PASS? (y/n/skip): ").strip().lower()
    if response == 'y':
        print("✅ PASS\n")
        return "PASS"
    elif response == 'n':
        print("❌ FAIL\n")
        return "FAIL"
    else:
        print("⚠️  SKIPPED\n")
        return "SKIP"


def test_startup_canvas():
    """Test 1: Startup default canvas."""
    print_test_section(1, "Startup Default Canvas")
    
    print("Instructions:")
    print("1. Launch the application: python3 src/shypn.py")
    print("2. On the DEFAULT canvas (no File → New needed):")
    print("   - Create a Place (P)")
    print("   - Create a Transition (T)")
    print("   - Create another Place (P)")
    print("   - Connect: P → T → P")
    print("3. Right-click the transition → 'Add to Analysis'")
    print("4. Go to 'Dynamic Analyses' panel (right side)")
    print("5. Click 'Simulate' button")
    print("\nExpected Result: Plot should appear in the matplotlib canvas")
    
    return wait_for_confirmation()


def test_file_new():
    """Test 2: File → New."""
    print_test_section(2, "File → New")
    
    print("Instructions:")
    print("1. With app still running from Test 1...")
    print("2. Go to File → New (or Ctrl+N)")
    print("3. A new canvas tab should appear")
    print("4. On this NEW canvas:")
    print("   - Create P-T-P structure")
    print("   - Right-click transition → 'Add to Analysis'")
    print("   - Go to Dynamic Analyses panel")
    print("   - Click 'Simulate'")
    print("\nExpected Result: Plot should appear (this scenario already worked)")
    
    return wait_for_confirmation()


def test_file_open():
    """Test 3: File → Open."""
    print_test_section(3, "File → Open")
    
    print("Instructions:")
    print("1. First, save the current work: File → Save As → test_model.shypn")
    print("2. Close the application completely")
    print("3. Re-launch: python3 src/shypn.py")
    print("4. Go to File → Open")
    print("5. Select 'test_model.shypn'")
    print("6. The saved model should load in a canvas")
    print("7. If no transitions in analysis list:")
    print("   - Right-click a transition → 'Add to Analysis'")
    print("8. Go to Dynamic Analyses panel")
    print("9. Click 'Simulate'")
    print("\nExpected Result: Plot should appear")
    
    return wait_for_confirmation()


def test_file_explorer_double_click():
    """Test 4: Double-click from File Explorer."""
    print_test_section(4, "Double-Click File in File Explorer Panel")
    
    print("Instructions:")
    print("1. With app running (with saved test_model.shypn)...")
    print("2. Look at the LEFT panel → 'File Explorer' tab")
    print("3. Navigate to where test_model.shypn is saved")
    print("4. DOUBLE-CLICK on test_model.shypn in the file list")
    print("5. The model should open in a new canvas tab")
    print("6. Right-click a transition → 'Add to Analysis'")
    print("7. Go to Dynamic Analyses panel")
    print("8. Click 'Simulate'")
    print("\nExpected Result: Plot should appear")
    
    return wait_for_confirmation()


def test_import_sbml():
    """Test 5: Import SBML."""
    print_test_section(5, "Import from SBML")
    
    print("Instructions:")
    print("1. Go to File → Import → From SBML")
    print("2. Select 'BioModels' as source")
    print("3. Enter a model ID (e.g., 'BIOMD0000000001')")
    print("4. Click 'Fetch and Import'")
    print("5. The SBML model should load in a new canvas")
    print("6. Right-click any transition → 'Add to Analysis'")
    print("7. Go to Dynamic Analyses panel")
    print("8. Click 'Simulate'")
    print("\nExpected Result: Plot should appear")
    
    return wait_for_confirmation()


def test_import_kegg():
    """Test 6: Import KEGG."""
    print_test_section(6, "Import from KEGG")
    
    print("Instructions:")
    print("1. Go to File → Import → From KEGG")
    print("2. Enter organism code: 'hsa' (human)")
    print("3. Enter pathway ID: '04010' (MAPK signaling)")
    print("4. Click 'Import'")
    print("5. The KEGG pathway should load in a new canvas")
    print("6. Right-click any transition → 'Add to Analysis'")
    print("7. Go to Dynamic Analyses panel")
    print("8. Click 'Simulate'")
    print("\nExpected Result: Plot should appear")
    
    return wait_for_confirmation()


def test_tab_switching():
    """Test 7: Tab switching between multiple canvases."""
    print_test_section(7, "Tab Switching - Multiple Canvases")
    
    print("Instructions:")
    print("1. You should now have multiple canvas tabs open")
    print("2. In EACH tab:")
    print("   - Make sure at least one transition is in the analysis list")
    print("   - (Add one if needed: right-click → 'Add to Analysis')")
    print("3. Go to Dynamic Analyses panel")
    print("4. SWITCH between tabs (click different canvas tabs)")
    print("5. After each tab switch:")
    print("   - The analysis list should update to show that tab's items")
    print("   - Click 'Simulate'")
    print("   - Plot should appear for that tab's data")
    print("\nExpected Result: Each tab maintains its own data_collector")
    print("                  Plot updates correctly when switching tabs")
    
    return wait_for_confirmation()


def main():
    """Run the manual test script."""
    print_header("CANVAS WIRING - MANUAL TEST SUITE")
    
    print("This script will guide you through testing all canvas creation scenarios.")
    print("Each test verifies that the Dynamic Analyses panel data_collector is")
    print("properly wired and plotting works correctly.")
    print("\nPress Enter to begin...")
    input()
    
    results = {}
    
    # Run all tests
    results['startup'] = test_startup_canvas()
    results['file_new'] = test_file_new()
    results['file_open'] = test_file_open()
    results['file_explorer'] = test_file_explorer_double_click()
    results['import_sbml'] = test_import_sbml()
    results['import_kegg'] = test_import_kegg()
    results['tab_switching'] = test_tab_switching()
    
    # Print summary
    print_header("TEST RESULTS SUMMARY")
    
    passed = sum(1 for r in results.values() if r == "PASS")
    failed = sum(1 for r in results.values() if r == "FAIL")
    skipped = sum(1 for r in results.values() if r == "SKIP")
    
    for test_name, result in results.items():
        status = "✅" if result == "PASS" else "❌" if result == "FAIL" else "⚠️ "
        print(f"{status} {test_name.replace('_', ' ').title()}: {result}")
    
    print(f"\n{'─'*70}")
    print(f"Total: {len(results)} tests")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Skipped: {skipped} ⚠️")
    print(f"{'─'*70}\n")
    
    if failed > 0:
        print("⚠️  Some tests failed. Please review the wiring implementation.")
        return 1
    elif passed == len(results):
        print("🎉 All tests passed! Canvas wiring is working correctly.")
        return 0
    else:
        print("⚠️  Some tests were skipped. Run again to complete testing.")
        return 0


if __name__ == '__main__':
    sys.exit(main())
