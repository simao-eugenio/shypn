#!/usr/bin/env python3
"""
Settings Sub-Palette Testbed with Real SwissKnife Palette

Uses the production SwissKnife palette and adds settings panel functionality
to test the new time scale controls before production integration.

Run:
    python -m shypn.dev.settings_sub_palette_testbed.test_app_with_swissknife
"""

import os
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import cairo

# Add parent directories to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))

# Fix import path issue in SwissKnife without modifying production code
# This monkey-patches the module path temporarily for the testbed
import shypn.ui
import shypn.helpers.swissknife_tool_registry
sys.modules['shypn.ui.swissknife_tool_registry'] = shypn.helpers.swissknife_tool_registry

from shypn.helpers.swissknife_palette import SwissKnifePalette
from shypn.dev.settings_sub_palette_testbed.mock_simulation import MockSimulationController


class ExtendedSwissKnifeTestApp(Gtk.Window):
    """Test application using real SwissKnife palette with settings extension."""
    
    def __init__(self):
        super().__init__(title="SwissKnife + Settings Testbed")
        
        # Window setup
        self.set_default_size(1000, 700)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('destroy', Gtk.main_quit)
        
        # Apply CSS styling for settings panel
        self._apply_css_styling()
        
        # Create mock model (minimal for testing)
        self.model = self._create_mock_model()
        
        # Create mock simulation controller
        self.simulation = MockSimulationController()
        
        # Create main layout
        self._setup_ui()
        
        print("=" * 70)
        print("SWISSKNIFE + SETTINGS TESTBED")
        print("=" * 70)
        print()
    
    def _create_mock_model(self):
        """Create a minimal mock model for SwissKnife palette."""
        class MockModel:
            def __init__(self):
                self.simulation_controller = None
        
        return MockModel()
    
    def _apply_css_styling(self):
        """Apply CSS styling for the settings panel."""
        css_provider = Gtk.CssProvider()
        css = b"""
        /* ============================================== */
        /* Settings Panel Styling - Dark Blue-Gray Theme */
        /* ============================================== */
        
        .settings-panel-frame {
            background-color: #3e5266;
            border-radius: 8px;
            border: 1px solid #1a252f;
        }
        
        .settings-panel {
            background-color: transparent;
            color: #ecf0f1;
        }
        
        .settings-header {
            font-size: 14px;
            font-weight: bold;
            color: #ecf0f1;
            padding: 4px 0;
        }
        
        .settings-section-label {
            font-size: 10px;
            font-weight: bold;
            color: #95a5a6;
            letter-spacing: 0.5px;
            padding: 2px 0;
        }
        
        .settings-label-small {
            font-size: 11px;
            color: #bdc3c7;
        }
        
        .settings-unit {
            font-size: 11px;
            color: #95a5a6;
            font-weight: bold;
        }
        
        /* Radio buttons */
        .settings-radio {
            color: #ecf0f1;
            padding: 4px 8px;
        }
        
        .settings-radio:checked {
            color: #3498db;
        }
        
        /* Entry fields */
        .settings-entry-small {
            background-color: #2c3e50;
            color: #ecf0f1;
            border: 1px solid #34495e;
            border-radius: 4px;
            padding: 4px 6px;
            min-height: 28px;
        }
        
        /* Speed preset buttons */
        .speed-preset-button {
            background-color: #34495e;
            color: #bdc3c7;
            border: 1px solid #1a252f;
            border-radius: 4px;
            min-height: 36px;
            padding: 6px 8px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .speed-preset-button:hover {
            background-color: #3e5266;
            color: #ecf0f1;
        }
        
        .speed-preset-button:checked {
            background-color: #3498db;
            color: white;
            border-color: #2980b9;
        }
        
        /* Spin button */
        .settings-spin {
            background-color: #2c3e50;
            color: #ecf0f1;
            border: 1px solid #34495e;
            border-radius: 4px;
            padding: 4px 6px;
            min-height: 32px;
        }
        
        /* Combo box */
        .settings-combo {
            background-color: #2c3e50;
            color: #ecf0f1;
            border: 1px solid #34495e;
            border-radius: 4px;
            padding: 6px 8px;
            min-height: 36px;
        }
        
        /* Action buttons */
        .settings-button {
            background-color: #34495e;
            color: #bdc3c7;
            border: 1px solid #1a252f;
            border-radius: 4px;
            min-height: 40px;
            padding: 8px 12px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .settings-button:hover {
            background-color: #3e5266;
            color: #ecf0f1;
        }
        
        .settings-button-primary {
            background-color: #3498db;
            color: white;
            border-color: #2980b9;
        }
        
        .settings-button-primary:hover {
            background-color: #52a8e0;
        }
        """
        
        css_provider.load_from_data(css)
        
        screen = self.get_screen()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(
            screen,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def _setup_ui(self):
        """Setup the test application UI."""
        # Create overlay to mimic production canvas structure
        overlay = Gtk.Overlay()
        self.add(overlay)
        
        # Add a drawing area as fake canvas background
        drawing_area = Gtk.DrawingArea()
        drawing_area.connect('draw', self._on_draw_background)
        overlay.add(drawing_area)
        
        # Create status label for dynamic feedback (hidden by default, updated on interactions)
        status_label = Gtk.Label()
        status_label.set_halign(Gtk.Align.CENTER)
        status_label.set_valign(Gtk.Align.START)
        status_label.set_margin_top(20)
        status_label.set_no_show_all(True)  # Don't show by default
        self.status_label = status_label
        overlay.add_overlay(status_label)
        
        # Create REAL SwissKnife palette in EDIT mode (which includes all categories: edit, simulate, layout)
        # Note: 'simulate' mode returns empty categories in tool registry - this is a production issue
        print("Creating SwissKnife palette...")
        self.swissknife = SwissKnifePalette(mode='edit', model=self.model)
        
        # Connect to SwissKnife signals
        self.swissknife.connect('category-selected', self._on_category_selected)
        self.swissknife.connect('mode-change-requested', self._on_mode_change)
        self.swissknife.connect('simulation-step-executed', self._on_simulation_step)
        
        # Connect to SwissKnife signals
        self.swissknife.connect('category-selected', self._on_category_selected)
        self.swissknife.connect('mode-change-requested', self._on_mode_change)
        self.swissknife.connect('simulation-step-executed', self._on_simulation_step)
        
        # Get SwissKnife widget and position it at bottom center
        swissknife_widget = self.swissknife.get_widget()
        print(f"SwissKnife widget: {swissknife_widget}")
        print(f"SwissKnife visible: {swissknife_widget.get_visible()}")
        
        # Make sure the widget is visible
        swissknife_widget.show_all()
        
        # Create a box to position the SwissKnife at bottom center
        swissknife_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        swissknife_container.set_halign(Gtk.Align.CENTER)
        swissknife_container.set_valign(Gtk.Align.END)
        swissknife_container.set_margin_bottom(20)
        swissknife_container.pack_start(swissknife_widget, False, False, 0)
        
        overlay.add_overlay(swissknife_container)
        
        # Debug: Print category buttons
        print(f"Category buttons: {list(self.swissknife.category_buttons.keys())}")
        print(f"Widget palettes: {list(self.swissknife.widget_palette_instances.keys())}")
        
        # Initially show the simulate category
        GLib.idle_add(self._show_initial_category)
        
        # Add settings panel functionality
        GLib.idle_add(self._setup_settings_panel)
        
        self.show_all()
    
    def _on_draw_background(self, widget, cr):
        """Draw fake canvas background."""
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        
        # Draw gradient background
        pattern = cairo.LinearGradient(0, 0, 0, height)
        pattern.add_color_stop_rgb(0, 0.95, 0.95, 0.97)
        pattern.add_color_stop_rgb(1, 0.85, 0.85, 0.90)
        cr.set_source(pattern)
        cr.rectangle(0, 0, width, height)
        cr.fill()
        
        # Draw grid pattern
        cr.set_source_rgba(0.8, 0.8, 0.85, 0.3)
        cr.set_line_width(1)
        
        # Vertical lines
        for x in range(0, width, 50):
            cr.move_to(x, 0)
            cr.line_to(x, height)
            cr.stroke()
        
        # Horizontal lines
        for y in range(0, height, 50):
            cr.move_to(0, y)
            cr.line_to(width, y)
            cr.stroke()
        
        return False
    
    def _show_initial_category(self):
        """Show the simulate category initially."""
        # Simulate clicking the Simulate category button
        if 'simulate' in self.swissknife.category_buttons:
            self.swissknife.category_buttons['simulate'].clicked()
        return False  # Don't repeat
    
    def _setup_settings_panel(self):
        """Setup the settings panel and connect to settings button."""
        print("Setting up settings panel...")
        
        # Get the simulate palette loader instance
        if 'simulate' not in self.swissknife.widget_palette_instances:
            print("ERROR: Simulate palette not found!")
            return False
        
        simulate_loader = self.swissknife.widget_palette_instances['simulate']
        print(f"Simulate loader: {simulate_loader}")
        
        # ⭐ IMPORTANT: Set the simulation controller so buttons become sensitive
        simulate_loader.simulation = self.simulation
        print(f"Connected mock simulation to loader")
        
        # ⭐ Initialize button states to "reset" state (Run✓, Step✓, Stop✗, Reset✗, Settings✓)
        simulate_loader._update_button_states(reset=True)
        print(f"✅ Button states initialized (reset state)")
        

        
        # Get the settings button
        if not hasattr(simulate_loader, 'settings_button'):
            print("ERROR: Settings button not found!")
            return False
        
        settings_button = simulate_loader.settings_button
        print(f"Settings button: {settings_button}")
        
        # IMPORTANT: Block the old settings dialog handler
        # The production code connects settings button to show_simulation_settings_dialog
        # We'll block all existing handlers before connecting our new one
        print("Blocking old settings handler...")
        
        # Block by handler block - simpler approach
        # Save the button for later if we need to unblock
        settings_button.handler_block_by_func(simulate_loader._on_settings_clicked)
        print("Old handler blocked")
        
        # Load the settings UI from our prototype
        builder = Gtk.Builder()
        ui_path = os.path.join(current_dir, 'settings_palette_prototype.ui')
        
        try:
            builder.add_from_file(ui_path)
            print(f"Loaded settings UI from: {ui_path}")
        except Exception as e:
            print(f"ERROR loading settings UI: {e}")
            return False
        
        # Get the settings revealer from the UI
        settings_revealer = builder.get_object('settings_revealer')
        if not settings_revealer:
            print("ERROR: settings_revealer not found in UI!")
            return False
        
        print(f"Settings revealer: {settings_revealer}")
        
        # Make sure revealer is visible and ready
        settings_revealer.set_visible(True)
        settings_revealer.show_all()
        
        # Get all child widgets and make sure they're visible
        # Note: EventBox was removed from UI, now directly have frame
        settings_frame = builder.get_object('settings_frame')
        settings_container = builder.get_object('settings_container')
        
        if settings_frame:
            settings_frame.show_all()
        if settings_container:
            settings_container.show_all()
        
        print(f"Revealer visible: {settings_revealer.get_visible()}")
        print(f"Revealer reveal-child: {settings_revealer.get_reveal_child()}")
        print(f"Revealer transition-type: {settings_revealer.get_transition_type()}")
        print(f"Revealer transition-duration: {settings_revealer.get_transition_duration()}")
        
        # Set to hidden initially (after it's been shown once to get proper size)
        GLib.idle_add(lambda: settings_revealer.set_reveal_child(False))
        
        # Get speed preset buttons for exclusive logic
        speed_0_1x_button = builder.get_object('speed_0_1x_button')
        speed_1x_button = builder.get_object('speed_1x_button')
        speed_10x_button = builder.get_object('speed_10x_button')
        speed_60x_button = builder.get_object('speed_60x_button')
        
        speed_buttons = [speed_0_1x_button, speed_1x_button, speed_10x_button, speed_60x_button]
        
        # Connect exclusive toggle logic for speed buttons
        def make_speed_button_handler(clicked_button, other_buttons):
            def on_speed_button_toggled(button):
                if button.get_active():
                    # Deactivate all other buttons
                    for other in other_buttons:
                        if other != button:
                            other.set_active(False)
                    print(f"Speed button activated: {button.get_label()}")
            return on_speed_button_toggled
        
        for button in speed_buttons:
            if button:
                other_buttons = [b for b in speed_buttons if b != button]
                button.connect('toggled', make_speed_button_handler(button, other_buttons))
        
        # ⭐ ADD SETTINGS AS A NEW SWISSKNIFE ROW (proper architecture)
        # SwissKnife structure:
        #   main_container (VBox)
        #     └── sub_palette_area (VBox) ← Contains all category revealers
        #           ├── edit_revealer
        #           ├── simulate_revealer (Grid inside)
        #           ├── layout_revealer
        #           └── settings_revealer ← WE ADD THIS
        #     └── category_buttons (HBox)
        
        # Get SwissKnife's sub_palette_area where all revealers live
        sub_palette_area = self.swissknife.sub_palette_area
        print(f"[Integration] SwissKnife sub_palette_area: {sub_palette_area}")
        
        # ⭐ DEBUG: Check that simulate_tools_container is properly in SwissKnife
        simulate_tools_container = simulate_loader.simulate_tools_container
        container_parent = simulate_tools_container.get_parent() if simulate_tools_container else None
        print(f"[DEBUG] simulate_tools_container: {simulate_tools_container}")
        print(f"[DEBUG] container parent: {container_parent}")
        print(f"[DEBUG] container parent type: {type(container_parent)}")
        
        if sub_palette_area:
            # ⭐ DEBUG: Check current children in sub_palette_area
            print(f"[DEBUG] sub_palette_area children BEFORE adding settings:")
            for i, child in enumerate(sub_palette_area.get_children()):
                print(f"  [{i}] {child}")
            
            # ⭐ Add settings_revealer at the TOP of the stack (pack_end pushes to top)
            # This makes it appear ABOVE the simulate palette, not between palettes
            # Stack order (bottom to top): category_buttons → simulate → settings
            sub_palette_area.pack_end(settings_revealer, False, False, 0)
            settings_revealer.show()  # Make it visible (but not revealed yet)
            
            print(f"[DEBUG] sub_palette_area children AFTER adding settings:")
            for i, child in enumerate(sub_palette_area.get_children()):
                print(f"  [{i}] {child}")
            
            print("✅ Settings revealer added at TOP of SwissKnife stack (proper architecture)")
        else:
            print(f"❌ ERROR: Could not find SwissKnife sub_palette_area")
            return False
        
        # Helper function to hide settings panel
        def hide_settings_panel():
            """Hide the settings panel with animation."""
            if settings_revealer.get_reveal_child():
                settings_revealer.set_reveal_child(False)
                # Set invisible after animation completes (500ms transition)
                GLib.timeout_add(550, lambda: settings_revealer.set_visible(False))
                print(f"   Settings hidden")
        
        # Connect the settings button to toggle the revealer
        def on_settings_clicked(button):
            is_revealed = settings_revealer.get_reveal_child()
            new_state = not is_revealed
            print(f"⚙️  Settings button clicked!")
            print(f"   Current reveal-child: {is_revealed}")
            print(f"   Setting reveal-child to: {new_state}")
            
            # ⭐ CRITICAL: Set visibility BEFORE toggling to prevent event blocking
            if new_state:
                # Opening: Make visible FIRST, then reveal
                settings_revealer.set_visible(True)
                settings_revealer.show_all()
                settings_frame.show_all()
                settings_container.show_all()
                # Small delay to ensure visibility is set before animation
                GLib.idle_add(lambda: settings_revealer.set_reveal_child(True))
            else:
                # Closing: Hide immediately (animation will still complete)
                settings_revealer.set_reveal_child(False)
                # Set invisible after animation completes (500ms transition)
                GLib.timeout_add(550, lambda: settings_revealer.set_visible(False))
            
            state_text = "SHOW" if new_state else "HIDE"
            print(f"   State: {state_text}")
            
            self.status_label.set_markup(
                f'<span color="#3498db">Settings: {state_text}</span>'
            )
            
            return False  # Ensure handler completes
        
        settings_button.connect('clicked', on_settings_clicked)
        print("Connected settings button to revealer")
        
        # ⭐ NEW: Connect simulate control buttons to hide settings when clicked
        def on_simulate_button_clicked(button, button_name):
            """Hide settings when any simulate control button is clicked."""
            print(f"🎮 {button_name} button clicked - hiding settings")
            hide_settings_panel()
        
        # Connect all simulate control buttons
        simulate_buttons = {
            'run': simulate_loader.run_button,
            'step': simulate_loader.step_button,
            'stop': simulate_loader.stop_button,
            'reset': simulate_loader.reset_button,
        }
        
        for button_name, button in simulate_buttons.items():
            if button:
                button.connect('clicked', on_simulate_button_clicked, button_name.upper())
                print(f"   Connected {button_name} button to hide settings")
            else:
                print(f"   ⚠️  {button_name} button not found")
        
        # ⭐ Store settings_revealer reference for hiding on other events
        self.settings_revealer = settings_revealer
        
        return False  # Don't repeat
    
    def _on_category_selected(self, palette, category):
        """Handle category selection - hide settings when switching categories."""
        # ⚙️ MASTER CONTROL: Hide settings when switching away from simulate category
        if hasattr(self, 'settings_revealer') and self.settings_revealer.get_reveal_child():
            if category != 'simulate':  # Only hide if switching AWAY from simulate
                self.settings_revealer.set_reveal_child(False)
                # Set not visible after animation completes (500ms + buffer)
                GLib.timeout_add(550, lambda: self.settings_revealer.set_visible(False))
                print(f"   Settings hidden (switched away from simulate to: {category})")
        
        self.status_label.set_markup(
            f'<span color="#3498db">Category: {category.upper()}</span>'
        )
    
    def _on_mode_change(self, palette, mode):
        """Handle mode change."""
        self.status_label.set_markup(
            f'<span color="#27ae60">Mode changed: {mode.upper()}</span>'
        )
    
    def _on_simulation_step(self, palette, time):
        """Handle simulation step."""
        self.status_label.set_markup(
            f'<span color="#f39c12">Simulation: t={time:.2f}s</span>'
        )


def main():
    """Run the testbed application."""
    app = ExtendedSwissKnifeTestApp()
    
    try:
        Gtk.main()
    except KeyboardInterrupt:
        print("\n\n✓ Testbed closed by user")
    
    print("\n" + "=" * 70)
    print("TESTBED SESSION COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. If settings panel works → Update production SimulateToolsPaletteLoader")
    print("  2. If issues found → Fix in testbed first")
    print("  3. Document any architecture changes needed")
    print()


if __name__ == '__main__':
    main()
