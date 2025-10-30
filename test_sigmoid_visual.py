#!/usr/bin/env python3
"""Visual test to see what user sees with sigmoid rate function.

This creates the exact scenario the user described:
- P-T-P simple net
- Continuous transition with sigmoid(t, 10, 0.5)
- Opens the transition rate plot to visualize
"""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.netobjs import Place, Transition, Arc
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.engine.simulation.controller import SimulationController
from shypn.analyses.data_collector import SimulationDataCollector
from shypn.analyses.transition_rate_panel import TransitionRatePanel
from shypn.utils.time_utils import TimeUnits

def create_model():
    """Create P-T-P model with sigmoid rate."""
    model = ModelCanvasManager()
    
    # Create places
    p1 = Place(x=100, y=100, id=1, name="P1", label="Input")
    p1.tokens = 100
    p1.initial_marking = 100
    
    p2 = Place(x=300, y=100, id=2, name="P2", label="Output")
    p2.tokens = 0
    p2.initial_marking = 0
    
    model.places.append(p1)
    model.places.append(p2)
    
    # Create transition with sigmoid rate
    t1 = Transition(x=200, y=100, id=1, name="T1", label="Transfer")
    t1.transition_type = 'continuous'
    t1.properties = {
        'rate_function': 'sigmoid(t, 10, 0.5)'
    }
    
    model.transitions.append(t1)
    
    # Create arcs
    arc_in = Arc(source=p1, target=t1, id=1, name="A1", weight=1)
    arc_out = Arc(source=t1, target=p2, id=2, name="A2", weight=1)
    
    model.arcs.append(arc_in)
    model.arcs.append(arc_out)
    
    return model, t1

def run_simulation_default_settings(controller):
    """Run simulation with default settings (what user might experience)."""
    print("\n" + "="*70)
    print("Running with DEFAULT settings...")
    print("="*70)
    print(f"  Duration: {controller.settings.duration}")
    print(f"  Time units: {controller.settings.time_units}")
    print(f"  DT auto: {controller.settings.dt_auto}")
    print(f"  DT manual: {controller.settings.dt_manual}")
    print(f"  Effective DT: {controller.settings.get_effective_dt()}")
    print()
    
    step_count = 0
    while controller.step():
        step_count += 1
        if step_count > 10000:
            break
    
    print(f"  Steps executed: {step_count}")
    print(f"  Final time: {controller.time:.2f}")
    print()

def run_simulation_with_duration(controller, duration_seconds):
    """Run simulation with specified duration."""
    print("\n" + "="*70)
    print(f"Running with DURATION={duration_seconds}s...")
    print("="*70)
    
    controller.settings.set_duration(duration_seconds, TimeUnits.SECONDS)
    controller.settings.dt_auto = False
    controller.settings.dt_manual = 0.1
    
    print(f"  Duration: {controller.settings.duration}")
    print(f"  DT: {controller.settings.dt_manual}")
    print(f"  Expected steps: {int(duration_seconds / 0.1)}")
    print()
    
    step_count = 0
    while controller.step():
        step_count += 1
        if step_count > 10000:
            break
    
    print(f"  Steps executed: {step_count}")
    print(f"  Final time: {controller.time:.2f}")
    print()

def show_plot(model, t1, data_collector):
    """Show the transition rate plot in a window."""
    window = Gtk.Window(title="Sigmoid Rate Function - Visual Test")
    window.set_default_size(800, 600)
    window.connect("destroy", Gtk.main_quit)
    
    # Create transition rate panel
    rate_panel = TransitionRatePanel()
    rate_panel.set_data_collector(data_collector)
    rate_panel.add_transition(t1)
    
    window.add(rate_panel.get_widget())
    window.show_all()
    
    print("\n" + "="*70)
    print("VISUAL TEST: Check if plot shows S-curve or straight line")
    print("="*70)
    print("Expected: S-curve starting near 0, rising through 0.5 at t=10, approaching 1.0")
    print("User reports: Straight line")
    print()
    print("Close the window to exit.")
    print("="*70 + "\n")
    
    Gtk.main()

def main():
    print("\n" + "="*70)
    print("SIGMOID RATE FUNCTION - VISUAL TEST")
    print("="*70)
    print("Reproducing user scenario: P-T-P with sigmoid(t, 10, 0.5)")
    print()
    
    # Create model
    print("Creating model...")
    model, t1 = create_model()
    print("✓ P1[100] --[T1: sigmoid(t, 10, 0.5)]--> P2[0]")
    print()
    
    # Create simulation
    print("Setting up simulation...")
    controller = SimulationController(model)
    data_collector = SimulationDataCollector()
    controller.data_collector = data_collector
    controller.add_step_listener(data_collector.on_simulation_step)
    print("✓ Controller and data collector ready")
    
    # Test 1: Default settings (user might experience this)
    run_simulation_default_settings(controller)
    
    # Check data
    t1_data = data_collector.get_transition_data(t1.id)
    print(f"Data collected: {len(t1_data)} points")
    
    if len(t1_data) < 10:
        print("⚠ Very few data points! This might cause plotting issues.")
        print()
        
        # Reset and try with explicit duration
        print("Resetting and trying with explicit duration...")
        controller.reset()
        data_collector = SimulationDataCollector()
        controller.data_collector = data_collector
        controller.add_step_listener(data_collector.on_simulation_step)
        
        run_simulation_with_duration(controller, 20.0)
        t1_data = data_collector.get_transition_data(t1.id)
        print(f"Data collected: {len(t1_data)} points")
    
    # Show sample of rate values
    print("\nSample rate values:")
    print("Time (s)   Rate")
    print("-" * 20)
    for i in [0, len(t1_data)//4, len(t1_data)//2, 3*len(t1_data)//4, len(t1_data)-1]:
        if i < len(t1_data):
            time, event, details = t1_data[i]
            if details and 'rate' in details:
                print(f"{time:6.2f}     {details['rate']:.6f}")
    print()
    
    # Show plot
    show_plot(model, t1, data_collector)

if __name__ == '__main__':
    main()
