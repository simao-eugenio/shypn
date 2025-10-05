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
    
    def __init__(self, place_panel=None, transition_panel=None, model=None, diagnostics_panel=None):
        """Initialize the context menu handler.
        
        Args:
            place_panel: PlaceRatePanel instance (optional, can be set later)
            transition_panel: TransitionRatePanel instance (optional, can be set later)
            model: ModelCanvasManager instance for locality detection (optional)
            diagnostics_panel: DiagnosticsPanel instance (optional, can be set later)
        """
        self.place_panel = place_panel
        self.transition_panel = transition_panel
        self.diagnostics_panel = diagnostics_panel
        self.model = model
        self.locality_detector = None
        
        # Initialize locality detector if model is available
        if model:
            from shypn.diagnostic import LocalityDetector
            self.locality_detector = LocalityDetector(model)
            print(f"[ContextMenuHandler] __init__ - Locality detector created with model")
        else:
            print(f"[ContextMenuHandler] __init__ - No model provided, locality detector is None")
    
    def set_panels(self, place_panel, transition_panel):
        """Set or update the analysis panels.
        
        Args:
            place_panel: PlaceRatePanel instance
            transition_panel: TransitionRatePanel instance
        """
        self.place_panel = place_panel
        self.transition_panel = transition_panel
        print("[ContextMenuHandler] Analysis panels set")
    
    def set_model(self, model):
        """Set or update the model for locality detection.
        
        Args:
            model: ModelCanvasManager instance
        """
        self.model = model
        if model:
            from shypn.diagnostic import LocalityDetector
            self.locality_detector = LocalityDetector(model)
            print("[ContextMenuHandler] Model and locality detector set")
    
    def add_analysis_menu_items(self, menu, obj):
        """Add analysis-related menu items to an object's context menu.
        
        This method adds a separator and "Add to Analysis" menu item
        to the provided GTK menu. The menu item is only added if the
        appropriate panel is available (place_panel for places,
        transition_panel for transitions).
        
        For transitions with valid localities, adds a submenu with:
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
            print(f"[ContextMenuHandler] Transition detected with locality_detector - calling _add_transition_locality_submenu")
            self._add_transition_locality_submenu(menu, obj, panel)
        else:
            # Simple menu item for places or transitions without locality support
            if isinstance(obj, Transition):
                print(f"[ContextMenuHandler] Transition detected but locality_detector={self.locality_detector} - using simple menu")
            
            menu_item = Gtk.MenuItem(label=f"Add to {obj_type_name}")
            
            def on_add_to_analysis(widget):
                """Callback when menu item is clicked."""
                self._on_add_to_analysis_clicked(obj, panel)
            
            menu_item.connect("activate", on_add_to_analysis)
            menu_item.show()
            menu.append(menu_item)
            
            print(f"[ContextMenuHandler] Added analysis menu item for {obj.name}")
    
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
        print(f"[ContextMenuHandler] Creating menu for transition {transition.name}")
        
        # Detect locality
        locality = self.locality_detector.get_locality_for_transition(transition)
        print(f"[ContextMenuHandler] Locality detected - valid: {locality.is_valid}, places: {locality.place_count}")
        
        if not locality.is_valid:
            # No valid locality, add simple menu item
            menu_item = Gtk.MenuItem(label=f"Add to Transition Analysis")
            menu_item.connect("activate", 
                            lambda w: self._on_add_to_analysis_clicked(transition, panel))
            menu_item.show()
            menu.append(menu_item)
            print(f"[ContextMenuHandler] Transition {transition.name} has no valid locality - simple menu item added")
            return
        
        # Create menu item that automatically adds transition + locality
        locality_count = locality.place_count
        menu_item = Gtk.MenuItem(label=f"Add to Transition Analysis")
        menu_item.connect("activate",
                         lambda w: self._add_transition_with_locality(transition, locality, panel))
        menu_item.show()
        menu.append(menu_item)
        
        print(f"[ContextMenuHandler] Menu item created for {transition.name} - will auto-add locality with {locality_count} places")
    
    def _add_transition_only(self, transition, panel):
        """Add transition without locality to analysis.
        
        Args:
            transition: Transition object
            panel: TransitionRatePanel instance
        """
        panel.add_object(transition)
        print(f"[ContextMenuHandler] Added {transition.name} (transition only) to analysis")
    
    def _add_transition_with_locality(self, transition, locality, panel):
        """Add transition with all locality places to analysis.
        
        Args:
            transition: Transition object
            locality: Locality object with input/output places
            panel: TransitionRatePanel instance
        """
        print(f"[ContextMenuHandler] _add_transition_with_locality called for {transition.name}")
        print(f"[ContextMenuHandler]   Locality valid: {locality.is_valid}")
        print(f"[ContextMenuHandler]   Input places: {len(locality.input_places)}")
        print(f"[ContextMenuHandler]   Output places: {len(locality.output_places)}")
        print(f"[ContextMenuHandler]   Panel type: {type(panel).__name__}")
        print(f"[ContextMenuHandler]   Has add_locality_places: {hasattr(panel, 'add_locality_places')}")
        
        # Add transition
        panel.add_object(transition)
        print(f"[ContextMenuHandler] Transition {transition.name} added to panel")
        
        # Add locality places if panel supports it
        if hasattr(panel, 'add_locality_places'):
            panel.add_locality_places(transition, locality)
            print(f"[ContextMenuHandler] Successfully added {transition.name} with locality "
                  f"({len(locality.input_places)} inputs, {len(locality.output_places)} outputs)")
        else:
            print(f"[ContextMenuHandler] Warning: Panel does not support add_locality_places()")
    
    def _on_add_to_analysis_clicked(self, obj, panel):
        """Handle "Add to Analysis" menu item click.
        
        Args:
            obj: Place or Transition object to add
            panel: PlaceRatePanel or TransitionRatePanel to add object to
        """
        from shypn.netobjs import Place, Transition
        
        # Add object to the appropriate panel
        panel.add_object(obj)
        
        # If it's a transition, also update the diagnostics panel
        if isinstance(obj, Transition) and self.diagnostics_panel:
            self.diagnostics_panel.set_transition(obj)
            print(f"[ContextMenuHandler] Updated diagnostics panel with transition {obj.name}")
        
        obj_type = "place" if isinstance(obj, Place) else "transition"
        print(f"[ContextMenuHandler] Added {obj_type} {obj.name} to analysis from context menu")
