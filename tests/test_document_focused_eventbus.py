"""Integration test for document.focused EventBus events during tab switching.

Tests that tab switching emits document.focused events correctly with proper data.
"""
import pytest
from unittest.mock import Mock
from shypn.events import EventBus


class TestDocumentFocusedEventBus:
    """Test EventBus integration for document.focused events."""
    
    def setup_method(self):
        """Clear EventBus before each test."""
        EventBus._subscribers.clear()
        EventBus._wildcard_subscribers.clear()
    
    def test_event_emission_mechanism(self):
        """Test that document.focused events can be emitted and received."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        # Subscribe as global listener (what panels do)
        EventBus.subscribe('document.focused', event_handler)
        
        # Simulate tab switch emission
        mock_drawing_area = Mock()
        mock_canvas_manager = Mock()
        mock_overlay_manager = Mock()
        document_id = id(mock_drawing_area)
        
        EventBus.emit('document.focused', {
            'drawing_area': mock_drawing_area,
            'canvas_manager': mock_canvas_manager,
            'overlay_manager': mock_overlay_manager,
            'page_num': 0
        }, document_id=document_id)
        
        # Verify event was received
        assert len(received_events) == 1
        assert received_events[0]['drawing_area'] == mock_drawing_area
        assert received_events[0]['canvas_manager'] == mock_canvas_manager
        assert received_events[0]['overlay_manager'] == mock_overlay_manager
        assert received_events[0]['page_num'] == 0
        assert received_events[0]['_document_id'] == document_id
    
    def test_multi_tab_switching_sequence(self):
        """Test that switching between multiple tabs emits correct events."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        # Global subscription (panels subscribe globally)
        EventBus.subscribe('document.focused', event_handler)
        
        # Create mock objects for 3 documents
        docs = []
        for i in range(3):
            mock_drawing_area = Mock()
            mock_drawing_area.mock_id = i  # Add identifier for testing
            docs.append({
                'drawing_area': mock_drawing_area,
                'canvas_manager': Mock(),
                'overlay_manager': Mock(),
                'document_id': id(mock_drawing_area)
            })
        
        # Simulate tab switching: 0 → 1 → 2 → 0
        for page_num, doc in enumerate([docs[0], docs[1], docs[2], docs[0]]):
            EventBus.emit('document.focused', {
                'drawing_area': doc['drawing_area'],
                'canvas_manager': doc['canvas_manager'],
                'overlay_manager': doc['overlay_manager'],
                'page_num': page_num % 3
            }, document_id=doc['document_id'])
        
        # Verify all switches were received
        assert len(received_events) == 4
        assert received_events[0]['drawing_area'].mock_id == 0
        assert received_events[1]['drawing_area'].mock_id == 1
        assert received_events[2]['drawing_area'].mock_id == 2
        assert received_events[3]['drawing_area'].mock_id == 0  # Back to first tab
    
    def test_document_specific_subscription(self):
        """Test that panels can subscribe to specific document events only."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        # Create two mock documents
        doc1_area = Mock()
        doc1_id = id(doc1_area)
        doc2_area = Mock()
        doc2_id = id(doc2_area)
        
        # Subscribe to only doc1 events
        EventBus.subscribe('document.focused', event_handler, document_id=doc1_id)
        
        # Emit event for doc1
        EventBus.emit('document.focused', {
            'drawing_area': doc1_area,
            'canvas_manager': Mock(),
            'overlay_manager': Mock(),
            'page_num': 0
        }, document_id=doc1_id)
        
        # Emit event for doc2
        EventBus.emit('document.focused', {
            'drawing_area': doc2_area,
            'canvas_manager': Mock(),
            'overlay_manager': Mock(),
            'page_num': 1
        }, document_id=doc2_id)
        
        # Should only receive doc1 event
        assert len(received_events) == 1
        assert received_events[0]['drawing_area'] == doc1_area
    
    def test_event_data_structure(self):
        """Verify document.focused event has correct data structure."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data)
        
        EventBus.subscribe('document.focused', event_handler)
        
        # Create complete mock data
        mock_area = Mock()
        mock_canvas = Mock()
        mock_overlay = Mock()
        
        # Emit event
        EventBus.emit('document.focused', {
            'drawing_area': mock_area,
            'canvas_manager': mock_canvas,
            'overlay_manager': mock_overlay,
            'page_num': 2
        }, document_id=id(mock_area))
        
        # Verify structure
        assert len(received_events) == 1
        event = received_events[0]
        
        # Should have all required fields
        assert 'drawing_area' in event
        assert 'canvas_manager' in event
        assert 'overlay_manager' in event
        assert 'page_num' in event
        assert '_document_id' in event  # Injected by EventBus
        
        # Verify types
        assert event['drawing_area'] == mock_area
        assert event['canvas_manager'] == mock_canvas
        assert event['overlay_manager'] == mock_overlay
        assert event['page_num'] == 2
    
    def test_multiple_panels_receive_same_event(self):
        """Test that multiple panels all receive tab switch events."""
        report_panel_events = []
        topology_panel_events = []
        pathway_panel_events = []
        
        def report_handler(data):
            report_panel_events.append(data)
        
        def topology_handler(data):
            topology_panel_events.append(data)
        
        def pathway_handler(data):
            pathway_panel_events.append(data)
        
        # All panels subscribe
        EventBus.subscribe('document.focused', report_handler)
        EventBus.subscribe('document.focused', topology_handler)
        EventBus.subscribe('document.focused', pathway_handler)
        
        # Emit tab switch event
        mock_area = Mock()
        EventBus.emit('document.focused', {
            'drawing_area': mock_area,
            'canvas_manager': Mock(),
            'overlay_manager': Mock(),
            'page_num': 0
        }, document_id=id(mock_area))
        
        # All panels should receive the event
        assert len(report_panel_events) == 1
        assert len(topology_panel_events) == 1
        assert len(pathway_panel_events) == 1
    
    def test_priority_ordering_for_panels(self):
        """Test that panel updates happen in priority order."""
        call_order = []
        
        def low_priority_handler(data):
            call_order.append('low')
        
        def high_priority_handler(data):
            call_order.append('high')
        
        # Subscribe with different priorities
        # Higher priority = updated first
        EventBus.subscribe('document.focused', low_priority_handler, priority=0)
        EventBus.subscribe('document.focused', high_priority_handler, priority=10)
        
        # Emit event
        mock_area = Mock()
        EventBus.emit('document.focused', {
            'drawing_area': mock_area,
            'canvas_manager': Mock(),
            'overlay_manager': Mock(),
            'page_num': 0
        }, document_id=id(mock_area))
        
        # High priority should be called first
        assert call_order == ['high', 'low']
    
    def test_unsubscribe_on_panel_cleanup(self):
        """Test that panels can unsubscribe when cleaned up."""
        received_events = []
        
        def panel_handler(data):
            received_events.append(data)
        
        # Subscribe
        EventBus.subscribe('document.focused', panel_handler)
        
        # Emit event - should be received
        mock_area1 = Mock()
        EventBus.emit('document.focused', {
            'drawing_area': mock_area1,
            'canvas_manager': Mock(),
            'overlay_manager': Mock(),
            'page_num': 0
        }, document_id=id(mock_area1))
        assert len(received_events) == 1
        
        # Panel cleanup - unsubscribe
        EventBus.unsubscribe('document.focused', panel_handler)
        
        # Emit another event - should NOT be received
        mock_area2 = Mock()
        EventBus.emit('document.focused', {
            'drawing_area': mock_area2,
            'canvas_manager': Mock(),
            'overlay_manager': Mock(),
            'page_num': 1
        }, document_id=id(mock_area2))
        assert len(received_events) == 1  # Still 1, not 2
    
    def test_error_isolation_between_panels(self):
        """Test that one panel's error doesn't prevent others from receiving events."""
        call_results = []
        
        def error_handler(data):
            call_results.append('error_handler_called')
            raise ValueError("Test error in panel handler")
        
        def ok_handler(data):
            call_results.append('ok_handler_called')
        
        # Subscribe both handlers
        EventBus.subscribe('document.focused', error_handler, priority=10)
        EventBus.subscribe('document.focused', ok_handler, priority=0)
        
        # Emit event - should not raise exception
        mock_area = Mock()
        EventBus.emit('document.focused', {
            'drawing_area': mock_area,
            'canvas_manager': Mock(),
            'overlay_manager': Mock(),
            'page_num': 0
        }, document_id=id(mock_area))
        
        # Both handlers should have been called despite error
        assert 'error_handler_called' in call_results
        assert 'ok_handler_called' in call_results
    
    def test_rapid_tab_switching(self):
        """Test rapid tab switching produces correct event sequence."""
        received_events = []
        
        def event_handler(data):
            received_events.append(data['page_num'])
        
        EventBus.subscribe('document.focused', event_handler)
        
        # Simulate rapid switching between 3 tabs
        for i in range(20):
            page_num = i % 3
            mock_area = Mock()
            EventBus.emit('document.focused', {
                'drawing_area': mock_area,
                'canvas_manager': Mock(),
                'overlay_manager': Mock(),
                'page_num': page_num
            }, document_id=id(mock_area))
        
        # All 20 events should be received
        assert len(received_events) == 20
        assert received_events == [i % 3 for i in range(20)]
    
    def test_wildcard_subscription_for_all_document_events(self):
        """Test that wildcard subscriptions receive document.* events."""
        received_events = []
        
        def wildcard_handler(data):
            received_events.append(data)
        
        # Subscribe to all document.* events
        EventBus.subscribe('document.*', wildcard_handler)
        
        # Emit document.focused
        mock_area = Mock()
        EventBus.emit('document.focused', {
            'drawing_area': mock_area,
            'canvas_manager': Mock(),
            'overlay_manager': Mock(),
            'page_num': 0
        }, document_id=id(mock_area))
        
        # Wildcard should receive it
        assert len(received_events) == 1
        assert received_events[0]['page_num'] == 0
