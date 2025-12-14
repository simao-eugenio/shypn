"""
Simulate Tools Palette Loader

Loads and manages the simulation tools palette UI (Run, Step, Stop, Reset, Settings buttons).
This palette appears below the main [S] simulate button when toggled.

PHASE 2 REFACTOR: Constant Height Architecture
===============================================
The loader now returns ONLY the tool buttons container (50px max height) via get_widget().
The settings panel is separated and available via create_settings_panel() factory method.

ARCHITECTURE:
- get_widget() → Returns simulate_tools_container ONLY (buttons: R, P, S, T, ⚙)
- create_settings_panel() → Returns settings_revealer (for Phase 3 parameter panel)

This separation allows:
1. Main palette maintains constant 50px height (no more jumps!)
2. Settings panel can be managed by universal parameter panel manager (Phase 3)
3. Consistent height across all sub-palettes (Edit, Simulate, Layout)

The palette directly manages the SimulationController - buttons call controller
methods directly rather than emitting signals for external handling.
"""
import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject, GLib
from shypn.engine.simulation import SimulationController
from shypn.engine.simulation.buffered import BufferedSimulationSettings
from shypn.analyses import SimulationDataCollector
from shypn.utils.time_utils import TimeUnits, TimeFormatter

class SimulateToolsPaletteLoader(GObject.GObject):
    """Loader for simulation tools palette - manages [R][P][S][T][⚙] button panel.
    
    This class loads and manages the simulation tools palette UI from
    simulate_tools_palette.ui. The palette contains five buttons:
    - Run [R]: Start continuous simulation execution
    - Step [P]: Execute one simulation step
    - Stop [S]: Pause simulation
    - Reset [T]: Reset to initial marking
    - Settings [⚙]: Open simulation settings dialog
    
    Plus duration controls, progress bar, and time display.
    
    The palette directly owns and operates the SimulationController.
    Buttons call controller methods directly (no external wiring needed).
    
    The palette is revealed/hidden by the main simulate button via show()/hide().
    
    Signals:
        step-executed(float): Emitted after each simulation step with current time
        reset-executed(): Emitted after simulation reset
        settings-changed(): Emitted when simulation settings are modified (duration, units, etc.)
        settings-toggle-requested(): PHASE 3 - Emitted when settings button clicked (for parameter panel)
    """
    __gsignals__ = {
        'step-executed': (GObject.SignalFlags.RUN_FIRST, None, (float,)),
        'reset-executed': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'settings-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'settings-toggle-requested': (GObject.SignalFlags.RUN_FIRST, None, ()),  # PHASE 3
    }

    def __init__(self, model=None, ui_dir: str=None):
        """Initialize the simulate tools palette loader.
        
        Args:
            model: PetriNetModel instance for simulation (can be set later)
            ui_dir: Directory containing UI files. Defaults to project ui/simulate/.
        """
        super().__init__()
        if ui_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            ui_dir = os.path.join(project_root, 'ui', 'simulate')
        self.ui_dir = ui_dir
        self.ui_path = os.path.join(ui_dir, 'simulate_tools_palette.ui')
        self._simulation = None  # Private attribute - use property
        self.buffered_settings = None
        self._model = model
        self.data_collector = SimulationDataCollector()
        self.builder = None
        self.simulate_tools_revealer = None
        self.simulate_tools_container = None
        self.run_button = None
        self.step_button = None
        self.stop_button = None
        self.reset_button = None
        self.settings_button = None
        self.duration_entry = None
        self.time_units_combo = None
        self.progress_bar = None
        self.time_display_label = None
        self._load_ui()
        
        # Initialize simulation controller AFTER UI is loaded
        if model is not None:
            self._init_simulation_controller()

    @property
    def simulation(self):
        """Get the simulation controller.
        
        Returns:
            SimulationController or None
        """
        return self._simulation
    
    @simulation.setter
    def simulation(self, controller):
        """Set the simulation controller.
        
        CRITICAL: When controller changes (e.g., lifecycle reset), we must
        recreate BufferedSimulationSettings to point to the NEW controller's
        settings object. Otherwise buffered settings point to stale/orphaned
        settings from the previous controller!
        
        Args:
            controller: SimulationController instance or None
        """
        self._simulation = controller
        
        # Recreate BufferedSimulationSettings with new controller's settings
        if controller is not None:
            # Create new BufferedSimulationSettings pointing to new controller's settings
            self.buffered_settings = BufferedSimulationSettings(controller.settings)
            
            # Sync UI with new controller's settings
            self._sync_settings_to_ui()
        else:
            self.buffered_settings = None

    def _load_ui(self):
        """Load the simulate tools palette UI from file."""
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f'Simulate tools palette UI file not found: {self.ui_path}')
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        self.simulate_tools_revealer = self.builder.get_object('simulate_tools_revealer')
        self.simulate_tools_container = self.builder.get_object('simulate_tools_container')
        self.run_button = self.builder.get_object('run_simulation_button')
        self.step_button = self.builder.get_object('step_simulation_button')
        self.stop_button = self.builder.get_object('stop_simulation_button')
        self.reset_button = self.builder.get_object('reset_simulation_button')
        self.settings_button = self.builder.get_object('settings_simulation_button')
        self.duration_entry = self.builder.get_object('duration_entry')
        self.time_units_combo = self.builder.get_object('time_units_combo')
        self.progress_bar = self.builder.get_object('simulation_progress_bar')
        self.time_display_label = self.builder.get_object('time_display_label')
        
        if self.simulate_tools_revealer is None:
            raise ValueError("Object 'simulate_tools_revealer' not found in simulate_tools_palette.ui")
        if not all([self.run_button, self.step_button, self.stop_button, self.reset_button]):
            raise ValueError('One or more simulation buttons not found in simulate_tools_palette.ui')
        
        # Connect button signals
        self.run_button.connect('clicked', self._on_run_clicked)
        self.step_button.connect('clicked', self._on_step_clicked)
        self.stop_button.connect('clicked', self._on_stop_clicked)
        self.reset_button.connect('clicked', self._on_reset_clicked)
        
        # Connect new control signals
        if self.settings_button:
            self.settings_button.connect('clicked', self._on_settings_clicked)
        if self.duration_entry:
            self.duration_entry.connect('changed', self._on_duration_changed)
        if self.time_units_combo:
            self.time_units_combo.connect('changed', self._on_time_units_changed)
            self._populate_time_units_combo()
        
        self._apply_styling()
        self._initialize_duration_controls()
        self._load_settings_panel()
        self._create_widget_container()
        
        # Reveal the palette by default when added to SwissKnife
        if self.simulate_tools_revealer:
            self.simulate_tools_revealer.set_reveal_child(True)
    
    def _create_widget_container(self):
        """Create a container for the simulate tools palette.
        
        FIXED: Return the revealer (not the grid) to maintain proper widget hierarchy.
        The revealer contains the grid with all controls including the progress bar.
        This ensures proper visibility and layout.
        """
        # Use the revealer from the UI file - do NOT extract the grid from it
        # The revealer is needed to control visibility and maintain widget hierarchy
        self.widget_container = self.simulate_tools_revealer
        
        # Note: settings_revealer still loaded but not included in widget_container
        # It will be accessed via create_settings_panel() factory method (Phase 3)

    def _load_settings_panel(self):
        """Load the inline settings panel UI from separate file.
        
        Loads settings_sub_palette.ui which contains the settings revealer panel.
        This replaces the modal settings dialog with an inline panel that slides
        up from the simulate palette when the settings button is clicked.
        """
        settings_ui_path = os.path.join(
            os.path.dirname(self.ui_dir), 'palettes', 'simulate', 'settings_sub_palette.ui'
        )
        
        if not os.path.exists(settings_ui_path):
            self.settings_revealer = None
            return
        
        try:
            # Load settings UI
            settings_builder = Gtk.Builder()
            settings_builder.add_from_file(settings_ui_path)
            
            # Get settings revealer
            self.settings_revealer = settings_builder.get_object('settings_revealer')
            
            if self.settings_revealer is None:
                return
            
            # Get control widgets (most controls removed - parameters panel simplified)
            # Only keeping the settings revealer for potential future use
            self.time_scale_spin = settings_builder.get_object('time_scale_spin')
            self.dt_auto_radio = settings_builder.get_object('dt_auto_radio')
            self.dt_manual_radio = settings_builder.get_object('dt_manual_radio')
            self.dt_manual_entry = settings_builder.get_object('dt_manual_entry')
            
            # τ-Leaping controls
            self.tau_leaping_check = settings_builder.get_object('tau_leaping_check')
            self.tau_epsilon_entry = settings_builder.get_object('tau_epsilon_entry')
            self.critical_threshold_entry = settings_builder.get_object('critical_threshold_entry')
            self.parallel_stochastic_check = settings_builder.get_object('parallel_stochastic_check')
            
            # Batch mode controls
            self.batch_mode_enabled_check = settings_builder.get_object('batch_mode_enabled_check')
            self.batch_replicates_label = settings_builder.get_object('batch_replicates_label')
            self.batch_replicates_spin = settings_builder.get_object('batch_replicates_spin')
            self.batch_output_label = settings_builder.get_object('batch_output_label')
            self.batch_output_chooser = settings_builder.get_object('batch_output_chooser')
            
            # Ensure manual entry is editable (critical fix)
            if self.dt_manual_entry:
                self.dt_manual_entry.set_editable(True)
                self.dt_manual_entry.set_can_focus(True)
            
            self.settings_apply_button = None  # Removed from parameters panel
            self.settings_reset_button = None  # Removed from parameters panel
            
            # Create buffered settings for atomic updates
            self.buffered_settings = None  # Will be initialized when simulation is set
            self._debounce_timer = None  # For entry field debouncing
            
            # Wire up control handlers
            self._wire_settings_controls()
            
            # Force white text on all labels programmatically
            self._apply_settings_panel_colors()
            
            # Load CSS
            self._load_settings_css()
            
            # Initially hidden
            self.settings_revealer.set_reveal_child(False)
            self.settings_revealer.set_visible(False)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.settings_revealer = None
    
    def _apply_settings_panel_colors(self):
        """Apply bright text colors to settings panel labels programmatically.
        
        This is done via GTK API instead of CSS to avoid rendering delays.
        """
        if not self.settings_revealer:
            return
        
        try:
            from gi.repository import Gdk
            
            # Define white color
            white = Gdk.RGBA()
            white.parse("#ffffff")
            
            # Recursively set all label colors to white
            def set_label_colors(widget):
                if isinstance(widget, Gtk.Label):
                    widget.override_color(Gtk.StateFlags.NORMAL, white)
                    widget.override_color(Gtk.StateFlags.ACTIVE, white)
                    widget.override_color(Gtk.StateFlags.PRELIGHT, white)
                    widget.override_color(Gtk.StateFlags.SELECTED, white)
                    widget.override_color(Gtk.StateFlags.INSENSITIVE, white)
                
                # Recurse into containers
                if isinstance(widget, Gtk.Container):
                    for child in widget.get_children():
                        set_label_colors(child)
            
            # Apply to entire settings panel
            set_label_colors(self.settings_revealer)
            
        except Exception as e:
            pass  # Silently ignore color setting errors
    
    def _load_settings_css(self):
        """Load CSS styling for settings panel.
        
        DISABLED: Custom CSS caused severe rendering delays (text appearing after 1 minute).
        Now using default SwissKnife palette styling which works instantly.
        """
        # CSS loading disabled - using SwissKnife default styling
        pass
    
    def _wire_settings_controls(self):
        """Wire settings panel controls to simulation settings.
        
        Now uses BufferedSimulationSettings for atomic updates without Apply button.
        All changes are buffered, validated, and committed atomically.
        Entry fields are debounced to prevent excessive updates.
        """
        # Wire playback speed spinner (immediate atomic update)
        if self.time_scale_spin:
            self.time_scale_spin.connect('value-changed', self._on_speed_changed)
        
        # Wire time step radio buttons (immediate atomic update)
        if self.dt_auto_radio:
            self.dt_auto_radio.connect('toggled', self._on_dt_mode_changed)
        if self.dt_manual_radio:
            self.dt_manual_radio.connect('toggled', self._on_dt_mode_changed)
        
        # Wire manual time step entry (debounced atomic update)
        if self.dt_manual_entry:
            self.dt_manual_entry.connect('changed', self._on_dt_entry_changed)
            self.dt_manual_entry.connect('activate', self._on_dt_entry_activate)
        
        # Wire τ-leaping controls
        if self.tau_leaping_check:
            self.tau_leaping_check.connect('toggled', self._on_tau_leaping_toggled)
        if self.tau_epsilon_entry:
            self.tau_epsilon_entry.connect('changed', self._on_tau_epsilon_changed)
            self.tau_epsilon_entry.connect('activate', self._on_tau_epsilon_activate)
        if self.critical_threshold_entry:
            self.critical_threshold_entry.connect('changed', self._on_critical_threshold_changed)
            self.critical_threshold_entry.connect('activate', self._on_critical_threshold_activate)
        if self.parallel_stochastic_check:
            self.parallel_stochastic_check.connect('toggled', self._on_parallel_stochastic_toggled)
        
        # Wire batch mode controls
        if self.batch_mode_enabled_check:
            self.batch_mode_enabled_check.connect('toggled', self._on_batch_mode_toggled)
        if self.batch_replicates_spin:
            self.batch_replicates_spin.connect('value-changed', self._on_batch_replicates_changed)
        if self.batch_output_chooser:
            self.batch_output_chooser.connect('file-set', self._on_batch_output_changed)
    
    def _on_batch_mode_toggled(self, check_button):
        """Handle batch mode enable/disable toggle with atomic persistence.
        
        Args:
            check_button: GtkCheckButton that was toggled
        """
        is_enabled = check_button.get_active()
        
        # Enable/disable batch controls
        if self.batch_replicates_label:
            self.batch_replicates_label.set_sensitive(is_enabled)
        if self.batch_replicates_spin:
            self.batch_replicates_spin.set_sensitive(is_enabled)
        if self.batch_output_label:
            self.batch_output_label.set_sensitive(is_enabled)
        if self.batch_output_chooser:
            self.batch_output_chooser.set_sensitive(is_enabled)
        
        # Atomically save to model's simulation_settings
        if self.simulation:
            model = self.simulation.model
            if hasattr(model, 'simulation_settings'):
                model.simulation_settings.batch_mode_enabled = is_enabled
                print(f"✓ Batch mode {'enabled' if is_enabled else 'disabled'}")
    
    def _on_batch_replicates_changed(self, spin_button):
        """Handle batch replicates spinner change with atomic persistence.
        
        Args:
            spin_button: GtkSpinButton that changed
        """
        value = int(spin_button.get_value())
        
        # Atomically save to model's simulation_settings
        if self.simulation:
            model = self.simulation.model
            if hasattr(model, 'simulation_settings'):
                model.simulation_settings.batch_replicates = value
                print(f"✓ Batch replicates set to {value}")
    
    def _on_batch_output_changed(self, file_chooser):
        """Handle batch output folder change with atomic persistence.
        
        Args:
            file_chooser: GtkFileChooserButton that changed
        """
        folder = file_chooser.get_filename()
        
        # Atomically save to model's simulation_settings
        if self.simulation and folder:
            model = self.simulation.model
            if hasattr(model, 'simulation_settings'):
                model.simulation_settings.batch_output_folder = folder
    
    def _on_speed_changed(self, spin):
        """Handle playback speed spinner change (atomic).
        
        Uses BufferedSimulationSettings for atomic update.
        """
        if not self.simulation or not self.buffered_settings:
            return
        
        new_value = spin.get_value()
        
        # Write to buffer
        self.buffered_settings.buffer.time_scale = new_value
        self.buffered_settings.mark_dirty()
        
        # Commit atomically
        if self.buffered_settings.commit():
            # Restart simulation if it was running
            if self.simulation.is_running():
                self.simulation.stop()
                time_step = self.simulation.get_effective_dt()
                self.simulation.run(time_step=time_step)
            
            self.emit('settings-changed')
        else:
            # Validation failed - restore previous value
            self.time_scale_spin.set_value(self.simulation.settings.time_scale)
    
    def _on_dt_mode_changed(self, radio_button):
        """Handle time step mode change (Auto/Manual) - atomic.
        
        Uses BufferedSimulationSettings for atomic update.
        """
        if not radio_button.get_active():
            return  # Only handle activation, not deactivation
        
        if not self.simulation or not self.buffered_settings:
            return
        
        # Determine which mode is selected
        is_auto = (radio_button == self.dt_auto_radio)
        
        # Write to buffer
        self.buffered_settings.buffer.dt_auto = is_auto
        self.buffered_settings.mark_dirty()
        
        # Commit atomically
        if self.buffered_settings.commit():
            # Update entry sensitivity and ensure it's editable
            if self.dt_manual_entry:
                self.dt_manual_entry.set_sensitive(not is_auto)
                self.dt_manual_entry.set_editable(True)
            
            self.emit('settings-changed')
        else:
            # Validation failed - restore previous state
            if self.simulation.settings.dt_auto:
                self.dt_auto_radio.set_active(True)
            else:
                self.dt_manual_radio.set_active(True)
    
    def _on_dt_entry_changed(self, entry):
        """Handle manual time step entry change (debounced).
        
        Debounces input to avoid excessive validation during typing.
        """
        # Cancel pending timer
        if self._debounce_timer:
            GLib.source_remove(self._debounce_timer)
        
        # Schedule update after 500ms of no typing
        self._debounce_timer = GLib.timeout_add(500, self._apply_dt_entry_value, entry)
    
    def _on_dt_entry_activate(self, entry):
        """Handle manual time step entry activation (Enter key) - immediate.
        
        When user presses Enter, apply immediately without debounce.
        """
        # Cancel pending debounce timer
        if self._debounce_timer:
            GLib.source_remove(self._debounce_timer)
            self._debounce_timer = None
        
        # Apply immediately
        self._apply_dt_entry_value(entry)
    
    def _apply_dt_entry_value(self, entry):
        """Apply manual time step entry value atomically.
        
        Uses BufferedSimulationSettings for atomic update with validation.
        """
        self._debounce_timer = None  # Clear timer reference
        
        if not self.simulation or not self.buffered_settings:
            return False  # Return False to stop timer
        
        try:
            # Parse value
            text = entry.get_text().strip()
            value = float(text)
            
            # Write to buffer
            self.buffered_settings.buffer.dt_manual = value
            self.buffered_settings.mark_dirty()
            
            # Commit atomically (with validation)
            if self.buffered_settings.commit():
                # Success - remove error styling
                entry.get_style_context().remove_class('error')
                self.emit('settings-changed')
            else:
                # Validation failed - show error
                entry.get_style_context().add_class('error')
                # Restore previous value after brief delay
                GLib.timeout_add(2000, self._restore_dt_entry_value, entry)
        
        except ValueError:
            # Parse error - show error styling
            entry.get_style_context().add_class('error')
            # Restore previous value after brief delay
            GLib.timeout_add(2000, self._restore_dt_entry_value, entry)
        
        return False  # Return False to stop timer (one-shot)
    
    def _restore_dt_entry_value(self, entry):
        """Restore entry to valid value after error."""
        if self.simulation:
            entry.set_text(str(self.simulation.settings.dt_manual))
            entry.get_style_context().remove_class('error')
        return False  # One-shot timer
    
    # ========== τ-Leaping Control Handlers ==========
    
    def _on_tau_leaping_toggled(self, check_button):
        """Handle τ-leaping checkbox toggle (atomic)."""
        if not self.simulation or not self.buffered_settings:
            return
        
        enabled = check_button.get_active()
        
        # Write to buffer
        self.buffered_settings.buffer.use_tau_leaping = enabled
        self.buffered_settings.mark_dirty()
        
        # Commit atomically
        if self.buffered_settings.commit():
            # Update UI sensitivity
            if self.tau_epsilon_entry:
                self.tau_epsilon_entry.set_sensitive(enabled)
            if self.critical_threshold_entry:
                self.critical_threshold_entry.set_sensitive(enabled)
            if self.parallel_stochastic_check:
                self.parallel_stochastic_check.set_sensitive(enabled)
            
            self.emit('settings-changed')
        else:
            # Validation failed - restore previous state
            check_button.set_active(self.simulation.settings.use_tau_leaping)
    
    def _on_tau_epsilon_changed(self, entry):
        """Handle epsilon entry change (debounced)."""
        # Cancel pending timer
        if self._debounce_timer:
            GLib.source_remove(self._debounce_timer)
        
        # Schedule update after 500ms of no typing
        self._debounce_timer = GLib.timeout_add(500, self._apply_tau_epsilon_value, entry)
    
    def _on_tau_epsilon_activate(self, entry):
        """Handle epsilon entry activation (Enter key) - immediate."""
        if self._debounce_timer:
            GLib.source_remove(self._debounce_timer)
            self._debounce_timer = None
        
        self._apply_tau_epsilon_value(entry)
    
    def _apply_tau_epsilon_value(self, entry):
        """Apply epsilon entry value atomically."""
        self._debounce_timer = None
        
        if not self.simulation or not self.buffered_settings:
            return False
        
        try:
            text = entry.get_text().strip()
            value = float(text)
            
            # Validate range
            if not 0 < value <= 1:
                entry.get_style_context().add_class('error')
                GLib.timeout_add(2000, self._restore_tau_epsilon_value, entry)
                return False
            
            # Write to buffer
            self.buffered_settings.buffer.tau_epsilon = value
            self.buffered_settings.mark_dirty()
            
            # Commit atomically
            if self.buffered_settings.commit():
                entry.get_style_context().remove_class('error')
                self.emit('settings-changed')
            else:
                entry.get_style_context().add_class('error')
                GLib.timeout_add(2000, self._restore_tau_epsilon_value, entry)
        
        except ValueError:
            entry.get_style_context().add_class('error')
            GLib.timeout_add(2000, self._restore_tau_epsilon_value, entry)
        
        return False
    
    def _restore_tau_epsilon_value(self, entry):
        """Restore epsilon to valid value after error."""
        if self.simulation:
            entry.set_text(str(self.simulation.settings.tau_epsilon))
            entry.get_style_context().remove_class('error')
        return False
    
    def _on_critical_threshold_changed(self, entry):
        """Handle critical threshold entry change (debounced)."""
        if self._debounce_timer:
            GLib.source_remove(self._debounce_timer)
        
        self._debounce_timer = GLib.timeout_add(500, self._apply_critical_threshold_value, entry)
    
    def _on_critical_threshold_activate(self, entry):
        """Handle critical threshold entry activation (Enter key) - immediate."""
        if self._debounce_timer:
            GLib.source_remove(self._debounce_timer)
            self._debounce_timer = None
        
        self._apply_critical_threshold_value(entry)
    
    def _apply_critical_threshold_value(self, entry):
        """Apply critical threshold entry value atomically."""
        self._debounce_timer = None
        
        if not self.simulation or not self.buffered_settings:
            return False
        
        try:
            text = entry.get_text().strip()
            value = float(text)
            
            # Validate range
            if value <= 0:
                entry.get_style_context().add_class('error')
                GLib.timeout_add(2000, self._restore_critical_threshold_value, entry)
                return False
            
            # Write to buffer
            self.buffered_settings.buffer.critical_threshold = value
            self.buffered_settings.mark_dirty()
            
            # Commit atomically
            if self.buffered_settings.commit():
                entry.get_style_context().remove_class('error')
                self.emit('settings-changed')
            else:
                entry.get_style_context().add_class('error')
                GLib.timeout_add(2000, self._restore_critical_threshold_value, entry)
        
        except ValueError:
            entry.get_style_context().add_class('error')
            GLib.timeout_add(2000, self._restore_critical_threshold_value, entry)
        
        return False
    
    def _restore_critical_threshold_value(self, entry):
        """Restore critical threshold to valid value after error."""
        if self.simulation:
            entry.set_text(str(self.simulation.settings.critical_threshold))
            entry.get_style_context().remove_class('error')
        return False
    
    def _on_parallel_stochastic_toggled(self, check_button):
        """Handle parallel stochastic checkbox toggle (atomic)."""
        if not self.simulation or not self.buffered_settings:
            return
        
        enabled = check_button.get_active()
        
        # Write to buffer
        self.buffered_settings.buffer.use_parallel_stochastic = enabled
        self.buffered_settings.mark_dirty()
        
        # Commit atomically
        if self.buffered_settings.commit():
            self.emit('settings-changed')
        else:
            # Validation failed - restore previous state
            check_button.set_active(self.simulation.settings.use_parallel_stochastic)
    
    # ========== UI Synchronization ==========
    
    def _sync_settings_to_ui(self):
        """Synchronize current simulation settings to UI controls.
        
        Syncs all settings panel controls with current simulation settings.
        """
        if not self.simulation or not hasattr(self, 'settings_revealer') or self.settings_revealer is None:
            return
        
        settings = self.simulation.settings
        
        # Update playback speed spinner
        if self.time_scale_spin:
            self.time_scale_spin.set_value(settings.time_scale)
        
        # Update time step mode radio buttons
        if self.dt_auto_radio and self.dt_manual_radio:
            if settings.dt_auto:
                self.dt_auto_radio.set_active(True)
            else:
                self.dt_manual_radio.set_active(True)
        
        # Update manual time step entry
        if self.dt_manual_entry:
            self.dt_manual_entry.set_text(str(settings.dt_manual))
            self.dt_manual_entry.set_sensitive(not settings.dt_auto)
            self.dt_manual_entry.set_editable(True)
        
        # Update τ-leaping controls
        if self.tau_leaping_check:
            self.tau_leaping_check.set_active(settings.use_tau_leaping)
        
        if self.tau_epsilon_entry:
            self.tau_epsilon_entry.set_text(str(settings.tau_epsilon))
            self.tau_epsilon_entry.set_sensitive(settings.use_tau_leaping)
        
        if self.critical_threshold_entry:
            self.critical_threshold_entry.set_text(str(settings.critical_threshold))
            self.critical_threshold_entry.set_sensitive(settings.use_tau_leaping)
        
        if self.parallel_stochastic_check:
            self.parallel_stochastic_check.set_active(settings.use_parallel_stochastic)
            self.parallel_stochastic_check.set_sensitive(settings.use_tau_leaping)
        
        # Update batch mode controls (sync from manager.simulation_settings)
        model = self.simulation.model
        if hasattr(model, 'simulation_settings'):
            batch_settings = model.simulation_settings
            
            if self.batch_mode_enabled_check:
                self.batch_mode_enabled_check.set_active(batch_settings.batch_mode_enabled)
            
            if self.batch_replicates_spin:
                self.batch_replicates_spin.set_value(batch_settings.batch_replicates)
                self.batch_replicates_spin.set_sensitive(batch_settings.batch_mode_enabled)
            
            if self.batch_output_chooser and batch_settings.batch_output_folder:
                self.batch_output_chooser.set_filename(batch_settings.batch_output_folder)
                self.batch_output_chooser.set_sensitive(batch_settings.batch_mode_enabled)
            
            if self.batch_replicates_label:
                self.batch_replicates_label.set_sensitive(batch_settings.batch_mode_enabled)
            
            if self.batch_output_label:
                self.batch_output_label.set_sensitive(batch_settings.batch_mode_enabled)
    
    def _hide_settings_panel(self):
        """Hide the settings panel with animation.
        
        DEPRECATED: Settings panel visibility is now managed by ParameterPanelManager (Phase 3).
        This method is kept for backward compatibility but does nothing.
        """
        # Parameter panel manager handles visibility - no-op
        pass

    def _init_simulation_controller(self):
        """Initialize the simulation controller with the model."""
        if self._model is None:
            return
        
        # Create controller and assign via property setter
        # The setter automatically creates BufferedSimulationSettings
        self.simulation = SimulationController(self._model)
        
        # PHASE 1-2 FIX: Do NOT overwrite controller.data_collector
        # The controller creates its own DataCollector (for Report Panel tables)
        # This palette has its own SimulationDataCollector (for real-time plots)
        # Both need to coexist - just register our collector as a step listener
        # DO NOT OVERWRITE: self.simulation.data_collector = self.data_collector
        self.simulation.add_step_listener(self._on_simulation_step)
        self.simulation.add_step_listener(self.data_collector.on_simulation_step)
        
        # Apply default UI values to simulation settings
        self._apply_ui_defaults_to_settings()
        
        # Note: _sync_settings_to_ui() is already called by the setter
    
    def _apply_ui_defaults_to_settings(self):
        """Apply default UI values to simulation settings on initialization.
        
        This ensures the progress bar works from the start by setting
        duration from the UI's default value (60 seconds).
        
        ALWAYS applies UI defaults to ensure progress bar works globally
        for all model loading paths (new models, file loading, etc.).
        """
        if self.simulation is None:
            return
        
        # Always apply UI defaults (removed "if duration is None" check)
        # This ensures progress bar works for ALL loading paths
        if self.duration_entry:
            try:
                duration_text = self.duration_entry.get_text().strip()
                duration = float(duration_text)
                
                # Get units from combo
                units = TimeUnits.SECONDS  # Default
                if self.time_units_combo:
                    units_str = self.time_units_combo.get_active_text()
                    if units_str:
                        units = TimeUnits.from_string(units_str)
                
                # Set duration in simulation settings
                self.simulation.settings.set_duration(duration, units)
            except (ValueError, AttributeError):
                # If UI values are invalid, set a reasonable default
                self.simulation.settings.set_duration(60.0, TimeUnits.SECONDS)

    def set_model(self, model):
        """Set the Petri net model for simulation.
        
        Args:
            model: PetriNetModel instance
        """
        self._model = model
        self._init_simulation_controller()

    def _on_simulation_step(self, controller, time):
        """Callback from SimulationController after each step.
        
        Emits 'step-executed' signal for canvas redraw.
        Updates progress bar and time display.
        
        Args:
            controller: The SimulationController instance
            time: Current simulation time
        """
        self.emit('step-executed', time)
        self._update_progress_display()

    def _apply_styling(self):
        """Apply custom CSS styling to the simulation tools palette."""
        css = '''
        .simulate-tools-palette {
            background: linear-gradient(to bottom, #34495e, #2c3e50);
            border: 2px solid #1a252f;
            border-radius: 8px;
            padding: 6px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),
                        0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .sim-tool-button {
            background: linear-gradient(to bottom, #5d6d7e, #566573);
            border: 2px solid #34495e;
            border-radius: 4px;
            font-size: 14px;
            font-weight: bold;
            color: white;
            min-width: 40px;
            min-height: 40px;
            padding: 0;
            margin: 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .sim-tool-button:hover {
            background: linear-gradient(to bottom, #6c7a89, #5d6d7e);
            border-color: #4a5f7f;
        }
        
        .sim-tool-button:active {
            background: linear-gradient(to bottom, #4a5568, #3d4855);
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .sim-tool-button:disabled {
            background: linear-gradient(to bottom, #454545, #383838);
            border-color: #2a2a2a;
            color: #888888;
            opacity: 0.5;
        }
        
        /* Run button - green theme */
        .run-button {
            background: linear-gradient(to bottom, #27ae60, #229954);
            border-color: #1e8449;
        }
        
        .run-button:hover {
            background: linear-gradient(to bottom, #2ecc71, #27ae60);
        }
        
        .run-button:active {
            background: linear-gradient(to bottom, #1e8449, #196f3d);
        }
        
        /* Step button - cyan/teal theme */
        .step-button {
            background: linear-gradient(to bottom, #16a085, #138d75);
            border-color: #117864;
        }
        
        .step-button:hover {
            background: linear-gradient(to bottom, #1abc9c, #16a085);
        }
        
        .step-button:active {
            background: linear-gradient(to bottom, #138d75, #117864);
        }
        
        /* Stop button - red theme */
        .stop-button {
            background: linear-gradient(to bottom, #e74c3c, #c0392b);
            border-color: #a93226;
        }
        
        .stop-button:hover {
            background: linear-gradient(to bottom, #ec7063, #e74c3c);
        }
        
        .stop-button:active {
            background: linear-gradient(to bottom, #c0392b, #a93226);
        }
        
        /* Reset button - orange theme */
        .reset-button {
            background: linear-gradient(to bottom, #f39c12, #e67e22);
            border-color: #ca6f1e;
        }
        
        .reset-button:hover {
            background: linear-gradient(to bottom, #f5b041, #f39c12);
        }
        
        .reset-button:active {
            background: linear-gradient(to bottom, #e67e22, #ca6f1e);
        }
        
        /* Settings button - blue/purple theme */
        .settings-button {
            background: linear-gradient(to bottom, #5d6db9, #4a5899);
            border-color: #3a4578;
        }
        
        .settings-button:hover {
            background: linear-gradient(to bottom, #6c7dc9, #5d6db9);
        }
        
        .settings-button:active {
            background: linear-gradient(to bottom, #4a5899, #3a4578);
        }
        
        /* Duration controls */
        .sim-control-label {
            color: #ffffff;
            font-size: 11px;
            font-weight: bold;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
        }
        
        .sim-control-entry {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid #34495e;
            border-radius: 3px;
            font-size: 11px;
            padding: 2px 4px;
            min-width: 60px;
            color: #000000;
        }
        
        .sim-control-combo {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid #34495e;
            border-radius: 3px;
            font-size: 11px;
        }
        
        /* Progress bar */
        .sim-progress-bar {
            min-height: 20px;
            border-radius: 3px;
        }
        
        .sim-progress-bar progress {
            background: linear-gradient(to right, #27ae60, #2ecc71);
        }
        
        .sim-progress-bar trough {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid #1a252f;
        }
        
        /* Time display */
        .sim-time-display {
            color: #ffffff;
            font-size: 11px;
            font-weight: bold;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
        }
        '''
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode())
        
        # Apply to container
        if self.simulate_tools_container:
            style_context = self.simulate_tools_container.get_style_context()
            style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        # Apply to all buttons
        buttons = [self.run_button, self.step_button, self.stop_button, 
                   self.reset_button, self.settings_button]
        for button in buttons:
            if button:
                style_context = button.get_style_context()
                style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        # Apply to new controls
        controls = [self.duration_entry, self.time_units_combo, 
                    self.progress_bar, self.time_display_label]
        for control in controls:
            if control:
                style_context = control.get_style_context()
                style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _update_button_states(self, running=False, completed=False, reset=False):
        """Update button sensitivity based on simulation state.
        
        This centralizes button state management to ensure consistency and
        make state transitions easier to reason about.
        
        State Machine:
        - IDLE (after reset): Run✓, Step✓, Stop✗, Reset✗, Settings✓
        - RUNNING: Run✗, Step✗, Stop✓, Reset✗, Settings✗
        - PAUSED: Run✓, Step✓, Stop✗, Reset✓, Settings✓
        - COMPLETED: Run✗, Step✗, Stop✗, Reset✓, Settings✓
        
        Args:
            running: True if simulation is actively running
            completed: True if simulation reached duration limit
            reset: True if simulation was just reset to initial state
        """
        if running:
            # Running: only Stop available, no settings changes
            self.run_button.set_sensitive(False)
            self.step_button.set_sensitive(False)
            self.stop_button.set_sensitive(True)
            self.reset_button.set_sensitive(False)
            self.settings_button.set_sensitive(False)
        elif completed:
            # Completed: only Reset available
            self.run_button.set_sensitive(False)
            self.step_button.set_sensitive(False)
            self.stop_button.set_sensitive(False)
            self.reset_button.set_sensitive(True)
            self.settings_button.set_sensitive(True)
        elif reset:
            # Just reset: fresh start state
            self.run_button.set_sensitive(True)
            self.step_button.set_sensitive(True)
            self.stop_button.set_sensitive(False)
            self.reset_button.set_sensitive(False)  # Already at start
            self.settings_button.set_sensitive(True)
        else:
            # Paused/stopped: can resume, step, or reset
            self.run_button.set_sensitive(True)
            self.step_button.set_sensitive(True)
            self.stop_button.set_sensitive(False)
            self.reset_button.set_sensitive(True)
            self.settings_button.set_sensitive(True)

    def _on_run_clicked(self, button):
        """Handle Run button click - start continuous simulation."""
        if self.simulation is None:
            return
        
        # Hide settings panel if open
        self._hide_settings_panel()
        
        # Check if batch mode is enabled in document model
        model = self.simulation.model
        batch_enabled = False
        recorded_objects = set()
        n_replicates = 100
        
        if hasattr(model, 'simulation_settings'):
            settings = model.simulation_settings
            batch_enabled = getattr(settings, 'batch_mode_enabled', False)
            n_replicates = getattr(settings, 'batch_replicates', 100)
            recorded_objects = getattr(settings, 'recorded_objects', set())
        
        if batch_enabled:
            # Batch mode - run N replicates
            self._run_batch_mode(n_replicates, recorded_objects)
        else:
            # Normal mode - single simulation
            self.simulation.run()
            
            # Update button states for running simulation
            self._update_button_states(running=True)

    def _on_step_clicked(self, button):
        """Handle Step button click - execute one simulation step."""
        if self.simulation is None:
            return
        
        # Hide settings panel if open
        self._hide_settings_panel()
        
        # Use effective dt from settings (no hardcoded time_step)
        success = self.simulation.step()
        
        # If step failed or simulation completed, update button states
        if not success or self.simulation.is_simulation_complete():
            self._update_button_states(running=False, completed=True)

    def _on_stop_clicked(self, button):
        """Handle Stop button click - pause simulation."""
        if self.simulation is None:
            return
        
        # Hide settings panel if open
        self._hide_settings_panel()
        
        self.simulation.stop()
        
        # Update button states for stopped/paused simulation
        self._update_button_states(running=False)

    def _on_reset_clicked(self, button):
        """Handle Reset button click - reset to initial marking."""
        if self.simulation is None:
            return
        
        # Hide settings panel if open
        self._hide_settings_panel()
        
        self.simulation.reset()
        
        # PHASE 1-2 FIX: Clear OLD data collector (for plots) on reset
        # The controller.reset() clears the NEW data collector (for Report Panel),
        # but we also need to clear the OLD one (for real-time plots)
        if self.data_collector:
            self.data_collector.clear()
        
        self.emit('reset-executed')
        self._update_progress_display()  # Reset progress bar
        
        # Update button states for reset simulation
        self._update_button_states(running=False, reset=True)
    
    def _run_batch_mode(self, n_replicates: int, recorded_objects: set):
        """Execute batch mode simulation with N replicates.
        
        Args:
            n_replicates: Number of replicates to run
            recorded_objects: Set of place/transition IDs to record
        """
        import threading
        from gi.repository import GLib
        from shypn.engine.simulation.batch_runner import BatchSimulationRunner
        from shypn.ui.dialogs.batch_progress_dialog import BatchProgressDialog
        
        # Apply recording color to recorded objects for visual feedback
        # This provides visual indication of what's being recorded during batch execution
        if hasattr(self.simulation, 'model') and recorded_objects:
            model = self.simulation.model
            
            # Define recording indicator color (same as context menu)
            RECORDING_COLOR = (1.0, 0.6, 0.0)  # RGB: orange
            
            from shypn.netobjs import Place, Transition
            
            # Apply color to recorded objects
            for obj_id in recorded_objects:
                # Find object by ID
                obj = None
                for place in model.places:
                    if place.id == obj_id:
                        obj = place
                        break
                if not obj:
                    for trans in model.transitions:
                        if trans.id == obj_id:
                            obj = trans
                            break
                
                # Apply recording color
                if obj:
                    if isinstance(obj, Place):
                        obj.border_color = RECORDING_COLOR
                    elif isinstance(obj, Transition):
                        obj.border_color = RECORDING_COLOR
                        obj.fill_color = RECORDING_COLOR
                    
                    # Trigger on_changed callback if available
                    if hasattr(obj, 'on_changed') and obj.on_changed:
                        obj.on_changed()
        
        # Get parent window for dialog
        parent_window = None
        widget = self.simulate_tools_container
        while widget:
            if isinstance(widget, Gtk.Window):
                parent_window = widget
                break
            widget = widget.get_parent()
        
        # Create and show progress dialog
        progress_dialog = BatchProgressDialog(parent_window, n_replicates)
        
        # Use present() instead of show() to properly handle parent hierarchy
        # This ensures parent window is mapped before showing the dialog
        if parent_window and parent_window.get_visible():
            progress_dialog.present()
        else:
            progress_dialog.show()
        
        # Disable buttons during batch execution (but preserve object selection/recording marks)
        self._update_button_states(running=True)
        
        # Keep recorded objects visually highlighted by NOT clearing selection
        # The selection shows which objects are being recorded in batch mode
        
        # Create batch runner
        batch_runner = BatchSimulationRunner()
        
        # Set up cancel callback
        def on_cancel():
            batch_runner.cancel()
        
        progress_dialog.set_cancel_callback(on_cancel)
        
        def run_batch_thread():
            """Background thread for batch execution."""
            import time
            start_time = time.time()
            
            try:
                # Progress callback to update dialog
                def progress_callback(replicate_num, total, elapsed, eta_str):
                    """Update progress dialog from background thread."""
                    GLib.idle_add(
                        progress_dialog.update_progress,
                        replicate_num, total, elapsed, eta_str
                    )
                
                # Check cancellation callback
                def cancellation_check():
                    return batch_runner.is_cancelled
                
                # Run batch
                results = batch_runner.run_batch(
                    controller=self.simulation,
                    n_replicates=n_replicates,
                    recorded_objects=recorded_objects,
                    progress_callback=progress_callback,
                    cancellation_check=cancellation_check
                )
                
                # Calculate results
                total_time = time.time() - start_time
                successful = sum(1 for r in results if 'error' not in r)
                
                # Show completion in dialog
                GLib.idle_add(progress_dialog.show_completion, successful, n_replicates, total_time)
                
                # Auto-save results
                try:
                    results_folder = self._save_batch_results(results, recorded_objects, n_replicates)
                except Exception as save_error:
                    print(f"⚠️ Failed to save results: {save_error}")
                    import traceback
                    traceback.print_exc()
                
                # Re-enable buttons on main thread
                GLib.idle_add(self._update_button_states, False, True)
                
            except Exception as e:
                print(f"❌ Batch execution error: {e}")
                import traceback
                traceback.print_exc()
                
                # Show error in dialog
                GLib.idle_add(progress_dialog.show_error, str(e))
                
                # Re-enable buttons
                GLib.idle_add(self._update_button_states, False, False)
        
        # Start batch execution in background thread
        batch_thread = threading.Thread(target=run_batch_thread, daemon=True)
        batch_thread.start()
    
    def _save_batch_results(self, results: list, recorded_objects: set, n_replicates: int) -> str:
        """Save batch simulation results to CSV files and JSON metadata.
        
        Args:
            results: List of result dictionaries from batch runner
            recorded_objects: Set of recorded object IDs
            n_replicates: Total number of replicates
            
        Returns:
            str: Path to results folder, or None if save failed
        """
        import os
        import json
        import csv
        from datetime import datetime
        import numpy as np
        
        # Use user-specified batch output folder if set
        model = self.simulation.model
        project_folder = None
        
        if hasattr(model, 'simulation_settings') and model.simulation_settings:
            settings = model.simulation_settings
            if hasattr(settings, 'batch_output_folder') and settings.batch_output_folder:
                # User chose a specific folder - use it
                project_folder = settings.batch_output_folder
        
        # Fallback: determine from document path
        if not project_folder:
            if hasattr(model, 'filepath') and model.filepath:
                # Document has been saved - use its directory
                model_path = model.filepath
                # Navigate up to find project root (assumes workspace/projects/{project}/models/model.shy)
                path_parts = model_path.split(os.sep)
                if 'projects' in path_parts:
                    projects_idx = path_parts.index('projects')
                    if projects_idx + 1 < len(path_parts):
                        # Project name is after 'projects'
                        project_folder = os.sep.join(path_parts[:projects_idx + 2])
        
        if not project_folder:
            # Final fallback: use workspace/results/
            current_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.normpath(os.path.join(current_dir, '..', '..', '..'))
            project_folder = os.path.join(repo_root, 'workspace')
        
        # Create results folder with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = os.path.join(project_folder, 'results', f'batch_{timestamp}')
        os.makedirs(results_dir, exist_ok=True)
        
        # Save configuration
        config = {
            'timestamp': timestamp,
            'n_replicates': n_replicates,
            'recorded_objects': list(recorded_objects),
            'settings': {
                'duration': self.simulation.settings.duration,
                'time_units': str(self.simulation.settings.time_units),
                'dt_auto': self.simulation.settings.dt_auto,
                'use_tau_leaping': self.simulation.settings.use_tau_leaping,
                'tau_epsilon': self.simulation.settings.tau_epsilon
            }
        }
        
        with open(os.path.join(results_dir, 'config.json'), 'w') as f:
            json.dump(config, f, indent=2)
        
        # Save individual replicate CSVs
        csv_count = 0
        for result in results:
            if 'error' in result:
                continue  # Skip failed replicates
            
            replicate_id = result['replicate_id']
            time_points = result['time_points']
            place_data = result.get('place_data', {})
            transition_data = result.get('transition_data', {})
            
            # Write CSV with time and recorded objects
            csv_path = os.path.join(results_dir, f'run_{replicate_id + 1:03d}.csv')
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Header row
                header = ['time'] + sorted(place_data.keys()) + sorted(transition_data.keys())
                writer.writerow(header)
                
                # Data rows
                for i, t in enumerate(time_points):
                    row = [t]
                    # Add place values
                    for obj_id in sorted(place_data.keys()):
                        row.append(place_data[obj_id][i] if i < len(place_data[obj_id]) else '')
                    # Add transition values
                    for obj_id in sorted(transition_data.keys()):
                        row.append(transition_data[obj_id][i] if i < len(transition_data[obj_id]) else '')
                    writer.writerow(row)
            csv_count += 1
        
        # Calculate and save summary statistics
        successful_results = [r for r in results if 'error' not in r]
        if successful_results:
            summary = {
                'timestamp': timestamp,
                'successful_replicates': len(successful_results),
                'total_replicates': n_replicates,
                'statistics': {}
            }
            
            # Calculate stats for each recorded object
            for obj_id in recorded_objects:
                obj_trajectories = []
                
                # Collect trajectories from all replicates
                for result in successful_results:
                    if obj_id in result.get('place_data', {}):
                        obj_trajectories.append(result['place_data'][obj_id])
                    elif obj_id in result.get('transition_data', {}):
                        obj_trajectories.append(result['transition_data'][obj_id])
                
                if obj_trajectories:
                    # Convert to numpy array (pad to same length if needed)
                    max_len = max(len(traj) for traj in obj_trajectories)
                    padded = np.array([
                        traj + [traj[-1]] * (max_len - len(traj))
                        for traj in obj_trajectories
                    ])
                    
                    summary['statistics'][obj_id] = {
                        'mean': np.mean(padded, axis=0).tolist(),
                        'std': np.std(padded, axis=0).tolist(),
                        'min': np.min(padded, axis=0).tolist(),
                        'max': np.max(padded, axis=0).tolist(),
                        'final_mean': float(np.mean(padded[:, -1])),
                        'final_std': float(np.std(padded[:, -1]))
                    }
            
            with open(os.path.join(results_dir, 'summary.json'), 'w') as f:
                json.dump(summary, f, indent=2)
        
        return results_dir

    def _on_settings_clicked(self, button):
        """Handle Settings button click - request parameter panel toggle.
        
        PHASE 3: Emit signal for parameter panel manager to handle.
        The universal parameter panel manager will control the settings panel display.
        
        Fallback: If signal not handled, toggles inline settings revealer directly (old behavior).
        """
        if self.simulation is None:
            return
        
        # PHASE 3: Emit signal for parameter panel manager
        self.emit('settings-toggle-requested')
        
        # OLD BEHAVIOR (kept as fallback if signal not handled):
        # Check if inline settings panel is available
        # if not hasattr(self, 'settings_revealer') or self.settings_revealer is None:
        #     return self._on_settings_clicked_modal_dialog(button)
        # ... (rest of old toggle code)
    
    def _on_settings_clicked_modal_dialog(self, button):
        """Handle Settings dialog click - open simulation settings dialog (OLD VERSION).
        
        This is the original modal dialog implementation, kept as fallback
        if the inline settings panel fails to load.
        """
        if self.simulation is None:
            return
        
        # Pause simulation if running
        was_running = self.simulation.is_running()
        if was_running:
            self.simulation.stop()
        
        try:
            from shypn.dialogs.simulation_settings_dialog import show_simulation_settings_dialog
            
            # Get parent window
            parent = self.simulate_tools_revealer.get_toplevel()
            if not isinstance(parent, Gtk.Window):
                parent = None
            
            # Synchronize batch mode settings from manager to controller before showing dialog
            model = self.simulation.model
            if hasattr(model, 'simulation_settings'):
                manager_settings = model.simulation_settings
                # Copy batch settings to controller settings before dialog
                self.simulation.settings.batch_mode_enabled = manager_settings.batch_mode_enabled
                self.simulation.settings.batch_replicates = manager_settings.batch_replicates
                self.simulation.settings.batch_output_folder = manager_settings.batch_output_folder
                # Note: recorded_objects is stored only in manager_settings
            
            # Show dialog and apply settings
            if show_simulation_settings_dialog(self.simulation.settings, parent):
                # Settings updated successfully
                
                # Synchronize batch mode settings back to manager
                if hasattr(model, 'simulation_settings'):
                    manager_settings = model.simulation_settings
                    manager_settings.batch_mode_enabled = self.simulation.settings.batch_mode_enabled
                    manager_settings.batch_replicates = self.simulation.settings.batch_replicates
                    manager_settings.batch_output_folder = self.simulation.settings.batch_output_folder
                    # recorded_objects stays in manager_settings (managed via context menu)
                
                # Update duration display to reflect any changes
                self._update_duration_display()
                # Reset progress if duration changed
                self._update_progress_display()
                
                # Emit signal for data collector/matplotlib updates
                self.emit('settings-changed')
                
                # Notify user if simulation was running
                pass
        except Exception as e:
            import sys
            import traceback
            traceback.print_exc()
        finally:
            # Update button states based on current state
            self._update_button_states(running=was_running)
    
    def _on_duration_changed(self, entry):
        """Handle duration entry change - update simulation settings.
        
        If simulation is running, it will continue with new duration.
        Progress bar will recalculate based on new duration.
        Emits 'settings-changed' signal for matplotlib/data collector updates.
        """
        if self.simulation is None:
            return
        
        try:
            duration_text = entry.get_text().strip()
            if not duration_text:
                return
            
            duration = float(duration_text)
            if duration <= 0:
                return
            
            # Get current time units
            units_str = self.time_units_combo.get_active_text()
            if not units_str:
                return
                
            units = TimeUnits.from_string(units_str)
            
            # Store old duration for comparison
            old_duration = self.simulation.settings.get_duration_seconds() if self.simulation.settings.duration else None
            
            # Update settings
            self.simulation.settings.set_duration(duration, units)
            new_duration = self.simulation.settings.get_duration_seconds()
            
            # If duration changed significantly, update progress display and notify listeners
            if old_duration is None or abs(new_duration - old_duration) > 0.001:
                self._update_progress_display()
                
                # Emit signal for data collector/matplotlib updates
                self.emit('settings-changed')
                    
        except (ValueError, AttributeError) as e:
            # Invalid input or units not set, ignore silently
            pass
    
    def _on_time_units_changed(self, combo):
        """Handle time units combo change - update simulation settings."""
        # Revalidate duration with new units
        if self.duration_entry:
            self._on_duration_changed(self.duration_entry)
    
    def _populate_time_units_combo(self):
        """Populate the time units combo box with available units."""
        if not self.time_units_combo:
            return
        
        # Clear existing items
        self.time_units_combo.remove_all()
        
        # Add all time units
        for unit in TimeUnits:
            self.time_units_combo.append_text(unit.full_name)
        
        # Set default to seconds
        self.time_units_combo.set_active(1)  # SECONDS is index 1
    
    def _initialize_duration_controls(self):
        """Initialize duration controls with current settings."""
        if self.simulation is None:
            return
        
        self._update_duration_display()
        self._update_progress_display()
    
    def _update_duration_display(self):
        """Update duration entry and combo from current settings."""
        if not self.duration_entry or not self.time_units_combo:
            return
        
        if self.simulation is None:
            return
        
        settings = self.simulation.settings
        if settings.duration:
            self.duration_entry.set_text(str(settings.duration))
            
            # Set combo to current units
            for i, unit in enumerate(TimeUnits):
                if unit == settings.time_units:
                    self.time_units_combo.set_active(i)
                    break
    
    def _update_progress_display(self):
        """Update progress bar and time display label."""
        if not self.progress_bar or not self.time_display_label:
            return
        
        if self.simulation is None:
            return
        
        settings = self.simulation.settings
        
        # Update progress bar
        if settings.duration:
            progress = self.simulation.get_progress()
            self.progress_bar.set_fraction(min(progress, 1.0))
            self.progress_bar.set_text(f"{int(progress * 100)}%")
            self.progress_bar.set_show_text(True)
        else:
            self.progress_bar.set_fraction(0.0)
            self.progress_bar.set_show_text(False)
        
        # Update time display with speed indicator
        if settings.duration:
            duration_seconds = settings.get_duration_seconds()
            text, _ = TimeFormatter.format_progress(
                self.simulation.time,
                duration_seconds,
                settings.time_units
            )
            
            # Add speed indicator if not 1.0x
            if abs(settings.time_scale - 1.0) > 0.01:
                speed_text = f" @ {settings.time_scale:.1f}x"
            else:
                speed_text = ""
            
            self.time_display_label.set_text(f"Time: {text}{speed_text}")
        else:
            # No duration set, just show current time
            time_text = TimeFormatter.format(
                self.simulation.time,
                TimeUnits.SECONDS,
                include_unit=True
            )
            
            # Add speed indicator if not 1.0x
            if abs(settings.time_scale - 1.0) > 0.01:
                speed_text = f" @ {settings.time_scale:.1f}x"
            else:
                speed_text = ""
            
            self.time_display_label.set_text(f"Time: {time_text}{speed_text}")

    def show(self):
        """Show the tools palette with animation."""
        if self.simulate_tools_revealer:
            self.simulate_tools_revealer.set_reveal_child(True)

    def hide(self):
        """Hide the tools palette with animation."""
        if self.simulate_tools_revealer:
            self.simulate_tools_revealer.set_reveal_child(False)

    def is_visible(self):
        """Check if the tools palette is currently visible.
        
        Returns:
            bool: True if palette is revealed, False otherwise.
        """
        if self.simulate_tools_revealer:
            return self.simulate_tools_revealer.get_reveal_child()
        return False

    def get_widget(self):
        """Get the root widget for adding to container.
        
        Returns the revealer containing the simulation tools palette.
        This maintains proper widget hierarchy and ensures all child widgets
        (including progress bar and time display) are properly visible.
        
        Returns:
            Gtk.Revealer: Revealer containing the tools palette grid.
        """
        return self.widget_container
    
    def create_settings_panel(self):
        """Factory method to create settings panel widget.
        
        PHASE 3: This will be called by the universal parameter panel manager
        to get the settings panel widget for display above the sub-palette.
        
        Returns:
            Gtk.Revealer: Settings panel revealer, or None if not available.
        """
        settings_revealer = getattr(self, 'settings_revealer', None)
        if settings_revealer:
            # Ensure revealer is visible and revealed when parameter panel shows it
            settings_revealer.set_visible(True)
            settings_revealer.set_reveal_child(True)
            # Sync current settings to UI
            self._sync_settings_to_ui()
        return settings_revealer

    def is_simulation_running(self):
        """Check if simulation is currently running.
        
        Returns:
            bool: True if simulation is active, False otherwise.
        """
        if self.simulation is None:
            return False
        return self.simulation.is_running()

def create_simulate_tools_palette(model=None, ui_dir: str=None):
    """Factory function to create a simulate tools palette loader.
    
    Args:
        model: PetriNetModel instance for simulation (optional)
        ui_dir: Directory containing UI files. Defaults to project ui/simulate/.
    
    Returns:
        SimulateToolsPaletteLoader: Configured palette loader instance.
    """
    return SimulateToolsPaletteLoader(model=model, ui_dir=ui_dir)