#!/usr/bin/env python3
"""
Debug Test: Rate Function Property Changes
===========================================

This test helps debug why the plot doesn't update when rate functions change.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.netobjs import Place, Transition
from shypn.helpers.controller import Controller


class PropertyChangeDebugTest(Gtk.Window):
    def __init__(self):
        super().__init__(title="Property Change Debug Test")
        self.set_default_size(1200, 800)
        
        # Create controller and model
        self.controller = Controller()
        self.controller.create_new_model()
        
        # Create test objects
        self._create_test_model()
        
        # Layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        
        # Instructions
        instructions = Gtk.Label()
        instructions.set_markup(
            "<b>🐛 Property Change Debug Test</b>\n\n"
            "<b>Steps:</b>\n"
            "1. Click 'Start & Add to Plot'\n"
            "2. Watch console for [PROPERTY CHANGE], [UPDATE], [UPDATE_PLOT] messages\n"
            "3. Click 'Change Rate Function' and watch console\n"
            "4. Check if needs_update flag is set and update_plot is called\n\n"
            "<b>Expected Console Output:</b>\n"
            "[PROPERTY CHANGE] Transition ... properties changed - setting needs_update=True\n"
            "[UPDATE] needs_update=True\n"
            "[UPDATE_PLOT] force_full_redraw=True\n"
            "[TRANSITION_RATE_PANEL] update_plot called"
        )
        instructions.set_justify(Gtk.Justification.LEFT)
        vbox.pack_start(instructions, False, False, 0)
        
        # Button controls
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        self.start_button = Gtk.Button(label="▶ Start & Add to Plot")
        self.start_button.connect('clicked', self._on_start_simulation)
        button_box.pack_start(self.start_button, True, True, 0)
        
        self.change_button = Gtk.Button(label="Change Rate Function")
        self.change_button.set_sensitive(False)
        self.change_button.connect('clicked', self._on_change_rate_function)
        button_box.pack_start(self.change_button, True, True, 0)
        
        self.manual_update_button = Gtk.Button(label="Manual needs_update=True")
        self.manual_update_button.set_sensitive(False)
        self.manual_update_button.connect('clicked', self._on_manual_update)
        button_box.pack_start(self.manual_update_button, True, True, 0)
        
        vbox.pack_start(button_box, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_markup("<i>Click 'Start & Add to Plot' to begin</i>")
        vbox.pack_start(self.status_label, False, False, 0)
        
        # Embed controller's UI
        vbox.pack_start(self.controller.main_container, True, True, 0)
        
        self.add(vbox)
        self.connect('destroy', Gtk.main_quit)
    
    def _create_test_model(self):
        """Create test model with one transition."""
        model = self.controller.model
        
        # Create places
        p1 = Place(id=1, name='P1', x=100, y=200, initial_tokens=10.0)
        p2 = Place(id=2, name='P2', x=300, y=200, initial_tokens=0.0)
        
        model.add_place(p1)
        model.add_place(p2)
        
        # Create transition with Hill equation initially
        self.transition = Transition(
            id=1,
            name='T_Test',
            x=200,
            y=200,
            transition_type='continuous'
        )
        self.transition.properties['rate_function'] = 'hill_equation(P1, vmax=10, kd=5, n=2)'
        model.add_transition(self.transition)
        
        # Add arcs
        model.add_arc(p1, self.transition, weight=1)
        model.add_arc(self.transition, p2, weight=1)
        
        print(f"\n{'='*80}")
        print(f"TEST MODEL CREATED")
        print(f"{'='*80}")
        print(f"Transition: {self.transition.name} (ID:{self.transition.id})")
        print(f"Initial rate_function: {self.transition.properties['rate_function']}")
        print(f"{'='*80}\n")
    
    def _on_start_simulation(self, button):
        """Start simulation and add transition to Dynamic Analyses plot."""
        print(f"\n{'='*80}")
        print(f"STARTING SIMULATION AND ADDING TO PLOT")
        print(f"{'='*80}\n")
        
        # Open Dynamic Analyses panel
        self.controller.right_panel_loader.notebook.set_current_page(2)  # Dynamic Analyses tab
        
        # Get transition panel
        self.transition_panel = self.controller.right_panel_loader.transition_panel
        
        print(f"Before add_object:")
        print(f"  selected_objects: {[o.name for o in self.transition_panel.selected_objects]}")
        print(f"  needs_update: {self.transition_panel.needs_update}")
        
        # Add transition to plot
        self.transition_panel.add_object(self.transition)
        
        print(f"\nAfter add_object:")
        print(f"  selected_objects: {[o.name for o in self.transition_panel.selected_objects]}")
        print(f"  needs_update: {self.transition_panel.needs_update}")
        print(f"  Transition in selected_objects: {self.transition in self.transition_panel.selected_objects}")
        
        # Start simulation
        self.controller.simulation_controls.on_start_stop(None)
        
        # Enable change button
        self.start_button.set_sensitive(False)
        self.change_button.set_sensitive(True)
        self.manual_update_button.set_sensitive(True)
        
        self.status_label.set_markup(
            "<b>✅ Simulation started, transition added to plot</b>\n"
            "Rate function: <tt>hill_equation(P1, vmax=10, kd=5, n=2)</tt>"
        )
        
        print(f"\n{'='*80}")
        print(f"READY - Click 'Change Rate Function' button")
        print(f"{'='*80}\n")
    
    def _on_change_rate_function(self, button):
        """Change the transition's rate function properties."""
        print(f"\n{'='*80}")
        print(f"CHANGING RATE FUNCTION")
        print(f"{'='*80}\n")
        
        old_function = self.transition.properties['rate_function']
        new_function = 'michaelis_menten(P1, vmax=15, km=3)'
        
        print(f"Before change:")
        print(f"  rate_function: {old_function}")
        print(f"  Transition ID: {self.transition.id}")
        print(f"  Transition in selected_objects: {self.transition in self.transition_panel.selected_objects}")
        print(f"  needs_update: {self.transition_panel.needs_update}")
        
        # Update transition properties
        self.transition.properties['rate_function'] = new_function
        
        print(f"\nAfter property assignment:")
        print(f"  rate_function: {self.transition.properties['rate_function']}")
        
        # Manually emit properties-changed signal like the dialog does
        # This simulates what happens when user clicks OK in properties dialog
        print(f"\nManually setting needs_update=True (simulating signal handler)...")
        if self.transition in self.transition_panel.selected_objects:
            self.transition_panel.needs_update = True
            print(f"  ✅ needs_update set to True")
        else:
            print(f"  ❌ Transition NOT in selected_objects!")
        
        print(f"\nAfter needs_update=True:")
        print(f"  needs_update: {self.transition_panel.needs_update}")
        
        self.status_label.set_markup(
            f"<b>🔄 Rate function changed</b>\n"
            f"From: <tt>{old_function}</tt>\n"
            f"To: <tt>{new_function}</tt>\n"
            f"needs_update: <b>{self.transition_panel.needs_update}</b>\n\n"
            f"<b>Watch console for update_plot() calls...</b>"
        )
        
        print(f"\n{'='*80}")
        print(f"WAITING FOR UPDATE LOOP TO TRIGGER")
        print(f"Watch for [UPDATE] and [UPDATE_PLOT] messages...")
        print(f"{'='*80}\n")
    
    def _on_manual_update(self, button):
        """Manually trigger update for debugging."""
        print(f"\n{'='*80}")
        print(f"MANUAL UPDATE TRIGGER")
        print(f"{'='*80}\n")
        
        print(f"Before manual update_plot:")
        print(f"  needs_update: {self.transition_panel.needs_update}")
        print(f"  selected_objects: {[o.name for o in self.transition_panel.selected_objects]}")
        
        print(f"\nCalling update_plot(force_full_redraw=True) manually...")
        self.transition_panel.update_plot(force_full_redraw=True)
        
        print(f"\nAfter manual update_plot:")
        print(f"  needs_update: {self.transition_panel.needs_update}")
        
        print(f"\n{'='*80}\n")


def main():
    print("=" * 80)
    print("PROPERTY CHANGE DEBUG TEST")
    print("=" * 80)
    print("\nThis test helps debug why the plot doesn't update when rate functions change.\n")
    print("Watch console output for debug messages.\n")
    
    test_window = PropertyChangeDebugTest()
    test_window.show_all()
    
    Gtk.main()


if __name__ == '__main__':
    main()
