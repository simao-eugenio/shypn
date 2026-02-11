#!/usr/bin/env python3
"""
Base class for all property dialogs.

Provides common functionality:
- UI loading
- Wayland-safe modal behavior
- Property validation coordination
- Dirty state tracking
"""

import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GObject

logger = logging.getLogger(__name__)


class WaylandDialogMixin:
    """Mixin providing Wayland-safe dialog behavior.
    
    Centralizes all Wayland-specific workarounds in one place.
    Tested on Ubuntu 24.04 Wayland.
    
    Protocol error fixes:
    - Error 71: xdg_toplevel@## protocol error: xdg_toplevel must have a buffer before commit
    - Solution: Ensure parent is mapped/realized, sync compositor, delay for state transitions
    """
    
    def _ensure_parent_ready(self) -> None:
        """Ensure parent window is mapped before setting transient.
        
        On Wayland, set_transient_for() requires parent to be mapped.
        Calling it on an unmapped parent triggers protocol warnings.
        """
        if not self.parent_window:
            return
            
        parent_mapped = self.parent_window.get_mapped()
        parent_realized = self.parent_window.get_realized()
        
        logger.debug(f"[WAYLAND] Parent mapped: {parent_mapped}, realized: {parent_realized}")
        
        if not parent_mapped:
            logger.warning("[WAYLAND] Parent window not mapped; may trigger protocol warnings")
    
    def _sync_compositor(self) -> None:
        """Wait for Wayland compositor to process pending events.
        
        Ensures compositor has processed all widget state changes before
        attempting to set transient parent.
        """
        display = Gdk.Display.get_default()
        if display:
            display.sync()
            logger.debug("[WAYLAND] Display sync completed")
    
    def _handle_window_state_transitions(self) -> None:
        """Check for problematic window states and delay if needed.
        
        When parent window is maximized, fullscreen, or tiled, the compositor
        may be in the middle of a state transition. Wait 100ms to let it settle.
        """
        if not self.parent_window:
            return
            
        window = self.parent_window.get_window()
        if not window:
            return
            
        state = window.get_state()
        is_maximized = bool(state & Gdk.WindowState.MAXIMIZED)
        is_fullscreen = bool(state & Gdk.WindowState.FULLSCREEN)
        is_tiled = bool(state & Gdk.WindowState.TILED)
        
        logger.debug(
            f"[WAYLAND] Window state: maximized={is_maximized}, "
            f"fullscreen={is_fullscreen}, tiled={is_tiled}"
        )
        
        if is_maximized or is_fullscreen or is_tiled:
            logger.debug("[WAYLAND] Special state detected; delaying 100ms")
            import time
            time.sleep(0.1)
    
    def _set_transient_safe(self) -> None:
        """Set transient parent with all Wayland safety checks.
        
        Call this instead of dialog.set_transient_for() directly.
        """
        if not self.parent_window:
            return
            
        # Step 1: Ensure parent is ready
        self._ensure_parent_ready()
        
        # Step 2: Handle window state transitions
        self._handle_window_state_transitions()
        
        # Step 3: Sync compositor
        self._sync_compositor()
        
        # Step 4: Now safe to set transient
        self.dialog.set_transient_for(self.parent_window)
        logger.debug("[WAYLAND] set_transient_for completed safely")


class PropertyDialogBase(GObject.GObject, WaylandDialogMixin):
    """Base class for all property dialogs.
    
    Provides:
    - UI loading from .ui files
    - Common signal handling  
    - Wayland-safe modal dialog behavior
    - Property validation coordination
    - Dirty state tracking
    
    Subclasses must implement:
    - _create_property_manager(): Return appropriate PropertyManager
    - _setup_widgets(): Setup dialog-specific widgets
    - _populate_fields(): Populate UI from netobject
    - _save_properties(): Save UI to netobject
    
    Signals:
        properties-changed: Emitted when properties are successfully saved
    """
    
    __gsignals__ = {
        'properties-changed': (GObject.SignalFlags.RUN_FIRST, None, ())
    }
    
    def __init__(self, netobject, parent_window: Optional[Gtk.Window] = None, 
                 model=None, persistency_manager=None):
        """Initialize property dialog.
        
        Args:
            netobject: Place, Transition, or Arc object to edit
            parent_window: Parent window for modal behavior
            model: PetriNetModel for topology/context information
            persistency_manager: For marking document dirty
        """
        super().__init__()
        
        self.netobject = netobject
        self.parent_window = parent_window
        self.model = model
        self.persistency_manager = persistency_manager
        
        # Create property manager (delegates business logic)
        self.property_manager = self._create_property_manager()
        
        # State tracking
        self.is_dirty = False
        
        # UI components (set by subclasses)
        self.builder: Optional[Gtk.Builder] = None
        self.dialog: Optional[Gtk.Dialog] = None
    
    def _create_property_manager(self):
        """Create appropriate property manager for this netobject type.
        
        Must be implemented by subclasses.
        
        Returns:
            PropertyManager subclass instance
        """
        raise NotImplementedError("Subclasses must implement _create_property_manager()")
    
    def _get_ui_path(self, ui_filename: str) -> Path:
        """Get full path to UI file.
        
        Args:
            ui_filename: Name of .ui file (e.g., 'place_prop_dialog.ui')
            
        Returns:
            Path to UI file
        """
        # Find project root
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent
        
        ui_path = project_root / 'ui' / 'dialogs' / ui_filename
        
        if not ui_path.exists():
            raise FileNotFoundError(f"UI file not found: {ui_path}")
            
        return ui_path
    
    def _load_ui(self, ui_filename: str) -> None:
        """Load UI from .ui file.
        
        Args:
            ui_filename: Name of .ui file
        """
        ui_path = self._get_ui_path(ui_filename)
        
        self.builder = Gtk.Builder.new_from_file(str(ui_path))
        self.dialog = self.builder.get_object(self._get_dialog_id())
        
        if self.dialog is None:
            raise ValueError(f"Dialog '{self._get_dialog_id()}' not found in {ui_filename}")
        
        # Connect response signal
        self.dialog.connect('response', self._on_response)
        
        logger.debug(f"Loaded UI from {ui_path}")
    
    def _get_dialog_id(self) -> str:
        """Get dialog widget ID from .ui file.
        
        Override if dialog ID differs from convention.
        
        Returns:
            Dialog widget ID
        """
        # Default convention: place_properties_dialog, transition_properties_dialog, etc.
        type_name = type(self.netobject).__name__.lower()
        return f"{type_name}_properties_dialog"
    
    def _setup_widgets(self) -> None:
        """Setup dialog-specific widgets.
        
        Override in subclasses to:
        - Add color pickers
        - Add custom panels (spatial, topology, etc.)
        - Connect additional signals
        """
        pass
    
    def _populate_fields(self) -> None:
        """Populate dialog fields from netobject.
        
        Must be implemented by subclasses.
        Gets data from property_manager and updates UI widgets.
        """
        raise NotImplementedError("Subclasses must implement _populate_fields()")
    
    def _save_properties(self) -> None:
        """Save dialog fields to netobject.
        
        Must be implemented by subclasses.
        Collects data from UI widgets and passes to property_manager.
        """
        raise NotImplementedError("Subclasses must implement _save_properties()")
    
    def _validate_properties(self) -> Tuple[bool, List[str]]:
        """Validate current property values.
        
        Delegates to property_manager for business logic validation.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        # Collect current data from UI (implemented by subclass)
        data = self._collect_ui_data()
        
        # Validate via property manager
        return self.property_manager.validate_properties(data)
    
    def _collect_ui_data(self) -> Dict[str, Any]:
        """Collect all data from UI widgets.
        
        Override in subclasses to collect dialog-specific data.
        Used by _validate_properties() to validate before saving.
        
        Returns:
            Dictionary of property_name -> value
        """
        # Default: return empty dict, subclasses should override
        return {}
    
    def _show_validation_errors(self, errors: List[str]) -> None:
        """Show validation error dialog to user.
        
        Args:
            errors: List of error messages
        """
        error_dialog = Gtk.MessageDialog(
            transient_for=self.dialog,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Invalid Properties"
        )
        
        error_text = "\n".join(f"• {error}" for error in errors)
        error_dialog.format_secondary_text(error_text)
        
        error_dialog.run()
        error_dialog.destroy()
    
    def _on_response(self, dialog: Gtk.Dialog, response: Gtk.ResponseType) -> None:
        """Handle dialog response (OK, Cancel, etc.).
        
        Args:
            dialog: The dialog widget
            response: Response type
        """
        if response == Gtk.ResponseType.OK:
            # Validate before saving
            is_valid, errors = self._validate_properties()
            
            if is_valid:
                # Save properties
                self._save_properties()
                
                # Mark document dirty
                if self.persistency_manager:
                    self.persistency_manager.mark_document_dirty()
                
                # Emit signal
                self.emit('properties-changed')
                
                # Mark as not dirty so dialog can close
                self.is_dirty = False
            else:
                # Show errors and prevent close
                self._show_validation_errors(errors)
                dialog.stop_emission_by_name('response')
                return
    
    def run(self) -> Gtk.ResponseType:
        """Show dialog and run modally with Wayland safety.
        
        Returns:
            Response type (OK, Cancel, etc.)
        """
        # Apply Wayland safety measures (from mixin)
        self._set_transient_safe()
        
        # Show dialog before run() to prevent protocol errors
        self.dialog.show()
        logger.debug("[WAYLAND] dialog.show() completed; entering run() loop")
        
        # Run modal
        response = self.dialog.run()
        
        return response
    
    def destroy(self) -> None:
        """Clean up dialog and all widget references.
        
        Ensures proper cleanup to prevent memory leaks and orphaned widgets.
        """
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None
        
        # Clean up references
        self.builder = None
        self.netobject = None
        self.parent_window = None
        self.property_manager = None
        self.persistency_manager = None
        self.model = None
    
    # ========== Helper Methods for Subclasses ==========
    
    def _get_entry(self, widget_id: str) -> str:
        """Get text from entry widget.
        
        Args:
            widget_id: Widget ID in .ui file
            
        Returns:
            Entry text value
        """
        entry = self.builder.get_object(widget_id)
        if entry:
            return entry.get_text().strip()
        return ""
    
    def _get_entry_float(self, widget_id: str, default: float = 0.0) -> float:
        """Get float value from entry widget.
        
        Args:
            widget_id: Widget ID in .ui file
            default: Default value if parsing fails
            
        Returns:
            Float value
        """
        text = self._get_entry(widget_id)
        try:
            return float(text) if text else default
        except ValueError:
            return default
    
    def _set_entry(self, widget_id: str, value: Any) -> None:
        """Set text in entry widget.
        
        Args:
            widget_id: Widget ID in .ui file
            value: Value to set (will be converted to string)
        """
        entry = self.builder.get_object(widget_id)
        if entry:
            entry.set_text(str(value) if value is not None else "")
    
    def _get_checkbox(self, widget_id: str) -> bool:
        """Get checkbox state.
        
        Args:
            widget_id: Widget ID in .ui file
            
        Returns:
            Checkbox active state
        """
        checkbox = self.builder.get_object(widget_id)
        if checkbox:
            return checkbox.get_active()
        return False
    
    def _set_checkbox(self, widget_id: str, active: bool) -> None:
        """Set checkbox state.
        
        Args:
            widget_id: Widget ID in .ui file
            active: Active state
        """
        checkbox = self.builder.get_object(widget_id)
        if checkbox:
            checkbox.set_active(active)
    
    def _get_textview(self, widget_id: str) -> str:
        """Get text from textview widget.
        
        Args:
            widget_id: Widget ID in .ui file
            
        Returns:
            Textview content
        """
        textview = self.builder.get_object(widget_id)
        if textview:
            buffer = textview.get_buffer()
            start = buffer.get_start_iter()
            end = buffer.get_end_iter()
            return buffer.get_text(start, end, True).strip()
        return ""
    
    def _set_textview(self, widget_id: str, text: str) -> None:
        """Set text in textview widget.
        
        Args:
            widget_id: Widget ID in .ui file
            text: Text to set
        """
        textview = self.builder.get_object(widget_id)
        if textview:
            buffer = textview.get_buffer()
            buffer.set_text(text if text else "")
