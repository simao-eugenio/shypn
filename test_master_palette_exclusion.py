#!/usr/bin/env python3
"""Test Master Palette exclusive button behavior.

This test verifies that:
1. Only one button can be active at a time
2. Clicking a button deactivates all others
3. Visual styling reflects active state clearly
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.ui.master_palette import MasterPalette


class ExclusionTest:
    """Test exclusive button behavior."""
    
    def __init__(self):
        self.palette = None
        self.window = None
        self.status_label = None
        self.test_results = []
    
    def run(self):
        """Run the test application."""
        # Create window
        self.window = Gtk.Window(title="Master Palette Exclusion Test")
        self.window.set_default_size(600, 400)
        self.window.connect('destroy', Gtk.main_quit)
        
        # Create main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        
        # Create palette
        self.palette = MasterPalette()
        palette_widget = self.palette.get_widget()
        main_box.pack_start(palette_widget, False, False, 0)
        
        # Create status panel
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        title_label = Gtk.Label()
        title_label.set_markup("<b>Exclusive Button Test</b>")
        status_box.pack_start(title_label, False, False, 0)
        
        instructions = Gtk.Label()
        instructions.set_text(
            "Test Instructions:\n"
            "1. Click any button - it should turn ORANGE\n"
            "2. Click another button - previous should turn GREY\n"
            "3. Only ONE button should be ORANGE at a time\n"
            "4. Hover shows GREEN highlight\n\n"
            "Colors:\n"
            "  GREY = inactive\n"
            "  GREEN = hover\n"
            "  ORANGE = active (only one at a time)"
        )
        instructions.set_justify(Gtk.Justification.LEFT)
        status_box.pack_start(instructions, False, False, 0)
        
        self.status_label = Gtk.Label()
        self.status_label.set_markup("<b>Status:</b> Ready")
        self.status_label.set_justify(Gtk.Justification.LEFT)
        self.status_label.set_line_wrap(True)
        status_box.pack_start(self.status_label, False, False, 0)
        
        # Add automated test button
        test_button = Gtk.Button(label="Run Automated Test")
        test_button.connect('clicked', self.run_automated_test)
        status_box.pack_start(test_button, False, False, 0)
        
        main_box.pack_start(status_box, True, True, 0)
        
        self.window.add(main_box)
        
        # Connect palette buttons with exclusion logic
        self.setup_exclusion_handlers()
        
        # Show window
        self.window.show_all()
        
        print("=" * 60)
        print("MASTER PALETTE EXCLUSION TEST")
        print("=" * 60)
        print("Click buttons to test exclusive behavior")
        print("Only one button should be active (ORANGE) at a time")
        print("=" * 60)
        
        Gtk.main()
    
    def setup_exclusion_handlers(self):
        """Setup exclusive toggle handlers for all buttons."""
        buttons = ['files', 'pathways', 'analyses', 'topology', 'report']
        
        for button_name in buttons:
            self.palette.connect(button_name, lambda active, name=button_name: 
                self.on_button_toggle(name, active))
    
    def on_button_toggle(self, button_name, is_active):
        """Handle button toggle with exclusive logic."""
        if is_active:
            # Deactivate all other buttons (exclusive mode)
            all_buttons = ['files', 'pathways', 'analyses', 'topology', 'report']
            for other in all_buttons:
                if other != button_name:
                    self.palette.set_active(other, False)
            
            # Update status
            status_text = f"<b>Active:</b> {button_name.upper()}"
            
            # Check if others are really deactivated
            active_count = sum(1 for btn in all_buttons if self.palette.is_active(btn))
            if active_count == 1:
                status_text += "\n<span foreground='green'>✓ Exclusion working correctly</span>"
            else:
                status_text += f"\n<span foreground='red'>✗ ERROR: {active_count} buttons active!</span>"
            
            self.status_label.set_markup(status_text)
        else:
            self.status_label.set_markup("<b>Status:</b> No button active")
    
    def run_automated_test(self, button):
        """Run automated test sequence."""
        print("\n" + "=" * 60)
        print("RUNNING AUTOMATED TEST")
        print("=" * 60)
        
        self.test_results = []
        self.test_step = 0
        
        # Start test sequence
        GLib.timeout_add(500, self.next_test_step)
    
    def next_test_step(self):
        """Execute next test step."""
        buttons = ['files', 'pathways', 'analyses', 'topology', 'report']
        
        if self.test_step < len(buttons):
            button_name = buttons[self.test_step]
            print(f"\nTest {self.test_step + 1}: Activating {button_name}...")
            
            # Activate button
            self.palette.set_active(button_name, True)
            
            # Check exclusion
            active_buttons = [btn for btn in buttons if self.palette.is_active(btn)]
            
            if len(active_buttons) == 1 and active_buttons[0] == button_name:
                print(f"  ✓ SUCCESS: Only {button_name} is active")
                self.test_results.append(True)
            else:
                print(f"  ✗ FAILED: Active buttons: {active_buttons}")
                self.test_results.append(False)
            
            self.test_step += 1
            return True  # Continue
        else:
            # Test complete
            self.show_test_results()
            return False  # Stop
    
    def show_test_results(self):
        """Show final test results."""
        print("\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)
        
        passed = sum(self.test_results)
        total = len(self.test_results)
        
        print(f"Passed: {passed}/{total}")
        
        if passed == total:
            print("✓ ALL TESTS PASSED - Exclusion working correctly!")
            result_text = f"<b>Automated Test Result:</b>\n<span foreground='green'>✓ ALL {total} TESTS PASSED</span>\nExclusion logic is working correctly!"
        else:
            print(f"✗ SOME TESTS FAILED - Check console for details")
            result_text = f"<b>Automated Test Result:</b>\n<span foreground='red'>✗ {total - passed} TESTS FAILED</span>\nSee console for details"
        
        print("=" * 60)
        
        self.status_label.set_markup(result_text)


if __name__ == '__main__':
    test = ExclusionTest()
    test.run()
