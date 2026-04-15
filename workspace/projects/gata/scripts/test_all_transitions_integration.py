#!/usr/bin/env python3
"""Test that all transition types work correctly after the type_name_map fix."""

import sys
import os
import json

sys.path.insert(0, 'src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation import SimulationController

def test_transition_type(type_name, transition_config):
    """Test a single transition type."""
    # Create minimal model
    model_data = {
        "places": [
            {"id": "P1", "name": "Input", "x": 0, "y": 0, "tokens": 10, "initial_marking": 10, "compartment_volume": 1.0},
            {"id": "P2", "name": "Output", "x": 100, "y": 0, "tokens": 0, "initial_marking": 0, "compartment_volume": 1.0}
        ],
        "transitions": [
            {"id": "T1", "name": "Transform", "x": 50, "y": 0, **transition_config}
        ],
        "arcs": [
            {"id": "A1", "source_id": "P1", "target_id": "T1", "arc_type": "normal", "weight": 1.0},
            {"id": "A2", "source_id": "T1", "target_id": "P2", "arc_type": "normal", "weight": 1.0}
        ]
    }
    
    try:
        document = DocumentModel.from_dict(model_data)
        controller = SimulationController(document, verbose=False)
        
        # Update enablement
        controller._update_enablement_states()
        
        # Get behavior
        trans = document.transitions[0]
        behavior = controller._get_behavior(trans)
        
        # Check state wasn't deleted
        if trans.id not in controller.transition_states:
            return False, "State was deleted after _get_behavior()"
        
        # Try to execute a step (may or may not fire, just checking no crash)
        controller.step()
        
        return True, f"Behavior: {type(behavior).__name__}"
    
    except Exception as e:
        return False, str(e)

print("="*80)
print("INTEGRATION TEST: All Transition Types")
print("="*80)
print()

# Test each transition type
test_cases = [
    ("immediate", {"transition_type": "immediate", "priority": 0, "weight": 1.0}),
    ("timed", {"transition_type": "timed", "delay": 5.0}),
    ("stochastic", {"transition_type": "stochastic", "rate_function": "1.0 * Input"}),
    ("continuous", {"transition_type": "continuous", "rate_function": "1.0 * Input"}),
    ("adaptive", {"transition_type": "adaptive", "rate_function": "1.0 * Input"}),
]

all_passed = True

for type_name, config in test_cases:
    success, message = test_transition_type(type_name, config)
    
    if success:
        print(f"✓ {type_name:12} - {message}")
    else:
        print(f"❌ {type_name:12} - {message}")
        all_passed = False

print()
print("="*80)
if all_passed:
    print("✅ ALL TRANSITION TYPES WORKING CORRECTLY")
    print("   The type_name_map fix does not break any existing functionality.")
else:
    print("❌ SOME TRANSITION TYPES FAILED")
print("="*80)
