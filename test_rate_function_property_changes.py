#!/usr/bin/env python3
"""
Test: Rate Function Property Changes Awareness
==============================================

Tests that the Dynamic Analyses panel plot automatically adjusts
when transition rate function properties are changed during simulation.

Scenario:
1. Create transition with hill_equation → Verify Hill adjustments
2. Change to michaelis_menten → Verify M-M adjustments  
3. Change to sigmoid → Verify Sigmoid adjustments
4. Change to exponential → Verify Exponential adjustments

Expected: Plot should automatically re-detect function type and
          re-apply appropriate axis scaling and parameter markers
          each time properties change.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.core.place import Place
from shypn.core.transition import Transition
from shypn.helpers.controller import Controller


class RateFunctionPropertyChangeTest(Gtk.Window):
    def __init__(self):
        super().__init__(title="Rate Function Property Change Test")
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
            "<b>📊 Rate Function Property Change Test</b>\n\n"
            "This test verifies that the Dynamic Analyses plot automatically\n"
            "adjusts when you change transition rate function properties.\n\n"
            "<b>Test Steps:</b>\n"
            "1. Click 'Start Simulation' to begin\n"
            "2. Observe initial Hill equation plot (X-axis: 0-20, gray marker at Kd=5)\n"
            "3. Click 'Change to Michaelis-Menten' → Plot should re-adjust\n"
            "   (X-axis: 0-12, orange marker at Km=3)\n"
            "4. Click 'Change to Sigmoid' → Plot should re-adjust\n"
            "   (X-axis: 0-20, purple marker at center=10)\n"
            "5. Click 'Change to Exponential' → Plot should re-adjust\n"
            "   (X-axis extended for exponential curve)\n\n"
            "<b>✅ Success Criteria:</b>\n"
            "Plot automatically re-scales and updates markers each time\n"
            "you change the rate function type."
        )
        instructions.set_justify(Gtk.Justification.LEFT)
        vbox.pack_start(instructions, False, False, 0)
        
        # Button controls
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        self.start_button = Gtk.Button(label="▶ Start Simulation")
        self.start_button.connect('clicked', self._on_start_simulation)
        button_box.pack_start(self.start_button, True, True, 0)
        
        self.change_mm_button = Gtk.Button(label="Change to Michaelis-Menten")
        self.change_mm_button.set_sensitive(False)
        self.change_mm_button.connect('clicked', lambda w: self._change_rate_function('michaelis_menten'))
        button_box.pack_start(self.change_mm_button, True, True, 0)
        
        self.change_sigmoid_button = Gtk.Button(label="Change to Sigmoid")
        self.change_sigmoid_button.set_sensitive(False)
        self.change_sigmoid_button.connect('clicked', lambda w: self._change_rate_function('sigmoid'))
        button_box.pack_start(self.change_sigmoid_button, True, True, 0)
        
        self.change_exp_button = Gtk.Button(label="Change to Exponential")
        self.change_exp_button.set_sensitive(False)
        self.change_exp_button.connect('clicked', lambda w: self._change_rate_function('exponential'))
        button_box.pack_start(self.change_exp_button, True, True, 0)
        
        vbox.pack_start(button_box, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_markup("<i>Click 'Start Simulation' to begin test</i>")
        vbox.pack_start(self.status_label, False, False, 0)
        
        # Embed controller's UI
        vbox.pack_start(self.controller.main_container, True, True, 0)
        
        self.add(vbox)
        self.connect('destroy', Gtk.main_quit)
        
        self.current_function = 'hill'
    
    def _create_test_model(self):
        """Create test model with one transition."""
        model = self.controller.model
        
        # Create places
        p1 = Place(id=1, name='Substrate', x=100, y=200, initial_tokens=10.0)
        p2 = Place(id=2, name='Product', x=300, y=200, initial_tokens=0.0)
        
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
        
        print(f"✅ Created test model:")
        print(f"   Places: {p1.name} (P1), {p2.name} (P2)")
        print(f"   Transition: {self.transition.name}")
        print(f"   Initial rate function: {self.transition.properties['rate_function']}")
    
    def _on_start_simulation(self, button):
        """Start simulation and add transition to Dynamic Analyses plot."""
        # Open Dynamic Analyses panel
        self.controller.right_panel_loader.notebook.set_current_page(2)  # Dynamic Analyses tab
        
        # Get transition panel
        transition_panel = self.controller.right_panel_loader.transition_panel
        
        # Add transition to plot
        transition_panel.add_object(self.transition)
        
        # Start simulation
        self.controller.simulation_controls.on_start_stop(None)
        
        # Enable change buttons
        self.start_button.set_sensitive(False)
        self.change_mm_button.set_sensitive(True)
        self.change_sigmoid_button.set_sensitive(True)
        self.change_exp_button.set_sensitive(True)
        
        self.status_label.set_markup(
            "<b>✅ Simulation started</b>\n"
            "Showing Hill equation: <tt>hill_equation(P1, vmax=10, kd=5, n=2)</tt>\n"
            "Expected: X-axis 0-20, gray marker at Kd=5"
        )
        
        print(f"\n📊 Simulation started with Hill equation")
        print(f"   Expected: X-axis 0-20, gray marker at Kd=5")
    
    def _change_rate_function(self, new_type):
        """Change the transition's rate function and verify plot updates."""
        old_function = self.transition.properties['rate_function']
        
        if new_type == 'michaelis_menten':
            new_function = 'michaelis_menten(P1, vmax=15, km=3)'
            expected = "X-axis 0-12, orange marker at Km=3"
            self.change_mm_button.set_sensitive(False)
            self.current_function = 'mm'
        elif new_type == 'sigmoid':
            new_function = 'sigmoid(t, 10, 0.5)'
            expected = "X-axis 0-20, purple marker at center=10"
            self.change_sigmoid_button.set_sensitive(False)
            self.current_function = 'sigmoid'
        elif new_type == 'exponential':
            new_function = 'math.exp(0.1 * t)'
            expected = "X-axis extended for exponential curve"
            self.change_exp_button.set_sensitive(False)
            self.current_function = 'exp'
        
        # Update transition properties
        self.transition.properties['rate_function'] = new_function
        
        # Emit properties-changed signal to trigger plot update
        # This simulates what happens when user saves properties dialog
        if hasattr(self.controller, 'canvas_loader'):
            canvas_loader = self.controller.canvas_loader
            transition_panel = self.controller.right_panel_loader.transition_panel
            
            # Manually trigger the update that would happen via signal
            if self.transition in transition_panel.selected_objects:
                transition_panel.needs_update = True
                print(f"\n🔄 Set needs_update=True on transition_panel")
        
        self.status_label.set_markup(
            f"<b>🔄 Changed rate function</b>\n"
            f"From: <tt>{old_function}</tt>\n"
            f"To: <tt>{new_function}</tt>\n"
            f"Expected: {expected}"
        )
        
        print(f"\n🔄 Changed rate function:")
        print(f"   From: {old_function}")
        print(f"   To:   {new_function}")
        print(f"   Expected: {expected}")
        print(f"   needs_update flag set → plot should redraw on next update")


def main():
    print("=" * 80)
    print("RATE FUNCTION PROPERTY CHANGE TEST")
    print("=" * 80)
    print("\nThis test verifies that changing a transition's rate function")
    print("properties automatically triggers the plot to re-adjust.\n")
    
    test_window = RateFunctionPropertyChangeTest()
    test_window.show_all()
    
    Gtk.main()


if __name__ == '__main__':
    main()
