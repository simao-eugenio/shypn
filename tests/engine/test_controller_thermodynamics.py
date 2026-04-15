"""
Tests for SimulationController Thermodynamic Validation

Tests the integration of thermodynamic validation in the simulation controller:
- validate_thermodynamics() method
- get_thermodynamic_summary() method
- Results caching and clearing on reset
"""

import pytest
from unittest.mock import MagicMock, Mock


class MockTransition:
    """Mock transition for testing."""
    
    def __init__(self, name, is_reversible=False, validation_result=None):
        self.name = name
        self.id = name
        self.label = name
        self.transition_type = 'immediate'  # avoid ContinuousBehavior which requires rate_function
        self.properties = {}
        
        if is_reversible:
            self.properties['is_reversible'] = True
        
        if validation_result:
            self.properties['thermodynamic_validation'] = validation_result
    
    def reset_firing_count(self):
        """Mock reset firing count."""
        pass


class MockModel:
    """Mock model canvas manager."""
    
    def __init__(self, transitions=None):
        self.transitions = transitions or []
        self.places = []
        self.arcs = []
    
    def register_observer(self, callback):
        """Mock observer registration."""
        pass


class MockPlace:
    """Mock place for testing."""
    
    def __init__(self, name, tokens=0):
        self.name = name
        self.id = name
        self.tokens = tokens
        self.initial_marking = tokens


class TestControllerThermodynamics:
    """Test suite for controller thermodynamic validation."""
    
    def test_validate_thermodynamics_no_reversible(self):
        """Test validation with no reversible transitions."""
        model = MockModel(transitions=[
            MockTransition('T1', is_reversible=False),
            MockTransition('T2', is_reversible=False),
        ])
        
        # Import controller
        from shypn.engine.simulation.controller import SimulationController
        controller = SimulationController(model, verbose=False)
        
        # Validate
        result = controller.validate_thermodynamics()
        
        assert result is not None
        assert result['summary']['total'] == 0
        assert result['summary']['valid'] == 0
        assert result['summary']['violations'] == 0
    
    def test_validate_thermodynamics_valid_transitions(self):
        """Test validation with valid transitions."""
        model = MockModel(transitions=[
            MockTransition('R1', is_reversible=True, validation_result={
                'status': 'valid',
                'k_ratio': 2.0,
                'k_eq': 2.1,
                'deviation': 0.05,
            }),
            MockTransition('R2', is_reversible=True, validation_result={
                'status': 'valid',
                'k_ratio': 1.5,
                'k_eq': 1.6,
                'deviation': 0.067,
            }),
        ])
        
        from shypn.engine.simulation.controller import SimulationController
        controller = SimulationController(model, verbose=False)
        
        result = controller.validate_thermodynamics()
        
        assert result is not None
        assert result['summary']['total'] == 2
        assert result['summary']['valid'] == 2
        assert result['summary']['violations'] == 0
        assert result['summary']['warnings'] == 0
        assert len(result['valid']) == 2
    
    def test_validate_thermodynamics_violations(self):
        """Test validation with violations."""
        model = MockModel(transitions=[
            MockTransition('R1', is_reversible=True, validation_result={
                'status': 'violation',
                'k_ratio': 10.0,
                'k_eq': 2.0,
                'deviation': 5.0,
                'message': 'Rate constants inconsistent with equilibrium',
            }),
        ])
        
        from shypn.engine.simulation.controller import SimulationController
        controller = SimulationController(model, verbose=False)
        
        result = controller.validate_thermodynamics()
        
        assert result is not None
        assert result['summary']['total'] == 1
        assert result['summary']['violations'] == 1
        assert len(result['violations']) == 1
        assert result['violations'][0]['transition'] == 'R1'
        assert result['violations'][0]['deviation'] == 5.0
    
    def test_validate_thermodynamics_warnings(self):
        """Test validation with warnings."""
        model = MockModel(transitions=[
            MockTransition('R1', is_reversible=True, validation_result={
                'status': 'warning',
                'k_ratio': 3.0,
                'k_eq': 2.0,
                'deviation': 1.5,
                'message': 'Deviation above warning threshold',
            }),
        ])
        
        from shypn.engine.simulation.controller import SimulationController
        controller = SimulationController(model, verbose=False)
        
        result = controller.validate_thermodynamics()
        
        assert result is not None
        assert result['summary']['total'] == 1
        assert result['summary']['warnings'] == 1
        assert len(result['warnings']) == 1
        assert result['warnings'][0]['transition'] == 'R1'
    
    def test_validate_thermodynamics_insufficient_data(self):
        """Test validation with insufficient data."""
        model = MockModel(transitions=[
            MockTransition('R1', is_reversible=True, validation_result={
                'status': 'insufficient_data',
                'message': 'Could not map species to KEGG compounds',
                'reactants_mapped': 0,
                'products_mapped': 1,
            }),
            MockTransition('R2', is_reversible=True, validation_result={
                'status': 'no_rate_constants',
                'message': 'Could not extract k_forward and k_reverse',
                'parameters': ['Vmax', 'Km'],
            }),
        ])
        
        from shypn.engine.simulation.controller import SimulationController
        controller = SimulationController(model, verbose=False)
        
        result = controller.validate_thermodynamics()
        
        assert result is not None
        assert result['summary']['total'] == 2
        assert result['summary']['insufficient_data'] == 2
        assert len(result['insufficient_data']) == 2
    
    def test_validate_thermodynamics_mixed_results(self):
        """Test validation with mixed results."""
        model = MockModel(transitions=[
            MockTransition('R1', is_reversible=True, validation_result={
                'status': 'valid',
                'deviation': 0.05,
            }),
            MockTransition('R2', is_reversible=True, validation_result={
                'status': 'warning',
                'deviation': 1.2,
            }),
            MockTransition('R3', is_reversible=True, validation_result={
                'status': 'violation',
                'deviation': 3.0,
            }),
            MockTransition('R4', is_reversible=True, validation_result={
                'status': 'insufficient_data',
            }),
        ])
        
        from shypn.engine.simulation.controller import SimulationController
        controller = SimulationController(model, verbose=False)
        
        result = controller.validate_thermodynamics()
        
        assert result is not None
        assert result['summary']['total'] == 4
        assert result['summary']['valid'] == 1
        assert result['summary']['warnings'] == 1
        assert result['summary']['violations'] == 1
        assert result['summary']['insufficient_data'] == 1
    
    def test_validate_thermodynamics_no_validation_stored(self):
        """Test handling of transitions without validation results."""
        model = MockModel(transitions=[
            MockTransition('R1', is_reversible=True),  # No validation result
        ])
        
        from shypn.engine.simulation.controller import SimulationController
        controller = SimulationController(model, verbose=False)
        
        result = controller.validate_thermodynamics()
        
        assert result is not None
        assert result['summary']['total'] == 1
        assert result['summary']['insufficient_data'] == 1
        assert 'Validation not performed' in result['insufficient_data'][0]['message']
    
    def test_get_thermodynamic_summary(self):
        """Test getting validation summary."""
        model = MockModel(transitions=[
            MockTransition('R1', is_reversible=True, validation_result={
                'status': 'valid',
                'deviation': 0.05,
            }),
            MockTransition('R2', is_reversible=True, validation_result={
                'status': 'violation',
                'deviation': 3.0,
            }),
        ])
        
        from shypn.engine.simulation.controller import SimulationController
        controller = SimulationController(model, verbose=False)
        
        # First call should trigger validation
        summary = controller.get_thermodynamic_summary()
        
        assert summary is not None
        assert summary['total'] == 2
        assert summary['valid'] == 1
        assert summary['violations'] == 1
    
    def test_thermodynamic_results_caching(self):
        """Test that validation results are cached."""
        model = MockModel(transitions=[
            MockTransition('R1', is_reversible=True, validation_result={
                'status': 'valid',
            }),
        ])
        
        from shypn.engine.simulation.controller import SimulationController
        controller = SimulationController(model, verbose=False)
        
        # First validation
        result1 = controller.validate_thermodynamics()
        
        # Second call should return cached result
        result2 = controller.get_thermodynamic_summary()
        
        # Should be same object (cached)
        assert controller.thermodynamic_results is not None
        assert result2 == result1['summary']
    
    def test_thermodynamic_results_cleared_on_reset(self):
        """Test that validation results are cleared on controller reset."""
        model = MockModel(transitions=[
            MockTransition('R1', is_reversible=True, validation_result={
                'status': 'valid',
            }),
        ])
        
        from shypn.engine.simulation.controller import SimulationController
        controller = SimulationController(model, verbose=False)
        
        # Validate
        controller.validate_thermodynamics()
        assert controller.thermodynamic_results is not None
        
        # Reset controller
        controller.reset()
        
        # Results should be cleared
        assert controller.thermodynamic_results is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
