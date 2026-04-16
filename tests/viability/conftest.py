"""Pytest fixtures for viability tests."""
import pytest
from dataclasses import dataclass
from typing import List, Set, Optional


@dataclass
class MockPlace:
    """Mock place for testing."""
    id: str
    compound_id: Optional[str] = None
    label: Optional[str] = None
    tokens: float = 0.0
    initial_marking: float = 0.0


@dataclass
class MockTransition:
    """Mock transition for testing."""
    id: str
    reaction_id: Optional[str] = None
    reaction_name: Optional[str] = None
    label: Optional[str] = None
    rate: float = 1.0


@dataclass
class MockArc:
    """Mock arc for testing."""
    id: str
    source: str  # place or transition id
    target: str  # transition or place id
    weight: float = 1.0


@dataclass
class MockLocality:
    """Mock locality for testing."""
    transition: MockTransition
    input_places: List[MockPlace]
    output_places: List[MockPlace]
    input_arcs: List[MockArc]
    output_arcs: List[MockArc]


@pytest.fixture
def simple_locality():
    """Create a simple locality for testing."""
    t1 = MockTransition(id="T1", label="Hexokinase")
    p1 = MockPlace(id="P1", label="Glucose", tokens=10.0)
    p2 = MockPlace(id="P2", label="ATP", tokens=5.0)
    p3 = MockPlace(id="P3", label="G6P", tokens=0.0)
    p4 = MockPlace(id="P4", label="ADP", tokens=0.0)
    
    a1 = MockArc(id="A1", source="P1", target="T1", weight=1.0)
    a2 = MockArc(id="A2", source="P2", target="T1", weight=1.0)
    a3 = MockArc(id="A3", source="T1", target="P3", weight=1.0)
    a4 = MockArc(id="A4", source="T1", target="P4", weight=1.0)
    
    return MockLocality(
        transition=t1,
        input_places=[p1, p2],
        output_places=[p3, p4],
        input_arcs=[a1, a2],
        output_arcs=[a3, a4]
    )


@pytest.fixture
def multiple_localities(simple_locality):
    """Create multiple localities for subnet testing."""
    # Locality 1: T1 (already created)
    loc1 = simple_locality
    
    # Locality 2: T2 uses P3 (output of T1) as input
    t2 = MockTransition(id="T2", label="Phosphoglucoisomerase")
    p3 = loc1.output_places[0]  # Shared place
    p5 = MockPlace(id="P5", label="F6P", tokens=0.0)
    
    a5 = MockArc(id="A5", source="P3", target="T2", weight=1.0)
    a6 = MockArc(id="A6", source="T2", target="P5", weight=1.0)
    
    loc2 = MockLocality(
        transition=t2,
        input_places=[p3],
        output_places=[p5],
        input_arcs=[a5],
        output_arcs=[a6]
    )
    
    return [loc1, loc2]
