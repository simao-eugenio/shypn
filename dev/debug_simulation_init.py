#!/usr/bin/env python3
"""
Debug simulation initialization after import.

This script tests if:
1. Transitions are created correctly
2. Controller reset is triggered
3. Transition states are initialized
4. Source transitions are marked as enabled
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc

def create_test_model():
    """Create a simple test model with source transition."""
    print("\n=== Creating Test Model ===")
    
    # Create a source place and transition
    source_place = Place(id="source_p", label="Source Place", x=100, y=100, tokens=0)
    target_place = Place(id="target_p", label="Target Place", x=300, y=100, tokens=0)
    
    source_transition = Transition(
        id="source_t",
        label="Source Transition",
        x=200,
        y=100,
        is_source=True,  # Mark as source
        transition_type="continuous",
        rate=1.0
    )
    
    # Create output arc from source transition to target place
    arc = Arc(
        id="arc1",
        source_id="source_t",
        target_id="target_p",
        weight=1
    )
    arc.source = source_transition
    arc.target = target_place
    
    print(f"✅ Created source transition: {source_transition.id}")
    print(f"   - is_source: {source_transition.is_source}")
    print(f"   - transition_type: {source_transition.transition_type}")
    print(f"   - rate: {source_transition.rate}")
    
    return [source_place, target_place], [source_transition], [arc]

def test_initialization():
    """Test the initialization process."""
    print("\n=== Testing Simulation Initialization ===")
    
    # Create manager
    manager = ModelCanvasManager()
    print("✅ Manager created")
    
    # Create test model
    places, transitions, arcs = create_test_model()
    
    # Create a fake drawing area (we need this for the controller lookup)
    class FakeDrawingArea:
        pass
    
    drawing_area = FakeDrawingArea()
    
    # Load objects
    print("\n--- Loading objects ---")
    manager.load_objects(places, transitions, arcs, drawing_area)
    print("✅ Objects loaded")
    
    # Wait for idle callback to execute
    print("\n--- Waiting for idle callback ---")
    context = GLib.MainContext.default()
    max_iterations = 100
    for i in range(max_iterations):
        if context.iteration(False):
            print(f"  Idle callback executed (iteration {i+1})")
            break
    
    # Now check if controller exists and is initialized
    print("\n=== Checking Controller State ===")
    
    # Import canvas_loader
    from shypn.helpers import model_canvas_loader
    
    if hasattr(model_canvas_loader, '_instance'):
        canvas_loader = model_canvas_loader._instance
        print("✅ Canvas loader found")
        
        # Check if drawing_area is registered
        if hasattr(canvas_loader, 'canvas_managers'):
            if drawing_area in canvas_loader.canvas_managers:
                print("✅ Drawing area registered")
            else:
                print("❌ Drawing area NOT registered")
                print(f"   Registered drawing areas: {len(canvas_loader.canvas_managers)}")
        
        # Check if controller exists
        if hasattr(canvas_loader, 'simulation_controllers'):
            if drawing_area in canvas_loader.simulation_controllers:
                controller = canvas_loader.simulation_controllers[drawing_area]
                print("✅ Controller found")
                
                # Check transition states
                print(f"\n--- Controller State ---")
                print(f"  Time: {controller.time}")
                print(f"  Transition states: {len(controller.transition_states)}")
                print(f"  Behavior cache: {len(controller.behavior_cache)}")
                
                # Check if source transition is enabled
                source_t_id = "source_t"
                if source_t_id in controller.transition_states:
                    state = controller.transition_states[source_t_id]
                    print(f"\n--- Source Transition State ---")
                    print(f"  Transition ID: {source_t_id}")
                    print(f"  Enablement time: {state.enablement_time}")
                    print(f"  Enabled: {state.enablement_time is not None}")
                    
                    if state.enablement_time == 0:
                        print("✅ Source transition ENABLED at t=0")
                    else:
                        print(f"❌ Source transition NOT enabled (enablement_time={state.enablement_time})")
                else:
                    print(f"❌ Source transition state NOT found")
                    print(f"   Available states: {list(controller.transition_states.keys())}")
            else:
                print("❌ Controller NOT found")
                print(f"   Registered controllers: {len(canvas_loader.simulation_controllers)}")
        else:
            print("❌ simulation_controllers attribute missing")
    else:
        print("❌ Canvas loader instance not found")
    
    # Check manager's transitions
    print(f"\n--- Manager State ---")
    print(f"  Places: {len(manager.places)}")
    print(f"  Transitions: {len(manager.transitions)}")
    print(f"  Arcs: {len(manager.arcs)}")
    
    for transition in manager.transitions:
        print(f"\n  Transition: {transition.id}")
        print(f"    is_source: {getattr(transition, 'is_source', False)}")
        print(f"    transition_type: {getattr(transition, 'transition_type', None)}")

if __name__ == '__main__':
    test_initialization()
    print("\n=== Test Complete ===\n")
