"""Base Plotting Panel for Simulation Analysis.

This module provides the base AnalysisPlotPanel class that handles:
- Matplotlib canvas integration with GTK3
- Selected objects list display with remove buttons
- Real-time plot updates with throttling
- Abstract methods for subclasses to implement specific plot types

This is a SEPARATE MODULE - not implemented in loaders!
Loaders only instantiate and attach this panel to the UI.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

import matplotlib
matplotlib.use('GTK3Agg')  # Must be before pyplot import
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure

from typing import List, Any, Optional, Tuple


class AnalysisPlotPanel(Gtk.Box):
    """Base class for rate-based analysis plotting panels.
    
    This class provides the common infrastructure for plotting place token rates
    and transition firing rates. It handles:
    - Matplotlib figure and canvas setup
    - Selected objects list display (with remove buttons)
    - Clear selection functionality
    - Throttled plot updates (to avoid overwhelming the UI)
    - Color palette for multiple objects
    
    Subclasses must implement:
    - _get_rate_data(obj_id) -> List[Tuple[float, float]]
    - _get_ylabel() -> str
    - _get_title() -> str
    
    Attributes:
        object_type: Type of objects this panel handles ('place' or 'transition')
        data_collector: SimulationDataCollector instance for accessing raw data
        rate_calculator: RateCalculator instance for computing rates
        selected_objects: List of currently selected objects for plotting
        needs_update: Flag indicating plot needs redrawing
    
    Example:
        # In subclass:
        class PlaceRatePanel(AnalysisPlotPanel):
            def __init__(self, data_collector):
                super().__init__('place', data_collector)
            
            def _get_rate_data(self, place_id):
                # Calculate token rate for this place
                return rate_data
    """
    
    # Color palette for multiple objects (up to 10 distinct colors)
    COLORS = [
        '#e74c3c',  # Red
        '#3498db',  # Blue
        '#2ecc71',  # Green
        '#f39c12',  # Orange
        '#9b59b6',  # Purple
        '#1abc9c',  # Turquoise
        '#e67e22',  # Dark Orange
        '#34495e',  # Dark Gray
        '#16a085',  # Dark Turquoise
        '#c0392b',  # Dark Red
    ]
    
    def __init__(self, object_type: str, data_collector):
        """Initialize the analysis plot panel.
        
        Args:
            object_type: Type of objects ('place' or 'transition')
            data_collector: SimulationDataCollector instance
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        self.object_type = object_type
        self.data_collector = data_collector
        
        # Import here to avoid circular dependency
        from shypn.analyses import RateCalculator
        self.rate_calculator = RateCalculator()
        
        # Selected objects for plotting
        self.selected_objects: List[Any] = []
        
        # Plot update throttling
        self.needs_update = False
        self.update_interval = 100  # milliseconds
        
        # Build UI
        self._setup_ui()
        
        # Start periodic update timer
        GLib.timeout_add(self.update_interval, self._periodic_update)
    
    def _setup_ui(self):
        """Set up the panel UI components."""
        # === Selected Objects List ===
        list_frame = Gtk.Frame(label=f"Selected {self.object_type.title()}s")
        list_frame.set_margin_start(6)
        list_frame.set_margin_end(6)
        list_frame.set_margin_top(6)
        
        list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        list_box.set_margin_start(6)
        list_box.set_margin_end(6)
        list_box.set_margin_top(6)
        list_box.set_margin_bottom(6)
        
        # Scrolled window for object list
        list_scroll = Gtk.ScrolledWindow()
        list_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        list_scroll.set_min_content_height(80)
        list_scroll.set_max_content_height(150)
        
        self.objects_listbox = Gtk.ListBox()
        self.objects_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        list_scroll.add(self.objects_listbox)
        
        list_box.pack_start(list_scroll, True, True, 0)
        
        # Clear button
        clear_btn = Gtk.Button(label="Clear Selection")
        clear_btn.connect('clicked', self._on_clear_clicked)
        list_box.pack_start(clear_btn, False, False, 0)
        
        list_frame.add(list_box)
        self.pack_start(list_frame, False, False, 0)
        
        # === Matplotlib Canvas ===
        self.figure = Figure(figsize=(6, 4), dpi=80)
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.set_size_request(400, 300)
        
        # Tight layout to avoid label cutoff
        self.figure.tight_layout()
        
        self.pack_start(self.canvas, True, True, 0)
        
        # Initial plot (empty state)
        self._show_empty_state()
        
        self.show_all()
    
    def add_object(self, obj: Any):
        """Add an object to the selected list for plotting.
        
        Args:
            obj: Place or Transition object to add
        """
        # Avoid duplicates
        if any(o.id == obj.id for o in self.selected_objects):
            print(f"[{self.__class__.__name__}] Object {obj.id} already selected")
            return
        
        self.selected_objects.append(obj)
        self._update_objects_list()
        self.needs_update = True
        
        print(f"[{self.__class__.__name__}] Added {self.object_type} {obj.id} to analysis")
    
    def remove_object(self, obj: Any):
        """Remove an object from the selected list.
        
        Args:
            obj: Place or Transition object to remove
        """
        self.selected_objects = [o for o in self.selected_objects if o.id != obj.id]
        self._update_objects_list()
        self.needs_update = True
        
        print(f"[{self.__class__.__name__}] Removed {self.object_type} {obj.id} from analysis")
    
    def _update_objects_list(self):
        """Update the UI list of selected objects."""
        # Clear existing list
        for child in self.objects_listbox.get_children():
            self.objects_listbox.remove(child)
        
        # Add rows for each selected object
        if not self.selected_objects:
            # Show empty message
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label="No objects selected")
            label.get_style_context().add_class('dim-label')
            row.add(label)
            self.objects_listbox.add(row)
        else:
            for i, obj in enumerate(self.selected_objects):
                row = Gtk.ListBoxRow()
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                hbox.set_margin_start(6)
                hbox.set_margin_end(6)
                hbox.set_margin_top(3)
                hbox.set_margin_bottom(3)
                
                # Color indicator
                color_box = Gtk.DrawingArea()
                color_box.set_size_request(20, 20)
                color = self._get_color(i)
                color_box.connect('draw', self._draw_color_box, color)
                hbox.pack_start(color_box, False, False, 0)
                
                # Object label
                obj_name = getattr(obj, 'name', f'{self.object_type.title()}{obj.id}')
                label = Gtk.Label(label=f"{obj_name} ({self.object_type[0].upper()}{obj.id})")
                label.set_xalign(0)
                hbox.pack_start(label, True, True, 0)
                
                # Remove button
                remove_btn = Gtk.Button(label="✕")
                remove_btn.set_relief(Gtk.ReliefStyle.NONE)
                remove_btn.connect('clicked', self._on_remove_clicked, obj)
                hbox.pack_start(remove_btn, False, False, 0)
                
                row.add(hbox)
                self.objects_listbox.add(row)
        
        self.objects_listbox.show_all()
    
    def _draw_color_box(self, widget, cr, color):
        """Draw a colored box for object identification.
        
        Args:
            widget: DrawingArea widget
            cr: Cairo context
            color: Hex color string
        """
        # Parse hex color
        r = int(color[1:3], 16) / 255.0
        g = int(color[3:5], 16) / 255.0
        b = int(color[5:7], 16) / 255.0
        
        # Draw filled rectangle
        cr.set_source_rgb(r, g, b)
        cr.rectangle(0, 0, 20, 20)
        cr.fill()
        
        # Draw border
        cr.set_source_rgb(0.5, 0.5, 0.5)
        cr.set_line_width(1)
        cr.rectangle(0, 0, 20, 20)
        cr.stroke()
    
    def _on_remove_clicked(self, button, obj):
        """Handle remove button click.
        
        Args:
            button: Button that was clicked
            obj: Object to remove
        """
        self.remove_object(obj)
    
    def _on_clear_clicked(self, button):
        """Handle clear button click."""
        self.selected_objects.clear()
        self._update_objects_list()
        self.needs_update = True
        print(f"[{self.__class__.__name__}] Cleared all selections")
    
    def _periodic_update(self) -> bool:
        """Periodic callback to update plot if needed.
        
        Returns:
            bool: True to continue periodic calls
        """
        if self.needs_update:
            self.update_plot()
            self.needs_update = False
        
        return True  # Continue calling
    
    def update_plot(self):
        """Update the plot with current data.
        
        This is the main plotting method that subclasses should call
        or override to customize plotting behavior.
        """
        self.axes.clear()
        
        if not self.selected_objects:
            self._show_empty_state()
            return
        
        # Plot rate for each selected object
        for i, obj in enumerate(self.selected_objects):
            rate_data = self._get_rate_data(obj.id)
            
            if rate_data:
                times = [t for t, r in rate_data]
                rates = [r for t, r in rate_data]
                
                color = self._get_color(i)
                obj_name = getattr(obj, 'name', f'{self.object_type.title()}{obj.id}')
                
                self.axes.plot(times, rates,
                              label=f'{obj_name} ({self.object_type[0].upper()}{obj.id})',
                              color=color,
                              linewidth=2)
        
        self._format_plot()
        self.canvas.draw()
    
    def _show_empty_state(self):
        """Show empty state message when no objects selected."""
        self.axes.text(0.5, 0.5, 
                      f'No {self.object_type}s selected\nAdd {self.object_type}s to analyze',
                      ha='center', va='center',
                      transform=self.axes.transAxes,
                      fontsize=12, color='gray')
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        self.canvas.draw()
    
    def _format_plot(self):
        """Format the plot with labels, grid, and legend."""
        self.axes.set_xlabel('Time (s)', fontsize=11)
        self.axes.set_ylabel(self._get_ylabel(), fontsize=11)
        self.axes.set_title(self._get_title(), fontsize=12, fontweight='bold')
        
        if self.selected_objects:
            self.axes.legend(loc='best', fontsize=9)
        
        self.axes.grid(True, alpha=0.3, linestyle='--')
        
        # Add zero line for place panels (consumption vs production)
        if self.object_type == 'place':
            self.axes.axhline(y=0, color='gray', linestyle='-', 
                            linewidth=0.8, alpha=0.5)
        
        self.figure.tight_layout()
    
    def _get_color(self, index: int) -> str:
        """Get color for object at index.
        
        Args:
            index: Index of object in selected list
            
        Returns:
            str: Hex color code
        """
        return self.COLORS[index % len(self.COLORS)]
    
    def on_simulation_step(self, controller, time: float):
        """Called when simulation advances (step listener).
        
        Args:
            controller: SimulationController instance
            time: Current simulation time
        """
        # Mark that plot needs updating
        self.needs_update = True
    
    # === Abstract methods for subclasses ===
    
    def _get_rate_data(self, obj_id: Any) -> List[Tuple[float, float]]:
        """Get rate data for an object.
        
        Subclasses must implement this to return rate time series.
        
        Args:
            obj_id: ID of the object
            
        Returns:
            List of (time, rate) tuples
        """
        raise NotImplementedError("Subclasses must implement _get_rate_data()")
    
    def _get_ylabel(self) -> str:
        """Get Y-axis label.
        
        Returns:
            str: Y-axis label text
        """
        raise NotImplementedError("Subclasses must implement _get_ylabel()")
    
    def _get_title(self) -> str:
        """Get plot title.
        
        Returns:
            str: Plot title text
        """
        raise NotImplementedError("Subclasses must implement _get_title()")
