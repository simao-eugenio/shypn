"""Test file operation EventBus integration.

This test suite verifies that file save/load/close/import operations emit proper
EventBus events with complete data.
"""
import pytest
import tempfile
import os
from unittest.mock import Mock
from pathlib import Path

# Import EventBus and DocumentModel
from shypn.events import EventBus
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place


@pytest.fixture(autouse=True)
def clean_eventbus():
    """Clear EventBus before and after each test."""
    EventBus.clear_all()
    yield
    EventBus.clear_all()


@pytest.fixture
def temp_directory():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestFileSaveEvents:
    """Test file.saved event emission."""
    
    def test_save_to_file_emits_event(self, temp_directory):
        """Test that save_to_file emits file.saved event."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        EventBus.subscribe('file.saved', handler)
        
        # Create a document and save it
        doc = DocumentModel()
        filepath = os.path.join(temp_directory, 'test_model.shy')
        doc.save_to_file(filepath)
        
        # Verify event was emitted
        assert len(events_received) == 1
        event = events_received[0]
        
        assert event['filepath'] == filepath
        assert event['document'] == doc
        assert event['was_autosave'] == False
        assert 'timestamp' in event
        assert isinstance(event['timestamp'], float)
    
    def test_save_event_includes_document_reference(self, temp_directory):
        """Test that save event includes reference to the actual document."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        EventBus.subscribe('file.saved', handler)
        
        # Create document with some content
        doc = DocumentModel()
        place = Place(100, 100, 'P1', 'P1')
        doc.add_place(place)
        
        filepath = os.path.join(temp_directory, 'test_with_objects.shy')
        doc.save_to_file(filepath)
        
        event = events_received[0]
        
        # Verify document reference
        assert event['document'] is doc
        assert len(event['document'].places) == 1
        assert event['document'].places[0] == place
    
    def test_multiple_saves_emit_multiple_events(self, temp_directory):
        """Test that multiple saves emit separate events."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        EventBus.subscribe('file.saved', handler)
        
        doc = DocumentModel()
        filepath1 = os.path.join(temp_directory, 'file1.shy')
        filepath2 = os.path.join(temp_directory, 'file2.shy')
        
        doc.save_to_file(filepath1)
        doc.save_to_file(filepath2)
        
        assert len(events_received) == 2
        assert events_received[0]['filepath'] == filepath1
        assert events_received[1]['filepath'] == filepath2


class TestFileLoadEvents:
    """Test file.opened event emission."""
    
    def test_load_from_file_emits_event(self, temp_directory):
        """Test that load_from_file emits file.opened event."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        # Create and save a document first
        doc = DocumentModel()
        place = Place(100, 100, 'P1', 'P1')
        doc.add_place(place)
        filepath = os.path.join(temp_directory, 'test_load.shy')
        doc.save_to_file(filepath)
        
        # Clear events from save
        events_received.clear()
        
        # Subscribe to file.opened
        EventBus.subscribe('file.opened', handler)
        
        # Load the document
        loaded_doc = DocumentModel.load_from_file(filepath)
        
        # Verify event was emitted
        assert len(events_received) == 1
        event = events_received[0]
        
        assert event['filepath'] == filepath
        assert event['document'] == loaded_doc
        assert 'timestamp' in event
        assert isinstance(event['timestamp'], float)
    
    def test_load_event_includes_loaded_document(self, temp_directory):
        """Test that load event includes the newly loaded document."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        # Create document with content
        original_doc = DocumentModel()
        place = Place(150, 200, 'P1', 'P1')
        place.label = "Test Place"
        original_doc.add_place(place)
        
        filepath = os.path.join(temp_directory, 'test_content.shy')
        original_doc.save_to_file(filepath)
        
        EventBus.subscribe('file.opened', handler)
        
        # Load the document
        loaded_doc = DocumentModel.load_from_file(filepath)
        
        event = events_received[0]
        
        # Verify loaded document has content
        assert event['document'] is loaded_doc
        assert len(loaded_doc.places) == 1
        assert loaded_doc.places[0].label == "Test Place"
    
    def test_load_multiple_files_emits_multiple_events(self, temp_directory):
        """Test that loading multiple files emits separate events."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        # Create and save two documents
        doc1 = DocumentModel()
        doc2 = DocumentModel()
        filepath1 = os.path.join(temp_directory, 'doc1.shy')
        filepath2 = os.path.join(temp_directory, 'doc2.shy')
        
        doc1.save_to_file(filepath1)
        doc2.save_to_file(filepath2)
        
        EventBus.subscribe('file.opened', handler)
        
        # Load both
        DocumentModel.load_from_file(filepath1)
        DocumentModel.load_from_file(filepath2)
        
        assert len(events_received) == 2
        assert events_received[0]['filepath'] == filepath1
        assert events_received[1]['filepath'] == filepath2


class TestEventDataStructure:
    """Test that event data structures are complete."""
    
    def test_save_event_has_all_required_fields(self, temp_directory):
        """Test that file.saved event has all required fields."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        EventBus.subscribe('file.saved', handler)
        
        doc = DocumentModel()
        filepath = os.path.join(temp_directory, 'test.shy')
        doc.save_to_file(filepath)
        
        event = events_received[0]
        
        # Verify all required fields
        assert 'filepath' in event
        assert 'document' in event
        assert 'timestamp' in event
        assert 'was_autosave' in event
        
        # Verify types
        assert isinstance(event['filepath'], str)
        assert isinstance(event['document'], DocumentModel)
        assert isinstance(event['timestamp'], float)
        assert isinstance(event['was_autosave'], bool)
    
    def test_load_event_has_all_required_fields(self, temp_directory):
        """Test that file.opened event has all required fields."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        doc = DocumentModel()
        filepath = os.path.join(temp_directory, 'test.shy')
        doc.save_to_file(filepath)
        
        EventBus.subscribe('file.opened', handler)
        DocumentModel.load_from_file(filepath)
        
        event = events_received[0]
        
        # Verify all required fields
        assert 'filepath' in event
        assert 'document' in event
        assert 'timestamp' in event
        
        # Verify types
        assert isinstance(event['filepath'], str)
        assert isinstance(event['document'], DocumentModel)
        assert isinstance(event['timestamp'], float)


class TestMultipleSubscribers:
    """Test that multiple subscribers receive file events."""
    
    def test_multiple_subscribers_receive_save_event(self, temp_directory):
        """Test that all subscribers receive file.saved events."""
        subscriber1_events = []
        subscriber2_events = []
        
        def handler1(data):
            subscriber1_events.append(data)
        
        def handler2(data):
            subscriber2_events.append(data)
        
        EventBus.subscribe('file.saved', handler1)
        EventBus.subscribe('file.saved', handler2)
        
        doc = DocumentModel()
        filepath = os.path.join(temp_directory, 'test.shy')
        doc.save_to_file(filepath)
        
        assert len(subscriber1_events) == 1
        assert len(subscriber2_events) == 1
        assert subscriber1_events[0]['filepath'] == filepath
        assert subscriber2_events[0]['filepath'] == filepath
    
    def test_wildcard_subscription_receives_all_file_events(self, temp_directory):
        """Test that wildcard subscriptions receive both save and load events."""
        all_events = []
        
        def handler(data):
            all_events.append(data)
        
        EventBus.subscribe('file.*', handler)
        
        doc = DocumentModel()
        filepath = os.path.join(temp_directory, 'test.shy')
        
        # Save
        doc.save_to_file(filepath)
        
        # Load
        DocumentModel.load_from_file(filepath)
        
        # Should have received both events
        assert len(all_events) == 2


class TestErrorIsolation:
    """Test that subscriber errors don't affect file operations."""
    
    def test_failing_subscriber_does_not_prevent_save(self, temp_directory):
        """Test that file saves even if a subscriber fails."""
        def failing_handler(data):
            raise RuntimeError("Intentional test failure")
        
        good_events = []
        def good_handler(data):
            good_events.append(data)
        
        EventBus.subscribe('file.saved', failing_handler)
        EventBus.subscribe('file.saved', good_handler)
        
        doc = DocumentModel()
        filepath = os.path.join(temp_directory, 'test.shy')
        
        # Should not raise, file should be saved
        doc.save_to_file(filepath)
        
        # File should exist
        assert os.path.exists(filepath)
        
        # Good subscriber should still receive event
        assert len(good_events) == 1
    
    def test_failing_subscriber_does_not_prevent_load(self, temp_directory):
        """Test that file loads even if a subscriber fails."""
        def failing_handler(data):
            raise RuntimeError("Intentional test failure")
        
        good_events = []
        def good_handler(data):
            good_events.append(data)
        
        # Create file
        doc = DocumentModel()
        filepath = os.path.join(temp_directory, 'test.shy')
        doc.save_to_file(filepath)
        
        EventBus.subscribe('file.opened', failing_handler)
        EventBus.subscribe('file.opened', good_handler)
        
        # Should not raise, file should be loaded
        loaded = DocumentModel.load_from_file(filepath)
        
        assert loaded is not None
        assert len(good_events) == 1


class TestSaveLoadSequence:
    """Test save-load sequences emit correct events."""
    
    def test_save_then_load_emits_both_events(self, temp_directory):
        """Test that saving then loading emits both event types."""
        all_events = {}
        
        def save_handler(data):
            all_events['saved'] = data
        
        def load_handler(data):
            all_events['loaded'] = data
        
        EventBus.subscribe('file.saved', save_handler)
        EventBus.subscribe('file.opened', load_handler)
        
        doc = DocumentModel()
        place = Place(100, 100, 'P1', 'P1')
        doc.add_place(place)
        filepath = os.path.join(temp_directory, 'test.shy')
        
        # Save
        doc.save_to_file(filepath)
        
        # Load
        loaded = DocumentModel.load_from_file(filepath)
        
        # Both events should have been emitted
        assert 'saved' in all_events
        assert 'loaded' in all_events
        assert all_events['saved']['filepath'] == filepath
        assert all_events['loaded']['filepath'] == filepath
    
    def test_timestamps_are_ordered(self, temp_directory):
        """Test that save timestamp comes before load timestamp."""
        all_events = {}
        
        def save_handler(data):
            all_events['saved'] = data
        
        def load_handler(data):
            all_events['loaded'] = data
        
        EventBus.subscribe('file.saved', save_handler)
        EventBus.subscribe('file.opened', load_handler)
        
        doc = DocumentModel()
        filepath = os.path.join(temp_directory, 'test.shy')
        
        doc.save_to_file(filepath)
        DocumentModel.load_from_file(filepath)
        
        # Save timestamp should be before or equal to load timestamp
        assert all_events['saved']['timestamp'] <= all_events['loaded']['timestamp']


class TestUnsubscribe:
    """Test that unsubscribe works for file events."""
    
    def test_unsubscribed_handler_does_not_receive_save_events(self, temp_directory):
        """Test that unsubscribed handlers stop receiving save events."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        EventBus.subscribe('file.saved', handler)
        
        doc = DocumentModel()
        filepath1 = os.path.join(temp_directory, 'file1.shy')
        filepath2 = os.path.join(temp_directory, 'file2.shy')
        
        # Save once - should receive
        doc.save_to_file(filepath1)
        assert len(events_received) == 1
        
        # Unsubscribe
        EventBus.unsubscribe('file.saved', handler)
        
        # Save again - should NOT receive
        doc.save_to_file(filepath2)
        assert len(events_received) == 1  # Still 1, not 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
