"""Integration test for DynamicAnalysesPanel → ReportPanel EventBus migration.

Tests that the decoupling via EventBus works correctly without requiring full GTK initialization.
These tests focus on the EventBus mechanics for simulation update events.
"""
import pytest
from unittest.mock import Mock
from shypn.events import EventBus


class TestDynamicAnalysesReportEventBusMigration:
    """Test EventBus migration between DynamicAnalysesPanel and ReportPanel."""
    
    def setup_method(self):
        """Clear EventBus before each test."""
        EventBus._subscribers.clear()
        EventBus._wildcard_subscribers.clear()
    
    def test_event_emission_mechanism(self):
        """Test that simulation.updated events can be emitted and received."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        # Subscribe as global listener (what ReportPanel does)
        EventBus.subscribe('simulation.updated', event_handler)
        
        # Emit event (what DynamicAnalysesPanel does)
        EventBus.emit('simulation.updated', {
            'transitions_count': 5,
            'places_count': 10
        }, document_id=12345)
        
        # Verify event was received
        assert len(received_events) == 1
        assert received_events[0]['transitions_count'] == 5
        assert received_events[0]['places_count'] == 10
        assert received_events[0]['_document_id'] == 12345
    
    def test_multi_tab_document_scoping(self):
        """Test that global subscribers receive events from all documents."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        # Global subscription (what ReportPanel does)
        EventBus.subscribe('simulation.updated', event_handler)
        
        # Emit from document 100
        EventBus.emit('simulation.updated', {
            'transitions_count': 3,
            'places_count': 5
        }, document_id=100)
        
        # Emit from document 200
        EventBus.emit('simulation.updated', {
            'transitions_count': 8,
            'places_count': 12
        }, document_id=200)
        
        # Global subscriber should receive both
        assert len(received_events) == 2
        assert received_events[0]['_document_id'] == 100
        assert received_events[0]['transitions_count'] == 3
        assert received_events[1]['_document_id'] == 200
        assert received_events[1]['transitions_count'] == 8
    
    def test_unsubscribe_mechanism(self):
        """Test that unsubscribing works correctly."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        # Subscribe
        EventBus.subscribe('simulation.updated', event_handler)
        
        # Emit event - should be received
        EventBus.emit('simulation.updated', {
            'transitions_count': 1,
            'places_count': 1
        }, document_id=100)
        assert len(received_events) == 1
        
        # Unsubscribe
        EventBus.unsubscribe('simulation.updated', event_handler)
        
        # Emit another event - should NOT be received
        EventBus.emit('simulation.updated', {
            'transitions_count': 2,
            'places_count': 2
        }, document_id=200)
        assert len(received_events) == 1  # Still 1, not 2
    
    def test_event_data_structure(self):
        """Verify simulation.updated event has correct data structure."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        EventBus.subscribe('simulation.updated', event_handler)
        
        # Emit event with simulation statistics
        EventBus.emit('simulation.updated', {
            'transitions_count': 15,
            'places_count': 25
        }, document_id=12345)
        
        # Verify structure
        assert len(received_events) == 1
        event = received_events[0]
        
        # Should have _document_id injected by EventBus
        assert '_document_id' in event
        assert event['_document_id'] == 12345
        
        # Should have count fields
        assert 'transitions_count' in event
        assert 'places_count' in event
        assert event['transitions_count'] == 15
        assert event['places_count'] == 25
    
    def test_multiple_simulation_updates(self):
        """Test that multiple simulation updates all emit events."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        EventBus.subscribe('simulation.updated', event_handler)
        
        # Simulate multiple updates during simulation
        for i in range(10):
            EventBus.emit('simulation.updated', {
                'transitions_count': i,
                'places_count': i * 2
            }, document_id=100)
        
        # All should be received
        assert len(received_events) == 10
        assert received_events[5]['transitions_count'] == 5
        assert received_events[5]['places_count'] == 10
    
    def test_event_emission_without_document_id(self):
        """Test event emission as global event (no document_id)."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        EventBus.subscribe('simulation.updated', event_handler)
        
        # Emit without document_id (global event)
        EventBus.emit('simulation.updated', {
            'transitions_count': 0,
            'places_count': 0
        })  # No document_id parameter
        
        # Should still emit and be received by global subscriber
        assert len(received_events) == 1
        assert received_events[0]['transitions_count'] == 0
    
    def test_multiple_subscribers_receive_same_event(self):
        """Test that multiple subscribers all receive the event."""
        received_by_report = []
        received_by_other = []
        
        def report_handler(data):
            received_by_report.append(data)
        
        def other_handler(data):
            received_by_other.append(data)
        
        # Multiple subscribers
        EventBus.subscribe('simulation.updated', report_handler)
        EventBus.subscribe('simulation.updated', other_handler)
        
        # Emit event
        EventBus.emit('simulation.updated', {
            'transitions_count': 7,
            'places_count': 14
        }, document_id=100)
        
        # Both should receive the event
        assert len(received_by_report) == 1
        assert len(received_by_other) == 1
        assert received_by_report[0]['transitions_count'] == 7
        assert received_by_other[0]['places_count'] == 14
    
    def test_priority_ordering(self):
        """Test that priority ordering works for multiple subscribers."""
        call_order = []
        
        def handler_low(data):
            call_order.append('low')
        
        def handler_high(data):
            call_order.append('high')
        
        # Subscribe with different priorities
        EventBus.subscribe('simulation.updated', handler_low, priority=0)
        EventBus.subscribe('simulation.updated', handler_high, priority=10)
        
        # Emit event
        EventBus.emit('simulation.updated', {
            'transitions_count': 1,
            'places_count': 1
        }, document_id=100)
        
        # High priority should be called first
        assert call_order == ['high', 'low']
    
    def test_error_isolation(self):
        """Test that one handler's error doesn't prevent others from receiving events."""
        call_results = []
        
        def handler_error(data):
            call_results.append('error_handler_called')
            raise ValueError("Test error")
        
        def handler_ok(data):
            call_results.append('ok_handler_called')
        
        # Subscribe both handlers
        EventBus.subscribe('simulation.updated', handler_error, priority=10)
        EventBus.subscribe('simulation.updated', handler_ok, priority=0)
        
        # Emit event - should not raise exception
        EventBus.emit('simulation.updated', {
            'transitions_count': 1,
            'places_count': 1
        }, document_id=100)
        
        # Both handlers should have been called despite error
        assert 'error_handler_called' in call_results
        assert 'ok_handler_called' in call_results
    
    def test_combined_all_panel_events(self):
        """Test that all three panel events work independently."""
        pathway_events = []
        topology_events = []
        simulation_events = []
        
        def pathway_handler(data):
            pathway_events.append(data)
        
        def topology_handler(data):
            topology_events.append(data)
        
        def simulation_handler(data):
            simulation_events.append(data)
        
        # Subscribe to all three event types
        EventBus.subscribe('pathway.imported', pathway_handler)
        EventBus.subscribe('topology.analyzed', topology_handler)
        EventBus.subscribe('simulation.updated', simulation_handler)
        
        # Emit all three events
        EventBus.emit('pathway.imported', {'source': 'kegg'}, document_id=100)
        EventBus.emit('topology.analyzed', {'timestamp': None}, document_id=100)
        EventBus.emit('simulation.updated', {'transitions_count': 5, 'places_count': 10}, document_id=100)
        
        # Each handler should only receive its own event type
        assert len(pathway_events) == 1
        assert len(topology_events) == 1
        assert len(simulation_events) == 1
        assert 'source' in pathway_events[0]  # pathway event
        assert 'timestamp' in topology_events[0]  # topology event
        assert 'transitions_count' in simulation_events[0]  # simulation event
    
    def test_realistic_simulation_scenario(self):
        """Test realistic simulation monitoring scenario."""
        received_updates = []
        
        def report_handler(data):
            received_updates.append(data)
        
        # ReportPanel subscribes
        EventBus.subscribe('simulation.updated', report_handler)
        
        # Simulate a running simulation sending periodic updates
        doc_id = 12345
        
        # Initial state: no monitoring
        EventBus.emit('simulation.updated', {
            'transitions_count': 0,
            'places_count': 0
        }, document_id=doc_id)
        
        # User selects some transitions and places to monitor
        EventBus.emit('simulation.updated', {
            'transitions_count': 3,
            'places_count': 5
        }, document_id=doc_id)
        
        # Simulation continues, counts stay same
        EventBus.emit('simulation.updated', {
            'transitions_count': 3,
            'places_count': 5
        }, document_id=doc_id)
        
        # User adds more elements to monitor
        EventBus.emit('simulation.updated', {
            'transitions_count': 7,
            'places_count': 12
        }, document_id=doc_id)
        
        # Verify all updates received
        assert len(received_updates) == 4
        assert received_updates[0]['transitions_count'] == 0
        assert received_updates[1]['transitions_count'] == 3
        assert received_updates[3]['transitions_count'] == 7
