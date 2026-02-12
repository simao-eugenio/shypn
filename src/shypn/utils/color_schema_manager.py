#!/usr/bin/env python3
"""Color Schema Manager - Centralized color management for SHYpn.

Provides consistent color assignments based on object types and semantic roles.
Eliminates scattered is_signal_place checks and isinstance() conditionals.

Color Schema (Minimalist Black-and-Blue):
- Regular places: Black border (0.0, 0.0, 0.0)
- Signal places: Blue border (0.0, 0.4, 0.8) - Ψ in 13-tuple Bio-PN
- Regular arcs: Black (0.0, 0.0, 0.0)
- Test arcs: Blue (0.0, 0.0, 1.0) - Read-only catalytic
- SignalFlowArcs: Light gray (0.7, 0.7, 0.7) - Information with consumption
- Inhibitor arcs: Black (0.0, 0.0, 0.0)
- Transitions: Black border + black fill (0.0, 0.0, 0.0)
- Source/Sink transitions: Green (0.0, 0.8, 0.0)
- Compartment places: Violet border (0.5, 0.0, 0.5)
- Recording color: Orange (1.0, 0.5, 0.0)

Author: Simão Eugénio
Date: 2026-01-01
"""

from typing import Tuple, Optional


class ColorSchemaManager:
    """Centralized color management for Petri net objects.
    
    Provides methods to get appropriate colors based on object types
    and semantic roles, eliminating scattered type checks throughout codebase.
    """
    
    # ========================================================================
    # PLACE COLORS
    # ========================================================================
    PLACE_DEFAULT_BORDER = (0.0, 0.0, 0.0)  # Black - regular places
    PLACE_SIGNAL_BORDER = (0.0, 0.0, 1.0)   # Blue - signal places (Ψ)
    PLACE_COMPARTMENT_BORDER = (0.5, 0.0, 0.5)  # Violet - compartment places
    PLACE_REGULATORY_BORDER = (0.0, 0.0, 0.0)   # Black - regulatory places (genes)
    
    # ========================================================================
    # ARC COLORS
    # ========================================================================
    ARC_DEFAULT = (0.0, 0.0, 0.0)        # Black - regular arcs
    ARC_TEST = (0.0, 0.0, 1.0)           # Blue - test arcs (read-only)
    ARC_SIGNAL_FLOW = (0.7, 0.7, 0.7)    # Light gray - signal flow arcs
    ARC_INHIBITOR = (0.0, 0.0, 0.0)      # Black - inhibitor arcs
    
    # ========================================================================
    # TRANSITION COLORS
    # ========================================================================
    TRANSITION_DEFAULT_BORDER = (0.0, 0.0, 0.0)  # Black border
    TRANSITION_DEFAULT_FILL = (0.0, 0.0, 0.0)    # Black fill
    TRANSITION_SOURCE_SINK = (0.0, 0.8, 0.0)     # Green - source/sink transitions
    
    # ========================================================================
    # RECORDING/ANALYSIS COLORS
    # ========================================================================
    RECORDING_COLOR = (1.0, 0.5, 0.0)    # Orange - recorded objects
    
    @staticmethod
    def get_place_border_color(place) -> Tuple[float, float, float]:
        """Get appropriate border color for a place based on its type.
        
        Args:
            place: Place object
            
        Returns:
            RGB tuple (r, g, b) with values 0.0-1.0
        """
        # Signal places get blue border (hexagonal shape distinguishes them)
        if getattr(place, 'is_signal_place', False):
            return ColorSchemaManager.PLACE_SIGNAL_BORDER
        
        # Compartment places get violet border (non-default compartment)
        if getattr(place, 'is_compartment_place', False):
            return ColorSchemaManager.PLACE_COMPARTMENT_BORDER
        
        # Regulatory places (genes, constant resources) get black border
        if getattr(place, 'is_regulatory_place', False):
            return ColorSchemaManager.PLACE_REGULATORY_BORDER
        
        # Default: black border for regular places
        return ColorSchemaManager.PLACE_DEFAULT_BORDER
    
    @staticmethod
    def get_arc_color(arc) -> Tuple[float, float, float]:
        """Get appropriate color for an arc based on its type.
        
        Args:
            arc: Arc object (Arc, TestArc, SignalFlowArc, InhibitorArc)
            
        Returns:
            RGB tuple (r, g, b) with values 0.0-1.0
        """
        # Import here to avoid circular dependencies
        from shypn.netobjs.test_arc import TestArc
        from shypn.netobjs.signal_flow_arc import SignalFlowArc
        from shypn.netobjs.inhibitor_arc import InhibitorArc
        
        # Test arcs are blue (read-only catalytic)
        if isinstance(arc, TestArc):
            return ColorSchemaManager.ARC_TEST
        
        # Signal flow arcs are light gray (information with consumption)
        if isinstance(arc, SignalFlowArc):
            return ColorSchemaManager.ARC_SIGNAL_FLOW
        
        # Inhibitor arcs are black (threshold-based inhibition)
        if isinstance(arc, InhibitorArc):
            return ColorSchemaManager.ARC_INHIBITOR
        
        # Default: black for regular mass-transfer arcs
        return ColorSchemaManager.ARC_DEFAULT
    
    @staticmethod
    def get_transition_colors(transition) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """Get appropriate border and fill colors for a transition.
        
        Args:
            transition: Transition object
            
        Returns:
            Tuple of (border_color, fill_color) as RGB tuples
        """
        # Source/sink transitions are green (signal regeneration/clearance)
        if getattr(transition, 'is_source', False) or getattr(transition, 'is_sink', False):
            color = ColorSchemaManager.TRANSITION_SOURCE_SINK
            return (color, color)
        
        # Default: black border, black fill
        return (
            ColorSchemaManager.TRANSITION_DEFAULT_BORDER,
            ColorSchemaManager.TRANSITION_DEFAULT_FILL
        )
    
    @staticmethod
    def reset_place_color(place) -> None:
        """Reset place border color to its type-appropriate default.
        
        Args:
            place: Place object to reset
        """
        place.border_color = ColorSchemaManager.get_place_border_color(place)
    
    @staticmethod
    def reset_arc_color(arc) -> None:
        """Reset arc color to its type-appropriate default.
        
        Args:
            arc: Arc object to reset
        """
        arc.color = ColorSchemaManager.get_arc_color(arc)
    
    @staticmethod
    def reset_transition_colors(transition) -> None:
        """Reset transition border and fill colors to type-appropriate defaults.
        
        Args:
            transition: Transition object to reset
        """
        border_color, fill_color = ColorSchemaManager.get_transition_colors(transition)
        transition.border_color = border_color
        transition.fill_color = fill_color
    
    @staticmethod
    def is_semantic_place_color(place) -> bool:
        """Check if place has a semantic color that should be preserved.
        
        Semantic colors indicate special roles: signal, compartment, regulatory.
        
        Args:
            place: Place object
            
        Returns:
            True if place has semantic color, False if default black
        """
        return (getattr(place, 'is_signal_place', False) or
                getattr(place, 'is_compartment_place', False) or
                getattr(place, 'is_regulatory_place', False))
    
    @staticmethod
    def is_semantic_arc_color(arc) -> bool:
        """Check if arc has a semantic color that should be preserved.
        
        Semantic colors distinguish arc types: test (blue), signal flow (gray).
        
        Args:
            arc: Arc object
            
        Returns:
            True if arc has semantic color, False if default black
        """
        from shypn.netobjs.test_arc import TestArc
        from shypn.netobjs.signal_flow_arc import SignalFlowArc
        
        return isinstance(arc, (TestArc, SignalFlowArc))
    
    @staticmethod
    def is_semantic_transition_color(transition) -> bool:
        """Check if transition has a semantic color that should be preserved.
        
        Semantic colors indicate special roles: source/sink.
        
        Args:
            transition: Transition object
            
        Returns:
            True if transition has semantic color, False if default
        """
        return (getattr(transition, 'is_source', False) or
                getattr(transition, 'is_sink', False))
    
    @staticmethod
    def fix_model_colors(model_canvas_manager):
        """Fix colors in an already-loaded model to match the color schema.
        
        This applies the color schema to all objects in the model that have
        semantic types. Useful for fixing models that were loaded before the
        color enforcement was added.
        
        Args:
            model_canvas_manager: ModelCanvasManager with loaded document
            
        Returns:
            dict with counts of fixed objects: {'places': int, 'arcs': int, 'transitions': int}
        """
        fixed_counts = {'places': 0, 'arcs': 0, 'transitions': 0}
        
        # Fix place colors
        if hasattr(model_canvas_manager, 'places'):
            for place in model_canvas_manager.places:
                if ColorSchemaManager.is_semantic_place_color(place):
                    old_color = place.border_color
                    ColorSchemaManager.reset_place_color(place)
                    if old_color != place.border_color:
                        fixed_counts['places'] += 1
        
        # Fix arc colors
        if hasattr(model_canvas_manager, 'arcs'):
            for arc in model_canvas_manager.arcs:
                if ColorSchemaManager.is_semantic_arc_color(arc):
                    old_color = arc.color
                    ColorSchemaManager.reset_arc_color(arc)
                    if old_color != arc.color:
                        fixed_counts['arcs'] += 1
        
        # Fix transition colors
        if hasattr(model_canvas_manager, 'transitions'):
            for transition in model_canvas_manager.transitions:
                if ColorSchemaManager.is_semantic_transition_color(transition):
                    old_border = transition.border_color
                    old_fill = transition.fill_color
                    ColorSchemaManager.reset_transition_colors(transition)
                    if old_border != transition.border_color or old_fill != transition.fill_color:
                        fixed_counts['transitions'] += 1
        
        return fixed_counts


__all__ = ['ColorSchemaManager']
