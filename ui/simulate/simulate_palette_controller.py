#!/usr/bin/env python3
"""Simulation Palette Controller.

Manages the simulation palette UI with Run, Stop, and Reset buttons.
Similar to edit palette but for simulation mode.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os


class SimulatePaletteController:
    """Controller for the simulation palette.
    
    Provides simulation controls: Run, Stop, Reset.
    Located beside edit palette at bottom center of canvas.
    """
    
    def __init__(self, overlay_container, manager):
        """Initialize simulation palette controller.
        
        Args:
            overlay_container: GTK overlay to add palette to
            manager: Canvas manager instance
        """
        self.overlay = overlay_container
        self.manager = manager
        
        # State
        self._simulation_running = False
        self._initial_marking = None  # Store for reset
        
        # Load UI files
        self._load_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Add to overlay
        self._add_to_overlay()
    
    def _load_ui(self):
        """Load GTK UI definition files."""
        ui_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'ui', 'simulate')
        
        # Load main palette (S button)
        palette_builder = Gtk.Builder()
        palette_path = os.path.join(ui_dir, 'simulate_palette.ui')
        palette_builder.add_from_file(palette_path)
        self.palette_container = palette_builder.get_object('simulate_palette_container')
        self.simulate_toggle = palette_builder.get_object('simulate_toggle_button')
        
        # Load tools palette (R, S, T buttons)
        tools_builder = Gtk.Builder()
        tools_path = os.path.join(ui_dir, 'simulate_tools_palette.ui')
        tools_builder.add_from_file(tools_path)
        self.tools_revealer = tools_builder.get_object('simulate_tools_revealer')
        self.run_button = tools_builder.get_object('run_simulation_button')
        self.stop_button = tools_builder.get_object('stop_simulation_button')
        self.reset_button = tools_builder.get_object('reset_simulation_button')
    
    def _connect_signals(self):
        """Connect button signals to handlers."""
        # Toggle button - show/hide tools
        self.simulate_toggle.connect('toggled', self._on_simulate_toggle)
        
        # Tool buttons
        self.run_button.connect('clicked', self._on_run_clicked)
        self.stop_button.connect('clicked', self._on_stop_clicked)
        self.reset_button.connect('clicked', self._on_reset_clicked)
    
    def _add_to_overlay(self):
        """Add palette widgets to overlay."""
        # Add main palette button
        self.overlay.add_overlay(self.palette_container)
        
        # Add tools revealer
        self.overlay.add_overlay(self.tools_revealer)
    
    # ============================================================================
    # Signal Handlers
    # ============================================================================
    
    def _on_simulate_toggle(self, toggle_button):
        """Handle simulate toggle button clicked.
        
        Shows/hides the simulation tools palette.
        """
        active = toggle_button.get_active()
        self.tools_revealer.set_reveal_child(active)
        
        if active:
            print("[Simulate] Tools palette opened")
        else:
            print("[Simulate] Tools palette closed")
    
    def _on_run_clicked(self, button):
        """Handle Run button clicked.
        
        Starts the simulation execution.
        """
        if self._simulation_running:
            print("[Simulate] Already running")
            return
        
        print("[Simulate] Run - Starting simulation")
        self._simulation_running = True
        
        # Store initial marking for reset
        if self._initial_marking is None:
            self._initial_marking = self._capture_current_marking()
        
        # Update button states
        self.run_button.set_sensitive(False)
        self.stop_button.set_sensitive(True)
        
        # TODO: Start simulation engine
        # self.manager.simulation_engine.start()
        
        print("[Simulate] Simulation started")
    
    def _on_stop_clicked(self, button):
        """Handle Stop button clicked.
        
        Stops/pauses the simulation execution.
        """
        if not self._simulation_running:
            print("[Simulate] Not running")
            return
        
        print("[Simulate] Stop - Pausing simulation")
        self._simulation_running = False
        
        # Update button states
        self.run_button.set_sensitive(True)
        self.stop_button.set_sensitive(False)
        
        # TODO: Stop simulation engine
        # self.manager.simulation_engine.stop()
        
        print("[Simulate] Simulation stopped")
    
    def _on_reset_clicked(self, button):
        """Handle Reset button clicked.
        
        Resets the simulation to initial marking.
        """
        print("[Simulate] Reset - Restoring initial marking")
        
        # Stop if running
        if self._simulation_running:
            self._on_stop_clicked(button)
        
        # Restore initial marking
        if self._initial_marking is not None:
            self._restore_marking(self._initial_marking)
            print(f"[Simulate] Restored {len(self._initial_marking)} place markings")
        
        # Clear stored marking
        self._initial_marking = None
        
        # TODO: Reset simulation engine
        # self.manager.simulation_engine.reset()
        
        print("[Simulate] Simulation reset")
    
    # ============================================================================
    # State Management
    # ============================================================================
    
    def _capture_current_marking(self):
        """Capture current marking of all places.
        
        Returns:
            dict: Place ID → token count mapping
        """
        marking = {}
        for place in self.manager.places:
            marking[place.id] = place.tokens
        return marking
    
    def _restore_marking(self, marking):
        """Restore marking from saved state.
        
        Args:
            marking: Place ID → token count mapping
        """
        for place in self.manager.places:
            if place.id in marking:
                place.tokens = marking[place.id]
        
        # Redraw canvas
        # TODO: Trigger canvas redraw
        # self.manager.queue_redraw()
    
    # ============================================================================
    # Public Interface
    # ============================================================================
    
    def is_simulation_running(self):
        """Check if simulation is currently running.
        
        Returns:
            bool: True if running, False otherwise
        """
        return self._simulation_running
    
    def show(self):
        """Show the simulation palette."""
        self.palette_container.show()
        self.tools_revealer.show()
    
    def hide(self):
        """Hide the simulation palette."""
        self.palette_container.hide()
        self.tools_revealer.hide()
    
    def cleanup(self):
        """Cleanup resources."""
        # Stop simulation if running
        if self._simulation_running:
            self._simulation_running = False
        
        # Clear stored state
        self._initial_marking = None


# ============================================================================
# Integration Example
# ============================================================================

def integrate_simulation_palette(overlay, manager):
    """Integration helper for adding simulation palette to main window.
    
    Args:
        overlay: GTK overlay container
        manager: Canvas manager instance
        
    Returns:
        SimulatePaletteController: The palette controller instance
    
    Example:
        # In main window setup:
        simulate_palette = integrate_simulation_palette(
            self.canvas_overlay,
            self.canvas_manager
        )
        
        # Access later:
        if simulate_palette.is_simulation_running():
            print("Simulation active!")
    """
    palette = SimulatePaletteController(overlay, manager)
    return palette
