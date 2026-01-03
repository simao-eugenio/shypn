#!/usr/bin/env python3
"""Pathway Operations Panel - Main Assembly.

This module assembles the KEGG, SBML, and BRENDA categories into a unified
Pathway Operations panel. It follows the CategoryFrame architecture used in
Topology, Dynamic Analyses, and Report panels.

Design:
  - Minimal container panel
  - All logic delegated to category classes
  - Wayland-safe operations
  - Simple data flow between categories (KEGG/SBML → BRENDA)
"""
import sys
import logging

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
except Exception as e:
    print(f'ERROR: GTK3 not available in pathway_operations_panel: {e}', file=sys.stderr)
    sys.exit(1)

from .pathway_operations.kegg_category import KEGGCategory
from .pathway_operations.sbml_category import SBMLCategory
from .pathway_operations.bigg_category import BiGGCategory
from .pathway_operations.brenda_category import BRENDACategory
from .pathway_operations.sabio_rk_category import SabioRKCategory
from .pathway_operations.heuristic_parameters_category import HeuristicParametersCategory
from .pathway_operations.enrichment_history_category import EnrichmentHistoryCategory


class PathwayOperationsPanel(Gtk.Box):
    """Main Pathway Operations panel container.
    
    Assembles seven categories:
    1. KEGG - Import pathways from KEGG database
    2. SBML - Import models from SBML files or BioModels
    3. BiGG Models - Import curated genome-scale models from BiGG database
    4. BRENDA - Enrich models with kinetic parameters from BRENDA
    5. SABIO-RK - Enrich models with kinetic parameters from SABIO-RK
    6. Heuristic Parameters - Type-aware parameter inference from multiple sources
    7. Enrichment History - View, rate, and undo parameter enrichments (Phase 2)
    
    Data flow:
      KEGG import → BRENDA/SABIO-RK/Heuristic (EC numbers)
      SBML import → BRENDA/SABIO-RK/Heuristic (reaction IDs)
      BiGG import → BRENDA/SABIO-RK/Heuristic (reaction IDs)
      All enrichments → History tracking (KB)
    
    Attributes:
        kegg_category: KEGGCategory instance
        sbml_category: SBMLCategory instance
        bigg_category: BiGGCategory instance
        brenda_category: BRENDACategory instance
        sabio_rk_category: SabioRKCategory instance
        heuristic_params_category: HeuristicParametersCategory instance
        enrichment_history_category: EnrichmentHistoryCategory instance (Phase 2)
        project: Current project
        model_canvas: Current model canvas
    """
    
    def __init__(self, workspace_settings=None, parent_window=None, 
                 project=None, model_canvas=None):
        """Initialize Pathway Operations panel.
        
        Args:
            workspace_settings: Optional WorkspaceSettings for preferences
            parent_window: Optional parent window for dialogs (Wayland fix)
            project: Optional current project
            model_canvas: Optional current model canvas
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.workspace_settings = workspace_settings
        self.parent_window = parent_window
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Callback for notifying Report panel when pathways are imported
        self.report_refresh_callback = None
        
        # Create categories
        self.kegg_category = KEGGCategory(
            expanded=False,
            model_canvas=model_canvas,
            project=project,
            parent_window=parent_window
        )
        
        self.sbml_category = SBMLCategory(
            workspace_settings=workspace_settings,
            parent_window=parent_window
        )
        
        self.bigg_category = BiGGCategory()
        
        self.brenda_category = BRENDACategory(
            workspace_settings=workspace_settings,
            parent_window=parent_window,
            model_canvas_loader=model_canvas
        )
        
        self.sabio_rk_category = SabioRKCategory(
            workspace_settings=workspace_settings,
            parent_window=parent_window
        )
        
        # Heuristic Parameters category - Type-aware parameter inference
        self.heuristic_params_category = HeuristicParametersCategory(
            model_canvas_loader=model_canvas
        )
        
        # Phase 2: Enrichment History category - View, rate, undo enrichments
        self.enrichment_history_category = EnrichmentHistoryCategory(
            model_canvas_loader=model_canvas,
            expanded=False
        )
        
        # Set initial project and canvas if provided
        if project:
            self.set_project(project)
        if model_canvas:
            self.set_model_canvas(model_canvas)
        
        # Build UI
        self._build_ui()
        
        # Wire up data flow between categories
        self._connect_category_signals()
    
    def _build_ui(self):
        """Build the panel UI with all categories."""
        # Panel title header (matches other panels: TOPOLOGY, REPORT, etc.)
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_size_request(-1, 48)  # Fixed 48px height
        header_box.set_margin_start(10)
        header_box.set_margin_end(10)
        
        header_label = Gtk.Label()
        header_label.set_markup("<b>PATHWAY OPERATIONS</b>")
        header_label.set_halign(Gtk.Align.START)
        header_label.set_valign(Gtk.Align.CENTER)
        header_box.pack_start(header_label, True, True, 0)
        
        # Float button on the far right (icon only)
        self.float_button = Gtk.ToggleButton()
        self.float_button.set_label("⬈")
        self.float_button.set_tooltip_text("Detach panel to floating window")
        self.float_button.set_relief(Gtk.ReliefStyle.NONE)  # Flat button
        self.float_button.set_valign(Gtk.Align.CENTER)
        header_box.pack_end(self.float_button, False, False, 0)
        
        self.pack_start(header_box, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(separator, False, False, 0)
        
        # Create scrolled window for categories
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        
        # Create vertical box for categories
        categories_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Add categories in order
        categories_box.pack_start(self.kegg_category, False, False, 0)
        categories_box.pack_start(self.sbml_category, False, False, 0)
        categories_box.pack_start(self.bigg_category, False, False, 0)
        categories_box.pack_start(self.brenda_category, False, False, 0)
        categories_box.pack_start(self.sabio_rk_category, False, False, 0)
        categories_box.pack_start(self.heuristic_params_category, False, False, 0)
        categories_box.pack_start(self.enrichment_history_category, False, False, 0)  # Phase 2
        
        scrolled.add(categories_box)
        self.pack_start(scrolled, True, True, 0)
        
        self.show_all()
    
    def _connect_category_signals(self):
        """Connect signals between categories for data flow.
        
        When KEGG or SBML complete an import, notify BRENDA so it can
        suggest queries based on the imported data. Also notify Report panel.
        """
        # KEGG → BRENDA data flow
        def on_kegg_import_complete(data):
            self.logger.info("KEGG import completed, notifying BRENDA category")
            data['source'] = 'kegg'
            self.brenda_category.receive_import_data(data)
            # Notify Report panel if callback is set
            if self.report_refresh_callback:
                self.report_refresh_callback()
        
        # SBML → BRENDA data flow
        def on_sbml_import_complete(data):
            self.logger.info("SBML import completed, notifying BRENDA category")
            data['source'] = 'sbml'
            self.brenda_category.receive_import_data(data)
            # Notify Report panel if callback is set
            if self.report_refresh_callback:
                self.report_refresh_callback()
        
        # BiGG → BRENDA data flow
        def on_bigg_import_complete(data):
            self.logger.info("BiGG import completed, notifying BRENDA category")
            data['source'] = 'bigg'
            self.brenda_category.receive_import_data(data)
            # Notify Report panel if callback is set
            if self.report_refresh_callback:
                self.report_refresh_callback()
        
        # Connect the signals (categories emit these via _trigger_import_complete)
        self.kegg_category.import_complete_callback = on_kegg_import_complete
        self.sbml_category.import_complete_callback = on_sbml_import_complete
        self.bigg_category.import_complete_callback = on_bigg_import_complete
    
    def set_project(self, project):
        """Set the current project for all categories.
        
        Args:
            project: Project instance
        """
        self.project = project
        
        # Propagate to all categories
        self.kegg_category.set_project(project)
        self.sbml_category.set_project(project)
        self.bigg_category.set_project(project)
        self.brenda_category.set_project(project)
        self.sabio_rk_category.set_project(project)
        self.enrichment_history_category.set_project(project)  # Phase 2
        
        self.logger.info(f"Project set: {project.name if project else None}")
    
    def set_model_canvas(self, model_canvas):
        """Set the current model canvas for all categories.
        
        Args:
            model_canvas: ModelCanvas instance
        """
        self.model_canvas = model_canvas
        
        # Propagate to all categories
        self.kegg_category.set_model_canvas(model_canvas)
        self.sbml_category.set_model_canvas(model_canvas)
        self.bigg_category.set_model_canvas(model_canvas)
        self.brenda_category.set_model_canvas(model_canvas)
        self.sabio_rk_category.set_model_canvas(model_canvas)
        self.enrichment_history_category.set_model_canvas(model_canvas)  # Phase 2
        
        self.logger.info("Model canvas updated for all categories")
    
    def set_file_panel_loader(self, file_panel_loader):
        """Set file panel loader for file tree refresh after imports.
        
        Args:
            file_panel_loader: FilePanelLoader instance
        """
        # Propagate to categories that need it (KEGG, SBML)
        if hasattr(self.kegg_category, 'set_file_panel_loader'):
            self.kegg_category.set_file_panel_loader(file_panel_loader)
        if hasattr(self.sbml_category, 'set_file_panel_loader'):
            self.sbml_category.set_file_panel_loader(file_panel_loader)
        
        self.logger.info("File panel loader set for categories")
    
    def set_report_refresh_callback(self, callback):
        """Set the callback to be invoked when pathway data is imported.
        
        This allows the Report panel to refresh its dynamic analyses category
        when new KEGG or SBML data becomes available.
        
        Args:
            callback: Function to call when pathway import completes
        """
        self.report_refresh_callback = callback
        self.logger.info("Report refresh callback registered")
    
    def switch_to_category(self, category_name: str):
        """Switch to and expand a specific category.
        
        Useful for directing user attention after context menu actions.
        For example, "Enrich with BRENDA" will switch to BRENDA category.
        
        Args:
            category_name: Name of category to switch to ('KEGG', 'SBML', 'BRENDA')
        """
        category_map = {
            'KEGG': self.kegg_category,
            'SBML': self.sbml_category,
            'BiGG': self.bigg_category,
            'BRENDA': self.brenda_category,
            'SABIO-RK': self.sabio_rk_category
        }
        
        category = category_map.get(category_name)
        if category:
            # Expand the category
            category.set_expanded(True)
            self.logger.info(f"Switched to {category_name} category")
        else:
            self.logger.warning(f"Unknown category: {category_name}")
    
    def on_tab_switched(self, drawing_area):
        """Called when user switches between model tabs.
        
        Notifies all categories to update their state for the new active model.
        This ensures KEGG/SBML/BRENDA panels show data for the currently focused model.
        
        Pattern: Like Report Panel, simply notify categories without complex logic.
        Each category is responsible for safely updating its own state.
        
        Args:
            drawing_area: The newly active drawing area
        """
        self.logger.debug("Tab switched, updating all categories")
        
        # Notify all categories that support tab switching
        for category in [self.kegg_category, self.sbml_category, self.bigg_category,
                        self.brenda_category, self.sabio_rk_category, 
                        self.enrichment_history_category]:
            if hasattr(category, 'on_tab_switched'):
                try:
                    category.on_tab_switched()
                except Exception as e:
                    # Log but don't let one category's failure affect others
                    self.logger.debug(f"{type(category).__name__} tab-switch update skipped: {e}")
    
    def cleanup(self):
        """Clean up resources when panel is destroyed."""
        self.logger.info("Cleaning up Pathway Operations panel")
        
        # Clean up categories
        if hasattr(self.kegg_category, 'cleanup'):
            self.kegg_category.cleanup()
        if hasattr(self.sbml_category, 'cleanup'):
            self.sbml_category.cleanup()
        if hasattr(self.brenda_category, 'cleanup'):
            self.brenda_category.cleanup()
        if hasattr(self.sabio_rk_category, 'cleanup'):
            self.sabio_rk_category.cleanup()


