"""Tests for cycle analyzer."""

import pytest
from unittest.mock import Mock, MagicMock


class MockPlace:
    """Mock place object for testing."""
    def __init__(self, place_id, name=None, tokens=0):
        self.id = place_id
        self.name = name or f"P{place_id}"
        self.tokens = tokens


class MockTransition:
    """Mock transition object for testing."""
    def __init__(self, trans_id, name=None):
        self.id = trans_id
        self.name = name or f"T{trans_id}"
        self.transition_type = "immediate"


class MockArc:
    """Mock arc object for testing."""
    def __init__(self, source_id, target_id, weight=1):
        self.source_id = source_id
        self.target_id = target_id
        self.weight = weight


class MockModel:
    """Mock Petri net model for testing."""
    def __init__(self):
        self.places = []
        self.transitions = []
        self.arcs = []
    
    def add_place(self, place):
        self.places.append(place)
    
    def add_transition(self, transition):
        self.transitions.append(transition)
    
    def add_arc(self, arc):
        self.arcs.append(arc)


def create_simple_cycle_model():
    """Create a simple cycle: P1 -> T1 -> P2 -> T2 -> P1."""
    model = MockModel()
    
    # Add places
    model.add_place(MockPlace(1, "P1"))
    model.add_place(MockPlace(2, "P2"))
    
    # Add transitions
    model.add_transition(MockTransition(3, "T1"))
    model.add_transition(MockTransition(4, "T2"))
    
    # Add arcs forming cycle
    model.add_arc(MockArc(1, 3))  # P1 -> T1
    model.add_arc(MockArc(3, 2))  # T1 -> P2
    model.add_arc(MockArc(2, 4))  # P2 -> T2
    model.add_arc(MockArc(4, 1))  # T2 -> P1
    
    return model


def create_dag_model():
    """Create a DAG (no cycles): P1 -> T1 -> P2 -> T2 -> P3."""
    model = MockModel()
    
    # Add places
    model.add_place(MockPlace(1, "P1"))
    model.add_place(MockPlace(2, "P2"))
    model.add_place(MockPlace(3, "P3"))
    
    # Add transitions
    model.add_transition(MockTransition(4, "T1"))
    model.add_transition(MockTransition(5, "T2"))
    
    # Add arcs (no cycle)
    model.add_arc(MockArc(1, 4))  # P1 -> T1
    model.add_arc(MockArc(4, 2))  # T1 -> P2
    model.add_arc(MockArc(2, 5))  # P2 -> T2
    model.add_arc(MockArc(5, 3))  # T2 -> P3
    
    return model


def create_self_loop_model():
    """Create a self-loop: T1 -> P1 -> T1."""
    model = MockModel()
    
    model.add_place(MockPlace(1, "P1"))
    model.add_transition(MockTransition(2, "T1"))
    
    model.add_arc(MockArc(2, 1))  # T1 -> P1
    model.add_arc(MockArc(1, 2))  # P1 -> T1
    
    return model


def create_multiple_cycles_model():
    """Create model with two independent cycles."""
    model = MockModel()
    
    # First cycle: P1 -> T1 -> P2 -> T2 -> P1
    model.add_place(MockPlace(1, "P1"))
    model.add_place(MockPlace(2, "P2"))
    model.add_transition(MockTransition(3, "T1"))
    model.add_transition(MockTransition(4, "T2"))
    model.add_arc(MockArc(1, 3))
    model.add_arc(MockArc(3, 2))
    model.add_arc(MockArc(2, 4))
    model.add_arc(MockArc(4, 1))
    
    # Second cycle: P3 -> T3 -> P4 -> T4 -> P3
    model.add_place(MockPlace(5, "P3"))
    model.add_place(MockPlace(6, "P4"))
    model.add_transition(MockTransition(7, "T3"))
    model.add_transition(MockTransition(8, "T4"))
    model.add_arc(MockArc(5, 7))
    model.add_arc(MockArc(7, 6))
    model.add_arc(MockArc(6, 8))
    model.add_arc(MockArc(8, 5))
    
    return model


class TestCycleAnalyzer:
    """Tests for CycleAnalyzer class."""
    
    def test_import(self):
        """Test that CycleAnalyzer can be imported."""
        from shypn.topology.graph import CycleAnalyzer
        assert CycleAnalyzer is not None
    
    def test_simple_cycle(self):
        """Test cycle detection on simple cycle."""
        from shypn.topology.graph import CycleAnalyzer
        
        model = create_simple_cycle_model()
        analyzer = CycleAnalyzer(model)
        result = analyzer.analyze()
        
        assert result.success
        assert result.get('count') == 1
        
        cycles = result.get('cycles', [])
        assert len(cycles) == 1
        assert cycles[0]['length'] == 4
        assert cycles[0]['type'] == 'balanced'
    
    def test_dag_no_cycles(self):
        """Test on DAG (should find no cycles)."""
        from shypn.topology.graph import CycleAnalyzer
        
        model = create_dag_model()
        analyzer = CycleAnalyzer(model)
        result = analyzer.analyze()
        
        assert result.success
        assert result.get('count') == 0
        assert 'DAG' in result.summary or 'No cycles' in result.summary
    
    def test_self_loop(self):
        """Test self-loop detection."""
        from shypn.topology.graph import CycleAnalyzer
        
        model = create_self_loop_model()
        analyzer = CycleAnalyzer(model)
        result = analyzer.analyze()
        
        assert result.success
        assert result.get('count') == 1
        
        cycles = result.get('cycles', [])
        assert len(cycles) == 1
        assert cycles[0]['length'] == 2
        assert cycles[0]['type'] == 'self-loop'
    
    def test_multiple_cycles(self):
        """Test model with multiple independent cycles."""
        from shypn.topology.graph import CycleAnalyzer
        
        model = create_multiple_cycles_model()
        analyzer = CycleAnalyzer(model)
        result = analyzer.analyze()
        
        assert result.success
        assert result.get('count') == 2
        
        cycles = result.get('cycles', [])
        assert len(cycles) == 2
    
    def test_max_cycles_limit(self):
        """Test max_cycles parameter."""
        from shypn.topology.graph import CycleAnalyzer
        
        model = create_multiple_cycles_model()
        analyzer = CycleAnalyzer(model)
        result = analyzer.analyze(max_cycles=1)
        
        assert result.success
        
        # Should only return 1 cycle even though 2 exist
        cycles = result.get('cycles', [])
        assert len(cycles) == 1
        
        # Should mark as truncated
        assert result.get('truncated') == True
        assert result.has_warnings()
    
    def test_find_cycles_containing_node(self):
        """Test finding cycles containing specific node."""
        from shypn.topology.graph import CycleAnalyzer
        
        model = create_simple_cycle_model()
        analyzer = CycleAnalyzer(model)
        
        # Find cycles containing place 1
        place_cycles = analyzer.find_cycles_containing_node(1)
        
        assert len(place_cycles) == 1
        assert 1 in place_cycles[0]['nodes']
    
    def test_cache_invalidation(self):
        """Test cache invalidation."""
        from shypn.topology.graph import CycleAnalyzer
        
        model = create_simple_cycle_model()
        analyzer = CycleAnalyzer(model)
        
        # First analysis
        result1 = analyzer.analyze()
        assert result1.success
        
        # Invalidate cache
        analyzer.invalidate()
        
        # Should work again
        result2 = analyzer.analyze()
        assert result2.success
    
    def test_invalid_model(self):
        """Test with None model (should raise error)."""
        from shypn.topology.graph import CycleAnalyzer
        from shypn.topology.base import InvalidModelError
        
        with pytest.raises(InvalidModelError):
            analyzer = CycleAnalyzer(None)
    
    def test_analysis_result_structure(self):
        """Test that result has expected structure."""
        from shypn.topology.graph import CycleAnalyzer
        
        model = create_simple_cycle_model()
        analyzer = CycleAnalyzer(model)
        result = analyzer.analyze()
        
        # Check required fields
        assert hasattr(result, 'success')
        assert hasattr(result, 'data')
        assert hasattr(result, 'summary')
        assert hasattr(result, 'warnings')
        assert hasattr(result, 'errors')
        assert hasattr(result, 'metadata')
        
        # Check data contents
        assert 'cycles' in result.data
        assert 'count' in result.data
        assert 'longest_length' in result.data
        
        # Check metadata
        assert 'analysis_time' in result.metadata
    
    def test_cycle_info_structure(self):
        """Test that cycle info has expected fields."""
        from shypn.topology.graph import CycleAnalyzer
        
        model = create_simple_cycle_model()
        analyzer = CycleAnalyzer(model)
        result = analyzer.analyze()
        
        cycles = result.get('cycles', [])
        assert len(cycles) > 0
        
        cycle = cycles[0]
        assert 'nodes' in cycle
        assert 'length' in cycle
        assert 'names' in cycle
        assert 'place_count' in cycle
        assert 'transition_count' in cycle
        assert 'type' in cycle


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
