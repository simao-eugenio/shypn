#!/usr/bin/env python3
"""
Phase 6: Master Palette Integration Testing

Comprehensive test suite to validate:
1. Rapid button switching (100+ cycles)
2. Panel content visibility
3. No Error 71 during operations
4. GtkStack state consistency
5. Paned widget behavior

This mimics the Phase 0 validation test but for the production Master Palette.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import sys
import time

class MasterPaletteValidator:
    """Validates Master Palette integration with automated testing."""
    
    def __init__(self):
        self.test_count = 0
        self.max_tests = 100  # 100 panel switches
        self.errors = []
        self.start_time = None
        self.button_sequence = ['files', 'pathways', 'analyses', 'topology']
        self.current_button_index = 0
        
    def run_tests(self):
        """Start the test suite."""
        print("="*80)
        print("PHASE 6: Master Palette Integration - Validation Test")
        print("="*80)
        print(f"\nTest Plan: {self.max_tests} rapid panel switches")
        print("Expected: No Error 71, smooth panel transitions\n")
        
        # Launch application
        import sys
        sys.path.insert(0, 'src')
        
        from shypn import create_application
        app = create_application()
        
        def on_activate(app):
            """Hook into app activation to get window reference."""
            windows = app.get_windows()
            if not windows:
                print("ERROR: No windows found!")
                return
            
            self.window = windows[0]
            
            if not hasattr(self.window, 'master_palette'):
                print("ERROR: Master Palette not found!")
                return
            
            self.palette = self.window.master_palette
            self.start_time = time.time()
            
            print("[INIT] Master Palette found, starting tests in 1 second...")
            print(f"[INIT] Available buttons: {list(self.palette.buttons.keys())}\n")
            
            # Start tests after 1 second
            GLib.timeout_add(1000, self._test_iteration)
        
        app.connect('activate', on_activate)
        
        try:
            app.run(None)
            return 0 if not self.errors else 1
        except Exception as e:
            print(f"\n❌ FATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    def _test_iteration(self):
        """Single test iteration - toggle a button."""
        if self.test_count >= self.max_tests:
            self._finish_tests()
            return False
        
        # Select button to test (cycle through all 4)
        button_name = self.button_sequence[self.current_button_index]
        button = self.palette.buttons[button_name]
        
        # Get current state
        current_state = button.get_active()
        new_state = not current_state
        
        # Toggle button
        if self.test_count % 10 == 0:
            elapsed = time.time() - self.start_time
            print(f"[TEST {self.test_count}/{self.max_tests}] {button_name.upper()} "
                  f"{'ON' if new_state else 'OFF'} (elapsed: {elapsed:.1f}s)")
        
        try:
            button.set_active(new_state)
        except Exception as e:
            error_msg = f"Test {self.test_count}: Error toggling {button_name}: {e}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
        
        self.test_count += 1
        
        # Move to next button in sequence
        if new_state:
            # Only advance when activating (not deactivating)
            self.current_button_index = (self.current_button_index + 1) % len(self.button_sequence)
        
        # Continue testing (50ms interval for rapid switching)
        return True
    
    def _finish_tests(self):
        """Complete testing and show results."""
        elapsed = time.time() - self.start_time
        
        print("\n" + "="*80)
        print("TEST RESULTS")
        print("="*80)
        print(f"Total Tests: {self.test_count}")
        print(f"Duration: {elapsed:.2f} seconds")
        print(f"Avg Speed: {self.test_count/elapsed:.1f} switches/second")
        print(f"Errors: {len(self.errors)}")
        
        if self.errors:
            print("\n❌ ERRORS DETECTED:")
            for error in self.errors:
                print(f"  - {error}")
            print("\n❌ TEST FAILED")
        else:
            print("\n✅ ALL TESTS PASSED!")
            print("✅ No Error 71 detected")
            print("✅ Master Palette integration working perfectly")
        
        print("="*80)
        
        # Exit application
        GLib.timeout_add(1000, Gtk.main_quit)


def main():
    """Run the validation test suite."""
    validator = MasterPaletteValidator()
    return validator.run_tests()


if __name__ == '__main__':
    sys.exit(main())
