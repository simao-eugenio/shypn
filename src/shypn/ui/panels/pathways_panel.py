"""Pathways panel controller."""

import sys
from gi.repository import Gtk
from .base_panel import BasePanel


class PathwaysPanelController(BasePanel):
    """Controller for Pathways panel (KEGG and SBML import).
    
    Manages:
    - KEGG pathway import tab
    - SBML file import tab
    - Import progress indicators
    
    Architecture:
    - Builds UI programmatically (Wayland-safe)
    - Uses GtkNotebook for import methods
    - Placeholder for import functionality (Phase 4)
    """
    
    def __init__(self, builder: Gtk.Builder):
        """Initialize Pathways panel controller.
        
        Args:
            builder: Gtk.Builder with main window UI loaded
        """
        super().__init__(builder, 'pathways')
        
        # Widgets
        self.import_notebook = None
        
        # Import controllers (to be wired in Phase 4)
        self.kegg_ctrl = None
        self.sbml_ctrl = None
    
    def get_preferred_width(self) -> int:
        """Get preferred width for Pathways panel.
        
        Returns:
            320 pixels
        """
        return 320
    
    def initialize(self):
        """Initialize Pathways panel widgets - build complete UI."""
        print(f"[PATHWAYS_PANEL] Initializing...", file=sys.stderr)
        
        try:
            # Get container from builder
            self._container = self.builder.get_object('pathways_panel_container')
            if not self._container:
                raise ValueError("pathways_panel_container not found in UI")
            
            # Main content box
            content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            content_box.set_margin_start(6)
            content_box.set_margin_end(6)
            content_box.set_margin_top(6)
            content_box.set_margin_bottom(6)
            
            # Import notebook
            self.import_notebook = Gtk.Notebook()
            self.import_notebook.set_tab_pos(Gtk.PositionType.TOP)
            
            # KEGG Import tab
            kegg_page = self._create_kegg_page()
            self.import_notebook.append_page(
                kegg_page,
                Gtk.Label(label="KEGG Import")
            )
            
            # SBML Import tab
            sbml_page = self._create_sbml_page()
            self.import_notebook.append_page(
                sbml_page,
                Gtk.Label(label="SBML Import")
            )
            
            content_box.pack_start(self.import_notebook, True, True, 0)
            self._container.pack_start(content_box, True, True, 0)
            self._container.show_all()
            
            print(f"[PATHWAYS_PANEL] Initialized successfully", file=sys.stderr)
            self._emit_ready()
            
        except Exception as e:
            error_msg = f"Failed to initialize Pathways panel: {e}"
            print(f"[PATHWAYS_PANEL] ERROR: {error_msg}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            self._emit_error(error_msg)
    
    def _create_kegg_page(self) -> Gtk.Widget:
        """Create KEGG import page.
        
        Returns:
            KEGG import widget
        """
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # Title
        title = Gtk.Label(label="KEGG Pathway Import")
        title.set_xalign(0)
        title.set_markup("<b>KEGG Pathway Import</b>")
        box.pack_start(title, False, False, 0)
        
        # Placeholder content
        placeholder = Gtk.Label(
            label="KEGG pathway import controls will appear here\n\n"
                  "(Phase 4: Wire KEGGImportController)"
        )
        placeholder.set_xalign(0)
        placeholder.get_style_context().add_class("dim-label")
        box.pack_start(placeholder, True, True, 0)
        
        return box
    
    def _create_sbml_page(self) -> Gtk.Widget:
        """Create SBML import page.
        
        Returns:
            SBML import widget
        """
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # Title
        title = Gtk.Label(label="SBML File Import")
        title.set_xalign(0)
        title.set_markup("<b>SBML File Import</b>")
        box.pack_start(title, False, False, 0)
        
        # Placeholder content
        placeholder = Gtk.Label(
            label="SBML file import controls will appear here\n\n"
                  "(Phase 4: Wire SBMLImportController)"
        )
        placeholder.set_xalign(0)
        placeholder.get_style_context().add_class("dim-label")
        box.pack_start(placeholder, True, True, 0)
        
        return box
    
    def activate(self):
        """Called when Pathways panel becomes visible."""
        print(f"[PATHWAYS_PANEL] Activated", file=sys.stderr)
        # TODO Phase 4: Refresh import state
    
    def deactivate(self):
        """Called when Pathways panel becomes hidden."""
        print(f"[PATHWAYS_PANEL] Deactivated", file=sys.stderr)
        # TODO Phase 4: Cancel ongoing imports if needed
