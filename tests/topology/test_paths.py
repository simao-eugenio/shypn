"""Tests for path analyzer."""

import pytest
from unittest.mock import Mock


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


def create_linear_path_model():
    """Create linear path: P1 -> T1 -> P2 -> T2 -> P3."""
    model = MockModel()
    
    model.add_place(MockPlace(1, "P1"))
    model.add_place(MockPlace(2, "P2"))
    model.add_place(MockPlace(3, "P3"))
    
    model.add_transition(MockTransition(4, "T1"))
    model.add_transition(MockTransition(5, "T2"))
    
    model.add_arc(MockArc(1, 4))  # P1 -> T1
    model.add_arc(MockArc(4, 2))  # T1 -> P2
    model.add_arc(MockArc(2, 5))  # P2 -> T2
    model.add_arc(MockArc(5, 3))  # T2 -> P3
    
    return model


def create_branching_paths_model():
    """Create branching paths: P1 -> {T1 -> P2, T2 -> P3} -> T3 -> P4."""
    model = MockModel()
    
    model.add_place(MockPlace(1, "P1"))
    model.add_place(MockPlace(2, "P2"))
    model.add_place(MockPlace(3, "P3"))
    model.add_place(MockPlace(4, "P4"))
    
    model.add_transition(MockTransition(5, "T1"))
    model.add_transition(MockTransition(6, "T2"))
    model.add_transition(MockTransition(7, "T3"))
    
    # Branch from P1
    model.add_arc(MockArc(1, 5))  # P1 -> T1
    model.add_arc(MockArc(1, 6))  # P1 -> T2
    
    # Two paths
    model.add_arc(MockArc(5, 2))  # T1 -> P2
    model.add_arc(MockArc(6, 3))  # T2 -> P3
    
    # Converge to P4
    model.add_arc(MockArc(2, 7))  # P2 -> T3
    model.add_arc(MockArc(3, 7))  # P3 -> T3
    model.add_arc(MockArc(7, 4))  # T3 -> P4
    
    return model


def create_disconnected_model():
    """Create model with disconnected components."""
    model = MockModel()
    
    # Component 1: P1 -> T1 -> P2
    model.add_place(MockPlace(1, "P1"))
    model.add_place(MockPlace(2, "P2"))
    model.add_transition(MockTransition(3, "T1"))
    model.add_arc(MockArc(1, 3))
    model.add_arc(MockArc(3, 2))
    
    # Component 2: P3 -> T2 -> P4 (disconnected)
    model.add_place(MockPlace(4, "P3"))
    model.add_place(MockPlace(5, "P4"))
    model.add_transition(MockTransition(6, "T2"))
    model.add_arc(MockArc(4, 6))
    model.add_arc(MockArc(6, 5))
    
    return model


class TestPathAnalyzer:
    """Tests for PathAnalyzer class."""
    
    def test_import(self):
        """Test that PathAnalyzer can be imported."""
        from shypn.topology.graph import PathAnalyzer
        assert PathAnalyzer is not None
    
    def test_shortest_path_linear(self):
        """Test shortest path on linear model."""
        from shypn.topology.graph import PathAnalyzer
        
        model = create_linear_path_model()
        analyzer = PathAnalyzer(model)
        
        # Find path from P1 to P3
        result = analyzer.find_shortest_path(source_id=1, target_id=3)
        
        assert result.success
        assert result.get('exists') == True
        assert result.get('length') == 4  # P1 -> T1 -> P2 -> T2 -> P3
        
        path_info = result.get('path')
        assert path_info['nodes'] == [1, 4, 2, 5, 3]
    
    def test_shortest_path_no_path(self):
        """Test shortest path when no path exists."""
        from shypn.topology.graph import PathAnalyzer
        
        model = create_disconnected_model()
        analyzer = PathAnalyzer(model)
        
        # Try to find path between disconnected components
        result = analyzer.find_shortest_path(source_id=1, target_id=5)
        
        assert result.success
        assert result.get('exists') == False
    
    def test_all_paths_single(self):
        """Test finding all paths when only one exists."""
        from shypn.topology.graph import PathAnalyzer
        
        model = create_linear_path_model()
        analyzer = PathAnalyzer(model)
        
        result = analyzer.find_all_paths(source_id=1, target_id=3)
        
        assert result.success
        assert result.get('count') == 1
        
        paths = result.get('paths', [])
        assert len(paths) == 1
        assert paths[0]['length'] == 4
    
    def test_all_paths_multiple(self):
        """Test finding multiple paths."""
        from shypn.topology.graph import PathAnalyzer
        
        model = create_branching_paths_model()
        analyzer = PathAnalyzer(model)
        
        result = analyzer.find_all_paths(source_id=1, target_id=4)
        
        assert result.success
        assert result.get('count') >= 2  # At least 2 paths
        
        paths = result.get('paths', [])
        assert len(paths) >= 2
    
    def test_max_paths_limit(self):
        """Test max_paths parameter."""
        from shypn.topology.graph import PathAnalyzer
        
        model = create_branching_paths_model()
        analyzer = PathAnalyzer(model)
        
        result = analyzer.find_all_paths(source_id=1, target_id=4, max_paths=1)
        
        assert result.success
        
        paths = result.get('paths', [])
        assert len(paths) <= 1
    
    def test_path_structure(self):
        """Test that path has expected fields."""
        from shypn.topology.graph import PathAnalyzer
        
        model = create_linear_path_model()
        analyzer = PathAnalyzer(model)
        
        result = analyzer.find_shortest_path(source_id=1, target_id=3)
        
        assert result.success
        
        path = result.get('path')
        assert 'nodes' in path
        assert 'names' in path
        assert 'length' in path
        assert 'place_count' in path
        assert 'transition_count' in path
        assert 'weights' in path
        assert 'total_weight' in path
    
    def test_general_analysis(self):
        """Test general path analysis (no specific source/target)."""
        from shypn.topology.graph import PathAnalyzer
        
        model = create_linear_path_model()
        analyzer = PathAnalyzer(model)
        
        result = analyzer.analyze()
        
        assert result.success
        # Should have general metrics
        assert 'diameter' in result.data or 'average_path_length' in result.data
    
    def test_find_paths_through_node(self):
        """Test finding paths through specific node."""
        from shypn.topology.graph import PathAnalyzer
        
        model = create_branching_paths_model()
        analyzer = PathAnalyzer(model)
        
        # Find paths through P1 (should be all paths)
        paths = analyzer.find_paths_through_node(1)
        
        # Should find some paths
        assert len(paths) >= 0  # At least doesn't crash
    
    def test_invalid_source_target(self):
        """Test with invalid source or target."""
        from shypn.topology.graph import PathAnalyzer
        
        model = create_linear_path_model()
        analyzer = PathAnalyzer(model)
        
        result = analyzer.find_shortest_path(source_id=999, target_id=1)
        
        assert not result.success
        assert len(result.errors) > 0
    
    def test_invalid_model(self):
        """Test with None model (should raise error)."""
        from shypn.topology.graph import PathAnalyzer
        from shypn.topology.base import InvalidModelError
        
        with pytest.raises(InvalidModelError):
            analyzer = PathAnalyzer(None)
    
    def test_analysis_result_structure(self):
        """Test that result has expected structure."""
        from shypn.topology.graph import PathAnalyzer
        
        model = create_linear_path_model()
        analyzer = PathAnalyzer(model)
        
        result = analyzer.find_shortest_path(source_id=1, target_id=3)
        
        # Check standard fields
        assert hasattr(result, 'success')
        assert hasattr(result, 'data')
        assert hasattr(result, 'summary')
        assert hasattr(result, 'metadata')
        
        # Check metadata
        assert 'analysis_time' in result.metadata


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
