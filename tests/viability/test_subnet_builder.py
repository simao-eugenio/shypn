"""Tests for subnet builder."""
import pytest
from shypn.ui.panels.viability.subnet_builder import SubnetBuilder
from shypn.ui.panels.viability.investigation import Subnet


def test_build_single_locality_subnet(simple_locality):
    """Test building subnet from single locality."""
    builder = SubnetBuilder()
    subnet = builder.build_subnet([simple_locality])
    
    assert len(subnet.transitions) == 1
    assert "T1" in subnet.transitions
    
    assert len(subnet.places) == 4  # P1, P2, P3, P4
    assert len(subnet.arcs) == 4
    
    # All places are boundary in single locality
    assert len(subnet.boundary_places) == 4
    assert len(subnet.internal_places) == 0
    
    # No dependencies in single locality
    assert len(subnet.dependencies) == 0


def test_build_empty_subnet():
    """Test building subnet from empty list."""
    builder = SubnetBuilder()
    subnet = builder.build_subnet([])
    
    assert len(subnet.transitions) == 0
    assert len(subnet.places) == 0


def test_build_multi_locality_subnet(multiple_localities):
    """Test building subnet from multiple localities."""
    builder = SubnetBuilder()
    subnet = builder.build_subnet(multiple_localities)
    
    assert len(subnet.transitions) == 2
    assert "T1" in subnet.transitions
    assert "T2" in subnet.transitions
    
    # P1, P2, P3, P4, P5 = 5 places
    assert len(subnet.places) == 5
    
    # P3 is internal (connects T1 and T2)
    # P1, P2, P4, P5 are boundary
    assert "P3" in subnet.internal_places or "P3" in subnet.boundary_places
    
    # Should have dependency: T1 → P3 → T2
    assert len(subnet.dependencies) >= 1
    
    # Check dependency structure
    deps = subnet.dependencies
    has_t1_t2_dep = any(
        d.source_transition_id == "T1" and 
        d.target_transition_id == "T2" and
        d.connecting_place_id == "P3"
        for d in deps
    )
    assert has_t1_t2_dep


def test_disconnected_localities_rejected():
    """Test that disconnected localities cannot form subnet."""
    from tests.viability.conftest import MockTransition, MockPlace, MockArc, MockLocality
    
    # Create two completely disconnected localities
    t1 = MockTransition(id="T1")
    p1 = MockPlace(id="P1")
    p2 = MockPlace(id="P2")
    a1 = MockArc(id="A1", source="P1", target="T1")
    a2 = MockArc(id="A2", source="T1", target="P2")
    
    loc1 = MockLocality(t1, [p1], [p2], [a1], [a2])
    
    # Second locality with completely different places
    t2 = MockTransition(id="T2")
    p3 = MockPlace(id="P3")
    p4 = MockPlace(id="P4")
    a3 = MockArc(id="A3", source="P3", target="T2")
    a4 = MockArc(id="A4", source="T2", target="P4")
    
    loc2 = MockLocality(t2, [p3], [p4], [a3], [a4])
    
    # Should raise ValueError for disconnected localities
    builder = SubnetBuilder()
    with pytest.raises(ValueError, match="not connected"):
        builder.build_subnet([loc1, loc2])


def test_are_localities_connected(multiple_localities):
    """Test connectivity check for localities."""
    builder = SubnetBuilder()
    
    # multiple_localities has T1 and T2 sharing P3
    assert builder._are_localities_connected(multiple_localities) is True
    
    # Single locality is always connected
    assert builder._are_localities_connected([multiple_localities[0]]) is True
    
    # Empty list is connected
    assert builder._are_localities_connected([]) is True


def test_get_all_places(simple_locality):
    """Test getting all places from locality."""
    builder = SubnetBuilder()
    places = builder._get_all_places(simple_locality)
    
    assert "P1" in places
    assert "P2" in places
    assert "P3" in places
    assert "P4" in places
    assert len(places) == 4


def test_find_connected_components():
    """Test finding connected components among localities."""
    from tests.viability.conftest import MockTransition, MockPlace, MockArc, MockLocality
    
    # Create 3 localities: T1-T2 connected, T3 isolated
    t1 = MockTransition(id="T1")
    p1 = MockPlace(id="P1")
    p2 = MockPlace(id="P2")
    loc1 = MockLocality(t1, [p1], [p2], [], [])
    
    t2 = MockTransition(id="T2")
    p3 = MockPlace(id="P3")
    # T2 shares P2 with T1
    loc2 = MockLocality(t2, [p2], [p3], [], [])
    
    t3 = MockTransition(id="T3")
    p4 = MockPlace(id="P4")
    p5 = MockPlace(id="P5")
    # T3 is isolated (no shared places)
    loc3 = MockLocality(t3, [p4], [p5], [], [])
    
    builder = SubnetBuilder()
    components = builder.find_connected_components([loc1, loc2, loc3])
    
    # Should have 2 components: [0,1] and [2]
    assert len(components) == 2
    assert [0, 1] in components or [1, 0] in components
    assert [2] in components


def test_classify_places(simple_locality):
    """Test place classification."""
    builder = SubnetBuilder()
    
    # In single locality, all places are considered boundary
    # (since they connect to transitions outside the subnet - none exist)
    places = {"P1", "P2", "P3", "P4"}
    transitions = {"T1"}
    
    boundary, internal = builder.classify_places(places, transitions, [simple_locality])
    
    # With proper locality info, classification depends on arcs
    assert isinstance(boundary, set)
    assert isinstance(internal, set)
    assert len(boundary) + len(internal) == len(places)


def test_find_dependencies(multiple_localities):
    """Test finding dependencies between localities."""
    builder = SubnetBuilder()
    subnet = builder.build_subnet(multiple_localities)
    
    deps = builder.find_dependencies(subnet, multiple_localities)
    
    assert len(deps) >= 1
    
    # T1 produces P3, T2 consumes P3
    t1_to_t2 = [d for d in deps 
                if d.source_transition_id == "T1" 
                and d.target_transition_id == "T2"]
    
    assert len(t1_to_t2) >= 1
    assert t1_to_t2[0].connecting_place_id == "P3"


def test_analyze_topology(multiple_localities):
    """Test topology analysis."""
    builder = SubnetBuilder()
    subnet = builder.build_subnet(multiple_localities)
    
    topo = builder.analyze_topology(subnet)
    
    assert topo['num_transitions'] == 2
    assert topo['num_places'] == 5
    assert topo['num_dependencies'] >= 1
    assert topo['is_connected'] is True
    assert 0 <= topo['boundary_ratio'] <= 1


def test_build_place_transition_map(simple_locality):
    """Test building place-transition map."""
    builder = SubnetBuilder()
    place_map = builder._build_place_transition_map([simple_locality])
    
    assert "P1" in place_map
    assert "T1" in place_map["P1"]
    
    assert "P3" in place_map
    assert "T1" in place_map["P3"]


def test_identify_boundary_io(multiple_localities):
    """Test identifying boundary inputs and outputs."""
    builder = SubnetBuilder()
    subnet = builder.build_subnet(multiple_localities)
    
    inputs, outputs = builder._identify_boundary_io(subnet, multiple_localities)
    
    # P1, P2 are inputs (to T1)
    # P5 is output (from T2)
    # P3 is intermediate (not strictly boundary I/O)
    # P4 is output (from T1)
    
    assert isinstance(inputs, list)
    assert isinstance(outputs, list)
    
    # Check that P1 or P2 are in inputs
    assert any(p in inputs for p in ["P1", "P2"])
