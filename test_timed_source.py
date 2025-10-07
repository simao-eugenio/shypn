#!/usr/bin/env python3
"""Test script to verify timed source transition behavior."""

# Test: Create a simple net with a timed source transition and a place
# Expected: Timed source should produce tokens without consuming any

class MockPlace:
    """Mock place for testing."""
    def __init__(self, id, tokens):
        self.id = id
        self.tokens = tokens
    
    def set_tokens(self, value):
        self.tokens = value

class MockTransition:
    """Mock transition for testing."""
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.transition_type = 'timed'
        self.is_source = True  # THIS IS THE KEY - source transition
        self.is_sink = False
        self.properties = {
            'earliest': 1.0,
            'latest': 1.0
        }

class MockArc:
    """Mock arc for testing."""
    def __init__(self, id, source, target, weight):
        self.id = id
        self.source = source  # Reference to source object
        self.target = target  # Reference to target object
        self.source_id = source.id if hasattr(source, 'id') else None
        self.target_id = target.id if hasattr(target, 'id') else None
        self.weight = weight
        self.kind = 'normal'

class MockModel:
    """Mock model for testing."""
    def __init__(self):
        self.places = {}
        self.transitions = {}
        self.arcs = {}
        self.logical_time = 0.0
    
    def add_place(self, place):
        self.places[place.id] = place
    
    def add_transition(self, transition):
        self.transitions[transition.id] = transition
    
    def add_arc(self, arc):
        self.arcs[arc.id] = arc

# Create test scenario
print("=" * 60)
print("Testing Timed Source Transition")
print("=" * 60)

# Setup: Timed Transition T1 (source) -> Place P1 with 0 tokens
model = MockModel()

place1 = MockPlace(1, 0)  # Start with 0 tokens
model.add_place(place1)

transition1 = MockTransition(1, "T1")
model.add_transition(transition1)

# Arc from Transition to Place (output arc for the transition)
arc1 = MockArc(1, transition1, place1, 3)  # Produces 3 tokens
model.add_arc(arc1)

print(f"\nInitial State:")
print(f"  Place P1: {place1.tokens} tokens")
print(f"  Transition T1: is_source={transition1.is_source}, type={transition1.transition_type}")

# Import behavior
import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.engine.timed_behavior import TimedBehavior

# Create behavior
behavior = TimedBehavior(transition1, model)

print(f"\nBehavior created: {behavior.get_type_name()}")

# Set enablement time (simulate that transition became enabled)
behavior.set_enablement_time(0.0)
model.logical_time = 1.0  # Advance time to allow firing

print(f"Enablement time set to: {behavior.get_enablement_time()}")
print(f"Model time: {model.logical_time}")

# Check if can fire
can_fire, reason = behavior.can_fire()
print(f"\nCan fire? {can_fire} - Reason: {reason}")

if can_fire:
    # Get arcs
    input_arcs = behavior.get_input_arcs()
    output_arcs = behavior.get_output_arcs()
    
    print(f"\nInput arcs: {len(input_arcs)}")
    for arc in input_arcs:
        print(f"  Arc {arc.id}: P{arc.source_id} -> T{arc.target_id}, weight={arc.weight}")
    
    print(f"Output arcs: {len(output_arcs)}")
    for arc in output_arcs:
        print(f"  Arc {arc.id}: T{arc.source_id} -> P{arc.target_id}, weight={arc.weight}")
    
    # Fire the transition
    print(f"\n{'='*60}")
    print("FIRING TRANSITION")
    print(f"{'='*60}")
    
    success, details = behavior.fire(input_arcs, output_arcs)
    
    print(f"\nFiring result: {success}")
    print(f"Details: {details}")
    
    print(f"\nFinal State:")
    print(f"  Place P1: {place1.tokens} tokens")
    
    print(f"\nExpected: 3 tokens (0 + 3)")
    print(f"Actual: {place1.tokens} tokens")
    
    if place1.tokens == 3:
        print("\n✅ TEST PASSED: Source correctly produced tokens without consuming")
    else:
        print(f"\n❌ TEST FAILED: Expected 3 tokens, got {place1.tokens}")
else:
    print(f"\n❌ TEST FAILED: Transition cannot fire - {reason}")
