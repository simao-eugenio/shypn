"""Integration test for TopologyPanel → ReportPanel EventBus migration.

Tests that the decoupling via EventBus works correctly without requiring full GTK initialization.
These tests focus on the EventBus mechanics for topology analysis events.
"""
import pytest
from unittest.mock import Mock
from shypn.events import EventBus


class TestTopologyReportEventBusMigration:
    """Test EventBus migration between TopologyPanel and ReportPanel."""
    
    def setup_method(self):
        """Clear EventBus before each test."""
        EventBus._subscribers.clear()
        EventBus._wildcard_subscribers.clear()
    
    def test_event_emission_mechanism(self):
        """Test that topology.analyzed events can be emitted and received."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        # Subscribe as global listener (what ReportPanel does)
        EventBus.subscribe('topology.analyzed', event_handler)
        
        # Emit event (what TopologyPanel does)
        EventBus.emit('topology.analyzed', {
            'timestamp': None
        }, document_id=12345)
        
        # Verify event was received
        assert len(received_events) == 1
        assert received_events[0]['_document_id'] == 12345
    
    def test_multi_tab_document_scoping(self):
        """Test that global subscribers receive events from all documents."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        # Global subscription (what ReportPanel does)
        EventBus.subscribe('topology.analyzed', event_handler)
        
        # Emit from document 100
        EventBus.emit('topology.analyzed', {
            'timestamp': None
        }, document_id=100)
        
        # Emit from document 200
        EventBus.emit('topology.analyzed', {
            'timestamp': None
        }, document_id=200)
        
        # Global subscriber should receive both
        assert len(received_events) == 2
        assert received_events[0]['_document_id'] == 100
        assert received_events[1]['_document_id'] == 200
    
    def test_unsubscribe_mechanism(self):
        """Test that unsubscribing works correctly."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        # Subscribe
        EventBus.subscribe('topology.analyzed', event_handler)
        
        # Emit event - should be received
        EventBus.emit('topology.analyzed', {'timestamp': None}, document_id=100)
        assert len(received_events) == 1
        
        # Unsubscribe
        EventBus.unsubscribe('topology.analyzed', event_handler)
        
        # Emit another event - should NOT be received
        EventBus.emit('topology.analyzed', {'timestamp': None}, document_id=200)
        assert len(received_events) == 1  # Still 1, not 2
    
    def test_event_data_structure(self):
        """Verify topology.analyzed event has correct data structure."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        EventBus.subscribe('topology.analyzed', event_handler)
        
        # Emit event with minimal data structure
        EventBus.emit('topology.analyzed', {
            'timestamp': None
        }, document_id=12345)
        
        # Verify structure
        assert len(received_events) == 1
        event = received_events[0]
        
        # Should have _document_id injected by EventBus
        assert '_document_id' in event
        assert event['_document_id'] == 12345
        
        # Should have timestamp field
        assert 'timestamp' in event
    
    def test_multiple_analysis_updates(self):
        """Test that multiple analyzer completions all emit events."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        EventBus.subscribe('topology.analyzed', event_handler)
        
        # Simulate multiple analyzers completing
        for i in range(5):
            EventBus.emit('topology.analyzed', {
                'timestamp': i
            }, document_id=100)
        
        # All should be received
        assert len(received_events) == 5
    
    def test_event_emission_without_document_id(self):
        """Test event emission as global event (no document_id)."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        EventBus.subscribe('topology.analyzed', event_handler)
        
        # Emit without document_id (global event)
        EventBus.emit('topology.analyzed', {
            'timestamp': None
        })  # No document_id parameter
        
        # Should still emit and be received by global subscriber
        assert len(received_events) == 1
    
    def test_multiple_subscribers_receive_same_event(self):
        """Test that multiple subscribers all receive the event."""
        received_by_report = []
        received_by_other = []
        
        def report_handler(data):
            received_by_report.append(data)
        
        def other_handler(data):
            received_by_other.append(data)
        
        # Multiple subscribers
        EventBus.subscribe('topology.analyzed', report_handler)
        EventBus.subscribe('topology.analyzed', other_handler)
        
        # Emit event
        EventBus.emit('topology.analyzed', {
            'timestamp': None
        }, document_id=100)
        
        # Both should receive the event
        assert len(received_by_report) == 1
        assert len(received_by_other) == 1
    
    def test_priority_ordering(self):
        """Test that priority ordering works for multiple subscribers."""
        call_order = []
        
        def handler_low(data):
            call_order.append('low')
        
        def handler_high(data):
            call_order.append('high')
        
        # Subscribe with different priorities
        EventBus.subscribe('topology.analyzed', handler_low, priority=0)
        EventBus.subscribe('topology.analyzed', handler_high, priority=10)
        
        # Emit event
        EventBus.emit('topology.analyzed', {'timestamp': None}, document_id=100)
        
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
        EventBus.subscribe('topology.analyzed', handler_error, priority=10)
        EventBus.subscribe('topology.analyzed', handler_ok, priority=0)
        
        # Emit event - should not raise exception
        EventBus.emit('topology.analyzed', {'timestamp': None}, document_id=100)
        
        # Both handlers should have been called despite error
        assert 'error_handler_called' in call_results
        assert 'ok_handler_called' in call_results
    
    def test_combined_pathway_and_topology_events(self):
        """Test that pathway and topology events work independently."""
        pathway_events = []
        topology_events = []
        
        def pathway_handler(data):
            pathway_events.append(data)
        
        def topology_handler(data):
            topology_events.append(data)
        
        # Subscribe to both event types
        EventBus.subscribe('pathway.imported', pathway_handler)
        EventBus.subscribe('topology.analyzed', topology_handler)
        
        # Emit pathway event
        EventBus.emit('pathway.imported', {
            'source': 'kegg',
            'data': {}
        }, document_id=100)
        
        # Emit topology event
        EventBus.emit('topology.analyzed', {
            'timestamp': None
        }, document_id=100)
        
        # Each handler should only receive its own event type
        assert len(pathway_events) == 1
        assert len(topology_events) == 1
        assert 'source' in pathway_events[0]  # pathway event
        assert 'timestamp' in topology_events[0]  # topology event
    
    def test_wildcard_subscription_for_all_events(self):
        """Test that wildcard subscriptions work for monitoring all events."""
        all_events = []
        
        def all_handler(data):
            all_events.append(data)
        
        # Subscribe with wildcard to monitor all panel events
        EventBus.subscribe('*', all_handler)
        
        # Emit various events
        EventBus.emit('pathway.imported', {'source': 'kegg'}, document_id=100)
        EventBus.emit('topology.analyzed', {'timestamp': None}, document_id=100)
        
        # Wildcard should receive all events
        assert len(all_events) == 2
