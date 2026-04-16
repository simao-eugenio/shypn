#!/usr/bin/env python3
"""Test rapid master palette button switching to detect race conditions.

This test rapidly toggles master palette buttons to see if:
1. Wrong panels appear (race condition in handler execution)
2. Multiple panels show at once (exclusivity failure)
3. Button states get out of sync with panel visibility
"""

import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

# Test configuration
RAPID_SWITCH_DELAY_MS = 100  # Very fast switching (100ms between clicks)
SWITCH_COUNT = 20  # Number of rapid switches to perform
CATEGORIES = ['files', 'pathways', 'analyses', 'topology']


class RapidSwitchTest:
    """Test harness for rapid master palette switching."""
    
    def __init__(self):
        self.switch_count = 0
        self.current_category_index = 0
        self.errors = []
        self.master_palette = None
        self.panel_states = {
            'files': {'expected': False, 'actual_button': False, 'actual_panel': False},
            'pathways': {'expected': False, 'actual_button': False, 'actual_panel': False},
            'analyses': {'expected': False, 'actual_button': False, 'actual_panel': False},
            'topology': {'expected': False, 'actual_button': False, 'actual_panel': False},
        }
        
    def setup_master_palette(self, master_palette):
        """Connect to master palette and track state changes."""
        self.master_palette = master_palette
        
        # Connect to all buttons to track actual state
        for category in CATEGORIES:
            master_palette.connect(category, lambda active, cat=category: self._on_button_toggled(cat, active))
    
    def _on_button_toggled(self, category, active):
        """Track button toggle events."""
        print(f"[TEST] Button toggled: {category} -> {active}")
        self.panel_states[category]['actual_button'] = active
        
        # Check if state matches expectation
        expected = self.panel_states[category]['expected']
        if active != expected:
            error = f"Button state mismatch: {category} expected={expected} actual={active}"
            print(f"[ERROR] {error}", file=sys.stderr)
            self.errors.append(error)
    
    def verify_exclusivity(self):
        """Verify only one button is active at a time."""
        active_buttons = [cat for cat in CATEGORIES if self.panel_states[cat]['actual_button']]
        
        if len(active_buttons) > 1:
            error = f"Multiple buttons active: {active_buttons}"
            print(f"[ERROR] {error}", file=sys.stderr)
            self.errors.append(error)
            return False
        
        return True
    
    def do_rapid_switch(self):
        """Perform one rapid switch to next category."""
        if self.switch_count >= SWITCH_COUNT:
            self.finish_test()
            return False  # Stop timer
        
        # Get next category
        category = CATEGORIES[self.current_category_index]
        
        print(f"\n[TEST] Switch #{self.switch_count + 1}: Activating {category}")
        
        # Update expected states (only this category should be active)
        for cat in CATEGORIES:
            self.panel_states[cat]['expected'] = (cat == category)
        
        # Activate button programmatically (simulates user click)
        if self.master_palette:
            self.master_palette.set_active(category, True)
        
        # Verify exclusivity after a short delay (let handlers run)
        GLib.timeout_add(50, self.verify_exclusivity)
        
        # Move to next category
        self.current_category_index = (self.current_category_index + 1) % len(CATEGORIES)
        self.switch_count += 1
        
        return True  # Continue timer
    
    def finish_test(self):
        """Complete test and print results."""
        print("\n" + "="*70)
        print("RAPID SWITCH TEST COMPLETE")
        print("="*70)
        print(f"Total switches performed: {SWITCH_COUNT}")
        print(f"Errors detected: {len(self.errors)}")
        
        if self.errors:
            print("\nERROR SUMMARY:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        else:
            print("\n✓ All switches completed successfully!")
            print("✓ No race conditions detected")
            print("✓ Exclusivity maintained throughout test")
        
        # Wait a bit before exiting
        GLib.timeout_add(2000, Gtk.main_quit)
    
    def start(self):
        """Start rapid switching test."""
        print("="*70)
        print("STARTING RAPID MASTER PALETTE SWITCH TEST")
        print("="*70)
        print(f"Switch delay: {RAPID_SWITCH_DELAY_MS}ms")
        print(f"Total switches: {SWITCH_COUNT}")
        print(f"Categories: {', '.join(CATEGORIES)}")
        print("="*70 + "\n")
        
        # Start rapid switching timer
        GLib.timeout_add(RAPID_SWITCH_DELAY_MS, self.do_rapid_switch)


def main():
    """Run rapid switch test on minimal shypn setup."""
    
    # Import shypn modules
    sys.path.insert(0, '/home/simao/projetos/shypn/src')
    from shypn.ui.master_palette import MasterPalette
    
    # Create minimal window
    window = Gtk.Window(title="Rapid Palette Switch Test")
    window.set_default_size(400, 100)
    window.connect('destroy', Gtk.main_quit)
    
    # Create master palette
    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    window.add(vbox)
    
    master_palette = MasterPalette()
    vbox.pack_start(master_palette.get_widget(), False, False, 0)
    
    # Create status label
    status_label = Gtk.Label()
    status_label.set_markup("<b>Running rapid switch test...</b>")
    vbox.pack_start(status_label, True, True, 0)
    
    # Setup test
    test = RapidSwitchTest()
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
