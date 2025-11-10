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
from gi.repository import Gtk
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
                print(f"[REPORT→KB] ⚠️ No KB available for structural update")
                return
            
            print(f"[REPORT→KB] Updating structural knowledge...")
            
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
            
            # Transitions
            if hasattr(model, 'transitions') and model.transitions:
                for transition in model.transitions:
                    if transition:
                        trans_info = {
                            'transition_id': transition.id if hasattr(transition, 'id') else str(id(transition)),
                            'label': transition.label if hasattr(transition, 'label') else '',
                        }
                        transitions_data.append(trans_info)
            
            # Arcs
            if hasattr(model, 'arcs') and model.arcs:
                for arc in model.arcs:
                    if arc:
                        arc_info = {
                            'arc_id': arc.id if hasattr(arc, 'id') else str(id(arc)),
                            'source_id': arc.source.id if hasattr(arc, 'source') and hasattr(arc.source, 'id') else None,
                            'target_id': arc.target.id if hasattr(arc, 'target') and hasattr(arc.target, 'id') else None,
                            'weight': arc.weight if hasattr(arc, 'weight') else 1,
                        }
                        arcs_data.append(arc_info)
            
            # Update KB
            kb.update_topology_structural(places_data, transitions_data, arcs_data)
            print(f"[REPORT→KB] ✓ Updated: {len(places_data)} places, {len(transitions_data)} transitions, {len(arcs_data)} arcs")
            
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
            
            print(f"[PATHWAY→KB] Updating pathway knowledge...")
            
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
            
            if compounds_added > 0 or reactions_added > 0:
                print(f"[PATHWAY→KB] ✓ Updated: {compounds_added} compounds, {reactions_added} reactions")
            
        except Exception as e:
            import traceback
            print(f"[PATHWAY→KB] ⚠️ Failed to update pathway knowledge: {e}")
            traceback.print_exc()
    
    def refresh(self):
        """Refresh tables when model changes or tab switches."""
        # If no model, show empty state
        if not self.model_canvas:
            self.overview_label.set_text("No model loaded")
            self.structure_label.set_text("No data")
            self.provenance_label.set_text("No import data")
            # Hide provenance frame when no data
            self.provenance_frame.hide()
            return
        
        # The model_canvas IS the model (ModelCanvasManager with places/transitions/arcs)
        model = self.model_canvas
        
        # UPDATE KNOWLEDGE BASE with structural data
        self._update_knowledge_base_structural(model)
        
        # UPDATE KNOWLEDGE BASE with pathway metadata
        self._update_knowledge_base_pathway(model)
        
        # === BUILD MODEL OVERVIEW ===
        overview_lines = []
        
        # Model name
        if hasattr(model, 'name') and model.name:
            overview_lines.append(f"Model Name: {model.name}")
        else:
            overview_lines.append("Model Name: Untitled")
        
        # Project name
        if self.project and hasattr(self.project, 'name'):
            overview_lines.append(f"Project: {self.project.name}")
        
        # File path (if available)
        if hasattr(model, 'file_path') and model.file_path:
            overview_lines.append(f"File: {model.file_path}")
        elif hasattr(self.model_canvas, 'file_path') and self.model_canvas.file_path:
            overview_lines.append(f"File: {self.model_canvas.file_path}")
        
        # Creation date (if available)
        if hasattr(model, 'created_date') and model.created_date:
            try:
                # Parse ISO format date
                dt = datetime.fromisoformat(model.created_date.replace('Z', '+00:00'))
                date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                overview_lines.append(f"Created: {date_str}")
            except:
                overview_lines.append(f"Created: {model.created_date}")
        
        # Last modified (if available)
        if hasattr(model, 'modified_date') and model.modified_date:
            try:
                dt = datetime.fromisoformat(model.modified_date.replace('Z', '+00:00'))
                date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                overview_lines.append(f"Modified: {date_str}")
            except:
                overview_lines.append(f"Modified: {model.modified_date}")
        
        # Description (if available)
        if hasattr(model, 'description') and model.description:
            overview_lines.append(f"\nDescription: {model.description}")
        
        self.overview_label.set_text("\n".join(overview_lines) if overview_lines else "No model information available")
        
        # === BUILD PETRI NET STRUCTURE ===
        places_count = len(model.places) if hasattr(model, 'places') else 0
        transitions_count = len(model.transitions) if hasattr(model, 'transitions') else 0
        arcs_count = len(model.arcs) if hasattr(model, 'arcs') else 0
        
        structure_lines = [
            f"Places: {places_count}",
            f"Transitions: {transitions_count}",
            f"Arcs: {arcs_count}",
        ]
        
        # Determine model type (if metadata available)
        model_types = []
        if hasattr(model, 'transitions') and model.transitions:
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
        
        if model_types:
            structure_lines.append(f"Type: {', '.join(model_types)}")
        
        self.structure_label.set_text("\n".join(structure_lines))
        
        # === BUILD IMPORT PROVENANCE (if available) ===
        pathway_doc = self._find_linked_pathway_document(model)
        
        if pathway_doc:
            provenance_lines = []
            
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
                except:
                    provenance_lines.append(f"Imported: {pathway_doc.imported_date}")
            
            # Original file
            if hasattr(pathway_doc, 'raw_file') and pathway_doc.raw_file:
                provenance_lines.append(f"Original File: {pathway_doc.raw_file}")
            
            # Additional metadata (species/reactions count from import)
            if hasattr(pathway_doc, 'metadata') and pathway_doc.metadata:
                metadata = pathway_doc.metadata
                if 'species_count' in metadata:
                    provenance_lines.append(f"Imported Species: {metadata['species_count']}")
                if 'reactions_count' in metadata:
                    provenance_lines.append(f"Imported Reactions: {metadata['reactions_count']}")
            
            self.provenance_label.set_text("\n".join(provenance_lines))
            self.provenance_frame.set_visible(True)
        else:
            self.provenance_label.set_text("No import data available (manually created model)")
            self.provenance_frame.set_visible(False)
        
        # === BUILD DETAILED TABLES ===
        self._populate_species_table(model)
        self._populate_reactions_table(model)
        
        # === REFRESH LOCALITY TABLE IF SELECTION EXISTS ===
        if self.selected_transition and self.selected_locality:
            self._populate_locality_table()
    
    def _find_linked_pathway_document(self, model):
        """Find the PathwayDocument linked to this model.
        
        Args:
            model: Current model instance
            
        Returns:
            PathwayDocument instance or None
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
            
            # Extract data
            trans_id = transition.id if hasattr(transition, 'id') else f"T{i}"
            name = transition.label if hasattr(transition, 'label') and transition.label else trans_id
            
            # Type
            trans_type = "unknown"
            if hasattr(transition, 'transition_type'):
                trans_type = transition.transition_type
            
            # EC Number - Multi-priority extraction
            ec_number = "-"
            
            # Priority 1: Extract from reaction_code (e.g., "EC:1.1.1.1")
            if hasattr(transition, 'reaction_code') and transition.reaction_code:
                reaction_code = transition.reaction_code
                if reaction_code.startswith('EC:'):
                    ec_number = reaction_code.replace('EC:', '')
                elif reaction_code.startswith('ec:'):
                    ec_number = reaction_code.replace('ec:', '')
                elif not reaction_code.startswith('R'):
                    # If it's not a KEGG R number, assume it's an EC number
                    ec_number = reaction_code
            
            # Priority 2: Extract from KEGG reaction ID (R00XXX -> EC via API/metadata)
            if ec_number == "-":
                kegg_reaction_id = None
                
                # Check metadata first
                if hasattr(transition, 'metadata') and transition.metadata:
                    kegg_reaction_id = transition.metadata.get('kegg_reaction_id',
                                      transition.metadata.get('reaction_id', ''))
                
                # Check reaction_code if it starts with R
                if not kegg_reaction_id and hasattr(transition, 'reaction_code') and transition.reaction_code:
                    if transition.reaction_code.startswith('R') or transition.reaction_code.startswith('rn:R'):
                        kegg_reaction_id = transition.reaction_code
                
                # Check label (transition name) if it starts with R - KEGG models often use R codes as labels
                if not kegg_reaction_id and name and (name.startswith('R') or name.startswith('rn:R')):
                    kegg_reaction_id = name
                # Check label (transition name) if it starts with R - KEGG models often use R codes as labels
                if not kegg_reaction_id and name and (name.startswith('R') or name.startswith('rn:R')):
                    kegg_reaction_id = name
                
                # Clean KEGG format and fetch EC
                if kegg_reaction_id:
                    kegg_reaction_id = kegg_reaction_id.replace('rn:', '').strip()
                    
                    # If we have KEGG reaction ID, actively fetch from KEGG API
                    # This is the same pattern used in BRENDA enrichment controller
                    if kegg_reaction_id.startswith('R'):
                        # First check if EC already in metadata (from previous fetch)
                        if hasattr(transition, 'metadata') and transition.metadata:
                            ec_val = transition.metadata.get('ec_number',
                                    transition.metadata.get('ec_numbers', []))
                            if isinstance(ec_val, list) and ec_val:
                                ec_number = ec_val[0]
                            elif ec_val and ec_val != '-':
                                ec_number = str(ec_val)
                        
                        # If still not found, actively fetch from KEGG API
                        if ec_number == "-":
                            try:
                                ec_numbers = self.kegg_ec_fetcher.fetch_ec_numbers(kegg_reaction_id)
                                if ec_numbers and len(ec_numbers) > 0:
                                    ec_number = ec_numbers[0]
                                    # Store in metadata for future use
                                    if not hasattr(transition, 'metadata'):
                                        transition.metadata = {}
                                    if not transition.metadata:
                                        transition.metadata = {}
                                    transition.metadata['ec_number'] = ec_number
                            except Exception as e:
                                pass  # Silently fail - EC number will remain "-"
            
            # Priority 3: Fallback to metadata ec_number directly
            if ec_number == "-" and hasattr(transition, 'metadata') and transition.metadata:
                ec_val = transition.metadata.get('ec_number',
                         transition.metadata.get('ec_numbers', []))
                if isinstance(ec_val, list) and ec_val:
                    ec_number = ec_val[0]
                elif ec_val and ec_val != '-':
                    ec_number = str(ec_val)
            
            # Extract individual kinetic parameters
            vmax = 0.0
            vmax_source = "unknown"
            km = 0.0
            km_source = "unknown"
            kcat = 0.0
            kcat_source = "unknown"
            ki = 0.0
            ki_source = "unknown"
            
            if hasattr(transition, 'metadata') and transition.metadata:
                # Check direct metadata (BRENDA/SABIO-RK enrichment)
                if 'vmax' in transition.metadata:
                    vmax = float(transition.metadata['vmax'])
                    vmax_source = transition.metadata.get('vmax_source',
                                 transition.metadata.get('data_source', 'unknown'))
                
                if 'km' in transition.metadata:
                    km = float(transition.metadata['km'])
                    km_source = transition.metadata.get('km_source', 
                               transition.metadata.get('data_source', 'unknown'))
                
                if 'kcat' in transition.metadata:
                    kcat = float(transition.metadata['kcat'])
                    kcat_source = transition.metadata.get('kcat_source',
                                 transition.metadata.get('data_source', 'unknown'))
                
                if 'ki' in transition.metadata:
                    ki = float(transition.metadata['ki'])
                    ki_source = transition.metadata.get('ki_source',
                               transition.metadata.get('data_source', 'unknown'))
                
                # Check kinetic_parameters dict (SBML/KEGG import)
                params = transition.metadata.get('kinetic_parameters', {})
                if params and isinstance(params, dict):
                    if vmax == 0.0:
                        vmax_val = params.get('Vmax', params.get('vmax', params.get('V_max', 0.0)))
                        if vmax_val:
                            vmax = float(vmax_val)
                            vmax_source = transition.metadata.get('data_source', 'kegg_import')
                    
                    if km == 0.0:
                        km_val = params.get('Km', params.get('km', params.get('KM', 0.0)))
                        if km_val:
                            km = float(km_val)
                            km_source = transition.metadata.get('data_source', 'kegg_import')
                    
                    if kcat == 0.0:
                        kcat_val = params.get('Kcat', params.get('kcat', params.get('k_cat', 0.0)))
                        if kcat_val:
                            kcat = float(kcat_val)
                            kcat_source = transition.metadata.get('data_source', 'kegg_import')
                    
                    if ki == 0.0:
                        ki_val = params.get('Ki', params.get('ki', params.get('KI', 0.0)))
                        if ki_val:
                            ki = float(ki_val)
                            ki_source = transition.metadata.get('data_source', 'kegg_import')
                
                # Check estimated_parameters dict (KEGG heuristic estimator)
                estimated_params = transition.metadata.get('estimated_parameters', {})
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
            
            # Rate Function - Extract as-is from transition properties
            rate_function = "-"
            
            # Priority 1: Check transition.properties['rate_function']
            if hasattr(transition, 'properties') and transition.properties:
                if isinstance(transition.properties, dict):
                    rate_function = transition.properties.get('rate_function', '-')
            
            # Priority 2: Check transition.rate_function directly
            if rate_function == "-" and hasattr(transition, 'rate_function'):
                if transition.rate_function:
                    rate_function = transition.rate_function
            
            # Priority 3: Check metadata
            if rate_function == "-" and hasattr(transition, 'metadata') and transition.metadata:
                rate_function = transition.metadata.get('rate_function',
                               transition.metadata.get('kinetic_formula',
                               transition.metadata.get('kinetic_law', '-')))
            
            # Priority 4: For stochastic transitions, default to "mass_action"
            # Stochastic transitions inherently use mass action kinetics
            if rate_function == "-" and trans_type == 'stochastic':
                rate_function = "mass_action"
            
            # Reversible
            reversible = "Unknown"
            if hasattr(transition, 'metadata') and transition.metadata:
                rev_val = transition.metadata.get('reversible')
                if rev_val is not None:
                    reversible = "Yes" if rev_val else "No"
            
            # Add row to table (new column order)
            self.reactions_store.append([
                i,                # 0: index
                trans_id,         # 1: Petri Net ID
                name,             # 2: Biological Name
                trans_type,       # 3: Type
                ec_number,        # 4: EC Number
                vmax,             # 5: Vmax
                vmax_source,      # 6: Vmax source
                km,               # 7: Km
                km_source,        # 8: Km source
                kcat,             # 9: Kcat
                kcat_source,      # 10: Kcat source
                ki,               # 11: Ki
                ki_source,        # 12: Ki source
                rate_function,    # 13: Rate Function
                reversible        # 14: Reversible
            ])
    
    def _populate_locality_table(self):
        """Populate locality table with selected transition + locality places.
        
        Called when user selects transition in Analyses panel.
        Shows: Input Places → Transition → Output Places in unified table.
        """
        print(f"[POPULATE_LOCALITY] Starting...")
        print(f"[POPULATE_LOCALITY]   selected_transition: {self.selected_transition}")
        print(f"[POPULATE_LOCALITY]   selected_locality: {self.selected_locality}")
        
        self.locality_store.clear()
        
        if not self.selected_transition or not self.selected_locality:
            # Hide expander when no selection
            print(f"[POPULATE_LOCALITY] No transition or locality, hiding expander")
            self.locality_expander.set_visible(False)
            return
        
        # Show expander
        print(f"[POPULATE_LOCALITY] Showing expander")
        self.locality_expander.set_visible(True)
        
        transition = self.selected_transition
        locality = self.selected_locality
        
        print(f"[POPULATE_LOCALITY] Transition: {transition.name if hasattr(transition, 'name') else transition.id}")
        print(f"[POPULATE_LOCALITY] Input places: {len(locality.input_places)}")
        print(f"[POPULATE_LOCALITY] Output places: {len(locality.output_places)}")
        
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
        print(f"[MODELS_CATEGORY] set_selected_locality() called")
        print(f"[MODELS_CATEGORY]   transition: {transition.name if hasattr(transition, 'name') else transition.id}")
        print(f"[MODELS_CATEGORY]   locality: {locality}")
        print(f"[MODELS_CATEGORY]   locality.is_valid: {locality.is_valid if locality else 'None'}")
        
        self.selected_transition = transition
        self.selected_locality = locality
        
        print(f"[MODELS_CATEGORY] Calling _populate_locality_table()")
        self._populate_locality_table()
        print(f"[MODELS_CATEGORY] _populate_locality_table() completed")
