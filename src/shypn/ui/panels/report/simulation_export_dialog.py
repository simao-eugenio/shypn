#!/usr/bin/env python3
"""Dialog for configuring simulation data export.

Allows user to select export format, data types, and format-specific options.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from typing import Tuple, Optional


class SimulationExportDialog(Gtk.Dialog):
    """Dialog for configuring simulation data export."""
    
    def __init__(self, parent: Optional[Gtk.Window], simulation_data: dict, metadata: dict):
        """Initialize export dialog.
        
        Args:
            parent: Parent window
            simulation_data: Dict with simulation data
            metadata: Metadata dict
        """
        super().__init__(title="Export Simulation Data", transient_for=parent, flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            "Export", Gtk.ResponseType.OK
        )
        
        self.simulation_data = simulation_data
        self.metadata = metadata
        
        self.set_default_size(500, 550)
        self.set_border_width(10)
        
        # Build UI
        content_area = self.get_content_area()
        content_area.set_spacing(12)
        
        self._build_format_section(content_area)
        self._build_data_section(content_area)
        self._build_csv_options_section(content_area)
        self._build_plot_options_section(content_area)
        
        self.show_all()
        
        # Update visibility based on initial format selection
        self._on_format_changed(None)
    
    def _build_format_section(self, container: Gtk.Box):
        """Build format selection section."""
        frame = Gtk.Frame(label="Export Format")
        frame.set_margin_bottom(6)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        
        # Radio buttons for format
        self.format_csv_wide = Gtk.RadioButton(label="CSV (Time Series - Wide Format)")
        self.format_csv_wide.set_tooltip_text("One column per species/reaction - good for Excel")
        vbox.pack_start(self.format_csv_wide, False, False, 0)
        
        self.format_csv_long = Gtk.RadioButton.new_from_widget(self.format_csv_wide)
        self.format_csv_long.set_label("CSV (Time Series - Long/Tidy Format)")
        self.format_csv_long.set_tooltip_text("Entity-Type-Value format - good for R/Python analysis")
        vbox.pack_start(self.format_csv_long, False, False, 0)
        
        self.format_csv_summary = Gtk.RadioButton.new_from_widget(self.format_csv_wide)
        self.format_csv_summary.set_label("CSV (Summary Statistics Only)")
        self.format_csv_summary.set_tooltip_text("Min, Max, Mean, StdDev for each species")
        vbox.pack_start(self.format_csv_summary, False, False, 0)
        
        self.format_json = Gtk.RadioButton.new_from_widget(self.format_csv_wide)
        self.format_json.set_label("JSON (Complete Data with Metadata)")
        self.format_json.set_tooltip_text("Full structured export - good for archival")
        vbox.pack_start(self.format_json, False, False, 0)
        
        self.format_svg = Gtk.RadioButton.new_from_widget(self.format_csv_wide)
        self.format_svg.set_label("SVG (Vector Plot)")
        self.format_svg.set_tooltip_text("Scalable vector graphics - good for publications")
        vbox.pack_start(self.format_svg, False, False, 0)
        
        self.format_png = Gtk.RadioButton.new_from_widget(self.format_csv_wide)
        self.format_png.set_label("PNG (Raster Plot)")
        self.format_png.set_tooltip_text("High-resolution bitmap image")
        vbox.pack_start(self.format_png, False, False, 0)
        
        # Connect signals
        for radio in [self.format_csv_wide, self.format_csv_long, self.format_csv_summary,
                     self.format_json, self.format_svg, self.format_png]:
            radio.connect('toggled', self._on_format_changed)
        
        frame.add(vbox)
        container.pack_start(frame, False, False, 0)
    
    def _build_data_section(self, container: Gtk.Box):
        """Build data inclusion section."""
        frame = Gtk.Frame(label="Include Data")
        frame.set_margin_bottom(6)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        
        self.include_time = Gtk.CheckButton(label="Time points")
        self.include_time.set_active(True)
        vbox.pack_start(self.include_time, False, False, 0)
        
        self.include_places = Gtk.CheckButton(label="Place concentrations (all species)")
        self.include_places.set_active(True)
        vbox.pack_start(self.include_places, False, False, 0)
        
        self.include_transitions = Gtk.CheckButton(label="Transition firing counts (all reactions)")
        self.include_transitions.set_active(True)
        vbox.pack_start(self.include_transitions, False, False, 0)
        
        self.include_metadata = Gtk.CheckButton(label="Simulation metadata and parameters")
        self.include_metadata.set_active(True)
        vbox.pack_start(self.include_metadata, False, False, 0)
        
        self.include_statistics = Gtk.CheckButton(label="Summary statistics")
        self.include_statistics.set_active(False)
        vbox.pack_start(self.include_statistics, False, False, 0)
        
        frame.add(vbox)
        container.pack_start(frame, False, False, 0)
    
    def _build_csv_options_section(self, container: Gtk.Box):
        """Build CSV-specific options."""
        self.csv_frame = Gtk.Frame(label="CSV Options")
        self.csv_frame.set_margin_bottom(6)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        
        label = Gtk.Label(label="(Format determined by selection above)")
        label.set_xalign(0)
        vbox.pack_start(label, False, False, 0)
        
        self.csv_frame.add(vbox)
        container.pack_start(self.csv_frame, False, False, 0)
    
    def _build_plot_options_section(self, container: Gtk.Box):
        """Build plot-specific options."""
        self.plot_frame = Gtk.Frame(label="Plot Options")
        self.plot_frame.set_margin_bottom(6)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        
        self.plot_concentrations = Gtk.CheckButton(label="Concentration curves (places)")
        self.plot_concentrations.set_active(True)
        vbox.pack_start(self.plot_concentrations, False, False, 0)
        
        self.plot_firing_rates = Gtk.CheckButton(label="Firing rate curves (transitions)")
        self.plot_firing_rates.set_active(False)
        vbox.pack_start(self.plot_firing_rates, False, False, 0)
        
        self.plot_combined = Gtk.CheckButton(label="Combined multi-panel plot")
        self.plot_combined.set_active(False)
        vbox.pack_start(self.plot_combined, False, False, 0)
        
        # DPI setting
        dpi_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        dpi_box.set_margin_top(6)
        dpi_label = Gtk.Label(label="Resolution:")
        dpi_box.pack_start(dpi_label, False, False, 0)
        
        self.dpi_spinbutton = Gtk.SpinButton(
            adjustment=Gtk.Adjustment(value=300, lower=72, upper=600, 
                                    step_increment=50, page_increment=100)
        )
        self.dpi_spinbutton.set_digits(0)
        dpi_box.pack_start(self.dpi_spinbutton, False, False, 0)
        
        dpi_unit_label = Gtk.Label(label="DPI")
        dpi_box.pack_start(dpi_unit_label, False, False, 0)
        
        vbox.pack_start(dpi_box, False, False, 0)
        
        self.plot_frame.add(vbox)
        container.pack_start(self.plot_frame, False, False, 0)
    
    def _on_format_changed(self, button):
        """Handle format selection change."""
        # Show/hide relevant options
        is_csv = (self.format_csv_wide.get_active() or 
                 self.format_csv_long.get_active() or
                 self.format_csv_summary.get_active())
        
        is_plot = self.format_svg.get_active() or self.format_png.get_active()
        
        self.csv_frame.set_visible(is_csv)
        self.plot_frame.set_visible(is_plot)
    
    def get_export_config(self) -> dict:
        """Get export configuration from dialog selections.
        
        Returns:
            Dict with export configuration
        """
        # Determine format
        if self.format_csv_wide.get_active():
            format_type = 'csv_timeseries_wide'
            extension = '.csv'
        elif self.format_csv_long.get_active():
            format_type = 'csv_timeseries_long'
            extension = '.csv'
        elif self.format_csv_summary.get_active():
            format_type = 'csv_summary'
            extension = '.csv'
        elif self.format_json.get_active():
            format_type = 'json'
            extension = '.json'
        elif self.format_svg.get_active():
            format_type = 'svg'
            extension = '.svg'
        elif self.format_png.get_active():
            format_type = 'png'
            extension = '.png'
        else:
            format_type = 'csv_timeseries_wide'
            extension = '.csv'
        
        config = {
            'format': format_type,
            'extension': extension,
            'include_time': self.include_time.get_active(),
            'include_places': self.include_places.get_active(),
            'include_transitions': self.include_transitions.get_active(),
            'include_metadata': self.include_metadata.get_active(),
            'include_statistics': self.include_statistics.get_active(),
        }
        
        # Plot-specific options
        if format_type in ['svg', 'png', 'pdf']:
            config['plot_options'] = {
                'dpi': int(self.dpi_spinbutton.get_value()),
                'concentrations': self.plot_concentrations.get_active(),
                'firing_rates': self.plot_firing_rates.get_active(),
                'combined': self.plot_combined.get_active(),
            }
        
        return config
    
    def run(self) -> Tuple[int, dict]:
        """Run dialog and return configuration.
        
        Returns:
            Tuple of (response, config_dict)
        """
        response = super().run()
        config = self.get_export_config() if response == Gtk.ResponseType.OK else {}
        return response, config
