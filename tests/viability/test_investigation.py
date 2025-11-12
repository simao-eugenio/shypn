"""Tests for investigation data structures."""
import pytest
from datetime import datetime
from shypn.ui.panels.viability.investigation import (
    InvestigationMode,
    InvestigationManager,
    LocalityInvestigation,
    SubnetInvestigation,
    Subnet,
    Dependency,
    Issue,
    Suggestion,
    BoundaryAnalysis,
    ConservationAnalysis
)
from tests.viability.conftest import MockTransition, MockLocality


def test_investigation_mode():
    """Test investigation mode enum."""
    assert InvestigationMode.SINGLE_LOCALITY.value == "single"
    assert InvestigationMode.SUBNET.value == "subnet"


def test_dependency():
    """Test dependency dataclass."""
    dep = Dependency(
        source_transition_id="T1",
        target_transition_id="T2",
        connecting_place_id="P3"
    )
    assert dep.source_transition_id == "T1"
    assert dep.target_transition_id == "T2"
    assert dep.connecting_place_id == "P3"
    assert "T1" in str(dep)
    assert "P3" in str(dep)
    assert "T2" in str(dep)


def test_subnet():
    """Test subnet dataclass."""
    subnet = Subnet()
    assert len(subnet) == 0
    
    subnet.transitions.add("T1")
    subnet.transitions.add("T2")
    subnet.places.add("P1")
    subnet.places.add("P2")
    
    assert len(subnet) == 2
    assert "T=2" in str(subnet)
    assert "P=2" in str(subnet)


def test_issue():
    """Test issue dataclass."""
    issue = Issue(
        category="structural",
        severity="error",
        message="Missing arc",
        element_id="T1"
    )
    assert issue.category == "structural"
    assert "🔴" in str(issue)
    assert "structural" in str(issue)


def test_suggestion():
    """Test suggestion dataclass."""
    sug = Suggestion(
        category="structural",
        action="add_arc",
        message="Add arc T1→P3",
        parameters={"source": "T1", "target": "P3"}
    )
    assert sug.action == "add_arc"
    assert "add_arc" in str(sug)


def test_boundary_analysis():
    """Test boundary analysis."""
    ba = BoundaryAnalysis()
    assert not ba.has_issues()
    
    ba.accumulating_places.append("P1")
    assert ba.has_issues()


def test_conservation_analysis():
    """Test conservation analysis."""
    ca = ConservationAnalysis()
    assert not ca.has_issues()
    
    ca.violated_invariants.append("ATP+ADP=const")
    assert ca.has_issues()
    
    ca2 = ConservationAnalysis(mass_balance_ok=False)
    assert ca2.has_issues()


def test_locality_investigation():
    """Test locality investigation."""
    t1 = MockTransition(id="T1")
    loc = MockLocality(
        transition=t1,
        input_places=[],
        output_places=[],
        input_arcs=[],
        output_arcs=[]
    )
    
    inv = LocalityInvestigation(
        transition_id="T1",
        locality=loc,
        timestamp=datetime.now()
    )
    
    assert inv.transition_id == "T1"
    assert inv.mode == InvestigationMode.SINGLE_LOCALITY
    assert len(inv.issues) == 0
    assert "T1" in str(inv)


def test_subnet_investigation():
    """Test subnet investigation."""
    t1 = MockTransition(id="T1")
    t2 = MockTransition(id="T2")
    
    loc1 = MockLocality(t1, [], [], [], [])
    loc2 = MockLocality(t2, [], [], [], [])
    
    inv1 = LocalityInvestigation("T1", loc1, datetime.now())
    inv2 = LocalityInvestigation("T2", loc2, datetime.now())
    
    subnet = Subnet()
    subnet.transitions.add("T1")
    subnet.transitions.add("T2")
    
    subnet_inv = SubnetInvestigation(
        localities=[inv1, inv2],
        subnet=subnet,
        timestamp=datetime.now()
    )
    
    assert len(subnet_inv.localities) == 2
    assert len(subnet_inv.subnet) == 2
    assert subnet_inv.transition_ids == ["T1", "T2"]


def test_investigation_manager_single():
    """Test investigation manager with single locality."""
    manager = InvestigationManager()
    
    t1 = MockTransition(id="T1")
    loc = MockLocality(t1, [], [], [], [])
    
    inv = manager.create_investigation(t1, loc)
    
    assert inv.transition_id == "T1"
    assert len(manager.list_investigations()) == 1
    assert "locality_T1" in manager.list_investigations()
    
    retrieved = manager.get_investigation("locality_T1")
    assert retrieved is inv
    
    assert manager.remove_investigation("locality_T1")
    assert len(manager.list_investigations()) == 0


def test_investigation_manager_subnet():
    """Test investigation manager with subnet."""
    manager = InvestigationManager()
    
    t1 = MockTransition(id="T1")
    t2 = MockTransition(id="T2")
    loc1 = MockLocality(t1, [], [], [], [])
    loc2 = MockLocality(t2, [], [], [], [])
    
    subnet = Subnet()
    subnet.transitions.add("T1")
    subnet.transitions.add("T2")
    
    inv = manager.create_subnet_investigation([t1, t2], [loc1, loc2], subnet)
    
    assert len(inv.localities) == 2
    assert len(manager.list_investigations()) == 1
    
    key = list(manager.list_investigations())[0]
    assert "subnet" in key


def test_investigation_manager_clear():
    """Test clearing all investigations."""
    manager = InvestigationManager()
    
    t1 = MockTransition(id="T1")
    loc = MockLocality(t1, [], [], [], [])
    
    manager.create_investigation(t1, loc)
    assert len(manager.list_investigations()) == 1
    
    manager.clear_all()
    assert len(manager.list_investigations()) == 0
