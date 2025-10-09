"""
Simulate Tools Palette Loader

Loads and manages the simulation tools palette UI (Run, Step, Stop, Reset, Settings buttons).
This palette appears below the main [S] simulate button when toggled.

The palette directly manages the SimulationController - buttons call controller
methods directly rather than emitting signals for external handling.
"""
import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
from shypn.engine.simulation import SimulationController
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
    """
    __gsignals__ = {
        'step-executed': (GObject.SignalFlags.RUN_FIRST, None, (float,)),
        'reset-executed': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'settings-changed': (GObject.SignalFlags.RUN_FIRST, None, ())
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
        self.simulation = None
        self._model = model
        self.data_collector = SimulationDataCollector()
        if model is not None:
            self._init_simulation_controller()
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

    def _init_simulation_controller(self):
        """Initialize the simulation controller with the model."""
        if self._model is None:
            return
        self.simulation = SimulationController(self._model)
        self.simulation.data_collector = self.data_collector
        self.simulation.add_step_listener(self._on_simulation_step)
        self.simulation.add_step_listener(self.data_collector.on_simulation_step)

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
            color: white;
            font-size: 11px;
            font-weight: bold;
        }
        
        .sim-control-entry {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid #34495e;
            border-radius: 3px;
            font-size: 11px;
            padding: 2px 4px;
            min-width: 60px;
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
            color: white;
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
        
        # Use effective dt from settings (no hardcoded time_step)
        self.simulation.run()
        
        # Update button states for running simulation
        self._update_button_states(running=True)

    def _on_step_clicked(self, button):
        """Handle Step button click - execute one simulation step."""
        if self.simulation is None:
            return
        
        # Use effective dt from settings (no hardcoded time_step)
        success = self.simulation.step()
        
        # If step failed or simulation completed, update button states
        if not success or self.simulation.is_simulation_complete():
            self._update_button_states(running=False, completed=True)

    def _on_stop_clicked(self, button):
        """Handle Stop button click - pause simulation."""
        if self.simulation is None:
            return
        
        self.simulation.stop()
        
        # Update button states for stopped/paused simulation
        self._update_button_states(running=False)

    def _on_reset_clicked(self, button):
        """Handle Reset button click - reset to initial marking."""
        if self.simulation is None:
            return
        
        self.simulation.reset()
        self.emit('reset-executed')
        self._update_progress_display()  # Reset progress bar
        
        # Update button states for reset simulation
        self._update_button_states(running=False, reset=True)
    
    def _on_settings_clicked(self, button):
        """Handle Settings dialog click - open simulation settings dialog."""
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
            
            # Show dialog and apply settings
            if show_simulation_settings_dialog(self.simulation.settings, parent):
                # Settings updated successfully
                # Update duration display to reflect any changes
                self._update_duration_display()
                # Reset progress if duration changed
                self._update_progress_display()
                
                # Emit signal for data collector/matplotlib updates
                self.emit('settings-changed')
                
                # Notify user if simulation was running
                if was_running:
                    print("⚠️  Simulation was paused to change settings. Click Run to resume.")
        except Exception as e:
            print(f"❌ Error opening settings dialog: {e}")
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
                
                # Log the change for user feedback
                if old_duration:
                    print(f"⏱️  Duration updated: {duration} {units.abbreviation} (was {old_duration:.1f}s)")
                    
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
        
        # Update time display
        if settings.duration:
            duration_seconds = settings.get_duration_seconds()
            text, _ = TimeFormatter.format_progress(
                self.simulation.time,
                duration_seconds,
                settings.time_units
            )
            self.time_display_label.set_text(f"Time: {text}")
        else:
            # No duration set, just show current time
            time_text = TimeFormatter.format(
                self.simulation.time,
                TimeUnits.SECONDS,
                include_unit=True
            )
            self.time_display_label.set_text(f"Time: {time_text}")

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
        
        Returns:
            Gtk.Widget: The revealer widget containing the tools palette.
        """
        return self.simulate_tools_revealer

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