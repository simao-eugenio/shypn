#!/usr/bin/env python3
"""Test rapid master palette button CLICKING to detect race conditions.

This test simulates actual user clicks (not programmatic set_active) to see if:
1. Wrong panels appear (race condition in handler execution)
2. Multiple panels show at once (exclusivity failure)
3. Button states get out of sync with panel visibility

The key difference from set_active() test:
- set_active() sets _in_handler=True BEFORE toggling (safe)
- User click toggles button FIRST, then handler runs (race condition possible)
"""

import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

# Test configuration
RAPID_CLICK_DELAY_MS = 150  # Fast clicking (150ms between clicks)
CLICK_COUNT = 20  # Number of rapid clicks to perform
CATEGORIES = ['files', 'pathways', 'analyses', 'topology']


class RapidClickTest:
    """Test harness for rapid master palette clicking."""
    
    def __init__(self):
        self.click_count = 0
        self.current_category_index = 0
        self.errors = []
        self.warnings = []
        self.master_palette = None
        self.handler_calls = []  # Track handler execution order
        
        # Track state
        self.panel_states = {
            'files': {'button_active': False, 'handler_called': False},
            'pathways': {'button_active': False, 'handler_called': False},
            'analyses': {'button_active': False, 'handler_called': False},
            'topology': {'button_active': False, 'handler_called': False},
        }
        
    def setup_master_palette(self, master_palette):
        """Connect to master palette and track state changes."""
        self.master_palette = master_palette
        
        # Connect to all buttons to track handler calls
        for category in CATEGORIES:
            master_palette.connect(category, lambda active, cat=category: self._on_button_toggled(cat, active))
    
    def _on_button_toggled(self, category, active):
        """Track button toggle events."""
        timestamp = GLib.get_monotonic_time() / 1000  # milliseconds
        
        print(f"[TEST] Handler called: {category} -> {active} (click #{self.click_count})")
        
        # Record handler call
        self.handler_calls.append({
            'timestamp': timestamp,
            'category': category,
            'active': active,
            'click_num': self.click_count
        })
        
        # Update state
        self.panel_states[category]['button_active'] = active
        self.panel_states[category]['handler_called'] = True
        
        # Check for issues
        self._check_handler_integrity()
    
    def _check_handler_integrity(self):
        """Check if handler calls are happening in expected order."""
        # Count active buttons
        active_buttons = [cat for cat in CATEGORIES if self.panel_states[cat]['button_active']]
        
        if len(active_buttons) > 1:
            error = f"EXCLUSIVITY VIOLATION: Multiple buttons active: {active_buttons}"
            print(f"[ERROR] {error}", file=sys.stderr)
            self.errors.append(error)
        elif len(active_buttons) == 0:
            warning = f"No buttons active (might be transitional state)"
            print(f"[WARNING] {warning}", file=sys.stderr)
            self.warnings.append(warning)
    
    def simulate_user_click(self, category):
        """Simulate a user click on a button by triggering its toggle signal.
        
        This is different from set_active() - it simulates the actual GTK signal flow.
        """
        if not self.master_palette:
            return
        
        button = self.master_palette.buttons.get(category)
        if not button:
            return
        
        # Get current state
        current_state = button.get_active()
        new_state = not current_state
        
        print(f"\n[TEST] Simulating click on '{category}' button ({current_state} -> {new_state})")
        
        # Toggle the button (this triggers the 'toggled' signal like a real click)
        button.set_active(new_state)
    
    def do_rapid_click(self):
        """Perform one rapid click on next category."""
        if self.click_count >= CLICK_COUNT:
            self.finish_test()
            return False  # Stop timer
        
        # Get next category
        category = CATEGORIES[self.current_category_index]
        
        self.click_count += 1
        print(f"\n{'='*70}")
        print(f"[TEST] Click #{self.click_count}: Clicking {category} button")
        print(f"{'='*70}")
        
        # Simulate user click (toggle button directly)
        self.simulate_user_click(category)
        
        # Move to next category
        self.current_category_index = (self.current_category_index + 1) % len(CATEGORIES)
        
        return True  # Continue timer
    
    def finish_test(self):
        """Complete test and print results."""
        print("\n" + "="*70)
        print("RAPID CLICK TEST COMPLETE")
        print("="*70)
        print(f"Total clicks performed: {CLICK_COUNT}")
        print(f"Total handler calls: {len(self.handler_calls)}")
        print(f"Errors detected: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")
        
        # Analyze handler call pattern
        print("\nHANDLER CALL ANALYSIS:")
        if len(self.handler_calls) > CLICK_COUNT:
            print(f"  ⚠ More handler calls ({len(self.handler_calls)}) than clicks ({CLICK_COUNT})")
            print(f"    This indicates deactivation handlers are running during exclusivity logic")
        
        # Show handler sequence
        print("\nHANDLER CALL SEQUENCE (last 10):")
        for call in self.handler_calls[-10:]:
            print(f"  {call['category']:10s} -> {call['active']:5} (click #{call['click_num']})")
        
        # Show errors
        if self.errors:
            print("\nERROR SUMMARY:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        else:
            print("\n✓ No exclusivity violations detected!")
        
        # Show warnings
        if self.warnings:
            print("\nWARNING SUMMARY:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        # Final state
        print("\nFINAL BUTTON STATES:")
        for category in CATEGORIES:
            state = self.panel_states[category]
            print(f"  {category:10s}: active={state['button_active']}")
        
        # Wait before exiting
        GLib.timeout_add(2000, Gtk.main_quit)
    
    def start(self):
        """Start rapid clicking test."""
        print("="*70)
        print("STARTING RAPID MASTER PALETTE CLICK TEST")
        print("="*70)
        print(f"Click delay: {RAPID_CLICK_DELAY_MS}ms")
        print(f"Total clicks: {CLICK_COUNT}")
        print(f"Categories: {', '.join(CATEGORIES)}")
        print("="*70 + "\n")
        
        # Start rapid clicking timer
        GLib.timeout_add(RAPID_CLICK_DELAY_MS, self.do_rapid_click)


def main():
    """Run rapid click test on minimal shypn setup."""
    
    # Import shypn modules
    sys.path.insert(0, '/home/simao/projetos/shypn/src')
    from shypn.ui.master_palette import MasterPalette
    
    # Create minimal window
    window = Gtk.Window(title="Rapid Palette Click Test")
    window.set_default_size(500, 150)
    window.connect('destroy', Gtk.main_quit)
    
    # Create master palette
    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    window.add(vbox)
    
    master_palette = MasterPalette()
    vbox.pack_start(master_palette.get_widget(), False, False, 0)
    
    # Create status label
    status_label = Gtk.Label()
    status_label.set_markup("<b>Running rapid click test...</b>\n<small>Watch for exclusivity violations</small>")
    vbox.pack_start(status_label, True, True, 0)
    
    # Setup test
    test = RapidClickTest()
    test.setup_master_palette(master_palette)
    
    # Show window
    window.show_all()
    
    # Start test after UI is ready
    GLib.timeout_add(500, test.start)
    
    # Run GTK main loop
    Gtk.main()
    
    # Return exit code based on errors
    return 1 if test.errors else 0


if __name__ == '__main__':
    sys.exit(main())
