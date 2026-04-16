"""Test settings.changed EventBus integration.

This test suite verifies that workspace settings emit proper EventBus events
when modified, and that subscribers receive complete event data.
"""
import pytest
import time
import tempfile
import os
from unittest.mock import Mock

# Import EventBus and WorkspaceSettings
from shypn.events import EventBus
from shypn.workspace_settings import WorkspaceSettings


@pytest.fixture(autouse=True)
def clean_eventbus():
    """Clear EventBus before and after each test."""
    EventBus.clear_all()
    yield
    EventBus.clear_all()


@pytest.fixture
def temp_settings():
    """Create WorkspaceSettings with temporary config file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        settings = WorkspaceSettings()
        # Override config file to use temp directory
        settings.config_file = os.path.join(tmpdir, 'workspace.json')
        yield settings


class TestSettingsEventBusBasics:
    """Test basic settings event emission."""
    
    def test_snap_to_grid_emits_event(self, temp_settings):
        """Test that set_snap_to_grid emits settings.changed event."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        EventBus.subscribe('settings.changed', handler)
        
        # Change snap to grid setting
        temp_settings.set_snap_to_grid(False)
        
        # Verify event was emitted
        assert len(events_received) == 1
        event = events_received[0]
        
        assert event['category'] == 'editor'
        assert event['key'] == 'editor.snap_to_grid'
        assert event['old_value'] == True  # Default is True
        assert event['new_value'] == False
        assert 'timestamp' in event
        assert isinstance(event['timestamp'], float)
    
    def test_grid_spacing_emits_event(self, temp_settings):
        """Test that set_grid_spacing emits settings.changed event."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        EventBus.subscribe('settings.changed', handler)
        
        # Change grid spacing
        temp_settings.set_grid_spacing(20.0)
        
        # Verify event was emitted
        assert len(events_received) == 1
        event = events_received[0]
        
        assert event['category'] == 'editor'
        assert event['key'] == 'editor.grid_spacing'
        assert event['old_value'] == 10.0  # Default is 10.0
        assert event['new_value'] == 20.0
        assert 'timestamp' in event
    
    def test_generic_setting_emits_event(self, temp_settings):
        """Test that set_setting emits settings.changed event."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        EventBus.subscribe('settings.changed', handler)
        
        # Get current value first
        old_biomodels_id = temp_settings.get_setting('sbml_import.last_biomodels_id')
        
        # Set a generic setting
        temp_settings.set_setting('sbml_import.last_biomodels_id', 'BIOMD0000000061')
        
        # Verify event was emitted
        assert len(events_received) == 1
        event = events_received[0]
        
        assert event['category'] == 'sbml_import'
        assert event['key'] == 'sbml_import.last_biomodels_id'
        assert event['old_value'] == old_biomodels_id  # Whatever it was before
        assert event['new_value'] == 'BIOMD0000000061'
        assert 'timestamp' in event
    
    def test_window_geometry_emits_event(self, temp_settings):
        """Test that set_window_geometry emits settings.changed event."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        EventBus.subscribe('settings.changed', handler)
        
        # Set window geometry
        temp_settings.set_window_geometry(1600, 900, x=100, y=50, maximized=False)
        
        # Verify event was emitted
        assert len(events_received) == 1
        event = events_received[0]
        
        assert event['category'] == 'window'
        assert event['key'] == 'window.geometry'
        assert isinstance(event['old_value'], dict)
        assert event['new_value']['width'] == 1600
        assert event['new_value']['height'] == 900
        assert event['new_value']['x'] == 100
        assert event['new_value']['y'] == 50
        assert event['new_value']['maximized'] == False


class TestMultipleSubscribers:
    """Test that multiple subscribers receive settings events."""
    
    def test_multiple_subscribers_receive_same_event(self, temp_settings):
        """Test that all subscribers receive the same settings.changed event."""
        subscriber1_events = []
        subscriber2_events = []
        subscriber3_events = []
        
        def handler1(data):
            subscriber1_events.append(data)
        
        def handler2(data):
            subscriber2_events.append(data)
        
        def handler3(data):
            subscriber3_events.append(data)
        
        EventBus.subscribe('settings.changed', handler1)
        EventBus.subscribe('settings.changed', handler2)
        EventBus.subscribe('settings.changed', handler3)
        
        # Change a setting
        temp_settings.set_snap_to_grid(False)
        
        # Verify all subscribers received the event
        assert len(subscriber1_events) == 1
        assert len(subscriber2_events) == 1
        assert len(subscriber3_events) == 1
        
        # Verify they all received the same data
        assert subscriber1_events[0]['key'] == 'editor.snap_to_grid'
        assert subscriber2_events[0]['key'] == 'editor.snap_to_grid'
        assert subscriber3_events[0]['key'] == 'editor.snap_to_grid'
    
    def test_wildcard_subscription_receives_all_settings(self, temp_settings):
        """Test that wildcard subscriptions receive all settings events."""
        all_events = []
        
        def handler(data):
            # Wildcard handlers receive only data, need to check event type via _event_name
            all_events.append(data)
        
        EventBus.subscribe('settings.*', handler)
        
        # Make multiple setting changes
        temp_settings.set_snap_to_grid(False)
        temp_settings.set_grid_spacing(15.0)
        temp_settings.set_setting('sbml_import.last_biomodels_id', 'BIOMD0000000061')
        
        # Verify wildcard subscriber received all events
        assert len(all_events) == 3
        
        # Verify different keys
        keys = [e['key'] for e in all_events]
        assert 'editor.snap_to_grid' in keys
        assert 'editor.grid_spacing' in keys
        assert 'sbml_import.last_biomodels_id' in keys


class TestEventDataStructure:
    """Test that event data structure is correct and complete."""
    
    def test_event_data_has_required_fields(self, temp_settings):
        """Test that event data contains all required fields."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        EventBus.subscribe('settings.changed', handler)
        
        temp_settings.set_snap_to_grid(False)
        
        event = events_received[0]
        
        # Verify all required fields are present
        assert 'category' in event
        assert 'key' in event
        assert 'old_value' in event
        assert 'new_value' in event
        assert 'timestamp' in event
        
        # Verify field types
        assert isinstance(event['category'], str)
        assert isinstance(event['key'], str)
        assert isinstance(event['timestamp'], float)
    
    def test_timestamp_is_recent(self, temp_settings):
        """Test that timestamp is current time."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        EventBus.subscribe('settings.changed', handler)
        
        before = time.time()
        temp_settings.set_snap_to_grid(False)
        after = time.time()
        
        event = events_received[0]
        
        # Timestamp should be between before and after
        assert before <= event['timestamp'] <= after


class TestSettingsSequence:
    """Test multiple settings changes in sequence."""
    
    def test_multiple_changes_emit_multiple_events(self, temp_settings):
        """Test that multiple setting changes emit separate events."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        EventBus.subscribe('settings.changed', handler)
        
        # Make multiple changes
        temp_settings.set_snap_to_grid(False)
        temp_settings.set_grid_spacing(20.0)
        temp_settings.set_snap_to_grid(True)  # Change back
        
        # Verify 3 separate events
        assert len(events_received) == 3
        
        assert events_received[0]['key'] == 'editor.snap_to_grid'
        assert events_received[0]['new_value'] == False
        
        assert events_received[1]['key'] == 'editor.grid_spacing'
        assert events_received[1]['new_value'] == 20.0
        
        assert events_received[2]['key'] == 'editor.snap_to_grid'
        assert events_received[2]['old_value'] == False
        assert events_received[2]['new_value'] == True
    
    def test_old_value_reflects_previous_state(self, temp_settings):
        """Test that old_value correctly reflects the previous state."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        EventBus.subscribe('settings.changed', handler)
        
        # First change
        temp_settings.set_snap_to_grid(False)
        assert events_received[0]['old_value'] == True
        assert events_received[0]['new_value'] == False
        
        # Second change (should track the False from first change)
        temp_settings.set_snap_to_grid(True)
        assert events_received[1]['old_value'] == False
        assert events_received[1]['new_value'] == True


class TestErrorIsolation:
    """Test that subscriber errors don't affect other subscribers."""
    
    def test_failing_subscriber_does_not_block_others(self, temp_settings):
        """Test that one failing subscriber doesn't prevent others from receiving events."""
        good_subscriber_events = []
        
        def failing_handler(data):
            raise RuntimeError("Intentional test failure")
        
        def good_handler(data):
            good_subscriber_events.append(data)
        
        EventBus.subscribe('settings.changed', failing_handler)
        EventBus.subscribe('settings.changed', good_handler)
        
        # Change setting (failing subscriber should not prevent good_handler)
        temp_settings.set_snap_to_grid(False)
        
        # Good subscriber should still receive event
        assert len(good_subscriber_events) == 1
        assert good_subscriber_events[0]['key'] == 'editor.snap_to_grid'


class TestCategoryFiltering:
    """Test filtering settings events by category."""
    
    def test_can_identify_editor_settings(self, temp_settings):
        """Test that editor settings can be identified by category."""
        events_received = []
        
        def handler(data):
            if data['category'] == 'editor':
                events_received.append(data)
        
        EventBus.subscribe('settings.changed', handler)
        
        # Change both editor and non-editor settings
        temp_settings.set_snap_to_grid(False)
        temp_settings.set_setting('sbml_import.last_biomodels_id', 'BIOMD0000000061')
        temp_settings.set_grid_spacing(20.0)
        
        # Only editor settings should be captured
        assert len(events_received) == 2
        assert all(e['category'] == 'editor' for e in events_received)
    
    def test_different_categories_have_different_keys(self, temp_settings):
        """Test that different categories use appropriate key prefixes."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        EventBus.subscribe('settings.changed', handler)
        
        # Change settings from different categories
        temp_settings.set_snap_to_grid(False)  # editor
        temp_settings.set_setting('sbml_import.last_biomodels_id', 'BIOMD0000000061')  # sbml_import
        temp_settings.set_window_geometry(1600, 900)  # window
        
        # Verify categories
        assert events_received[0]['category'] == 'editor'
        assert events_received[0]['key'].startswith('editor.')
        
        assert events_received[1]['category'] == 'sbml_import'
        assert events_received[1]['key'].startswith('sbml_import.')
        
        assert events_received[2]['category'] == 'window'
        assert events_received[2]['key'].startswith('window.')


class TestUnsubscribe:
    """Test that unsubscribe works correctly for settings events."""
    
    def test_unsubscribed_handler_does_not_receive_events(self, temp_settings):
        """Test that unsubscribed handlers stop receiving events."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        # Subscribe
        EventBus.subscribe('settings.changed', handler)
        
        # Change setting - should receive
        temp_settings.set_snap_to_grid(False)
        assert len(events_received) == 1
        
        # Unsubscribe
        EventBus.unsubscribe('settings.changed', handler)
        
        # Change setting - should NOT receive
        temp_settings.set_grid_spacing(20.0)
        assert len(events_received) == 1  # Still 1, not 2


class TestPersistence:
    """Test that settings are properly persisted after events."""
    
    def test_settings_saved_to_file_after_change(self, temp_settings):
        """Test that settings are written to file after change."""
        events_received = []
        
        def handler(data):
            events_received.append(data)
        
        EventBus.subscribe('settings.changed', handler)
        
        # Change setting
        temp_settings.set_snap_to_grid(False)
        
        # Verify event was emitted
        assert len(events_received) == 1
        
        # Verify setting was persisted (reload from file)
        temp_settings.load()
        assert temp_settings.get_snap_to_grid() == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
