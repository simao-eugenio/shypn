#!/usr/bin/env python3
"""Simulation control toolbar widget.

Provides UI controls for experiment management and subnet simulation.
Includes experiment snapshots, simulation controls (Run/Step/Pause/Stop),
and settings (time limit, steps, method).

Author: Simão Eugénio
Date: November 13, 2025
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class SimulationControlToolbar(Gtk.Box):
    """Toolbar for experiment management and simulation control."""
    
    def __init__(self):
        """Initialize simulation control toolbar."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        self._build_experiment_row()
        self._build_simulation_row()
        
        # Styling
        self.set_margin_start(10)
        self.set_margin_end(10)
        self.set_margin_top(10)
        self.set_margin_bottom(5)
        
        # Add subtle border
        self.get_style_context().add_class("frame")
    
    def _build_experiment_row(self):
        """Build experiment management row."""
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        row.set_margin_start(5)
        row.set_margin_end(5)
        row.set_margin_top(5)
        
        # Label
        label = Gtk.Label(label="Experiment:")
        label.set_markup("<b>Experiment:</b>")
        row.pack_start(label, False, False, 0)
        
        # Experiment selector combo
        self.experiment_combo = Gtk.ComboBoxText()
        self.experiment_combo.append_text("Current")
        self.experiment_combo.set_active(0)
        self.experiment_combo.set_tooltip_text("Select experiment configuration")
        row.pack_start(self.experiment_combo, False, False, 0)
        
        # Management buttons
        self.add_exp_button = Gtk.Button(label="+ Add")
        self.add_exp_button.set_tooltip_text("Create new experiment from current parameters")
        row.pack_start(self.add_exp_button, False, False, 0)
        
        self.copy_exp_button = Gtk.Button(label="📋 Copy")
        self.copy_exp_button.set_tooltip_text("Duplicate current experiment for variation")
        row.pack_start(self.copy_exp_button, False, False, 0)
        
        self.save_exp_button = Gtk.Button(label="💾 Save")
        self.save_exp_button.set_tooltip_text("Export experiments to JSON file")
        row.pack_start(self.save_exp_button, False, False, 0)
        
        self.load_exp_button = Gtk.Button(label="📂 Load")
        self.load_exp_button.set_tooltip_text("Import experiments from JSON file")
        row.pack_start(self.load_exp_button, False, False, 0)
        
        self.pack_start(row, False, False, 0)
    
    def _build_simulation_row(self):
        """Build simulation controls row."""
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        row.set_margin_start(5)
        row.set_margin_end(5)
        row.set_margin_bottom(5)
        
        # === CONTROL BUTTONS ===
        
        self.run_button = Gtk.Button(label="▶ Run")
        self.run_button.set_tooltip_text("Run simulation to completion (time/step limit)")
        self.run_button.get_style_context().add_class("suggested-action")
        row.pack_start(self.run_button, False, False, 0)
        
        self.step_button = Gtk.Button(label="⏭ Step")
        self.step_button.set_tooltip_text("Execute single firing event")
        row.pack_start(self.step_button, False, False, 0)
        
        self.pause_button = Gtk.Button(label="⏸ Pause")
        self.pause_button.set_tooltip_text("Pause running simulation")
        self.pause_button.set_sensitive(False)
        row.pack_start(self.pause_button, False, False, 0)
        
        self.stop_button = Gtk.Button(label="⏹ Stop")
        self.stop_button.set_tooltip_text("Stop and reset simulation")
        self.stop_button.set_sensitive(False)
        row.pack_start(self.stop_button, False, False, 0)
        
        self.reset_button = Gtk.Button(label="↻ Reset")
        self.reset_button.set_tooltip_text("Reset to initial state")
        row.pack_start(self.reset_button, False, False, 0)
        
        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        row.pack_start(sep, False, False, 5)
        
        # === SETTINGS ===
        
        # Time limit
        row.pack_start(Gtk.Label(label="Time:"), False, False, 0)
        self.time_spinbutton = Gtk.SpinButton(
            adjustment=Gtk.Adjustment(100, 0.1, 10000, 1, 10, 0)
        )
        self.time_spinbutton.set_width_chars(5)
        self.time_spinbutton.set_digits(1)
        self.time_spinbutton.set_tooltip_text("Maximum simulation time (seconds)")
        row.pack_start(self.time_spinbutton, False, False, 0)
        row.pack_start(Gtk.Label(label="s"), False, False, 0)
        
        # Step limit
        row.pack_start(Gtk.Label(label="  Steps:"), False, False, 0)
        self.steps_spinbutton = Gtk.SpinButton(
            adjustment=Gtk.Adjustment(1000, 1, 1000000, 100, 1000, 0)
        )
        self.steps_spinbutton.set_width_chars(6)
        self.steps_spinbutton.set_digits(0)
        self.steps_spinbutton.set_tooltip_text("Maximum firing events")
        row.pack_start(self.steps_spinbutton, False, False, 0)
        
        # Method selector
        row.pack_start(Gtk.Label(label="  Method:"), False, False, 0)
        self.method_combo = Gtk.ComboBoxText()
        self.method_combo.append_text("Gillespie")
        self.method_combo.append_text("ODE")
        self.method_combo.append_text("Hybrid")
        self.method_combo.set_active(0)
        self.method_combo.set_tooltip_text("Simulation algorithm")
        row.pack_start(self.method_combo, False, False, 0)
        
        # === STATUS LABEL ===
        
        self.status_label = Gtk.Label(label="● Ready")
        self.status_label.set_halign(Gtk.Align.END)
        self.status_label.set_margin_start(10)
        row.pack_end(self.status_label, True, True, 0)
        
        self.pack_start(row, False, False, 0)
    
    def set_status(self, text, status_type="ready"):
        """Update status label.
        
        Args:
            text: Status message
            status_type: One of "ready", "running", "paused", "success", "error"
        """
        symbols = {
            "ready": "●",
            "running": "⏵",
            "paused": "⏸",
            "success": "✓",
            "error": "✗"
        }
        
        symbol = symbols.get(status_type, "●")
        self.status_label.set_label(f"{symbol} {text}")
    
    def set_running_state(self, is_running):
        """Update button states for running/stopped.
        
        Args:
            is_running: True if simulation is running
        """
        self.run_button.set_sensitive(not is_running)
        self.step_button.set_sensitive(not is_running)
        self.pause_button.set_sensitive(is_running)
        self.stop_button.set_sensitive(is_running)
        
        # Disable experiment switching during simulation
        self.experiment_combo.set_sensitive(not is_running)
        self.add_exp_button.set_sensitive(not is_running)
        self.copy_exp_button.set_sensitive(not is_running)
        self.save_exp_button.set_sensitive(not is_running)
        self.load_exp_button.set_sensitive(not is_running)
    
    def get_simulation_settings(self):
        """Get current simulation settings.
        
        Returns:
            dict: Settings with 'max_time', 'max_steps', 'method'
        """
        return {
            'max_time': self.time_spinbutton.get_value(),
            'max_steps': int(self.steps_spinbutton.get_value()),
            'method': self.method_combo.get_active_text().lower()
        }
    
    def get_active_experiment_index(self):
        """Get currently selected experiment index.
        
        Returns:
            int: Active experiment index
        """
        return self.experiment_combo.get_active()
    
    def populate_experiment_combo(self, experiment_names):
        """Populate experiment combo with names.
        
        Args:
            experiment_names: List of experiment names
        """
        # Remember current selection
        current_index = self.experiment_combo.get_active()
        
        # Clear and repopulate
        self.experiment_combo.remove_all()
        for name in experiment_names:
            self.experiment_combo.append_text(name)
        
        # Restore selection (or default to 0)
        if current_index >= 0 and current_index < len(experiment_names):
            self.experiment_combo.set_active(current_index)
        elif experiment_names:
            self.experiment_combo.set_active(0)
    
    def add_experiment_to_combo(self, name):
        """Add new experiment to combo and select it.
        
        Args:
            name: Experiment name
        """
        self.experiment_combo.append_text(name)
        # Select newly added item
        self.experiment_combo.set_active(self.experiment_combo.get_model().iter_n_children(None) - 1)
