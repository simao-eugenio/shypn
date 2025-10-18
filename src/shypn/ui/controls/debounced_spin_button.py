"""
Debounced SpinButton widget.

This module provides a GTK SpinButton with built-in debouncing for value
changes. This prevents rapid-fire callbacks during slider dragging or
continuous value adjustments.

Usage:
    spin = DebouncedSpinButton(adjustment, delay_ms=250)
    spin.set_debounced_callback(lambda widget: print(f"Final value: {widget.get_value()}"))
"""

from typing import Optional, Callable, Any
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .base import DebouncedWidget, DebounceStrategy


class DebouncedSpinButton(Gtk.SpinButton, DebouncedWidget):
    """
    GTK SpinButton with debounced value change callbacks.
    
    This widget wraps Gtk.SpinButton to add debouncing behavior for value
    changes. When the user drags the slider or rapidly clicks the increment/
    decrement buttons, the debounced callback is only invoked after the user
    stops for the specified delay period.
    
    This is especially important for simulation parameters where each change
    might trigger expensive computations or buffer updates.
    
    Example:
        # Create with adjustment
        adj = Gtk.Adjustment(value=1.0, lower=0.0, upper=10.0, step_increment=0.1)
        spin = DebouncedSpinButton(adjustment=adj, delay_ms=250)
        
        # Register debounced callback
        def on_value_changed(widget):
            value = widget.get_value()
            buffered_settings.set_parameter('time_scale', value)
        
        spin.set_debounced_callback(on_value_changed)
        
        # Force immediate execution (e.g., before dialog close)
        spin.flush_debounced_callback()
    
    Attributes:
        Inherits from Gtk.SpinButton and DebouncedWidget
    """
    
    def __init__(
        self,
        adjustment: Optional[Gtk.Adjustment] = None,
        climb_rate: float = 0.0,
        digits: int = 0,
        delay_ms: int = 250,
        strategy: Optional[DebounceStrategy] = None
    ):
        """
        Initialize debounced spin button.
        
        Args:
            adjustment: GTK adjustment for value range (optional)
            climb_rate: Acceleration rate for continuous changes
            digits: Number of decimal places to display
            delay_ms: Debounce delay in milliseconds (default 250ms)
            strategy: Custom debounce strategy (optional)
        """
        # Initialize GTK SpinButton
        Gtk.SpinButton.__init__(
            self,
            adjustment=adjustment,
            climb_rate=climb_rate,
            digits=digits
        )
        
        # Initialize debouncing
        DebouncedWidget.__init__(self, delay_ms=delay_ms, strategy=strategy)
        
        # Connect to raw value-changed signal
        self.connect('value-changed', self._on_raw_value_changed)
    
    def _on_raw_value_changed(self, widget: Gtk.SpinButton) -> None:
        """
        Internal handler for raw value-changed signals.
        
        This is called on every value change (potentially 100+ times
        during slider drag). It schedules the debounced callback which
        will only execute after the user stops changing the value.
        
        Args:
            widget: The SpinButton (self)
        """
        self._schedule_debounced_callback()
    
    def set_value_debounced(
        self,
        value: float,
        trigger_callback: bool = False
    ) -> None:
        """
        Set value without triggering debounced callback.
        
        This is useful for programmatically setting values (e.g., loading
        from file) without causing unnecessary callback execution.
        
        Args:
            value: New value to set
            trigger_callback: If True, schedule debounced callback
        """
        # Temporarily disconnect to avoid triggering callback
        handler_id = self.handler_block_by_func(self._on_raw_value_changed)
        try:
            self.set_value(value)
        finally:
            self.handler_unblock(handler_id)
        
        if trigger_callback:
            self._schedule_debounced_callback()
    
    def get_value_float(self) -> float:
        """
        Get current value as float.
        
        Convenience method for clearer code.
        
        Returns:
            Current spin button value
        """
        return self.get_value()
    
    def destroy(self) -> None:
        """
        Clean up debounce resources before destroying widget.
        
        This ensures any pending callbacks are cancelled and GLib
        timeout sources are removed.
        """
        self.cancel_debounced_callback()
        Gtk.SpinButton.destroy(self)


# Convenience factory function
def create_debounced_spin_button(
    value: float,
    lower: float,
    upper: float,
    step: float = 1.0,
    page: float = 10.0,
    digits: int = 0,
    delay_ms: int = 250,
    callback: Optional[Callable[[DebouncedSpinButton], None]] = None
) -> DebouncedSpinButton:
    """
    Factory function to create a fully configured DebouncedSpinButton.
    
    This convenience function creates the adjustment and widget in one call,
    reducing boilerplate code.
    
    Args:
        value: Initial value
        lower: Minimum value
        upper: Maximum value  
        step: Step increment (default 1.0)
        page: Page increment (default 10.0)
        digits: Decimal places to display (default 0)
        delay_ms: Debounce delay in milliseconds (default 250)
        callback: Debounced callback function (optional)
    
    Returns:
        Configured DebouncedSpinButton
    
    Example:
        spin = create_debounced_spin_button(
            value=1.0,
            lower=0.1,
            upper=10.0,
            step=0.1,
            digits=1,
            callback=lambda w: print(f"Value: {w.get_value()}")
        )
    """
    adjustment = Gtk.Adjustment(
        value=value,
        lower=lower,
        upper=upper,
        step_increment=step,
        page_increment=page,
        page_size=0
    )
    
    spin = DebouncedSpinButton(
        adjustment=adjustment,
        climb_rate=0.0,
        digits=digits,
        delay_ms=delay_ms
    )
    
    if callback is not None:
        spin.set_debounced_callback(callback)
    
    return spin
