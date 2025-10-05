"""
Simulate Tools Palette Loader

Loads and manages the simulation tools palette UI (Run, Step, Stop, Reset buttons).
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


class SimulateToolsPaletteLoader(GObject.GObject):
    """Loader for simulation tools palette - manages [R][P][S][T] button panel.
    
    This class loads and manages the simulation tools palette UI from
    simulate_tools_palette.ui. The palette contains four buttons:
    - Run [R]: Start continuous simulation execution
    - Step [P]: Execute one simulation step
    - Stop [S]: Pause simulation
    - Reset [T]: Reset to initial marking
    
    The palette directly owns and operates the SimulationController.
    Buttons call controller methods directly (no external wiring needed).
    
    The palette is revealed/hidden by the main simulate button via show()/hide().
    """
    
    __gsignals__ = {
        # Signal emitted after each simulation step (for canvas redraw)
        'step-executed': (GObject.SignalFlags.RUN_FIRST, None, (float,)),  # time
        # Signal emitted when simulation is reset to initial marking
        'reset-executed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, model=None, ui_dir: str = None):
        """Initialize the simulate tools palette loader.
        
        Args:
            model: PetriNetModel instance for simulation (can be set later)
            ui_dir: Directory containing UI files. Defaults to project ui/simulate/.
        """
        super().__init__()
        
        # Determine UI directory
        if ui_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            ui_dir = os.path.join(project_root, 'ui', 'simulate')
        
        self.ui_dir = ui_dir
        self.ui_path = os.path.join(ui_dir, 'simulate_tools_palette.ui')
        
        # Simulation controller
        self.simulation = None
        self._model = model
        
        # Data collector for analysis/plotting
        self.data_collector = SimulationDataCollector()
        
        if model is not None:
            self._init_simulation_controller()
        
        # Widget references
        self.builder = None
        self.simulate_tools_revealer = None  # Revealer container
        self.simulate_tools_container = None
        self.run_button = None
        self.step_button = None
        self.stop_button = None
        self.reset_button = None
        
        # Load UI
        self._load_ui()
    
    def _load_ui(self):
        """Load the simulate tools palette UI from file."""
        # Validate UI file exists
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f"Simulate tools palette UI file not found: {self.ui_path}")
        
        # Load the UI
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        
        # Extract widgets
        self.simulate_tools_revealer = self.builder.get_object('simulate_tools_revealer')
        self.simulate_tools_container = self.builder.get_object('simulate_tools_container')
        self.run_button = self.builder.get_object('run_simulation_button')
        self.step_button = self.builder.get_object('step_simulation_button')
        self.stop_button = self.builder.get_object('stop_simulation_button')
        self.reset_button = self.builder.get_object('reset_simulation_button')
        
        if self.simulate_tools_revealer is None:
            raise ValueError("Object 'simulate_tools_revealer' not found in simulate_tools_palette.ui")
        
        # Verify all buttons exist
        if not all([self.run_button, self.step_button, self.stop_button, self.reset_button]):
            raise ValueError("One or more simulation buttons not found in simulate_tools_palette.ui")
        
        # Connect button signals
        self.run_button.connect('clicked', self._on_run_clicked)
        self.step_button.connect('clicked', self._on_step_clicked)
        self.stop_button.connect('clicked', self._on_stop_clicked)
        self.reset_button.connect('clicked', self._on_reset_clicked)
        
        # Apply custom CSS styling
        self._apply_styling()
        
        print(f"[SimulateToolsPaletteLoader] UI loaded successfully from {self.ui_path}")
    
    def _init_simulation_controller(self):
        """Initialize the simulation controller with the model."""
        if self._model is None:
            return
        
        self.simulation = SimulationController(self._model)
        
        # Attach data collector to controller
        self.simulation.data_collector = self.data_collector
        
        # Register step listener to emit signal for canvas redraw
        self.simulation.add_step_listener(self._on_simulation_step)
        
        # Register data collector as step listener
        self.simulation.add_step_listener(self.data_collector.on_simulation_step)
        
        print("[SimulateToolsPaletteLoader] SimulationController initialized with data collector")
    
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
        
        Args:
            controller: The SimulationController instance
            time: Current simulation time
        """
        # Emit signal so canvas can redraw
        self.emit('step-executed', time)
    
    def _apply_styling(self):
        """Apply custom CSS styling to the simulation tools palette."""
        css = """
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
        """
        
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode())
        
        # Apply to the tools container
        if self.simulate_tools_container:
            style_context = self.simulate_tools_container.get_style_context()
            style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        # Apply to each button
        for button in [self.run_button, self.step_button, self.stop_button, self.reset_button]:
            if button:
                style_context = button.get_style_context()
                style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    
    def _on_run_clicked(self, button):
        """Handle Run button click - start continuous simulation."""
        if self.simulation is None:
            print("[SimulateToolsPaletteLoader] No simulation controller - model not set")
            return
        
        print("[SimulateToolsPaletteLoader] Run clicked")
        
        # Start continuous simulation
        self.simulation.run(time_step=0.1)
        
        # Update button states
        self.run_button.set_sensitive(False)
        self.step_button.set_sensitive(False)
        self.stop_button.set_sensitive(True)
        self.reset_button.set_sensitive(False)
    
    def _on_step_clicked(self, button):
        """Handle Step button click - execute one simulation step."""
        if self.simulation is None:
            print("[SimulateToolsPaletteLoader] No simulation controller - model not set")
            return
        
        print("[SimulateToolsPaletteLoader] Step clicked")
        
        # Execute single step
        success = self.simulation.step(time_step=0.1)
        
        if not success:
            print("[SimulateToolsPaletteLoader] Step failed - no enabled transitions")
    
    def _on_stop_clicked(self, button):
        """Handle Stop button click - pause simulation."""
        if self.simulation is None:
            print("[SimulateToolsPaletteLoader] No simulation controller - model not set")
            return
        
        print("[SimulateToolsPaletteLoader] Stop clicked")
        
        # Stop continuous simulation
        self.simulation.stop()
        
        # Update button states
        self.run_button.set_sensitive(True)
        self.step_button.set_sensitive(True)
        self.stop_button.set_sensitive(False)
        self.reset_button.set_sensitive(True)
    
    def _on_reset_clicked(self, button):
        """Handle Reset button click - reset to initial marking."""
        if self.simulation is None:
            print("[SimulateToolsPaletteLoader] No simulation controller - model not set")
            return
        
        print("[SimulateToolsPaletteLoader] Reset clicked")
        
        # Reset simulation
        self.simulation.reset()
        
        # Emit signal to notify listeners (for plot refresh)
        self.emit('reset-executed')
        
        # Update button states
        self.run_button.set_sensitive(True)
        self.step_button.set_sensitive(True)
        self.stop_button.set_sensitive(False)
        self.reset_button.set_sensitive(True)
    
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


# Factory function for convenience
def create_simulate_tools_palette(model=None, ui_dir: str = None):
    """Factory function to create a simulate tools palette loader.
    
    Args:
        model: PetriNetModel instance for simulation (optional)
        ui_dir: Directory containing UI files. Defaults to project ui/simulate/.
    
    Returns:
        SimulateToolsPaletteLoader: Configured palette loader instance.
    """
    return SimulateToolsPaletteLoader(model=model, ui_dir=ui_dir)
