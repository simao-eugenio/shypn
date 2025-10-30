#!/usr/bin/env python3
"""
Test Rate Function Auto-Adjustment in Dynamic Analyses Panel
=============================================================

This test demonstrates the automatic matplotlib plot adjustment based on
rate function types entered in transition properties dialog.

When you enter rate functions like:
- hill_equation(P1, vmax=10, kd=5, n=2)
- michaelis_menten(P1, vmax=15, km=3)
- sigmoid(t, 10, 0.5)

And add the transition to Dynamic Analyses → Transitions panel,
the plot automatically:
- Detects the function type
- Sets appropriate X-axis range (0 to 4×Kd for Hill, etc.)
- Shows parameter marker lines (Kd, Km, center)
- Adds annotations for key points

Usage:
    python3 test_rate_function_auto_adjust.py
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.edit.manager import Manager
from shypn.netobjs import Place, Transition
from shypn.engine.simulation.controller import SimulationController
from shypn.analyses.transition_rate_panel import TransitionRatePanel
from shypn.diagnostic import SimulationDataCollector


def create_test_model():
    """Create a test model with transitions using different rate functions."""
    manager = Manager()
    model = manager.model
    
    # Create places
    p1 = Place(1, 100, 200, "P1")
    p1.tokens = 10.0
    model.places.append(p1)
    
    p2 = Place(2, 300, 200, "P2")
    p2.tokens = 0.0
    model.places.append(p2)
    
    # Transition 1: Hill equation
    t1 = Transition(1, 200, 200, "T1_Hill", "Hill", horizontal=False)
    t1.transition_type = 'continuous'
    t1.properties = {
        'rate_function': 'hill_equation(P1, vmax=10, kd=5, n=2)'
    }
    model.transitions.append(t1)
    
    # Transition 2: Michaelis-Menten
    t2 = Transition(2, 200, 300, "T2_MM", "Michaelis-Menten", horizontal=False)
    t2.transition_type = 'continuous'
    t2.properties = {
        'rate_function': 'michaelis_menten(P1, vmax=15, km=3)'
    }
    model.transitions.append(t2)
    
    # Transition 3: Sigmoid
    t3 = Transition(3, 200, 400, "T3_Sigmoid", "Sigmoid", horizontal=False)
    t3.transition_type = 'continuous'
    t3.properties = {
        'rate_function': 'sigmoid(t, 10, 0.5)'
    }
    model.transitions.append(t3)
    
    # Create arcs (P1 → transitions → P2)
    from shypn.netobjs import Arc
    
    arc1 = Arc(1, p1, t1, weight=1.0)
    model.arcs.append(arc1)
    
    arc2 = Arc(2, t1, p2, weight=1.0)
    model.arcs.append(arc2)
    
    return manager


class TestWindow(Gtk.Window):
    """Test window showing rate function auto-adjustment."""
    
    def __init__(self):
        super().__init__(title="Rate Function Auto-Adjustment Test")
        self.set_default_size(1000, 700)
        self.connect('destroy', Gtk.main_quit)
        
        # Create model
        self.manager = create_test_model()
        
        # Create data collector
        self.data_collector = SimulationDataCollector()
        
        # Create simulation controller
        self.sim_controller = SimulationController(self.manager.model, self.data_collector)
        
        # Create UI
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        self.add(vbox)
        
        # Info label
        info_label = Gtk.Label()
        info_label.set_markup(
            "<b>Rate Function Auto-Adjustment Test</b>\n\n"
            "This test shows how the Dynamic Analyses panel automatically adjusts\n"
            "the matplotlib plot based on the rate function type:\n\n"
            "• <b>T1_Hill</b>: hill_equation(P1, vmax=10, kd=5, n=2)\n"
            "  → X-axis: 0 to 20 (4×Kd), shows Kd=5 marker\n\n"
            "• <b>T2_MM</b>: michaelis_menten(P1, vmax=15, km=3)\n"
            "  → X-axis: 0 to 12 (4×Km), shows Km=3 marker\n\n"
            "• <b>T3_Sigmoid</b>: sigmoid(t, 10, 0.5)\n"
            "  → X-axis: 0 to 20 (2×center), shows center=10 marker"
        )
        info_label.set_justify(Gtk.Justification.LEFT)
        vbox.pack_start(info_label, False, False, 0)
        
        # Control buttons
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        vbox.pack_start(hbox, False, False, 0)
        
        # Add transitions buttons
        add_t1_btn = Gtk.Button(label="Add T1 (Hill)")
        add_t1_btn.connect('clicked', self.on_add_t1_clicked)
        hbox.pack_start(add_t1_btn, False, False, 0)
        
        add_t2_btn = Gtk.Button(label="Add T2 (Michaelis-Menten)")
        add_t2_btn.connect('clicked', self.on_add_t2_clicked)
        hbox.pack_start(add_t2_btn, False, False, 0)
        
        add_t3_btn = Gtk.Button(label="Add T3 (Sigmoid)")
        add_t3_btn.connect('clicked', self.on_add_t3_clicked)
        hbox.pack_start(add_t3_btn, False, False, 0)
        
        # Run simulation button
        run_btn = Gtk.Button(label="▶ Run Simulation")
        run_btn.connect('clicked', self.on_run_simulation_clicked)
        hbox.pack_start(run_btn, False, False, 0)
        
        # Clear button
        clear_btn = Gtk.Button(label="🗑️ Clear")
        clear_btn.connect('clicked', self.on_clear_clicked)
        hbox.pack_start(clear_btn, False, False, 0)
        
        # Create transition rate panel
        self.rate_panel = TransitionRatePanel(self.data_collector)
        vbox.pack_start(self.rate_panel.get_widget(), True, True, 0)
        
        # Status label
        self.status_label = Gtk.Label(label="Add transitions and run simulation to see auto-adjustment")
        vbox.pack_start(self.status_label, False, False, 0)
    
    def on_add_t1_clicked(self, button):
        """Add T1 (Hill equation) to plot."""
        t1 = self.manager.model.transitions[0]
        self.rate_panel.add_object(t1)
        self.status_label.set_text(f"✓ Added {t1.label} - Run simulation to see Hill equation with Kd=5 marker")
    
    def on_add_t2_clicked(self, button):
        """Add T2 (Michaelis-Menten) to plot."""
        t2 = self.manager.model.transitions[1]
        self.rate_panel.add_object(t2)
        self.status_label.set_text(f"✓ Added {t2.label} - Run simulation to see M-M curve with Km=3 marker")
    
    def on_add_t3_clicked(self, button):
        """Add T3 (Sigmoid) to plot."""
        t3 = self.manager.model.transitions[2]
        self.rate_panel.add_object(t3)
        self.status_label.set_text(f"✓ Added {t3.label} - Run simulation to see sigmoid with center=10 marker")
    
    def on_run_simulation_clicked(self, button):
        """Run simulation to generate data."""
        self.status_label.set_text("⏳ Running simulation...")
        
        # Reset simulation
        self.data_collector.clear()
        self.sim_controller.reset()
        
        # Run simulation for 25 seconds
        duration = 25.0
        dt = 0.1
        
        def run_step():
            """Run one simulation step."""
            if self.sim_controller.time < duration:
                self.sim_controller.step(dt)
                self.rate_panel.update_plot()
                return True  # Continue
            else:
                self.status_label.set_text(
                    "✅ Simulation complete! Notice the auto-adjusted X-axis ranges and parameter markers"
                )
                return False  # Stop
        
        # Run simulation steps with idle callback
        GLib.idle_add(run_step)
    
    def on_clear_clicked(self, button):
        """Clear all transitions from plot."""
        self.rate_panel.selected_objects.clear()
        self.rate_panel.update_plot()
        self.data_collector.clear()
        self.status_label.set_text("Cleared - Add transitions and run again")


def main():
    """Run the test."""
    print("=" * 70)
    print("RATE FUNCTION AUTO-ADJUSTMENT TEST")
    print("=" * 70)
    print()
    print("This test demonstrates automatic matplotlib plot adjustment based on")
    print("rate function types from transition properties.")
    print()
    print("Test Procedure:")
    print("1. Click 'Add T1 (Hill)' to add Hill equation transition")
    print("2. Click 'Add T2 (Michaelis-Menten)' to add M-M transition")
    print("3. Click 'Add T3 (Sigmoid)' to add sigmoid transition")
    print("4. Click '▶ Run Simulation' to generate data")
    print("5. Observe:")
    print("   - Hill: X-axis 0-20 (4×Kd=5), gray Kd marker at x=5")
    print("   - M-M: X-axis 0-12 (4×Km=3), orange Km marker at x=3")
    print("   - Sigmoid: X-axis 0-20 (2×center=10), purple center marker at x=10")
    print()
    print("The plot automatically adjusts X-axis ranges based on function parameters!")
    print("=" * 70)
    print()
    
    window = TestWindow()
    window.show_all()
    
    Gtk.main()


if __name__ == '__main__':
    main()
