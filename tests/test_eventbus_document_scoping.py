"""Unit tests for EventBus document-scoped event routing.

Tests verify that events with document_id only reach subscribers for that
specific document, while global subscribers receive all events.
"""
import pytest
from unittest.mock import Mock
from shypn.events import EventBus


class TestEventBusDocumentScoping:
    """Test document-scoped event routing."""
    
    def setup_method(self):
        """Clear EventBus before each test."""
        EventBus._subscribers.clear()
        EventBus._wildcard_subscribers.clear()
    
    def test_global_subscriber_receives_all_events(self):
        """Global subscribers (no document_id) should receive ALL events."""
        handler = Mock()
        
        # Subscribe globally (no document_id)
        EventBus.subscribe('model.changed', handler)
        
        # Emit events for different documents
        EventBus.emit('model.changed', {'action': 'doc1'}, document_id=100)
        EventBus.emit('model.changed', {'action': 'doc2'}, document_id=200)
        EventBus.emit('model.changed', {'action': 'global'})  # No document_id
        
        # Global subscriber should receive all 3 events
        assert handler.call_count == 3
        assert handler.call_args_list[0][0][0]['action'] == 'doc1'
        assert handler.call_args_list[1][0][0]['action'] == 'doc2'
        assert handler.call_args_list[2][0][0]['action'] == 'global'
    
    def test_document_subscriber_receives_only_matching_events(self):
        """Document-specific subscribers should only receive events for their document."""
        handler_doc1 = Mock()
        handler_doc2 = Mock()
        
        # Subscribe to specific documents
        EventBus.subscribe('model.changed', handler_doc1, document_id=100)
        EventBus.subscribe('model.changed', handler_doc2, document_id=200)
        
        # Emit events for different documents
        EventBus.emit('model.changed', {'action': 'doc1'}, document_id=100)
        EventBus.emit('model.changed', {'action': 'doc2'}, document_id=200)
        EventBus.emit('model.changed', {'action': 'doc3'}, document_id=300)
        
        # Each handler should only receive its own document's event
        assert handler_doc1.call_count == 1
        assert handler_doc1.call_args[0][0]['action'] == 'doc1'
        
        assert handler_doc2.call_count == 1
        assert handler_doc2.call_args[0][0]['action'] == 'doc2'
    
    def test_document_subscriber_ignores_global_events(self):
        """Document-specific subscribers should NOT receive global events (no document_id)."""
        handler = Mock()
        
        # Subscribe to specific document
        EventBus.subscribe('model.changed', handler, document_id=100)
        
        # Emit global event (no document_id)
        EventBus.emit('model.changed', {'action': 'global'})
        
        # Document-specific subscriber should NOT receive global event
        assert handler.call_count == 0
    
    def test_mixed_global_and_document_subscribers(self):
        """Test mixture of global and document-specific subscribers."""
        global_handler = Mock()
        doc1_handler = Mock()
        doc2_handler = Mock()
        
        # Mix of global and document-specific subscriptions
        EventBus.subscribe('model.changed', global_handler)  # Global
        EventBus.subscribe('model.changed', doc1_handler, document_id=100)
        EventBus.subscribe('model.changed', doc2_handler, document_id=200)
        
        # Emit event for document 100
        EventBus.emit('model.changed', {'action': 'doc1'}, document_id=100)
        
        # Global + doc1 should receive, doc2 should not
        assert global_handler.call_count == 1
        assert doc1_handler.call_count == 1
        assert doc2_handler.call_count == 0
    
    def test_wildcard_subscription_with_document_scoping(self):
        """Wildcard subscriptions should also respect document scoping."""
        global_handler = Mock()
        doc1_handler = Mock()
        
        # Wildcard subscriptions
        EventBus.subscribe('model.*', global_handler)  # Global wildcard
        EventBus.subscribe('model.*', doc1_handler, document_id=100)  # Doc-specific wildcard
        
        # Emit events
        EventBus.emit('model.changed', {'action': 'doc1'}, document_id=100)
        EventBus.emit('model.loaded', {'action': 'doc2'}, document_id=200)
        
        # Global receives both, doc1 only receives its own
        assert global_handler.call_count == 2
        assert doc1_handler.call_count == 1
        assert doc1_handler.call_args[0][0]['action'] == 'doc1'
    
    def test_unsubscribe_document_specific(self):
        """Unsubscribe should work correctly with document_id."""
        handler = Mock()
        
        # Subscribe to two documents
        EventBus.subscribe('model.changed', handler, document_id=100)
        EventBus.subscribe('model.changed', handler, document_id=200)
        
        # Unsubscribe from document 100 only
        EventBus.unsubscribe('model.changed', handler, document_id=100)
        
        # Emit events
        EventBus.emit('model.changed', {'action': 'doc1'}, document_id=100)
        EventBus.emit('model.changed', {'action': 'doc2'}, document_id=200)
        
        # Should only receive event from document 200
        assert handler.call_count == 1
        assert handler.call_args[0][0]['action'] == 'doc2'
    
    def test_unsubscribe_global_keeps_document_subscriptions(self):
        """Unsubscribing globally should not affect document-specific subscriptions."""
        handler = Mock()
        
        # Subscribe both globally and to specific document
        EventBus.subscribe('model.changed', handler)  # Global
        EventBus.subscribe('model.changed', handler, document_id=100)
        
        # Unsubscribe globally only
        EventBus.unsubscribe('model.changed', handler)  # No document_id = global
        
        # Emit event for document 100
        EventBus.emit('model.changed', {'action': 'doc1'}, document_id=100)
        
        # Should still receive via document-specific subscription
        assert handler.call_count == 1
    
    def test_event_data_includes_document_id(self):
        """Event data should include _document_id field for convenience."""
        handler = Mock()
        
        EventBus.subscribe('model.changed', handler)
        EventBus.emit('model.changed', {'value': 42}, document_id=100)
        
        # Handler should receive data with _document_id injected
        data = handler.call_args[0][0]
        assert data['value'] == 42
        assert data['_document_id'] == 100
    
    def test_priority_ordering_with_document_scoping(self):
        """Priority ordering should work correctly with document scoping."""
        calls = []
        
        def handler_low(data):
            calls.append('low')
        
        def handler_high(data):
            calls.append('high')
        
        # Subscribe with different priorities for same document
        EventBus.subscribe('model.changed', handler_low, document_id=100, priority=0)
        EventBus.subscribe('model.changed', handler_high, document_id=100, priority=10)
        
        # Emit event
        EventBus.emit('model.changed', {}, document_id=100)
        
        # High priority should be called first
        assert calls == ['high', 'low']
    
    def test_error_isolation_with_document_scoping(self):
        """Errors in one subscriber should not prevent others from receiving events."""
        calls = []
        
        def handler_error(data):
            raise ValueError("Test error")
        
        def handler_ok(data):
            calls.append('ok')
        
        # Subscribe both to same document
        EventBus.subscribe('model.changed', handler_error, document_id=100, priority=10)
        EventBus.subscribe('model.changed', handler_ok, document_id=100, priority=0)
        
        # Emit event - should not raise exception
        EventBus.emit('model.changed', {}, document_id=100)
        
        # Second handler should still be called despite first handler error
        assert calls == ['ok']
    
    def test_realistic_multi_tab_scenario(self):
        """Simulate realistic multi-tab scenario with panels subscribing to events."""
        # Simulate 2 tabs open, each with a report panel
        tab1_report_updates = []
        tab2_report_updates = []
        
        def tab1_report_handler(data):
            tab1_report_updates.append(data['message'])
        
        def tab2_report_handler(data):
            tab2_report_updates.append(data['message'])
        
        # Each tab's report panel subscribes with its document_id
        # IMPORTANT: Keep references to prevent garbage collection and ID reuse
        drawing_area_tab1 = object()  # Simulate drawing_area for tab 1
        drawing_area_tab2 = object()  # Simulate drawing_area for tab 2
        doc_id_tab1 = id(drawing_area_tab1)
        doc_id_tab2 = id(drawing_area_tab2)
        
        EventBus.subscribe('pathway.imported', tab1_report_handler, document_id=doc_id_tab1)
        EventBus.subscribe('pathway.imported', tab2_report_handler, document_id=doc_id_tab2)
        
        # User imports pathway in tab 1
        EventBus.emit('pathway.imported', {'message': 'Imported hsa00010'}, document_id=doc_id_tab1)
        
        # User imports pathway in tab 2
        EventBus.emit('pathway.imported', {'message': 'Imported hsa00020'}, document_id=doc_id_tab2)
        
        # Each panel should only see its own tab's import
        assert tab1_report_updates == ['Imported hsa00010']
        assert tab2_report_updates == ['Imported hsa00020']
    
    def test_document_id_zero_is_valid(self):
        """Document ID of 0 should be treated as valid (not confused with None)."""
        handler = Mock()
        
        # Subscribe with document_id=0 (technically valid, though unlikely with id())
        EventBus.subscribe('model.changed', handler, document_id=0)
        
        # Emit event for document 0
        EventBus.emit('model.changed', {}, document_id=0)
        
        # Should receive event
        assert handler.call_count == 1
        
        # Should NOT receive event for different document
        EventBus.emit('model.changed', {}, document_id=100)
        assert handler.call_count == 1  # Still 1
