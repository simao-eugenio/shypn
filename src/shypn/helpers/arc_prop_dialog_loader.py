"""
Arc Properties Dialog Loader

Loads and manages the Arc properties dialog UI.
"""
import os
import json
import ast
import logging
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
from shypn.helpers.color_picker import setup_color_picker_in_dialog
from shypn.utils.arc_transform import is_inhibitor, is_test, is_signal_flow, convert_to_inhibitor, convert_to_normal, convert_to_test, convert_to_signal_flow

logger = logging.getLogger(__name__)

class ArcPropDialogLoader(GObject.GObject):
    """Loader for Arc properties dialog.
    
    This class loads and manages the Arc properties dialog UI from
    arc_prop_dialog.ui. The dialog allows editing Arc attributes
    such as weight, label, and other properties.
    
    Signals:
        properties-changed: Emitted when properties are changed and applied
    """
    __gsignals__ = {'properties-changed': (GObject.SignalFlags.RUN_FIRST, None, ())}

    def __init__(self, arc_obj, parent_window=None, ui_dir: str=None, persistency_manager=None, model=None):
        """Initialize the Arc properties dialog loader.
        
        Args:
            arc_obj: Arc object to edit properties for.
            parent_window: Parent window for modal dialog.
            ui_dir: Directory containing UI files. Defaults to project ui/dialogs/.
            persistency_manager: NetObjPersistency instance for marking document dirty
            model: PetriNetModel instance (optional, for future use)
        """
        super().__init__()
        if ui_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            ui_dir = os.path.join(project_root, 'ui', 'dialogs')
        self.ui_dir = ui_dir
        self.ui_path = os.path.join(ui_dir, 'arc_prop_dialog.ui')
        self.arc_obj = arc_obj
        self.parent_window = parent_window
        self.persistency_manager = persistency_manager
        self.model = model
        self.builder = None
        self.dialog = None
        self.color_picker = None
        self._load_ui()
        self._setup_color_picker()
        self._populate_fields()

    def _load_ui(self):
        """Load the Arc properties dialog UI from file."""
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f'Arc properties dialog UI file not found: {self.ui_path}')
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        self.dialog = self.builder.get_object('arc_properties_dialog')
        if self.dialog is None:
            raise ValueError("Object 'arc_properties_dialog' not found in arc_prop_dialog.ui")
        
        # WAYLAND FIX: Do NOT set transient_for here!
        # On Wayland, parent must be realized/mapped before set_transient_for()
        # We'll set it in run() when parent is guaranteed to be ready
        
        ok_button = self.builder.get_object('ok_button')
        cancel_button = self.builder.get_object('cancel_button')
        if ok_button:
            ok_button.connect('clicked', lambda btn: self.dialog.response(Gtk.ResponseType.OK))
        if cancel_button:
            cancel_button.connect('clicked', lambda btn: self.dialog.response(Gtk.ResponseType.CANCEL))
        self.dialog.connect('response', self._on_response)

    def _setup_color_picker(self):
        """Setup color picker widget for arc color selection."""
        current_color = getattr(self.arc_obj, 'color', (0.0, 0.0, 0.0))
        self.color_picker = setup_color_picker_in_dialog(self.builder, 'arc_color_picker', current_color=current_color, button_size=28)
        if self.color_picker:
            self.color_picker.connect('color-selected', self._on_color_selected)

    def _on_color_selected(self, color_picker, color_rgb):
        """Handle color selection from color picker.
        
        Args:
            color_picker: ColorPickerRow instance
            color_rgb: Selected color as RGB tuple (0.0-1.0)
        """

    def _replace_arc_in_model(self):
        """Replace the old arc with the transformed arc in the model.
        
        This method finds the old arc in the model's arc list and replaces it
        with the new transformed arc object (self.arc_obj).
        """
        # Check if arc has a manager reference
        if hasattr(self.arc_obj, '_manager') and self.arc_obj._manager:
            manager = self.arc_obj._manager
            
            # Use manager's replace_arc method for consistency with context menu path
            # This ensures _manager reference, on_changed callback, and modified flags are set
            if hasattr(manager, 'replace_arc'):
                # Find old arc with same ID
                old_arc = None
                for arc in manager.arcs:
                    if arc.id == self.arc_obj.id and arc is not self.arc_obj:
                        old_arc = arc
                        break
                
                if old_arc:
                    manager.replace_arc(old_arc, self.arc_obj)
            else:
                # Fallback: Direct replacement if replace_arc method not available
                for i, arc in enumerate(manager.arcs):
                    if arc.id == self.arc_obj.id:
                        manager.arcs[i] = self.arc_obj
                        break
            
            # Invalidate ModelAdapter cache if simulation is running
            self._invalidate_simulation_cache(manager)
        
        # Notify that the arc was transformed (for redrawing, etc.)
        if hasattr(self.arc_obj, 'on_changed') and self.arc_obj.on_changed:
            self.arc_obj.on_changed()
    
    def _invalidate_simulation_cache(self, manager):
        """Force simulation reinitialization after arc transformations.
        
        When an arc is converted (e.g., Arc → TestArc), the SubnetSimulator's
        subnet_model still holds references to the OLD arc objects. We must
        force reinitialization so the subnet is rebuilt with new arc instances.
        
        Args:
            manager: ModelCanvasManager instance
        """
        # Try to find active simulation and force reinitialization
        try:
            # Method 1: Check document controller's viability panel (subnet simulator)
            if hasattr(manager, 'document_controller'):
                doc_controller = manager.document_controller
                # Viability panel has simulation controller
                if hasattr(doc_controller, 'viability_panel') and doc_controller.viability_panel:
                    viability_panel = doc_controller.viability_panel
                    if hasattr(viability_panel, 'subnet_simulator') and viability_panel.subnet_simulator:
                        simulator = viability_panel.subnet_simulator
                        # If simulation is initialized, force complete reinitialization
                        # This clears the old subnet and rebuilds with updated arc instances
                        if simulator.is_initialized():
                            # Clear old controller and subnet
                            simulator.controller = None
                            simulator.subnet_model = None
                            # Rebuild subnet with new arc instances from main model
                            simulator.initialize_simulation()
            
            # Method 2: Check overlay_manager's main simulation controller
            if hasattr(manager, 'overlay_manager') and manager.overlay_manager:
                overlay_manager = manager.overlay_manager
                if hasattr(overlay_manager, 'simulation_controller') and overlay_manager.simulation_controller:
                    sim_controller = overlay_manager.simulation_controller
                    # Invalidate ModelAdapter caches to pick up new arc instances
                    if hasattr(sim_controller, 'model_adapter') and sim_controller.model_adapter:
                        sim_controller.model_adapter.invalidate_caches()
                    # Clear behavior cache so behaviors are recreated with new arcs
                    if hasattr(sim_controller, 'behavior_cache'):
                        sim_controller.behavior_cache.clear()
                    # Clear transition states (enablement times, scheduled times)
                    if hasattr(sim_controller, 'transition_states'):
                        sim_controller.transition_states.clear()
        except Exception:
            # Silently ignore if no active simulation found
            logger.debug("Simulation state reset after arc property change failed", exc_info=True)

    def _populate_fields(self):
        """Populate dialog fields with current Arc properties."""
        name_entry = self.builder.get_object('name_entry')
        if name_entry and hasattr(self.arc_obj, 'name'):
            name_entry.set_text(str(self.arc_obj.name))
            # Name is editable - user-created alias
        
        # Populate ID field (read-only)
        id_entry = self.builder.get_object('id_entry')
        if id_entry and hasattr(self.arc_obj, 'id'):
            id_entry.set_text(str(self.arc_obj.id))
        
        # Update color picker to reflect current arc color (CRITICAL for ColorSchemaManager)
        # When arc is transformed, ColorSchemaManager sets semantic colors that must be preserved
        if self.color_picker and hasattr(self.arc_obj, 'color'):
            self.color_picker.set_selected_color(self.arc_obj.color)
        
        description_text = self.builder.get_object('description_text')
        if description_text and hasattr(self.arc_obj, 'label'):
            buffer = description_text.get_buffer()
            label_text = str(self.arc_obj.label) if self.arc_obj.label else ''
            buffer.set_text(label_text)
        weight_entry = self.builder.get_object('prop_arc_weight_entry')
        if weight_entry and hasattr(self.arc_obj, 'weight'):
            weight_entry.set_text(str(self.arc_obj.weight))
        line_width_spin = self.builder.get_object('prop_arc_line_width_spin')
        if line_width_spin and hasattr(self.arc_obj, 'width'):
            line_width_spin.set_value(float(self.arc_obj.width))
        
        # Set arc type combo
        type_combo = self.builder.get_object('prop_arc_type_combo')
        if type_combo:
            # Determine current arc type
            # 0 = Normal, 1 = Inhibitor, 2 = Test, 3 = Signal Flow
            if is_signal_flow(self.arc_obj):
                type_combo.set_active(3)  # Signal Flow
            elif is_test(self.arc_obj):
                type_combo.set_active(2)  # Test
            elif is_inhibitor(self.arc_obj):
                type_combo.set_active(1)  # Inhibitor
            else:
                type_combo.set_active(0)  # Normal
        
        threshold_textview = self.builder.get_object('prop_arc_threshold_entry')
        if threshold_textview and hasattr(self.arc_obj, 'threshold'):
            buffer = threshold_textview.get_buffer()
            threshold_text = self._format_threshold_for_display(self.arc_obj.threshold)
            buffer.set_text(threshold_text)
        source_info = self.builder.get_object('source_info_label')
        target_info = self.builder.get_object('target_info_label')
        if source_info and hasattr(self.arc_obj, 'source'):
            source_name = getattr(self.arc_obj.source, 'name', 'Unknown')
            source_info.set_text(f'Source: {source_name}')
        if target_info and hasattr(self.arc_obj, 'target'):
            target_name = getattr(self.arc_obj.target, 'name', 'Unknown')
            target_info.set_text(f'Target: {target_name}')

    def _format_threshold_for_display(self, threshold):
        """Format threshold value for display in UI TextView.
        
        Args:
            threshold: Can be None, dict, number, or string
        
        Returns:
            String representation for display
        """
        if threshold is None:
            return ''
        elif isinstance(threshold, dict):
            return json.dumps(threshold, indent=2)
        elif isinstance(threshold, (int, float)):
            return str(threshold)
        else:
            return str(threshold)

    def _parse_threshold(self, text):
        """Parse threshold text from UI into appropriate format.
        
        Supports multiple formats:
            pass
        - Empty string → None
        - Number string → numeric value
        - Dictionary string → parsed dict
        - Expression string → kept as string
        
        Args:
            text: Raw text from TextView
        
        Returns:
            Parsed threshold (None, number, dict, or string)
        """
        text = text.strip()
        if not text:
            return None
        try:
            if '.' in text:
                return float(text)
            else:
                return int(text)
        except ValueError:
            pass
        if text.startswith('{') and text.endswith('}'):
            try:
                parsed = ast.literal_eval(text)
                if isinstance(parsed, dict):
                    return parsed
            except (ValueError, SyntaxError) as e:
                pass
        return text

    def _on_response(self, dialog, response_id):
        """Handle dialog response (OK/Cancel).
        
        Args:
            dialog: The dialog widget.
            response_id: Response ID (OK, Cancel, etc.)
        """
        if response_id == Gtk.ResponseType.OK:
            self._apply_changes()
            if self.persistency_manager:
                self.persistency_manager.mark_dirty()
            # IMPORTANT: Signal passes self (loader) so callback can access 
            # self.arc_obj which is updated to new arc after transformations
            self.emit('properties-changed')
        # Don't destroy here - let explicit destroy() method handle it

    def _apply_changes(self):
        """Apply changes from dialog fields to Arc object.
        
        For arc type transformations, we follow the same pattern as context menu:
        1. Check if type needs to change
        2 If yes: transform arc (which creates new arc with correct class and color)
        3. Replace old arc with new arc in model
        4. Done - don't apply other properties (already copied by transformation)
        
        If no type change: apply all property changes directly to existing arc.
        """
        # Check if arc type needs to change FIRST (before applying other properties)
        type_combo = self.builder.get_object('prop_arc_type_combo')
        if type_combo:
            new_type_index = type_combo.get_active()
            # 0 = Normal, 1 = Inhibitor, 2 = Test, 3 = Signal Flow
            current_is_inhibitor = is_inhibitor(self.arc_obj)
            current_is_test = is_test(self.arc_obj)
            current_is_signal_flow = is_signal_flow(self.arc_obj)
            
            # Type transformation needed?
            type_changed = False
            new_arc = None
            
            if new_type_index == 0 and (current_is_inhibitor or current_is_test or current_is_signal_flow):
                # Convert to Normal
                new_arc = convert_to_normal(self.arc_obj)
                type_changed = True
            elif new_type_index == 1 and not current_is_inhibitor:
                # Convert to Inhibitor
                try:
                    new_arc = convert_to_inhibitor(self.arc_obj)
                    type_changed = True
                except ValueError as e:
                    self._show_conversion_error("Cannot convert to Inhibitor Arc", str(e))
                    return
            elif new_type_index == 2 and not current_is_test:
                # Convert to Test
                try:
                    new_arc = convert_to_test(self.arc_obj)
                    type_changed = True
                except ValueError as e:
                    self._show_conversion_error("Cannot convert to Test Arc", 
                        f"{e}\n\nTest arcs model catalysts/enzymes that enable reactions without being consumed. "
                        "They must connect Place → Transition only.")
                    return
            elif new_type_index == 3 and not current_is_signal_flow:
                # Convert to Signal Flow
                try:
                    new_arc = convert_to_signal_flow(self.arc_obj)
                    type_changed = True
                except ValueError as e:
                    self._show_conversion_error("Cannot convert to Signal Flow Arc",
                        f"{e}\n\nSignal flow arcs model dual-role information transfer: "
                        "they consume/produce tokens AND propagate information to the vertical decision hierarchy.")
                    return
            
            # If type changed, replace arc in model and done
            if type_changed and new_arc:
                old_arc = self.arc_obj
                if hasattr(old_arc, '_manager') and old_arc._manager:
                    old_arc._manager.replace_arc(old_arc, new_arc)
                    self._invalidate_simulation_cache(old_arc._manager)
                    # Notify the canvas to redraw the new arc visually
                    if hasattr(new_arc, 'on_changed') and new_arc.on_changed:
                        new_arc.on_changed()

                # CRITICAL FIX: Update dialog's arc reference to point to NEW arc
                # This allows successive transformations (e.g., normal → test → inhibitor)
                # without the dialog operating on stale/removed arc references
                self.arc_obj = new_arc

                # BUG-2 FIX: Do NOT return early.  Fall through so that any other
                # field edits (name, weight, colour, threshold) the user made in the
                # same dialog session are applied to the newly-created arc object.
                # (The previous early-return silently discarded those edits.)
        
        # No type change - apply all property changes to existing arc
        
        # Name
        name_entry = self.builder.get_object('name_entry')
        if name_entry and hasattr(self.arc_obj, 'name'):
            new_name = name_entry.get_text().strip()
            if new_name:
                self.arc_obj.name = new_name
        
        # Label/description
        description_text = self.builder.get_object('description_text')
        if description_text and hasattr(self.arc_obj, 'label'):
            buffer = description_text.get_buffer()
            start, end = buffer.get_bounds()
            label_text = buffer.get_text(start, end, True).strip()
            self.arc_obj.label = label_text if label_text else None
        
        # Weight
        weight_entry = self.builder.get_object('prop_arc_weight_entry')
        if weight_entry and hasattr(self.arc_obj, 'weight'):
            try:
                weight_text = weight_entry.get_text().strip()
                weight_value = float(weight_text) if weight_text else 1.0
                self.arc_obj.weight = max(0.0, weight_value)
            except ValueError:
                pass
        
        # Width
        line_width_spin = self.builder.get_object('prop_arc_line_width_spin')
        if line_width_spin and hasattr(self.arc_obj, 'width'):
            self.arc_obj.width = float(line_width_spin.get_value())
        
        # Color - ONLY apply if not a semantic arc type
        # ColorSchemaManager maintains semantic colors for TestArc (blue) and SignalFlowArc (gray)
        if self.color_picker and hasattr(self.arc_obj, 'color'):
            from shypn.utils.color_schema_manager import ColorSchemaManager
            
            # Skip color application for semantic arc types (preserves ColorSchemaManager colors)
            if not ColorSchemaManager.is_semantic_arc_color(self.arc_obj):
                selected_color = self.color_picker.get_selected_color()
                self.arc_obj.color = selected_color
        
        # Threshold
        threshold_textview = self.builder.get_object('prop_arc_threshold_entry')
        if threshold_textview and hasattr(self.arc_obj, 'threshold'):
            buffer = threshold_textview.get_buffer()
            start, end = buffer.get_bounds()
            threshold_text = buffer.get_text(start, end, True).strip()
            self.arc_obj.threshold = self._parse_threshold(threshold_text)
    
    def _show_conversion_error(self, title, message):
        """Show error dialog for arc conversion failure.
        
        Args:
            title: Dialog title
            message: Error message
        """
        error_dialog = Gtk.MessageDialog(
            transient_for=self.dialog,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        error_dialog.format_secondary_text(message)
        error_dialog.run()
        error_dialog.destroy()

    def run(self):
        """Show the dialog and run it modally.
        
        Returns:
            Response ID from the dialog.
        """
        # WAYLAND FIX: Set transient_for HERE, not in __init__!
        # On Wayland, parent must be realized/mapped before set_transient_for()
        # At run() time, parent is guaranteed to be ready
        if self.parent_window:
            # CRITICAL WAYLAND FIX: Check window state (maximized, fullscreen, etc.)
            # Error 71 occurs when dialogs are opened while window is in transition
            import gi
            gi.require_version('Gdk', '3.0')
            from gi.repository import Gdk
            
            window = self.parent_window.get_window()
            if window:
                state = window.get_state()
                is_maximized = bool(state & Gdk.WindowState.MAXIMIZED)
                is_fullscreen = bool(state & Gdk.WindowState.FULLSCREEN)
                is_tiled = bool(state & Gdk.WindowState.TILED)
                
                # WAYLAND WORKAROUND: If window is maximized/fullscreen/tiled, wait a bit
                # This gives Wayland compositor time to complete the state transition
                if is_maximized or is_fullscreen or is_tiled:
                    import time
                    time.sleep(0.1)  # 100ms delay to let compositor settle
            
            # CRITICAL WAYLAND FIX: Process pending events before set_transient_for()
            # This ensures the Wayland compositor has processed all widget state changes
            display = Gdk.Display.get_default()
            if display:
                display.sync()  # Wait for all requests to be processed
            
            # Now set transient after compositor is synced
            self.dialog.set_transient_for(self.parent_window)
        
        # WAYLAND FIX: Explicitly show dialog before run() to prevent protocol errors
        # Critical for imported canvases where widget hierarchy is established asynchronously
        # Default canvas works because it's realized when main window shows
        # Imported canvases are created programmatically and dialogs may open before fully ready
        self.dialog.show()
        return self.dialog.run()

    def get_dialog(self):
        """Get the dialog widget.
        
        Returns:
            Gtk.Dialog: The dialog widget.
        """
        return self.dialog

    def destroy(self):
        """Destroy dialog and clean up all widget references.
        
        This ensures proper cleanup to prevent orphaned widgets that can
        cause Wayland focus issues and application crashes.
        """
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None
        
        # Clean up widget references to prevent memory leaks
        self.color_picker = None
        self.builder = None
        self.arc_obj = None
        self.parent_window = None
        self.persistency_manager = None

def create_arc_prop_dialog(arc_obj, parent_window=None, ui_dir: str=None, persistency_manager=None, model=None):
    """Factory function to create an Arc properties dialog loader.
    
    Args:
        arc_obj: Arc object to edit properties for.
        parent_window: Parent window for modal dialog.
        ui_dir: Directory containing UI files. Defaults to project ui/dialogs/.
        persistency_manager: NetObjPersistency instance for marking document dirty
        model: PetriNetModel instance (optional, for future use)
    
    Returns:
        ArcPropDialogLoader: Configured dialog loader instance.
    """
    return ArcPropDialogLoader(arc_obj, parent_window=parent_window, ui_dir=ui_dir, 
                               persistency_manager=persistency_manager, model=model)