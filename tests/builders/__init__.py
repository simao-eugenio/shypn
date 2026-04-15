"""Test suite for builder pattern implementations.

Tests for Phase 3 quality improvements - fluent builder interfaces for
Petri net object construction.

Test modules:
- test_place_builder: PlaceBuilder with SHPN signal place support
- test_arc_builder: ArcBuilder for all 7 arc types (when implemented)
- test_transition_builder: TransitionBuilder for 5 behavior types (when implemented)
- test_petri_net_builder: PetriNetBuilder for complete models (when implemented)
- test_simulation_config_builder: SimulationConfigBuilder (when implemented)

Run all builder tests:
    pytest tests/builders/ -v

Run specific test module:
    pytest tests/builders/test_place_builder.py -v
"""

