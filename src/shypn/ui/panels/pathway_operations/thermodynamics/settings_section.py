"""Settings section for thermodynamic parameters.

Provides UI for configuring pH, temperature, ionic strength, and tolerance.
Includes preset selector for common organisms/conditions.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import logging

from .base_section import ThermodynamicsSectionBase


logger = logging.getLogger(__name__)


class SettingsSection(ThermodynamicsSectionBase):
    """Thermodynamic settings configuration section.
    
    Provides:
    - Preset selector (E. coli, human, thermophile, etc.)
    - pH slider/entry
    - Temperature slider/entry
    - Ionic strength entry
    - Tolerance slider
    - Enable/disable validation toggle
    """
    
    def __init__(self, model_canvas=None):
        """Initialize settings section.
        
        Args:
            model_canvas: ModelCanvasManager instance (optional)
        """
        super().__init__(model_canvas)
        
        # Widgets (created in build_widget)
        self.preset_combo = None
        self.ph_scale = None
        self.ph_entry = None
        self.temp_scale = None
        self.temp_entry = None
        self.ionic_entry = None
        self.tolerance_scale = None
        self.tolerance_label = None
        self.enable_check = None
        
        # Block signal handlers during refresh
        self._refreshing = False
    
    def build_widget(self) -> Gtk.Widget:
        """Build settings section widget.
        
        Returns:
            Gtk.Frame: Settings configuration frame
        """
        frame = Gtk.Frame()
        frame.set_label("Thermodynamic Settings")
        frame.set_margin_top(6)
        frame.set_margin_bottom(6)
        
        grid = Gtk.Grid()
        grid.set_row_spacing(8)
        grid.set_column_spacing(12)
        grid.set_margin_start(12)
        grid.set_margin_end(12)
        grid.set_margin_top(12)
        grid.set_margin_bottom(12)
        
        row = 0
        
        # Preset selector
        label = Gtk.Label(label="Preset:")
        label.set_halign(Gtk.Align.START)
        grid.attach(label, 0, row, 1, 1)
        
        self.preset_combo = Gtk.ComboBoxText()
        self.preset_combo.append("biochemical_standard", "Biochemical Standard (pH 7.0, 25°C)")
        self.preset_combo.append("e_coli_cytoplasm", "E. coli Cytoplasm (pH 7.4, 37°C)")
        self.preset_combo.append("human_blood", "Human Blood (pH 7.4, 37°C)")
        self.preset_combo.append("thermophile", "Thermophile (pH 7.0, 80°C)")
        self.preset_combo.append("acidophile", "Acidophile (pH 3.0, 25°C)")
        self.preset_combo.append("alkaliphile", "Alkaliphile (pH 10.0, 25°C)")
        self.preset_combo.append("custom", "Custom")
        self.preset_combo.set_active_id("biochemical_standard")
        self.preset_combo.connect("changed", self._on_preset_changed)
        grid.attach(self.preset_combo, 1, row, 2, 1)
        row += 1
        
        # pH control
        label = Gtk.Label(label="pH:")
        label.set_halign(Gtk.Align.START)
        grid.attach(label, 0, row, 1, 1)
        
        self.ph_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 14.0, 0.1)
        self.ph_scale.set_value(7.0)
        self.ph_scale.set_hexpand(True)
        self.ph_scale.connect("value-changed", self._on_ph_changed)
        grid.attach(self.ph_scale, 1, row, 1, 1)
        
        self.ph_entry = Gtk.Entry()
        self.ph_entry.set_text("7.0")
        self.ph_entry.set_width_chars(5)
        self.ph_entry.connect("activate", self._on_ph_entry_activate)
        grid.attach(self.ph_entry, 2, row, 1, 1)
        row += 1
        
        # Temperature control (in Kelvin)
        label = Gtk.Label(label="Temperature (K):")
        label.set_halign(Gtk.Align.START)
        grid.attach(label, 0, row, 1, 1)
        
        self.temp_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 273.15, 373.15, 1.0)
        self.temp_scale.set_value(298.15)
        self.temp_scale.set_hexpand(True)
        self.temp_scale.connect("value-changed", self._on_temp_changed)
        grid.attach(self.temp_scale, 1, row, 1, 1)
        
        self.temp_entry = Gtk.Entry()
        self.temp_entry.set_text("298.15")
        self.temp_entry.set_width_chars(7)
        self.temp_entry.connect("activate", self._on_temp_entry_activate)
        grid.attach(self.temp_entry, 2, row, 1, 1)
        
        # Add Celsius helper label
        temp_celsius_label = Gtk.Label(label="(25°C)")
        temp_celsius_label.set_halign(Gtk.Align.START)
        temp_celsius_label.get_style_context().add_class("dim-label")
        grid.attach(temp_celsius_label, 3, row, 1, 1)
        self.temp_celsius_label = temp_celsius_label
        row += 1
        
        # Ionic strength
        label = Gtk.Label(label="Ionic Strength (M):")
        label.set_halign(Gtk.Align.START)
        grid.attach(label, 0, row, 1, 1)
        
        self.ionic_entry = Gtk.Entry()
        self.ionic_entry.set_text("0.1")
        self.ionic_entry.set_width_chars(7)
        self.ionic_entry.connect("activate", self._on_ionic_changed)
        grid.attach(self.ionic_entry, 1, row, 1, 1)
        row += 1
        
        # Tolerance
        label = Gtk.Label(label="Tolerance:")
        label.set_halign(Gtk.Align.START)
        grid.attach(label, 0, row, 1, 1)
        
        self.tolerance_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 1.0, 0.05)
        self.tolerance_scale.set_value(0.5)
        self.tolerance_scale.set_hexpand(True)
        self.tolerance_scale.connect("value-changed", self._on_tolerance_changed)
        grid.attach(self.tolerance_scale, 1, row, 1, 1)
        
        self.tolerance_label = Gtk.Label(label="±50% (≈±1 order of magnitude)")
        self.tolerance_label.set_halign(Gtk.Align.START)
        grid.attach(self.tolerance_label, 2, row, 2, 1)
        row += 1
        
        # Enable validation checkbox
        self.enable_check = Gtk.CheckButton(label="Enable thermodynamic validation")
        self.enable_check.set_active(True)
        self.enable_check.connect("toggled", self._on_enable_toggled)
        grid.attach(self.enable_check, 0, row, 3, 1)
        row += 1
        
        # Apply button
        apply_button = Gtk.Button(label="Apply Settings")
        apply_button.connect("clicked", self._on_apply_clicked)
        grid.attach(apply_button, 0, row, 3, 1)
        
        frame.add(grid)
        return frame
    
    def refresh_data(self):
        """Refresh settings from document."""
        # Get current document from canvas manager
        manager = self._get_canvas_manager()
        if not manager or not hasattr(manager, 'document'):
            return
        
        document = manager.document
        if not document:
            return
        
        # Update cached document reference
        self.document = document
        
        self._refreshing = True
        
        try:
            settings = document.thermodynamic_settings
            
            # Update preset
            preset = settings.get('preset', 'custom')
            self.preset_combo.set_active_id(preset)
            
            # Update pH
            ph = settings.get('ph', 7.0)
            self.ph_scale.set_value(ph)
            self.ph_entry.set_text(f"{ph:.1f}")
            
            # Update temperature
            temp = settings.get('temperature', 298.15)
            self.temp_scale.set_value(temp)
            self.temp_entry.set_text(f"{temp:.2f}")
            self._update_celsius_label(temp)
            
            # Update ionic strength
            ionic = settings.get('ionic_strength', 0.1)
            self.ionic_entry.set_text(f"{ionic:.2f}")
            
            # Update tolerance
            tolerance = settings.get('tolerance', 0.5)
            self.tolerance_scale.set_value(tolerance)
            self._update_tolerance_label(tolerance)
            
            # Update enable checkbox
            enable = settings.get('enable_validation', True)
            self.enable_check.set_active(enable)
            
        finally:
            self._refreshing = False
    
    def save_to_document(self):
        """Save settings to document."""
        if not self.document:
            return
        
        ph = self.ph_scale.get_value()
        temp = self.temp_scale.get_value()
        ionic = float(self.ionic_entry.get_text())
        tolerance = self.tolerance_scale.get_value()
        enable = self.enable_check.get_active()
        preset = self.preset_combo.get_active_id()
        
        self.document.update_thermodynamic_settings(
            ph=ph,
            temperature=temp,
            ionic_strength=ionic,
            tolerance=tolerance,
            enable_validation=enable,
            preset=preset
        )
        
        logger.info(f"Thermodynamic settings updated: pH={ph:.1f}, T={temp:.1f}K, preset={preset}")
    
    def _on_preset_changed(self, combo):
        """Handle preset selection."""
        if self._refreshing or not self.document:
            return
        
        preset_id = combo.get_active_id()
        
        if preset_id == "custom":
            return  # User is customizing, don't overwrite
        
        # Apply preset
        try:
            self.document.set_thermodynamic_preset(preset_id)
            self.refresh_data()
            logger.info(f"Applied thermodynamic preset: {preset_id}")
        except ValueError as e:
            self._show_error(f"Invalid preset: {e}")
    
    def _on_ph_changed(self, scale):
        """Handle pH slider change."""
        if self._refreshing:
            return
        ph = scale.get_value()
        self.ph_entry.set_text(f"{ph:.1f}")
        self._mark_as_custom()
    
    def _on_ph_entry_activate(self, entry):
        """Handle pH entry activation."""
        try:
            ph = float(entry.get_text())
            if 0.0 <= ph <= 14.0:
                self.ph_scale.set_value(ph)
                self._mark_as_custom()
            else:
                self._show_error("pH must be between 0.0 and 14.0")
                self.ph_entry.set_text(f"{self.ph_scale.get_value():.1f}")
        except ValueError:
            self._show_error("Invalid pH value")
            self.ph_entry.set_text(f"{self.ph_scale.get_value():.1f}")
    
    def _on_temp_changed(self, scale):
        """Handle temperature slider change."""
        if self._refreshing:
            return
        temp = scale.get_value()
        self.temp_entry.set_text(f"{temp:.2f}")
        self._update_celsius_label(temp)
        self._mark_as_custom()
    
    def _on_temp_entry_activate(self, entry):
        """Handle temperature entry activation."""
        try:
            temp = float(entry.get_text())
            if 273.15 <= temp <= 373.15:
                self.temp_scale.set_value(temp)
                self._update_celsius_label(temp)
                self._mark_as_custom()
            else:
                self._show_error("Temperature must be between 273.15K and 373.15K")
                self.temp_entry.set_text(f"{self.temp_scale.get_value():.2f}")
        except ValueError:
            self._show_error("Invalid temperature value")
            self.temp_entry.set_text(f"{self.temp_scale.get_value():.2f}")
    
    def _on_ionic_changed(self, entry):
        """Handle ionic strength entry activation."""
        try:
            ionic = float(entry.get_text())
            if ionic >= 0:
                self._mark_as_custom()
            else:
                self._show_error("Ionic strength must be non-negative")
        except ValueError:
            self._show_error("Invalid ionic strength value")
            if self.document:
                self.ionic_entry.set_text(f"{self.document.thermodynamic_settings.get('ionic_strength', 0.1):.2f}")
    
    def _on_tolerance_changed(self, scale):
        """Handle tolerance slider change."""
        if self._refreshing:
            return
        tolerance = scale.get_value()
        self._update_tolerance_label(tolerance)
        self._mark_as_custom()
    
    def _on_enable_toggled(self, check):
        """Handle enable validation toggle."""
        if self._refreshing:
            return
        self._mark_as_custom()
    
    def _on_apply_clicked(self, button):
        """Handle apply button click."""
        # Ensure document is available
        manager = self._get_canvas_manager()
        if not manager or not hasattr(manager, 'document') or not manager.document:
            self._show_error("No document loaded")
            return
        
        self.document = manager.document
        self.save_to_document()
        self._show_info("Thermodynamic settings applied")
    
    def _update_celsius_label(self, kelvin: float):
        """Update Celsius helper label."""
        celsius = kelvin - 273.15
        self.temp_celsius_label.set_text(f"({celsius:.0f}°C)")
    
    def _update_tolerance_label(self, tolerance: float):
        """Update tolerance description label."""
        percent = tolerance * 100
        orders = tolerance * 2  # Rough approximation
        self.tolerance_label.set_text(f"±{percent:.0f}% (≈±{orders:.1f} orders of magnitude)")
    
    def _mark_as_custom(self):
        """Mark preset as custom when user modifies values."""
        if not self._refreshing:
            self.preset_combo.set_active_id("custom")
