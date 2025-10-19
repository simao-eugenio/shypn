"""Tests for hub analyzer."""

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


def create_hub_model():
    """Create model with a central hub place (P1 connected to many transitions)."""
    model = MockModel()
    
    # Central hub place
    model.add_place(MockPlace(1, "ATP"))  # Hub
    
    # Many transitions connected to hub
    for i in range(5):
        trans_id = 10 + i
        place_id = 20 + i
        
        model.add_transition(MockTransition(trans_id, f"T{i}"))
        model.add_place(MockPlace(place_id, f"P{i}"))
        
        # Connect: Pi -> Ti -> ATP (hub)
        model.add_arc(MockArc(place_id, trans_id))
        model.add_arc(MockArc(trans_id, 1))  # To hub
        
        # Also: ATP (hub) -> Ti+5 -> Pi+5
        trans_id2 = 30 + i
        place_id2 = 40 + i
        
        model.add_transition(MockTransition(trans_id2, f"T{i+5}"))
        model.add_place(MockPlace(place_id2, f"P{i+5}"))
        
        model.add_arc(MockArc(1, trans_id2))  # From hub
        model.add_arc(MockArc(trans_id2, place_id2))
    
    return model


def create_no_hub_model():
    """Create model with no hubs (all nodes have low degree)."""
    model = MockModel()
    
    # Simple chain: P1 -> T1 -> P2 -> T2 -> P3
    model.add_place(MockPlace(1, "P1"))
    model.add_place(MockPlace(2, "P2"))
    model.add_place(MockPlace(3, "P3"))
    
    model.add_transition(MockTransition(4, "T1"))
    model.add_transition(MockTransition(5, "T2"))
    
    model.add_arc(MockArc(1, 4))
    model.add_arc(MockArc(4, 2))
    model.add_arc(MockArc(2, 5))
    model.add_arc(MockArc(5, 3))
    
    return model


class TestHubAnalyzer:
    """Tests for HubAnalyzer class."""
    
    def test_import(self):
        """Test that HubAnalyzer can be imported."""
        from shypn.topology.network import HubAnalyzer
        assert HubAnalyzer is not None
    
    def test_detect_hub(self):
        """Test hub detection on model with central hub."""
        from shypn.topology.network import HubAnalyzer
        
        model = create_hub_model()
        analyzer = HubAnalyzer(model)
        
        result = analyzer.analyze(min_degree=5)
        
        assert result.success
        assert result.get('count') >= 1
        
        hubs = result.get('hubs', [])
        assert len(hubs) >= 1
        
        # ATP should be detected as hub (has many connections)
        atp_hub = next((h for h in hubs if h['name'] == 'ATP'), None)
        assert atp_hub is not None
        assert atp_hub['degree'] >= 10  # Many connections
    
    def test_no_hubs(self):
        """Test model with no hubs."""
        from shypn.topology.network import HubAnalyzer
        
        model = create_no_hub_model()
        analyzer = HubAnalyzer(model)
        
        result = analyzer.analyze(min_degree=5)
        
        assert result.success
        assert result.get('count') == 0  # No hubs with degree >= 5
    
    def test_place_hubs_only(self):
        """Test finding place hubs only."""
        from shypn.topology.network import HubAnalyzer
        
        model = create_hub_model()
        analyzer = HubAnalyzer(model)
        
        result = analyzer.find_place_hubs(min_degree=5)
        
        assert result.success
        
        hubs = result.get('hubs', [])
        # All returned hubs should be places
        for hub in hubs:
            assert hub['type'] == 'place'
    
    def test_transition_hubs_only(self):
        """Test finding transition hubs only."""
        from shypn.topology.network import HubAnalyzer
        
        model = create_hub_model()
        analyzer = HubAnalyzer(model)
        
        result = analyzer.find_transition_hubs(min_degree=3)
        
        assert result.success
        
        hubs = result.get('hubs', [])
        # All returned hubs should be transitions
        for hub in hubs:
            assert hub['type'] == 'transition'
    
    def test_is_hub(self):
        """Test is_hub method."""
        from shypn.topology.network import HubAnalyzer
        
        model = create_hub_model()
        analyzer = HubAnalyzer(model)
        
        # ATP (id=1) should be a hub
        assert analyzer.is_hub(1, min_degree=5) == True
        
        # Other places likely not hubs
        assert analyzer.is_hub(20, min_degree=5) == False
    
    def test_get_node_degree_info(self):
        """Test getting degree info for specific node."""
        from shypn.topology.network import HubAnalyzer
        
        model = create_hub_model()
        analyzer = HubAnalyzer(model)
        
        info = analyzer.get_node_degree_info(1)  # ATP hub
        
        assert info is not None
        assert 'degree' in info
        assert 'in_degree' in info
        assert 'out_degree' in info
        assert 'is_hub' in info
        assert info['degree'] >= 10
        assert info['is_hub'] == True
    
    def test_get_node_degree_info_invalid(self):
        """Test getting degree info for invalid node."""
        from shypn.topology.network import HubAnalyzer
        
        model = create_hub_model()
        analyzer = HubAnalyzer(model)
        
        info = analyzer.get_node_degree_info(999)
        
        assert info is None
    
    def test_top_n_limit(self):
        """Test top_n parameter."""
        from shypn.topology.network import HubAnalyzer
        
        model = create_hub_model()
        analyzer = HubAnalyzer(model)
        
        result = analyzer.analyze(min_degree=1, top_n=3)
        
        assert result.success
        
        hubs = result.get('hubs', [])
        assert len(hubs) <= 3
    
    def test_hub_structure(self):
        """Test that hub has expected fields."""
        from shypn.topology.network import HubAnalyzer
        
        model = create_hub_model()
        analyzer = HubAnalyzer(model)
        
        result = analyzer.analyze(min_degree=5)
        
        assert result.success
        
        hubs = result.get('hubs', [])
        if len(hubs) > 0:
            hub = hubs[0]
            
            assert 'id' in hub
            assert 'name' in hub
            assert 'type' in hub
            assert 'degree' in hub
            assert 'in_degree' in hub
            assert 'out_degree' in hub
            assert 'weighted_degree' in hub
    
    def test_invalid_model(self):
        """Test with None model (should raise error)."""
        from shypn.topology.network import HubAnalyzer
        from shypn.topology.base import InvalidModelError
        
        with pytest.raises(InvalidModelError):
            analyzer = HubAnalyzer(None)
    
    def test_empty_model(self):
        """Test with empty model."""
        from shypn.topology.network import HubAnalyzer
        
        model = MockModel()
        analyzer = HubAnalyzer(model)
        
        result = analyzer.analyze()
        
        assert result.success
        assert result.get('count') == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
