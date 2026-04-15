"""Test suite for ArcBuilder - Fluent interface for Arc construction.

Tests cover:
- All 7 arc types (normal, curved, inhibitor, test, signal flow)
- Source and target configuration (by ID and by object)
- Weight configuration (W and W_s for SHPN)
- Type-specific properties (threshold, control points)
- Validation and error handling
- Complex real-world examples
"""

import pytest
from shypn.builders.arc_builder import ArcBuilder
from shypn.builders.place_builder import PlaceBuilder
from shypn.netobjs.arc import Arc
from shypn.netobjs.curved_arc import CurvedArc
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc
from shypn.netobjs.test_arc import TestArc
from shypn.netobjs.signal_flow_arc import SignalFlowArc
from shypn.netobjs.curved_signal_flow_arc import CurvedSignalFlowArc
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition


# ========== Fixtures ==========

@pytest.fixture
def simple_place():
    """Create a simple place for testing."""
    return Place(x=100, y=100, id="P1", name="P1")


@pytest.fixture
def signal_place():
    """Create a signal place for testing."""
    place = Place(x=150, y=150, id="ATP", name="ATP")
    place.is_signal_place = True
    return place


@pytest.fixture
def simple_transition():
    """Create a simple transition for testing."""
    return Transition(x=200, y=200, id="T1", name="T1")


@pytest.fixture
def resolve_dict(simple_place, signal_place, simple_transition):
    """Create resolve_refs dictionary for ID-based arc construction."""
    return {
        "P1": simple_place,
        "ATP": signal_place,
        "T1": simple_transition,
    }


# ========== Test Basic Arc Construction ==========

class TestArcBuilderBasics:
    """Test basic arc construction functionality."""
    
    def test_normal_arc_with_objects(self, simple_place, simple_transition):
        """Test normal arc with object references."""
        arc = (ArcBuilder()
               .from_place(simple_place)
               .to_transition(simple_transition)
               .with_weight(2)
               .build())
        
        assert isinstance(arc, Arc)
        assert arc.source == simple_place
        assert arc.target == simple_transition
        assert arc.weight == 2.0
        assert arc.arc_type == "normal"
    
    def test_normal_arc_with_ids(self, resolve_dict):
        """Test normal arc with ID-based references."""
        arc = (ArcBuilder()
               .from_place("P1")
               .to_transition("T1")
               .with_weight(3)
               .build(resolve_dict))
        
        assert isinstance(arc, Arc)
        assert arc.source.id == "P1"
        assert arc.target.id == "T1"
        assert arc.weight == 3.0
    
    def test_arc_reverse_direction(self, simple_transition, simple_place):
        """Test arc from transition to place."""
        arc = (ArcBuilder()
               .from_transition(simple_transition)
               .to_place(simple_place)
               .with_weight(1)
               .build())
        
        assert arc.source == simple_transition
        assert arc.target == simple_place
    
    def test_arc_with_default_weight(self, simple_place, simple_transition):
        """Test arc uses default weight of 1.0 when not specified."""
        arc = (ArcBuilder()
               .from_place(simple_place)
               .to_transition(simple_transition)
               .build())
        
        assert arc.weight == 1.0
    
    def test_missing_source_raises_error(self, simple_transition):
        """Test that missing source raises ValueError."""
        with pytest.raises(ValueError, match="must have a source"):
            (ArcBuilder()
             .to_transition(simple_transition)
             .build())
    
    def test_missing_target_raises_error(self, simple_place):
        """Test that missing target raises ValueError."""
        with pytest.raises(ValueError, match="must have a target"):
            (ArcBuilder()
             .from_place(simple_place)
             .build())
    
    def test_negative_weight_raises_error(self, simple_place, simple_transition):
        """Test that negative weight raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            (ArcBuilder()
             .from_place(simple_place)
             .to_transition(simple_transition)
             .with_weight(-1)
             .build())


# ========== Test Arc Type Selection ==========

class TestArcBuilderTypes:
    """Test all 7 arc type selections."""
    
    def test_normal_arc(self, simple_place, simple_transition):
        """Test normal arc (default type)."""
        arc = (ArcBuilder()
               .from_place(simple_place)
               .to_transition(simple_transition)
               .build())
        
        assert type(arc) == Arc
        assert arc.arc_type == "normal"
    
    def test_curved_arc(self, simple_place, simple_transition):
        """Test curved arc."""
        arc = (ArcBuilder()
               .from_place(simple_place)
               .to_transition(simple_transition)
               .as_curved()
               .build())
        
        assert isinstance(arc, CurvedArc)
        assert arc.arc_type == "curved_arc"
    
    def test_inhibitor_arc(self, simple_place, simple_transition):
        """Test inhibitor arc."""
        arc = (ArcBuilder()
               .from_place(simple_place)
               .to_transition(simple_transition)
               .as_inhibitor()
               .with_threshold(10)
               .build())
        
        assert isinstance(arc, InhibitorArc)
        assert arc.arc_type == "inhibitor"
        assert arc.threshold == 10
    
    def test_curved_inhibitor_arc(self, simple_place, simple_transition):
        """Test curved inhibitor arc."""
        arc = (ArcBuilder()
               .from_place(simple_place)
               .to_transition(simple_transition)
               .as_inhibitor()
               .as_curved()
               .with_threshold(5)
               .build())
        
        assert isinstance(arc, CurvedInhibitorArc)
        assert arc.arc_type == "curved_inhibitor_arc"
        assert arc.threshold == 5
    
    def test_test_arc(self, simple_place, simple_transition):
        """Test test arc (non-consuming catalyst)."""
        arc = (ArcBuilder()
               .from_place(simple_place)
               .to_transition(simple_transition)
               .as_test()
               .with_weight(1)
               .build())
        
        assert isinstance(arc, TestArc)
        assert arc.arc_type == "test"
    
    def test_signal_flow_arc(self, signal_place, simple_transition):
        """Test signal flow arc (SHPN)."""
        arc = (ArcBuilder()
               .from_place(signal_place)
               .to_transition(simple_transition)
               .as_signal_flow()
               .build())
        
        assert isinstance(arc, SignalFlowArc)
        assert arc.arc_type == "signal_flow"
    
    def test_curved_signal_flow_arc(self, signal_place, simple_transition):
        """Test curved signal flow arc (SHPN)."""
        arc = (ArcBuilder()
               .from_place(signal_place)
               .to_transition(simple_transition)
               .as_signal_flow()
               .as_curved()
               .build())
        
        assert isinstance(arc, CurvedSignalFlowArc)
        # arc_type depends on direction; opposite direction yields 'curved_opposite_signal_flow'
        assert arc.arc_type in ["curved_arc", "curved_signal_flow", "curved_opposite_signal_flow"]


# ========== Test SHPN Signal Flow Features ==========

class TestArcBuilderSignalFlow:
    """Test SHPN signal flow arc functionality."""
    
    def test_signal_weight(self, signal_place, simple_transition):
        """Test signal weight W_s setting."""
        arc = (ArcBuilder()
               .from_place(signal_place)
               .to_transition(simple_transition)
               .as_signal_flow()
               .with_signal_weight(0.17)
               .build())
        
        # Signal weight stored in properties (or attribute if added to class)
        assert arc.properties.get('signal_weight') == 0.17 or \
               getattr(arc, 'signal_weight', None) == 0.17
    
    def test_dual_arc_weights(self, signal_place, simple_transition):
        """Test dual arc semantics (both W and W_s).
        
        For SignalFlowArc, the constructor weight parameter IS W_s (the signal
        weight / commitment quota). When with_signal_weight() is used, the
        builder correctly passes it as the arc's weight.
        """
        arc = (ArcBuilder()
               .from_place(signal_place)
               .to_transition(simple_transition)
               .as_signal_flow()
               .with_weight(2.0)  # Normal weight W (stored in builder, not used for signal flow)
               .with_signal_weight(0.17)  # Signal weight W_s → becomes arc.weight
               .build())
        
        # For signal flow arcs, weight IS W_s
        assert arc.weight == 0.17  # W_s used as constructor weight
    
    def test_signal_weight_must_be_positive(self, signal_place, simple_transition):
        """Test that signal weight must be positive."""
        with pytest.raises(ValueError, match="must be positive"):
            (ArcBuilder()
             .from_place(signal_place)
             .to_transition(simple_transition)
             .as_signal_flow()
             .with_signal_weight(0)  # Zero not allowed
             .build())
    
    def test_bacillus_subtilis_commitment_arc(self, simple_transition):
        """Test B. subtilis ATP commitment arc (canonical SHPN example).
        
        From formalism:
        - ATP signal place at Layer 0
        - Commitment transition with θ(t) = 2.21 mM
        - Signal weight W_s = 0.17 mM
        - → M_commit = 2.21 + 0.17 = 2.38 mM
        """
        # Create ATP signal place with proper initialization
        atp_place = Place(x=100, y=100, id="ATP", name="ATP")
        atp_place.is_signal_place = True
        
        # Create commitment arc
        arc = (ArcBuilder()
               .from_place(atp_place)
               .to_transition(simple_transition)
               .as_signal_flow()
               .with_signal_weight(0.17)  # Decision quota
               .with_label("ATP → Commitment")
               .with_metadata(
                   source="B. subtilis sporulation",
                   commitment_threshold=2.38  # θ + W_s
               )
               .build())
        
        assert isinstance(arc, SignalFlowArc)
        assert arc.metadata["commitment_threshold"] == 2.38


# ========== Test Inhibitor Arc Validation ==========

class TestArcBuilderInhibitor:
    """Test inhibitor arc specific functionality."""
    
    def test_inhibitor_direction_valid(self, simple_place, simple_transition):
        """Test inhibitor arc with valid Place → Transition direction."""
        arc = (ArcBuilder()
               .from_place(simple_place)
               .to_transition(simple_transition)
               .as_inhibitor()
               .build())
        
        assert isinstance(arc, InhibitorArc)
    
    def test_inhibitor_direction_invalid_raises_error(self, simple_transition, simple_place):
        """Test inhibitor arc with invalid Transition → Place direction."""
        with pytest.raises(ValueError, match="must go from Place to Transition"):
            (ArcBuilder()
             .from_transition(simple_transition)  # Wrong direction!
             .to_place(simple_place)
             .as_inhibitor()
             .build())
    
    def test_inhibitor_with_threshold(self, simple_place, simple_transition):
        """Test inhibitor arc threshold setting."""
        arc = (ArcBuilder()
               .from_place(simple_place)
               .to_transition(simple_transition)
               .as_inhibitor()
               .with_threshold(15)
               .build())
        
        assert arc.threshold == 15


# ========== Test Curved Arc Features ==========

class TestArcBuilderCurved:
    """Test curved arc functionality."""
    
    def test_curved_with_control_points(self, simple_place, simple_transition):
        """Test curved arc with explicit control points."""
        arc = (ArcBuilder()
               .from_place(simple_place)
               .to_transition(simple_transition)
               .as_curved()
               .with_control_points([(160, 180), (170, 190)])
               .build())
        
        assert isinstance(arc, CurvedArc)
        assert arc.control_points == [(160, 180), (170, 190)]
    
    def test_curved_with_offset(self, simple_place, simple_transition):
        """Test curved arc with control offset."""
        arc = (ArcBuilder()
               .from_place(simple_place)
               .to_transition(simple_transition)
               .as_curved()
               .with_control_offset(20, 30)
               .build())
        
        assert isinstance(arc, CurvedArc)
        assert arc.control_offset_x == 20
        assert arc.control_offset_y == 30
    
    def test_control_points_without_curved_raises_error(self, simple_place, simple_transition):
        """Test control points require .as_curved()."""
        with pytest.raises(ValueError, match="require .as_curved"):
            (ArcBuilder()
             .from_place(simple_place)
             .to_transition(simple_transition)
             .with_control_points([(160, 180)])  # Missing .as_curved()
             .build())


# ========== Test Optional Properties ==========

class TestArcBuilderProperties:
    """Test optional arc properties."""
    
    def test_arc_with_label(self, simple_place, simple_transition):
        """Test arc label setting."""
        arc = (ArcBuilder()
               .from_place(simple_place)
               .to_transition(simple_transition)
               .with_label("Glycolysis")
               .build())
        
        assert arc.label == "Glycolysis"
    
    def test_arc_with_id_and_name(self, simple_place, simple_transition):
        """Test custom ID and name."""
        arc = (ArcBuilder()
               .from_place(simple_place)
               .to_transition(simple_transition)
               .with_id("A_custom")
               .with_name("CustomArc")
               .build())
        
        assert arc.id == "A_custom"
        assert arc.name == "CustomArc"
    
    def test_arc_with_color(self, simple_place, simple_transition):
        """Test custom color."""
        arc = (ArcBuilder()
               .from_place(simple_place)
               .to_transition(simple_transition)
               .with_color(0.5, 0.5, 0.5)
               .build())
        
        assert arc.color == (0.5, 0.5, 0.5)
    
    def test_arc_with_custom_property(self, simple_place, simple_transition):
        """Test custom properties."""
        arc = (ArcBuilder()
               .from_place(simple_place)
               .to_transition(simple_transition)
               .with_property("formula", "2*[ATP]")
               .with_property("reversible", False)
               .build())
        
        assert arc.properties["formula"] == "2*[ATP]"
        assert arc.properties["reversible"] is False
    
    def test_arc_with_metadata(self, simple_place, simple_transition):
        """Test metadata."""
        arc = (ArcBuilder()
               .from_place(simple_place)
               .to_transition(simple_transition)
               .with_metadata(
                   source="KEGG",
                   reaction=True,
                   stoichiometry=2
               )
               .build())
        
        assert arc.metadata["source"] == "KEGG"
        assert arc.metadata["reaction"] is True
        assert arc.metadata["stoichiometry"] == 2


# ========== Test Validation and Error Handling ==========

class TestArcBuilderValidation:
    """Test validation and error handling."""
    
    def test_mutually_exclusive_types(self, simple_place, simple_transition):
        """Test that inhibitor + test is invalid."""
        with pytest.raises(ValueError, match="mutually exclusive"):
            (ArcBuilder()
             .from_place(simple_place)
             .to_transition(simple_transition)
             .as_inhibitor()
             .as_test()  # Cannot combine!
             .build())
    
    def test_inhibitor_and_signal_flow_exclusive(self, signal_place, simple_transition):
        """Test that inhibitor + signal_flow is invalid."""
        with pytest.raises(ValueError, match="mutually exclusive"):
            (ArcBuilder()
             .from_place(signal_place)
             .to_transition(simple_transition)
             .as_inhibitor()
             .as_signal_flow()  # Cannot combine!
             .build())
    
    def test_unresolvable_id_raises_error(self, resolve_dict):
        """Test that unresolvable ID raises ValueError."""
        with pytest.raises(ValueError, match="Cannot resolve ID"):
            (ArcBuilder()
             .from_place("UNKNOWN_ID")  # Not in resolve_dict
             .to_transition("T1")
             .build(resolve_dict))
    
    def test_missing_resolve_dict_raises_error(self):
        """Test that ID without resolve_dict raises ValueError."""
        with pytest.raises(ValueError, match="without resolve_refs"):
            (ArcBuilder()
             .from_place("P1")  # ID string
             .to_transition("T1")
             .build())  # No resolve_dict!


# ========== Test Complex Real-World Examples ==========

class TestArcBuilderComplexExamples:
    """Test complex real-world arc configurations."""
    
    def test_enzyme_catalysis_test_arc(self, simple_place, simple_transition):
        """Test enzyme catalysis using test arc (non-consuming)."""
        # Enzyme place
        enzyme = Place(x=50, y=50, id="hexokinase", name="hexokinase")
        
        # Catalytic arc (enzyme reads substrate without consuming itself)
        arc = (ArcBuilder()
               .from_place(enzyme)
               .to_transition(simple_transition)
               .as_test()
               .with_weight(1)  # Requires 1 enzyme present
               .with_label("Catalysis")
               .with_metadata(
                   enzyme_type="kinase",
                   km=5.0,
                   vmax=10.0
               )
               .build())
        
        assert isinstance(arc, TestArc)
        assert arc.weight == 1
        assert arc.metadata["enzyme_type"] == "kinase"
    
    def test_feedback_inhibition_arc(self, simple_place, simple_transition):
        """Test product inhibition using inhibitor arc."""
        # Product place that inhibits its own production
        product = Place(x=300, y=100, id="product", name="product")
        
        # Inhibitor arc (high product disables production)
        arc = (ArcBuilder()
               .from_place(product)
               .to_transition(simple_transition)
               .as_inhibitor()
               .as_curved()  # Curved for visual clarity (feedback loop)
               .with_threshold(100)  # Inhibits when product > 100
               .with_control_offset(30, -20)
               .with_label("Feedback inhibition")
               .build())
        
        assert isinstance(arc, CurvedInhibitorArc)
        assert arc.threshold == 100
    
    def test_multilayer_signal_hierarchy(self):
        """Test signal flow arcs in multi-layer hierarchy (B. subtilis complete).
        
        Four-layer architecture:
        - Layer 0: ATP (metabolism)
        - Layer 1: CodY (sensing)
        - Layer 2: Spo0A (integration)
        - Layer 3: sigmaF (execution)
        """
        # Layer 0: ATP signal
        atp = Place(x=100, y=100, id="ATP", name="ATP")
        atp.is_signal_place = True
        
        # Layer 1: CodY signal
        cody = Place(x=200, y=100, id="CodY", name="CodY")
        cody.is_signal_place = True
        
        # Transitions
        t_sense = Transition(x=150, y=100, id="sense", name="sense")
        
        # Layer 0 → 1 signal flow (ATP enables sensing)
        arc_atp_sense = (ArcBuilder()
                         .from_place(atp)
                         .to_transition(t_sense)
                         .as_signal_flow()
                         .with_signal_weight(0.5)  # ATP commitment quota
                         .with_label("Energy gating")
                         .build())
        
        arc_sense_cody = (ArcBuilder()
                          .from_transition(t_sense)
                          .to_place(cody)
                          .as_signal_flow()
                          .with_signal_weight(1.0)  # Produces CodY signal
                          .build())
        
        assert isinstance(arc_atp_sense, SignalFlowArc)
        assert isinstance(arc_sense_cody, SignalFlowArc)
        assert arc_atp_sense.properties.get('signal_weight') == 0.5 or \
               getattr(arc_atp_sense, 'signal_weight', None) == 0.5


# ========== Test Repr ==========

class TestArcBuilderRepr:
    """Test __repr__ for debugging."""
    
    def test_repr_normal_arc(self, simple_place, simple_transition):
        """Test repr for normal arc."""
        builder = (ArcBuilder()
                   .from_place(simple_place)
                   .to_transition(simple_transition)
                   .with_weight(2))
        repr_str = repr(builder)
        
        assert "P1" in repr_str
        assert "T1" in repr_str
        assert "normal" in repr_str
        assert "W=2" in repr_str
    
    def test_repr_signal_flow_arc(self, signal_place, simple_transition):
        """Test repr for signal flow arc."""
        builder = (ArcBuilder()
                   .from_place(signal_place)
                   .to_transition(simple_transition)
                   .as_signal_flow()
                   .with_signal_weight(0.17))
        repr_str = repr(builder)
        
        assert "ATP" in repr_str
        assert "signal_flow" in repr_str
        assert "W_s=0.17" in repr_str


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])

