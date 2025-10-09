"""
Simulation Settings Dialog

Proper GTK dialog subclass for configuring simulation timing and execution
parameters. Follows OOP principles with separation from loader pattern.
"""
import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from shypn.engine.simulation.settings import SimulationSettings
from shypn.engine.simulation.conflict_policy import ConflictResolutionPolicy
from shypn.utils.time_utils import TimeUnits


class SimulationSettingsDialog(Gtk.Dialog):
    """Dialog for configuring simulation settings.
    
    This is a proper GTK Dialog subclass (not a loader pattern). It manages
    its own UI, validation, and interaction with SimulationSettings object.
    
    Attributes:
        settings: SimulationSettings instance to configure
        _widgets: Dictionary of UI widgets
    
    Example:
        dialog = SimulationSettingsDialog(controller.settings, parent_window)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            dialog.apply_to_settings()
        dialog.destroy()
    """
    
    def __init__(self, settings: SimulationSettings, parent: Gtk.Window = None):
        """Initialize the settings dialog.
        
        Args:
            settings: SimulationSettings instance to configure
            parent: Parent window for modal dialog (optional)
        """
        super().__init__(
            title="Simulation Settings",
            parent=parent,
            modal=True,
            destroy_with_parent=True
        )
        
        self.settings = settings
        self._widgets = {}
        
        # Load UI from file
        self._load_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Load current settings
        self._load_from_settings()
    
    def _load_ui(self):
        """Load UI definition from file."""
        # Find UI file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        ui_path = os.path.join(project_root, 'ui', 'dialogs', 'simulation_settings.ui')
        
        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"UI file not found: {ui_path}")
        
        # Load UI
        builder = Gtk.Builder()
        builder.add_from_file(ui_path)
        
        # Get dialog object
        dialog_obj = builder.get_object('simulation_settings_dialog')
        if dialog_obj is None:
            raise ValueError("Dialog object 'simulation_settings_dialog' not found in UI file")
        
        # Extract content and buttons
        content_area = self.get_content_area()
        dialog_content = builder.get_object('dialog_content')
        
        # Reparent content
        if dialog_content:
            parent = dialog_content.get_parent()
            if parent:
                parent.remove(dialog_content)
            content_area.pack_start(dialog_content, True, True, 0)
        
        # Get action buttons
        cancel_button = builder.get_object('cancel_button')
        ok_button = builder.get_object('ok_button')
        
        if cancel_button and ok_button:
            action_area = self.get_action_area()
            
            # Remove from builder parent
            for button in [cancel_button, ok_button]:
                parent = button.get_parent()
                if parent:
                    parent.remove(button)
            
            # Add to dialog action area
            action_area.pack_start(cancel_button, False, False, 0)
            action_area.pack_start(ok_button, False, False, 0)
            
            # Set response IDs
            self.add_action_widget(cancel_button, Gtk.ResponseType.CANCEL)
            self.add_action_widget(ok_button, Gtk.ResponseType.OK)
            ok_button.set_can_default(True)
            ok_button.grab_default()
        
        # Store widget references
        self._widgets = {
            'dt_auto_radio': builder.get_object('dt_auto_radio'),
            'dt_manual_radio': builder.get_object('dt_manual_radio'),
            'dt_manual_entry': builder.get_object('dt_manual_entry'),
            'time_scale_entry': builder.get_object('time_scale_entry'),
            'conflict_policy_combo': builder.get_object('conflict_policy_combo')
        }
        
        # Validate all widgets found
        for name, widget in self._widgets.items():
            if widget is None:
                raise ValueError(f"Widget '{name}' not found in UI file")
    
    def _connect_signals(self):
        """Connect widget signals."""
        # Manual dt radio toggle
        if self._widgets['dt_manual_radio']:
            self._widgets['dt_manual_radio'].connect('toggled', self._on_manual_dt_toggled)
    
    def _on_manual_dt_toggled(self, button):
        """Handle manual dt radio toggle.
        
        Args:
            button: GtkRadioButton that was toggled
        """
        is_manual = button.get_active()
        if self._widgets['dt_manual_entry']:
            self._widgets['dt_manual_entry'].set_sensitive(is_manual)
    
    def _load_from_settings(self):
        """Load current values from settings object."""
        # Time step mode
        if self.settings.dt_auto:
            self._widgets['dt_auto_radio'].set_active(True)
            self._widgets['dt_manual_entry'].set_sensitive(False)
        else:
            self._widgets['dt_manual_radio'].set_active(True)
            self._widgets['dt_manual_entry'].set_sensitive(True)
        
        # Manual dt value
        self._widgets['dt_manual_entry'].set_text(str(self.settings.dt_manual))
        
        # Time scale
        self._widgets['time_scale_entry'].set_text(str(self.settings.time_scale))
        
        # Conflict policy
        policy_map = {
            ConflictResolutionPolicy.RANDOM: 0,
            ConflictResolutionPolicy.PRIORITY: 1,
            ConflictResolutionPolicy.ROUND_ROBIN: 2
        }
        
        # Get current policy from settings' parent controller if available
        # For now, default to RANDOM (index 0)
        index = 0  # Default to Random
        self._widgets['conflict_policy_combo'].set_active(index)
    
    def apply_to_settings(self) -> bool:
        """Apply dialog values to settings object.
        
        Returns:
            bool: True if successful, False if validation failed
        """
        try:
            # Time step mode
            self.settings.dt_auto = self._widgets['dt_auto_radio'].get_active()
            
            # Manual dt value
            dt_text = self._widgets['dt_manual_entry'].get_text()
            try:
                dt_value = float(dt_text)
                self.settings.dt_manual = dt_value
            except ValueError:
                self._show_error("Invalid time step", 
                               f"Time step must be a positive number. Got: {dt_text}")
                return False
            
            # Time scale
            scale_text = self._widgets['time_scale_entry'].get_text()
            try:
                scale_value = float(scale_text)
                self.settings.time_scale = scale_value
            except ValueError:
                self._show_error("Invalid time scale",
                               f"Time scale must be a positive number. Got: {scale_text}")
                return False
            
            return True
            
        except ValueError as e:
            self._show_error("Validation Error", str(e))
            return False
    
    def get_conflict_policy(self) -> ConflictResolutionPolicy:
        """Get selected conflict resolution policy.
        
        Returns:
            ConflictResolutionPolicy: Selected policy enum value
        """
        index = self._widgets['conflict_policy_combo'].get_active()
        policy_map = [
            ConflictResolutionPolicy.RANDOM,
            ConflictResolutionPolicy.PRIORITY,
            ConflictResolutionPolicy.ROUND_ROBIN
        ]
        
        if 0 <= index < len(policy_map):
            return policy_map[index]
        else:
            return ConflictResolutionPolicy.RANDOM  # Default
    
    def _show_error(self, title: str, message: str):
        """Show error dialog.
        
        Args:
            title: Error dialog title
            message: Error message
        """
        error_dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        error_dialog.format_secondary_text(message)
        error_dialog.run()
        error_dialog.destroy()
    
    def run_and_apply(self) -> bool:
        """Run dialog and apply settings if OK clicked.
        
        Convenience method that combines run(), apply_to_settings(), and destroy().
        
        Returns:
            bool: True if settings were applied, False if cancelled
        """
        response = self.run()
        
        if response == Gtk.ResponseType.OK:
            success = self.apply_to_settings()
            self.destroy()
            return success
        else:
            self.destroy()
            return False


# Convenience function for quick dialog usage
def show_simulation_settings_dialog(settings: SimulationSettings, 
                                    parent: Gtk.Window = None) -> bool:
    """Show simulation settings dialog (convenience function).
    
    Args:
        settings: SimulationSettings instance to configure
        parent: Parent window for modal dialog
    
    Returns:
        bool: True if settings were changed, False if cancelled
    """
    dialog = SimulationSettingsDialog(settings, parent)
    return dialog.run_and_apply()
