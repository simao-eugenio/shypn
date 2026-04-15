#!/usr/bin/env python3
"""Verify all transition type mappings are correct."""

import sys
import os

sys.path.insert(0, 'src')

from shypn.engine.immediate_behavior import ImmediateBehavior
from shypn.engine.timed_behavior import TimedBehavior
from shypn.engine.stochastic_behavior import StochasticBehavior
from shypn.engine.continuous_behavior import ContinuousBehavior
from shypn.engine.adaptive_hybrid_behavior import AdaptiveHybridBehavior

# The mapping from controller.py
type_name_map = {
    'Immediate': 'immediate',
    'Timed (TPN)': 'timed',
    'Stochastic (FSPN)': 'stochastic',
    'Continuous (SHPN)': 'continuous',
    'Adaptive Hybrid (ODE/Stochastic)': 'adaptive'
}

# Expected transition types
expected_types = {
    'Immediate': 'immediate',
    'Timed (TPN)': 'timed',
    'Stochastic (FSPN)': 'stochastic',
    'Continuous (SHPN)': 'continuous',
    'Adaptive Hybrid (ODE/Stochastic)': 'adaptive'
}

# Behavior classes and their transition_type values
behaviors = [
    ('ImmediateBehavior', ImmediateBehavior, 'immediate'),
    ('TimedBehavior', TimedBehavior, 'timed'),
    ('StochasticBehavior', StochasticBehavior, 'stochastic'),
    ('ContinuousBehavior', ContinuousBehavior, 'continuous'),
    ('AdaptiveHybridBehavior', AdaptiveHybridBehavior, 'adaptive'),
]

print("="*80)
print("TRANSITION TYPE MAPPING VERIFICATION")
print("="*80)
print()

all_correct = True

for class_name, behavior_class, expected_transition_type in behaviors:
    # Create a mock transition
    class MockTransition:
        def __init__(self, tid, ttype):
            self.id = tid
            self.name = f"Test_{ttype}"
            self.transition_type = ttype
            self.rate = 1.0
            self.rate_function = "1.0"
    
    # Create a mock model
    class MockModel:
        places = []
        transitions = []
        arcs = []
    
    mock_trans = MockTransition('T1', expected_transition_type)
    mock_model = MockModel()
    
    # Try to create behavior (this will work if imports are correct)
    try:
        behavior = behavior_class(mock_trans, mock_model)
        type_name = behavior.get_type_name()
        
        # Check if mapping exists
        if type_name in type_name_map:
            mapped_type = type_name_map[type_name]
            
            # Check if it maps correctly
            if mapped_type == expected_transition_type:
                print(f"✓ {class_name}")
                print(f"    get_type_name() = '{type_name}'")
                print(f"    Maps to: '{mapped_type}'")
                print(f"    Expected: '{expected_transition_type}'")
                print(f"    STATUS: CORRECT")
            else:
                print(f"❌ {class_name}")
                print(f"    get_type_name() = '{type_name}'")
                print(f"    Maps to: '{mapped_type}'")
                print(f"    Expected: '{expected_transition_type}'")
                print(f"    STATUS: INCORRECT MAPPING")
                all_correct = False
        else:
            print(f"❌ {class_name}")
            print(f"    get_type_name() = '{type_name}'")
            print(f"    STATUS: MISSING FROM type_name_map")
            all_correct = False
    except Exception as e:
        print(f"❌ {class_name}")
        print(f"    ERROR creating behavior: {e}")
        all_correct = False
    
    print()

print("="*80)
if all_correct:
    print("✅ ALL TRANSITION TYPE MAPPINGS ARE CORRECT")
else:
    print("❌ SOME MAPPINGS ARE INCORRECT OR MISSING")
print("="*80)
