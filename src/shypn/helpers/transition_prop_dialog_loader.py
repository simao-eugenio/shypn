"""
Transition Properties Dialog Loader

Loads and manages the Transition properties dialog UI.
Follows project pattern: thin loader with business logic in data layer.
"""
import os
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
from shypn.helpers.color_picker import setup_color_picker_in_dialog
from shypn.data.validation import ExpressionValidator


class TransitionPropDialogLoader(GObject.GObject):
    """Loader for Transition properties dialog.
    
    This class loads and manages the Transition properties dialog UI from
    transition_prop_dialog.ui. The dialog allows editing Transition attributes
    with context-sensitive fields based on transition type.
    
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
            ui_dir: Directory containing UI files. Defaults to project ui/dialogs/
            persistency_manager: NetObjPersistency instance for marking document dirty
            model: ModelCanvasManager instance for accessing Petri net structure
            data_collector: Optional SimulationDataCollector for runtime diagnostics
        """
        super().__init__()
        
        # Resolve UI path (same pattern as place_prop_dialog_loader)
        if ui_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            ui_dir = os.path.join(project_root, 'ui', 'dialogs')
        
        self.ui_dir = ui_dir
        self.ui_path = os.path.join(ui_dir, 'transition_prop_dialog.ui')
        self.transition_obj = transition_obj
        self.parent_window = parent_window
        self.persistency_manager = persistency_manager
        self.model = model
        self.data_collector = data_collector
        
        # Widget references
        self.builder = None
        self.dialog = None
        self.color_picker = None
        self.locality_widget = None
        self.topology_loader = None
        
        # Load and setup
        self._load_ui()
        self._setup_color_picker()
        self._populate_fields()
        self._update_field_visibility()
        self._setup_type_change_handler()
        self._setup_rate_sync()
        self._setup_topology_tab()
    
    def _load_ui(self):
        """Load the Transition properties dialog UI from file."""
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(
                f"Transition properties dialog UI file not found: {self.ui_path}"
            )
        
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        self.dialog = self.builder.get_object('transition_properties_dialog')
        
        if self.dialog is None:
            raise ValueError(
                "Object 'transition_properties_dialog' not found in transition_prop_dialog.ui"
            )
        
        # WAYLAND FIX: Always set parent (explicitly None if not available)
        # This must be done immediately after getting the dialog from builder
        parent = self.parent_window if self.parent_window else None
        if parent:
            self.dialog.set_transient_for(parent)
        
        self.dialog.connect('response', self._on_response)
    
    def _setup_color_picker(self):
        """Setup and insert the color picker widget into the dialog."""
        current_color = getattr(self.transition_obj, 'border_color', (0.0, 0.0, 0.0))
        
        self.color_picker = setup_color_picker_in_dialog(
            self.builder,
            'transition_color_picker',
            current_color=current_color,
            button_size=28
        )
        
        if self.color_picker:
            self.color_picker.connect('color-selected', self._on_color_selected)
    
    def _on_color_selected(self, picker, color_rgb):
        """Handle color selection from picker.
        
        Args:
            picker: ColorPickerRow widget
            color_rgb: Selected RGB tuple (0.0-1.0)
        """
        pass  # Color applied on OK
    
    def _populate_fields(self):
        """Populate dialog fields with current Transition properties."""
        # Name (read-only system identifier)
        name_entry = self.builder.get_object('name_entry')
        if name_entry and hasattr(self.transition_obj, 'name'):
            name_entry.set_text(str(self.transition_obj.name))
            name_entry.set_editable(False)
            name_entry.set_can_focus(False)
        
        # Label (user-editable)
        label_entry = self.builder.get_object('transition_label_entry')
        if label_entry and hasattr(self.transition_obj, 'label'):
            label_entry.set_text(
                str(self.transition_obj.label) if self.transition_obj.label else ''
            )
        
        # Transition type
        type_combo = self.builder.get_object('prop_transition_type_combo')
        if type_combo and hasattr(self.transition_obj, 'transition_type'):
            type_map = {'immediate': 0, 'timed': 1, 'stochastic': 2, 'continuous': 3}
            transition_type = self.transition_obj.transition_type or 'continuous'
            type_combo.set_active(type_map.get(transition_type, 3))
        
        # Priority
        priority_spin = self.builder.get_object('priority_spin')
        if priority_spin and hasattr(self.transition_obj, 'priority'):
            priority_spin.set_value(float(self.transition_obj.priority))
        
        # Firing policy
        firing_policy_combo = self.builder.get_object('firing_policy_combo')
        if firing_policy_combo and hasattr(self.transition_obj, 'firing_policy'):
            policy_map = {'earliest': 0, 'latest': 1}
            policy = self.transition_obj.firing_policy or 'earliest'
            firing_policy_combo.set_active(policy_map.get(policy, 0))
        
        # Source/Sink checkboxes
        is_source_check = self.builder.get_object('is_source_check')
        if is_source_check and hasattr(self.transition_obj, 'is_source'):
            is_source_check.set_active(self.transition_obj.is_source)
        
        is_sink_check = self.builder.get_object('is_sink_check')
        if is_sink_check and hasattr(self.transition_obj, 'is_sink'):
            is_sink_check.set_active(self.transition_obj.is_sink)
        
        # Rate (simple entry)
        rate_entry = self.builder.get_object('rate_entry')
        if rate_entry and hasattr(self.transition_obj, 'rate'):
            rate_value = self.transition_obj.rate
            if rate_value is not None:
                rate_entry.set_text(str(rate_value))
        
        # Guard function (TextView)
        guard_textview = self.builder.get_object('guard_textview')
        if guard_textview and hasattr(self.transition_obj, 'guard'):
            buffer = guard_textview.get_buffer()
            guard_value = self.transition_obj.guard
            if guard_value is not None:
                buffer.set_text(str(guard_value))
        
        # Rate function (TextView)
        rate_textview = self.builder.get_object('rate_textview')
        if rate_textview and hasattr(self.transition_obj, 'rate'):
            buffer = rate_textview.get_buffer()
            rate_value = self.transition_obj.rate
            if rate_value is not None:
                buffer.set_text(str(rate_value))
        
        # Line Width
        width_entry = self.builder.get_object('prop_transition_width_entry')
        if width_entry and hasattr(self.transition_obj, 'border_width'):
            width_entry.set_text(str(self.transition_obj.border_width))
        
        # Update type description
        self._update_type_description()
    
    def _update_field_visibility(self):
        """Update field visibility based on transition type.
        
        Delegates to transition object for business logic.
        """
        editable_fields = self.transition_obj.get_editable_fields()
        
        # Show/hide rate entry
        rate_entry = self.builder.get_object('rate_entry')
        if rate_entry:
            rate_entry.set_visible(editable_fields.get('rate', True))
        
        # Show/hide rate function (multi-line)
        rate_textview = self.builder.get_object('rate_textview')
        if rate_textview:
            parent = rate_textview.get_parent()
            if parent:
                parent.set_visible(editable_fields.get('rate_function', True))
        
        # Show/hide firing policy
        firing_policy_combo = self.builder.get_object('firing_policy_combo')
        if firing_policy_combo:
            parent = firing_policy_combo.get_parent()
            if parent:
                parent.set_visible(editable_fields.get('firing_policy', True))
    
    def _update_type_description(self):
        """Update type description label based on current type."""
        desc_label = self.builder.get_object('type_description_label')
        if desc_label:
            description = self.transition_obj.get_type_description()
            desc_label.set_text(description)
    
    def _setup_type_change_handler(self):
        """Setup handler for transition type changes."""
        type_combo = self.builder.get_object('prop_transition_type_combo')
        if type_combo:
            type_combo.connect('changed', self._on_type_changed)
    
    def _on_type_changed(self, combo):
        """Handle transition type change - update field visibility."""
        type_list = ['immediate', 'timed', 'stochastic', 'continuous']
        new_type = type_list[combo.get_active()]
        
        # Update transition object temporarily (not persisted until OK)
        self.transition_obj.transition_type = new_type
        
        # Update UI
        self._update_field_visibility()
        self._update_type_description()
    
    def _setup_rate_sync(self):
        """Setup synchronization between rate function TextView and rate entry."""
        rate_textview = self.builder.get_object('rate_textview')
        rate_entry = self.builder.get_object('rate_entry')
        
        if rate_textview and rate_entry:
            buffer = rate_textview.get_buffer()
            buffer.connect('changed', lambda buf: self._sync_rate_to_entry(buf, rate_entry))
    
    def _sync_rate_to_entry(self, buffer, rate_entry):
        """Sync rate function TextView to rate entry with preview.
        
        Shows expression preview or simplified value in the entry field.
        """
        start, end = buffer.get_bounds()
        text = buffer.get_text(start, end, True).strip()
        
        if not text:
            rate_entry.set_text('')
            return
        
        # Validate expression
        is_valid, error_msg, parsed = ExpressionValidator.validate_expression(text)
        
        if not is_valid:
            # Show error in entry
            rate_entry.set_text(f'[Error] {error_msg[:30]}...')
            return
        
        # If it's a simple number, show it directly
        if isinstance(parsed, (int, float)):
            rate_entry.set_text(str(parsed))
        else:
            # Show expression indicator
            rate_entry.set_text(f'[Expression] {text[:20]}...')
    
    def _on_response(self, dialog, response_id):
        """Handle dialog response (OK/Cancel).
        
        Args:
            dialog: The dialog widget
            response_id: Response ID (OK, Cancel, etc.)
        """
        if response_id == Gtk.ResponseType.OK:
            if self._apply_changes():
                if self.persistency_manager:
                    self.persistency_manager.mark_dirty()
                self.emit('properties-changed')
        
        # Don't destroy here - let explicit destroy() method handle it
    
    def _apply_changes(self):
        """Apply changes from dialog fields to Transition object.
        
        Returns:
            bool: True if successful, False if validation failed
        """
        try:
            # Label
            label_entry = self.builder.get_object('transition_label_entry')
            if label_entry:
                new_label = label_entry.get_text().strip()
                self.transition_obj.label = new_label if new_label else None
            
            # Transition type
            type_combo = self.builder.get_object('prop_transition_type_combo')
            if type_combo:
                type_list = ['immediate', 'timed', 'stochastic', 'continuous']
                self.transition_obj.transition_type = type_list[type_combo.get_active()]
            
            # Priority
            priority_spin = self.builder.get_object('priority_spin')
            if priority_spin:
                self.transition_obj.priority = int(priority_spin.get_value())
            
            # Firing policy
            firing_policy_combo = self.builder.get_object('firing_policy_combo')
            if firing_policy_combo:
                policy_list = ['earliest', 'latest']
                policy_index = firing_policy_combo.get_active()
                if policy_index >= 0:
                    self.transition_obj.firing_policy = policy_list[policy_index]
            
            # Source/Sink
            is_source_check = self.builder.get_object('is_source_check')
            if is_source_check:
                self.transition_obj.is_source = is_source_check.get_active()
            
            is_sink_check = self.builder.get_object('is_sink_check')
            if is_sink_check:
                self.transition_obj.is_sink = is_sink_check.get_active()
            
            # Rate - let object validate
            rate_textview = self.builder.get_object('rate_textview')
            if rate_textview:
                buffer = rate_textview.get_buffer()
                start, end = buffer.get_bounds()
                rate_text = buffer.get_text(start, end, True).strip()
                
                # Use object's validation method
                self.transition_obj.set_rate(rate_text if rate_text else None)
            
            # Guard - let object handle it
            guard_textview = self.builder.get_object('guard_textview')
            if guard_textview:
                buffer = guard_textview.get_buffer()
                start, end = buffer.get_bounds()
                guard_text = buffer.get_text(start, end, True).strip()
                
                self.transition_obj.set_guard(guard_text if guard_text else None)
            
            # Color from picker
            if self.color_picker:
                selected_color = self.color_picker.get_selected_color()
                self.transition_obj.border_color = selected_color
                self.transition_obj.fill_color = selected_color
            
            # Line Width
            width_entry = self.builder.get_object('prop_transition_width_entry')
            if width_entry and hasattr(self.transition_obj, 'border_width'):
                try:
                    width_text = width_entry.get_text().strip()
                    if width_text:
                        width_value = float(width_text)
                        self.transition_obj.border_width = max(0.5, width_value)
                except ValueError:
                    pass  # Keep current value if invalid
            
            return True
            
        except ValueError as e:
            # Show error dialog
            error_dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Validation Error"
            )
            error_dialog.format_secondary_text(str(e))
            error_dialog.run()
            error_dialog.destroy()
            return False
    
    def run(self):
        """Show the dialog and run it modally.
        
        Returns:
            Response ID from the dialog
        """
        # WAYLAND FIX: Explicitly show dialog before run() to prevent protocol errors
        # Critical for imported canvases where widget hierarchy is established asynchronously
        # Default canvas works because it's realized when main window shows
        # Imported canvases are created programmatically and dialogs may open before fully ready
        self.dialog.show()
        return self.dialog.run()
    
    def get_dialog(self):
        """Get the dialog widget.
        
        Returns:
            Gtk.Dialog: The dialog widget
        """
        return self.dialog
    
    def _setup_topology_tab(self):
        """Setup topology information tab using TransitionTopologyTabLoader.
        
        Loads the topology tab from XML and populates it with analysis
        for this transition (if model is available).
        """
        # Skip if no model available
        if not self.model:
            return
        
        try:
            from shypn.ui.topology_tab_loader import TransitionTopologyTabLoader
            
            # Create topology tab loader with parent_window for Wayland compatibility
            self.topology_loader = TransitionTopologyTabLoader(
                model=self.model,
                element_id=self.transition_obj.id,
                parent_window=self.parent_window  # Pass parent for dialog creation
            )
            
            # NOTE: Do NOT call populate() here - it can hang on large models!
            # CycleAnalyzer uses nx.simple_cycles() which has exponential complexity.
            # For complex models (e.g., Glycolysis with 60 nodes), this can freeze
            # the application indefinitely.
            # TODO: Implement lazy loading - populate when user switches to Topology tab
            # self.topology_loader.populate()  # ❌ REMOVED - causes freeze
            
            # Get the topology widget
            topology_widget = self.topology_loader.get_root_widget()
            
            # Get the topology tab container and add the widget
            container = self.builder.get_object('topology_tab_container')
            if container and topology_widget:
                container.pack_start(topology_widget, True, True, 0)
                topology_widget.show_all()
                
                # Show "Click to analyze" message in topology tab
                if hasattr(self.topology_loader, 'cycles_label'):
                    self.topology_loader.cycles_label.set_markup(
                        "<i>Topology analysis available.\n"
                        "Click 'Analyze' button to run analysis.</i>"
                    )
        
        except ImportError as e:
            # Topology module not available - silently skip
            print(f"Topology tab not available: {e}")
        except Exception as e:
            # Any other error - log but don't crash the dialog
            print(f"Error setting up topology tab: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    def destroy(self):
        """Destroy dialog and clean up all widget references.
        
        This ensures proper cleanup to prevent orphaned widgets that can
        cause Wayland focus issues and application crashes.
        """
        # Clean up topology loader first
        if self.topology_loader:
            self.topology_loader.destroy()
            self.topology_loader = None
        
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None
        
        # Clean up widget references to prevent memory leaks
        self.color_picker = None
        self.locality_widget = None
        self.builder = None
        self.transition_obj = None
        self.parent_window = None
        self.persistency_manager = None
        self.model = None
        self.data_collector = None


# Factory function for backward compatibility
def create_transition_prop_dialog(transition_obj, parent_window=None, ui_dir=None,
                                   persistency_manager=None, model=None, data_collector=None):
    """Factory function to create a Transition properties dialog loader.
    
    Args:
        transition_obj: Transition object to edit properties for
        parent_window: Parent window for modal dialog
        ui_dir: Directory containing UI files. Defaults to project ui/dialogs/
        persistency_manager: NetObjPersistency instance for marking document dirty
        model: ModelCanvasManager instance for accessing Petri net structure
        data_collector: Optional SimulationDataCollector for runtime diagnostics
    
    Returns:
        TransitionPropDialogLoader: Configured dialog loader instance
    """
    return TransitionPropDialogLoader(
        transition_obj,
        parent_window=parent_window,
        ui_dir=ui_dir,
        persistency_manager=persistency_manager,
        model=model,
        data_collector=data_collector
    )
