#!/usr/bin/env python3
"""Test multi-canvas ID isolation fix.

This script verifies that each canvas gets its own isolated ID namespace.

Expected behavior:
- Canvas 1: Creates P1, P2, T1
- Canvas 2: Creates P1, P2, T1 (same IDs, different scope)
- Console shows: [ID_SCOPE] Set scope for new canvas: canvas_XXXX

Test procedure:
1. Launch application: python src/shypn.py
2. Create a place on default canvas → should be P1
3. Create File → New to open second canvas
4. Create a place on second canvas → should be P1 (not P2!)
5. Verify console shows ID scope messages
6. Switch between tabs and verify IDs remain correct

Verification:
- Check that both canvases have P1 (isolated namespaces)
- Console log should show different scope names for each canvas
- Tab switching should preserve each canvas's ID state
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.canvas.lifecycle.id_scope_manager import IDScopeManager

def test_id_scope_manager():
    """Test IDScopeManager directly to verify isolation."""
    print("\n" + "="*60)
    print("Testing IDScopeManager directly")
    print("="*60 + "\n")
    
    scope_manager = IDScopeManager()
    
    # Simulate Canvas 1
    print("Canvas 1: Creating objects")
    scope_manager.set_scope("canvas_12345")
    p1_c1 = scope_manager.generate_place_id()
    p2_c1 = scope_manager.generate_place_id()
    t1_c1 = scope_manager.generate_transition_id()
    print(f"  Place 1: {p1_c1}")
    print(f"  Place 2: {p2_c1}")
    print(f"  Transition 1: {t1_c1}")
    
    # Simulate Canvas 2
    print("\nCanvas 2: Creating objects (should start from 1 again)")
    scope_manager.set_scope("canvas_67890")
    p1_c2 = scope_manager.generate_place_id()
    p2_c2 = scope_manager.generate_place_id()
    t1_c2 = scope_manager.generate_transition_id()
    print(f"  Place 1: {p1_c2}")
    print(f"  Place 2: {p2_c2}")
    print(f"  Transition 1: {t1_c2}")
    
    # Switch back to Canvas 1 and create more
    print("\nCanvas 1: Creating more objects (should continue from 3)")
    scope_manager.set_scope("canvas_12345")
    p3_c1 = scope_manager.generate_place_id()
    print(f"  Place 3: {p3_c1}")
    
    # Verify results
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    
    success = True
    
    # Canvas 1 should have P1, P2, P3, T1
    if p1_c1 != "P1":
        print(f"❌ Canvas 1 Place 1 should be P1, got {p1_c1}")
        success = False
    else:
        print(f"✅ Canvas 1 Place 1: {p1_c1}")
        
    if p2_c1 != "P2":
        print(f"❌ Canvas 1 Place 2 should be P2, got {p2_c1}")
        success = False
    else:
        print(f"✅ Canvas 1 Place 2: {p2_c1}")
        
    if p3_c1 != "P3":
        print(f"❌ Canvas 1 Place 3 should be P3, got {p3_c1}")
        success = False
    else:
        print(f"✅ Canvas 1 Place 3: {p3_c1}")
        
    if t1_c1 != "T1":
        print(f"❌ Canvas 1 Transition 1 should be T1, got {t1_c1}")
        success = False
    else:
        print(f"✅ Canvas 1 Transition 1: {t1_c1}")
    
    # Canvas 2 should have P1, P2, T1 (isolated)
    if p1_c2 != "P1":
        print(f"❌ Canvas 2 Place 1 should be P1, got {p1_c2}")
        success = False
    else:
        print(f"✅ Canvas 2 Place 1: {p1_c2} (isolated from Canvas 1)")
        
    if p2_c2 != "P2":
        print(f"❌ Canvas 2 Place 2 should be P2, got {p2_c2}")
        success = False
    else:
        print(f"✅ Canvas 2 Place 2: {p2_c2} (isolated from Canvas 1)")
        
    if t1_c2 != "T1":
        print(f"❌ Canvas 2 Transition 1 should be T1, got {t1_c2}")
        success = False
    else:
        print(f"✅ Canvas 2 Transition 1: {t1_c2} (isolated from Canvas 1)")
    
    # Show internal state
    print("\n" + "="*60)
    print("INTERNAL STATE")
    print("="*60)
    print(f"Scopes: {scope_manager._scopes}")
    
    if success:
        print("\n✅ ALL TESTS PASSED - ID isolation working correctly!")
    else:
        print("\n❌ SOME TESTS FAILED - ID isolation has issues")
    
    return success

def print_manual_test_instructions():
    """Print instructions for manual testing in the GUI."""
    print("\n" + "="*60)
    print("MANUAL GUI TEST INSTRUCTIONS")
    print("="*60 + "\n")
    
    print("1. Launch application:")
    print("   python src/shypn.py")
    print()
    
    print("2. On the default canvas:")
    print("   - Select Place tool (P)")
    print("   - Click on canvas to create a place")
    print("   - Verify ID is 'P1' (check properties or object label)")
    print()
    
    print("3. Create second canvas:")
    print("   - File → New")
    print("   - A new tab should appear")
    print()
    
    print("4. On the second canvas:")
    print("   - Select Place tool (P)")
    print("   - Click on canvas to create a place")
    print("   - **CRITICAL**: ID should be 'P1' (NOT 'P2'!)")
    print("   - If it's 'P2' or higher, the fix didn't work")
    print()
    
    print("5. Verify console output:")
    print("   - Look for messages like:")
    print("     [ID_SCOPE] Set scope for new canvas: canvas_140234567890")
    print("     [ID_SCOPE] Set scope for new canvas: canvas_140234568000")
    print("   - Each canvas should have a different scope ID")
    print()
    
    print("6. Switch between tabs:")
    print("   - Click on first tab")
    print("   - Create another place → should be 'P2' (continuing from P1)")
    print("   - Click on second tab")
    print("   - Create another place → should be 'P2' (continuing from P1 on this canvas)")
    print()
    
    print("7. Expected results:")
    print("   - Canvas 1: P1, P2, ...")
    print("   - Canvas 2: P1, P2, ... (isolated from Canvas 1)")
    print("   - Console shows scope switching messages")
    print()
    
    print("="*60)
    print("If each canvas starts from P1, the fix is working! ✅")
    print("If second canvas continues numbering, the fix needs work. ❌")
    print("="*60 + "\n")

if __name__ == '__main__':
    # Test the scope manager directly
    success = test_id_scope_manager()
    
    # Print manual test instructions
    print_manual_test_instructions()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
