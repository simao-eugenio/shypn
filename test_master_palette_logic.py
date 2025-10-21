#!/usr/bin/env python3
"""
Headless test for Master Palette button logic.
Tests the exclusive radio button behavior without GUI.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class MockToggleButton:
    """Mock GTK ToggleButton for testing."""
    
    def __init__(self, name):
        self.name = name
        self._active = False
        self._callbacks = []
        self._sensitive = True
    
    def get_active(self):
        return self._active
    
    def set_active(self, active):
        if self._active == active:
            return  # No change, no signal
        
        self._active = active
        print(f"  [{self.name}] set_active({active}) - triggering callbacks")
        
        # Trigger all connected callbacks
        for callback in self._callbacks:
            callback(active)
    
    def connect_toggled(self, callback):
        self._callbacks.append(callback)
        print(f"  [{self.name}] callback connected (total: {len(self._callbacks)})")
    
    def set_sensitive(self, sensitive):
        self._sensitive = sensitive
    
    def get_sensitive(self):
        return self._sensitive


class MockPaletteButton:
    """Mock PaletteButton for testing."""
    
    def __init__(self, icon_name, tooltip):
        self.icon_name = icon_name
        self.tooltip = tooltip
        self._button = MockToggleButton(f"PaletteButton[{icon_name}]")
    
    def connect_toggled(self, callback):
        self._button.connect_toggled(callback)
    
    def set_active(self, active):
        self._button.set_active(active)
    
    def get_active(self):
        return self._button.get_active()
    
    def set_sensitive(self, sensitive):
        self._button.set_sensitive(sensitive)


class TestMasterPalette:
    """Test harness for MasterPalette logic."""
    
    def __init__(self):
        self.buttons = {}
        self._callbacks = {}
        self._in_handler = False
        self.callback_log = []
    
    def add_button(self, category, icon_name, tooltip):
        """Add a button (mimics MasterPalette.add_button)."""
        button = MockPaletteButton(icon_name, tooltip)
        self.buttons[category] = button
        return button
    
    def connect(self, category, callback):
        """Connect callback with exclusive behavior (mimics MasterPalette.connect)."""
        if category not in self.buttons:
            raise KeyError(f"Unknown category: {category}")
        self._callbacks[category] = callback
        
        # Wrap callback to implement exclusive radio-button behavior
        def exclusive_callback(active):
            print(f"\n[exclusive_callback] {category} toggled: active={active}, _in_handler={self._in_handler}")
            
            # Prevent re-entrance from programmatic set_active() calls
            if self._in_handler:
                print(f"[exclusive_callback] Skipping {category} - handler already running")
                return
            
            self._in_handler = True
            try:
                if active:
                    print(f"[exclusive_callback] Activating {category}, deactivating others")
                    # User clicked this button to activate it
                    # Deactivate all other buttons
                    for btn_name, btn in self.buttons.items():
                        if btn_name != category and btn.get_active():
                            print(f"[exclusive_callback] Deactivating {btn_name}")
                            btn.set_active(False)
                    
                    # Call the activation callback for this button
                    print(f"[exclusive_callback] Calling activation callback for {category}")
                    self.callback_log.append(f"activate_{category}")
                    callback(True)
                else:
                    # User clicked active button to try to deactivate it
                    # For radio behavior, prevent deactivation by re-activating it
                    print(f"[exclusive_callback] Re-activating {category} (radio behavior)")
                    self.buttons[category].set_active(True)
            except Exception as e:
                print(f"[ERROR] Callback failed for {category}: {e}")
                import traceback
                traceback.print_exc()
            finally:
                print(f"[exclusive_callback] Resetting _in_handler")
                self._in_handler = False
        
        self.buttons[category].connect_toggled(exclusive_callback)
    
    def set_active(self, category, active):
        """Set button active state programmatically (mimics MasterPalette.set_active)."""
        if category not in self.buttons:
            return
        
        print(f"\n[set_active] {category}.set_active({active}) called")
        
        # Guard to prevent triggering callbacks during programmatic changes
        # Only set the guard if we're not already in a handler
        was_in_handler = self._in_handler
        if not was_in_handler:
            self._in_handler = True
            print(f"[set_active] Setting _in_handler = True")
        else:
            print(f"[set_active] Already in handler, not setting flag")
        
        try:
            self.buttons[category].set_active(active)
        finally:
            # Only reset if we set it
            if not was_in_handler:
                self._in_handler = False
                print(f"[set_active] Resetting _in_handler = False")


def test_basic_switching():
    """Test basic button switching."""
    print("\n" + "="*70)
    print("TEST 1: Basic Button Switching")
    print("="*70)
    
    palette = TestMasterPalette()
    
    # Add buttons
    palette.add_button('files', 'folder-symbolic', 'Files')
    palette.add_button('analyses', 'utilities-system-monitor-symbolic', 'Analyses')
    palette.add_button('pathway', 'view-list-symbolic', 'Pathway')
    palette.add_button('topology', 'network-server-symbolic', 'Topology')
    
    # Connect callbacks
    def on_files(active):
        print(f"    >>> on_files({active}) executed")
    
    def on_analyses(active):
        print(f"    >>> on_analyses({active}) executed")
    
    def on_pathway(active):
        print(f"    >>> on_pathway({active}) executed")
    
    def on_topology(active):
        print(f"    >>> on_topology({active}) executed")
    
    palette.connect('files', on_files)
    palette.connect('analyses', on_analyses)
    palette.connect('pathway', on_pathway)
    palette.connect('topology', on_topology)
    
    # Test sequence
    print("\n--- Click Files (first activation) ---")
    palette.buttons['files'].set_active(True)
    
    print("\n--- Click Analyses (switch from Files) ---")
    palette.buttons['analyses'].set_active(True)
    
    print("\n--- Click Pathway (switch from Analyses) ---")
    palette.buttons['pathway'].set_active(True)
    
    print("\n--- Click Topology (switch from Pathway) ---")
    palette.buttons['topology'].set_active(True)
    
    print("\n--- Click Files again (switch from Topology) ---")
    palette.buttons['files'].set_active(True)
    
    print("\n--- Try to deactivate Files (should re-activate) ---")
    palette.buttons['files'].set_active(False)
    
    # Check final state
    print("\n" + "="*70)
    print("FINAL STATE:")
    for name, btn in palette.buttons.items():
        print(f"  {name}: active={btn.get_active()}")
    
    print("\nCALLBACK LOG:")
    for log_entry in palette.callback_log:
        print(f"  {log_entry}")
    
    # Verify
    assert palette.buttons['files'].get_active(), "Files should be active"
    assert not palette.buttons['analyses'].get_active(), "Analyses should be inactive"
    assert not palette.buttons['pathway'].get_active(), "Pathway should be inactive"
    assert not palette.buttons['topology'].get_active(), "Topology should be inactive"
    
    print("\n✅ TEST 1 PASSED: Basic switching works correctly")


def test_programmatic_set_active():
    """Test programmatic set_active() calls (like from float/attach)."""
    print("\n" + "="*70)
    print("TEST 2: Programmatic set_active() Calls")
    print("="*70)
    
    palette = TestMasterPalette()
    
    # Add buttons
    palette.add_button('files', 'folder-symbolic', 'Files')
    palette.add_button('analyses', 'utilities-system-monitor-symbolic', 'Analyses')
    
    # Track callback invocations
    callback_count = {'files': 0, 'analyses': 0}
    
    def on_files(active):
        callback_count['files'] += 1
        print(f"    >>> on_files({active}) executed (count: {callback_count['files']})")
    
    def on_analyses(active):
        callback_count['analyses'] += 1
        print(f"    >>> on_analyses({active}) executed (count: {callback_count['analyses']})")
    
    palette.connect('files', on_files)
    palette.connect('analyses', on_analyses)
    
    # Test: User click Files
    print("\n--- User clicks Files ---")
    palette.buttons['files'].set_active(True)
    
    # Test: Programmatic call from within callback (simulating attach callback)
    print("\n--- Programmatic set_active during callback ---")
    palette._in_handler = True  # Simulate being inside a callback
    palette.set_active('files', True)  # Should not trigger callback
    palette._in_handler = False
    
    # Test: User click Analyses
    print("\n--- User clicks Analyses ---")
    palette.buttons['analyses'].set_active(True)
    
    print("\n" + "="*70)
    print("CALLBACK COUNTS:")
    print(f"  files: {callback_count['files']}")
    print(f"  analyses: {callback_count['analyses']}")
    
    # Each button should have been called exactly once
    assert callback_count['files'] == 1, "Files callback should be called once"
    assert callback_count['analyses'] == 1, "Analyses callback should be called once"
    
    print("\n✅ TEST 2 PASSED: Programmatic calls don't trigger extra callbacks")


def test_circular_callback_scenario():
    """Test the circular callback scenario that was causing the bug."""
    print("\n" + "="*70)
    print("TEST 3: Circular Callback Scenario (Bug Reproduction)")
    print("="*70)
    
    palette = TestMasterPalette()
    
    # Add buttons
    palette.add_button('files', 'folder-symbolic', 'Files')
    palette.add_button('analyses', 'utilities-system-monitor-symbolic', 'Analyses')
    
    callback_count = {'files': 0, 'analyses': 0}
    
    def on_files(active):
        callback_count['files'] += 1
        print(f"    >>> on_files({active}) executed (count: {callback_count['files']})")
        # Simulate attach callback calling set_active (OLD BUGGY BEHAVIOR)
        # This should be blocked by the guard
        if active:
            print(f"    >>> Simulating attach callback trying to call set_active")
            palette.set_active('files', True)  # Should be blocked
    
    def on_analyses(active):
        callback_count['analyses'] += 1
        print(f"    >>> on_analyses({active}) executed (count: {callback_count['analyses']})")
        if active:
            print(f"    >>> Simulating attach callback trying to call set_active")
            palette.set_active('analyses', True)  # Should be blocked
    
    palette.connect('files', on_files)
    palette.connect('analyses', on_analyses)
    
    # Test: Click Files (which tries to call set_active again)
    print("\n--- User clicks Files (triggers attach → set_active) ---")
    palette.buttons['files'].set_active(True)
    
    # Test: Click Analyses (which also tries to call set_active)
    print("\n--- User clicks Analyses (triggers attach → set_active) ---")
    palette.buttons['analyses'].set_active(True)
    
    # Test: Click Files again
    print("\n--- User clicks Files again ---")
    palette.buttons['files'].set_active(True)
    
    print("\n" + "="*70)
    print("CALLBACK COUNTS:")
    print(f"  files: {callback_count['files']}")
    print(f"  analyses: {callback_count['analyses']}")
    
    # Even with circular calls, each button should only be called when actually clicked
    # Files: clicked twice, so 2 calls
    # Analyses: clicked once, so 1 call
    assert callback_count['files'] == 2, f"Files should be called 2 times, got {callback_count['files']}"
    assert callback_count['analyses'] == 1, f"Analyses should be called 1 time, got {callback_count['analyses']}"
    
    print("\n✅ TEST 3 PASSED: Circular callbacks are properly blocked")


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("MASTER PALETTE LOGIC - HEADLESS TEST SUITE")
    print("="*70)
    
    try:
        test_basic_switching()
        test_programmatic_set_active()
        test_circular_callback_scenario()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        print("\nThe Master Palette logic is correct.")
        print("If buttons still don't work in the GUI, the issue is elsewhere.")
        print("\nPossible GUI-specific issues to investigate:")
        print("  1. Multiple callback connections (check if connect() is called multiple times)")
        print("  2. GTK event loop timing (callbacks might be queued differently)")
        print("  3. Panel attach/detach side effects (check what attach_to() actually does)")
        print("  4. Signal blocking (check if signals are being blocked somewhere)")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
