"""
Debounced Entry widget.

This module provides a GTK Entry with built-in debouncing for text
changes. This prevents rapid-fire callbacks during fast typing or
paste operations.

Usage:
    entry = DebouncedEntry(delay_ms=300)
    entry.set_debounced_callback(lambda widget: print(f"Final text: {widget.get_text()}"))
"""

from typing import Optional, Callable
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .base import DebouncedWidget, DebounceStrategy


class DebouncedEntry(Gtk.Entry, DebouncedWidget):
    """
    GTK Entry with debounced text change callbacks.
    
    This widget wraps Gtk.Entry to add debouncing behavior for text
    changes. When the user types rapidly or pastes large amounts of text,
    the debounced callback is only invoked after the user stops for the
    specified delay period.
    
    This is useful for:
    - Search fields (avoid searching on every keystroke)
    - Parameter inputs (avoid validating/applying on every character)
    - Filtering (reduce UI updates during typing)
    
    Example:
        # Create entry
        entry = DebouncedEntry(delay_ms=300)
        entry.set_placeholder_text("Enter value...")
        
        # Register debounced callback
        def on_text_changed(widget):
            text = widget.get_text()
            try:
                value = float(text)
                buffered_settings.set_parameter('rate', value)
            except ValueError:
                pass  # Invalid input, ignore
        
        entry.set_debounced_callback(on_text_changed)
        
        # Force immediate execution (e.g., before dialog close)
        entry.flush_debounced_callback()
    
    Attributes:
        Inherits from Gtk.Entry and DebouncedWidget
    """
    
    def __init__(
        self,
        delay_ms: int = 300,
        strategy: Optional[DebounceStrategy] = None
    ):
        """
        Initialize debounced entry.
        
        Args:
            delay_ms: Debounce delay in milliseconds (default 300ms)
            strategy: Custom debounce strategy (optional)
        """
        # Initialize GTK Entry
        Gtk.Entry.__init__(self)
        
        # Initialize debouncing
        DebouncedWidget.__init__(self, delay_ms=delay_ms, strategy=strategy)
        
        # Connect to raw changed signal
        self.connect('changed', self._on_raw_text_changed)
    
    def _on_raw_text_changed(self, widget: Gtk.Entry) -> None:
        """
        Internal handler for raw changed signals.
        
        This is called on every text change (every keystroke, paste, etc.).
        It schedules the debounced callback which will only execute after
        the user stops typing.
        
        Args:
            widget: The Entry (self)
        """
        self._schedule_debounced_callback()
    
    def set_text_debounced(
        self,
        text: str,
        trigger_callback: bool = False
    ) -> None:
        """
        Set text without triggering debounced callback.
        
        This is useful for programmatically setting text (e.g., loading
        from file) without causing unnecessary callback execution.
        
        Args:
            text: New text to set
            trigger_callback: If True, schedule debounced callback
        """
        # Temporarily disconnect to avoid triggering callback
        handler_id = self.handler_block_by_func(self._on_raw_text_changed)
        try:
            self.set_text(text)
        finally:
            self.handler_unblock(handler_id)
        
        if trigger_callback:
            self._schedule_debounced_callback()
    
    def get_text_stripped(self) -> str:
        """
        Get current text with leading/trailing whitespace removed.
        
        Convenience method for cleaner input handling.
        
        Returns:
            Trimmed text content
        """
        return self.get_text().strip()
    
    def is_empty(self) -> bool:
        """
        Check if entry is empty (ignoring whitespace).
        
        Returns:
            True if entry contains only whitespace or is empty
        """
        return len(self.get_text_stripped()) == 0
    
    def destroy(self) -> None:
        """
        Clean up debounce resources before destroying widget.
        
        This ensures any pending callbacks are cancelled and GLib
        timeout sources are removed.
        """
        self.cancel_debounced_callback()
        Gtk.Entry.destroy(self)


class DebouncedSearchEntry(Gtk.SearchEntry, DebouncedWidget):
    """
    GTK SearchEntry with debounced text change callbacks.
    
    Similar to DebouncedEntry but uses Gtk.SearchEntry which includes
    search-specific styling and a clear button.
    
    Example:
        search = DebouncedSearchEntry(delay_ms=200)
        search.set_debounced_callback(lambda w: filter_results(w.get_text()))
    """
    
    def __init__(
        self,
        delay_ms: int = 200,
        strategy: Optional[DebounceStrategy] = None
    ):
        """
        Initialize debounced search entry.
        
        Args:
            delay_ms: Debounce delay in milliseconds (default 200ms,
                     shorter for better search responsiveness)
            strategy: Custom debounce strategy (optional)
        """
        # Initialize GTK SearchEntry
        Gtk.SearchEntry.__init__(self)
        
        # Initialize debouncing
        DebouncedWidget.__init__(self, delay_ms=delay_ms, strategy=strategy)
        
        # Connect to search-changed signal (preferred for SearchEntry)
        self.connect('search-changed', self._on_raw_search_changed)
    
    def _on_raw_search_changed(self, widget: Gtk.SearchEntry) -> None:
        """
        Internal handler for raw search-changed signals.
        
        Args:
            widget: The SearchEntry (self)
        """
        self._schedule_debounced_callback()
    
    def set_text_debounced(
        self,
        text: str,
        trigger_callback: bool = False
    ) -> None:
        """
        Set text without triggering debounced callback.
        
        Args:
            text: New text to set
            trigger_callback: If True, schedule debounced callback
        """
        # Temporarily disconnect to avoid triggering callback
        handler_id = self.handler_block_by_func(self._on_raw_search_changed)
        try:
            self.set_text(text)
        finally:
            self.handler_unblock(handler_id)
        
        if trigger_callback:
            self._schedule_debounced_callback()
    
    def get_text_stripped(self) -> str:
        """
        Get current text with leading/trailing whitespace removed.
        
        Returns:
            Trimmed text content
        """
        return self.get_text().strip()
    
    def is_empty(self) -> bool:
        """
        Check if entry is empty (ignoring whitespace).
        
        Returns:
            True if entry contains only whitespace or is empty
        """
        return len(self.get_text_stripped()) == 0
    
    def destroy(self) -> None:
        """
        Clean up debounce resources before destroying widget.
        """
        self.cancel_debounced_callback()
        Gtk.SearchEntry.destroy(self)


# Convenience factory function
def create_debounced_entry(
    text: str = "",
    placeholder: str = "",
    delay_ms: int = 300,
    callback: Optional[Callable[[DebouncedEntry], None]] = None
) -> DebouncedEntry:
    """
    Factory function to create a fully configured DebouncedEntry.
    
    Args:
        text: Initial text content (default "")
        placeholder: Placeholder text (default "")
        delay_ms: Debounce delay in milliseconds (default 300)
        callback: Debounced callback function (optional)
    
    Returns:
        Configured DebouncedEntry
    
    Example:
        entry = create_debounced_entry(
            placeholder="Enter parameter value",
            delay_ms=250,
            callback=lambda w: apply_value(w.get_text())
        )
    """
    entry = DebouncedEntry(delay_ms=delay_ms)
    
    if text:
        entry.set_text_debounced(text, trigger_callback=False)
    
    if placeholder:
        entry.set_placeholder_text(placeholder)
    
    if callback is not None:
        entry.set_debounced_callback(callback)
    
    return entry
