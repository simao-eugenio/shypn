"""
Simulation Settings Dialog

Proper GTK dialog subclass for configuring simulation timing and execution
parameters. Follows OOP principles with separation from loader pattern.

Uses debounced controls and buffered settings for atomic parameter updates.
"""
import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from shypn.engine.simulation.settings import SimulationSettings
from shypn.engine.simulation.buffered import BufferedSimulationSettings
from shypn.engine.simulation.conflict_policy import ConflictResolutionPolicy
from shypn.utils.time_utils import TimeUnits


class SimulationSettingsDialog(Gtk.Dialog):
    """Dialog for configuring simulation settings.
    
    This is a proper GTK Dialog subclass (not a loader pattern). It manages
    its own UI, validation, and interaction with SimulationSettings object.
    
    Uses BufferedSimulationSettings for atomic parameter updates with
    validation and rollback support.
    
    Attributes:
        settings: SimulationSettings instance (live settings)
        buffered_settings: BufferedSimulationSettings for atomic updates
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
        self.set_keep_above(True)  # Ensure dialog stays on top
        
        self.settings = settings
        self._widgets = {}
        
        # Create buffered settings for atomic updates
        self.buffered_settings = BufferedSimulationSettings(settings)
        
        # Load UI from file
        self._load_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Load current settings
        self._load_from_settings()
        
        print("DEBUG: SimulationSettingsDialog __init__ called")
        
        # Manually trigger the initial state update for the entry field
        # This ensures the sensitivity is correctly set on dialog open
        self._update_dt_entry_sensitivity()
    
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
            'conflict_policy_combo': builder.get_object('conflict_policy_combo'),
            # τ-leaping settings
            'tau_leaping_enabled_check': builder.get_object('tau_leaping_enabled_check'),
            'tau_epsilon_entry': builder.get_object('tau_epsilon_entry'),
            'critical_threshold_entry': builder.get_object('critical_threshold_entry'),
            'parallel_stochastic_check': builder.get_object('parallel_stochastic_check')
        }
        
        # Validate all widgets found
        for name, widget in self._widgets.items():
            if widget is None:
                raise ValueError(f"Widget '{name}' not found in UI file")
        
        # Explicitly ensure the manual entry is editable and can receive focus
        entry = self._widgets['dt_manual_entry']
        entry.set_editable(True)
        entry.set_can_focus(True)
        entry.set_property('editable', True)
        
        # Show all widgets
        self.show_all()
    
    def _connect_signals(self):
        """Connect widget signals.
        
        NOTE: Entry widgets could be replaced with DebouncedEntry for real-time
        validation feedback. Current implementation validates on OK click which
        is sufficient for this dialog.
        
        For future enhancement:
            from shypn.ui.controls import DebouncedEntry
            entry = DebouncedEntry(delay_ms=300)
            entry.set_debounced_callback(self._on_value_changed_debounced)
        """
        # Auto dt radio toggle - disable manual entry when auto is selected
        if self._widgets['dt_auto_radio']:
            self._widgets['dt_auto_radio'].connect('toggled', self._on_auto_dt_toggled)
        
        # Manual dt radio toggle - enable manual entry when manual is selected
        if self._widgets['dt_manual_radio']:
            self._widgets['dt_manual_radio'].connect('toggled', self._on_manual_dt_toggled)
    
    def _update_dt_entry_sensitivity(self):
        """Update the manual dt entry sensitivity based on current radio button state."""
        is_manual_active = self._widgets['dt_manual_radio'].get_active()
        entry = self._widgets['dt_manual_entry']
        
        # Debug output
        print(f"DEBUG: Manual radio active: {is_manual_active}")
        print(f"DEBUG: Entry sensitive before: {entry.get_sensitive()}")
        print(f"DEBUG: Entry editable before: {entry.get_editable()}")
        
        entry.set_sensitive(is_manual_active)
        entry.set_editable(True)
        
        print(f"DEBUG: Entry sensitive after: {entry.get_sensitive()}")
        print(f"DEBUG: Entry editable after: {entry.get_editable()}")
        print(f"DEBUG: Entry can-focus: {entry.get_can_focus()}")
    
    def _on_auto_dt_toggled(self, button):
        """Handle auto dt radio toggle.
        
        Args:
            button: GtkRadioButton that was toggled
        """
        print(f"DEBUG _on_auto_dt_toggled: button active = {button.get_active()}")
        # Only act when button becomes active (not when it becomes inactive)
        if button.get_active():
            self._update_dt_entry_sensitivity()
    
    def _on_manual_dt_toggled(self, button):
        """Handle manual dt radio toggle.
        
        Args:
            button: GtkRadioButton that was toggled
        """
        print(f"DEBUG _on_manual_dt_toggled: button active = {button.get_active()}")
        # Only act when button becomes active (not when it becomes inactive)
        if button.get_active():
            self._update_dt_entry_sensitivity()
    
    def _load_from_settings(self):
        """Load current values from settings object."""
        # Time step mode - setting the radio button will trigger the signal handler
        # which will automatically set the entry sensitivity
        if self.settings.dt_auto:
            self._widgets['dt_auto_radio'].set_active(True)
        else:
            self._widgets['dt_manual_radio'].set_active(True)
        
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
        
        # τ-Leaping settings
        self._widgets['tau_leaping_enabled_check'].set_active(self.settings.use_tau_leaping)
        self._widgets['tau_epsilon_entry'].set_text(str(self.settings.tau_epsilon))
        self._widgets['critical_threshold_entry'].set_text(str(self.settings.critical_threshold))
        self._widgets['parallel_stochastic_check'].set_active(self.settings.use_parallel_stochastic)
    
    def apply_to_settings(self) -> bool:
        """Apply dialog values to settings object atomically.
        
        Uses BufferedSimulationSettings for atomic commit with validation.
        All changes succeed together or none are applied.
        
        Returns:
            bool: True if successful, False if validation failed
        """
        try:
            # Update buffered settings (changes not applied yet)
            
            # Time step mode
            dt_auto = self._widgets['dt_auto_radio'].get_active()
            self.buffered_settings.buffer.dt_auto = dt_auto
            
            # Manual dt value
            dt_text = self._widgets['dt_manual_entry'].get_text().strip()
            try:
                dt_value = float(dt_text)
                self.buffered_settings.buffer.dt_manual = dt_value
            except ValueError:
                self._show_error("Invalid time step", 
                               f"Time step must be a positive number. Got: {dt_text}")
                self.buffered_settings.rollback()
                return False
            
            # Time scale
            scale_text = self._widgets['time_scale_entry'].get_text().strip()
            try:
                scale_value = float(scale_text)
                self.buffered_settings.buffer.time_scale = scale_value
            except ValueError:
                self._show_error("Invalid time scale",
                               f"Time scale must be a positive number. Got: {scale_text}")
                self.buffered_settings.rollback()
                return False
            
            # τ-Leaping settings
            use_tau_leaping = self._widgets['tau_leaping_enabled_check'].get_active()
            self.buffered_settings.buffer.use_tau_leaping = use_tau_leaping
            
            # Epsilon
            epsilon_text = self._widgets['tau_epsilon_entry'].get_text().strip()
            try:
                epsilon_value = float(epsilon_text)
                if epsilon_value <= 0 or epsilon_value > 1:
                    self._show_error("Invalid epsilon",
                                   f"Epsilon must be between 0 and 1. Got: {epsilon_value}")
                    self.buffered_settings.rollback()
                    return False
                self.buffered_settings.buffer.tau_epsilon = epsilon_value
            except ValueError:
                self._show_error("Invalid epsilon",
                               f"Epsilon must be a number. Got: {epsilon_text}")
                self.buffered_settings.rollback()
                return False
            
            # Critical threshold
            threshold_text = self._widgets['critical_threshold_entry'].get_text().strip()
            try:
                threshold_value = float(threshold_text)
                if threshold_value < 0:
                    self._show_error("Invalid critical threshold",
                                   f"Critical threshold must be non-negative. Got: {threshold_value}")
                    self.buffered_settings.rollback()
                    return False
                self.buffered_settings.buffer.critical_threshold = threshold_value
            except ValueError:
                self._show_error("Invalid critical threshold",
                               f"Critical threshold must be a number. Got: {threshold_text}")
                self.buffered_settings.rollback()
                return False
            
            # Parallel stochastic
            use_parallel = self._widgets['parallel_stochastic_check'].get_active()
            self.buffered_settings.buffer.use_parallel_stochastic = use_parallel
            
            # Mark as dirty (has uncommitted changes)
            self.buffered_settings.mark_dirty()
            
            # Commit all changes atomically (validated)
            from shypn.engine.simulation.buffered import ValidationError
            try:
                self.buffered_settings.commit()
                return True
            except ValidationError as e:
                self._show_error("Validation Error", str(e))
                self.buffered_settings.rollback()
                return False
            
        except Exception as e:
            self._show_error("Unexpected Error", str(e))
            self.buffered_settings.rollback()
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
        Automatically rolls back buffered changes if cancelled.
        
        Returns:
            bool: True if settings were applied, False if cancelled
        """
        response = self.run()
        
        if response == Gtk.ResponseType.OK:
            success = self.apply_to_settings()
            self.destroy()
            return success
        else:
            # Rollback any uncommitted changes
            self.buffered_settings.rollback()
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
