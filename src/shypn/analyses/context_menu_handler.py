#!/usr/bin/env python3
"""Context Menu Handler - Add analysis menu items to canvas object context menus.

This module provides the ContextMenuHandler class for adding "Add to Analysis"
menu items to the context menus of places and transitions in the canvas.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class ContextMenuHandler:
    """Handles adding analysis-related menu items to canvas object context menus.
    
    This class provides methods to augment existing context menus with
    "Add to Analysis" options that allow users to right-click on places
    or transitions and directly add them to the rate analysis plots in
    the right panel.
    
    Attributes:
        place_panel: PlaceRatePanel instance for adding places
        transition_panel: TransitionRatePanel instance for adding transitions
    
    Example:
        # In model_canvas_loader
        handler = ContextMenuHandler(place_panel, transition_panel)
        
        # When building object context menu
        handler.add_analysis_menu_items(menu, obj)
    """
    
    def __init__(self, place_panel=None, transition_panel=None, model=None, diagnostics_panel=None, pathway_operations_panel=None, viability_panel=None, model_canvas_loader=None):
        """Initialize the context menu handler.
        
        Args:
            place_panel: PlaceRatePanel instance (optional, can be set later)
            transition_panel: TransitionRatePanel instance (optional, can be set later)
            model: ModelCanvasManager instance for locality detection (optional)
            diagnostics_panel: DiagnosticsPanel instance (optional, can be set later)
            pathway_operations_panel: PathwayOperationsPanel instance for BRENDA enrichment (optional)
            viability_panel: ViabilityPanel instance for model viability analysis (optional, DEPRECATED - use model_canvas_loader)
            model_canvas_loader: ModelCanvasLoader instance for accessing per-document viability panels (optional)
        """
        self.place_panel = place_panel
        self.transition_panel = transition_panel
        self.diagnostics_panel = diagnostics_panel
        self.pathway_operations_panel = pathway_operations_panel
        self.viability_panel = viability_panel  # DEPRECATED: kept for backward compatibility
        self.model_canvas_loader = model_canvas_loader  # For per-document viability panels
        self.model = model
        self.locality_detector = None
        
        # Initialize locality detector if model is available
        if model:
            from shypn.diagnostic import LocalityDetector
            self.locality_detector = LocalityDetector(model)
        else:
    
            pass
    def set_panels(self, place_panel, transition_panel):
        """Set or update the analysis panels.
        
        Args:
            place_panel: PlaceRatePanel instance
            transition_panel: TransitionRatePanel instance
        """
        self.place_panel = place_panel
        self.transition_panel = transition_panel
    
    def set_pathway_operations_panel(self, pathway_operations_panel):
        """Set or update the pathway operations panel for BRENDA enrichment.
        
        Args:
            pathway_operations_panel: PathwayOperationsPanel instance
        """
        self.pathway_operations_panel = pathway_operations_panel
    
    def set_viability_panel(self, viability_panel):
        """Set or update the viability panel for model viability analysis.
        
        DEPRECATED: Use set_model_canvas_loader() for per-document viability panels.
        
        Args:
            viability_panel: ViabilityPanel instance
        """
        self.viability_panel = viability_panel
    
    def set_model_canvas_loader(self, model_canvas_loader):
        """Set the model canvas loader for accessing per-document viability panels.
        
        Args:
            model_canvas_loader: ModelCanvasLoader instance
        """
        self.model_canvas_loader = model_canvas_loader
    
    def _get_current_viability_panel(self):
        """Get the viability panel for the current document.
        
        Returns per-document viability panel if available, otherwise returns
        the global viability panel (for backward compatibility).
        
        Returns:
            ViabilityPanel instance or None
        """
        # Try per-document panel first (new architecture)
        if self.model_canvas_loader:
            drawing_area = self.model_canvas_loader.get_current_document()
            if drawing_area and hasattr(self.model_canvas_loader, 'overlay_managers'):
                overlay_manager = self.model_canvas_loader.overlay_managers.get(drawing_area)
                if overlay_manager and hasattr(overlay_manager, 'viability_panel_loader'):
                    viability_loader = overlay_manager.viability_panel_loader
                    if viability_loader and hasattr(viability_loader, 'panel'):
                        panel = viability_loader.panel
                        return panel
        
        # Fallback to global panel (old architecture)
        return self.viability_panel
    
    def set_model(self, model):
        """Set or update the model for locality detection.
        
        Args:
            model: ModelCanvasManager instance
        """
        self.model = model
        if model:
            from shypn.diagnostic import LocalityDetector
            self.locality_detector = LocalityDetector(model)
    
    def add_analysis_menu_items(self, menu, obj):
        """Add analysis-related menu items to an object's context menu.
        
        This method adds a separator and "Add to Analysis" menu item
        to the provided GTK menu. The menu item is only added if the
        appropriate panel is available (place_panel for places,
        transition_panel for transitions).
        
        For transitions with valid localities, adds a submenu with:
            pass
        - "Transition Only" option
        - "With Locality (N places)" option
        
        Args:
            menu: Gtk.Menu instance to add items to
            obj: Place or Transition object
        """
        from shypn.netobjs import Place, Transition
        
        # Determine which panel to use
        panel = None
        obj_type_name = None
        
        if isinstance(obj, Place):
            panel = self.place_panel
            obj_type_name = "Place Analysis"
        elif isinstance(obj, Transition):
            panel = self.transition_panel
            obj_type_name = "Transition Analysis"
        else:
            # Not a place or transition, don't add menu item
            return
        
        # Only add if panel is available
        if panel is None:
            return
        
        # Add separator
        separator = Gtk.SeparatorMenuItem()
        separator.show()
        menu.append(separator)
        
        # For transitions with locality support, add submenu
        if isinstance(obj, Transition) and self.locality_detector:
            self._add_transition_locality_submenu(menu, obj, panel)
        else:
            # Simple menu item for places or transitions without locality support
            menu_item = Gtk.MenuItem(label=f"Add to {obj_type_name}")
            
            def on_add_to_analysis(widget):
                """Callback when menu item is clicked."""
                self._on_add_to_analysis_clicked(obj, panel)
            
            menu_item.connect("activate", on_add_to_analysis)
            menu_item.show()
            menu.append(menu_item)
        
        # Add BRENDA enrichment option for transitions
        if isinstance(obj, Transition) and self.pathway_operations_panel:
            self._add_brenda_enrichment_menu(menu, obj)
            self._add_sabio_rk_enrichment_menu(menu, obj)
        
        # Add "Add to Viability" option for places and transitions
        viability_panel = self._get_current_viability_panel()
        if viability_panel:
            self._add_viability_menu_item(menu, obj, viability_panel)
            
    
    def _add_viability_menu_item(self, menu, obj, viability_panel):
        """Add 'Add to Viability' menu item for model viability analysis.
        
        Args:
            menu: Gtk.Menu instance to add items to
            obj: Place or Transition object
            viability_panel: ViabilityPanel instance
        """
        from shypn.netobjs import Place, Transition
        
        # Add separator
        separator = Gtk.SeparatorMenuItem()
        separator.show()
        menu.append(separator)
        
        # Determine object type
        if isinstance(obj, Place):
            obj_label = f"Place: {obj.id}"
        elif isinstance(obj, Transition):
            obj_label = f"Transition: {obj.id}"
        else:
            return
        
        # Add menu item
        menu_item = Gtk.MenuItem(label="Add to Viability Analysis")
        
        def on_add_to_viability(widget):
            """Callback when 'Add to Viability' is clicked."""
            # Add the object to viability panel for focused analysis
            if hasattr(viability_panel, 'add_object_for_analysis'):
                viability_panel.add_object_for_analysis(obj)
        
        menu_item.connect("activate", on_add_to_viability)
        menu_item.show()
        menu.append(menu_item)
    
    def _add_transition_locality_submenu(self, menu, transition, panel):
        """Add menu item for transition - automatically includes locality if valid.
        
        Automatically adds transition with locality (if valid), matching the
        behavior of the search UI where finding a transition also adds its
        locality places.
        
        Args:
            menu: Gtk.Menu instance to add menu item to
            transition: Transition object
            panel: TransitionRatePanel instance
        """
        
        # Detect locality
        locality = self.locality_detector.get_locality_for_transition(transition)
        
        if not locality.is_valid:
            # No valid locality, add simple menu item
            menu_item = Gtk.MenuItem(label=f"Add to Transition Analysis")
            menu_item.connect("activate", 
                            lambda w: self._on_add_to_analysis_clicked(transition, panel))
            menu_item.show()
            menu.append(menu_item)
            return
        
        # Create menu item that automatically adds transition + locality
        locality_count = locality.place_count
        menu_item = Gtk.MenuItem(label=f"Add to Transition Analysis")
        menu_item.connect("activate",
                         lambda w: self._add_transition_with_locality(transition, locality, panel))
        menu_item.show()
        menu.append(menu_item)
        
    
    def _add_transition_only(self, transition, panel):
        """Add transition without locality to analysis.
        
        Args:
            transition: Transition object
            panel: TransitionRatePanel instance
        """
        panel.add_object(transition)
    
    def _add_transition_with_locality(self, transition, locality, panel):
        """Add transition with all locality places to analysis.
        
        Args:
            transition: Transition object
            locality: Locality object with input/output places
            panel: TransitionRatePanel instance
        """
        
        # Add transition (border color will be set automatically in panel.add_object)
        panel.add_object(transition)
        
        # Add locality places if panel supports it
        # (these places will also get their border colors set automatically)
        if hasattr(panel, 'add_locality_places'):
            panel.add_locality_places(transition, locality)
        
        # Request canvas redraw to show new border colors
        if self.model:
            self.model.mark_needs_redraw()
        else:
    
            pass
    
    def _add_brenda_enrichment_menu(self, menu, transition):
        """Add BRENDA enrichment menu item for transitions.
        
        Extracts enzyme/reaction information from the transition metadata
        and pre-fills the BRENDA query in the Pathway Operations panel.
        
        Args:
            menu: Gtk.Menu instance to add menu item to
            transition: Transition object
        """
        menu_item = Gtk.MenuItem(label="Enrich with BRENDA")
        menu_item.connect("activate", lambda w: self._on_enrich_with_brenda(transition))
        menu_item.show()
        menu.append(menu_item)
    
    def _on_enrich_with_brenda(self, transition):
        """Handle BRENDA enrichment request.
        
        Extracts transition data and pre-fills BRENDA query fields:
        - EC number from metadata
        - Reaction name from label or metadata
        - Enzyme name from metadata
        
        Args:
            transition: Transition object to enrich
        """
        # Extract data from transition
        ec_number = ""
        reaction_name = ""
        enzyme_name = ""
        
        # Check metadata for enzyme/reaction information
        if hasattr(transition, 'metadata') and transition.metadata:
            metadata = transition.metadata
            
            # Try to get EC number
            if 'ec_number' in metadata:
                ec_number = metadata['ec_number']
            elif 'ec_numbers' in metadata and metadata['ec_numbers']:
                # Take first EC number if list
                ec_list = metadata['ec_numbers']
                if isinstance(ec_list, list) and ec_list:
                    ec_number = ec_list[0]
                elif isinstance(ec_list, str):
                    ec_number = ec_list
            
            # Try to get enzyme name
            if 'enzyme_name' in metadata:
                enzyme_name = metadata['enzyme_name']
            elif 'enzyme' in metadata:
                enzyme_name = metadata['enzyme']
            
            # Try to get reaction name
            if 'reaction' in metadata:
                reaction_name = metadata['reaction']
            elif 'reaction_id' in metadata:
                reaction_name = metadata['reaction_id']
        
        # Use label as reaction name if not found in metadata
        if not reaction_name and transition.label:
            reaction_name = transition.label
        
        # Use name as fallback
        if not reaction_name:
            reaction_name = transition.name
        
        # Access BRENDA category in pathway operations panel
        if hasattr(self.pathway_operations_panel, 'brenda_category'):
            brenda_category = self.pathway_operations_panel.brenda_category
            
            # Pre-fill the query fields
            if hasattr(brenda_category, 'set_query_from_transition'):
                brenda_category.set_query_from_transition(
                    ec_number=ec_number,
                    reaction_name=reaction_name,
                    enzyme_name=enzyme_name,
                    transition_id=transition.id
                )
            
            # Keep transition highlighted on canvas to remind user which transition is being enriched
            transition.selected = True
            
            # Store reference to transition so BRENDA panel can clear selection later if needed
            brenda_category._enrichment_transition = transition
            
            # Trigger canvas redraw to show selection
            if hasattr(self, 'canvas_loader') and self.canvas_loader:
                # Find the drawing area for this manager
                for drawing_area, manager in self.canvas_loader.managers.items():
                    if transition in manager.transitions:
                        drawing_area.queue_draw()
                        break
            
            # Switch to Pathway Operations panel and expand BRENDA category
            # This makes the pre-filled query visible to the user
            if hasattr(self.pathway_operations_panel, 'switch_to_category'):
                self.pathway_operations_panel.switch_to_category('BRENDA')
    
    def _add_sabio_rk_enrichment_menu(self, menu, transition):
        """Add SABIO-RK enrichment menu item for transitions.
        
        Extracts enzyme/reaction information from the transition metadata
        and pre-fills the SABIO-RK query in the Pathway Operations panel.
        
        Args:
            menu: Gtk.Menu instance to add menu item to
            transition: Transition object
        """
        menu_item = Gtk.MenuItem(label="Enrich with SABIO-RK")
        menu_item.connect("activate", lambda w: self._on_enrich_with_sabio_rk(transition))
        menu_item.show()
        menu.append(menu_item)
    
    def _on_enrich_with_sabio_rk(self, transition):
        """Handle SABIO-RK enrichment request.
        
        Extracts transition data and pre-fills SABIO-RK query fields:
        - EC number from metadata
        - Reaction ID from metadata (KEGG reaction ID preferred over EC)
        - Organism from metadata if available
        
        Args:
            transition: Transition object to enrich
        """
        # Extract data from transition
        ec_number = ""
        reaction_id = ""
        organism = ""
        
        # Check metadata for enzyme/reaction information
        if hasattr(transition, 'metadata') and transition.metadata:
            metadata = transition.metadata
            
            # Try to get reaction ID (KEGG reaction ID preferred for SABIO-RK)
            if 'reaction_id' in metadata:
                reaction_id = metadata['reaction_id']
            elif 'kegg_reaction_id' in metadata:
                reaction_id = metadata['kegg_reaction_id']
            elif 'reaction' in metadata:
                reaction_id = metadata['reaction']
            
            # Try to get EC number as fallback
            if 'ec_number' in metadata:
                ec_number = metadata['ec_number']
            elif 'ec_numbers' in metadata and metadata['ec_numbers']:
                # Take first EC number if list
                ec_list = metadata['ec_numbers']
                if isinstance(ec_list, list) and ec_list:
                    ec_number = ec_list[0]
                elif isinstance(ec_list, str):
                    ec_number = ec_list
            
            # Try to get organism from metadata
            if 'organism' in metadata:
                organism = metadata['organism']
            elif 'species' in metadata:
                organism = metadata['species']
        
        # If EC number is empty but reaction_id looks like EC format, use it
        if not ec_number and reaction_id:
            # Check if reaction_id is EC format (e.g., "2.7.1.1")
            import re
            if re.match(r'^\d+\.\d+\.\d+\.\d+$', reaction_id):
                ec_number = reaction_id
                reaction_id = ""
        
        # Access SABIO-RK category in pathway operations panel
        if hasattr(self.pathway_operations_panel, 'sabio_rk_category'):
            sabio_rk_category = self.pathway_operations_panel.sabio_rk_category
            
            # Pre-fill the query fields
            if hasattr(sabio_rk_category, 'set_query_from_transition'):
                sabio_rk_category.set_query_from_transition(
                    ec_number=ec_number,
                    reaction_id=reaction_id,
                    organism=organism,
                    transition_id=transition.id
                )
            
            # Switch to Pathway Operations panel and expand SABIO-RK category
            # This makes the pre-filled query visible to the user
            if hasattr(self.pathway_operations_panel, 'switch_to_category'):
                self.pathway_operations_panel.switch_to_category('SABIO-RK')
    
    def _on_add_to_analysis_clicked(self, obj, panel):
        """Handle "Add to Analysis" menu item click.
        
        Args:
            obj: Place or Transition object to add
            panel: PlaceRatePanel or TransitionRatePanel to add object to
        """
        from shypn.netobjs import Place, Transition
        
        # Add object to the appropriate panel
        # (border color will be set automatically in panel.add_object)
        panel.add_object(obj)
        
        # Request canvas redraw to show new border color
        if self.model:
            self.model.mark_needs_redraw()
        
        # If it's a transition, also update the diagnostics panel
        if isinstance(obj, Transition) and self.diagnostics_panel:
            self.diagnostics_panel.set_transition(obj)
        
        obj_type = "place" if isinstance(obj, Place) else "transition"
