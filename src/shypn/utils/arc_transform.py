#!/usr/bin/env python3
"""Arc Transformation Utilities.

This module provides utilities for transforming arcs between different types:
- Straight ↔ Curved
- Normal ↔ Inhibitor

Transformations preserve all arc properties (weight, color, width, etc.)
and maintain the arc's identity (ID, name) in the model.
"""
from shypn.netobjs import Arc, InhibitorArc, CurvedArc, CurvedInhibitorArc


def transform_arc(arc, make_curved=None, make_inhibitor=None):
    """Transform an arc to a different type while preserving its properties.
    
    This function creates a new arc instance of the target type with the
    same properties as the original arc. The original arc should be replaced
    in the model's arc list.
    
    Args:
        arc: Original arc instance to transform
        make_curved: True=make curved, False=make straight, None=keep current
        make_inhibitor: True=make inhibitor, False=make normal, None=keep current
        
    Returns:
        New arc instance of the target type with same properties
        
    Raises:
        ValueError: If trying to create inhibitor arc with invalid direction
        
    Examples:
        >>> # Convert straight arc to curved
        >>> new_arc = transform_arc(my_arc, make_curved=True)
        
        >>> # Convert normal arc to inhibitor
        >>> new_arc = transform_arc(my_arc, make_inhibitor=True)
        
        >>> # Convert straight inhibitor to curved inhibitor
        >>> new_arc = transform_arc(my_arc, make_curved=True, make_inhibitor=True)
        
        >>> # Convert curved arc to straight (keeping inhibitor status)
        >>> new_arc = transform_arc(my_curved_arc, make_curved=False)
    """
    from shypn.netobjs.place import Place
    from shypn.netobjs.transition import Transition
    
    # Determine current state
    is_curved = isinstance(arc, (CurvedArc, CurvedInhibitorArc))
    is_inhibitor = isinstance(arc, (InhibitorArc, CurvedInhibitorArc))
    
    # Apply transformations (if specified)
    if make_curved is not None:
        is_curved = make_curved
    if make_inhibitor is not None:
        is_inhibitor = make_inhibitor
    
    # Validate inhibitor arc direction (Place → Transition only)
    if is_inhibitor:
        if isinstance(arc.source, Transition) and isinstance(arc.target, Place):
            raise ValueError(
                "Cannot convert to inhibitor arc: Transition → Place is forbidden. "
                "Inhibitor arcs must connect Place → Transition only."
            )
    
    # Select appropriate target class
    if is_curved and is_inhibitor:
        target_class = CurvedInhibitorArc
    elif is_curved:
        target_class = CurvedArc
    elif is_inhibitor:
        target_class = InhibitorArc
    else:
        target_class = Arc
    
    # If already the correct type, return the same instance
    if type(arc) == target_class:
        return arc
    
    # Create new arc of target type
    new_arc = target_class(
        source=arc.source,
        target=arc.target,
        id=arc.id,
        name=arc.name,
        weight=arc.weight
    )
    
    # Copy all properties
    new_arc.color = arc.color
    new_arc.width = arc.width
    new_arc.threshold = arc.threshold
    new_arc.control_points = arc.control_points
    
    # Copy optional properties if they exist
    if hasattr(arc, 'label'):
        new_arc.label = arc.label
    if hasattr(arc, 'description'):
        new_arc.description = arc.description
    
    # Copy internal references
    if hasattr(arc, '_manager'):
        new_arc._manager = arc._manager
    if hasattr(arc, 'on_changed'):
        new_arc.on_changed = arc.on_changed
    
    return new_arc


def make_straight(arc):
    """Convert curved arc to straight arc.
    
    Args:
        arc: Arc instance to convert
        
    Returns:
        Arc or InhibitorArc: Straight version of the arc
    """
    return transform_arc(arc, make_curved=False)


def make_curved(arc):
    """Convert straight arc to curved arc.
    
    Args:
        arc: Arc instance to convert
        
    Returns:
        CurvedArc or CurvedInhibitorArc: Curved version of the arc
    """
    return transform_arc(arc, make_curved=True)


def convert_to_inhibitor(arc):
    """Convert normal arc to inhibitor arc.
    
    Args:
        arc: Arc instance to convert
        
    Returns:
        InhibitorArc or CurvedInhibitorArc: Inhibitor version of the arc
    """
    return transform_arc(arc, make_inhibitor=True)


def convert_to_normal(arc):
    """Convert inhibitor arc to normal arc.
    
    Args:
        arc: Arc instance to convert
        
    Returns:
        Arc or CurvedArc: Normal version of the arc
    """
    return transform_arc(arc, make_inhibitor=False)


def is_straight(arc):
    """Check if arc is straight (not curved).
    
    Args:
        arc: Arc instance to check
        
    Returns:
        bool: True if arc is straight (Arc or InhibitorArc)
    """
    return not isinstance(arc, (CurvedArc, CurvedInhibitorArc))


def is_curved(arc):
    """Check if arc is curved.
    
    Args:
        arc: Arc instance to check
        
    Returns:
        bool: True if arc is curved (CurvedArc or CurvedInhibitorArc)
    """
    return isinstance(arc, (CurvedArc, CurvedInhibitorArc))


def is_inhibitor(arc):
    """Check if arc is an inhibitor arc.
    
    Args:
        arc: Arc instance to check
        
    Returns:
        bool: True if arc is inhibitor (InhibitorArc or CurvedInhibitorArc)
    """
    return isinstance(arc, (InhibitorArc, CurvedInhibitorArc))


def is_normal(arc):
    """Check if arc is a normal arc (not inhibitor).
    
    Args:
        arc: Arc instance to check
        
    Returns:
        bool: True if arc is normal (Arc or CurvedArc)
    """
    return not isinstance(arc, (InhibitorArc, CurvedInhibitorArc))


def get_arc_type_name(arc):
    """Get human-readable name of arc type.
    
    Args:
        arc: Arc instance
        
    Returns:
        str: Arc type name ("Arc", "Inhibitor Arc", "Curved Arc", "Curved Inhibitor Arc")
    """
    if isinstance(arc, CurvedInhibitorArc):
        return "Curved Inhibitor Arc"
    elif isinstance(arc, CurvedArc):
        return "Curved Arc"
    elif isinstance(arc, InhibitorArc):
        return "Inhibitor Arc"
    else:
        return "Arc"
