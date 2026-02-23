#!/usr/bin/env python3
"""Models category for Report Panel.

Displays comprehensive scientific information about the current model:
- Model metadata (name, dates, file path, description)
- Petri net structure (places, transitions, arcs)
- Import provenance (KEGG/SBML source information)
- Detailed species and reactions lists with metadata

WHEN IT POPULATES:
- NOT immediately after KEGG/SBML import (import only saves file)
- ONLY after user opens file via File → Open or double-click
- on_file_opened event → report_panel.set_model_canvas() → refresh()
- Raw imported data shown in green cells
- Enriched BRENDA data shown in blue cells
- Manually edited fields shown in orange cells
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from datetime import datetime

from .base_category import BaseReportCategory
from shypn.data.kegg_ec_fetcher import KEGGECFetcher


class ModelsCategory(BaseReportCategory):
    """Models report category with comprehensive scientific information.
    
    Displays:
    - Model Overview: name, creation date, file path, description
    - Petri Net Structure: counts and model type
    - Import Provenance: source type, organism, import date (if available)
    - Species/Places List: ID mappings with metadata
    - Reactions/Transitions List: ID mappings with metadata
    """
    
    def __init__(self, project=None, model_canvas=None):
        """Initialize models category."""
        # Initialize instance variables BEFORE super().__init__
        # because super will call _build_content() which calls refresh()
        
        # Refresh throttling to prevent redundant updates during file loading
        self._refresh_scheduled = False
        self._refresh_pending = False
        self._refresh_timeout_id = None
        self._last_interaction_time = 0  # Track user activity
        
        # Lazy table population flags (only populate when user opens expander)
        self._species_table_needs_refresh = False
        self._reactions_table_needs_refresh = False
        self._kb_needs_update = False
        
        # Selected locality tracking
        self.selected_transition = None
        self.selected_locality = None
        self.locality_store = None
        self.locality_treeview = None
        self.locality_expander = None
        
        # KEGG EC fetcher
        self.kegg_ec_fetcher = KEGGECFetcher()
        
        super().__init__(
            title="MODELS",
            project=project,
            model_canvas=model_canvas,
            expanded=False
        )
    
    def _build_content(self):
        """Build models content with comprehensive scientific information."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # === MODEL OVERVIEW SECTION ===
        overview_frame = Gtk.Frame()
        overview_frame.set_label("Model Overview")
        overview_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        
        overview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        overview_box.set_margin_start(12)
        overview_box.set_margin_end(12)
        overview_box.set_margin_top(6)
        overview_box.set_margin_bottom(6)
        
        self.overview_label = Gtk.Label()
        self.overview_label.set_xalign(0)
        self.overview_label.set_line_wrap(True)
        self.overview_label.set_selectable(True)
        self.overview_label.set_text("No model loaded")
        overview_box.pack_start(self.overview_label, False, False, 0)
        
        overview_frame.add(overview_box)
        box.pack_start(overview_frame, False, False, 0)
        
        # === PETRI NET STRUCTURE SECTION ===
        structure_frame = Gtk.Frame()
        structure_frame.set_label("Petri Net Structure")
        structure_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        
        structure_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        structure_box.set_margin_start(12)
        structure_box.set_margin_end(12)
        structure_box.set_margin_top(6)
        structure_box.set_margin_bottom(6)
        
        self.structure_label = Gtk.Label()
        self.structure_label.set_xalign(0)
        self.structure_label.set_line_wrap(True)
        self.structure_label.set_selectable(True)
        self.structure_label.set_text("No data")
        structure_box.pack_start(self.structure_label, False, False, 0)
        
        structure_frame.add(structure_box)
        box.pack_start(structure_frame, False, False, 0)
        
        # === IMPORT PROVENANCE SECTION (conditional) ===
        self.provenance_frame = Gtk.Frame()
        self.provenance_frame.set_label("Import Provenance")
        self.provenance_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        
        provenance_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        provenance_box.set_margin_start(12)
        provenance_box.set_margin_end(12)
        provenance_box.set_margin_top(6)
        provenance_box.set_margin_bottom(6)
        
        self.provenance_label = Gtk.Label()
        self.provenance_label.set_xalign(0)
        self.provenance_label.set_line_wrap(True)
        self.provenance_label.set_selectable(True)
        self.provenance_label.set_text("No import data")
        provenance_box.pack_start(self.provenance_label, False, False, 0)
        
        self.provenance_frame.add(provenance_box)
        box.pack_start(self.provenance_frame, False, False, 0)
        self.provenance_frame.set_visible(False)  # Hidden by default
        
        # === SUB-EXPANDERS (Collapsed by default) ===
        
        # Species/Places Table with controls
        self.species_expander = Gtk.Expander(label="Show Species/Places Table (sortable)")
        self.species_expander.set_expanded(False)
        self.species_expander.connect('activate', self._on_species_expander_activate)
        
        # Container for table and controls
        species_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        species_container.set_margin_start(6)
        species_container.set_margin_end(6)
        species_container.set_margin_top(6)
        species_container.set_margin_bottom(6)
        
        # Toolbar with column toggles and legend
        toolbar = self._create_species_toolbar()
        species_container.pack_start(toolbar, False, False, 0)
        
        # Table
        scrolled_species, self.species_treeview, self.species_store = self._create_species_table()
        species_container.pack_start(scrolled_species, True, True, 0)
        
        self.species_expander.add(species_container)
        box.pack_start(self.species_expander, False, False, 0)
        
        # Reactions/Transitions Table
        self.reactions_expander = Gtk.Expander(label="Show Reactions/Transitions Table (sortable)")
        self.reactions_expander.set_expanded(False)
        self.reactions_expander.connect('activate', self._on_reactions_expander_activate)
        scrolled_reactions, self.reactions_treeview, self.reactions_store = self._create_reactions_table()
        self.reactions_expander.add(scrolled_reactions)
        box.pack_start(self.reactions_expander, False, False, 0)
        
        # === SELECTED LOCALITY TABLE ===
        self.locality_expander = Gtk.Expander(label="Show Selected Locality (sortable)")
        self.locality_expander.set_expanded(False)
        self.locality_expander.set_visible(False)  # Initially hidden until selection
        scrolled_locality, self.locality_treeview, self.locality_store = self._create_locality_table()
        self.locality_expander.add(scrolled_locality)
        box.pack_start(self.locality_expander, False, False, 0)
        
        # Initial populate
        self.refresh()
        
        return box
    
    def mark_user_interaction(self):
        """Mark that user is actively interacting with the canvas.
        
        Called by canvas during pan/zoom/drag operations to defer
        expensive refresh operations until user is idle.
        """
        import time
        self._last_interaction_time = time.time()
    
    def _on_species_expander_activate(self, expander):
        """Populate species table when expander is opened."""
        # Schedule population for next idle (after expander animation)
        GLib.idle_add(self._populate_species_if_needed)
    
    def _on_reactions_expander_activate(self, expander):
        """Populate reactions table when expander is opened."""
        # Schedule population for next idle (after expander animation)
        GLib.idle_add(self._populate_reactions_if_needed)
    
    def _populate_species_if_needed(self):
        """Populate species table if it needs refresh and expander is open."""
        if self.species_expander.get_expanded():
            # Get current active model dynamically
            model = self.get_current_model()
            if model:
                # Do KB update first if needed
                if self._kb_needs_update:
                    self._update_knowledge_base_structural(model)
                    self._update_knowledge_base_pathway(model)
                    self._update_knowledge_base_kinetics(model)
                    self._kb_needs_update = False
                
                if self._species_table_needs_refresh:
                    self._populate_species_table(model)
                    self._species_table_needs_refresh = False
        return False  # Don't repeat
    
    def _populate_reactions_if_needed(self):
        """Populate reactions table if it needs refresh and expander is open."""
        if self.reactions_expander.get_expanded():
            # Get current active model dynamically
            model = self.get_current_model()
            if model:
                # Do KB update first if needed
                if self._kb_needs_update:
                    self._update_knowledge_base_structural(model)
                    self._update_knowledge_base_pathway(model)
                    self._update_knowledge_base_kinetics(model)
                    self._kb_needs_update = False
                
                if self._reactions_table_needs_refresh:
                    self._populate_reactions_table(model)
                    self._reactions_table_needs_refresh = False
        return False  # Don't repeat
    
    def _create_summary_grid(self):
        """No longer needed - summary is in frame."""
        pass
    
    def _create_species_toolbar(self):
        """Create toolbar with color legend for species table.
        
        Returns:
            Gtk.Box: Toolbar widget
        """
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        toolbar.set_margin_start(6)
        toolbar.set_margin_end(6)
        toolbar.set_margin_top(6)
        toolbar.set_margin_bottom(6)
        
        # Color Legend (centered)
        legend_label = Gtk.Label()
        legend_label.set_markup(
            "<b>Color Legend:</b> "
            "<span foreground='#16a34a'>■</span> Database  "
            "<span foreground='#2563eb'>■</span> BRENDA  "
            "<span foreground='#9333ea'>■</span> SABIO-RK  "
            "<span foreground='#ea580c'>■</span> User  "
            "<span foreground='#6b7280'><i>■</i></span> Heuristic"
        )
        legend_label.set_halign(Gtk.Align.CENTER)
        toolbar.pack_start(legend_label, True, True, 0)
        
        return toolbar
    
    def _create_species_table(self):
        """Create TreeView for species/places with sortable columns.
        
        Minimal view with essential columns only:
        - #, Petri Net ID, Biological Name, Initial Amount, Units, Mass, Conservation
        
        Returns:
            tuple: (ScrolledWindow, TreeView, ListStore)
        """
        # Create ListStore with column types (minimal structure)
        # Columns:
        #   0: index (int)
        #   1: id (str)
        #   2: name (str)
        #   3: tokens (float)
        #   4: token_units (str)
        #   5: mass (float)
        #   6: mass_source (str)
        #   7: conservation_status (str)
        store = Gtk.ListStore(
            int,    # 0: index
            str,    # 1: Petri Net ID
            str,    # 2: Biological Name
            float,  # 3: Initial Tokens
            str,    # 4: Token Units
            float,  # 5: Mass
            str,    # 6: Mass source
            str     # 7: Conservation Status
        )
        
        # Create TreeView
        treeview = Gtk.TreeView(model=store)
        treeview.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
        treeview.set_enable_search(True)
        treeview.set_search_column(2)  # Search by biological name
        
        # Add columns (all visible)
        self._add_column(treeview, "#", 0, width=50, sortable=False)
        self._add_column(treeview, "Petri Net ID", 1, sortable=True, width=120)
        self._add_column(treeview, "Biological Name", 2, sortable=True, width=250)
        self._add_column(treeview, "Initial Amount", 3, sortable=True, numeric=True, width=120)
        self._add_column(treeview, "Units", 4, sortable=True, width=100)
        self._add_colored_column(treeview, "Mass (g/mol)", 5, 6, sortable=True, numeric=True, width=120)
        self._add_column(treeview, "Conservation", 7, sortable=True, width=120)
        
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(300)
        scrolled.add(treeview)
        
        return scrolled, treeview, store
    
    def _create_reactions_table(self):
        """Create TreeView for reactions/transitions with sortable columns.
        
        Column order: #, Petri Net ID, Biological Name, Type, EC Number,
                     Vmax, Km, Kcat, Ki, Rate Function, Reversible
        
        Returns:
            tuple: (ScrolledWindow, TreeView, ListStore)
        """
        # Create ListStore with column types
        # Columns:
        #   0: index (int)
        #   1: id (str)
        #   2: name (str)
        #   3: type (str)
        #   4: ec_number (str)
        #   5: vmax (float)
        #   6: vmax_source (str)
        #   7: km (float)
        #   8: km_source (str)
        #   9: kcat (float)
        #   10: kcat_source (str)
        #   11: ki (float)
        #   12: ki_source (str)
        #   13: rate_function (str)
        #   14: reversible (str)
        store = Gtk.ListStore(
            int,    # 0: index
            str,    # 1: Petri Net ID
            str,    # 2: Biological Name
            str,    # 3: Type
            str,    # 4: EC Number
            float,  # 5: Vmax
            str,    # 6: Vmax source
            float,  # 7: Km
            str,    # 8: Km source
            float,  # 9: Kcat
            str,    # 10: Kcat source
            float,  # 11: Ki
            str,    # 12: Ki source
            str,    # 13: Rate Function
            str     # 14: Reversible
        )
        
        # Create TreeView
        treeview = Gtk.TreeView(model=store)
        treeview.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
        treeview.set_enable_search(True)
        treeview.set_search_column(2)  # Search by biological name
        
        # Add columns with renderers
        self._add_column(treeview, "#", 0, width=50, sortable=False)
        self._add_column(treeview, "Petri Net ID", 1, sortable=True, width=120)
        self._add_column(treeview, "Biological Name", 2, sortable=True, width=200)
        self._add_column(treeview, "Type", 3, sortable=True, width=100)
        self._add_column(treeview, "EC Number", 4, sortable=True, width=120)
        
        # Add colored kinetic parameter columns (reordered: Vmax, Km, Kcat, Ki)
        self._add_colored_column(treeview, "Vmax", 5, 6, sortable=True, width=100, numeric=True)
        self._add_colored_column(treeview, "Km", 7, 8, sortable=True, width=100, numeric=True)
        self._add_colored_column(treeview, "Kcat", 9, 10, sortable=True, width=100, numeric=True)
        self._add_colored_column(treeview, "Ki", 11, 12, sortable=True, width=100, numeric=True)
        
        # Rate function and reversible
        self._add_column(treeview, "Rate Function", 13, sortable=True, width=250)
        self._add_column(treeview, "Reversible", 14, sortable=True, width=90)
        
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(300)
        scrolled.add(treeview)
        
        return scrolled, treeview, store
    
    def _create_locality_table(self):
        """Create TreeView for selected transition locality.
        
        Shows transition + input places + output places in unified table.
        
        Returns:
            tuple: (ScrolledWindow, TreeView, ListStore)
        """
        # Create ListStore
        # Columns:
        #   0: index (int)
        #   1: Type (str) - "Place" or "Transition"
        #   2: Direction (str) - "", "← Input", "→ Output"
        #   3: Petri Net ID (str) - P1, T1, etc.
        #   4: Biological Name (str)
        #   5: Info (str) - Type for transition, token count str for place
        #   6: Value (float) - Rate for transition, tokens for place
        #   7: Units (str)
        #   8: Parameters (str) - EC/Vmax/Km for transition, Mass for place
        store = Gtk.ListStore(
            int,    # 0: index
            str,    # 1: Type
            str,    # 2: Direction
            str,    # 3: Petri Net ID
            str,    # 4: Biological Name
            str,    # 5: Info
            float,  # 6: Value
            str,    # 7: Units
            str     # 8: Parameters
        )
        
        # Create TreeView
        treeview = Gtk.TreeView(model=store)
        treeview.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
        treeview.set_enable_search(True)
        treeview.set_search_column(4)  # Search by biological name
        
        # Add columns
        self._add_column(treeview, "#", 0, width=40, sortable=False)
        self._add_column(treeview, "Type", 1, sortable=True, width=100)
        self._add_column(treeview, "Direction", 2, sortable=True, width=100)
        self._add_column(treeview, "ID", 3, sortable=True, width=100)
        self._add_column(treeview, "Name", 4, sortable=True, width=250)
        self._add_column(treeview, "Info", 5, sortable=True, width=120)
        self._add_column(treeview, "Value", 6, sortable=True, numeric=True, width=100)
        self._add_column(treeview, "Units", 7, sortable=True, width=80)
        self._add_column(treeview, "Parameters", 8, sortable=True, width=200)
        
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        scrolled.add(treeview)
        
        return scrolled, treeview, store
    
    def _add_column(self, treeview, title, column_id, sortable=False, 
                    width=None, numeric=False):
        """Helper to add a column to TreeView.
        
        Args:
            treeview: TreeView widget
            title: Column title
            column_id: Column index in ListStore
            sortable: Whether column is sortable
            width: Fixed width (None for auto)
            numeric: Whether to right-align (for numbers)
            
        Returns:
            Gtk.TreeViewColumn: The created column
        """
        renderer = Gtk.CellRendererText()
        if numeric:
            renderer.set_property('xalign', 1.0)  # Right-align numbers
        
        column = Gtk.TreeViewColumn(title, renderer, text=column_id)
        column.set_resizable(True)
        if width:
            column.set_min_width(width)
        if sortable:
            column.set_sort_column_id(column_id)
            column.set_clickable(True)
        
        treeview.append_column(column)
        return column
    
    def _add_colored_column(self, treeview, title, data_column_id, source_column_id,
                            sortable=False, width=None, numeric=False):
        """Helper to add a colored column to TreeView based on data source.
        
        Args:
            treeview: TreeView widget
            title: Column title
            data_column_id: Column index for data in ListStore
            source_column_id: Column index for source info in ListStore
            sortable: Whether column is sortable
            width: Fixed width (None for auto)
            numeric: Whether to right-align (for numbers)
            
        Returns:
            Gtk.TreeViewColumn: The created column
        """
        renderer = Gtk.CellRendererText()
        if numeric:
            renderer.set_property('xalign', 1.0)  # Right-align numbers
        
        column = Gtk.TreeViewColumn(title, renderer, text=data_column_id)
        column.set_resizable(True)
        if width:
            column.set_min_width(width)
        if sortable:
            column.set_sort_column_id(data_column_id)
            column.set_clickable(True)
        
        # Set cell data func to color based on source
        column.set_cell_data_func(renderer, self._color_cell_by_source, 
                                   (data_column_id, source_column_id))
        
        treeview.append_column(column)
        return column
    
    def _color_cell_by_source(self, column, renderer, model, iter, user_data):
        """Color cell based on data source.
        
        Color scheme:
        - Green (#16a34a): Real data from KEGG/SBML database
        - Blue (#2563eb): BRENDA-enriched experimental data
        - Purple (#9333ea): SABIO-RK-enriched kinetic data
        - Orange (#ea580c): User-edited values
        - Gray (#6b7280): KEGG heuristic estimates (placeholder values)
        - Light Gray (#9ca3af): Missing/unknown data
        """
        data_column_id, source_column_id = user_data
        value = model.get_value(iter, data_column_id)
        source = model.get_value(iter, source_column_id)
        
        # Determine color based on source
        if not value or value == "-" or value == 0.0:
            # Missing data - light gray
            renderer.set_property('foreground', '#9ca3af')
            renderer.set_property('weight', 400)  # Normal weight
            renderer.set_property('style', 0)  # Normal style
        elif source in ('kegg_import', 'sbml_import', 'biopax_import'):
            # Real database data - bright green
            renderer.set_property('foreground', '#16a34a')
            renderer.set_property('weight', 600)  # Semi-bold
            renderer.set_property('style', 0)  # Normal style
        elif source == 'brenda_enriched':
            # BRENDA enriched - bright blue
            renderer.set_property('foreground', '#2563eb')
            renderer.set_property('weight', 600)  # Semi-bold
            renderer.set_property('style', 0)  # Normal style
        elif source == 'sabio_rk_enriched':
            # SABIO-RK enriched - bright purple
            renderer.set_property('foreground', '#9333ea')
            renderer.set_property('weight', 600)  # Semi-bold
            renderer.set_property('style', 0)  # Normal style
        elif source == 'kegg_heuristic':
            # KEGG heuristic estimates (10.0, 0.5) - gray italic
            renderer.set_property('foreground', '#6b7280')
            renderer.set_property('weight', 400)  # Normal weight
            renderer.set_property('style', 2)  # Italic (Pango.Style.ITALIC = 2)
        elif source == 'user_edited':
            # User edited - bright orange
            renderer.set_property('foreground', '#ea580c')
            renderer.set_property('weight', 600)  # Semi-bold
            renderer.set_property('style', 0)  # Normal style
        else:
            # Unknown - default black
            renderer.set_property('foreground', '#000000')
            renderer.set_property('weight', 400)  # Normal weight
            renderer.set_property('style', 0)  # Normal style
    
    def _update_knowledge_base_structural(self, model):
        """Update Knowledge Base with structural model data.
        
        Args:
            model: ModelCanvasManager with places, transitions, arcs
        """
        try:
            # Get KB from model_canvas_loader (the actual loader, not the manager)
            kb = None
            if hasattr(self, 'parent_panel') and self.parent_panel:
                if hasattr(self.parent_panel, 'model_canvas_loader'):
                    loader = self.parent_panel.model_canvas_loader
                    if hasattr(loader, 'get_current_knowledge_base'):
                        kb = loader.get_current_knowledge_base()
            
            if not kb:
                return  # KB not available yet
            
            # Extract structural data
            places_data = []
            transitions_data = []
            arcs_data = []
            
            # Places
            if hasattr(model, 'places') and model.places:
                for place in model.places:
                    if place:
                        place_info = {
                            'place_id': place.id if hasattr(place, 'id') else str(id(place)),
                            'label': place.label if hasattr(place, 'label') else '',
                            'initial_marking': place.tokens if hasattr(place, 'tokens') else 0,
                        }
                        places_data.append(place_info)
            
            # Transitions - Pass objects directly so DTO can extract metadata (including kinetic_law)
            if hasattr(model, 'transitions') and model.transitions:
                transitions_data = [t for t in model.transitions if t]
            
            # Arcs - Pass objects directly so DTO can infer arc_type
            if hasattr(model, 'arcs') and model.arcs:
                arcs_data = [arc for arc in model.arcs if arc]
            
            # Update KB (DTOs will normalize the data)
            kb.update_topology_structural(places_data, transitions_data, arcs_data)
            
        except Exception as e:
            import traceback
            print(f"[REPORT→KB] ⚠️ Failed to update structural knowledge: {e}")
            traceback.print_exc()
    
    def _update_knowledge_base_pathway(self, model):
        """Extract pathway metadata from model and update Knowledge Base.
        
        Args:
            model: ModelCanvasManager with places/transitions/arcs and their metadata
        """
        try:
            # Get Knowledge Base instance
            kb = None
            if hasattr(self, 'parent_panel') and self.parent_panel:
                # Through parent panel -> model_canvas_loader
                if hasattr(self.parent_panel, 'model_canvas_loader'):
                    loader = self.parent_panel.model_canvas_loader
                    if hasattr(loader, 'get_current_knowledge_base'):
                        kb = loader.get_current_knowledge_base()
            
            if not kb:
                return  # KB not available
            
            # Track stats
            compounds_added = 0
            reactions_added = 0
            
            # Extract compound info from places
            for place in model.places:
                if not place or not hasattr(place, 'metadata'):
                    continue
                
                metadata = place.metadata
                
                # Extract KEGG compound data
                kegg_ids = metadata.get('kegg_compound_ids', [])
                compound_name = metadata.get('compound_name', '')
                
                if kegg_ids:
                    for kegg_id in kegg_ids:
                        # Create compound info dict
                        compound_data = {
                            'compound_id': kegg_id,  # e.g., "cpd:C00031"
                            'name': compound_name,
                            'formula': None,  # Not in KEGG KGML
                            'molecular_weight': None,  # Not in KEGG KGML
                            'place_ids': [place.id]  # Link to place
                        }
                        
                        kb.update_compound_info(kegg_id, compound_data)
                        compounds_added += 1
            
            # Extract reaction info from transitions
            for transition in model.transitions:
                if not transition or not hasattr(transition, 'metadata'):
                    continue
                
                metadata = transition.metadata
                
                # Extract KEGG reaction data
                # Note: 'kegg_reaction_name' contains the KEGG API ID (e.g., "rn:R00710")
                # while 'kegg_reaction_id' is the internal pathway entry ID (e.g., "61")
                kegg_reaction_name = metadata.get('kegg_reaction_name')
                ec_numbers = metadata.get('ec_numbers', [])
                reversible = metadata.get('reversible', False)
                
                if kegg_reaction_name:
                    # Strip "rn:" prefix if present (e.g., "rn:R00710" → "R00710")
                    reaction_id = kegg_reaction_name.replace('rn:', '')
                    
                    # Create reaction info dict
                    reaction_data = {
                        'reaction_id': reaction_id,  # e.g., "R00710"
                        'name': transition.label or transition.name,
                        'ec_number': ec_numbers[0] if ec_numbers else None,
                        'ec_numbers': ec_numbers,  # All EC numbers
                        'reversible': reversible,
                        'transition_id': transition.id  # Link to transition
                    }
                    
                    kb.update_reaction_info(reaction_id, reaction_data)
                    reactions_added += 1
            
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def _update_knowledge_base_kinetics(self, model):
        """Extract kinetic parameters from transitions and update Knowledge Base.
        
        Extracts from two sources:
        1. BRENDA enrichment (stored in transition metadata)
        2. Heuristic database (local SQLite with BRENDA/SABIO-RK/BioModels data)
        
        Args:
            model: ModelCanvasManager with transitions
        """
        try:
            # Get Knowledge Base instance
            kb = None
            if hasattr(self, 'parent_panel') and self.parent_panel:
                # Through parent panel -> model_canvas_loader
                if hasattr(self.parent_panel, 'model_canvas_loader'):
                    loader = self.parent_panel.model_canvas_loader
                    if hasattr(loader, 'get_current_knowledge_base'):
                        kb = loader.get_current_knowledge_base()
            
            if not kb:
                return  # KB not available
            
            # Try to get heuristic database
            heuristic_db = None
            try:
                from shypn.crossfetch.database.heuristic_db import HeuristicDatabase
                heuristic_db = HeuristicDatabase()
            except (ImportError, AttributeError) as e:
                self.logger.debug(f"Heuristic database not available: {e}")
            
            # Track stats
            transitions_with_kinetics = 0
            from_enrichment = 0
            from_database = 0
            
            # Extract kinetic parameters from transitions
            for transition in model.transitions:
                if not transition or not hasattr(transition, 'metadata'):
                    continue
                
                metadata = transition.metadata
                kinetic_params = None
                
                # SOURCE 1: Check for BRENDA enrichment in metadata
                enrichment_source = metadata.get('enrichment_source')
                if enrichment_source == 'brenda':
                    km = metadata.get('km')
                    kcat = metadata.get('kcat')
                    vmax = metadata.get('vmax')
                    ki = metadata.get('ki')
                    
                    if any([km, kcat, vmax, ki]):
                        # Get EC number
                        ec_number = None
                        ec_numbers = metadata.get('ec_numbers', [])
                        if ec_numbers and isinstance(ec_numbers, list):
                            ec_number = ec_numbers[0]
                        elif 'ec_number' in metadata:
                            ec_number = metadata['ec_number']
                        
                        # Get organism
                        organism = metadata.get('organism')
                        
                        # Create KineticParams object
                        from shypn.viability.knowledge.data_structures import KineticParams
                        
                        kinetic_params = KineticParams(
                            transition_id=transition.id,
                            ec_number=ec_number,
                            vmax=vmax,
                            kcat=kcat,
                            source='brenda_enrichment',
                            organism=organism,
                            confidence=0.8  # High confidence for BRENDA enrichment
                        )
                        
                        # Add Km values (substrate -> Km mapping)
                        if km is not None:
                            substrate_name = metadata.get('substrate', 'default')
                            kinetic_params.km_values[substrate_name] = km
                        
                        # Add Ki values (inhibitor -> Ki mapping)
                        if ki is not None:
                            inhibitor_name = metadata.get('inhibitor', 'default')
                            kinetic_params.ki_values[inhibitor_name] = ki
                        
                        from_enrichment += 1
                
                # SOURCE 2: Query heuristic database for EC number
                if not kinetic_params and heuristic_db:
                    # Get EC number from metadata
                    ec_numbers = metadata.get('ec_numbers', [])
                    ec_number = None
                    if ec_numbers and isinstance(ec_numbers, list) and len(ec_numbers) > 0:
                        ec_number = ec_numbers[0]
                    elif 'ec_number' in metadata:
                        ec_number = metadata['ec_number']
                    
                    if ec_number:
                        # Query database for kinetic parameters
                        try:
                            # Get Km values
                            km_results = heuristic_db.query_brenda_data(
                                ec_number=ec_number,
                                parameter_type='Km',
                                min_quality=0.7,
                                limit=1  # Just get the best one
                            )
                            
                            # Get Kcat values
                            kcat_results = heuristic_db.query_brenda_data(
                                ec_number=ec_number,
                                parameter_type='Kcat',
                                min_quality=0.7,
                                limit=1
                            )
                            
                            if km_results or kcat_results:
                                from shypn.viability.knowledge.data_structures import KineticParams
                                
                                kinetic_params = KineticParams(
                                    transition_id=transition.id,
                                    ec_number=ec_number,
                                    source='heuristic_db',
                                    confidence=0.6  # Medium confidence for database lookup
                                )
                                
                                # Add Km from database
                                if km_results:
                                    km_data = km_results[0]
                                    substrate = km_data.get('substrate', 'default')
                                    kinetic_params.km_values[substrate] = km_data['value']
                                    if km_data.get('organism'):
                                        kinetic_params.organism = km_data['organism']
                                
                                # Add Kcat from database
                                if kcat_results:
                                    kcat_data = kcat_results[0]
                                    kinetic_params.kcat = kcat_data['value']
                                
                                from_database += 1
                        
                        except Exception as e:
                            # Database query failed, skip
                            pass
                
                # Update Knowledge Base if we found kinetic parameters
                if kinetic_params:
                    kb.update_kinetic_parameters(transition.id, kinetic_params)
                    transitions_with_kinetics += 1
            
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def refresh(self):
        """Refresh tables when model changes or tab switches.
        
        Calls _do_refresh directly - deferral mechanism was causing callbacks
        to be cancelled before execution.
        """
        self._do_refresh()
    
    def _do_refresh(self):
        """Actual refresh implementation - only updates lightweight UI elements.
        
        Expensive operations (KB updates, table population) are deferred until
        user actually opens the corresponding expanders.
        """
        try:
            # Get current active model dynamically instead of using stale reference
            model = self.get_current_model()
            
            # If no model, show empty state
            if not model:
                self.overview_label.set_text("No model loaded")
                self.overview_label.show_all()
                self.structure_label.set_text("No data")
                self.structure_label.show_all()
                self.provenance_label.set_text("No import data")
                self.provenance_label.show_all()
                self.provenance_frame.hide()
                return
            
            places_count = len(model.places) if hasattr(model, 'places') else 0
            transitions_count = len(model.transitions) if hasattr(model, 'transitions') else 0
            
            # DEFER EXPENSIVE KB UPDATES
            self._kb_needs_update = True
            
            # === BUILD MODEL OVERVIEW (quick - just metadata) ===
            overview_lines = []
            
            # Get metadata dictionary (contains name, source info, etc.)
            # Now using public property instead of private _document_model
            metadata = getattr(model, 'metadata', {}) or {}
            
            model_name = metadata.get('name') or metadata.get('model_name')
            if not model_name and hasattr(model, 'name') and model.name:
                model_name = model.name
            
            if model_name:
                overview_lines.append(f"Model Name: {model_name}")
            elif places_count > 0 or transitions_count > 0:
                # Has objects but no name - user hasn't named it yet
                overview_lines.append("Model Name: Untitled (not saved)")
            else:
                # Empty model with no name
                overview_lines.append("Model Name: Untitled (empty model)")
            
            # Project name
            if self.project and hasattr(self.project, 'name'):
                overview_lines.append(f"Project: {self.project.name}")
            
            # File path (if available)
            if hasattr(model, 'file_path') and model.file_path:
                overview_lines.append(f"File: {model.file_path}")
            
            # Creation date (if available)
            if hasattr(model, 'created_date') and model.created_date:
                try:
                    # Parse ISO format date
                    dt = datetime.fromisoformat(model.created_date.replace('Z', '+00:00'))
                    date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    overview_lines.append(f"Created: {date_str}")
                except (ValueError, AttributeError) as e:
                    # Date parsing failed, use raw string
                    import logging
                    logging.getLogger(__name__).debug(f"Created date parsing failed: {e}")
                    overview_lines.append(f"Created: {model.created_date}")
            
            # Last modified (if available)
            if hasattr(model, 'modified_date') and model.modified_date:
                try:
                    dt = datetime.fromisoformat(model.modified_date.replace('Z', '+00:00'))
                    date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    overview_lines.append(f"Modified: {date_str}")
                except (ValueError, AttributeError) as e:
                    # Date parsing failed, use raw string
                    import logging
                    logging.getLogger(__name__).debug(f"Modified date parsing failed: {e}")
                    overview_lines.append(f"Modified: {model.modified_date}")
            
            # Description (if available)
            if hasattr(model, 'description') and model.description:
                overview_lines.append(f"\nDescription: {model.description}")
            
            overview_text = "\n".join(overview_lines) if overview_lines else "No model information available"
            self.overview_label.set_text(overview_text)
            self.overview_label.show_all()
            # === BUILD PETRI NET STRUCTURE ===
            places_count = len(model.places) if hasattr(model, 'places') else 0
            transitions_count = len(model.transitions) if hasattr(model, 'transitions') else 0
            arcs_count = len(model.arcs) if hasattr(model, 'arcs') else 0
            
            # Check if we successfully retrieved data
            has_places_attr = hasattr(model, 'places')
            has_transitions_attr = hasattr(model, 'transitions')
            has_arcs_attr = hasattr(model, 'arcs')
            
            if not (has_places_attr and has_transitions_attr and has_arcs_attr):
                # Failed to retrieve data structure
                structure_lines = [
                    "⚠️ Error: Failed to retrieve model data",
                    f"Places attribute: {'✓' if has_places_attr else '✗'}",
                    f"Transitions attribute: {'✓' if has_transitions_attr else '✗'}",
                    f"Arcs attribute: {'✓' if has_arcs_attr else '✗'}"
                ]
            elif places_count == 0 and transitions_count == 0:
                # Empty model - valid state for new models
                structure_lines = [
                    "Empty Model (no objects yet)",
                    "Places: 0",
                    "Transitions: 0",
                    "Arcs: 0"
                ]
            else:
                # Normal case - has objects
                structure_lines = [
                    f"Places: {places_count}",
                    f"Transitions: {transitions_count}",
                    f"Arcs: {arcs_count}",
                ]
            
            # Determine model type (if metadata available)
            model_types = []
            if hasattr(model, 'transitions') and model.transitions and transitions_count > 0:
                # Check for different transition types
                # Note: transitions is a list, not a dict
                has_stochastic = any(
                    hasattr(t, 'transition_type') and t.transition_type == 'stochastic'
                    for t in model.transitions if t
                )
                has_continuous = any(
                    hasattr(t, 'transition_type') and t.transition_type == 'continuous'
                    for t in model.transitions if t
                )
                has_timed = any(
                    hasattr(t, 'transition_type') and t.transition_type == 'timed'
                    for t in model.transitions if t
                )
                
                if has_stochastic:
                    model_types.append("Stochastic")
                if has_continuous:
                    model_types.append("Continuous")
                if has_timed:
                    model_types.append("Timed")
                
                # Check for test arcs (biological petri nets)
                # Note: arcs is a list, not a dict
                has_test_arcs = any(
                    hasattr(arc, 'arc_type') and arc.arc_type == 'test'
                    for arc in model.arcs if hasattr(model, 'arcs') and arc
                )
                if has_test_arcs:
                    model_types.append("Bio-PN")
            
            if model_types and places_count > 0:
                structure_lines.append(f"Type: {', '.join(model_types)}")
            
            structure_text = "\n".join(structure_lines)
            self.structure_label.set_text(structure_text)
            self.structure_label.show_all()
            
            # === BUILD IMPORT PROVENANCE (if available) ===
            # Check both pathway_doc and metadata for provenance info
            pathway_doc = self._find_linked_pathway_document(model)
            
            # Get metadata dictionary (now using public property)
            metadata = getattr(model, 'metadata', {}) or {}
            
            provenance_lines = []
            
            # Try pathway_doc first (for active imports)
            if pathway_doc:
                # Source type
                if hasattr(pathway_doc, 'source_type'):
                    source_type = pathway_doc.source_type.upper()
                    provenance_lines.append(f"Source: {source_type}")
                
                # Source ID
                if hasattr(pathway_doc, 'source_id') and pathway_doc.source_id:
                    provenance_lines.append(f"Source ID: {pathway_doc.source_id}")
                
                # Organism
                if hasattr(pathway_doc, 'source_organism') and pathway_doc.source_organism:
                    provenance_lines.append(f"Organism: {pathway_doc.source_organism}")
                
                # Import date
                if hasattr(pathway_doc, 'imported_date') and pathway_doc.imported_date:
                    try:
                        dt = datetime.fromisoformat(pathway_doc.imported_date.replace('Z', '+00:00'))
                        date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                        provenance_lines.append(f"Imported: {date_str}")
                    except (ValueError, AttributeError) as e:
                        # Import date parsing failed
                        import logging
                        logging.getLogger(__name__).debug(f"Import date parsing failed: {e}")
                        provenance_lines.append(f"Imported: {pathway_doc.imported_date}")
                
                # Original file
                if hasattr(pathway_doc, 'raw_file') and pathway_doc.raw_file:
                    provenance_lines.append(f"Original File: {pathway_doc.raw_file}")
                
                # Additional metadata (species/reactions count from import)
                if hasattr(pathway_doc, 'metadata') and pathway_doc.metadata:
                    pmeta = pathway_doc.metadata
                    if 'species_count' in pmeta:
                        provenance_lines.append(f"Imported Species: {pmeta['species_count']}")
                    if 'reactions_count' in pmeta:
                        provenance_lines.append(f"Imported Reactions: {pmeta['reactions_count']}")
            
            # Fallback to metadata dictionary (persists after save/load)
            elif metadata:
                # Source type from metadata
                source = metadata.get('source') or metadata.get('source_type')
                if source:
                    provenance_lines.append(f"Source: {source.upper()}")
                
                # Source ID
                source_id = metadata.get('source_id') or metadata.get('pathway_id')
                if source_id:
                    provenance_lines.append(f"Source ID: {source_id}")
                
                # Organism
                organism = metadata.get('organism') or metadata.get('source_organism')
                if organism:
                    provenance_lines.append(f"Organism: {organism}")
                
                # Import/Creation date
                imported = metadata.get('imported_date') or metadata.get('created')
                if imported:
                    try:
                        dt = datetime.fromisoformat(imported.replace('Z', '+00:00'))
                        date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                        provenance_lines.append(f"Imported: {date_str}")
                    except (ValueError, AttributeError) as e:
                        # Import date parsing failed
                        import logging
                        logging.getLogger(__name__).debug(f"Generic import date parsing failed: {e}")
                        provenance_lines.append(f"Imported: {imported}")
                
                # Original file
                raw_file = metadata.get('raw_file') or metadata.get('original_file')
                if raw_file:
                    provenance_lines.append(f"Original File: {raw_file}")
            
            # Display provenance if we have any data
            if provenance_lines:
                self.provenance_label.set_text("\n".join(provenance_lines))
                self.provenance_label.show_all()
                self.provenance_frame.set_visible(True)
                self.provenance_frame.show_all()
            else:
                # Check if this is an imported model or manually created
                if metadata:
                    # Has metadata but no provenance - might be incomplete data
                    self.provenance_label.set_text("⚠️ Import information not available\n(Model may have been created manually)")
                else:
                    # No metadata at all - clearly manual
                    self.provenance_label.set_text("✓ Manually created model\n(No import provenance)")
                self.provenance_label.show_all()
                self.provenance_frame.set_visible(True)
                self.provenance_frame.show_all()
            
            # === DEFER DETAILED TABLES POPULATION ===
            # Instead of populating tables immediately (expensive for large models),
            # mark them as needing refresh and populate lazily when user expands them
            # This makes refresh instant for large models (rn00071 with 268 objects)
            self._species_table_needs_refresh = True
            self._reactions_table_needs_refresh = True
            
            # Clear tables immediately to show they're ready for data
            self.species_store.clear()
            self.reactions_store.clear()
            
            # === REFRESH LOCALITY TABLE IF SELECTION EXISTS ===
            if self.selected_transition and self.selected_locality:
                self._populate_locality_table()
            
            # Force the entire category to redraw
            if hasattr(self, 'category_frame') and self.category_frame:
                self.category_frame.show_all()
                self.category_frame.queue_draw()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.overview_label.set_text(f"Error: {e}")
            
    def _find_linked_pathway_document(self, model):
        """Find the PathwayDocument linked to this model.
        
        Args:
            model: Current model instance
            
        Returns:
            PathwayDocument or None if not found
        """
        if not self.project:
            return None
        
        # Get model ID
        model_id = None
        if hasattr(model, 'id'):
            model_id = model.id
        elif hasattr(self.model_canvas, 'model_id'):
            model_id = self.model_canvas.model_id
        
        if not model_id:
            return None
        
        # Search in project's pathway documents
        if hasattr(self.project, 'pathway_documents') and self.project.pathway_documents:
            for pathway_doc in self.project.pathway_documents:
                if hasattr(pathway_doc, 'model_id') and pathway_doc.model_id == model_id:
                    return pathway_doc
        
        # Search in legacy pathways structure
        if hasattr(self.project, 'pathways') and isinstance(self.project.pathways, dict):
            for pathway_id, pathway_doc in self.project.pathways.items():
                if hasattr(pathway_doc, 'model_id') and pathway_doc.model_id == model_id:
                    return pathway_doc
        
        return None
    
    def _populate_species_table(self, model):
        """Populate species table with current model data.
        
        Minimal view: only essential columns.
        
        Args:
            model: DocumentModel instance
        """
        self.species_store.clear()
        
        if not hasattr(model, 'places') or not model.places:
            return
        
        for i, place in enumerate(model.places, 1):
            if not place:
                continue
            
            # Extract data
            place_id = place.id if hasattr(place, 'id') else f"P{i}"
            name = place.label if hasattr(place, 'label') and place.label else place_id
            
            # Initial tokens
            tokens = 0.0
            if hasattr(place, 'initial_marking'):
                tokens = float(place.initial_marking)
            elif hasattr(place, 'tokens'):
                tokens = float(place.tokens)
            
            # Token units
            token_units = "arbitrary"
            if hasattr(place, 'metadata') and place.metadata:
                token_units = place.metadata.get('concentration_units',
                             place.metadata.get('amount_units',
                             place.metadata.get('units', 'arbitrary')))
            
            # Mass
            mass = 0.0
            mass_source = "unknown"
            if hasattr(place, 'metadata') and place.metadata:
                mass_val = place.metadata.get('mass', 
                           place.metadata.get('molecular_weight', 0))
                if mass_val:
                    try:
                        mass = float(mass_val)
                        mass_source = place.metadata.get('mass_source',
                                     place.metadata.get('data_source', 'kegg_import'))
                    except (ValueError, TypeError):
                        mass = 0.0
            
            # Conservation status
            conservation_status = "Unknown"
            if hasattr(place, 'metadata') and place.metadata:
                conservation_status = place.metadata.get('conservation_status', 'Unknown')
            # Infer from boundary condition if not set
            if conservation_status == "Unknown":
                if hasattr(place, 'boundary_condition'):
                    conservation_status = "Buffered" if place.boundary_condition else "Conserved"
                elif hasattr(place, 'metadata') and place.metadata:
                    is_boundary = place.metadata.get('boundary_condition', False)
                    conservation_status = "Buffered" if is_boundary else "Conserved"
            
            # Add row to table (minimal columns)
            self.species_store.append([
                i,                      # 0: index
                place_id,               # 1: Petri Net ID
                name,                   # 2: Biological Name
                tokens,                 # 3: Initial Tokens
                token_units,            # 4: Token Units
                mass,                   # 5: Mass
                mass_source,            # 6: Mass source
                conservation_status     # 7: Conservation Status
            ])
    
    def _populate_reactions_table(self, model):
        """Populate reactions table with current model data.
        
        REFACTORED (Sprint 2): Extracted helper methods to reduce complexity.
        Original complexity: 55 → New complexity: <15
        
        New structure: #, ID, Name, Type, EC Number, Vmax, Km, Kcat, Ki, Rate Function, Reversible
        
        Args:
            model: DocumentModel instance
        """
        self.reactions_store.clear()
        
        if not hasattr(model, 'transitions') or not model.transitions:
            return
        
        for i, transition in enumerate(model.transitions, 1):
            if not transition:
                continue
            
            # Extract basic data
            trans_id = transition.id if hasattr(transition, 'id') else f"T{i}"
            name = transition.label if hasattr(transition, 'label') and transition.label else trans_id
            trans_type = transition.transition_type if hasattr(transition, 'transition_type') else "unknown"
            
            # Extract complex data using helper methods
            ec_number = self._extract_ec_number(transition, name)
            vmax, vmax_source, km, km_source, kcat, kcat_source, ki, ki_source = \
                self._extract_kinetic_parameters(transition)
            rate_function = self._extract_rate_function(transition, trans_type)
            reversible = self._extract_reversible_status(transition)
            
            # Add row to table
            self.reactions_store.append([
                i, trans_id, name, trans_type, ec_number,
                vmax, vmax_source, km, km_source,
                kcat, kcat_source, ki, ki_source,
                rate_function, reversible
            ])

    def _extract_ec_number(self, transition, name: str) -> str:
        """Extract EC number from transition with multi-priority fallback.
        
        Priority order:
        1. reaction_code (e.g., "EC:1.1.1.1")
        2. KEGG reaction ID (fetch from API)
        3. metadata ec_number field
        
        Returns:
            str: EC number or "-" if not found
        """
        ec_number = "-"
        
        # Priority 1: Extract from reaction_code
        if hasattr(transition, 'reaction_code') and transition.reaction_code:
            reaction_code = transition.reaction_code
            if reaction_code.startswith('EC:'):
                ec_number = reaction_code.replace('EC:', '')
            elif reaction_code.startswith('ec:'):
                ec_number = reaction_code.replace('ec:', '')
            elif not reaction_code.startswith('R'):
                ec_number = reaction_code
        
        # Priority 2: Extract from KEGG reaction ID
        if ec_number == "-":
            kegg_reaction_id = self._get_kegg_reaction_id(transition, name)
            if kegg_reaction_id and kegg_reaction_id.startswith('R'):
                ec_number = self._fetch_ec_from_kegg(transition, kegg_reaction_id)
        
        # Priority 3: Fallback to metadata ec_number
        if ec_number == "-" and hasattr(transition, 'metadata') and transition.metadata:
            ec_val = transition.metadata.get('ec_number', transition.metadata.get('ec_numbers', []))
            if isinstance(ec_val, list) and ec_val:
                ec_number = ec_val[0]
            elif ec_val and ec_val != '-':
                ec_number = str(ec_val)
        
        return ec_number

    def _get_kegg_reaction_id(self, transition, name: str) -> str:
        """Get KEGG reaction ID from various sources."""
        kegg_reaction_id = None
        
        # Check metadata
        if hasattr(transition, 'metadata') and transition.metadata:
            kegg_reaction_id = transition.metadata.get('kegg_reaction_id',
                              transition.metadata.get('reaction_id', ''))
        
        # Check reaction_code
        if not kegg_reaction_id and hasattr(transition, 'reaction_code') and transition.reaction_code:
            if transition.reaction_code.startswith('R') or transition.reaction_code.startswith('rn:R'):
                kegg_reaction_id = transition.reaction_code
        
        # Check label
        if not kegg_reaction_id and name and (name.startswith('R') or name.startswith('rn:R')):
            kegg_reaction_id = name
        
        if kegg_reaction_id:
            kegg_reaction_id = kegg_reaction_id.replace('rn:', '').strip()
        
        return kegg_reaction_id

    def _fetch_ec_from_kegg(self, transition, kegg_reaction_id: str) -> str:
        """Fetch EC number from KEGG API for given reaction ID."""
        ec_number = "-"
        
        # First check if EC already in metadata
        if hasattr(transition, 'metadata') and transition.metadata:
            ec_val = transition.metadata.get('ec_number', transition.metadata.get('ec_numbers', []))
            if isinstance(ec_val, list) and ec_val:
                ec_number = ec_val[0]
            elif ec_val and ec_val != '-':
                ec_number = str(ec_val)
        
        # Fetch from API if not found
        if ec_number == "-":
            try:
                ec_numbers = self.kegg_ec_fetcher.fetch_ec_numbers(kegg_reaction_id)
                if ec_numbers and len(ec_numbers) > 0:
                    ec_number = ec_numbers[0]
                    # Store in metadata
                    if not hasattr(transition, 'metadata'):
                        transition.metadata = {}
                    if not transition.metadata:
                        transition.metadata = {}
                    transition.metadata['ec_number'] = ec_number
            except (KeyError, AttributeError, IndexError) as e:
                self.logger.debug(f"Failed to extract EC number from KEGG compound_names for transition {transition.id}: {e}")
        
        return ec_number

    def _extract_kinetic_parameters(self, transition) -> tuple:
        """Extract kinetic parameters with multi-source fallback.
        
        Returns:
            tuple: (vmax, vmax_source, km, km_source, kcat, kcat_source, ki, ki_source)
        """
        vmax, vmax_source = 0.0, "unknown"
        km, km_source = 0.0, "unknown"
        kcat, kcat_source = 0.0, "unknown"
        ki, ki_source = 0.0, "unknown"
        
        if not (hasattr(transition, 'metadata') and transition.metadata):
            return vmax, vmax_source, km, km_source, kcat, kcat_source, ki, ki_source
        
        metadata = transition.metadata
        
        # Direct metadata (BRENDA/SABIO-RK enrichment)
        if 'vmax' in metadata:
            vmax = float(metadata['vmax'])
            vmax_source = metadata.get('vmax_source', metadata.get('data_source', 'unknown'))
        
        if 'km' in metadata:
            km = float(metadata['km'])
            km_source = metadata.get('km_source', metadata.get('data_source', 'unknown'))
        
        if 'kcat' in metadata:
            kcat = float(metadata['kcat'])
            kcat_source = metadata.get('kcat_source', metadata.get('data_source', 'unknown'))
        
        if 'ki' in metadata:
            ki = float(metadata['ki'])
            ki_source = metadata.get('ki_source', metadata.get('data_source', 'unknown'))
        
        # kinetic_parameters dict (SBML/KEGG import)
        params = metadata.get('kinetic_parameters', {})
        if params and isinstance(params, dict):
            if vmax == 0.0:
                vmax_val = params.get('Vmax', params.get('vmax', params.get('V_max', 0.0)))
                if vmax_val:
                    vmax = float(vmax_val)
                    vmax_source = metadata.get('data_source', 'kegg_import')
            
            if km == 0.0:
                km_val = params.get('Km', params.get('km', params.get('KM', 0.0)))
                if km_val:
                    km = float(km_val)
                    km_source = metadata.get('data_source', 'kegg_import')
            
            if kcat == 0.0:
                kcat_val = params.get('Kcat', params.get('kcat', params.get('k_cat', 0.0)))
                if kcat_val:
                    kcat = float(kcat_val)
                    kcat_source = metadata.get('data_source', 'kegg_import')
            
            if ki == 0.0:
                ki_val = params.get('Ki', params.get('ki', params.get('KI', 0.0)))
                if ki_val:
                    ki = float(ki_val)
                    ki_source = metadata.get('data_source', 'kegg_import')
        
        # estimated_parameters dict (KEGG heuristic estimator)
        estimated_params = metadata.get('estimated_parameters', {})
        if estimated_params and isinstance(estimated_params, dict):
            if vmax == 0.0:
                vmax_val = estimated_params.get('vmax', 0.0)
                if vmax_val:
                    vmax = float(vmax_val)
                    vmax_source = 'kegg_heuristic'
            
            if km == 0.0:
                km_val = estimated_params.get('km', 0.0)
                if km_val:
                    km = float(km_val)
                    km_source = 'kegg_heuristic'
        
        return vmax, vmax_source, km, km_source, kcat, kcat_source, ki, ki_source

    def _extract_rate_function(self, transition, trans_type: str) -> str:
        """Extract rate function with priority fallback.
        
        Priority order:
        1. transition.properties['rate_function']
        2. transition.rate_function attribute
        3. metadata rate_function/kinetic_formula/kinetic_law
        4. Default "mass_action" for stochastic transitions
        
        Returns:
            str: Rate function or "-" if not found
        """
        rate_function = "-"
        
        # Priority 1: properties dict
        if hasattr(transition, 'properties') and transition.properties:
            if isinstance(transition.properties, dict):
                rate_function = transition.properties.get('rate_function', '-')
        
        # Priority 2: direct attribute
        if rate_function == "-" and hasattr(transition, 'rate_function'):
            if transition.rate_function:
                rate_function = transition.rate_function
        
        # Priority 3: metadata
        if rate_function == "-" and hasattr(transition, 'metadata') and transition.metadata:
            rate_function = transition.metadata.get('rate_function',
                           transition.metadata.get('kinetic_formula',
                           transition.metadata.get('kinetic_law', '-')))
        
        # Priority 4: default for stochastic
        if rate_function == "-" and trans_type == 'stochastic':
            rate_function = "mass_action"
        
        return rate_function

    def _extract_reversible_status(self, transition) -> str:
        """Extract reversible status from metadata.
        
        Returns:
            str: "Yes", "No", or "Unknown"
        """
        reversible = "Unknown"
        if hasattr(transition, 'metadata') and transition.metadata:
            rev_val = transition.metadata.get('reversible')
            if rev_val is not None:
                reversible = "Yes" if rev_val else "No"
        return reversible
    
    def _populate_locality_table(self):
        """Populate locality table with selected transition + locality places.
        
        Called when user selects transition in Analyses panel.
        Shows: Input Places → Transition → Output Places in unified table.
        """
        self.locality_store.clear()
        
        if not self.selected_transition or not self.selected_locality:
            # Hide expander when no selection
            self.locality_expander.set_visible(False)
            return
        
        # Show expander
        self.locality_expander.set_visible(True)
        
        transition = self.selected_transition
        locality = self.selected_locality
        
        index = 0
        
        # === ADD INPUT PLACES ===
        for place in locality.input_places:
            index += 1
            
            # Extract place data
            place_id = f"P{place.id}"
            bio_name = getattr(place, 'biological_name', getattr(place, 'name', f'Place_{place.id}'))
            tokens = getattr(place, 'tokens', 0.0)
            units = getattr(place, 'token_units', 'tokens')
            
            # Mass parameter
            mass = getattr(place, 'mass', 0.0)
            mass_source = getattr(place, 'mass_source', 'unknown')
            params = f"Mass: {mass:.2f} g/mol ({mass_source})" if mass > 0 else "Mass: N/A"
            
            self.locality_store.append([
                index,
                "Place",
                "← Input",
                place_id,
                bio_name,
                f"{tokens:.3f}",
                tokens,
                units,
                params
            ])
        
        # === ADD TRANSITION ===
        index += 1
        
        trans_id = f"T{transition.id}"
        trans_name = getattr(transition, 'biological_name', getattr(transition, 'name', f'T{transition.id}'))
        trans_type = getattr(transition, 'transition_type', 'continuous')
        
        # Type abbreviation
        type_abbrev = {
            'immediate': 'IMM',
            'timed': 'TIM',
            'stochastic': 'STO',
            'continuous': 'CON'
        }.get(trans_type, trans_type[:3].upper())
        
        # Check source/sink status
        is_source = getattr(transition, 'is_source', False)
        is_sink = getattr(transition, 'is_sink', False)
        if is_source:
            type_abbrev += '+SRC'
        elif is_sink:
            type_abbrev += '+SNK'
        
        # Extract rate and parameters
        rate = getattr(transition, 'rate', 0.0)
        # Handle case where rate might be a string expression (rate_function)
        if isinstance(rate, str):
            # For continuous transitions with rate_function, show as N/A
            rate = 0.0
        else:
            try:
                rate = float(rate)
            except (ValueError, TypeError):
                rate = 0.0
        units = getattr(transition, 'rate_units', '1/s')
        
        # Build parameters string
        params_list = []
        if hasattr(transition, 'ec_number') and transition.ec_number:
            params_list.append(f"EC:{transition.ec_number}")
        if hasattr(transition, 'vmax') and transition.vmax and transition.vmax > 0:
            params_list.append(f"Vmax:{transition.vmax:.3g}")
        if hasattr(transition, 'km') and transition.km and transition.km > 0:
            params_list.append(f"Km:{transition.km:.3g}")
        if hasattr(transition, 'kcat') and transition.kcat and transition.kcat > 0:
            params_list.append(f"Kcat:{transition.kcat:.3g}")
        params = " ".join(params_list) if params_list else "N/A"
        
        self.locality_store.append([
            index,
            "Transition",
            "",  # No direction for transition
            trans_id,
            trans_name,
            type_abbrev,
            rate,
            units,
            params
        ])
        
        # === ADD OUTPUT PLACES ===
        for place in locality.output_places:
            index += 1
            
            # Extract place data
            place_id = f"P{place.id}"
            bio_name = getattr(place, 'biological_name', getattr(place, 'name', f'Place_{place.id}'))
            tokens = getattr(place, 'tokens', 0.0)
            units = getattr(place, 'token_units', 'tokens')
            
            # Mass parameter
            mass = getattr(place, 'mass', 0.0)
            mass_source = getattr(place, 'mass_source', 'unknown')
            params = f"Mass: {mass:.2f} g/mol ({mass_source})" if mass > 0 else "Mass: N/A"
            
            self.locality_store.append([
                index,
                "Place",
                "→ Output",
                place_id,
                bio_name,
                f"{tokens:.3f}",
                tokens,
                units,
                params
            ])
        
        # Update expander label with count
        n_inputs = len(locality.input_places)
        n_outputs = len(locality.output_places)
        total = n_inputs + 1 + n_outputs
        self.locality_expander.set_label(
            f"Show Selected Locality: {trans_name} ({n_inputs}→T→{n_outputs}, {total} rows)"
        )
    
    def _build_species_list(self, model):
        """DEPRECATED: Old text-based species list builder.
        
        Kept for backwards compatibility with export functions.
        Use _populate_species_table() for UI display.
        
        Format: Internal ID | Label | Metadata (KEGG codes, formulas, etc.)
        """
        if not hasattr(model, 'places') or not model.places:
            return "No species found"
        
        lines = [
            f"Total Species/Places: {len(model.places)}",
            "",
            "Format: [Internal ID] Label | Metadata",
            "-" * 60,
            ""
        ]
        
        # Note: places is a list, not a dict
        for i, place in enumerate(model.places, 1):
            if not place:
                continue
            
            # Get internal ID
            place_id = place.id if hasattr(place, 'id') else f"P{i}"
            
            # Get label
            label = "Unnamed"
            if hasattr(place, 'label') and place.label:
                label = place.label
            elif hasattr(place, 'id'):
                label = place.id
            
            # Build line
            line_parts = [f"{i}. [{place_id}] {label}"]
            
            # Add metadata if available
            metadata_items = []
            if hasattr(place, 'metadata') and place.metadata:
                metadata = place.metadata
                
                # KEGG compound code
                if 'kegg_id' in metadata:
                    metadata_items.append(f"KEGG:{metadata['kegg_id']}")
                elif 'compound_id' in metadata:
                    metadata_items.append(f"KEGG:{metadata['compound_id']}")
                
                # Chemical formula
                if 'formula' in metadata:
                    metadata_items.append(f"Formula:{metadata['formula']}")
                
                # Molecular mass
                if 'mass' in metadata:
                    metadata_items.append(f"Mass:{metadata['mass']}")
                
                # Any other relevant metadata
                if 'type' in metadata:
                    metadata_items.append(f"Type:{metadata['type']}")
            
            if metadata_items:
                line_parts.append(" | " + ", ".join(metadata_items))
            
            lines.append("".join(line_parts))
        
        return "\n".join(lines)
    
    def _build_reactions_list(self, model):
        """Build comprehensive reactions/transitions list with metadata.
        
        Format:
        Internal ID | Label | Type | Metadata (EC numbers, KEGG reactions, etc.)
        """
        if not hasattr(model, 'transitions') or not model.transitions:
            return "No reactions found"
        
        lines = [
            f"Total Reactions/Transitions: {len(model.transitions)}",
            "",
            "Format: [Internal ID] Label | Type | Metadata",
            "-" * 60,
            ""
        ]
        
        # Note: transitions is a list, not a dict
        for i, transition in enumerate(model.transitions, 1):
            if not transition:
                continue
            
            # Get internal ID
            trans_id = transition.id if hasattr(transition, 'id') else f"T{i}"
            
            # Get label
            label = "Unnamed"
            if hasattr(transition, 'label') and transition.label:
                label = transition.label
            elif hasattr(transition, 'id'):
                label = transition.id
            
            # Get transition type
            trans_type = "unknown"
            if hasattr(transition, 'transition_type'):
                trans_type = transition.transition_type
            
            # Build line
            line_parts = [f"{i}. [{trans_id}] {label} | {trans_type}"]
            
            # Add metadata if available
            metadata_items = []
            if hasattr(transition, 'metadata') and transition.metadata:
                metadata = transition.metadata
                
                # KEGG reaction ID
                if 'kegg_reaction_id' in metadata:
                    metadata_items.append(f"KEGG:{metadata['kegg_reaction_id']}")
                elif 'reaction_id' in metadata:
                    metadata_items.append(f"Reaction:{metadata['reaction_id']}")
                
                # EC number (enzyme classification)
                if 'ec_number' in metadata:
                    metadata_items.append(f"EC:{metadata['ec_number']}")
                
                # Kinetic law type
                if 'kinetic_law' in metadata:
                    metadata_items.append(f"Kinetics:{metadata['kinetic_law']}")
                
                # Any other relevant metadata
                if 'type' in metadata:
                    metadata_items.append(f"Type:{metadata['type']}")
            
            if metadata_items:
                line_parts.append(" | " + ", ".join(metadata_items))
            
            lines.append("".join(line_parts))
        
        return "\n".join(lines)
    
    def export_to_text(self):
        """Export comprehensive model information as plain text."""
        if not self.model_canvas or not hasattr(self.model_canvas, 'model'):
            return "# MODELS\n\nNo model loaded\n"
        
        sections = [
            "=" * 80,
            "MODELS CATEGORY - SCIENTIFIC REPORT",
            "=" * 80,
            "",
            "## Model Overview",
            "-" * 80,
            self.overview_label.get_text(),
            "",
            "## Petri Net Structure",
            "-" * 80,
            self.structure_label.get_text(),
            ""
        ]
        
        # Add provenance if visible
        if self.provenance_frame.get_visible():
            sections.extend([
                "## Import Provenance",
                "-" * 80,
                self.provenance_label.get_text(),
                ""
            ])
        
        # Add detailed tables if expanders are expanded
        if self.species_expander.get_expanded():
            sections.extend([
                "## Species/Places Table",
                "-" * 80,
                self._export_species_table(),
                ""
            ])
        
        if self.reactions_expander.get_expanded():
            sections.extend([
                "## Reactions/Transitions Table",
                "-" * 80,
                self._export_reactions_table(),
                ""
            ])
        
        sections.append("=" * 80)
        
        return "\n".join(sections)
    
    def _export_species_table(self):
        """Export species table as formatted text.
        
        Minimal view with essential columns only.
        
        Returns:
            str: Formatted table as text
        """
        if not self.species_store or len(self.species_store) == 0:
            return "No species data"
        
        lines = [
            f"Total Species/Places: {len(self.species_store)}",
            "",
            "{:<5} {:<15} {:<30} {:<15} {:<15} {:<15} {:<15}".format(
                "#", "Petri Net ID", "Biological Name", "Initial Amount",
                "Units", "Mass (g/mol)", "Conservation"
            ),
            "-" * 115
        ]
        
        for row in self.species_store:
            lines.append(
                "{:<5} {:<15} {:<30} {:<15.4g} {:<15} {:<15.2f} {:<15}".format(
                    row[0],      # 0: index
                    row[1][:14], # 1: Petri Net ID
                    row[2][:29], # 2: Biological Name
                    row[3],      # 3: Initial Tokens
                    row[4][:14], # 4: Token Units
                    row[5] if row[5] > 0 else 0,  # 5: Mass
                    row[7][:14]  # 7: Conservation Status
                )
            )
        
        return "\n".join(lines)
    
    def _export_reactions_table(self):
        """Export reactions table as formatted text.
        
        New structure: #, ID, Name, Type, EC Number, Vmax, Km, Kcat, Ki, Rate Function, Reversible
        
        Returns:
            str: Formatted table as text
        """
        if not self.reactions_store or len(self.reactions_store) == 0:
            return "No reactions data"
        
        lines = [
            f"Total Reactions/Transitions: {len(self.reactions_store)}",
            "",
            "{:<5} {:<15} {:<30} {:<12} {:<15} {:<12} {:<12} {:<12} {:<12} {:<40} {:<10}".format(
                "#", "Petri Net ID", "Biological Name", "Type", 
                "EC Number", "Vmax", "Km", "Kcat", "Ki", "Rate Function", "Reversible"
            ),
            "-" * 180
        ]
        
        for row in self.reactions_store:
            # Format rate function (truncate if too long)
            rate_func_str = row[13][:39] if row[13] != "-" else "-"
            
            lines.append(
                "{:<5} {:<15} {:<30} {:<12} {:<15} {:<12.4g} {:<12.4g} {:<12.4g} {:<12.4g} {:<40} {:<10}".format(
                    row[0],           # 0: index
                    row[1][:14],      # 1: Petri Net ID
                    row[2][:29],      # 2: Biological Name
                    row[3][:11],      # 3: Type
                    row[4][:14],      # 4: EC Number
                    row[5] if row[5] > 0 else 0,  # 5: Vmax
                    row[7] if row[7] > 0 else 0,  # 7: Km
                    row[9] if row[9] > 0 else 0,  # 9: Kcat
                    row[11] if row[11] > 0 else 0,  # 11: Ki
                    rate_func_str,    # 13: Rate Function
                    row[14][:9]       # 14: Reversible
                )
            )
        
        return "\n".join(lines)
    
    def set_selected_locality(self, transition, locality):
        """Set the selected transition and its locality for display.
        
        Called from Analyses panel when user selects a transition.
        
        Args:
            transition: Transition object
            locality: Locality object from LocalityDetector
        """
        self.selected_transition = transition
        self.selected_locality = locality
        
        self._populate_locality_table()
    
    def get_structured_data(self):
        """Get structured model data for document generation.
        
        Returns:
            dict: Model data with keys:
                - title: 'Model Structure'
                - has_data: Boolean
                - overview: dict with name, project, file_path, dates, description
                - structure: dict with places_count, transitions_count, arcs_count, model_types
                - provenance: dict with source info (if available)
                - species: list of dicts with species data
                - reactions: list of dicts with reaction data
        """
        # Get current active model dynamically
        model = self.get_current_model()
        if not model:
            return {
                'title': 'Model Structure',
                'has_data': False,
                'summary': 'No model loaded'
            }
        
        # Extract overview data
        overview = {
            'name': getattr(model, 'name', 'Untitled'),
            'project': self.project.name if self.project and hasattr(self.project, 'name') else None,
            'file_path': getattr(model, 'file_path', None),
            'created_date': getattr(model, 'created_date', None),
            'modified_date': getattr(model, 'modified_date', None),
            'description': getattr(model, 'description', None)
        }
        
        # Extract structure counts
        places_count = len(model.places) if hasattr(model, 'places') else 0
        transitions_count = len(model.transitions) if hasattr(model, 'transitions') else 0
        arcs_count = len(model.arcs) if hasattr(model, 'arcs') else 0
        
        structure = {
            'places_count': places_count,
            'transitions_count': transitions_count,
            'arcs_count': arcs_count,
            'model_types': self._extract_model_types(model)
        }
        
        # Extract provenance data (if available from metadata)
        provenance = self._extract_provenance_data(model)
        
        # Extract species data from TreeView store
        species = []
        if self.species_store:
            for row in self.species_store:
                species.append({
                    'index': row[0],
                    'id': row[1],
                    'name': row[2],
                    'initial_tokens': row[3],
                    'units': row[4],
                    'mass': row[5],
                    'conservation': row[7]
                })
        
        # Extract reaction data from TreeView store
        reactions = []
        if self.reactions_store:
            for row in self.reactions_store:
                reactions.append({
                    'index': row[0],
                    'id': row[1],
                    'name': row[2],
                    'type': row[3],
                    'ec_number': row[4],
                    'vmax': row[5],
                    'km': row[7],
                    'kcat': row[9],
                    'ki': row[11],
                    'rate_function': row[13],
                    'reversible': row[14]
                })
        
        return {
            'title': 'Model Structure',
            'has_data': True,
            'overview': overview,
            'structure': structure,
            'provenance': provenance,
            'species': species,
            'reactions': reactions
        }
    
    def _extract_model_types(self, model):
        """Extract model type information.
        
        Returns:
            list: List of model type strings (e.g., ['Stochastic', 'Timed'])
        """
        model_types = []
        if hasattr(model, 'transitions') and model.transitions:
            has_stochastic = any(
                hasattr(t, 'transition_type') and t.transition_type == 'stochastic'
                for t in model.transitions if t
            )
            has_continuous = any(
                hasattr(t, 'transition_type') and t.transition_type == 'continuous'
                for t in model.transitions if t
            )
            has_timed = any(
                hasattr(t, 'transition_type') and t.transition_type == 'timed'
                for t in model.transitions if t
            )
            
            if has_stochastic:
                model_types.append('Stochastic')
            if has_continuous:
                model_types.append('Continuous')
            if has_timed:
                model_types.append('Timed')
        
        if not model_types:
            model_types.append('Standard')
        
        return model_types
    
    def _extract_provenance_data(self, model):
        """Extract provenance/import data if available.
        
        Returns:
            dict: Provenance data or None if not available
        """
        # Check for import metadata
        metadata = getattr(model, 'metadata', {})
        if isinstance(metadata, dict):
            import_data = metadata.get('import', {})
            if import_data:
                return {
                    'source_type': import_data.get('source_type'),
                    'source_id': import_data.get('source_id'),
                    'organism': import_data.get('organism'),
                    'import_date': import_data.get('import_date')
                }
        
        return None
