"""
Unit tests for debounced UI controls.

Tests the debounced SpinButton and Entry widgets to ensure proper
callback debouncing behavior.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gtk, GLib

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.ui.controls.base import (
    DebounceStrategy,
    TimeoutDebounceStrategy,
    DebouncedWidget
)
from shypn.ui.controls.debounced_spin_button import (
    DebouncedSpinButton,
    create_debounced_spin_button
)
from shypn.ui.controls.debounced_entry import (
    DebouncedEntry,
    DebouncedSearchEntry,
    create_debounced_entry
)


class MockDebounceStrategy(DebounceStrategy):
    """Mock debounce strategy for testing without real timers."""
    
    def __init__(self):
        self.scheduled_callback = None
        self.delay_ms = None
        self.cancelled = False
        self.flushed = False
    
    def schedule(self, callback, delay_ms):
        self.scheduled_callback = callback
        self.delay_ms = delay_ms
        self.cancelled = False
        self.flushed = False
    
    def cancel(self):
        self.scheduled_callback = None
        self.cancelled = True
    
    def flush(self):
        if self.scheduled_callback:
            callback = self.scheduled_callback
            self.scheduled_callback = None
            self.flushed = True
            callback()
    
    def execute_scheduled(self):
        """Helper to manually trigger scheduled callback."""
        if self.scheduled_callback:
            callback = self.scheduled_callback
            self.scheduled_callback = None
            callback()


class TestDebounceStrategy:
    """Test DebounceStrategy base class and implementations."""
    
    def test_mock_strategy_schedule(self):
        """Test mock strategy schedules callbacks."""
        strategy = MockDebounceStrategy()
        callback = Mock()
        
        strategy.schedule(callback, 100)
        
        assert strategy.scheduled_callback is not None
        assert strategy.delay_ms == 100
        assert not strategy.cancelled
    
    def test_mock_strategy_cancel(self):
        """Test mock strategy cancels callbacks."""
        strategy = MockDebounceStrategy()
        callback = Mock()
        
        strategy.schedule(callback, 100)
        strategy.cancel()
        
        assert strategy.scheduled_callback is None
        assert strategy.cancelled
    
    def test_mock_strategy_flush(self):
        """Test mock strategy flushes callbacks."""
        strategy = MockDebounceStrategy()
        callback = Mock()
        
        strategy.schedule(callback, 100)
        strategy.flush()
        
        callback.assert_called_once()
        assert strategy.flushed
        assert strategy.scheduled_callback is None
    
    def test_mock_strategy_reschedule_cancels_previous(self):
        """Test rescheduling cancels previous callback."""
        strategy = MockDebounceStrategy()
        callback1 = Mock()
        callback2 = Mock()
        
        strategy.schedule(callback1, 100)
        strategy.schedule(callback2, 200)
        strategy.execute_scheduled()
        
        callback1.assert_not_called()
        callback2.assert_called_once()


class TestDebouncedWidget:
    """Test DebouncedWidget mixin."""
    
    def test_initialization(self):
        """Test widget initializes with default strategy."""
        widget = DebouncedWidget(delay_ms=250)
        
        assert widget.get_debounce_delay() == 250
        assert widget._debounce_strategy is not None
        assert widget._debounced_callback is None
    
    def test_custom_strategy(self):
        """Test widget accepts custom strategy."""
        strategy = MockDebounceStrategy()
        widget = DebouncedWidget(delay_ms=100, strategy=strategy)
        
        assert widget._debounce_strategy is strategy
    
    def test_set_debounced_callback(self):
        """Test setting debounced callback."""
        widget = DebouncedWidget(delay_ms=250)
        callback = Mock()
        
        widget.set_debounced_callback(callback)
        
        assert widget._debounced_callback is callback
    
    def test_set_debounced_callback_with_delay(self):
        """Test setting callback with custom delay."""
        widget = DebouncedWidget(delay_ms=250)
        callback = Mock()
        
        widget.set_debounced_callback(callback, delay_ms=500)
        
        assert widget._debounced_callback is callback
        assert widget.get_debounce_delay() == 500
    
    def test_schedule_debounced_callback(self):
        """Test scheduling executes callback through strategy."""
        strategy = MockDebounceStrategy()
        widget = DebouncedWidget(delay_ms=100, strategy=strategy)
        callback = Mock()
        widget.set_debounced_callback(callback)
        
        widget._schedule_debounced_callback()
        
        assert strategy.scheduled_callback is not None
        
        # Execute scheduled callback
        strategy.execute_scheduled()
        callback.assert_called_once()
    
    def test_schedule_without_callback_does_nothing(self):
        """Test scheduling without callback does nothing."""
        strategy = MockDebounceStrategy()
        widget = DebouncedWidget(delay_ms=100, strategy=strategy)
        
        widget._schedule_debounced_callback()
        
        assert strategy.scheduled_callback is None
    
    def test_flush_executes_immediately(self):
        """Test flush executes callback immediately."""
        strategy = MockDebounceStrategy()
        widget = DebouncedWidget(delay_ms=100, strategy=strategy)
        callback = Mock()
        widget.set_debounced_callback(callback)
        
        widget._schedule_debounced_callback()
        widget.flush_debounced_callback()
        
        callback.assert_called_once()
        assert strategy.flushed
    
    def test_cancel_prevents_execution(self):
        """Test cancel prevents callback execution."""
        strategy = MockDebounceStrategy()
        widget = DebouncedWidget(delay_ms=100, strategy=strategy)
        callback = Mock()
        widget.set_debounced_callback(callback)
        
        widget._schedule_debounced_callback()
        widget.cancel_debounced_callback()
        
        assert strategy.cancelled
        strategy.execute_scheduled()  # Try to execute
        callback.assert_not_called()
    
    def test_set_debounce_delay(self):
        """Test changing debounce delay."""
        widget = DebouncedWidget(delay_ms=100)
        
        widget.set_debounce_delay(500)
        
        assert widget.get_debounce_delay() == 500


class TestDebouncedSpinButton:
    """Test DebouncedSpinButton widget."""
    
    def test_initialization(self):
        """Test spin button initializes correctly."""
        adj = Gtk.Adjustment(value=5.0, lower=0.0, upper=10.0, step_increment=1.0)
        spin = DebouncedSpinButton(adjustment=adj, delay_ms=200)
        
        assert spin.get_value() == 5.0
        assert spin.get_debounce_delay() == 200
    
    def test_value_change_schedules_callback(self):
        """Test value change schedules debounced callback."""
        strategy = MockDebounceStrategy()
        adj = Gtk.Adjustment(value=5.0, lower=0.0, upper=10.0, step_increment=1.0)
        spin = DebouncedSpinButton(adjustment=adj, delay_ms=100, strategy=strategy)
        callback = Mock()
        spin.set_debounced_callback(callback)
        
        # Change value
        spin.set_value(7.0)
        
        assert strategy.scheduled_callback is not None
        
        # Execute scheduled callback
        strategy.execute_scheduled()
        callback.assert_called_once_with(spin)
    
    def test_multiple_changes_debounced(self):
        """Test multiple rapid changes result in single callback."""
        strategy = MockDebounceStrategy()
        adj = Gtk.Adjustment(value=0.0, lower=0.0, upper=100.0, step_increment=1.0)
        spin = DebouncedSpinButton(adjustment=adj, delay_ms=100, strategy=strategy)
        callback = Mock()
        spin.set_debounced_callback(callback)
        
        # Simulate rapid value changes
        for i in range(1, 51):
            spin.set_value(float(i))
        
        # Only last callback should be scheduled
        strategy.execute_scheduled()
        
        callback.assert_called_once()
        assert spin.get_value() == 50.0
    
    def test_set_value_debounced_without_trigger(self):
        """Test setting value programmatically without trigger."""
        strategy = MockDebounceStrategy()
        adj = Gtk.Adjustment(value=5.0, lower=0.0, upper=10.0, step_increment=1.0)
        spin = DebouncedSpinButton(adjustment=adj, delay_ms=100, strategy=strategy)
        callback = Mock()
        spin.set_debounced_callback(callback)
        
        spin.set_value_debounced(8.0, trigger_callback=False)
        
        assert spin.get_value() == 8.0
        assert strategy.scheduled_callback is None
        callback.assert_not_called()
    
    def test_set_value_debounced_with_trigger(self):
        """Test setting value programmatically with trigger."""
        strategy = MockDebounceStrategy()
        adj = Gtk.Adjustment(value=5.0, lower=0.0, upper=10.0, step_increment=1.0)
        spin = DebouncedSpinButton(adjustment=adj, delay_ms=100, strategy=strategy)
        callback = Mock()
        spin.set_debounced_callback(callback)
        
        spin.set_value_debounced(8.0, trigger_callback=True)
        
        assert spin.get_value() == 8.0
        assert strategy.scheduled_callback is not None
    
    def test_get_value_float(self):
        """Test convenience method for getting value."""
        adj = Gtk.Adjustment(value=3.14, lower=0.0, upper=10.0, step_increment=0.01)
        spin = DebouncedSpinButton(adjustment=adj, digits=2)
        
        assert spin.get_value_float() == pytest.approx(3.14)
    
    def test_factory_function(self):
        """Test factory function creates configured widget."""
        callback = Mock()
        spin = create_debounced_spin_button(
            value=5.0,
            lower=0.0,
            upper=10.0,
            step=0.5,
            digits=1,
            delay_ms=300,
            callback=callback
        )
        
        assert spin.get_value() == 5.0
        assert spin.get_debounce_delay() == 300
        assert spin._debounced_callback is callback


class TestDebouncedEntry:
    """Test DebouncedEntry widget."""
    
    def test_initialization(self):
        """Test entry initializes correctly."""
        entry = DebouncedEntry(delay_ms=300)
        
        assert entry.get_text() == ""
        assert entry.get_debounce_delay() == 300
    
    def test_text_change_schedules_callback(self):
        """Test text change schedules debounced callback."""
        strategy = MockDebounceStrategy()
        entry = DebouncedEntry(delay_ms=100, strategy=strategy)
        callback = Mock()
        entry.set_debounced_callback(callback)
        
        # Change text
        entry.set_text("hello")
        
        assert strategy.scheduled_callback is not None
        
        # Execute scheduled callback
        strategy.execute_scheduled()
        callback.assert_called_once_with(entry)
    
    def test_multiple_changes_debounced(self):
        """Test multiple rapid changes result in single callback."""
        strategy = MockDebounceStrategy()
        entry = DebouncedEntry(delay_ms=100, strategy=strategy)
        callback = Mock()
        entry.set_debounced_callback(callback)
        
        # Simulate rapid typing
        for char in "hello world":
            entry.set_text(entry.get_text() + char)
        
        # Only last callback should be scheduled
        strategy.execute_scheduled()
        
        callback.assert_called_once()
        assert entry.get_text() == "hello world"
    
    def test_set_text_debounced_without_trigger(self):
        """Test setting text programmatically without trigger."""
        strategy = MockDebounceStrategy()
        entry = DebouncedEntry(delay_ms=100, strategy=strategy)
        callback = Mock()
        entry.set_debounced_callback(callback)
        
        entry.set_text_debounced("test", trigger_callback=False)
        
        assert entry.get_text() == "test"
        assert strategy.scheduled_callback is None
        callback.assert_not_called()
    
    def test_set_text_debounced_with_trigger(self):
        """Test setting text programmatically with trigger."""
        strategy = MockDebounceStrategy()
        entry = DebouncedEntry(delay_ms=100, strategy=strategy)
        callback = Mock()
        entry.set_debounced_callback(callback)
        
        entry.set_text_debounced("test", trigger_callback=True)
        
        assert entry.get_text() == "test"
        assert strategy.scheduled_callback is not None
    
    def test_get_text_stripped(self):
        """Test getting stripped text."""
        entry = DebouncedEntry()
        entry.set_text("  hello world  ")
        
        assert entry.get_text_stripped() == "hello world"
    
    def test_is_empty(self):
        """Test empty check."""
        entry = DebouncedEntry()
        
        assert entry.is_empty()
        
        entry.set_text("   ")
        assert entry.is_empty()
        
        entry.set_text("text")
        assert not entry.is_empty()
    
    def test_factory_function(self):
        """Test factory function creates configured widget."""
        callback = Mock()
        entry = create_debounced_entry(
            text="initial",
            placeholder="Enter text",
            delay_ms=250,
            callback=callback
        )
        
        assert entry.get_text() == "initial"
        assert entry.get_placeholder_text() == "Enter text"
        assert entry.get_debounce_delay() == 250
        assert entry._debounced_callback is callback


class TestDebouncedSearchEntry:
    """Test DebouncedSearchEntry widget."""
    
    def test_initialization(self):
        """Test search entry initializes correctly."""
        search = DebouncedSearchEntry(delay_ms=200)
        
        assert search.get_text() == ""
        assert search.get_debounce_delay() == 200
    
    def test_search_change_schedules_callback(self):
        """Test search change schedules debounced callback."""
        strategy = MockDebounceStrategy()
        search = DebouncedSearchEntry(delay_ms=100, strategy=strategy)
        callback = Mock()
        search.set_debounced_callback(callback)
        
        # Emit search-changed signal manually (set_text doesn't trigger it automatically)
        search.emit('search-changed')
        
        assert strategy.scheduled_callback is not None


class TestIntegrationScenarios:
    """Integration tests for realistic usage scenarios."""
    
    def test_spin_button_parameter_update_workflow(self):
        """Test typical workflow: spin button -> debounce -> buffer update."""
        strategy = MockDebounceStrategy()
        adj = Gtk.Adjustment(value=1.0, lower=0.1, upper=10.0, step_increment=0.1)
        spin = DebouncedSpinButton(adjustment=adj, delay_ms=250, strategy=strategy)
        
        # Mock buffered settings
        buffered_settings = Mock()
        
        def on_value_changed(widget):
            buffered_settings.set_parameter('time_scale', widget.get_value())
        
        spin.set_debounced_callback(on_value_changed)
        
        # Simulate slider drag (10 rapid changes)
        for i in range(1, 11):
            spin.set_value(float(i))
        
        # Before debounce expires, no buffer update
        buffered_settings.set_parameter.assert_not_called()
        
        # After debounce expires
        strategy.execute_scheduled()
        buffered_settings.set_parameter.assert_called_once_with('time_scale', 10.0)
    
    def test_entry_validation_workflow(self):
        """Test typical workflow: entry -> debounce -> validation -> buffer."""
        strategy = MockDebounceStrategy()
        entry = DebouncedEntry(delay_ms=300, strategy=strategy)
        
        # Mock buffered settings
        buffered_settings = Mock()
        validation_errors = []
        
        def on_text_changed(widget):
            text = widget.get_text_stripped()
            try:
                value = float(text)
                if value > 0:
                    buffered_settings.set_parameter('rate', value)
                    validation_errors.clear()
                else:
                    validation_errors.append("Value must be positive")
            except ValueError:
                validation_errors.append("Invalid number")
        
        entry.set_debounced_callback(on_text_changed)
        
        # Simulate typing "3.14"
        for char in "3.14":
            entry.set_text(entry.get_text() + char)
        
        # Before debounce expires, no validation
        assert len(validation_errors) == 0
        buffered_settings.set_parameter.assert_not_called()
        
        # After debounce expires
        strategy.execute_scheduled()
        buffered_settings.set_parameter.assert_called_once_with('rate', 3.14)
        assert len(validation_errors) == 0
    
    def test_flush_before_dialog_close(self):
        """Test flushing pending changes before closing dialog."""
        strategy = MockDebounceStrategy()
        adj = Gtk.Adjustment(value=1.0, lower=0.0, upper=10.0, step_increment=1.0)
        spin = DebouncedSpinButton(adjustment=adj, delay_ms=250, strategy=strategy)
        
        buffered_settings = Mock()
        spin.set_debounced_callback(
            lambda w: buffered_settings.set_parameter('value', w.get_value())
        )
        
        # User changes value
        spin.set_value(5.0)
        
        # User clicks OK button (before debounce expires)
        spin.flush_debounced_callback()
        
        # Value should be applied immediately
        buffered_settings.set_parameter.assert_called_once_with('value', 5.0)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
