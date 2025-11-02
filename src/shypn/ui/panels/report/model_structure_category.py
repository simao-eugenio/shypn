#!/usr/bin/env python3
"""Models category for Report Panel.

Displays comprehensive scientific information about the current model:
- Model metadata (name, dates, file path, description)
- Petri net structure (places, transitions, arcs)
- Import provenance (KEGG/SBML source information)
- Detailed species and reactions lists with metadata
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from datetime import datetime

from .base_category import BaseReportCategory


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
        
        # Species/Places Table
        self.species_expander = Gtk.Expander(label="Show Species/Places Table (sortable)")
        self.species_expander.set_expanded(False)
        scrolled_species, self.species_treeview, self.species_store = self._create_species_table()
        self.species_expander.add(scrolled_species)
        box.pack_start(self.species_expander, False, False, 0)
        
        # Reactions/Transitions Table
        self.reactions_expander = Gtk.Expander(label="Show Reactions/Transitions Table (sortable)")
        self.reactions_expander.set_expanded(False)
        scrolled_reactions, self.reactions_treeview, self.reactions_store = self._create_reactions_table()
        self.reactions_expander.add(scrolled_reactions)
        box.pack_start(self.reactions_expander, False, False, 0)
        
        # Initial populate
        self.refresh()
        
        return box
    
    def _create_summary_grid(self):
        """No longer needed - summary is in frame."""
        pass
    
    def _create_species_table(self):
        """Create TreeView for species/places with sortable columns.
        
        Returns:
            tuple: (ScrolledWindow, TreeView, ListStore)
        """
        # Create ListStore with column types
        # Columns: index (int), id (str), name (str), extended_name (str), 
        #          db_id (str), db_id_source (str), tokens (float), 
        #          formula (str), formula_source (str), mass (float), mass_source (str), type (str)
        store = Gtk.ListStore(int, str, str, str, str, str, float, str, str, float, str, str)
        
        # Create TreeView
        treeview = Gtk.TreeView(model=store)
        treeview.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
        treeview.set_enable_search(True)
        treeview.set_search_column(2)  # Search by biological name
        
        # Add columns with renderers (colored for source tracking)
        self._add_column(treeview, "#", 0, width=50, sortable=False)
        self._add_column(treeview, "Petri Net ID", 1, sortable=True, width=100)
        self._add_column(treeview, "Biological Name", 2, sortable=True, width=150)
        self._add_column(treeview, "Extended Name", 3, sortable=True, width=200)
        self._add_colored_column(treeview, "Database ID", 4, 5, sortable=True, width=120)
        self._add_column(treeview, "Initial Tokens", 6, sortable=True, numeric=True, width=100)
        self._add_colored_column(treeview, "Formula", 7, 8, sortable=True, width=100)
        self._add_colored_column(treeview, "Mass (g/mol)", 9, 10, sortable=True, numeric=True, width=100)
        self._add_column(treeview, "Type", 11, sortable=True, width=90)
        
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(300)
        scrolled.add(treeview)
        
        return scrolled, treeview, store
    
    def _create_reactions_table(self):
        """Create TreeView for reactions/transitions with sortable columns.
        
        Returns:
            tuple: (ScrolledWindow, TreeView, ListStore)
        """
        # Create ListStore with column types
        # Columns: index (int), id (str), name (str), type (str), 
        #          kegg_reaction (str), ec_number (str), rate_law (str),
        #          parameters (str), reversible (str)
        store = Gtk.ListStore(int, str, str, str, str, str, str, str, str)
        
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
        self._add_column(treeview, "Reaction ID", 4, sortable=True, width=140)
        self._add_column(treeview, "EC Number", 5, sortable=True, width=100)
        self._add_column(treeview, "Rate Law", 6, sortable=True, width=150)
        self._add_column(treeview, "Parameters", 7, sortable=False, width=200)
        self._add_column(treeview, "Reversible", 8, sortable=True, width=90)
        
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(300)
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
    
    def _color_cell_by_source(self, column, renderer, model, iter, user_data):
        """Color cell based on data source.
        
        Color scheme:
        - Green (#2d5016): Raw import data (KEGG/SBML)
        - Blue (#1e3a8a): BRENDA-enriched data
        - Orange (#c2410c): User-edited values
        - Gray (#6b7280): Missing/unknown data
        """
        data_column_id, source_column_id = user_data
        value = model.get_value(iter, data_column_id)
        source = model.get_value(iter, source_column_id)
        
        # Determine color based on source
        if not value or value == "-" or value == 0.0:
            # Missing data - gray
            renderer.set_property('foreground', '#6b7280')
        elif source in ('kegg_import', 'sbml_import', 'biopax_import'):
            # Raw import - green
            renderer.set_property('foreground', '#2d5016')
        elif source == 'brenda_enriched':
            # BRENDA enriched - blue
            renderer.set_property('foreground', '#1e3a8a')
        elif source == 'user_edited':
            # User edited - orange
            renderer.set_property('foreground', '#c2410c')
        else:
            # Unknown - default black
            renderer.set_property('foreground', '#000000')
    
    def refresh(self):
        """Refresh models data with comprehensive scientific information."""
        print(f"[MODELS_CATEGORY] refresh() called, model_canvas={self.model_canvas}")
        
        # ModelCanvasManager IS the model - it has places, transitions, arcs directly
        if not self.model_canvas:
            print(f"[MODELS_CATEGORY] No model_canvas, clearing tables")
            self.overview_label.set_text("No model loaded")
            self.structure_label.set_text("No data")
            self.provenance_label.set_text("No import data")
            self.provenance_frame.set_visible(False)
            self.species_store.clear()
            self.reactions_store.clear()
            return
        
        print(f"[MODELS_CATEGORY] model_canvas has {len(self.model_canvas.places)} places, {len(self.model_canvas.transitions)} transitions")
        
        # The model_canvas IS the model (ModelCanvasManager with places/transitions/arcs)
        model = self.model_canvas
        
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
        
        Args:
            model: DocumentModel instance
        """
        print(f"[MODELS_CATEGORY] _populate_species_table() called")
        self.species_store.clear()
        
        if not hasattr(model, 'places') or not model.places:
            print(f"[MODELS_CATEGORY] No places to populate")
            return
        
        print(f"[MODELS_CATEGORY] Populating {len(model.places)} places")
        
        for i, place in enumerate(model.places, 1):
            if not place:
                continue
            
            # Extract data
            place_id = place.id if hasattr(place, 'id') else f"P{i}"
            name = place.label if hasattr(place, 'label') and place.label else place_id
            
            # Database ID (KEGG, ChEBI, or other)
            db_id = "-"
            db_id_source = "unknown"
            if hasattr(place, 'metadata') and place.metadata:
                # Try different database IDs in order of preference
                db_id = place.metadata.get('kegg_id',
                        place.metadata.get('chebi_id',
                        place.metadata.get('compound_id', 
                        place.metadata.get('sbml_species_id', '-'))))
                # Clean up ID format
                if db_id and db_id != '-':
                    db_id = db_id.replace('cpd:', '')  # Clean KEGG format
                    # Determine source
                    db_id_source = place.metadata.get('db_id_source',
                                   place.metadata.get('data_source', 'kegg_import'))
            
            # Extended Name - infer from database ID if possible
            extended_name = "-"
            if hasattr(place, 'metadata') and place.metadata:
                # First try metadata (explicit extended_name field)
                extended_name = place.metadata.get('extended_name', '-')
            
            # If not in metadata, try to infer from KEGG compound ID
            if extended_name == "-" and db_id and db_id != "-":
                if db_id.startswith('C') and len(db_id) == 6:
                    extended_name = self._infer_compound_name(db_id)
                else:
                    # If we have a compound_name or full_name in metadata, use it
                    if hasattr(place, 'metadata') and place.metadata:
                        extended_name = place.metadata.get('compound_name',
                                       place.metadata.get('full_name', '-'))
            
            # Initial tokens
            tokens = 0.0
            if hasattr(place, 'initial_marking'):
                tokens = float(place.initial_marking)
            elif hasattr(place, 'tokens'):
                tokens = float(place.tokens)
            
            # Formula
            formula = "-"
            formula_source = "unknown"
            if hasattr(place, 'metadata') and place.metadata:
                formula = place.metadata.get('formula', '-')
                if formula != '-':
                    formula_source = place.metadata.get('formula_source',
                                    place.metadata.get('data_source', 'kegg_import'))
            
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
            
            # Type
            type_val = "unknown"
            if hasattr(place, 'metadata') and place.metadata:
                type_val = place.metadata.get('type', 'unknown')
            
            # Add row to table with source tracking
            self.species_store.append([
                i,                # 0: index
                place_id,         # 1: Petri Net ID
                name,             # 2: Biological Name
                extended_name,    # 3: Extended Name
                db_id,            # 4: Database ID (KEGG/ChEBI/etc)
                db_id_source,     # 5: Database ID source
                tokens,           # 6: Initial Tokens
                formula,          # 7: Formula
                formula_source,   # 8: Formula source
                mass,             # 9: Mass
                mass_source,      # 10: Mass source
                type_val          # 11: Type
            ])
    
    def _infer_compound_name(self, compound_id):
        """Infer compound name from KEGG compound ID.
        
        Args:
            compound_id: KEGG compound ID (e.g., "C00033")
            
        Returns:
            Compound name or "-" if not found
        """
        # Check cache first
        if not hasattr(self, '_compound_name_cache'):
            self._compound_name_cache = {}
        
        if compound_id in self._compound_name_cache:
            return self._compound_name_cache[compound_id]
        
        # Common compounds hardcoded (to avoid API calls for every common metabolite)
        common_compounds = {
            'C00001': 'H2O (Water)',
            'C00002': 'ATP (Adenosine triphosphate)',
            'C00003': 'NAD+ (Nicotinamide adenine dinucleotide)',
            'C00004': 'NADH (Reduced nicotinamide adenine dinucleotide)',
            'C00005': 'NADPH (Reduced nicotinamide adenine dinucleotide phosphate)',
            'C00006': 'NADP+ (Nicotinamide adenine dinucleotide phosphate)',
            'C00008': 'ADP (Adenosine diphosphate)',
            'C00009': 'Orthophosphate',
            'C00010': 'CoA (Coenzyme A)',
            'C00011': 'CO2 (Carbon dioxide)',
            'C00013': 'Diphosphate',
            'C00014': 'Ammonia',
            'C00020': 'AMP (Adenosine monophosphate)',
            'C00025': 'L-Glutamate',
            'C00033': 'Acetate',
            'C00035': 'GDP (Guanosine diphosphate)',
            'C00044': 'GTP (Guanosine triphosphate)',
            'C00063': 'CTP (Cytidine triphosphate)',
            'C00080': 'H+ (Hydrogen ion)',
            'C00081': 'ITP (Inosine triphosphate)',
            'C00082': 'L-Tyrosine',
            'C00086': 'Urea',
            'C00103': 'D-Glucose 1-phosphate',
            'C00122': 'Fumarate',
            'C00149': 'L-Malate',
            'C00158': 'Citrate',
            'C00183': 'L-Valine',
        }
        
        if compound_id in common_compounds:
            result = common_compounds[compound_id]
            self._compound_name_cache[compound_id] = result
            return result
        
        # For uncommon compounds, return the ID (avoids API calls during display)
        # Could be enhanced with async API fetching in the future
        self._compound_name_cache[compound_id] = f"Compound {compound_id}"
        return f"Compound {compound_id}"
    
    def _populate_reactions_table(self, model):
        """Populate reactions table with current model data.
        
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
            
            # Reaction ID (KEGG, SBML, or other)
            reaction_id = "-"
            if hasattr(transition, 'metadata') and transition.metadata:
                # Try different reaction IDs in order of preference
                reaction_id = transition.metadata.get('kegg_reaction_id',
                             transition.metadata.get('sbml_reaction_id',
                             transition.metadata.get('kegg_reaction_name', 
                             transition.metadata.get('reaction_id', '-'))))
                # Clean up reaction ID format
                if reaction_id and reaction_id != '-':
                    reaction_id = reaction_id.replace('rn:', '')  # Clean KEGG format
            
            # EC Number
            ec_number = "-"
            if hasattr(transition, 'metadata') and transition.metadata:
                ec_val = transition.metadata.get('ec_number',
                         transition.metadata.get('ec_numbers', []))
                if isinstance(ec_val, list) and ec_val:
                    ec_number = ec_val[0]
                elif ec_val and ec_val != '-':
                    ec_number = str(ec_val)
            
            # Rate Law
            rate_law = "-"
            if hasattr(transition, 'metadata') and transition.metadata:
                rate_law = transition.metadata.get('kinetic_law',
                           transition.metadata.get('kinetics_rule', '-'))
            
            # Parameters (formatted string)
            parameters = "-"
            if hasattr(transition, 'metadata') and transition.metadata:
                params = transition.metadata.get('kinetics_parameters', {})
                if params and isinstance(params, dict):
                    params_list = []
                    for k, v in params.items():
                        if isinstance(v, float):
                            params_list.append(f"{k}={v:.4g}")
                        else:
                            params_list.append(f"{k}={v}")
                    parameters = ", ".join(params_list)
            
            # Reversible
            reversible = "Unknown"
            if hasattr(transition, 'metadata') and transition.metadata:
                rev_val = transition.metadata.get('reversible')
                if rev_val is not None:
                    reversible = "Yes" if rev_val else "No"
            
            # Add row to table
            self.reactions_store.append([
                i,               # index
                trans_id,        # Petri Net ID
                name,            # Biological Name
                trans_type,      # Type
                reaction_id,     # Reaction ID (KEGG/SBML/etc)
                ec_number,       # EC Number
                rate_law,        # Rate Law
                parameters,      # Parameters
                reversible       # Reversible
            ])
    
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
        
        Returns:
            str: Formatted table as text
        """
        if not self.species_store or len(self.species_store) == 0:
            return "No species data"
        
        lines = [
            f"Total Species/Places: {len(self.species_store)}",
            "",
            "{:<5} {:<12} {:<20} {:<25} {:<12} {:<12} {:<10} {:<12}".format(
                "#", "Petri ID", "Name", "Extended Name", "DB ID", 
                "Tokens", "Formula", "Mass"
            ),
            "-" * 125
        ]
        
        for row in self.species_store:
            # Skip source columns (5, 8, 10) in export
            lines.append(
                "{:<5} {:<12} {:<20} {:<25} {:<12} {:<12.4g} {:<10} {:<12.2f}".format(
                    row[0],   # index
                    row[1][:11],   # Petri Net ID
                    row[2][:19],   # Biological Name
                    row[3][:24],   # Extended Name
                    row[4][:11],   # Database ID
                    row[6],   # Initial Tokens (skip source at 5)
                    row[7][:9],    # Formula (skip source at 8)
                    row[9] if row[9] > 0 else 0  # Mass (skip source at 10)
                )
            )
        
        return "\n".join(lines)
    
    def _export_reactions_table(self):
        """Export reactions table as formatted text.
        
        Returns:
            str: Formatted table as text
        """
        if not self.reactions_store or len(self.reactions_store) == 0:
            return "No reactions data"
        
        lines = [
            f"Total Reactions/Transitions: {len(self.reactions_store)}",
            "",
            "{:<5} {:<15} {:<25} {:<12} {:<18} {:<12} {:<18} {:<30} {:<10}".format(
                "#", "Petri Net ID", "Biological Name", "Type", 
                "Reaction ID", "EC Number", "Rate Law", "Parameters", "Reversible"
            ),
            "-" * 163
        ]
        
        for row in self.reactions_store:
            lines.append(
                "{:<5} {:<15} {:<25} {:<12} {:<18} {:<12} {:<18} {:<30} {:<10}".format(
                    row[0],  # index
                    row[1][:14],  # Petri Net ID
                    row[2][:24],  # Biological Name
                    row[3][:11],  # Type
                    row[4][:17],  # Reaction ID (KEGG/SBML/etc)
                    row[5][:11],  # EC Number
                    row[6][:17],  # Rate Law
                    row[7][:29],  # Parameters
                    row[8][:9]    # Reversible
                )
            )
        
        return "\n".join(lines)
