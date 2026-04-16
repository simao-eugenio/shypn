"""Unit tests for ViabilityChecker class.

Tests the viability checking logic extracted from SimulationController
as part of Phase 2.3.2 quality improvements.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from unittest.mock import Mock, MagicMock, patch
from shypn.engine.simulation.checkers import ViabilityChecker


class TestViabilityChecker:
    """Test suite for ViabilityChecker class."""
    
    def setup_method(self):
        """Create mock controller and checker for each test."""
        self.mock_controller = Mock()
        self.mock_controller.model = Mock()
        self.mock_controller.model.transitions = []
        self.mock_controller.model.arcs = []
        self.mock_controller.model.places = []
        self.mock_controller._get_behavior = Mock()
        
        self.checker = ViabilityChecker(self.mock_controller)
    
    def test_initialization(self):
        """Test checker initializes with controller reference."""
        assert self.checker.controller == self.mock_controller
    
    def test_is_enabled_true(self):
        """Test is_enabled returns True when behavior can fire."""
        mock_transition = Mock()
        mock_behavior = Mock()
        mock_behavior.can_fire = Mock(return_value=(True, None))
        self.mock_controller._get_behavior = Mock(return_value=mock_behavior)
        
        result = self.checker.is_enabled(mock_transition)
        
        assert result is True
        self.mock_controller._get_behavior.assert_called_once_with(mock_transition)
        mock_behavior.can_fire.assert_called_once()
    
    def test_is_enabled_false(self):
        """Test is_enabled returns False when behavior cannot fire."""
        mock_transition = Mock()
        mock_behavior = Mock()
        mock_behavior.can_fire = Mock(return_value=(False, "Insufficient tokens"))
        self.mock_controller._get_behavior = Mock(return_value=mock_behavior)
        
        result = self.checker.is_enabled(mock_transition)
        
        assert result is False
    
    def test_is_enabled_with_reason_true(self):
        """Test is_enabled_with_reason returns (True, None) when enabled."""
        mock_transition = Mock()
        mock_behavior = Mock()
        mock_behavior.can_fire = Mock(return_value=(True, None))
        self.mock_controller._get_behavior = Mock(return_value=mock_behavior)
        
        enabled, reason = self.checker.is_enabled_with_reason(mock_transition)
        
        assert enabled is True
        assert reason is None
    
    def test_is_enabled_with_reason_false(self):
        """Test is_enabled_with_reason returns (False, reason) when disabled."""
        mock_transition = Mock()
        mock_behavior = Mock()
        mock_behavior.can_fire = Mock(return_value=(False, "Insufficient tokens in P1"))
        self.mock_controller._get_behavior = Mock(return_value=mock_behavior)
        
        enabled, reason = self.checker.is_enabled_with_reason(mock_transition)
        
        assert enabled is False
        assert reason == "Insufficient tokens in P1"
    
    def test_validate_all_empty_set(self):
        """Test validate_all returns True for empty transition set."""
        result = self.checker.validate_all([])
        assert result is True
    
    def test_validate_all_single_transition_sufficient_tokens(self):
        """Test validate_all succeeds when transition has sufficient tokens."""
        # Create mock place with tokens
        mock_place = Mock()
        mock_place.tokens = 5
        mock_place.id = 'P1'
        
        # Create mock transition
        mock_transition = Mock()
        mock_transition.id = 'T1'
        mock_transition.guard = None
        
        # Create normal arc (place → transition)
        mock_arc = Mock()
        mock_arc.source = mock_place
        mock_arc.target = mock_transition
        mock_arc.weight = 3
        mock_arc.threshold = None
        mock_arc.kind = 'normal'
        mock_arc.arc_type = 'normal'
        
        self.mock_controller.model.arcs = [mock_arc]
        
        result = self.checker.validate_all([mock_transition])
        
        assert result is True
    
    def test_validate_all_insufficient_tokens(self):
        """Test validate_all fails when transition lacks sufficient tokens."""
        # Create mock place with insufficient tokens
        mock_place = Mock()
        mock_place.tokens = 2
        mock_place.id = 'P1'
        
        # Create mock transition
        mock_transition = Mock()
        mock_transition.id = 'T1'
        mock_transition.guard = None
        
        # Create normal arc (place → transition) requiring 5 tokens
        mock_arc = Mock()
        mock_arc.source = mock_place
        mock_arc.target = mock_transition
        mock_arc.weight = 5
        mock_arc.threshold = None
        mock_arc.kind = 'normal'
        mock_arc.arc_type = 'normal'
        
        self.mock_controller.model.arcs = [mock_arc]
        
        result = self.checker.validate_all([mock_transition])
        
        assert result is False
    
    def test_validate_all_inhibitor_arc_enabled(self):
        """Test validate_all with inhibitor arc - enabled when tokens low."""
        # Create mock place with low tokens
        mock_place = Mock()
        mock_place.tokens = 1
        mock_place.id = 'P1'
        
        # Create mock transition
        mock_transition = Mock()
        mock_transition.id = 'T1'
        mock_transition.guard = None
        
        # Create inhibitor arc - use arc_type attribute for type checking
        mock_arc = Mock()
        mock_arc.source = mock_place
        mock_arc.target = mock_transition
        mock_arc.weight = 5
        mock_arc.threshold = 5
        mock_arc.kind = 'inhibitor'
        mock_arc.arc_type = 'inhibitor'
        
        self.mock_controller.model.arcs = [mock_arc]
        
        result = self.checker.validate_all([mock_transition])
        
        # Should be enabled because tokens (1) < threshold (5)
        assert result is True
    
    def test_validate_all_inhibitor_arc_disabled(self):
        """Test validate_all with inhibitor arc - disabled when tokens high."""
        # Create mock place with high tokens
        mock_place = Mock()
        mock_place.tokens = 10
        mock_place.id = 'P1'
        
        # Create mock transition
        mock_transition = Mock()
        mock_transition.id = 'T1'
        mock_transition.guard = None
        
        # Create inhibitor arc - use arc_type attribute for type checking
        mock_arc = Mock()
        mock_arc.source = mock_place
        mock_arc.target = mock_transition
        mock_arc.weight = 5
        mock_arc.threshold = 5
        mock_arc.kind = 'inhibitor'
        mock_arc.arc_type = 'inhibitor'
        
        self.mock_controller.model.arcs = [mock_arc]
        
        result = self.checker.validate_all([mock_transition])
        
        # Should be disabled because tokens (10) >= threshold (5)
        assert result is False
    
    def test_validate_all_test_arc_enabled(self):
        """Test validate_all with test arc - enabled when catalyst present."""
        # Create mock place with sufficient tokens
        mock_place = Mock()
        mock_place.tokens = 5
        mock_place.id = 'P1'
        
        # Create mock transition
        mock_transition = Mock()
        mock_transition.id = 'T1'
        mock_transition.guard = None
        
        # Create test arc - use arc_type attribute for type checking
        mock_arc = Mock()
        mock_arc.source = mock_place
        mock_arc.target = mock_transition
        mock_arc.weight = 3
        mock_arc.threshold = 3
        mock_arc.kind = 'test'
        mock_arc.arc_type = 'test'
        
        self.mock_controller.model.arcs = [mock_arc]
        
        result = self.checker.validate_all([mock_transition])
        
        # Should be enabled because tokens (5) >= threshold (3)
        assert result is True
    
    def test_validate_all_test_arc_disabled(self):
        """Test validate_all with test arc - disabled when catalyst absent."""
        # Create mock place with insufficient tokens
        mock_place = Mock()
        mock_place.tokens = 1
        mock_place.id = 'P1'
        
        # Create mock transition
        mock_transition = Mock()
        mock_transition.id = 'T1'
        mock_transition.guard = None
        
        # Create test arc - use arc_type attribute for type checking
        mock_arc = Mock()
        mock_arc.source = mock_place
        mock_arc.target = mock_transition
        mock_arc.weight = 3
        mock_arc.threshold = 3
        mock_arc.kind = 'test'
        mock_arc.arc_type = 'test'
        
        self.mock_controller.model.arcs = [mock_arc]
        
        result = self.checker.validate_all([mock_transition])
        
        # Should be disabled because tokens (1) < threshold (3)
        assert result is False
    
    def test_validate_all_guard_true(self):
        """Test validate_all succeeds when guard evaluates to True."""
        # Create mock transition with guard
        mock_transition = Mock()
        mock_transition.id = 'T1'
        mock_guard = Mock()
        mock_guard.evaluate = Mock(return_value=True)
        mock_transition.guard = mock_guard
        
        self.mock_controller.model.arcs = []  # No input arcs
        
        result = self.checker.validate_all([mock_transition])
        
        assert result is True
        mock_guard.evaluate.assert_called_once()
    
    def test_validate_all_guard_false(self):
        """Test validate_all fails when guard evaluates to False."""
        # Create mock transition with guard
        mock_transition = Mock()
        mock_transition.id = 'T1'
        mock_guard = Mock()
        mock_guard.evaluate = Mock(return_value=False)
        mock_transition.guard = mock_guard
        
        self.mock_controller.model.arcs = []  # No input arcs
        
        result = self.checker.validate_all([mock_transition])
        
        assert result is False
    
    def test_validate_all_guard_exception(self):
        """Test validate_all fails when guard evaluation throws exception."""
        # Create mock transition with failing guard
        mock_transition = Mock()
        mock_transition.id = 'T1'
        mock_guard = Mock()
        mock_guard.evaluate = Mock(side_effect=RuntimeError("Guard error"))
        mock_transition.guard = mock_guard
        
        self.mock_controller.model.arcs = []  # No input arcs
        
        result = self.checker.validate_all([mock_transition])
        
        assert result is False
    
    def test_validate_all_multiple_transitions(self):
        """Test validate_all with multiple transitions."""
        # Create places
        place1 = Mock()
        place1.tokens = 5
        place1.id = 'P1'
        
        place2 = Mock()
        place2.tokens = 3
        place2.id = 'P2'
        
        # Create transitions
        trans1 = Mock()
        trans1.id = 'T1'
        trans1.guard = None
        
        trans2 = Mock()
        trans2.id = 'T2'
        trans2.guard = None
        
        # Create arcs
        arc1 = Mock()
        arc1.source = place1
        arc1.target = trans1
        arc1.weight = 2
        arc1.threshold = None
        arc1.kind = 'normal'
        arc1.arc_type = 'normal'
        
        arc2 = Mock()
        arc2.source = place2
        arc2.target = trans2
        arc2.weight = 2
        arc2.threshold = None
        arc2.kind = 'normal'
        arc2.arc_type = 'normal'
        
        self.mock_controller.model.arcs = [arc1, arc2]
        
        result = self.checker.validate_all([trans1, trans2])
        
        # Both should be enabled (P1 has 5>=2, P2 has 3>=2)
        assert result is True
    
    def test_validate_all_with_reasons_success(self):
        """Test validate_all_with_reasons returns empty reasons on success."""
        mock_transition = Mock()
        mock_transition.id = 'T1'
        mock_transition.name = 'Transition1'
        mock_transition.guard = None
        
        self.mock_controller.model.arcs = []
        
        all_enabled, reasons = self.checker.validate_all_with_reasons([mock_transition])
        
        assert all_enabled is True
        assert reasons == []
    
    def test_validate_all_with_reasons_failure(self):
        """Test validate_all_with_reasons returns reasons on failure."""
        # Create mock place with insufficient tokens
        mock_place = Mock()
        mock_place.tokens = 1
        mock_place.id = 'P1'
        mock_place.name = 'Place1'
        
        # Create mock transition
        mock_transition = Mock()
        mock_transition.id = 'T1'
        mock_transition.name = 'Transition1'
        mock_transition.guard = None
        
        # Create normal arc requiring more tokens
        mock_arc = Mock()
        mock_arc.source = mock_place
        mock_arc.target = mock_transition
        mock_arc.weight = 5
        mock_arc.threshold = None
        mock_arc.kind = 'normal'
        mock_arc.arc_type = 'normal'
        
        self.mock_controller.model.arcs = [mock_arc]
        
        all_enabled, reasons = self.checker.validate_all_with_reasons([mock_transition])
        
        assert all_enabled is False
        assert len(reasons) == 1
        assert "Transition1" in reasons[0]
        assert "Place1" in reasons[0]
        assert "1 < needed 5" in reasons[0]
    
    def test_get_enabled_transitions(self):
        """Test get_enabled_transitions returns list of enabled transitions."""
        # Create transitions
        trans1 = Mock()
        trans1.id = 'T1'
        trans2 = Mock()
        trans2.id = 'T2'
        trans3 = Mock()
        trans3.id = 'T3'
        
        self.mock_controller.model.transitions = [trans1, trans2, trans3]
        
        # Mock is_enabled to return True for trans1 and trans3, False for trans2
        def mock_is_enabled(transition):
            return transition.id in ['T1', 'T3']
        
        # Patch is_enabled method
        self.checker.is_enabled = Mock(side_effect=mock_is_enabled)
        
        result = self.checker.get_enabled_transitions()
        
        assert len(result) == 2
        assert trans1 in result
        assert trans3 in result
        assert trans2 not in result
    
    def test_get_disabled_transitions_with_reasons(self):
        """Test get_disabled_transitions_with_reasons returns disabled transitions with reasons."""
        # Create transitions
        trans1 = Mock()
        trans1.id = 'T1'
        trans1.name = 'Transition1'
        trans2 = Mock()
        trans2.id = 'T2'
        trans2.name = 'Transition2'
        
        self.mock_controller.model.transitions = [trans1, trans2]
        
        # Mock is_enabled_with_reason
        def mock_is_enabled_with_reason(transition):
            if transition.id == 'T1':
                return (True, None)
            else:
                return (False, "Insufficient tokens")
        
        self.checker.is_enabled_with_reason = Mock(side_effect=mock_is_enabled_with_reason)
        
        result = self.checker.get_disabled_transitions_with_reasons()
        
        assert len(result) == 1
        assert result[0][0] == trans2
        assert result[0][1] == "Insufficient tokens"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
