#!/usr/bin/env python3
"""
Test ReplicateRunner basic functionality

Quick validation that ReplicateRunner works. Uses mock model for testing.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parents[3] / 'src'))

from shypn.engine.simulation.replicate_runner import ReplicateRunner


class MockPlace:
    """Mock place for testing."""
    def __init__(self, id, tokens=0):
        self.id = id
        self.name = id
        self.tokens = tokens
        self.initial_tokens = tokens
        
        
class MockTransition:
    """Mock transition for testing."""
    def __init__(self, id):
        self.id = id
        self.name = id
        self.transition_type = 'stochastic'
        self.rate = 1.0


class MockModel:
    """Mock model for testing."""
    def __init__(self):
        self.places = [MockPlace(f'S{i}', tokens=100) for i in range(3)]
        self.transitions = [MockTransition(f'T{i}') for i in range(2)]
        self.arcs = []


def test_replicate_runner():
    """Test ReplicateRunner with mock model."""
    print("Creating mock model...")
    model = MockModel()
    print(f"  ✓ Model: {len(model.places)} places, {len(model.transitions)} transitions")
    
    print("\nInitializing ReplicateRunner...")
    runner = ReplicateRunner(model)
    print("  ✓ ReplicateRunner created")
    
    # Test initialization only for now
    print("\n" + "="*60)
    print("✅ BASIC INITIALIZATION TEST PASSED!")
    print("="*60)
    print("\nReplicateRunner class loaded successfully.")
    print("Full integration test requires SimulationController setup.")


if __name__ == '__main__':
    test_replicate_runner()
