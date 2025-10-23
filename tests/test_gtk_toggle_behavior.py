#!/usr/bin/env python3
"""
Test GTK ToggleButton behavior to understand signal firing.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

def test_toggle_button_signals():
    """Test when GTK ToggleButton fires 'toggled' signal."""
    print("="*70)
    print("GTK ToggleButton Signal Behavior Test")
    print("="*70)
    
    button = Gtk.ToggleButton(label="Test")
    
    call_count = [0]
    
    def on_toggled(widget):
        call_count[0] += 1
        active = widget.get_active()
        print(f"  Callback #{call_count[0]}: toggled signal fired, active={active}")
    
    button.connect('toggled', on_toggled)
    
    print("\n1. set_active(True) when already False:")
    button.set_active(True)
    
    print("\n2. set_active(True) when already True (no change):")
    button.set_active(True)
    
    print("\n3. set_active(False) when True:")
    button.set_active(False)
    
    print("\n4. set_active(False) when already False (no change):")
    button.set_active(False)
    
    print("\n5. set_active(True) again:")
    button.set_active(True)
    
    print(f"\n{'='*70}")
    print(f"Total callbacks fired: {call_count[0]}")
    print(f"Expected: 3 (changes only)")
    
    if call_count[0] == 3:
        print("✅ PASS: Signal only fires on state changes")
    else:
        print("❌ FAIL: Signal fires even when state doesn't change")
    
    return call_count[0] == 3


def test_multiple_callbacks():
    """Test multiple callbacks on same button."""
    print("\n" + "="*70)
    print("Multiple Callbacks Test")
    print("="*70)
    
    button = Gtk.ToggleButton(label="Test")
    
    call_log = []
    
    def callback1(widget):
        active = widget.get_active()
        call_log.append(f"callback1({active})")
        print(f"  callback1 called: active={active}")
    
    def callback2(widget):
        active = widget.get_active()
        call_log.append(f"callback2({active})")
        print(f"  callback2 called: active={active}")
    
    button.connect('toggled', callback1)
    button.connect('toggled', callback2)
    
    print("\nset_active(True):")
    button.set_active(True)
    
    print("\nset_active(False):")
    button.set_active(False)
    
    print(f"\n{'='*70}")
    print("Call log:")
    for call in call_log:
        print(f"  {call}")
    
    expected = [
        'callback1(True)', 'callback2(True)',
        'callback1(False)', 'callback2(False)'
    ]
    
    if call_log == expected:
        print("✅ PASS: Both callbacks fired in order")
        return True
    else:
        print("❌ FAIL: Unexpected callback order")
        return False


def test_callback_during_callback():
    """Test calling set_active() from within a callback."""
    print("\n" + "="*70)
    print("Callback During Callback Test (Recursion)")
    print("="*70)
    
    button = Gtk.ToggleButton(label="Test")
    
    call_count = [0]
    recursion_depth = [0]
    max_depth = [0]
    
    def on_toggled(widget):
        recursion_depth[0] += 1
        max_depth[0] = max(max_depth[0], recursion_depth[0])
        
        call_count[0] += 1
        active = widget.get_active()
        indent = "  " * recursion_depth[0]
        print(f"{indent}Callback #{call_count[0]}: depth={recursion_depth[0]}, active={active}")
        
        # Try to change state from within callback (should cause recursion if not guarded)
        if call_count[0] <= 2:  # Prevent infinite recursion
            if active:
                print(f"{indent}  → Trying set_active(False) from within callback")
                widget.set_active(False)
            else:
                print(f"{indent}  → Trying set_active(True) from within callback")
                widget.set_active(True)
        
        recursion_depth[0] -= 1
    
    button.connect('toggled', on_toggled)
    
    print("\nInitial set_active(True):")
    button.set_active(True)
    
    print(f"\n{'='*70}")
    print(f"Total callbacks: {call_count[0]}")
    print(f"Max recursion depth: {max_depth[0]}")
    
    if max_depth[0] > 1:
        print("⚠️  WARNING: GTK allows recursive callback invocation!")
        print("    This is why we need guard flags in MasterPalette")
        return True
    else:
        print("✅ GTK prevents recursive callback invocation")
        return True


def main():
    print("\nGTK ToggleButton Behavior Analysis")
    print("="*70)
    
    test1 = test_toggle_button_signals()
    test2 = test_multiple_callbacks()
    test3 = test_callback_during_callback()
    
    print("\n" + "="*70)
    if test1 and test2 and test3:
        print("✅ ALL TESTS PASSED")
        print("\nKey Findings:")
        print("  1. GTK only fires 'toggled' on actual state changes")
        print("  2. Multiple callbacks are supported and fire in order")
        print("  3. Recursive set_active() calls ARE ALLOWED (need guards!)")
    else:
        print("❌ SOME TESTS FAILED")
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
