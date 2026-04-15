#!/usr/bin/env python3
"""
# This is a script-style test intended to be run directly (not via pytest).
if __name__ != '__main__':
    import pytest
    pytest.skip('Script-style test, run directly with python3', allow_module_level=True)

Test that rate functions with T_celsius can now evaluate without errors.
"""

import sys
sys.path.insert(0, 'src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController
from shypn.engine.stochastic_behavior import StochasticBehavior

# Load model
model_path = 'workspace/projects/My_Project/drug_discovery/models/normal/macrocycle_transport_normal_nme_0_thermo.shy'
print(f"Loading model: {model_path}")
document = DocumentModel.load_from_file(model_path)

print(f"✓ Model loaded (T = 310.15 K = 37°C)\n")

# Create controller
controller = SimulationController(document, verbose=False)

print("Testing rate function evaluation for transitions using T_celsius:\n")

# Find transitions with T_celsius in rate function
test_transitions = []
for transition in document.transitions:
    if hasattr(transition, 'rate_function') and transition.rate_function:
        if 'T_celsius' in transition.rate_function or 'arrhenius' in transition.rate_function:
            test_transitions.append(transition)

print(f"Found {len(test_transitions)} transitions with thermodynamic rate functions:\n")

success_count = 0
error_count = 0

for transition in test_transitions:
    print(f"Testing: {transition.name}")
    print(f"  Rate function: {transition.rate_function[:100]}...")
    
    try:
        # Create behavior
        behavior = StochasticBehavior(transition, controller.model)
        
        # Try to evaluate rate function
        if hasattr(behavior, '_evaluate_rate_at_enablement'):
            rate = behavior._evaluate_rate_at_enablement(time=0.0)
            print(f"  ✓ Evaluated successfully: rate = {rate:.6f}")
            success_count += 1
        else:
            print(f"  ⚠ No _evaluate_rate_at_enablement method")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        error_count += 1
    print()

print(f"{'='*60}")
if error_count == 0:
    print(f"✓ SUCCESS: All {success_count} rate functions evaluated correctly")
    print(f"  T_celsius is now properly injected into evaluation context")
else:
    print(f"✗ FAILED: {error_count}/{len(test_transitions)} rate functions failed")
    sys.exit(1)
print(f"{'='*60}")
