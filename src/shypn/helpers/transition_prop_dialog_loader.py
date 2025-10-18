"""
Transition Properties Dialog Loader

**DEPRECATED**: This module provides backward compatibility wrapper.
New code should use: from shypn.ui.dialogs.transition import TransitionPropertyDialog

Maintains API compatibility with existing code while delegating to new OOP architecture.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject

# Import new OOP implementation
from shypn.ui.dialogs.transition import TransitionPropertyDialog


class TransitionPropDialogLoader(GObject.GObject):
    """Loader for Transition properties dialog.
    
    **DEPRECATED**: This is a compatibility wrapper around TransitionPropertyDialog.
    New code should use TransitionPropertyDialog directly from:
        from shypn.ui.dialogs.transition import TransitionPropertyDialog
        
    This wrapper maintains backward compatibility with existing code that uses
    the old loader API while delegating all functionality to the new modular
    OOP architecture.
    
    Signals:
        properties-changed: Emitted when properties are changed and applied
    """
    
    __gsignals__ = {
        'properties-changed': (GObject.SignalFlags.RUN_FIRST, None, ())
    }
    
    def __init__(self, transition_obj, parent_window=None, ui_dir=None,
                 persistency_manager=None, model=None, data_collector=None):
        """Initialize the Transition properties dialog loader.
        
        Args:
            transition_obj: Transition object to edit properties for
            parent_window: Parent window for modal dialog
            ui_dir: Directory containing UI files (auto-detected if None)
            persistency_manager: NetObjPersistency for document dirty tracking
            model: ModelCanvasManager for accessing Petri net structure
            data_collector: SimulationDataCollector for runtime diagnostics
        """
        super().__init__()
        
        # Create new-style dialog instance
        self._dialog_impl = TransitionPropertyDialog(
            net_object=transition_obj,
            parent_window=parent_window,
            ui_dir=ui_dir,
            persistency_manager=persistency_manager,
            model=model,
            data_collector=data_collector
        )
        
        # Forward properties-changed signal
        self._dialog_impl.connect('properties-changed', self._on_properties_changed)
        
        # Expose attributes for backward compatibility
        self.dialog = self._dialog_impl.dialog
        self.builder = self._dialog_impl.builder
        self.transition_obj = transition_obj
        self.ui_dir = self._dialog_impl.ui_dir
        self.color_picker = self._dialog_impl.color_picker
    
    def _on_properties_changed(self, dialog_impl):
        """Forward properties-changed signal from new implementation."""
        self.emit('properties-changed')
    
    def run(self):
        """Run the dialog modally.
        
        Returns:
            Response ID (OK, CANCEL, etc.)
        """
        return self._dialog_impl.run()
    
    def show(self):
        """Show the dialog non-modally."""
        self._dialog_impl.show()
    
    def destroy(self):
        """Destroy the dialog."""
        self._dialog_impl.destroy()
