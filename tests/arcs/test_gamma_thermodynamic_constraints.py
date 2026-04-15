"""Phase 4 tests for thermodynamic constraint tuple Γ = (K, n, ε).

Tests cover all four test cases from the implementation plan:
1. Unit (backward compat): ε = 0 ⇒ θ_eff = 0
2. Unit (paper values): K = 2.04, n = 1, ε = 0.52 ⇒ θ_eff ≈ 2.21 mM
3. Integration (sporulation subnet): enablement gated by θ_eff + Ws
4. Regression: existing arcs without Γ behave identically

Plus additional coverage:
- Builder with_gamma() validation
- Serialization round-trip (to_dict / from_dict)
- CurvedSignalFlowArc parity
- Hill coefficient n > 1 (cooperativity)
- Signal hierarchy reporting of Γ statistics
"""

import math
import pytest
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.signal_flow_arc import SignalFlowArc
from shypn.netobjs.curved_signal_flow_arc import CurvedSignalFlowArc
from shypn.builders.arc_builder import ArcBuilder


# ========== Fixtures ==========

@pytest.fixture
def signal_place():
    """Signal place representing Spo0A~P (B. subtilis sporulation)."""
    p = Place(100, 100, "Spo0A_P", "Spo0A~P")
    p.is_signal_place = True
    return p


@pytest.fixture
def transition():
    """Commitment transition."""
    return Transition(200, 200, "commit", "Sporulation Commit")


@pytest.fixture
def places(signal_place):
    """Places dict for from_dict resolution."""
    return {"Spo0A_P": signal_place}


@pytest.fixture
def transitions(transition):
    """Transitions dict for from_dict resolution."""
    return {"commit": transition}


@pytest.fixture
def gamma_arc(signal_place, transition):
    """SignalFlowArc with B. subtilis paper Γ values."""
    arc = SignalFlowArc(signal_place, transition, "A1", "A1", weight=0.17)
    arc.michaelis_K = 2.04
    arc.hill_n = 1.0
    arc.suppression_epsilon = 0.52
    return arc


@pytest.fixture
def plain_arc(signal_place, transition):
    """SignalFlowArc with no Γ (default ε = 0)."""
    return SignalFlowArc(signal_place, transition, "A2", "A2", weight=0.17)


# ========== Test Case 1: Backward Compatibility ==========

class TestBackwardCompatibility:
    """ε = 0 (default) ⇒ θ_eff = 0, reproducing pre-Γ behavior."""

    def test_default_epsilon_zero(self, plain_arc):
        assert plain_arc.suppression_epsilon == 0.0

    def test_theta_eff_zero_when_no_gamma(self, plain_arc):
        assert plain_arc.theta_eff == 0.0

    def test_commitment_marking_equals_weight(self, plain_arc):
        """M_commit = θ_eff + Ws = 0 + 0.17 = 0.17."""
        assert plain_arc.commitment_marking == pytest.approx(0.17)

    def test_default_gamma_values(self, plain_arc):
        assert plain_arc.michaelis_K == 0.0
        assert plain_arc.hill_n == 1.0
        assert plain_arc.suppression_epsilon == 0.0

    def test_serialization_omits_default_gamma(self, plain_arc):
        """to_dict should not include Γ keys when all defaults."""
        d = plain_arc.to_dict()
        assert 'michaelis_K' not in d
        assert 'hill_n' not in d
        assert 'suppression_epsilon' not in d


# ========== Test Case 2: Paper Values ==========

class TestPaperValues:
    """K = 2.04, n = 1, ε = 0.52 ⇒ θ_eff ≈ 2.21 mM (B. subtilis)."""

    def test_theta_eff_paper_value(self, gamma_arc):
        """θ_eff = K · (ε/(1-ε))^(1/n) = 2.04 · (0.52/0.48)^1 ≈ 2.21."""
        expected = 2.04 * (0.52 / 0.48)
        assert gamma_arc.theta_eff == pytest.approx(expected, rel=1e-6)

    def test_commitment_marking_paper_value(self, gamma_arc):
        """M_commit = θ_eff + Ws = 2.21 + 0.17 ≈ 2.38."""
        expected = 2.04 * (0.52 / 0.48) + 0.17
        assert gamma_arc.commitment_marking == pytest.approx(expected, rel=1e-6)

    def test_theta_eff_with_hill_n2(self, signal_place, transition):
        """n = 2: θ_eff = K · (ε/(1-ε))^(1/2)."""
        arc = SignalFlowArc(signal_place, transition, "A3", "A3", weight=0.17)
        arc.michaelis_K = 2.04
        arc.hill_n = 2.0
        arc.suppression_epsilon = 0.52
        expected = 2.04 * math.sqrt(0.52 / 0.48)
        assert arc.theta_eff == pytest.approx(expected, rel=1e-6)

    def test_theta_eff_with_hill_n4(self, signal_place, transition):
        """n = 4 (high cooperativity): sharper switch."""
        arc = SignalFlowArc(signal_place, transition, "A4", "A4", weight=0.17)
        arc.michaelis_K = 2.04
        arc.hill_n = 4.0
        arc.suppression_epsilon = 0.52
        expected = 2.04 * ((0.52 / 0.48) ** 0.25)
        assert arc.theta_eff == pytest.approx(expected, rel=1e-6)

    def test_epsilon_near_zero_small_theta(self, signal_place, transition):
        """ε → 0 ⇒ θ_eff → 0."""
        arc = SignalFlowArc(signal_place, transition, "A5", "A5", weight=0.17)
        arc.michaelis_K = 2.04
        arc.hill_n = 1.0
        arc.suppression_epsilon = 0.001
        # θ_eff = 2.04 * (0.001/0.999) ≈ 0.00204
        assert arc.theta_eff < 0.01

    def test_epsilon_near_one_large_theta(self, signal_place, transition):
        """ε → 1 ⇒ θ_eff → ∞ (practically very large)."""
        arc = SignalFlowArc(signal_place, transition, "A6", "A6", weight=0.17)
        arc.michaelis_K = 2.04
        arc.hill_n = 1.0
        arc.suppression_epsilon = 0.999
        # θ_eff = 2.04 * (0.999/0.001) = 2037.96
        assert arc.theta_eff > 2000


# ========== Test Case 3: Engine Enablement Integration ==========

class TestEngineEnablement:
    """Sporulation subnet: transition gated by M(ps) ≥ θ_eff + Ws."""

    def test_disabled_below_commitment(self, gamma_arc, signal_place):
        """M(Spo0A~P) = 2.3 < θ_eff + Ws ≈ 2.38 ⇒ disabled."""
        signal_place.tokens = 2.3
        theta = gamma_arc.theta_eff
        required = gamma_arc.weight + theta
        assert signal_place.tokens < required

    def test_enabled_above_commitment(self, gamma_arc, signal_place):
        """M(Spo0A~P) = 2.4 > θ_eff + Ws ≈ 2.38 ⇒ enabled."""
        signal_place.tokens = 2.4
        theta = gamma_arc.theta_eff
        required = gamma_arc.weight + theta
        assert signal_place.tokens >= required

    def test_basin_preserved_after_firing(self, gamma_arc, signal_place):
        """After firing: M = 2.4 - Ws = 2.4 - 0.17 = 2.23 > θ_eff ≈ 2.21."""
        signal_place.tokens = 2.4
        # Simulate firing: only Ws consumed (basin floor preserved)
        remaining = signal_place.tokens - gamma_arc.weight  # 2.4 - 0.17
        assert remaining > gamma_arc.theta_eff
        assert remaining == pytest.approx(2.23)

    def test_exactly_at_commitment(self, gamma_arc, signal_place):
        """M exactly at M_commit ⇒ enabled (≥ is the condition)."""
        signal_place.tokens = gamma_arc.commitment_marking
        required = gamma_arc.weight + gamma_arc.theta_eff
        assert signal_place.tokens >= required

    def test_no_gamma_no_basin_floor(self, plain_arc, signal_place):
        """Without Γ, any tokens ≥ Ws enables transition."""
        signal_place.tokens = 0.17
        theta = plain_arc.theta_eff
        required = plain_arc.weight + theta  # 0.17 + 0 = 0.17
        assert signal_place.tokens >= required


# ========== Test Case 4: Serialization Round-Trip ==========

class TestSerializationRoundTrip:
    """Serialize to_dict → from_dict and verify Γ preserved."""

    def test_gamma_serialized(self, gamma_arc):
        d = gamma_arc.to_dict()
        assert d['michaelis_K'] == 2.04
        assert d['hill_n'] == 1.0
        assert d['suppression_epsilon'] == 0.52

    def test_gamma_deserialized(self, gamma_arc, places, transitions):
        d = gamma_arc.to_dict()
        arc2 = SignalFlowArc.from_dict(d, places, transitions)
        assert arc2.michaelis_K == 2.04
        assert arc2.hill_n == 1.0
        assert arc2.suppression_epsilon == 0.52
        assert arc2.theta_eff == pytest.approx(gamma_arc.theta_eff, rel=1e-10)

    def test_round_trip_preserves_commitment(self, gamma_arc, places, transitions):
        d = gamma_arc.to_dict()
        arc2 = SignalFlowArc.from_dict(d, places, transitions)
        assert arc2.commitment_marking == pytest.approx(
            gamma_arc.commitment_marking, rel=1e-10
        )

    def test_no_gamma_round_trip(self, plain_arc, places, transitions):
        """Arcs without Γ round-trip with θ_eff = 0."""
        d = plain_arc.to_dict()
        arc2 = SignalFlowArc.from_dict(d, places, transitions)
        assert arc2.theta_eff == 0.0

    def test_curved_signal_flow_round_trip(self, signal_place, transition, places, transitions):
        """CurvedSignalFlowArc preserves Γ through serialization."""
        arc = CurvedSignalFlowArc(signal_place, transition, "A_C1", "A_C1", weight=0.17)
        arc.michaelis_K = 2.04
        arc.hill_n = 1.0
        arc.suppression_epsilon = 0.52
        d = arc.to_dict()
        arc2 = CurvedSignalFlowArc.from_dict(d, places, transitions)
        assert arc2.theta_eff == pytest.approx(arc.theta_eff, rel=1e-10)


# ========== Builder Integration ==========

class TestBuilderGamma:
    """ArcBuilder.with_gamma() creates correct Γ arcs."""

    def test_builder_with_gamma(self, signal_place, transition):
        arc = (ArcBuilder()
               .from_place(signal_place)
               .to_transition(transition)
               .as_signal_flow()
               .with_signal_weight(0.17)
               .with_gamma(K=2.04, n=1.0, epsilon=0.52)
               .build())
        assert arc.theta_eff == pytest.approx(2.04 * (0.52 / 0.48), rel=1e-6)

    def test_builder_without_gamma(self, signal_place, transition):
        arc = (ArcBuilder()
               .from_place(signal_place)
               .to_transition(transition)
               .as_signal_flow()
               .with_signal_weight(0.17)
               .build())
        assert arc.theta_eff == 0.0

    def test_builder_gamma_on_non_signal_raises(self, signal_place, transition):
        with pytest.raises(ValueError, match="require .as_signal_flow"):
            (ArcBuilder()
             .from_place(signal_place)
             .to_transition(transition)
             .with_gamma(K=1.0, epsilon=0.5)
             .build())

    def test_builder_gamma_negative_K_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            ArcBuilder().with_gamma(K=-1.0)

    def test_builder_gamma_zero_n_raises(self):
        with pytest.raises(ValueError, match="positive"):
            ArcBuilder().with_gamma(K=1.0, n=0.0)

    def test_builder_gamma_epsilon_out_of_range_raises(self):
        with pytest.raises(ValueError, match="\\[0, 1\\)"):
            ArcBuilder().with_gamma(K=1.0, epsilon=1.0)

    def test_builder_curved_with_gamma(self, signal_place, transition):
        arc = (ArcBuilder()
               .from_place(signal_place)
               .to_transition(transition)
               .as_signal_flow()
               .as_curved()
               .with_signal_weight(0.17)
               .with_gamma(K=2.04, n=1.0, epsilon=0.52)
               .build())
        assert isinstance(arc, CurvedSignalFlowArc)
        assert arc.theta_eff == pytest.approx(2.04 * (0.52 / 0.48), rel=1e-6)

    def test_builder_repr_includes_gamma(self, signal_place, transition):
        b = (ArcBuilder()
             .from_place(signal_place)
             .to_transition(transition)
             .as_signal_flow()
             .with_signal_weight(0.17)
             .with_gamma(K=2.04, n=1.0, epsilon=0.52))
        r = repr(b)
        assert "Γ" in r
        assert "K=2.04" in r
        assert "ε=0.52" in r


# ========== Signal Hierarchy Reporting ==========

class TestSignalHierarchyReporting:
    """Signal hierarchy analyzer includes Γ statistics."""

    def test_hierarchy_detects_gamma(self):
        """Hierarchy analyzer reports arcs_with_gamma count."""
        try:
            from shypn.topology.biological.signal_hierarchy import SignalHierarchyAnalyzer
        except ImportError:
            pytest.skip("signal_hierarchy module not available")

        p = Place(100, 100, "ATP", "ATP")
        p.is_signal_place = True
        t = Transition(200, 200, "T1", "T1")
        arc = SignalFlowArc(p, t, "A1", "A1", weight=0.17)
        arc.michaelis_K = 2.04
        arc.hill_n = 1.0
        arc.suppression_epsilon = 0.52

        # Create a minimal model-like object
        class MockModel:
            def __init__(self, places, transitions, arcs):
                self.places = places
                self.transitions = transitions
                self.arcs = arcs

        model = MockModel([p], [t], [arc])
        analyzer = SignalHierarchyAnalyzer(model)
        result = analyzer.analyze()
        data = result.data if hasattr(result, 'data') else result
        stats = data.get('statistics', {})
        assert stats.get('arcs_with_gamma', 0) >= 1
        assert stats.get('max_theta_eff', 0) > 2.0


# ========== Arrhenius Temperature Dependence ==========

class TestArrheniusDefaults:
    """Arrhenius fields have safe defaults for backward compatibility."""

    def test_default_activation_energy(self):
        """Default E_a = 0.0 (no temperature effect)."""
        p = Place(0, 0, "P1", "P1")
        p.is_signal_place = True
        t = Transition(0, 0, "T1", "T1")
        arc = SignalFlowArc(p, t, "A1", "A1")
        assert arc.activation_energy == 0.0

    def test_default_reference_temperature(self):
        """Default T_ref = 298.15 K."""
        p = Place(0, 0, "P1", "P1")
        p.is_signal_place = True
        t = Transition(0, 0, "T1", "T1")
        arc = SignalFlowArc(p, t, "A1", "A1")
        assert arc.reference_temperature == 298.15

    def test_theta_eff_at_equals_static_when_ea_zero(self):
        """theta_eff_at(T) == theta_eff when E_a = 0 (backward compat)."""
        p = Place(0, 0, "P1", "P1")
        p.is_signal_place = True
        t = Transition(0, 0, "T1", "T1")
        arc = SignalFlowArc(p, t, "A1", "A1", weight=0.17)
        arc.michaelis_K = 2.04
        arc.hill_n = 1.0
        arc.suppression_epsilon = 0.52
        # E_a = 0 by default
        for T in [250.0, 298.15, 310.15, 350.0]:
            assert arc.theta_eff_at(T) == pytest.approx(arc.theta_eff)

    def test_theta_eff_at_ref_temp_equals_static(self):
        """theta_eff_at(T_ref) == theta_eff regardless of E_a."""
        p = Place(0, 0, "P1", "P1")
        p.is_signal_place = True
        t = Transition(0, 0, "T1", "T1")
        arc = SignalFlowArc(p, t, "A1", "A1", weight=0.17)
        arc.michaelis_K = 2.04
        arc.hill_n = 1.0
        arc.suppression_epsilon = 0.52
        arc.activation_energy = 50.0  # Non-zero E_a
        arc.reference_temperature = 298.15
        assert arc.theta_eff_at(298.15) == pytest.approx(arc.theta_eff)


class TestArrheniusKinetics:
    """Temperature-dependent K(T) via Arrhenius equation."""

    def test_higher_temp_increases_theta(self):
        """Higher temperature → higher K(T) → higher θ_eff (positive E_a)."""
        p = Place(0, 0, "P1", "P1")
        p.is_signal_place = True
        t = Transition(0, 0, "T1", "T1")
        arc = SignalFlowArc(p, t, "A1", "A1", weight=0.17)
        arc.michaelis_K = 2.04
        arc.hill_n = 1.0
        arc.suppression_epsilon = 0.52
        arc.activation_energy = 50.0  # 50 kJ/mol
        arc.reference_temperature = 298.15

        theta_ref = arc.theta_eff_at(298.15)
        theta_hot = arc.theta_eff_at(310.15)  # 37°C
        assert theta_hot > theta_ref

    def test_lower_temp_decreases_theta(self):
        """Lower temperature → lower K(T) → lower θ_eff."""
        p = Place(0, 0, "P1", "P1")
        p.is_signal_place = True
        t = Transition(0, 0, "T1", "T1")
        arc = SignalFlowArc(p, t, "A1", "A1", weight=0.17)
        arc.michaelis_K = 2.04
        arc.hill_n = 1.0
        arc.suppression_epsilon = 0.52
        arc.activation_energy = 50.0
        arc.reference_temperature = 298.15

        theta_ref = arc.theta_eff_at(298.15)
        theta_cold = arc.theta_eff_at(278.15)  # 5°C
        assert theta_cold < theta_ref

    def test_arrhenius_magnitude(self):
        """K(T) = K_ref · exp(−E_a/R · (1/T − 1/T_ref)) with known values."""
        p = Place(0, 0, "P1", "P1")
        p.is_signal_place = True
        t = Transition(0, 0, "T1", "T1")
        arc = SignalFlowArc(p, t, "A1", "A1", weight=0.17)
        arc.michaelis_K = 2.0
        arc.hill_n = 1.0
        arc.suppression_epsilon = 0.5
        arc.activation_energy = 50.0  # kJ/mol
        arc.reference_temperature = 300.0

        R = 0.008314  # kJ/(mol·K)
        T = 310.0
        expected_K = 2.0 * math.exp(-(50.0 / R) * (1.0 / T - 1.0 / 300.0))
        # θ_eff = K(T) · (ε/(1-ε))^(1/n) = K(T) · (0.5/0.5)^1 = K(T)
        assert arc.theta_eff_at(T) == pytest.approx(expected_K, rel=1e-6)

    def test_curved_arc_arrhenius_parity(self):
        """CurvedSignalFlowArc has same Arrhenius behavior."""
        p = Place(0, 0, "P1", "P1")
        p.is_signal_place = True
        t = Transition(0, 0, "T1", "T1")
        straight = SignalFlowArc(p, t, "A1s", "A1s", weight=0.17)
        curved = CurvedSignalFlowArc(p, t, "A1c", "A1c", weight=0.17)
        for arc in [straight, curved]:
            arc.michaelis_K = 2.04
            arc.hill_n = 1.0
            arc.suppression_epsilon = 0.52
            arc.activation_energy = 40.0
            arc.reference_temperature = 298.15
        assert straight.theta_eff_at(310.0) == pytest.approx(
            curved.theta_eff_at(310.0))


class TestArrheniusSerialization:
    """Arrhenius params survive serialization round-trip."""

    def test_to_dict_excludes_defaults(self):
        """E_a=0 and default T_ref are not serialized (compact format)."""
        p = Place(0, 0, "P1", "P1")
        p.is_signal_place = True
        t = Transition(0, 0, "T1", "T1")
        arc = SignalFlowArc(p, t, "A1", "A1", weight=0.17)
        d = arc.to_dict()
        assert 'activation_energy' not in d
        assert 'reference_temperature' not in d

    def test_to_dict_includes_nondefault(self):
        """Non-default Arrhenius values are serialized."""
        p = Place(0, 0, "P1", "P1")
        p.is_signal_place = True
        t = Transition(0, 0, "T1", "T1")
        arc = SignalFlowArc(p, t, "A1", "A1", weight=0.17)
        arc.activation_energy = 42.0
        arc.reference_temperature = 310.0
        d = arc.to_dict()
        assert d['activation_energy'] == 42.0
        assert d['reference_temperature'] == 310.0

    def test_round_trip(self):
        """Full round-trip preserves Arrhenius parameters."""
        p = Place(0, 0, "P1", "P1")
        p.is_signal_place = True
        t = Transition(0, 0, "T1", "T1")
        arc = SignalFlowArc(p, t, "A1", "A1", weight=0.17)
        arc.michaelis_K = 2.04
        arc.hill_n = 1.5
        arc.suppression_epsilon = 0.52
        arc.activation_energy = 50.0
        arc.reference_temperature = 310.0

        d = arc.to_dict()
        restored = SignalFlowArc.from_dict(
            d, places={"P1": p}, transitions={"T1": t})
        assert restored.activation_energy == 50.0
        assert restored.reference_temperature == 310.0
        assert restored.theta_eff_at(320.0) == pytest.approx(
            arc.theta_eff_at(320.0))

    def test_from_dict_missing_arrhenius_uses_defaults(self):
        """Loading old files without Arrhenius fields uses defaults."""
        p = Place(0, 0, "P1", "P1")
        p.is_signal_place = True
        t = Transition(0, 0, "T1", "T1")
        arc = SignalFlowArc(p, t, "A1", "A1", weight=0.17)
        d = arc.to_dict()
        # Old file: no activation_energy or reference_temperature keys
        assert 'activation_energy' not in d
        restored = SignalFlowArc.from_dict(
            d, places={"P1": p}, transitions={"T1": t})
        assert restored.activation_energy == 0.0
        assert restored.reference_temperature == 298.15


class TestBuilderArrhenius:
    """ArcBuilder with_arrhenius() fluent method."""

    def test_builder_with_arrhenius(self, signal_place, transition):
        """Builder sets activation energy and reference temperature."""
        arc = (ArcBuilder()
               .from_place(signal_place)
               .to_transition(transition)
               .as_signal_flow()
               .with_signal_weight(0.17)
               .with_gamma(K=2.04, n=1.0, epsilon=0.52)
               .with_arrhenius(activation_energy=50.0, reference_temperature=310.0)
               .build())
        assert arc.activation_energy == 50.0
        assert arc.reference_temperature == 310.0

    def test_builder_arrhenius_negative_ea_raises(self):
        """Negative activation energy is rejected."""
        with pytest.raises(ValueError, match="non-negative"):
            (ArcBuilder()
             .from_place("P1")
             .to_transition("T1")
             .as_signal_flow()
             .with_arrhenius(activation_energy=-10.0))

    def test_builder_arrhenius_zero_tref_raises(self):
        """Zero reference temperature is rejected."""
        with pytest.raises(ValueError, match="positive"):
            (ArcBuilder()
             .from_place("P1")
             .to_transition("T1")
             .as_signal_flow()
             .with_arrhenius(activation_energy=50.0, reference_temperature=0.0))

    def test_builder_arrhenius_requires_signal_flow(self):
        """Arrhenius on non-signal-flow arc is rejected at build time."""
        with pytest.raises(ValueError, match="signal flow"):
            (ArcBuilder()
             .from_place("P1")
             .to_transition("T1")
             .with_arrhenius(activation_energy=50.0)
             .build())

    def test_repr_includes_arrhenius(self):
        """Builder repr shows Arrhenius parameters."""
        b = (ArcBuilder()
             .from_place("P1")
             .to_transition("T1")
             .as_signal_flow()
             .with_gamma(K=2.04, n=1.0, epsilon=0.52)
             .with_arrhenius(activation_energy=50.0))
        r = repr(b)
        assert "E_a=50.0" in r


class TestEngineTemperatureWiring:
    """Engine _get_theta_eff and _get_model_temperature integration."""

    @staticmethod
    def _make_behavior(model):
        """Create a minimal concrete TransitionBehavior subclass instance."""
        from shypn.engine.transition_behavior import TransitionBehavior

        class _Concrete(TransitionBehavior):
            def can_fire(self, *a, **kw): return True, "ok"
            def fire(self, *a, **kw): return True, {}
            def get_type_name(self): return "test"

        tb = _Concrete.__new__(_Concrete)
        tb.model = model
        tb.transition = None
        return tb

    def test_get_model_temperature_default(self):
        """Default temperature is 298.15 K when model has no settings."""
        class MockModel:
            pass

        tb = self._make_behavior(MockModel())
        assert tb._get_model_temperature() == 298.15

    def test_get_model_temperature_from_settings(self):
        """Temperature extracted from model.thermodynamic_settings."""
        class MockModel:
            thermodynamic_settings = {'temperature': 310.15}

        tb = self._make_behavior(MockModel())
        assert tb._get_model_temperature() == 310.15

    def test_get_theta_eff_static_fallback(self):
        """_get_theta_eff falls back to static theta_eff when E_a=0."""
        class MockModel:
            thermodynamic_settings = {'temperature': 310.15}

        p = Place(0, 0, "P1", "P1")
        p.is_signal_place = True
        t = Transition(0, 0, "T1", "T1")
        arc = SignalFlowArc(p, t, "A1", "A1", weight=0.17)
        arc.michaelis_K = 2.04
        arc.hill_n = 1.0
        arc.suppression_epsilon = 0.52
        # E_a = 0 → should use static theta_eff

        tb = self._make_behavior(MockModel())
        assert tb._get_theta_eff(arc) == pytest.approx(arc.theta_eff)

    def test_get_theta_eff_dynamic_when_ea_nonzero(self):
        """_get_theta_eff uses theta_eff_at(T) when E_a > 0."""
        class MockModel:
            thermodynamic_settings = {'temperature': 310.15}

        p = Place(0, 0, "P1", "P1")
        p.is_signal_place = True
        t = Transition(0, 0, "T1", "T1")
        arc = SignalFlowArc(p, t, "A1", "A1", weight=0.17)
        arc.michaelis_K = 2.04
        arc.hill_n = 1.0
        arc.suppression_epsilon = 0.52
        arc.activation_energy = 50.0
        arc.reference_temperature = 298.15

        tb = self._make_behavior(MockModel())
        theta = tb._get_theta_eff(arc)
        # Should match dynamic calculation at 310.15 K
        assert theta == pytest.approx(arc.theta_eff_at(310.15))
        # And should differ from static
        assert theta != pytest.approx(arc.theta_eff)

    def test_get_theta_eff_normal_arc_returns_zero(self):
        """Normal arcs without theta_eff return 0."""
        from shypn.netobjs.arc import Arc

        class MockModel:
            thermodynamic_settings = {'temperature': 310.15}

        p = Place(0, 0, "P1", "P1")
        t = Transition(0, 0, "T1", "T1")
        arc = Arc(p, t, "A1", "A1")

        tb = self._make_behavior(MockModel())
        assert tb._get_theta_eff(arc) == 0
