"""
Base classes for debounced UI controls.

This module defines the abstract interfaces and strategies for implementing
debounced user input controls. Debouncing delays the execution of callbacks
until after a period of inactivity, preventing rapid-fire events during
continuous user interactions.

Architecture:
    - DebounceStrategy: Abstract strategy for debouncing implementations
    - DebouncedWidget: Mixin providing debouncing to GTK widgets
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional, Any
import gi

gi.require_version('GLib', '2.0')
from gi.repository import GLib


class DebounceStrategy(ABC):
    """
    Abstract strategy for debouncing user input.
    
    Debouncing delays callback execution until after a quiet period,
    preventing callbacks from firing too frequently during continuous
    input (e.g., slider dragging, rapid typing).
    
    Implementations can use timers, frame scheduling, or other mechanisms
    to achieve debouncing behavior.
    """
    
    @abstractmethod
    def schedule(self, callback: Callable[[], None], delay_ms: int) -> None:
        """
        Schedule a callback to execute after a delay.
        
        If called multiple times before the delay expires, previous
        scheduled callbacks should be cancelled and replaced with
        the new one.
        
        Args:
            callback: Function to call after the delay
            delay_ms: Delay in milliseconds
        """
        pass
    
    @abstractmethod
    def cancel(self) -> None:
        """
        Cancel any pending callback execution.
        
        This should be called when the widget is destroyed or when
        debouncing is no longer needed.
        """
        pass
    
    @abstractmethod
    def flush(self) -> None:
        """
        Immediately execute any pending callback and cancel the timer.
        
        This is useful when you need to force immediate execution,
        such as when committing buffered changes.
        """
        pass


class TimeoutDebounceStrategy(DebounceStrategy):
    """
    Debounce strategy using GLib timeout sources.
    
    This is the standard debouncing implementation for GTK applications.
    Uses GLib.timeout_add to schedule callbacks on the main event loop.
    
    Each call to schedule() cancels the previous timeout and starts a new one,
    ensuring only the last callback is executed after the quiet period.
    """
    
    def __init__(self):
        """Initialize with no pending timeout."""
        self._timeout_id: Optional[int] = None
        self._pending_callback: Optional[Callable[[], None]] = None
    
    def schedule(self, callback: Callable[[], None], delay_ms: int) -> None:
        """
        Schedule callback using GLib.timeout_add.
        
        Args:
            callback: Function to execute after delay
            delay_ms: Delay in milliseconds (typically 100-500ms)
        """
        # Cancel previous timeout
        self.cancel()
        
        # Store callback for flush()
        self._pending_callback = callback
        
        # Schedule new timeout
        def timeout_handler() -> bool:
            self._timeout_id = None
            self._pending_callback = None
            callback()
            return False  # Don't repeat
        
        self._timeout_id = GLib.timeout_add(delay_ms, timeout_handler)
    
    def cancel(self) -> None:
        """Cancel pending timeout if one exists."""
        if self._timeout_id is not None:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None
            self._pending_callback = None
    
    def flush(self) -> None:
        """Execute pending callback immediately and cancel timeout."""
        if self._pending_callback is not None:
            callback = self._pending_callback
            self.cancel()
            callback()


class DebouncedWidget:
    """
    Mixin class providing debouncing capabilities to GTK widgets.
    
    This mixin can be combined with any GTK widget to add debounced
    callback support. Instead of connecting directly to widget signals,
    users register debounced callbacks that only fire after a period of
    inactivity.
    
    Usage:
        class MyDebouncedWidget(Gtk.SpinButton, DebouncedWidget):
            def __init__(self):
                Gtk.SpinButton.__init__(self)
                DebouncedWidget.__init__(self, delay_ms=250)
                self.connect('value-changed', self._on_raw_value_changed)
            
            def _on_raw_value_changed(self, widget):
                self._schedule_debounced_callback()
    
    Attributes:
        _debounce_strategy: Strategy implementation for debouncing
        _debounce_delay_ms: Delay before callback execution
        _debounced_callback: User callback to execute
    """
    
    def __init__(
        self,
        delay_ms: int = 250,
        strategy: Optional[DebounceStrategy] = None
    ):
        """
        Initialize debouncing for this widget.
        
        Args:
            delay_ms: Debounce delay in milliseconds (default 250ms)
            strategy: Debounce strategy to use (default: TimeoutDebounceStrategy)
        """
        self._debounce_delay_ms = delay_ms
        self._debounce_strategy = strategy or TimeoutDebounceStrategy()
        self._debounced_callback: Optional[Callable[[Any], None]] = None
    
    def set_debounced_callback(
        self,
        callback: Callable[[Any], None],
        delay_ms: Optional[int] = None
    ) -> None:
        """
        Register a debounced callback for this widget.
        
        The callback will be invoked after the user stops interacting
        with the widget for the specified delay period.
        
        Args:
            callback: Function to call with widget as argument
            delay_ms: Override default delay (optional)
        """
        self._debounced_callback = callback
        if delay_ms is not None:
            self._debounce_delay_ms = delay_ms
    
    def _schedule_debounced_callback(self) -> None:
        """
        Schedule the debounced callback for execution.
        
        This should be called by the widget whenever a change event occurs
        (e.g., in signal handlers). The callback will only execute after
        the delay period with no further changes.
        """
        if self._debounced_callback is None:
            return
        
        def execute_callback():
            if self._debounced_callback is not None:
                self._debounced_callback(self)
        
        self._debounce_strategy.schedule(execute_callback, self._debounce_delay_ms)
    
    def flush_debounced_callback(self) -> None:
        """
        Immediately execute pending callback without waiting.
        
        This is useful when you need to ensure all changes are processed,
        such as before committing buffered settings or closing a dialog.
        """
        self._debounce_strategy.flush()
    
    def cancel_debounced_callback(self) -> None:
        """
        Cancel any pending debounced callback.
        
        This should be called when the widget is destroyed or when
        you want to discard pending changes.
        """
        self._debounce_strategy.cancel()
    
    def get_debounce_delay(self) -> int:
        """
        Get current debounce delay in milliseconds.
        
        Returns:
            Delay in milliseconds
        """
        return self._debounce_delay_ms
    
    def set_debounce_delay(self, delay_ms: int) -> None:
        """
        Set debounce delay in milliseconds.
        
        Args:
            delay_ms: New delay (typically 100-500ms)
        """
        self._debounce_delay_ms = delay_ms
