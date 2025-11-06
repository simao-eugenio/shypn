"""Analyses panel controller."""

import sys
from gi.repository import Gtk
from .base_panel import BasePanel


class AnalysesPanelController(BasePanel):
    """Controller for Analyses panel (plotting and data visualization).
    
    Manages:
    - Topological analyses expander
    - Dynamic analyses notebook with tabs:
      * Time Series plots
      * Histograms
      * Scatter plots  
      * Phase plots
    
    Architecture:
    - Builds UI programmatically (Wayland-safe)
    - Uses GtkNotebook for multiple plot types
    - Clean separation of plot types
    """
    
    def __init__(self, builder: Gtk.Builder):
        """Initialize Analyses panel controller.
        
        Args:
            builder: Gtk.Builder with main window UI loaded
        """
        super().__init__(builder, 'analyses')
        
        # Widgets
        self.topological_expander = None
        self.dynamic_notebook = None
        
        # Plot controllers (to be wired in Phase 4)
        self.time_series_ctrl = None
        self.histogram_ctrl = None
        self.scatter_ctrl = None
        self.phase_ctrl = None
    
    def get_preferred_width(self) -> int:
        """Get preferred width for Analyses panel.
        
        Returns:
            350 pixels
        """
        return 350
    
    def initialize(self):
        """Initialize Analyses panel widgets - build complete UI."""
        
        try:
            # Get container from builder
            self._container = self.builder.get_object('analyses_panel_container')
            if not self._container:
                raise ValueError("analyses_panel_container not found in UI")
            
            # Main content box
            content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            content_box.set_margin_start(6)
            content_box.set_margin_end(6)
            content_box.set_margin_top(6)
            content_box.set_margin_bottom(6)
            
            # Build sections
            self._build_topological_section(content_box)
            self._build_dynamic_analyses_section(content_box)
            
            self._container.pack_start(content_box, True, True, 0)
            self._container.show_all()
            
            self._emit_ready()
            
        except Exception as e:
            error_msg = f"Failed to initialize Analyses panel: {e}"
            import traceback
            traceback.print_exc()
            self._emit_error(error_msg)
    
    def _build_topological_section(self, parent):
        """Build topological analyses expander section."""
        self.topological_expander = Gtk.Expander()
        self.topological_expander.set_expanded(False)
        
        # Label
        label = Gtk.Label(label="TOPOLOGICAL ANALYSES")
        label.set_xalign(0)
        label.set_markup("<b>TOPOLOGICAL ANALYSES</b>")
        self.topological_expander.set_label_widget(label)
        
        # Content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        content.set_margin_start(12)
        content.set_margin_top(6)
        content.set_margin_bottom(6)
        
        placeholder = Gtk.Label(label="Topologic analysis tools will appear here")
        placeholder.set_xalign(0)
        placeholder.get_style_context().add_class("dim-label")
        content.pack_start(placeholder, False, False, 0)
        
        self.topological_expander.add(content)
        parent.pack_start(self.topological_expander, False, True, 0)
    
    def _build_dynamic_analyses_section(self, parent):
        """Build dynamic analyses section with notebook."""
        expander = Gtk.Expander()
        expander.set_expanded(True)
        
        # Label
        label = Gtk.Label(label="DYNAMIC ANALYSES")
        label.set_xalign(0)
        label.set_markup("<b>DYNAMIC ANALYSES</b>")
        expander.set_label_widget(label)
        
        # Notebook with plot tabs
        self.dynamic_notebook = Gtk.Notebook()
        self.dynamic_notebook.set_tab_pos(Gtk.PositionType.TOP)
        self.dynamic_notebook.set_scrollable(True)
        
        # Time Series tab
        time_series_page = self._create_placeholder_page("Time Series")
        self.dynamic_notebook.append_page(
            time_series_page,
            Gtk.Label(label="Time Series")
        )
        
        # Histogram tab
        histogram_page = self._create_placeholder_page("Histogram")
        self.dynamic_notebook.append_page(
            histogram_page,
            Gtk.Label(label="Histogram")
        )
        
        # Scatter Plot tab
        scatter_page = self._create_placeholder_page("Scatter Plot")
        self.dynamic_notebook.append_page(
            scatter_page,
            Gtk.Label(label="Scatter")
        )
        
        # Phase Plot tab
        phase_page = self._create_placeholder_page("Phase Plot")
        self.dynamic_notebook.append_page(
            phase_page,
            Gtk.Label(label="Phase")
        )
        
        expander.add(self.dynamic_notebook)
        parent.pack_start(expander, True, True, 0)
    
    def _create_placeholder_page(self, title: str) -> Gtk.Widget:
        """Create placeholder page for notebook tab.
        
        Args:
            title: Tab title
            
        Returns:
            Placeholder widget
        """
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        label = Gtk.Label(label=f"{title} plot controls and visualization")
        label.set_xalign(0)
        label.get_style_context().add_class("dim-label")
        box.pack_start(label, False, False, 0)
        
        # Placeholder for plot area
        plot_frame = Gtk.Frame()
        plot_frame.set_shadow_type(Gtk.ShadowType.IN)
        plot_frame.set_size_request(-1, 200)
        
        plot_label = Gtk.Label(label=f"{title} Plot Area\n(Phase 4: Wire plot controller)")
        plot_label.get_style_context().add_class("dim-label")
        plot_frame.add(plot_label)
        
        box.pack_start(plot_frame, True, True, 0)
        
        return box
    
    def activate(self):
        """Called when Analyses panel becomes visible."""
        # TODO Phase 4: Refresh plots if needed
    
    def deactivate(self):
        """Called when Analyses panel becomes hidden."""
        # TODO Phase 4: Pause plotting operations
