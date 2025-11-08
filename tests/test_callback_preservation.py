#!/usr/bin/env python3
"""Test that on_simulation_complete callback is preserved during reset_for_new_model."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.engine.simulation.controller import SimulationController
from shypn.data.model_canvas_manager import ModelCanvasManager

print("=" * 80)
print("TEST: Callback Preservation During reset_for_new_model")
print("=" * 80)

# Create initial model
print("\n[1] Creating initial model...")
manager1 = ModelCanvasManager()
manager1.add_place(100, 100)
manager1.add_transition(200, 100)
print(f"   Model 1: {len(manager1.places)} places, {len(manager1.transitions)} transitions")

# Create controller
print("\n[2] Creating controller...")
controller = SimulationController(manager1)
print(f"   Controller created, model has {len(controller.model.places)} places")

# Register callback
print("\n[3] Registering on_simulation_complete callback...")
callback_called = [False]  # Use list to allow modification in nested function

def test_callback():
    print("   [CALLBACK] ✅ on_simulation_complete was called!")
    callback_called[0] = True

controller.on_simulation_complete = test_callback
print(f"   Callback registered: {controller.on_simulation_complete is not None}")

# Create new model
print("\n[4] Creating new model...")
manager2 = ModelCanvasManager()
manager2.add_place(150, 150)
manager2.add_transition(250, 150)
print(f"   Model 2: {len(manager2.places)} places, {len(manager2.transitions)} transitions")

# Reset controller with new model
print("\n[5] Calling reset_for_new_model()...")
controller.reset_for_new_model(manager2)
print(f"   Reset complete, model now has {len(controller.model.places)} places")

# Check if callback was preserved
print("\n[6] Checking callback preservation...")
callback_preserved = controller.on_simulation_complete is not None
print(f"   Callback preserved: {callback_preserved}")

if not callback_preserved:
    print("\n❌ TEST FAILED: Callback was lost during reset_for_new_model!")
    sys.exit(1)

# Test that callback actually works
print("\n[7] Testing callback by calling it...")
if controller.on_simulation_complete:
    controller.on_simulation_complete()
    
if callback_called[0]:
    print("\n✅ TEST PASSED: Callback was preserved and works correctly!")
    sys.exit(0)
else:
    print("\n❌ TEST FAILED: Callback exists but didn't execute!")
    sys.exit(1)
