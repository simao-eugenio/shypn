"""
Transition Properties Dialog Loader

Loads and manages the Transition properties dialog UI.
"""

import os
import json
import ast
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

from shypn.helpers.color_picker import setup_color_picker_in_dialog


class TransitionPropDialogLoader(GObject.GObject):
    """Loader for Transition properties dialog.
    
    This class loads and manages the Transition properties dialog UI from
    transition_prop_dialog.ui. The dialog allows editing Transition attributes
    such as name, label, and other properties.
    
    Signals:
        properties-changed: Emitted when properties are changed and applied
    """
    
    __gsignals__ = {
        'properties-changed': (GObject.SignalFlags.RUN_FIRST, None, ())
    }
    
    def __init__(self, transition_obj, parent_window=None, ui_dir: str = None, persistency_manager=None):
        """Initialize the Transition properties dialog loader.
        
        Args:
            transition_obj: Transition object to edit properties for.
            parent_window: Parent window for modal dialog.
            ui_dir: Directory containing UI files. Defaults to project ui/dialogs/.
            persistency_manager: NetObjPersistency instance for marking document dirty
        """
        super().__init__()
        
        # Determine UI directory
        if ui_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            ui_dir = os.path.join(project_root, 'ui', 'dialogs')
        
        self.ui_dir = ui_dir
        self.ui_path = os.path.join(ui_dir, 'transition_prop_dialog.ui')
        self.transition_obj = transition_obj
        self.parent_window = parent_window
        self.persistency_manager = persistency_manager
        
        # Widget references
        self.builder = None
        self.dialog = None
        self.color_picker = None
        
        # Load UI
        self._load_ui()
        self._setup_color_picker()
        self._populate_fields()
    
    def _load_ui(self):
        """Load the Transition properties dialog UI from file."""
        # Validate UI file exists
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f"Transition properties dialog UI file not found: {self.ui_path}")
        
        # Load the UI
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        
        # Extract main dialog widget
        self.dialog = self.builder.get_object('transition_properties_dialog')
        
        if self.dialog is None:
            raise ValueError("Object 'transition_properties_dialog' not found in transition_prop_dialog.ui")
        
        # Set parent window if provided
        if self.parent_window:
            self.dialog.set_transient_for(self.parent_window)
        
        # Wire OK and Cancel buttons
        ok_button = self.builder.get_object('ok_button')
        cancel_button = self.builder.get_object('cancel_button')
        
        if ok_button:
            ok_button.connect('clicked', lambda btn: self.dialog.response(Gtk.ResponseType.OK))
        if cancel_button:
            cancel_button.connect('clicked', lambda btn: self.dialog.response(Gtk.ResponseType.CANCEL))
        
        # Connect signals
        self.dialog.connect('response', self._on_response)
        
        print(f"[TransitionPropDialogLoader] UI loaded successfully from {self.ui_path}")
    
    def _setup_color_picker(self):
        """Setup color picker in the dialog."""
        # Get initial color (border_color for transitions)
        initial_color = getattr(self.transition_obj, 'border_color', (0.0, 0.0, 0.0))
        
        # Setup color picker using helper function
        self.color_picker = setup_color_picker_in_dialog(
            self.builder,
            'transition_color_picker',
            current_color=initial_color,
            button_size=28
        )
        
        # Connect to color selection signal if picker was created
        if self.color_picker:
            self.color_picker.connect('color-selected', self._on_color_selected)
            print("[TransitionPropDialogLoader] Color picker setup complete")
    
    def _on_color_selected(self, picker, color_rgb):
        """Callback when color is selected.
        
        Args:
            picker: The ColorPickerRow widget
            color_rgb: Selected color as RGB tuple (0.0-1.0)
        """
        print(f"[TransitionPropDialogLoader] Color selected: {color_rgb}")
    
    def _format_formula_for_display(self, formula):
        """Format formula value for display in UI TextView.
        
        Supports guard/rate formulas which can be:
        - None → empty string
        - dict → JSON formatted
        - number → string representation
        - expression string → as-is
        
        Args:
            formula: Can be None, dict, number, or string
        
        Returns:
            String representation for display
        """
        if formula is None:
            return ""
        elif isinstance(formula, dict):
            # Format dict as JSON for readability
            return json.dumps(formula, indent=2)
        elif isinstance(formula, (int, float)):
            return str(formula)
        else:
            # Already a string (expression)
            return str(formula)
    
    def _parse_formula(self, text):
        """Parse formula text from UI into appropriate format.
        
        Supports multiple formats:
        - Empty string → None
        - Number string → numeric value
        - Dictionary string → parsed dict
        - Expression string → kept as string
        
        Args:
            text: Raw text from TextView
        
        Returns:
            Parsed value (None, number, dict, or string)
        """
        text = text.strip()
        
        if not text:
            return None
        
        # Try to parse as number first
        try:
            # Try integer
            if '.' not in text:
                return int(text)
            # Try float
            return float(text)
        except ValueError:
            pass
        
        # Try to parse as dict (JSON or Python dict literal)
        if text.startswith('{') and text.endswith('}'):
            try:
                # Try ast.literal_eval for Python dict syntax
                return ast.literal_eval(text)
            except (ValueError, SyntaxError):
                try:
                    # Try JSON parsing
                    return json.loads(text)
                except json.JSONDecodeError:
                    pass
        
        # Return as string (expression)
        return text
    
    def _populate_fields(self):
        """Populate dialog fields with current Transition properties."""
        # Get widget references
        
        # Name field (read-only system-assigned identifier)
        name_entry = self.builder.get_object('name_entry')
        if name_entry and hasattr(self.transition_obj, 'name'):
            name_entry.set_text(str(self.transition_obj.name))
            name_entry.set_editable(False)  # Read-only
        
        # Label field (optional user-editable text)
        label_entry = self.builder.get_object('transition_label_entry')
        if label_entry and hasattr(self.transition_obj, 'label'):
            label_entry.set_text(str(self.transition_obj.label) if self.transition_obj.label else '')
        
        # Transition type combo box
        type_combo = self.builder.get_object('prop_transition_type_combo')
        if type_combo and hasattr(self.transition_obj, 'transition_type'):
            transition_type = self.transition_obj.transition_type if self.transition_obj.transition_type else 'immediate'
            # Map type to combo index: immediate=0, timed=1, stochastic=2, continuous=3
            type_map = {'immediate': 0, 'timed': 1, 'stochastic': 2, 'continuous': 3}
            index = type_map.get(transition_type, 0)  # Default to immediate
            type_combo.set_active(index)
        
        # Priority spin button
        priority_spin = self.builder.get_object('priority_spin')
        if priority_spin and hasattr(self.transition_obj, 'priority'):
            priority_spin.set_value(float(self.transition_obj.priority))
        
        # Rate entry (simple numeric/expression field)
        rate_entry = self.builder.get_object('rate_entry')
        if rate_entry and hasattr(self.transition_obj, 'rate'):
            rate_text = self._format_formula_for_display(self.transition_obj.rate)
            rate_entry.set_text(rate_text)
        
        # Guard function (TextView) - format as JSON if dict
        guard_textview = self.builder.get_object('guard_textview')
        if guard_textview and hasattr(self.transition_obj, 'guard'):
            buffer = guard_textview.get_buffer()
            guard_text = self._format_formula_for_display(self.transition_obj.guard)
            buffer.set_text(guard_text)
        
        # Rate function (TextView) - format as JSON if dict
        rate_textview = self.builder.get_object('rate_textview')
        if rate_textview and hasattr(self.transition_obj, 'rate'):
            buffer = rate_textview.get_buffer()
            rate_text = self._format_formula_for_display(self.transition_obj.rate)
            buffer.set_text(rate_text)
    
    def _on_response(self, dialog, response_id):
        """Handle dialog response (OK/Cancel).
        
        Args:
            dialog: The dialog widget.
            response_id: Response ID (OK, Cancel, etc.)
        """
        if response_id == Gtk.ResponseType.OK:
            self._apply_changes()
            
            # Mark document as dirty if persistency manager is available
            if self.persistency_manager:
                self.persistency_manager.mark_dirty()
                print(f"[TransitionPropDialogLoader] Document marked as dirty")
            
            # Emit signal to notify observers (for canvas redraw)
            self.emit('properties-changed')
        
        dialog.destroy()
    
    def _apply_changes(self):
        """Apply changes from dialog fields to Transition object."""
        # Name field is read-only (immutable), so we skip it
        
        # Label field (optional user-editable text)
        label_entry = self.builder.get_object('transition_label_entry')
        if label_entry and hasattr(self.transition_obj, 'label'):
            new_label = label_entry.get_text().strip()
            self.transition_obj.label = new_label if new_label else None
        
        # Transition type combo box
        type_combo = self.builder.get_object('prop_transition_type_combo')
        if type_combo and hasattr(self.transition_obj, 'transition_type'):
            type_index = type_combo.get_active()
            # Map index to type: 0=immediate, 1=timed, 2=stochastic, 3=continuous
            type_list = ['immediate', 'timed', 'stochastic', 'continuous']
            if 0 <= type_index < len(type_list):
                old_type = self.transition_obj.transition_type
                self.transition_obj.transition_type = type_list[type_index]
                print(f"[TransitionPropDialogLoader] Type changed: {old_type} -> {self.transition_obj.transition_type}")
        
        # Priority spin button
        priority_spin = self.builder.get_object('priority_spin')
        if priority_spin and hasattr(self.transition_obj, 'priority'):
            old_priority = self.transition_obj.priority
            self.transition_obj.priority = int(priority_spin.get_value())
            print(f"[TransitionPropDialogLoader] Priority changed: {old_priority} -> {self.transition_obj.priority}")
        
        # Rate entry (simple value - takes precedence over rate_textview if both exist)
        rate_entry = self.builder.get_object('rate_entry')
        if rate_entry and hasattr(self.transition_obj, 'rate'):
            rate_text = rate_entry.get_text().strip()
            if rate_text:  # Only update if entry has content
                old_rate = self.transition_obj.rate
                self.transition_obj.rate = self._parse_formula(rate_text)
                print(f"[TransitionPropDialogLoader] Rate changed (from entry): {old_rate} -> {self.transition_obj.rate}")
        
        # Guard function (TextView) - parse with formula parser
        guard_textview = self.builder.get_object('guard_textview')
        if guard_textview and hasattr(self.transition_obj, 'guard'):
            buffer = guard_textview.get_buffer()
            start, end = buffer.get_bounds()
            guard_text = buffer.get_text(start, end, True)
            old_guard = self.transition_obj.guard
            self.transition_obj.guard = self._parse_formula(guard_text)
            print(f"[TransitionPropDialogLoader] Guard changed: {old_guard} -> {self.transition_obj.guard}")
        
        # Rate function (TextView) - parse with formula parser (only if rate_entry is empty)
        rate_textview = self.builder.get_object('rate_textview')
        rate_entry = self.builder.get_object('rate_entry')
        # Only use TextView if entry doesn't have content
        if rate_textview and hasattr(self.transition_obj, 'rate'):
            rate_entry_text = rate_entry.get_text().strip() if rate_entry else ""
            if not rate_entry_text:  # Entry is empty, use TextView
                buffer = rate_textview.get_buffer()
                start, end = buffer.get_bounds()
                rate_text = buffer.get_text(start, end, True)
                old_rate = self.transition_obj.rate
                self.transition_obj.rate = self._parse_formula(rate_text)
                print(f"[TransitionPropDialogLoader] Rate changed (from textview): {old_rate} -> {self.transition_obj.rate}")
        
        # Color from color picker
        if self.color_picker and hasattr(self.transition_obj, 'border_color'):
            old_color = self.transition_obj.border_color
            selected_color = self.color_picker.get_selected_color()
            self.transition_obj.border_color = selected_color
            print(f"[TransitionPropDialogLoader] Border color changed: {old_color} -> {self.transition_obj.border_color}")
        
        # Also update fill_color to match border_color for consistency
        if self.color_picker and hasattr(self.transition_obj, 'fill_color'):
            self.transition_obj.fill_color = self.transition_obj.border_color
            print(f"[TransitionPropDialogLoader] Fill color updated to match border: {self.transition_obj.fill_color}")
        
        print(f"[TransitionPropDialogLoader] Applied changes to Transition: {self.transition_obj.name}")
    
    def run(self):
        """Show the dialog and run it modally.
        
        Returns:
            Response ID from the dialog.
        """
        return self.dialog.run()
    
    def get_dialog(self):
        """Get the dialog widget.
        
        Returns:
            Gtk.Dialog: The dialog widget.
        """
        return self.dialog


# Factory function for convenience
def create_transition_prop_dialog(transition_obj, parent_window=None, ui_dir: str = None, persistency_manager=None):
    """Factory function to create a Transition properties dialog loader.
    
    Args:
        transition_obj: Transition object to edit properties for.
        parent_window: Parent window for modal dialog.
        ui_dir: Directory containing UI files. Defaults to project ui/dialogs/.
        persistency_manager: NetObjPersistency instance for marking document dirty
    
    Returns:
        TransitionPropDialogLoader: Configured dialog loader instance.
    """
    return TransitionPropDialogLoader(transition_obj, parent_window=parent_window, ui_dir=ui_dir, persistency_manager=persistency_manager)
