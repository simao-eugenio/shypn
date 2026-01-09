#!/usr/bin/env python3
"""Base class for publication-quality matplotlib plots.

Provides common infrastructure for different plot types with time range
control and export configuration.

Author: Simão Eugénio
Date: 2025-12-30
"""
import warnings
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import matplotlib
matplotlib.use('GTK3Agg')

# Suppress matplotlib deprecation warnings (we use keyword args for compatibility)
warnings.filterwarnings('ignore', category=matplotlib._api.deprecation.MatplotlibDeprecationWarning)

from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3
from matplotlib.figure import Figure
from typing import List, Optional, Tuple, Dict


class BasePlot(Gtk.Box):
    """Base class for publication-quality plots.
    
    Provides:
    - Matplotlib figure with toolbar
    - Time range controls
    - Object selection UI
    - Export configuration
    - Real-time data updates
    
    Subclasses implement:
    - _create_plot(): Generate the specific plot type
    - _get_plot_title(): Return plot title
    """
    
    def __init__(self, data_collector=None, model=None):
        """Initialize base plot.
        
        Args:
            data_collector: SimulationDataCollector for data access
            model: ModelCanvasManager for object lookup
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        self.data_collector = data_collector
        self.model = model
        self.selected_objects = []
        
        # Time range (None = use all data)
        self.start_time = None
        self.end_time = None
        
        # Export settings
        self.export_dpi = 300
        self.export_format = 'pdf'
        self.export_transparent = False
        
        # Matplotlib components
        self.figure = None
        self.axes = None
        self.canvas = None
        self.toolbar = None
        
        # Update throttling
        self.needs_update = False
        self.update_interval = 500  # ms - match transitions/places panel update rate
        self.update_enabled = False  # Toggle for pausing updates (disabled by default)
        
        # Object filter (None = all, 'places' = places only, 'transitions' = transitions only)
        self.object_filter = None
        
        # Track last data state to avoid redundant updates
        self._last_data_count = 0
        self._last_selected_count = 0
        
        # Timeout source ID for cleanup
        self._timeout_id = None
        
        # Build UI
        self._build_ui()
        
        # Start periodic update and store timeout ID
        self._timeout_id = GLib.timeout_add(self.update_interval, self._periodic_update)
        
        # Connect destroy signal to cleanup timeout
        self.connect('destroy', self._on_destroy)
    
    def _build_ui(self):
        """Build complete UI with controls and plot canvas."""
        # Controls panel
        controls = self._build_controls()
        self.pack_start(controls, False, False, 0)
        
        # Plot canvas with toolbar
        canvas_container = self._build_canvas()
        self.pack_start(canvas_container, True, True, 0)
    
    def _build_controls(self) -> Gtk.Widget:
        """Build control panel with time range and object selection.
        
        Returns:
            Gtk.Frame: Container with controls
        """
        frame = Gtk.Frame()
        frame.set_label("Plot Controls")
        frame.set_margin_start(6)
        frame.set_margin_end(6)
        frame.set_margin_top(6)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_start(6)
        vbox.set_margin_end(6)
        vbox.set_margin_top(6)
        vbox.set_margin_bottom(6)
        
        # Time range controls
        time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        start_label = Gtk.Label(label="Start:")
        time_box.pack_start(start_label, False, False, 0)
        
        self.start_spin = Gtk.SpinButton()
        self.start_spin.set_range(0, 10000)
        self.start_spin.set_increments(1, 10)
        self.start_spin.set_value(0)
        self.start_spin.connect('value-changed', self._on_time_range_changed)
        time_box.pack_start(self.start_spin, False, False, 0)
        
        end_label = Gtk.Label(label="End:")
        time_box.pack_start(end_label, False, False, 0)
        
        self.end_spin = Gtk.SpinButton()
        self.end_spin.set_range(0, 10000)
        self.end_spin.set_increments(1, 10)
        self.end_spin.set_value(100)
        self.end_spin.connect('value-changed', self._on_time_range_changed)
        time_box.pack_start(self.end_spin, False, False, 0)
        
        use_all_check = Gtk.CheckButton(label="Use all data")
        use_all_check.set_active(True)
        use_all_check.connect('toggled', self._on_use_all_toggled)
        time_box.pack_start(use_all_check, False, False, 0)
        self.use_all_check = use_all_check
        
        vbox.pack_start(time_box, False, False, 0)
        
        # Action buttons row
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        # Clear all button
        clear_btn = Gtk.Button(label="Clear All")
        clear_btn.connect('clicked', self._on_clear_clicked)
        clear_btn.set_tooltip_text("Remove all objects from selection")
        action_box.pack_start(clear_btn, False, False, 0)
        
        # Update on/off toggle
        update_check = Gtk.CheckButton(label="Auto-update")
        update_check.set_active(False)  # OFF by default
        update_check.connect('toggled', self._on_update_toggled)
        update_check.set_tooltip_text("Enable/disable automatic plot updates during simulation")
        action_box.pack_start(update_check, False, False, 0)
        self.update_check = update_check
        
        # Object filter
        filter_label = Gtk.Label(label="Show:")
        action_box.pack_start(filter_label, False, False, 0)
        
        filter_combo = Gtk.ComboBoxText()
        filter_combo.append_text("All Objects")
        filter_combo.append_text("Places Only")
        filter_combo.append_text("Transitions Only")
        filter_combo.set_active(0)
        filter_combo.connect('changed', self._on_filter_changed)
        filter_combo.set_tooltip_text("Filter which objects are plotted")
        action_box.pack_start(filter_combo, False, False, 0)
        self.filter_combo = filter_combo
        
        vbox.pack_start(action_box, False, False, 0)
        
        # Object selection info
        self.selection_label = Gtk.Label()
        self.selection_label.set_markup("<i>No objects selected</i>")
        self.selection_label.set_xalign(0)
        vbox.pack_start(self.selection_label, False, False, 0)
        
        frame.add(vbox)
        return frame
    
    def _build_canvas(self) -> Gtk.Widget:
        """Build matplotlib canvas with toolbar.
        
        Returns:
            Gtk.Frame: Container with canvas and toolbar
        """
        frame = Gtk.Frame()
        frame.set_margin_start(6)
        frame.set_margin_end(6)
        frame.set_margin_bottom(6)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.set_size_request(400, 300)
        
        # Navigation toolbar (matplotlib 3.6+ compatible)
        self.toolbar = NavigationToolbar2GTK3(self.canvas)
        
        vbox.pack_start(self.toolbar, False, False, 0)
        vbox.pack_start(self.canvas, True, True, 0)
        
        frame.add(vbox)
        return frame
    
    def _on_time_range_changed(self, spin):
        """Handle time range spinner change."""
        if not self.use_all_check.get_active():
            self.start_time = self.start_spin.get_value()
            self.end_time = self.end_spin.get_value()
            self.needs_update = True
    
    def _on_use_all_toggled(self, check):
        """Handle 'use all data' checkbox toggle."""
        use_all = check.get_active()
        
        # Enable/disable spinners
        self.start_spin.set_sensitive(not use_all)
        self.end_spin.set_sensitive(not use_all)
        
        if use_all:
            self.start_time = None
            self.end_time = None
        else:
            self.start_time = self.start_spin.get_value()
            self.end_time = self.end_spin.get_value()
        
        self.needs_update = True
    
    def _on_clear_clicked(self, button):
        """Handle Clear All button click."""
        self.selected_objects.clear()
        self._update_selection_label()
        self.needs_update = True
    
    def _on_reset_clicked(self, button):
        """Handle Reset button click - blank the canvas with proper axes/grid/legend."""
        self._show_reset_state()
    
    def clear_plot(self):
        """Clear plot data and show reset state.
        
        Called when simulation is reset to blank the canvas.
        """
        # Reset tracking counters
        self._last_data_count = 0
        self._last_selected_count = 0
        self.needs_update = False
        
        # Show blank reset state
        self._show_reset_state()
    
    def _on_update_toggled(self, check):
        """Handle Auto-update toggle."""
        self.update_enabled = check.get_active()
        if self.update_enabled:
            # Force immediate update when re-enabled
            self.needs_update = True
    
    def _on_filter_changed(self, combo):
        """Handle object filter change."""
        active = combo.get_active()
        if active == 0:
            self.object_filter = None  # All objects
        elif active == 1:
            self.object_filter = 'places'  # Places only
        elif active == 2:
            self.object_filter = 'transitions'  # Transitions only
        
        self.needs_update = True
    
    def _on_destroy(self, widget):
        """Cleanup resources when widget is destroyed.
        
        Critical for dock/detach/reattach stability on Wayland.
        Ensures all matplotlib resources and GTK widgets are properly released.
        """
        # Remove timeout source to allow clean exit
        if self._timeout_id:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None
        
        # Cleanup matplotlib components (important for memory and Wayland stability)
        if self.toolbar:
            # NavigationToolbar2GTK3 needs explicit cleanup
            if hasattr(self.toolbar, 'destroy'):
                self.toolbar.destroy()
            self.toolbar = None
        
        if self.canvas:
            # Close any matplotlib event connections
            self.canvas.mpl_disconnect_all()
            self.canvas = None
        
        if self.figure:
            # Clear figure to release memory
            import matplotlib.pyplot as plt
            plt.close(self.figure)
            self.figure = None
        
        self.axes = None
        
        # Clear references to avoid circular dependencies
        self.data_collector = None
        self.model = None
        self.selected_objects = []
    
    def _periodic_update(self) -> bool:
        """Periodic update callback.
        
        Returns:
            bool: True to continue periodic updates
        """
        # Skip update if widget is not visible (not the active tab)
        if not self.get_visible():
            return True
        
        # Only proceed if auto-update is enabled
        if not self.update_enabled:
            return True
        
        # Check if anything changed that requires an update
        if self.data_collector and self.selected_objects:
            # Count current data points
            current_data_count = 0
            if hasattr(self.data_collector, 'place_data'):
                current_data_count = sum(len(data) for data in self.data_collector.place_data.values())
                current_data_count += sum(len(data) for data in self.data_collector.transition_data.values())
            elif hasattr(self.data_collector, 'time_points'):
                current_data_count = len(self.data_collector.time_points)
            
            current_selected_count = len(self.selected_objects)
            
            # Only update if data count or selection changed
            if (current_data_count != self._last_data_count or 
                current_selected_count != self._last_selected_count):
                self.needs_update = True
                self._last_data_count = current_data_count
                self._last_selected_count = current_selected_count
        
        if self.needs_update:
            self._update_plot()
            self.needs_update = False
        return True
    
    def _update_plot(self):
        """Update the plot with current data and settings."""
        if not self.selected_objects:
            self._show_empty_state()
            return
        
        if not self.data_collector:
            self._show_empty_state()
            return
        
        # Get filtered data
        data = self._get_filtered_data()
        
        # Check if we actually have data to plot
        if not data.get('data'):
            self._show_waiting_for_data_state()
            return
        
        # Clear ALL axes and remove extra axes (like colorbars)
        # This prevents colorbar/axes accumulation on updates
        axes_list = self.figure.get_axes()[:]  # Make a copy of the list
        for ax in axes_list:
            self.figure.delaxes(ax)
        
        # Recreate primary axes
        self.axes = self.figure.add_subplot(111)
        
        # Create plot
        self._create_plot(data)
        
        # Update canvas
        self.canvas.draw_idle()
    
    def _get_filtered_data(self) -> Dict:
        """Get data filtered by time range and object type.
        
        Returns:
            dict: Filtered time points and object data
        """
        if not self.data_collector:
            return {'data': {}}
        
        # Apply object type filter
        from shypn.netobjs import Place, Transition
        
        filtered_objects = self.selected_objects
        if self.object_filter == 'places':
            filtered_objects = [obj for obj in self.selected_objects if isinstance(obj, Place)]
        elif self.object_filter == 'transitions':
            filtered_objects = [obj for obj in self.selected_objects if isinstance(obj, Transition)]
        
        if not filtered_objects:
            return {'data': {}}
        
        # Temporarily swap selected_objects for filtering
        original_objects = self.selected_objects
        self.selected_objects = filtered_objects
        
        # Check if data collector has place_data (SimulationDataCollector)
        # or time_points (DataCollector from simulation controller)
        if hasattr(self.data_collector, 'place_data'):
            result = self._get_filtered_data_from_simulation_collector()
        elif hasattr(self.data_collector, 'time_points'):
            result = self._get_filtered_data_from_controller_collector()
        else:
            result = {'data': {}}
        
        # Restore original objects
        self.selected_objects = original_objects
        
        return result
    
    def _get_filtered_data_from_simulation_collector(self) -> Dict:
        """Get data from SimulationDataCollector (used by rate panels).
        
        Returns:
            dict: Data with per-object time points and values
                  {'data': {obj_id: {'time': [...], 'values': [...]}}}
        """
        from shypn.netobjs import Place
        
        data = {}
        
        # Collect data for each selected object
        for obj in self.selected_objects:
            obj_id = obj.id
            
            if isinstance(obj, Place):
                # Get place data using direct property access
                place_data = self.data_collector.place_data.get(obj_id, [])
                if place_data:
                    # Apply time range filter
                    if self.start_time is not None or self.end_time is not None:
                        start = self.start_time if self.start_time is not None else place_data[0][0]
                        end = self.end_time if self.end_time is not None else place_data[-1][0]
                        place_data = [(t, v) for t, v in place_data if start <= t <= end]
                    
                    if place_data:
                        times, values = zip(*place_data)
                        data[obj_id] = {
                            'time': list(times),
                            'values': list(values)
                        }
            else:
                # Get transition data using proper getter method
                # PRIORITY 1: Try get_transition_rate_series for rate functions
                if hasattr(self.data_collector, 'get_transition_rate_series'):
                    times, rates = self.data_collector.get_transition_rate_series(obj_id)
                    if times and rates and len(times) == len(rates):
                        # Apply time range filter
                        if self.start_time is not None or self.end_time is not None:
                            if times:
                                start = self.start_time if self.start_time is not None else times[0]
                                end = self.end_time if self.end_time is not None else times[-1]
                                filtered = [(t, r) for t, r in zip(times, rates) if start <= t <= end]
                                if filtered:
                                    times, rates = zip(*filtered)
                                else:
                                    times, rates = [], []
                        
                        if times:
                            data[obj_id] = {
                                'time': list(times),
                                'values': list(rates)
                            }
                            continue
                
                # PRIORITY 2: Fall back to cumulative firing count from transition_data
                trans_data = self.data_collector.transition_data.get(obj_id, [])
                if trans_data:
                    # transition_data now stores (time, count) tuples
                    # Apply time range filter
                    if self.start_time is not None or self.end_time is not None:
                        start = self.start_time if self.start_time is not None else trans_data[0][0]
                        end = self.end_time if self.end_time is not None else trans_data[-1][0]
                        trans_data = [(t, c) for t, c in trans_data if start <= t <= end]
                    
                    if trans_data:
                        times, counts = zip(*trans_data)
                        data[obj_id] = {
                            'time': list(times),
                            'values': list(counts)
                        }
        
        return {'data': data}
    
    def _get_filtered_data_from_controller_collector(self) -> Dict:
        """Get data from DataCollector (from simulation controller).
        
        Returns:
            dict: Filtered time and object data
        """
        time_points = self.data_collector.time_points
        
        if not time_points:
            return {'time': [], 'data': {}}
        
        # Apply time range filter
        if self.start_time is not None or self.end_time is not None:
            start = self.start_time if self.start_time is not None else time_points[0]
            end = self.end_time if self.end_time is not None else time_points[-1]
            
            # Find indices
            start_idx = 0
            end_idx = len(time_points)
            
            for i, t in enumerate(time_points):
                if t >= start:
                    start_idx = i
                    break
            
            for i in range(len(time_points) - 1, -1, -1):
                if time_points[i] <= end:
                    end_idx = i + 1
                    break
            
            time_points = time_points[start_idx:end_idx]
        else:
            start_idx = 0
            end_idx = len(time_points)
        
        # Get data for selected objects
        data = {}
        for obj in self.selected_objects:
            obj_id = obj.id
            
            # Determine if place or transition
            from shypn.netobjs import Place
            if isinstance(obj, Place):
                if obj_id in self.data_collector.place_data:
                    data[obj_id] = self.data_collector.place_data[obj_id][start_idx:end_idx]
            else:
                if obj_id in self.data_collector.transition_data:
                    data[obj_id] = self.data_collector.transition_data[obj_id][start_idx:end_idx]
        
        return {'time': time_points, 'data': data}
    
    def _show_empty_state(self):
        """Show empty state message."""
        self.axes.clear()
        
        # Check if 3D axes
        from mpl_toolkits.mplot3d import Axes3D
        if isinstance(self.axes, Axes3D):
            # 3D axes require x, y, z, s arguments
            self.axes.text(0.5, 0.5, 0.5,
                'No data to display\n\nAdd objects from Transitions or Places categories',
                horizontalalignment='center',
                verticalalignment='center',
                transform=self.axes.transAxes,
                fontsize=12,
                color='gray'
            )
            self.axes.set_zticks([])
        else:
            # 2D axes
            self.axes.text(
                0.5, 0.5,
                'No data to display\n\nAdd objects from Transitions or Places categories',
                horizontalalignment='center',
                verticalalignment='center',
                transform=self.axes.transAxes,
                fontsize=12,
                color='gray'
            )
        
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        self.canvas.draw_idle()
    
    def _show_reset_state(self):
        """Show reset state with proper axes, grid, and legend.
        
        Called when simulation is reset to blank the canvas while
        maintaining proper plot structure (axes, grid, legend).
        """
        # Clear all axes including any twin axes (twinx/twiny)
        # This ensures leftover trajectories from dual-axis plots are removed
        for ax in self.figure.get_axes():
            ax.clear()
        
        # Re-get the primary axes reference after clearing
        self.axes = self.figure.get_axes()[0] if self.figure.get_axes() else self.figure.add_subplot(111)
        
        # Check if 3D axes
        from mpl_toolkits.mplot3d import Axes3D
        if isinstance(self.axes, Axes3D):
            # 3D axes - set up basic structure
            self.axes.set_xlabel('X', fontsize=11)
            self.axes.set_ylabel('Y', fontsize=11)
            self.axes.set_zlabel('Z', fontsize=11)
            self.axes.set_title('Phase Space (3D)', fontsize=12, fontweight='bold')
            self.axes.grid(True, alpha=0.3)
        else:
            # 2D axes - set up basic structure
            self.axes.set_xlabel('Time (s)', fontsize=11)
            self.axes.set_ylabel('Value', fontsize=11)
            self.axes.set_title(self._get_plot_title(), fontsize=12, fontweight='bold')
            self.axes.grid(True, alpha=0.3)
            
            # Set reasonable default limits
            self.axes.set_xlim(0, 10)
            self.axes.set_ylim(0, 10)
        
        # Add empty legend
        self.axes.legend([], [], loc='best', fontsize=9, framealpha=0.9)
        
        self.canvas.draw_idle()
    
    def _show_waiting_for_data_state(self):
        """Show waiting for simulation data message."""
        self.axes.clear()
        
        # Show selected objects
        obj_names = [obj.name for obj in self.selected_objects]
        objects_text = ', '.join(obj_names[:3])
        if len(obj_names) > 3:
            objects_text += f' + {len(obj_names) - 3} more'
        
        # Check if 3D axes
        from mpl_toolkits.mplot3d import Axes3D
        if isinstance(self.axes, Axes3D):
            # 3D axes require x, y, z, s arguments
            self.axes.text(0.5, 0.5, 0.5,
                f'Waiting for simulation data\n\nSelected objects: {objects_text}\n\nRun simulation to see plots',
                horizontalalignment='center',
                verticalalignment='center',
                transform=self.axes.transAxes,
                fontsize=12,
                color='orange'
            )
            self.axes.set_zticks([])
        else:
            # 2D axes
            self.axes.text(
                0.5, 0.5,
                f'Waiting for simulation data\n\nSelected objects: {objects_text}\n\nRun simulation to see plots',
                horizontalalignment='center',
                verticalalignment='center',
                transform=self.axes.transAxes,
                fontsize=12,
                color='orange'
            )
        
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        self.canvas.draw_idle()
    
    def _create_plot(self, data: Dict):
        """Create the specific plot type (implemented by subclasses).
        
        Args:
            data: Filtered time and object data
        """
        raise NotImplementedError("Subclasses must implement _create_plot()")
    
    def _get_plot_title(self) -> str:
        """Get plot title (implemented by subclasses).
        
        Returns:
            str: Plot title
        """
        raise NotImplementedError("Subclasses must implement _get_plot_title()")
    
    def add_object(self, obj):
        """Add object to plot.
        
        Args:
            obj: Place or Transition to plot
        """
        if obj not in self.selected_objects:
            self.selected_objects.append(obj)
            self._update_selection_label()
            # Reset last count to force update
            self._last_selected_count = 0
            self.needs_update = True
            # Force immediate update to reflect changes
            self._update_plot()
    
    def remove_object(self, obj):
        """Remove object from plot.
        
        Args:
            obj: Place or Transition to remove
        """
        if obj in self.selected_objects:
            self.selected_objects.remove(obj)
            self._update_selection_label()
            # Reset last count to force update
            self._last_selected_count = 0
            self.needs_update = True
            # Force immediate update to reflect changes
            self._update_plot()
    
    def clear_objects(self):
        """Clear all selected objects."""
        self.selected_objects.clear()
        self._update_selection_label()
        # Reset last count to force update
        self._last_selected_count = 0
        self._last_data_count = 0
        self.needs_update = True
    
    def _update_selection_label(self):
        """Update the selection label with current object count and filter."""
        if not self.selected_objects:
            self.selection_label.set_markup("<i>No objects selected</i>")
            return
        
        # Count by type
        from shypn.netobjs import Place, Transition
        places = sum(1 for obj in self.selected_objects if isinstance(obj, Place))
        transitions = sum(1 for obj in self.selected_objects if isinstance(obj, Transition))
        
        # Apply filter to get what will actually be plotted
        plotted_count = 0
        if self.object_filter == 'places':
            plotted_count = places
        elif self.object_filter == 'transitions':
            plotted_count = transitions
        else:
            plotted_count = places + transitions
        
        # Build label
        parts = []
        if places > 0:
            parts.append(f"{places} place{'s' if places != 1 else ''}")
        if transitions > 0:
            parts.append(f"{transitions} transition{'s' if transitions != 1 else ''}")
        
        label_text = ", ".join(parts)
        
        if self.object_filter:
            filter_name = "Places" if self.object_filter == 'places' else "Transitions"
            label_text += f" | <b>Plotting: {plotted_count} {filter_name}</b>"
        else:
            label_text += f" | <b>Plotting: {plotted_count} total</b>"
        
        self.selection_label.set_markup(label_text)
    
    def set_data_collector(self, data_collector):
        """Set data collector for updates.
        
        Args:
            data_collector: SimulationDataCollector instance
        """
        self.data_collector = data_collector
        # Reset tracking to force fresh update
        self._last_data_count = 0
        self._last_selected_count = 0
        self.needs_update = True
    
    def export_plot(self, filepath: str, dpi: int = 300, format: str = 'pdf', 
                   transparent: bool = False):
        """Export plot to file with custom settings.
        
        Args:
            filepath: Output file path
            dpi: Resolution (for raster formats)
            format: File format ('pdf', 'png', 'svg', 'eps')
            transparent: Use transparent background
        """
        self.figure.savefig(
            filepath,
            dpi=dpi,
            format=format,
            bbox_inches='tight',
            transparent=transparent
        )
