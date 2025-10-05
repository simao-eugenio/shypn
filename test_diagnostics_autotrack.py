#!/usr/bin/env python3
"""Test script to verify diagnostics panel auto-tracking.

This script checks:
1. Timer is created when enable_auto_tracking() is called
2. Timer callback is being executed
3. Auto-tracking logic is working
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

import sys
sys.path.insert(0, 'src')

from shypn.analyses.diagnostics_panel import DiagnosticsPanel
from shypn.models import PetriNetModel, Place, Transition
from shypn.simulate import SimulationDataCollector


def test_auto_tracking():
    """Test auto-tracking setup and timer."""
    print("=" * 60)
    print("Testing Diagnostics Panel Auto-Tracking")
    print("=" * 60)
    
    # Create simple model
    model = PetriNetModel()
    place1 = Place(x=100, y=100, tokens=5)
    place2 = Place(x=200, y=100, tokens=0)
    transition = Transition(x=150, y=100, transition_type='immediate')
    
    model.add_place(place1)
    model.add_place(place2)
    model.add_transition(transition)
    
    # Add arcs to create locality
    from shypn.models import Arc
    arc1 = Arc(place1, transition, weight=1.0)
    arc2 = Arc(transition, place2, weight=1.0)
    model.add_arc(arc1)
    model.add_arc(arc2)
    
    print(f"\n✓ Created model with {len(model.transitions)} transition(s)")
    
    # Create data collector
    data_collector = SimulationDataCollector()
    print("✓ Created data collector")
    
    # Create diagnostics panel
    panel = DiagnosticsPanel(model, data_collector)
    print("✓ Created diagnostics panel")
    print(f"  - Model: {panel.model is not None}")
    print(f"  - Data collector: {panel.data_collector is not None}")
    print(f"  - Runtime analyzer: {panel.runtime_analyzer is not None}")
    print(f"  - Update timer (before enable): {panel.update_timer}")
    
    # Create minimal GTK setup
    window = Gtk.Window()
    container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    label = Gtk.Label()
    window.add(container)
    
    # Setup panel
    print("\n" + "=" * 60)
    print("Calling panel.setup()...")
    print("=" * 60)
    panel.setup(container, selection_label=label)
    
    print(f"\n✓ Panel setup complete")
    print(f"  - Update timer (after setup): {panel.update_timer}")
    print(f"  - Current transition: {panel.current_transition}")
    
    # Simulate some firing events
    print("\n" + "=" * 60)
    print("Simulating transition firing...")
    print("=" * 60)
    
    # Record a firing event
    data_collector.record_transition_fire(transition, 0.5)
    data_collector.record_transition_fire(transition, 1.0)
    data_collector.record_transition_fire(transition, 1.5)
    
    print(f"✓ Recorded 3 firing events for transition")
    
    # Check if runtime analyzer can see events
    if panel.runtime_analyzer:
        diag = panel.runtime_analyzer.get_transition_diagnostics(transition, window=10)
        print(f"  - Last fired: {diag.get('last_fired')}")
        print(f"  - Event count: {diag.get('event_count')}")
        print(f"  - Throughput: {diag.get('throughput'):.3f} fires/sec")
    
    # Let timer run a few times
    print("\n" + "=" * 60)
    print("Letting timer run (checking 3 times)...")
    print("=" * 60)
    
    def check_timer(count=[0]):
        count[0] += 1
        print(f"\n--- Check #{count[0]} ---")
        print(f"Current transition: {panel.current_transition}")
        if panel.current_transition:
            trans_name = getattr(panel.current_transition, 'name', panel.current_transition.id)
            print(f"Auto-tracking found transition: {trans_name}")
            print("✅ AUTO-TRACKING IS WORKING!")
            Gtk.main_quit()
            return False
        
        if count[0] >= 3:
            print("\n❌ AUTO-TRACKING DID NOT ACTIVATE")
            print("   Timer ran 3 times but no transition was selected")
            Gtk.main_quit()
            return False
        
        return True
    
    # Check after 1 second intervals
    GLib.timeout_add(1000, check_timer)
    
    print("\nStarting GTK main loop...")
    Gtk.main()
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)


if __name__ == '__main__':
    test_auto_tracking()
