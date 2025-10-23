"""Topology panel controller."""

import sys
from gi.repository import Gtk
from .base_panel import BasePanel


class TopologyPanelController(BasePanel):
    """Controller for Topology panel (network analysis).
    
    Manages:
    - Topology analysis interface
    - Network visualization controls
    - Analysis results display
    
    Architecture:
    - Builds UI programmatically (Wayland-safe)
    - Placeholder for topology functionality (Phase 4)
    """
    
    def __init__(self, builder: Gtk.Builder):
        """Initialize Topology panel controller.
        
        Args:
            builder: Gtk.Builder with main window UI loaded
        """
        super().__init__(builder, 'topology')
        self.topology_analyzer = None
    
    def get_preferred_width(self) -> int:
        """Get preferred width for Topology panel.
        
        Returns:
            400 pixels
        """
        return 400
    
    def initialize(self):
        """Initialize Topology panel widgets - build complete UI."""
        print(f"[TOPOLOGY_PANEL] Initializing...", file=sys.stderr)
        
        try:
            # Get container from builder
            self._container = self.builder.get_object('topology_panel_container')
            if not self._container:
                raise ValueError("topology_panel_container not found in UI")
            
            # Main content box
            content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            content_box.set_margin_start(12)
            content_box.set_margin_end(12)
            content_box.set_margin_top(12)
            content_box.set_margin_bottom(12)
            
            # Title
            title = Gtk.Label(label="Topology Analysis")
            title.set_xalign(0)
            title.set_markup("<b>Topology Analysis</b>")
            content_box.pack_start(title, False, False, 0)
            
            # Placeholder content
            placeholder = Gtk.Label(
                label="Topology analysis interface will appear here\n\n"
                      "Features:\n"
                      "• Network visualization\n"
                      "• Connectivity analysis\n"
                      "• Path finding\n"
                      "• Structural metrics\n\n"
                      "(Phase 4: Wire TopologyPanelController)"
            )
            placeholder.set_xalign(0)
            placeholder.set_justify(Gtk.Justification.LEFT)
            placeholder.get_style_context().add_class("dim-label")
            content_box.pack_start(placeholder, True, True, 0)
            
            self._container.pack_start(content_box, True, True, 0)
            self._container.show_all()
            
            print(f"[TOPOLOGY_PANEL] Initialized successfully", file=sys.stderr)
            self._emit_ready()
            
        except Exception as e:
            error_msg = f"Failed to initialize Topology panel: {e}"
            print(f"[TOPOLOGY_PANEL] ERROR: {error_msg}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            self._emit_error(error_msg)
    
    def activate(self):
        """Called when Topology panel becomes visible."""
        print(f"[TOPOLOGY_PANEL] Activated", file=sys.stderr)
        # TODO Phase 4: Refresh analysis results
    
    def deactivate(self):
        """Called when Topology panel becomes hidden."""
        print(f"[TOPOLOGY_PANEL] Deactivated", file=sys.stderr)
        # TODO Phase 4: Pause analysis operations
