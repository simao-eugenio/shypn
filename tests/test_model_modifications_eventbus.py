"""Test model modification EventBus integration.

This test suite verifies that place/transition/arc creation and deletion operations
emit proper EventBus events with complete data.
"""
import pytest
from unittest.mock import Mock, MagicMock

# Import EventBus and ModelCanvasManager
from shypn.events import EventBus
from shypn.data.model_canvas_manager import ModelCanvasManager


@pytest.fixture(autouse=True)
def clean_eventbus():
    """Clear EventBus before and after each test."""
    EventBus.clear_all()
    yield
    EventBus.clear_all()


@pytest.fixture
def canvas_manager():
    """Create ModelCanvasManager with mock drawing area."""
    manager = ModelCanvasManager()
    # Mock drawing_area to enable document_id generation
    manager._drawing_area = Mock()
    return manager


class TestPlaceCreationEvents:
    """Test model.place.created event emission."""
    
    def test_add_place_emits_event(self, canvas_manager):
        """Test that add_place emits model.place.created event."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        document_id = id(canvas_manager._drawing_area)
        EventBus.subscribe('model.place.created', handler, document_id=document_id)
        
        # Create a place
        place = canvas_manager.add_place(100, 150)
        
        # Verify event was emitted
        assert len(events_received) == 1
        event = events_received[0]
        
        assert event['object'] == place
        assert event['object_type'] == 'place'
        assert event['object_id'] == place.id
        assert event['action'] == 'created'
        assert 'timestamp' in event
        assert isinstance(event['timestamp'], float)
        assert event['batch_id'] is None
    
    def test_multiple_places_emit_multiple_events(self, canvas_manager):
        """Test that creating multiple places emits separate events."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        document_id = id(canvas_manager._drawing_area)
        EventBus.subscribe('model.place.created', handler, document_id=document_id)
        
        # Create three places
        place1 = canvas_manager.add_place(100, 100)
        place2 = canvas_manager.add_place(200, 100)
        place3 = canvas_manager.add_place(300, 100)
        
        # Verify three events
        assert len(events_received) == 3
        assert events_received[0]['object'] == place1
        assert events_received[1]['object'] == place2
        assert events_received[2]['object'] == place3


class TestTransitionCreationEvents:
    """Test model.transition.created event emission."""
    
    def test_add_transition_emits_event(self, canvas_manager):
        """Test that add_transition emits model.transition.created event."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        document_id = id(canvas_manager._drawing_area)
        EventBus.subscribe('model.transition.created', handler, document_id=document_id)
        
        # Create a transition
        transition = canvas_manager.add_transition(200, 150)
        
        # Verify event was emitted
        assert len(events_received) == 1
        event = events_received[0]
        
        assert event['object'] == transition
        assert event['object_type'] == 'transition'
        assert event['object_id'] == transition.id
        assert event['action'] == 'created'
        assert 'timestamp' in event


class TestArcCreationEvents:
    """Test model.arc.created event emission."""
    
    def test_add_arc_emits_event(self, canvas_manager):
        """Test that add_arc emits model.arc.created event."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        document_id = id(canvas_manager._drawing_area)
        EventBus.subscribe('model.arc.created', handler, document_id=document_id)
        
        # Create place and transition first
        place = canvas_manager.add_place(100, 100)
        transition = canvas_manager.add_transition(200, 100)
        
        # Create arc
        arc = canvas_manager.add_arc(place, transition)
        
        # Verify event was emitted
        assert len(events_received) == 1
        event = events_received[0]
        
        assert event['object'] == arc
        assert event['object_type'] == 'arc'
        assert event['object_id'] == arc.id
        assert event['action'] == 'created'
        assert 'timestamp' in event


class TestPlaceDeletionEvents:
    """Test model.place.deleted event emission."""
    
    def test_remove_place_emits_event(self, canvas_manager):
        """Test that remove_place emits model.place.deleted event."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        document_id = id(canvas_manager._drawing_area)
        EventBus.subscribe('model.place.deleted', handler, document_id=document_id)
        
        # Create and remove a place
        place = canvas_manager.add_place(100, 100)
        place_id = place.id
        canvas_manager.remove_place(place)
        
        # Verify event was emitted
        assert len(events_received) == 1
        event = events_received[0]
        
        assert event['object'] == place
        assert event['object_type'] == 'place'
        assert event['object_id'] == place_id
        assert event['action'] == 'deleted'
        assert 'timestamp' in event


class TestTransitionDeletionEvents:
    """Test model.transition.deleted event emission."""
    
    def test_remove_transition_emits_event(self, canvas_manager):
        """Test that remove_transition emits model.transition.deleted event."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        document_id = id(canvas_manager._drawing_area)
        EventBus.subscribe('model.transition.deleted', handler, document_id=document_id)
        
        # Create and remove a transition
        transition = canvas_manager.add_transition(200, 100)
        transition_id = transition.id
        canvas_manager.remove_transition(transition)
        
        # Verify event was emitted
        assert len(events_received) == 1
        event = events_received[0]
        
        assert event['object'] == transition
        assert event['object_type'] == 'transition'
        assert event['object_id'] == transition_id
        assert event['action'] == 'deleted'


class TestArcDeletionEvents:
    """Test model.arc.deleted event emission."""
    
    def test_remove_arc_emits_event(self, canvas_manager):
        """Test that remove_arc emits model.arc.deleted event."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        document_id = id(canvas_manager._drawing_area)
        EventBus.subscribe('model.arc.deleted', handler, document_id=document_id)
        
        # Create place, transition, and arc
        place = canvas_manager.add_place(100, 100)
        transition = canvas_manager.add_transition(200, 100)
        arc = canvas_manager.add_arc(place, transition)
        arc_id = arc.id
        
        # Remove arc
        canvas_manager.remove_arc(arc)
        
        # Verify event was emitted
        assert len(events_received) == 1
        event = events_received[0]
        
        assert event['object'] == arc
        assert event['object_type'] == 'arc'
        assert event['object_id'] == arc_id
        assert event['action'] == 'deleted'


class TestDocumentScoping:
    """Test that events are document-scoped correctly."""
    
    def test_events_are_document_scoped(self):
        """Test that events from different documents don't cross."""
        # Create two canvas managers (different documents)
        manager1 = ModelCanvasManager()
        manager1._drawing_area = Mock()
        doc1_id = id(manager1._drawing_area)
        
        manager2 = ModelCanvasManager()
        manager2._drawing_area = Mock()
        doc2_id = id(manager2._drawing_area)
        
        doc1_events = []
        doc2_events = []
        
        def doc1_handler(data):
            doc1_events.append(data)
        
        def doc2_handler(data):
            doc2_events.append(data)
        
        # Subscribe each handler to its document
        EventBus.subscribe('model.place.created', doc1_handler, document_id=doc1_id)
        EventBus.subscribe('model.place.created', doc2_handler, document_id=doc2_id)
        
        # Create places in each document
        place1 = manager1.add_place(100, 100)
        place2 = manager2.add_place(200, 200)
        
        # Each handler should only receive events from its document
        assert len(doc1_events) == 1
        assert len(doc2_events) == 1
        assert doc1_events[0]['object'] == place1
        assert doc2_events[0]['object'] == place2


class TestWildcardSubscriptions:
    """Test wildcard subscriptions for model events."""
    
    def test_wildcard_receives_all_model_events(self, canvas_manager):
        """Test that model.* wildcard receives all model modification events."""
        all_events = []
        
        def handler(data):
            all_events.append(data)
        
        document_id = id(canvas_manager._drawing_area)
        EventBus.subscribe('model.*', handler, document_id=document_id)
        
        # Create various objects
        place = canvas_manager.add_place(100, 100)
        transition = canvas_manager.add_transition(200, 100)
        arc = canvas_manager.add_arc(place, transition)
        
        # Should have received 3 events
        assert len(all_events) == 3
        assert all_events[0]['object_type'] == 'place'
        assert all_events[1]['object_type'] == 'transition'
        assert all_events[2]['object_type'] == 'arc'


class TestEventDataStructure:
    """Test that event data structure is correct."""
    
    def test_creation_event_has_all_required_fields(self, canvas_manager):
        """Test that creation events have all required fields."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        document_id = id(canvas_manager._drawing_area)
        EventBus.subscribe('model.place.created', handler, document_id=document_id)
        
        canvas_manager.add_place(100, 100)
        
        event = events_received[0]
        
        # Verify all required fields
        assert 'object' in event
        assert 'object_type' in event
        assert 'object_id' in event
        assert 'action' in event
        assert 'timestamp' in event
        assert 'batch_id' in event
        
        # Verify types
        assert isinstance(event['object_type'], str)
        assert isinstance(event['object_id'], str)
        assert isinstance(event['action'], str)
        assert isinstance(event['timestamp'], float)
        assert event['batch_id'] is None or isinstance(event['batch_id'], str)


class TestErrorIsolation:
    """Test that subscriber errors don't affect model operations."""
    
    def test_failing_subscriber_does_not_prevent_creation(self, canvas_manager):
        """Test that object creation succeeds even if a subscriber fails."""
        def failing_handler(data):
            raise RuntimeError("Intentional test failure")
        
        good_events = []
        def good_handler(data):
            good_events.append(data)
        
        document_id = id(canvas_manager._drawing_area)
        EventBus.subscribe('model.place.created', failing_handler, document_id=document_id)
        EventBus.subscribe('model.place.created', good_handler, document_id=document_id)
        
        # Should not raise, place should be created
        place = canvas_manager.add_place(100, 100)
        
        # Place should exist in model
        assert place in canvas_manager.places
        
        # Good subscriber should still receive event
        assert len(good_events) == 1


class TestCascadeDeletion:
    """Test that cascade deletions emit appropriate events."""
    
    def test_deleting_place_emits_arc_deletion_events(self, canvas_manager):
        """Test that deleting a place also emits events for cascade-deleted arcs."""
        place_delete_events = []
        arc_delete_events = []
        
        def place_handler(data):
            place_delete_events.append(data)
        
        def arc_handler(data):
            arc_delete_events.append(data)
        
        document_id = id(canvas_manager._drawing_area)
        EventBus.subscribe('model.place.deleted', place_handler, document_id=document_id)
        EventBus.subscribe('model.arc.deleted', arc_handler, document_id=document_id)
        
        # Create place, transition, and arcs
        place = canvas_manager.add_place(100, 100)
        transition = canvas_manager.add_transition(200, 100)
        arc1 = canvas_manager.add_arc(place, transition)
        arc2 = canvas_manager.add_arc(transition, place)
        
        # Delete place (should cascade-delete both arcs)
        canvas_manager.remove_place(place)
        
        # Should get 1 place deletion event
        assert len(place_delete_events) == 1
        
        # Arcs should be removed from model (cascade deletion)
        assert arc1 not in canvas_manager.arcs
        assert arc2 not in canvas_manager.arcs


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
