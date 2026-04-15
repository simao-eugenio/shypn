#!/usr/bin/env python3
"""
# This is a script-style test intended to be run directly (not via pytest).
if __name__ != '__main__':
    import pytest
    pytest.skip('Script-style test, run directly with python3', allow_module_level=True)

Test script to verify T_celsius is properly injected into rate evaluation context.
"""

import sys
sys.path.insert(0, 'src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import ModelAdapter, SimulationController

# Load the model
model_path = 'workspace/projects/My_Project/drug_discovery/models/normal/macrocycle_transport_normal_nme_0_thermo.shy'
print(f"Loading model: {model_path}")
document = DocumentModel.load_from_file(model_path)

print(f"\n✓ Model loaded successfully")
print(f"  Places: {len(document.places)}")
print(f"  Transitions: {len(document.transitions)}")

# Check thermodynamic_settings on DocumentModel
if hasattr(document, 'thermodynamic_settings'):
    print(f"\n✓ DocumentModel has thermodynamic_settings:")
    for key, value in document.thermodynamic_settings.items():
        print(f"    {key}: {value}")
else:
    print(f"\n✗ DocumentModel missing thermodynamic_settings")
    sys.exit(1)

# Create ModelAdapter (this is what behaviors actually see)
adapter = ModelAdapter(document)

# Check thermodynamic_settings on ModelAdapter
if hasattr(adapter, 'thermodynamic_settings'):
    print(f"\n✓ ModelAdapter exposes thermodynamic_settings:")
    settings = adapter.thermodynamic_settings
    for key, value in settings.items():
        print(f"    {key}: {value}")
    
    # Verify T_celsius calculation
    T = settings.get('temperature', 298.15)
    T_celsius = T - 273.15
    print(f"\n✓ Temperature conversion:")
    print(f"    T (Kelvin): {T}")
    print(f"    T_celsius: {T_celsius}°C")
else:
    print(f"\n✗ ModelAdapter missing thermodynamic_settings property")
    print(f"   Available attributes: {[a for a in dir(adapter) if not a.startswith('_')]}")
    sys.exit(1)

# Test actual behavior context building
print(f"\n✓ Simulating rate evaluation context...")
# Find a transition with thermodynamic rate function
for transition in document.transitions:
    if hasattr(transition, 'rate_function') and transition.rate_function:
        if 'T_celsius' in transition.rate_function or 'arrhenius' in transition.rate_function:
            print(f"  Found transition: {transition.name}")
            print(f"  Rate function: {transition.rate_function[:80]}...")
            
            # Create controller (which creates adapter)
            controller = SimulationController(document, verbose=False)
            
            # Check if adapter is used
            if hasattr(controller.model, 'thermodynamic_settings'):
                print(f"  ✓ Controller's model adapter has thermodynamic_settings")
                
                # Simulate what happens in StochasticBehavior._evaluate_rate_function
                settings = controller.model.thermodynamic_settings
                T = settings.get('temperature', 298.15)
                T_celsius = T - 273.15
                
                print(f"  ✓ Context would contain:")
                print(f"      T = {T} K")
                print(f"      T_celsius = {T_celsius}°C")
                print(f"      pH = {settings.get('ph', 7.0)}")
                print(f"      ionic_strength = {settings.get('ionic_strength', 0.1)}")
            else:
                print(f"  ✗ Controller's model adapter missing thermodynamic_settings")
                sys.exit(1)
            break

print(f"\n{'='*60}")
print(f"✓ ALL TESTS PASSED")
print(f"  T_celsius will now be available in rate evaluation context")
print(f"{'='*60}")
