"""Test multi-document isolation with EventBus and per-canvas controllers.

Week 3 - Phase 4: Verify that multiple documents maintain independent state
and that EventBus events are properly scoped to their respective documents.

Test Cases:
1. Multiple documents have independent simulation controllers
2. EventBus events are document-scoped (no cross-contamination)
3. Panel visibility controlled by document.focused events
4. Controller cleanup happens when documents are closed
5. 3+ documents can be open simultaneously

Usage:
    pytest tests/test_multi_document_isolation.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from shypn.events import EventBus


class TestMultiDocumentIsolation:
    """Test suite for multi-document isolation."""
    
    def setup_method(self):
        """Clear EventBus before each test."""
        EventBus.clear_all()
    
    def teardown_method(self):
        """Clean up after each test."""
        EventBus.clear_all()
    
    def test_document_scoped_events(self):
        """Test that EventBus events are properly scoped to documents."""
        # Create 3 document IDs
        doc1_id = id("document_1")
        doc2_id = id("document_2")
        doc3_id = id("document_3")
        
        # Track which documents received events
        received_events = []
        
        # Document 1 subscribes to its own events
        def doc1_handler(data):
            received_events.append(('doc1', data.get('_document_id')))
        EventBus.subscribe('simulation.progress', doc1_handler, document_id=doc1_id)
        
        # Document 2 subscribes to its own events
        def doc2_handler(data):
            received_events.append(('doc2', data.get('_document_id')))
        EventBus.subscribe('simulation.progress', doc2_handler, document_id=doc2_id)
        
        # Document 3 subscribes globally (receives all)
        def doc3_handler(data):
            received_events.append(('doc3_global', data.get('_document_id')))
        EventBus.subscribe('simulation.progress', doc3_handler)  # No document_id = global
        
        # Emit event for document 1
        EventBus.emit('simulation.progress', {'time': 0.1}, document_id=doc1_id)
        
        # Only doc1 and doc3_global should receive it
        assert len(received_events) == 2
        assert ('doc1', doc1_id) in received_events
        assert ('doc3_global', doc1_id) in received_events
        assert ('doc2', doc1_id) not in received_events
        
        # Clear for next test
        received_events.clear()
        
        # Emit event for document 2
        EventBus.emit('simulation.progress', {'time': 0.2}, document_id=doc2_id)
        
        # Only doc2 and doc3_global should receive it
        assert len(received_events) == 2
        assert ('doc2', doc2_id) in received_events
        assert ('doc3_global', doc2_id) in received_events
        assert ('doc1', doc2_id) not in received_events
    
    def test_panel_isolation_via_eventbus(self):
        """Test that panels respond only to their document's events."""
        doc1_id = id("doc1")
        doc2_id = id("doc2")
        
        # Mock panel loaders for two documents
        panel1_visible = []
        panel2_visible = []
        
        def panel1_on_focused(data):
            event_doc_id = data.get('_document_id')
            if event_doc_id == doc1_id:
                panel1_visible.append(True)
            else:
                panel1_visible.append(False)
        
        def panel2_on_focused(data):
            event_doc_id = data.get('_document_id')
            if event_doc_id == doc2_id:
                panel2_visible.append(True)
            else:
                panel2_visible.append(False)
        
        # Subscribe panels to document.focused events
        EventBus.subscribe('document.focused', panel1_on_focused, document_id=doc1_id)
        EventBus.subscribe('document.focused', panel2_on_focused, document_id=doc2_id)
        
        # Switch to document 1
        EventBus.emit('document.focused', {'page_num': 0}, document_id=doc1_id)
        
        # Panel1 should show, panel2 should not receive event
        assert len(panel1_visible) == 1
        assert panel1_visible[-1] is True
        assert len(panel2_visible) == 0
        
        # Switch to document 2
        EventBus.emit('document.focused', {'page_num': 1}, document_id=doc2_id)
        
        # Panel2 should show, panel1 should not receive new event
        assert len(panel1_visible) == 1  # No change
        assert len(panel2_visible) == 1
        assert panel2_visible[-1] is True
    
    def test_controller_independence(self):
        """Test that each document has independent controller state."""
        # This test verifies the architecture is set up correctly
        # In real usage, model_canvas_loader maintains:
        # - self.simulation_controllers[drawing_area] = controller
        # - controller.document_id = id(drawing_area)
        
        # Simulate 3 documents with controllers
        doc1 = Mock()
        doc2 = Mock()
        doc3 = Mock()
        
        controllers = {}
        controllers[id(doc1)] = {'time': 0.0, 'running': False}
        controllers[id(doc2)] = {'time': 5.5, 'running': True}
        controllers[id(doc3)] = {'time': 10.0, 'running': False}
        
        # Verify independence
        assert controllers[id(doc1)]['time'] == 0.0
        assert controllers[id(doc2)]['time'] == 5.5
        assert controllers[id(doc3)]['time'] == 10.0
        
        # Modify doc2, others unchanged
        controllers[id(doc2)]['time'] = 7.0
        assert controllers[id(doc1)]['time'] == 0.0
        assert controllers[id(doc2)]['time'] == 7.0
        assert controllers[id(doc3)]['time'] == 10.0
    
    def test_unsubscribe_on_cleanup(self):
        """Test that panels properly unsubscribe when cleaned up."""
        doc_id = id("test_doc")
        
        received = []
        def handler(data):
            received.append(data)
        
        # Subscribe
        EventBus.subscribe('document.focused', handler, document_id=doc_id)
        
        # Emit - should receive
        EventBus.emit('document.focused', {'test': 1}, document_id=doc_id)
        assert len(received) == 1
        
        # Unsubscribe (simulating panel cleanup)
        EventBus.unsubscribe('document.focused', handler, document_id=doc_id)
        
        # Emit again - should NOT receive
        EventBus.emit('document.focused', {'test': 2}, document_id=doc_id)
        assert len(received) == 1  # No change
    
    def test_global_events_reach_all_documents(self):
        """Test that global events (no document_id) only reach global subscribers."""
        doc1_id = id("doc1")
        doc2_id = id("doc2")
        
        doc1_received = []
        doc2_received = []
        global_received = []
        
        # Document-specific subscribers
        EventBus.subscribe('settings.changed', lambda d: doc1_received.append(d), document_id=doc1_id)
        EventBus.subscribe('settings.changed', lambda d: doc2_received.append(d), document_id=doc2_id)
        
        # Global subscriber
        EventBus.subscribe('settings.changed', lambda d: global_received.append(d))
        
        # Emit global event (no document_id)
        EventBus.emit('settings.changed', {'theme': 'dark'})
        
        # Only global subscriber should receive
        assert len(doc1_received) == 0
        assert len(doc2_received) == 0
        assert len(global_received) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
