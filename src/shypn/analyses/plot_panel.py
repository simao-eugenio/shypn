"""Base Plotting Panel for Simulation Analysis.

This module provides the base AnalysisPlotPanel class that handles:
    pass
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
matplotlib.use('GTK3Agg')
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure
from typing import List, Any, Optional, Tuple

class AnalysisPlotPanel(Gtk.Box):
    """Base class for rate-based analysis plotting panels.
    
    This class provides the common infrastructure for plotting place token rates
    and transition firing rates. It handles:
        pass
    - Matplotlib figure and canvas setup
    - Selected objects list display (with remove buttons)
    - Clear selection functionality
    - Throttled plot updates (to avoid overwhelming the UI)
    - Color palette for multiple objects
    
    Subclasses must implement:
        pass
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
    COLORS = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e', '#16a085', '#c0392b']

    def __init__(self, object_type: str, data_collector):
        """Initialize the analysis plot panel.
        
        Args:
            object_type: Type of objects ('place' or 'transition')
            data_collector: SimulationDataCollector instance
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.object_type = object_type
        self.data_collector = data_collector
        from shypn.analyses import RateCalculator
        self.rate_calculator = RateCalculator()
        self.selected_objects: List[Any] = []
        self.needs_update = False
        self.update_interval = 250  # Increased from 100ms to 250ms for better performance
        self.last_data_length = {}
        self._model_manager = None  # Will be set by register_with_model()
        self._plot_lines = {}  # Cache matplotlib line objects for efficient updates
        self._setup_ui()
        GLib.timeout_add(self.update_interval, self._periodic_update)
        # Periodic cleanup of stale objects (safety net)
        GLib.timeout_add(5000, self._cleanup_stale_objects)

    def register_with_model(self, model_manager):
        """Register this panel to observe model changes.
        
        Args:
            model_manager: ModelCanvasManager instance to observe
        """
        if self._model_manager is not None:
            # Unregister from previous manager
            self._model_manager.unregister_observer(self._on_model_changed)
        
        self._model_manager = model_manager
        if model_manager is not None:
            model_manager.register_observer(self._on_model_changed)

    def _on_model_changed(self, event_type: str, obj, old_value=None, new_value=None):
        """Handle model change notifications.
        
        Args:
            event_type: 'created' | 'deleted' | 'modified' | 'transformed'
            obj: The affected object (Place, Transition, or Arc)
            old_value: Previous value (for transformed events)
            new_value: New value (for transformed events)
        """
        if event_type == 'deleted':
            # Remove deleted object from selection if present
            self._remove_if_selected(obj)

    def _remove_if_selected(self, obj):
        """Remove object from selection if it's currently selected.
        
        Args:
            obj: Object to remove from selection
        """
        # Check if object is in our selection
        before_count = len(self.selected_objects)
        self.selected_objects = [o for o in self.selected_objects 
                                if o is not obj and o.id != obj.id]
        
        # If we removed something, trigger full UI update
        if len(self.selected_objects) < before_count:
            self._update_objects_list()
            self.needs_update = True

    def _cleanup_stale_objects(self):
        """Periodic cleanup of stale object references (safety net).
        
        This method runs periodically to catch any objects that were deleted
        but not properly removed from selection. This is a safety net in case
        the observer pattern fails for any reason.
        
        Returns:
            True to continue periodic callbacks
        """
        if self._model_manager is None:
            return True
        
        # Get valid object IDs from model
        if self.object_type == 'place':
            valid_ids = {p.id for p in self._model_manager.places}
        else:  # transition
            valid_ids = {t.id for t in self._model_manager.transitions}
        
        # Remove objects with invalid IDs
        before_count = len(self.selected_objects)
        self.selected_objects = [o for o in self.selected_objects 
                                if o.id in valid_ids]
        
        # If we removed something, trigger full UI update
        if len(self.selected_objects) < before_count:
            self._update_objects_list()
            self.needs_update = True
        
        return True  # Continue periodic callbacks

    def _setup_ui(self):
        """Set up the panel UI components."""
        list_frame = Gtk.Frame(label=f'Selected {self.object_type.title()}s')
        list_frame.set_margin_start(6)
        list_frame.set_margin_end(6)
        list_frame.set_margin_top(6)
        list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        list_box.set_margin_start(6)
        list_box.set_margin_end(6)
        list_box.set_margin_top(6)
        list_box.set_margin_bottom(6)
        list_scroll = Gtk.ScrolledWindow()
        list_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        list_scroll.set_min_content_height(80)
        list_scroll.set_max_content_height(150)
        self.objects_listbox = Gtk.ListBox()
        self.objects_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        list_scroll.add(self.objects_listbox)
        list_box.pack_start(list_scroll, True, True, 0)
        clear_btn = Gtk.Button(label='Clear Selection')
        clear_btn.connect('clicked', self._on_clear_clicked)
        list_box.pack_start(clear_btn, False, False, 0)
        list_frame.add(list_box)
        self.pack_start(list_frame, False, False, 0)
        controls_frame = Gtk.Frame(label='Plot Controls')
        controls_frame.set_margin_start(6)
        controls_frame.set_margin_end(6)
        controls_frame.set_margin_top(6)
        controls_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        controls_hbox.set_margin_start(6)
        controls_hbox.set_margin_end(6)
        controls_hbox.set_margin_top(6)
        controls_hbox.set_margin_bottom(6)
        self.grid_toggle = Gtk.CheckButton(label='Show Grid')
        self.grid_toggle.set_active(True)
        self.grid_toggle.connect('toggled', self._on_grid_toggled)
        controls_hbox.pack_start(self.grid_toggle, False, False, 0)
        self.legend_toggle = Gtk.CheckButton(label='Show Legend')
        self.legend_toggle.set_active(True)
        self.legend_toggle.connect('toggled', self._on_legend_toggled)
        controls_hbox.pack_start(self.legend_toggle, False, False, 0)
        self.auto_scale_toggle = Gtk.CheckButton(label='Auto Scale Y-axis')
        self.auto_scale_toggle.set_active(True)
        self.auto_scale_toggle.connect('toggled', self._on_auto_scale_toggled)
        controls_hbox.pack_start(self.auto_scale_toggle, False, False, 0)
        controls_frame.add(controls_hbox)
        self.pack_start(controls_frame, False, False, 0)
        canvas_frame = Gtk.Frame()
        canvas_frame.set_margin_start(6)
        canvas_frame.set_margin_end(6)
        canvas_frame.set_margin_top(6)
        canvas_frame.set_margin_bottom(6)
        canvas_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.figure = Figure(figsize=(6, 4), dpi=80)
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.set_size_request(400, 200)
        from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3
        self.toolbar = NavigationToolbar2GTK3(self.canvas, None)
        canvas_box.pack_start(self.toolbar, False, False, 0)
        canvas_box.pack_start(self.canvas, True, True, 0)
        canvas_frame.add(canvas_box)
        self.figure.tight_layout()
        self.pack_start(canvas_frame, True, True, 0)
        self.show_grid = True
        self.show_legend = True
        self.auto_scale = True
        self._show_empty_state()
        self.show_all()

    def add_object(self, obj: Any):
        """Add an object to the selected list for plotting.
        
        Args:
            obj: Place or Transition object to add
        """
        if any((o.id == obj.id for o in self.selected_objects)):
            return
        
        # Get the color that will be assigned to this object
        # (before adding it to the selected_objects list)
        index = len(self.selected_objects)
        color_hex = self._get_color(index)
        
        # Convert hex color to RGB tuple for Cairo rendering
        # Hex format: '#e74c3c' -> RGB tuple: (0.906, 0.298, 0.235)
        import matplotlib.colors as mcolors
        color_rgb = mcolors.hex2color(color_hex)
        
        # Set both border and fill color to match the plot color
        # (same as transition property dialog does)
        from shypn.netobjs import Transition
        
        obj.border_color = color_rgb
        
        # Only set fill_color for Transitions (Places don't have fill_color)
        if isinstance(obj, Transition):
            obj.fill_color = color_rgb
        
        # Trigger object's on_changed callback to notify the canvas
        if hasattr(obj, 'on_changed') and obj.on_changed:
            obj.on_changed()
        
        self.selected_objects.append(obj)
        # Add UI row immediately without full rebuild
        self._add_object_row(obj, len(self.selected_objects) - 1)
        self.needs_update = True
        
        # Trigger canvas redraw to show the new border color
        if self._model_manager:
            self._model_manager.mark_needs_redraw()


    def remove_object(self, obj: Any):
        """Remove an object from the selected list.
        
        Args:
            obj: Place or Transition object to remove
        """
        # Reset both border and fill color to default before removing
        old_callback = obj.on_changed if hasattr(obj, 'on_changed') else None
        obj.on_changed = None
        
        from shypn.netobjs import Transition, Place
        if isinstance(obj, Transition):
            obj.border_color = Transition.DEFAULT_BORDER_COLOR
            obj.fill_color = Transition.DEFAULT_COLOR
        elif isinstance(obj, Place):
            obj.border_color = Place.DEFAULT_BORDER_COLOR
            # Places don't have fill_color attribute
        
        obj.on_changed = old_callback
        
        self.selected_objects = [o for o in self.selected_objects if o.id != obj.id]
        # Full rebuild needed since colors/indices change
        self._update_objects_list()
        self.needs_update = True
        
        # Trigger canvas redraw to show the color reset
        if self._model_manager:
            self._model_manager.mark_needs_redraw()

    def _add_object_row(self, obj: Any, index: int):
        """Add a single object row to the UI list (optimized for incremental adds).
        
        Args:
            obj: Object to add
            index: Index in selected_objects list
        """
        # If we're adding first object, clear the "No objects selected" message
        if len(self.selected_objects) == 1:
            for child in self.objects_listbox.get_children():
                self.objects_listbox.remove(child)
        
        row = Gtk.ListBoxRow()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hbox.set_margin_start(6)
        hbox.set_margin_end(6)
        hbox.set_margin_top(3)
        hbox.set_margin_bottom(3)
        color_box = Gtk.DrawingArea()
        color_box.set_size_request(20, 20)
        color = self._get_color(index)
        color_box.connect('draw', self._draw_color_box, color)
        hbox.pack_start(color_box, False, False, 0)
        obj_name = getattr(obj, 'name', f'{self.object_type.title()}{obj.id}')
        if self.object_type == 'transition':
            transition_type = getattr(obj, 'transition_type', 'continuous')
            type_abbrev = {'immediate': 'IMM', 'timed': 'TIM', 'stochastic': 'STO', 'continuous': 'CON'}.get(transition_type, transition_type[:3].upper())
            label_text = f'{obj_name} [{type_abbrev}] ({self.object_type[0].upper()}{obj.id})'
        else:
            label_text = f'{obj_name} ({self.object_type[0].upper()}{obj.id})'
        label = Gtk.Label(label=label_text)
        label.set_xalign(0)
        hbox.pack_start(label, True, True, 0)
        remove_btn = Gtk.Button(label='✕')
        remove_btn.set_relief(Gtk.ReliefStyle.NONE)
        remove_btn.connect('clicked', self._on_remove_clicked, obj)
        hbox.pack_start(remove_btn, False, False, 0)
        row.add(hbox)
        self.objects_listbox.add(row)
        self.objects_listbox.show_all()

    def _update_objects_list(self):
        """Rebuild the entire UI list of selected objects (full refresh).
        
        This is only called when necessary (e.g., after removal, clear, or reordering).
        For adding new objects, use _add_object_row() instead for better performance.
        """
        for child in self.objects_listbox.get_children():
            self.objects_listbox.remove(child)
        if not self.selected_objects:
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label='No objects selected')
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
                color_box = Gtk.DrawingArea()
                color_box.set_size_request(20, 20)
                color = self._get_color(i)
                color_box.connect('draw', self._draw_color_box, color)
                hbox.pack_start(color_box, False, False, 0)
                obj_name = getattr(obj, 'name', f'{self.object_type.title()}{obj.id}')
                if self.object_type == 'transition':
                    transition_type = getattr(obj, 'transition_type', 'continuous')
                    type_abbrev = {'immediate': 'IMM', 'timed': 'TIM', 'stochastic': 'STO', 'continuous': 'CON'}.get(transition_type, transition_type[:3].upper())
                    label_text = f'{obj_name} [{type_abbrev}] ({self.object_type[0].upper()}{obj.id})'
                else:
                    label_text = f'{obj_name} ({self.object_type[0].upper()}{obj.id})'
                label = Gtk.Label(label=label_text)
                label.set_xalign(0)
                hbox.pack_start(label, True, True, 0)
                remove_btn = Gtk.Button(label='✕')
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
        r = int(color[1:3], 16) / 255.0
        g = int(color[3:5], 16) / 255.0
        b = int(color[5:7], 16) / 255.0
        cr.set_source_rgb(r, g, b)
        cr.rectangle(0, 0, 20, 20)
        cr.fill()
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
        """Handle clear button click - clear selection and blank canvas."""
        # Reset both border and fill colors for all selected objects
        from shypn.netobjs import Transition, Place
        for obj in self.selected_objects:
            old_callback = obj.on_changed if hasattr(obj, 'on_changed') else None
            obj.on_changed = None
            
            if isinstance(obj, Transition):
                obj.border_color = Transition.DEFAULT_BORDER_COLOR
                obj.fill_color = Transition.DEFAULT_COLOR
            elif isinstance(obj, Place):
                obj.border_color = Place.DEFAULT_BORDER_COLOR
                # Places don't have fill_color attribute
            
            obj.on_changed = old_callback
        
        self.selected_objects.clear()
        self.last_data_length.clear()
        self._plot_lines.clear()
        self._show_empty_state()
        self._update_objects_list()
        
        # Trigger canvas redraw to show color resets
        if self._model_manager:
            self._model_manager.mark_needs_redraw()

    def _on_grid_toggled(self, button):
        """Handle grid toggle button.
        
        Args:
            button: CheckButton that was toggled
        """
        self.show_grid = button.get_active()
        self.needs_update = True

    def _on_legend_toggled(self, button):
        """Handle legend toggle button.
        
        Args:
            button: CheckButton that was toggled
        """
        self.show_legend = button.get_active()
        self.needs_update = True

    def _on_auto_scale_toggled(self, button):
        """Handle auto scale toggle button.
        
        Args:
            button: CheckButton that was toggled
        """
        self.auto_scale = button.get_active()
        self.needs_update = True

    def _periodic_update(self) -> bool:
        """Periodic callback to update plot and UI list if needed.
        
        Returns:
            bool: True to continue periodic calls
        """
        # Skip update if no data collector available yet
        if not self.data_collector:
            print(f"[DEBUG PERIODIC] No data collector, skipping update")
            return True
            
        if not self.selected_objects:
            return True
        
        data_changed = False
        for obj in self.selected_objects:
            if self.object_type == 'place':
                current_length = len(self.data_collector.get_place_data(obj.id))
            else:
                current_length = len(self.data_collector.get_transition_data(obj.id))
            last_length = self.last_data_length.get(obj.id, 0)
            if current_length != last_length:
                data_changed = True
                self.last_data_length[obj.id] = current_length
        
        if data_changed or self.needs_update:
            # Only update plot, UI list is updated immediately in add_object()
            # Force full redraw when needs_update (properties changed) to re-apply adjustments
            print(f"[UPDATE] data_changed={data_changed}, needs_update={self.needs_update}")
            print(f"[UPDATE] Calling update_plot(force_full_redraw={self.needs_update})")
            self.update_plot(force_full_redraw=self.needs_update)
            self.needs_update = False
        return True

    def update_plot(self, force_full_redraw=False):
        """Update the plot with current data using efficient line updates.
        
        Uses matplotlib's set_data() for fast updates instead of axes.clear() + replot.
        Only does full redraw when object list changes or when forced.
        
        Args:
            force_full_redraw: If True, force a full redraw even if object list hasn't changed.
                              Used when properties change to re-apply adjustments.
        """
        print(f"[UPDATE_PLOT] force_full_redraw={force_full_redraw}, selected_objects={len(self.selected_objects)}")
        
        if not self.selected_objects:
            self._show_empty_state()
            return
        
        # Check if we need a full redraw (object list changed or forced)
        current_ids = [obj.id for obj in self.selected_objects]
        cached_ids = list(self._plot_lines.keys())
        
        print(f"[UPDATE_PLOT] current_ids={current_ids}, cached_ids={cached_ids}")
        
        if current_ids != cached_ids or force_full_redraw:
            # Full redraw needed - object list changed or properties changed
            print(f"[UPDATE_PLOT] Triggering _full_redraw() - ids_changed={current_ids != cached_ids}, force={force_full_redraw}")
            self._full_redraw()
            return
        
        # Fast update - just update existing line data
        for i, obj in enumerate(self.selected_objects):
            rate_data = self._get_rate_data(obj.id)
            if rate_data and obj.id in self._plot_lines:
                times = [t for t, r in rate_data]
                rates = [r for t, r in rate_data]
                line = self._plot_lines[obj.id]
                line.set_data(times, rates)
        
        # Update axis limits efficiently
        self.axes.relim()
        self.axes.autoscale_view()
        
        # Force immediate draw for smooth continuous curves
        # draw_idle() can sometimes be too lazy during rapid updates
        self.canvas.draw()
    
    def _full_redraw(self):
        """Perform a full plot redraw when object list changes."""
        self.axes.clear()
        self._plot_lines.clear()
        
        if not self.selected_objects:
            self._show_empty_state()
            return
        
        # Track if any data was plotted
        has_data = False
        
        for i, obj in enumerate(self.selected_objects):
            rate_data = self._get_rate_data(obj.id)
            color = self._get_color(i)
            obj_name = getattr(obj, 'name', f'{self.object_type.title()}{obj.id}')
            
            if self.object_type == 'transition':
                transition_type = getattr(obj, 'transition_type', 'continuous')
                type_abbrev = {'immediate': 'IMM', 'timed': 'TIM', 'stochastic': 'STO', 'continuous': 'CON'}.get(transition_type, transition_type[:3].upper())
                legend_label = f'{obj_name} [{type_abbrev}]'
            else:
                legend_label = f'{obj_name} ({self.object_type[0].upper()}{obj.id})'
            
            if rate_data:
                times = [t for t, r in rate_data]
                rates = [r for t, r in rate_data]
                line, = self.axes.plot(times, rates, label=legend_label, color=color, linewidth=2)
                self._plot_lines[obj.id] = line
                has_data = True
            else:
                # Plot empty line to maintain legend and color consistency
                line, = self.axes.plot([], [], label=legend_label, color=color, linewidth=2)
                self._plot_lines[obj.id] = line
        
        self._format_plot()
        self.canvas.draw()

    def _show_empty_state(self):
        """Show empty state message when no objects selected."""
        # Clear the axes first to remove any existing plots
        self.axes.clear()
        
        self.axes.text(0.5, 0.5, f'No {self.object_type}s selected\nAdd {self.object_type}s to analyze', ha='center', va='center', transform=self.axes.transAxes, fontsize=12, color='gray')
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        self.canvas.draw()

    def _format_plot(self):
        """Format the plot with labels, grid, and legend."""
        self.axes.set_xlabel('Time (s)', fontsize=11)
        self.axes.set_ylabel(self._get_ylabel(), fontsize=11)
        self.axes.set_title(self._get_title(), fontsize=12, fontweight='bold')
        if self.show_legend and self.selected_objects:
            handles, labels = self.axes.get_legend_handles_labels()
            if handles:
                self.axes.legend(loc='best', fontsize=9)
        if self.show_grid:
            self.axes.grid(True, alpha=0.3, linestyle='--')
        if not self.auto_scale and self.selected_objects:
            ylim = self.axes.get_ylim()
            y_range = ylim[1] - ylim[0]
            if y_range > 0:
                self.axes.set_ylim(ylim[0] - y_range * 0.1, ylim[1] + y_range * 0.1)
        # tight_layout is expensive - only call on full redraw
        # (this method is only called from _full_redraw now)
        try:
            self.figure.tight_layout()
        except:
            pass  # Ignore tight_layout errors

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
        self.needs_update = True

    def _get_rate_data(self, obj_id: Any) -> List[Tuple[float, float]]:
        """Get rate data for an object.
        
        Subclasses must implement this to return rate time series.
        
        Args:
            obj_id: ID of the object
            
        Returns:
            List of (time, rate) tuples
        """
        raise NotImplementedError('Subclasses must implement _get_rate_data()')

    def _get_ylabel(self) -> str:
        """Get Y-axis label.
        
        Returns:
            str: Y-axis label text
        """
        raise NotImplementedError('Subclasses must implement _get_ylabel()')

    def _get_title(self) -> str:
        """Get plot title.
        
        Returns:
            str: Plot title text
        """
        raise NotImplementedError('Subclasses must implement _get_title()')