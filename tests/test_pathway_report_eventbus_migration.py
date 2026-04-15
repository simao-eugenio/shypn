"""Integration test for PathwayOperationsPanel → ReportPanel EventBus migration.

Tests that the decoupling via EventBus works correctly without requiring full GTK initialization.
These tests focus on the EventBus mechanics rather than full panel instantiation.
"""
import pytest
from unittest.mock import Mock
from shypn.events import EventBus


class TestPathwayReportEventBusMigration:
    """Test EventBus migration between PathwayOperationsPanel and ReportPanel."""
    
    def setup_method(self):
        """Clear EventBus before each test."""
        EventBus._subscribers.clear()
        EventBus._wildcard_subscribers.clear()
    
    def test_event_emission_mechanism(self):
        """Test that pathway.imported events can be emitted and received."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        # Subscribe as global listener (what ReportPanel does)
        EventBus.subscribe('pathway.imported', event_handler)
        
        # Emit event (what PathwayOperationsPanel does)
        EventBus.emit('pathway.imported', {
            'source': 'kegg',
            'data': {'pathway_id': 'hsa00010'}
        }, document_id=12345)
        
        # Verify event was received
        assert len(received_events) == 1
        assert received_events[0]['source'] == 'kegg'
        assert received_events[0]['data']['pathway_id'] == 'hsa00010'
        assert received_events[0]['_document_id'] == 12345
    
    def test_multi_tab_document_scoping(self):
        """Test that global subscribers receive events from all documents."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        # Global subscription (what ReportPanel does)
        EventBus.subscribe('pathway.imported', event_handler)
        
        # Emit from document 100
        EventBus.emit('pathway.imported', {
            'source': 'kegg',
            'data': {'pathway_id': 'hsa00010'}
        }, document_id=100)
        
        # Emit from document 200
        EventBus.emit('pathway.imported', {
            'source': 'sbml',
            'data': {'model_id': 'BIOMD123'}
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
        EventBus.subscribe('pathway.imported', event_handler)
        
        # Emit event - should be received
        EventBus.emit('pathway.imported', {'source': 'kegg'}, document_id=100)
        assert len(received_events) == 1
        
        # Unsubscribe
        EventBus.unsubscribe('pathway.imported', event_handler)
        
        # Emit another event - should NOT be received
        EventBus.emit('pathway.imported', {'source': 'sbml'}, document_id=200)
        assert len(received_events) == 1  # Still 1, not 2
    
    def test_event_data_structure(self):
        """Verify pathway.imported event has correct data structure."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        EventBus.subscribe('pathway.imported', event_handler)
        
        # Emit event with nested data structure
        EventBus.emit('pathway.imported', {
            'source': 'kegg',
            'data': {
                'pathway_id': 'hsa00010',
                'organism': 'hsa',
                'compounds': ['C00001', 'C00002'],
                'reactions': ['R00001', 'R00002']
            }
        }, document_id=12345)
        
        # Verify structure
        assert len(received_events) == 1
        event = received_events[0]
        
        # Should have 'source' and 'data' keys
        assert 'source' in event
        assert 'data' in event
        assert event['source'] == 'kegg'
        
        # Should have _document_id injected by EventBus
        assert '_document_id' in event
        assert event['_document_id'] == 12345
        
        # Data should be nested correctly
        assert event['data']['pathway_id'] == 'hsa00010'
        assert len(event['data']['compounds']) == 2
        assert len(event['data']['reactions']) == 2
    
    def test_multiple_import_sources(self):
        """Test that all three import sources (KEGG, SBML, BiGG) use same event."""
        received_events = {}
        
        def event_handler(data):
            source = data['source']
            received_events[source] = data
        
        EventBus.subscribe('pathway.imported', event_handler)
        
        # Emit from KEGG
        EventBus.emit('pathway.imported', {
            'source': 'kegg',
            'data': {'pathway_id': 'hsa00010'}
        }, document_id=100)
        
        # Emit from SBML
        EventBus.emit('pathway.imported', {
            'source': 'sbml',
            'data': {'model_id': 'BIOMD123'}
        }, document_id=100)
        
        # Emit from BiGG
        EventBus.emit('pathway.imported', {
            'source': 'bigg',
            'data': {'model_id': 'iJO1366'}
        }, document_id=100)
        
        # Verify all three sources emitted events
        assert 'kegg' in received_events
        assert 'sbml' in received_events
        assert 'bigg' in received_events
        
        assert received_events['kegg']['data']['pathway_id'] == 'hsa00010'
        assert received_events['sbml']['data']['model_id'] == 'BIOMD123'
        assert received_events['bigg']['data']['model_id'] == 'iJO1366'
    
    def test_event_emission_without_document_id(self):
        """Test event emission as global event (no document_id)."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        EventBus.subscribe('pathway.imported', event_handler)
        
        # Emit without document_id (global event)
        EventBus.emit('pathway.imported', {
            'source': 'kegg',
            'data': {'pathway_id': 'hsa00010'}
        })  # No document_id parameter
        
        # Should still emit and be received by global subscriber
        assert len(received_events) == 1
        assert received_events[0]['source'] == 'kegg'
    
    def test_multiple_subscribers_receive_same_event(self):
        """Test that multiple subscribers all receive the event."""
        received_by_report = []
        received_by_other = []
        
        def report_handler(data):
            received_by_report.append(data)
        
        def other_handler(data):
            received_by_other.append(data)
        
        # Multiple subscribers
        EventBus.subscribe('pathway.imported', report_handler)
        EventBus.subscribe('pathway.imported', other_handler)
        
        # Emit event
        EventBus.emit('pathway.imported', {
            'source': 'kegg',
            'data': {'pathway_id': 'hsa00010'}
        }, document_id=100)
        
        # Both should receive the event
        assert len(received_by_report) == 1
        assert len(received_by_other) == 1
        assert received_by_report[0]['source'] == 'kegg'
        assert received_by_other[0]['source'] == 'kegg'
    
    def test_priority_ordering(self):
        """Test that priority ordering works for multiple subscribers."""
        call_order = []
        
        def handler_low(data):
            call_order.append('low')
        
        def handler_high(data):
            call_order.append('high')
        
        # Subscribe with different priorities
        EventBus.subscribe('pathway.imported', handler_low, priority=0)
        EventBus.subscribe('pathway.imported', handler_high, priority=10)
        
        # Emit event
        EventBus.emit('pathway.imported', {'source': 'kegg'}, document_id=100)
        
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
        EventBus.subscribe('pathway.imported', handler_error, priority=10)
        EventBus.subscribe('pathway.imported', handler_ok, priority=0)
        
        # Emit event - should not raise exception
        EventBus.emit('pathway.imported', {'source': 'kegg'}, document_id=100)
        
        # Both handlers should have been called despite error
        assert 'error_handler_called' in call_results
        assert 'ok_handler_called' in call_results
