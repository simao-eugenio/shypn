"""Abstract base class for property dialogs.

Provides common functionality for all property dialog implementations:
- UI loading from Glade files
- Field population and extraction
- Validation framework
- Atomic apply with rollback
- Color picker integration
- Change tracking and persistence
"""

import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

from shypn.helpers.color_picker import setup_color_picker_in_dialog


# Create a metaclass that combines GObject and ABC metaclasses
class PropertyDialogMeta(type(GObject.GObject), type(ABC)):
    """Metaclass combining GObject and ABC."""
    pass


class PropertyDialogBase(GObject.GObject, ABC, metaclass=PropertyDialogMeta):
    """Abstract base class for property dialogs.
    
    Provides common infrastructure for editing Petri net object properties
    with validation, rollback, and persistence integration.
    
    Signals:
        properties-changed: Emitted when properties are successfully applied
    
    Subclasses must implement:
        - get_ui_filename() -> str
        - get_dialog_id() -> str
        - populate_fields()
        - validate_fields() -> List[str]
        - apply_changes()
        - get_field_specs() -> Dict (optional, for generic handling)
    """
    
    __gsignals__ = {
        'properties-changed': (GObject.SignalFlags.RUN_FIRST, None, ())
    }
    
    def __init__(self, 
                 net_object: Any,
                 parent_window: Optional[Gtk.Window] = None,
                 ui_dir: Optional[str] = None,
                 persistency_manager: Optional[Any] = None,
                 model: Optional[Any] = None,
                 data_collector: Optional[Any] = None):
        """Initialize property dialog base.
        
        Args:
            net_object: Petri net object to edit (Place, Transition, or Arc)
            parent_window: Parent window for modal dialog
            ui_dir: Directory containing UI files (auto-detected if None)
            persistency_manager: NetObjPersistency for document dirty tracking
            model: ModelCanvasManager for accessing net structure
            data_collector: SimulationDataCollector for runtime stats
        """
        super().__init__()
        
        self.net_object = net_object
        self.parent_window = parent_window
        self.persistency_manager = persistency_manager
        self.model = model
        self.data_collector = data_collector
        
        # Determine UI directory
        if ui_dir is None:
            # Auto-detect: go up from src/shypn/ui/dialogs/base to project root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))))
            ui_dir = os.path.join(project_root, 'ui', 'dialogs')
        
        self.ui_dir = ui_dir
        self.ui_path = os.path.join(ui_dir, self.get_ui_filename())
        
        # Widget references (populated by subclasses)
        self.builder: Optional[Gtk.Builder] = None
        self.dialog: Optional[Gtk.Dialog] = None
        self.color_picker = None
        
        # State tracking
        self._original_values: Dict[str, Any] = {}
        self._validation_errors: List[str] = []
        
        # Initialize dialog
        self._load_ui()
        self._setup_dialog()
        self._setup_color_picker()
        self.populate_fields()
        self._setup_additional_widgets()
    
    # ========== Abstract Methods (must be implemented by subclasses) ==========
    
    @abstractmethod
    def get_ui_filename(self) -> str:
        """Get the UI filename for this dialog.
        
        Returns:
            Filename like 'transition_prop_dialog.ui'
        """
        pass
    
    @abstractmethod
    def get_dialog_id(self) -> str:
        """Get the GTK object ID of the main dialog.
        
        Returns:
            ID like 'transition_properties_dialog'
        """
        pass
    
    @abstractmethod
    def populate_fields(self):
        """Populate dialog fields with current object properties.
        
        Called during initialization to load current values into UI.
        Subclasses should get widgets via self.builder.get_object()
        and set their values from self.net_object attributes.
        """
        pass
    
    @abstractmethod
    def validate_fields(self) -> List[str]:
        """Validate all fields and return list of error messages.
        
        Returns:
            List of error strings. Empty list = valid.
            Each error should be user-friendly, e.g.:
            "Rate function: Syntax error at position 5"
        """
        pass
    
    @abstractmethod
    def apply_changes(self):
        """Apply validated changes to the net object.
        
        Called after validation succeeds. Should:
        1. Store original values in self._original_values for rollback
        2. Read values from UI widgets
        3. Set attributes on self.net_object
        4. Update any properties dict if applicable
        
        Raises:
            Exception: If apply fails (will trigger rollback)
        """
        pass
    
    # ========== Optional Methods (can be overridden) ==========
    
    def _setup_additional_widgets(self):
        """Setup additional widgets after UI load.
        
        Optional hook for subclasses to setup custom widgets
        like locality displays, runtime stats, etc.
        """
        pass
    
    def get_color_attribute_name(self) -> str:
        """Get the attribute name for color on the net object.
        
        Returns:
            Attribute name like 'border_color' or 'fill_color'
            Default: 'border_color'
        """
        return 'border_color'
    
    def get_color_picker_container_id(self) -> str:
        """Get the container ID for inserting color picker.
        
        Returns:
            Container ID like 'transition_color_picker'
            Default: None (no color picker)
        """
        return None
    
    # ========== Common Implementation ==========
    
    def _load_ui(self):
        """Load the dialog UI from Glade file."""
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(
                f"Property dialog UI file not found: {self.ui_path}"
            )
        
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        self.dialog = self.builder.get_object(self.get_dialog_id())
        
        if self.dialog is None:
            raise ValueError(
                f"Dialog '{self.get_dialog_id()}' not found in {self.get_ui_filename()}"
            )
    
    def _setup_dialog(self):
        """Setup dialog properties and connect signals."""
        # Set parent window
        if self.parent_window:
            self.dialog.set_transient_for(self.parent_window)
        
        # Wire OK and Cancel buttons
        ok_button = self.builder.get_object('ok_button')
        cancel_button = self.builder.get_object('cancel_button')
        
        if ok_button:
            ok_button.connect('clicked', 
                            lambda btn: self.dialog.response(Gtk.ResponseType.OK))
        if cancel_button:
            cancel_button.connect('clicked', 
                                lambda btn: self.dialog.response(Gtk.ResponseType.CANCEL))
        
        # Connect response handler
        self.dialog.connect('response', self._on_response)
    
    def _setup_color_picker(self):
        """Setup color picker if container is defined."""
        container_id = self.get_color_picker_container_id()
        if not container_id:
            return  # No color picker for this dialog
        
        # Get initial color
        color_attr = self.get_color_attribute_name()
        initial_color = getattr(self.net_object, color_attr, (0.0, 0.0, 0.0))
        
        # Setup color picker
        self.color_picker = setup_color_picker_in_dialog(
            self.builder,
            container_id,
            current_color=initial_color,
            button_size=28
        )
        
        # Connect to color selection signal if picker was created
        if self.color_picker:
            self.color_picker.connect('color-selected', self._on_color_selected)
    
    def _on_color_selected(self, picker, color_rgb):
        """Handle color selection.
        
        Args:
            picker: ColorPickerRow widget
            color_rgb: Selected color as RGB tuple (0.0-1.0)
        """
        # Color will be applied in apply_changes()
        pass
    
    def _on_response(self, dialog: Gtk.Dialog, response_id: int):
        """Handle dialog response (OK or Cancel).
        
        Args:
            dialog: The dialog widget
            response_id: Response type (OK, CANCEL, etc.)
        """
        if response_id != Gtk.ResponseType.OK:
            # Cancel - destroy dialog without changes
            dialog.destroy()
            return
        
        # Validate all fields
        self._validation_errors = self.validate_fields()
        
        if self._validation_errors:
            # Show validation errors
            self._show_validation_errors()
            
            # Don't close dialog - let user fix errors
            dialog.stop_emission_by_name('response')
            return
        
        # All valid - apply changes atomically
        try:
            self.apply_changes()
            
            # Mark document dirty
            if self.persistency_manager:
                self.persistency_manager.mark_dirty()
            
            # Emit properties-changed signal
            self.emit('properties-changed')
            
            # Close dialog
            dialog.destroy()
            
        except Exception as e:
            # Rollback on error
            self._rollback_changes()
            
            # Show error
            self._show_apply_error(str(e))
            
            # Don't close dialog
            dialog.stop_emission_by_name('response')
    
    def _show_validation_errors(self):
        """Show validation error dialog to user."""
        error_dialog = Gtk.MessageDialog(
            parent=self.dialog,
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            message_format="Validation Errors"
        )
        
        error_text = "\n".join(f"• {err}" for err in self._validation_errors)
        error_dialog.format_secondary_text(error_text)
        
        error_dialog.run()
        error_dialog.destroy()
    
    def _show_apply_error(self, error_message: str):
        """Show error dialog when apply fails.
        
        Args:
            error_message: Error description
        """
        error_dialog = Gtk.MessageDialog(
            parent=self.dialog,
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            message_format="Failed to Apply Changes"
        )
        error_dialog.format_secondary_text(error_message)
        
        error_dialog.run()
        error_dialog.destroy()
    
    def _rollback_changes(self):
        """Rollback changes using stored original values."""
        if not self._original_values:
            return  # Nothing to rollback
        
        for attr, value in self._original_values.items():
            if attr == 'properties':
                # Deep copy properties dict
                self.net_object.properties = dict(value) if value else {}
            else:
                setattr(self.net_object, attr, value)
    
    # ========== Utility Methods ==========
    
    def get_widget(self, widget_id: str) -> Optional[Gtk.Widget]:
        """Safely get widget by ID.
        
        Args:
            widget_id: GTK object ID
        
        Returns:
            Widget or None if not found
        """
        return self.builder.get_object(widget_id) if self.builder else None
    
    def get_text_from_entry(self, entry_id: str) -> str:
        """Get text from Entry widget.
        
        Args:
            entry_id: Entry widget ID
        
        Returns:
            Text content or empty string
        """
        entry = self.get_widget(entry_id)
        return entry.get_text().strip() if entry else ""
    
    def get_text_from_textview(self, textview_id: str) -> str:
        """Get text from TextView widget.
        
        Args:
            textview_id: TextView widget ID
        
        Returns:
            Text content or empty string
        """
        textview = self.get_widget(textview_id)
        if not textview:
            return ""
        
        buffer = textview.get_buffer()
        start, end = buffer.get_bounds()
        return buffer.get_text(start, end, True).strip()
    
    def set_entry_text(self, entry_id: str, text: str):
        """Set text in Entry widget.
        
        Args:
            entry_id: Entry widget ID
            text: Text to set
        """
        entry = self.get_widget(entry_id)
        if entry:
            entry.set_text(str(text))
    
    def set_textview_text(self, textview_id: str, text: str):
        """Set text in TextView widget.
        
        Args:
            textview_id: TextView widget ID
            text: Text to set
        """
        textview = self.get_widget(textview_id)
        if textview:
            buffer = textview.get_buffer()
            buffer.set_text(str(text))
    
    def store_original_value(self, attr_name: str):
        """Store original value of an attribute for rollback.
        
        Args:
            attr_name: Attribute name on self.net_object
        """
        if attr_name not in self._original_values:
            value = getattr(self.net_object, attr_name, None)
            
            # Deep copy for mutable types
            if isinstance(value, dict):
                self._original_values[attr_name] = dict(value)
            elif isinstance(value, list):
                self._original_values[attr_name] = list(value)
            else:
                self._original_values[attr_name] = value
    
    def run(self) -> int:
        """Run the dialog modally.
        
        Returns:
            Response ID (OK, CANCEL, etc.)
        """
        return self.dialog.run()
    
    def show(self):
        """Show the dialog non-modally."""
        self.dialog.show()
    
    def destroy(self):
        """Destroy the dialog."""
        if self.dialog:
            self.dialog.destroy()
