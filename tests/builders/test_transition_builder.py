"""Test suite for TransitionBuilder - Fluent interface for Transition construction.

Tests cover:
- All 5 transition types (immediate, timed, stochastic, continuous, adaptive)
- Rate configuration (rate, delay, rate functions)
- Priority and guard conditions
- SHPN signal hierarchy (enablement thresholds, signal places)
- Source/sink markers
- Module assignment
- Validation and error handling
- Complex real-world examples
"""

import pytest
from shypn.builders.transition_builder import TransitionBuilder
from shypn.netobjs.transition import Transition


# ========== Test Basic Transition Construction ==========

class TestTransitionBuilderBasics:
    """Test basic transition construction functionality."""
    
    def test_minimal_transition(self):
        """Test transition with minimal configuration."""
        t = (TransitionBuilder("T1")
             .at_position(100, 100)
             .build())
        
        assert isinstance(t, Transition)
        assert t.name == "T1"
        assert t.x == 100.0
        assert t.y == 100.0
        assert t.transition_type == 'continuous'  # Default
    
    def test_transition_with_position(self):
        """Test transition position setting."""
        t = (TransitionBuilder()
             .at_position(150.5, 200.3)
             .build())
        
        assert t.x == 150.5
        assert t.y == 200.3
    
    def test_transition_with_dimensions(self):
        """Test custom dimensions."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .with_dimensions(width=80, height=25)
             .build())
        
        assert t.width == 80.0
        assert t.height == 25.0
    
    def test_transition_vertical(self):
        """Test vertical orientation."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .as_vertical()
             .build())
        
        assert t.horizontal is False
    
    def test_transition_with_label(self):
        """Test label setting."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .with_label("Glycolysis")
             .build())
        
        assert t.label == "Glycolysis"
    
    def test_transition_with_custom_id(self):
        """Test custom ID assignment."""
        t = (TransitionBuilder("MyTransition")
             .at_position(100, 100)
             .with_id("T_custom")
             .build())
        
        assert t.id == "T_custom"
        assert t.name == "MyTransition"


# ========== Test Transition Type Selection ==========

class TestTransitionBuilderTypes:
    """Test all 5 transition type selections."""
    
    def test_immediate_transition(self):
        """Test immediate transition (zero-delay)."""
        t = (TransitionBuilder("T_immediate")
             .at_position(100, 100)
             .as_immediate()
             .with_priority(5)
             .build())
        
        assert t.transition_type == 'immediate'
        assert t.priority == 5
    
    def test_timed_transition(self):
        """Test timed transition (deterministic delay)."""
        t = (TransitionBuilder("T_timed")
             .at_position(100, 100)
             .as_timed()
             .with_rate(2.0)
             .build())
        
        assert t.transition_type == 'timed'
        assert t.rate == 2.0
    
    def test_stochastic_transition(self):
        """Test stochastic transition (Gillespie)."""
        t = (TransitionBuilder("T_stochastic")
             .at_position(100, 100)
             .as_stochastic()
             .with_rate(10.5)
             .build())
        
        assert t.transition_type == 'stochastic'
        assert t.rate == 10.5
    
    def test_continuous_transition(self):
        """Test continuous transition (ODE-based)."""
        t = (TransitionBuilder("T_continuous")
             .at_position(100, 100)
             .as_continuous()
             .with_rate_function("0.5 * [glucose]")
             .build())
        
        assert t.transition_type == 'continuous'
        assert t.rate_function == "0.5 * [glucose]"
    
    def test_adaptive_transition(self):
        """Test adaptive transition (hybrid)."""
        t = (TransitionBuilder("T_adaptive")
             .at_position(100, 100)
             .as_adaptive()
             .with_rate_function("k * [substrate]")
             .with_rate(5.0)
             .build())
        
        assert t.transition_type == 'adaptive'
        assert t.rate_function == "k * [substrate]"
        assert t.rate == 5.0
    
    def test_default_transition_type(self):
        """Test default transition type is continuous."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .build())
        
        assert t.transition_type == 'continuous'


# ========== Test Rate Configuration ==========

class TestTransitionBuilderRates:
    """Test rate configuration methods."""
    
    def test_with_rate(self):
        """Test constant rate setting."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .as_stochastic()
             .with_rate(15.3)
             .build())
        
        assert t.rate == 15.3
    
    def test_with_delay(self):
        """Test delay conversion to rate."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .as_timed()
             .with_delay(2.0)  # delay=2 → rate=0.5
             .build())
        
        assert t.rate == 0.5
    
    def test_with_rate_function(self):
        """Test rate function for continuous transitions."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .as_continuous()
             .with_rate_function("k_cat * [E] * [S] / (K_m + [S])")
             .build())
        
        assert t.rate_function == "k_cat * [E] * [S] / (K_m + [S])"
    
    def test_with_reversible_rates(self):
        """Test reversible reaction rates."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .as_continuous()
             .with_reversible_rates(
                 forward="k_f * [A] * [B]",
                 reverse="k_r * [C]"
             )
             .build())
        
        assert t.rate_forward == "k_f * [A] * [B]"
        assert t.rate_reverse == "k_r * [C]"
    
    def test_negative_rate_raises_error(self):
        """Test that negative rate raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            (TransitionBuilder()
             .at_position(100, 100)
             .with_rate(-1.0)
             .build())
    
    def test_non_positive_delay_raises_error(self):
        """Test that non-positive delay raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            (TransitionBuilder()
             .at_position(100, 100)
             .with_delay(0)
             .build())
    
    def test_continuous_default_rate_function(self):
        """Test continuous transition gets default rate function."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .as_continuous()
             .build())
        
        assert t.rate_function == "1"  # Default


# ========== Test Priority and Guard ==========

class TestTransitionBuilderPriorityGuard:
    """Test priority and guard condition functionality."""
    
    def test_with_priority(self):
        """Test priority setting."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .as_immediate()
             .with_priority(10)
             .build())
        
        assert t.priority == 10
    
    def test_with_guard_string(self):
        """Test guard condition as string expression."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .with_guard("[ATP] > 5")
             .build())
        
        assert t.guard == "[ATP] > 5"
    
    def test_with_guard_numeric(self):
        """Test guard condition as numeric value."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .with_guard(0)  # Always disabled
             .build())
        
        assert t.guard == 0
    
    def test_with_firing_policy(self):
        """Test firing policy setting."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .with_firing_policy('priority')
             .build())
        
        assert t.firing_policy == 'priority'
    
    def test_invalid_firing_policy_raises_error(self):
        """Test that invalid firing policy raises ValueError."""
        with pytest.raises(ValueError, match="Invalid firing policy"):
            (TransitionBuilder()
             .at_position(100, 100)
             .with_firing_policy('invalid_policy')
             .build())


# ========== Test SHPN Signal Hierarchy ==========

class TestTransitionBuilderSHPN:
    """Test SHPN signal hierarchy functionality."""
    
    def test_with_enablement_threshold(self):
        """Test enablement threshold θ(t) setting."""
        t = (TransitionBuilder("commit")
             .at_position(100, 100)
             .with_enablement_threshold(2.21)
             .build())
        
        assert t.properties['enablement_threshold'] == 2.21
    
    def test_with_signal_places(self):
        """Test signal place dependencies."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .with_signal_places(['P10', 'P15', 'P20'])
             .build())
        
        assert t.signal_places == ['P10', 'P15', 'P20']
        assert t.is_environment_aware is True
    
    def test_signal_places_empty(self):
        """Test empty signal places list."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .with_signal_places([])
             .build())
        
        assert t.signal_places == []
        assert t.is_environment_aware is False
    
    def test_negative_enablement_threshold_raises_error(self):
        """Test that negative threshold raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            (TransitionBuilder()
             .at_position(100, 100)
             .with_enablement_threshold(-1.0)
             .build())
    
    def test_bacillus_subtilis_commitment_transition(self):
        """Test B. subtilis commitment transition (canonical SHPN example).
        
        From formalism:
        - Commitment transition with θ(t) = 2.21 mM ATP
        - Signal weight W_s = 0.17 mM (on incoming arc)
        - → M_commit = 2.21 + 0.17 = 2.38 mM
        """
        t = (TransitionBuilder("commit")
             .at_position(250, 200)
             .as_immediate()
             .with_enablement_threshold(2.21)  # θ(commit)
             .with_priority(10)
             .with_label("Sporulation commitment")
             .with_metadata(
                 source="B. subtilis sporulation",
                 commitment_threshold=2.38,  # θ + W_s
                 experimental_value=2.21,
                 unit="mM"
             )
             .build())
        
        assert t.transition_type == 'immediate'
        assert t.properties['enablement_threshold'] == 2.21
        assert t.priority == 10
        assert t.metadata['experimental_value'] == 2.21


# ========== Test Source/Sink Markers ==========

class TestTransitionBuilderSourceSink:
    """Test source and sink marker functionality."""
    
    def test_as_source(self):
        """Test source transition marker."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .as_source()
             .build())
        
        assert t.is_source is True
        assert t.is_sink is False
    
    def test_as_sink(self):
        """Test sink transition marker."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .as_sink()
             .build())
        
        assert t.is_source is False
        assert t.is_sink is True
    
    def test_source_and_sink(self):
        """Test transition can be both source and sink."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .as_source()
             .as_sink()
             .build())
        
        assert t.is_source is True
        assert t.is_sink is True


# ========== Test Module Assignment ==========

class TestTransitionBuilderModule:
    """Test module assignment functionality."""
    
    def test_with_module(self):
        """Test module assignment."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .with_module("M_cytoplasm")
             .build())
        
        assert t.module_id == "M_cytoplasm"
    
    def test_compartment_example(self):
        """Test mitochondrial transition."""
        t = (TransitionBuilder("ATP_synthesis")
             .at_position(200, 150)
             .with_module("M_mitochondria")
             .as_continuous()
             .with_rate_function("V_max * [ADP] * [Pi]")
             .build())
        
        assert t.module_id == "M_mitochondria"
        assert t.name == "ATP_synthesis"


# ========== Test Optional Properties ==========

class TestTransitionBuilderProperties:
    """Test optional properties and metadata."""
    
    def test_disabled_transition(self):
        """Test disabled transition."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .disabled()
             .build())
        
        assert t.enabled is False
    
    def test_with_custom_property(self):
        """Test custom properties."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .with_property("k_cat", 100.0)
             .with_property("K_m", 5.0)
             .build())
        
        assert t.properties["k_cat"] == 100.0
        assert t.properties["K_m"] == 5.0
    
    def test_with_metadata(self):
        """Test metadata."""
        t = (TransitionBuilder()
             .at_position(100, 100)
             .with_metadata(
                 source="KEGG",
                 pathway="Glycolysis",
                 ec_number="2.7.1.1"
             )
             .build())
        
        assert t.metadata["source"] == "KEGG"
        assert t.metadata["pathway"] == "Glycolysis"
        assert t.metadata["ec_number"] == "2.7.1.1"


# ========== Test Complex Real-World Examples ==========

class TestTransitionBuilderComplexExamples:
    """Test complex real-world transition configurations."""
    
    def test_enzyme_kinetics_michaelis_menten(self):
        """Test enzyme with Michaelis-Menten kinetics."""
        t = (TransitionBuilder("hexokinase")
             .at_position(150, 200)
             .as_continuous()
             .with_rate_function("V_max * [glucose] / (K_m + [glucose])")
             .with_property("V_max", 10.0)
             .with_property("K_m", 5.0)
             .with_label("Hexokinase")
             .with_metadata(ec_number="2.7.1.1", enzyme="hexokinase")
             .build())
        
        assert t.transition_type == 'continuous'
        assert "V_max" in t.rate_function
        assert t.properties["V_max"] == 10.0
    
    def test_stochastic_gene_expression(self):
        """Test stochastic gene expression (bursting)."""
        t = (TransitionBuilder("transcription")
             .at_position(100, 150)
             .as_stochastic()
             .with_rate(0.05)  # Low rate for rare events
             .with_property("burst_size", 10)
             .with_label("mRNA production")
             .build())
        
        assert t.transition_type == 'stochastic'
        assert t.rate == 0.05
        assert t.properties["burst_size"] == 10
    
    def test_reversible_reaction(self):
        """Test reversible chemical reaction."""
        t = (TransitionBuilder("ATP_ADP_equilibrium")
             .at_position(200, 200)
             .as_continuous()
             .with_reversible_rates(
                 forward="k_forward * [ATP]",
                 reverse="k_reverse * [ADP] * [Pi]"
             )
             .with_property("k_forward", 0.1)
             .with_property("k_reverse", 1.0)
             .build())
        
        assert t.rate_forward == "k_forward * [ATP]"
        assert t.rate_reverse == "k_reverse * [ADP] * [Pi]"
    
    def test_adaptive_hybrid_calcium_signaling(self):
        """Test adaptive hybrid transition for calcium signaling."""
        t = (TransitionBuilder("calcium_release")
             .at_position(180, 220)
             .as_adaptive()
             .with_rate_function("k_release * [IP3] * [Ca_ER]")
             .with_rate(5.0)  # Stochastic rate for low copy number
             .with_property("switching_threshold", 100)
             .with_label("IP3-induced Ca²⁺ release")
             .build())
        
        assert t.transition_type == 'adaptive'
        assert t.rate_function == "k_release * [IP3] * [Ca_ER]"
        assert t.properties["switching_threshold"] == 100
    
    def test_glucose_influx_source(self):
        """Test glucose influx as source transition."""
        t = (TransitionBuilder("glucose_import")
             .at_position(50, 200)
             .as_continuous()
             .with_rate_function("v_import")
             .as_source()
             .with_property("v_import", 1.0)
             .with_label("Glucose influx")
             .build())
        
        assert t.is_source is True
        assert t.transition_type == 'continuous'
    
    def test_hierarchical_signal_integration(self):
        """Test multi-signal integration transition (quorum sensing).
        
        Transition fires when multiple environmental signals are present.
        """
        t = (TransitionBuilder("virulence_activation")
             .at_position(300, 250)
             .as_immediate()
             .with_signal_places(['AHL', 'AI2', 'temperature'])
             .with_guard("[AHL] > 5 AND [AI2] > 2 AND [temperature] > 37")
             .with_priority(15)
             .with_label("Virulence gene expression")
             .with_metadata(
                 organism="P. aeruginosa",
                 regulation_type="quorum_sensing"
             )
             .build())
        
        assert t.signal_places == ['AHL', 'AI2', 'temperature']
        assert t.is_environment_aware is True
        assert t.guard == "[AHL] > 5 AND [AI2] > 2 AND [temperature] > 37"


# ========== Test Repr ==========

class TestTransitionBuilderRepr:
    """Test __repr__ for debugging."""
    
    def test_repr_immediate(self):
        """Test repr for immediate transition."""
        builder = (TransitionBuilder("T_test")
                   .at_position(100, 150)
                   .as_immediate()
                   .with_priority(5))
        repr_str = repr(builder)
        
        assert "T_test" in repr_str
        assert "immediate" in repr_str
        assert "priority=5" in repr_str
    
    def test_repr_continuous(self):
        """Test repr for continuous transition."""
        builder = (TransitionBuilder("T_enzyme")
                   .at_position(200, 100)
                   .as_continuous()
                   .with_rate_function("k * [S]"))
        repr_str = repr(builder)
        
        assert "T_enzyme" in repr_str
        assert "continuous" in repr_str
        assert "rate_fn" in repr_str
    
    def test_repr_with_threshold(self):
        """Test repr includes enablement threshold."""
        builder = (TransitionBuilder("T_signal")
                   .at_position(150, 150)
                   .with_enablement_threshold(2.21))
        repr_str = repr(builder)
        
        assert "θ=2.21" in repr_str


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
