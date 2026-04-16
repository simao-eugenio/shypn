#!/usr/bin/env python3
"""Unit tests for quorum sensing detection (13-tuple Bio-PN extension)."""

import pytest
from unittest.mock import Mock, MagicMock
from shypn.analysis.quorum_sensing import (
    QuorumSensingDetector,
    detect_and_annotate_signal_places,
    get_signal_network,
    classify_quorum_sensing_modules
)


class TestQuorumSensingDetector:
    """Test signal place detection algorithm."""
    
    def test_detect_simple_signal(self):
        """Test detection of single signal place in rate formula."""
        # Create mock model
        model = Mock()
        
        # Create mock places
        ahl_place = Mock()
        ahl_place.id = 'P_AHL'
        ahl_place.name = 'AHL'
        
        substrate_place = Mock()
        substrate_place.id = 'P1'
        substrate_place.name = 'Substrate'
        
        model.places = {
            'P_AHL': ahl_place,
            'P1': substrate_place
        }
        
        # Create mock transition with rate formula
        transition = Mock()
        transition.id = 'T1'
        transition.name = 'lux_transcription'
        
        # Create mock arcs - only substrate has arc
        arc = Mock()
        arc.source = 'P1'
        arc.target = 'T1'
        arc.arc_type = 'normal'
        
        model.arcs = {'A1': arc}
        
        # Rate formula references AHL (no arc) and Substrate (has arc)
        rate = "0.5 * AHL / (1.0 + AHL)"
        
        # Test detection
        detector = QuorumSensingDetector(model)
        signals = detector.detect_signal_places(transition, rate)
        
        # AHL should be detected as signal (no arc)
        # Substrate should NOT be signal (has arc)
        assert 'P_AHL' in signals or 'AHL' in signals
        assert 'P1' not in signals
        assert 'Substrate' not in signals
        assert len(signals) >= 1
    
    def test_no_false_positives_with_arcs(self):
        """Test that places with arcs are NOT detected as signals."""
        model = Mock()
        
        # Place with input arc
        place = Mock()
        place.id = 'P1'
        place.name = 'Substrate'
        
        model.places = {'P1': place}
        
        transition = Mock()
        transition.id = 'T1'
        transition.name = 'reaction'
        
        # Arc connects place to transition
        arc = Mock()
        arc.source = 'P1'
        arc.target = 'T1'
        arc.arc_type = 'normal'
        
        model.arcs = {'A1': arc}
        
        # Rate references place that has arc
        rate = "0.5 * Substrate"
        
        detector = QuorumSensingDetector(model)
        signals = detector.detect_signal_places(transition, rate)
        
        # Should NOT detect as signal (has arc)
        assert 'P1' not in signals
        assert 'Substrate' not in signals
        assert len(signals) == 0
    
    def test_exclude_math_functions(self):
        """Test that math functions are not detected as places."""
        model = Mock()
        
        ahl_place = Mock()
        ahl_place.id = 'P_AHL'
        ahl_place.name = 'AHL'
        
        model.places = {'P_AHL': ahl_place}
        
        transition = Mock()
        transition.id = 'T1'
        
        model.arcs = {}
        
        # Formula with math functions
        rate = "max(0, min(1.0, exp(-AHL)))"
        
        detector = QuorumSensingDetector(model)
        signals = detector.detect_signal_places(transition, rate)
        
        # Math functions should NOT be detected
        assert 'max' not in signals
        assert 'min' not in signals
        assert 'exp' not in signals
        
        # AHL should be detected
        assert 'P_AHL' in signals or 'AHL' in signals
    
    def test_exclude_time_variable(self):
        """Test that time variable is not detected as place."""
        model = Mock()
        model.places = {}
        model.arcs = {}
        
        transition = Mock()
        transition.id = 'T1'
        
        # Formula with time variable
        rate = "0.5 * t"
        
        detector = QuorumSensingDetector(model)
        signals = detector.detect_signal_places(transition, rate)
        
        # 't' should NOT be detected (it's time)
        assert 't' not in signals
        assert len(signals) == 0
    
    def test_multiple_signals(self):
        """Test detection of multiple signal places."""
        model = Mock()
        
        ahl = Mock()
        ahl.id = 'P_AHL'
        ahl.name = 'AHL'
        
        ai2 = Mock()
        ai2.id = 'P_AI2'
        ai2.name = 'AI2'
        
        model.places = {
            'P_AHL': ahl,
            'P_AI2': ai2
        }
        
        transition = Mock()
        transition.id = 'T1'
        
        model.arcs = {}
        
        # Formula with two signals
        rate = "0.1 * AHL * AI2"
        
        detector = QuorumSensingDetector(model)
        signals = detector.detect_signal_places(transition, rate)
        
        # Both should be detected
        assert len(signals) == 2
        signal_list = list(signals)
        assert any('AHL' in str(s) for s in signal_list)
        assert any('AI2' in str(s) for s in signal_list)
    
    def test_regulatory_arc_not_signal(self):
        """Test that places with test/inhibitor arcs are NOT signals."""
        model = Mock()
        
        enzyme = Mock()
        enzyme.id = 'P_Enzyme'
        enzyme.name = 'Enzyme'
        
        model.places = {'P_Enzyme': enzyme}
        
        transition = Mock()
        transition.id = 'T1'
        
        # Test arc (catalyst)
        arc = Mock()
        arc.source = 'P_Enzyme'
        arc.target = 'T1'
        arc.arc_type = 'test'
        
        model.arcs = {'A1': arc}
        
        # Rate references enzyme
        rate = "0.5 * Enzyme"
        
        detector = QuorumSensingDetector(model)
        signals = detector.detect_signal_places(transition, rate)
        
        # Should NOT be signal (has test arc)
        assert 'P_Enzyme' not in signals
        assert 'Enzyme' not in signals
        assert len(signals) == 0


class TestSignalNetwork:
    """Test signal network topology extraction."""
    
    def test_get_signal_network_simple(self):
        """Test extraction of signal→transitions mapping."""
        model = Mock()
        
        # Transition with signal dependency
        t1 = Mock()
        t1.id = 'T1'
        t1.signal_places = ['P_AHL']
        
        t2 = Mock()
        t2.id = 'T2'
        t2.signal_places = ['P_AHL']
        
        model.transitions = {'T1': t1, 'T2': t2}
        
        network = get_signal_network(model)
        
        # P_AHL should map to both transitions
        assert 'P_AHL' in network
        assert 'T1' in network['P_AHL']
        assert 'T2' in network['P_AHL']
        assert len(network['P_AHL']) == 2
    
    def test_classify_external_signal(self):
        """Test classification of external signal module."""
        model = Mock()
        
        # Transition that senses signal
        t_sense = Mock()
        t_sense.id = 'T_sense'
        t_sense.signal_places = ['P_Signal']
        
        model.transitions = {'T_sense': t_sense}
        
        # No producer (no output arc to P_Signal)
        model.arcs = {}
        
        modules = classify_quorum_sensing_modules(model)
        
        # Should classify as external signal
        assert len(modules) >= 1
        signal_module = [m for m in modules if m['signal_place'] == 'P_Signal'][0]
        assert signal_module['module_type'] == 'external_signal'
        assert len(signal_module['producer_transitions']) == 0
        assert 'T_sense' in signal_module['sensor_transitions']


class TestStochasticIntegration:
    """Test integration with stochastic behavior."""
    
    def test_signal_detection_on_init(self):
        """Test that signal places are detected during initialization."""
        # This is more of an integration test
        # Will be expanded when we have better model fixtures
        pass


# Fixtures for reusable test data
@pytest.fixture
def simple_qs_model():
    """Create a simple quorum sensing model fixture."""
    model = Mock()
    
    # Places
    ahl = Mock()
    ahl.id = 'P_AHL'
    ahl.name = 'AHL'
    ahl.tokens = 0.1
    
    model.places = {'P_AHL': ahl}
    
    # Transition
    transition = Mock()
    transition.id = 'T_lux'
    transition.name = 'lux_transcription'
    
    model.transitions = {'T_lux': transition}
    
    # No arcs (AHL is signal)
    model.arcs = {}
    
    return model


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
