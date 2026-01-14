#!/usr/bin/env python3
"""Arc Transformation Utilities.

This module provides utilities for transforming arcs between different types:
- Straight ↔ Curved
- Normal ↔ Inhibitor ↔ Test ↔ SignalFlow

Transformations preserve all arc properties (weight, color, width, etc.)
and maintain the arc's identity (ID, name) in the model.
"""
from shypn.netobjs import Arc, InhibitorArc, CurvedArc, CurvedInhibitorArc
from shypn.netobjs.test_arc import TestArc
from shypn.netobjs.signal_flow_arc import SignalFlowArc
from shypn.netobjs.curved_signal_flow_arc import CurvedSignalFlowArc
from shypn.utils.color_schema_manager import ColorSchemaManager


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
    is_curved = isinstance(arc, (CurvedArc, CurvedInhibitorArc, CurvedSignalFlowArc))
    is_inhibitor = isinstance(arc, (InhibitorArc, CurvedInhibitorArc))
    is_signal = isinstance(arc, (SignalFlowArc, CurvedSignalFlowArc))
    
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
    # Priority: inhibitor > signal > normal (test arcs not handled here)
    if is_curved and is_inhibitor:
        target_class = CurvedInhibitorArc
    elif is_curved and is_signal:
        target_class = CurvedSignalFlowArc
    elif is_curved:
        target_class = CurvedArc
    elif is_inhibitor:
        target_class = InhibitorArc
    elif is_signal:
        target_class = SignalFlowArc
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
    # For semantic arc types (TestArc, SignalFlowArc), apply color schema
    # For normal arcs, preserve the original color
    if ColorSchemaManager.is_semantic_arc_color(new_arc):
        ColorSchemaManager.reset_arc_color(new_arc)
    else:
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
    """Convert arc to normal arc (non-inhibitor, non-test, non-signal).
    
    Args:
        arc: Arc instance to convert
        
    Returns:
        Arc or CurvedArc: Normal version of the arc
    """
    from shypn.netobjs.place import Place
    from shypn.netobjs.transition import Transition
    
    # Check if it's curved
    is_curved = isinstance(arc, (CurvedArc, CurvedInhibitorArc, CurvedSignalFlowArc))
    
    # Select target class (Arc or CurvedArc)
    target_class = CurvedArc if is_curved else Arc
    
    # If already the correct type, return it
    if type(arc) == target_class:
        return arc
    
    # Create new normal arc
    new_arc = target_class(
        source=arc.source,
        target=arc.target,
        id=arc.id,
        name=arc.name,
        weight=arc.weight
    )
    
    # Apply ColorSchemaManager for normal arc (black)
    ColorSchemaManager.reset_arc_color(new_arc)
    
    # Copy all properties (except color - now managed by ColorSchemaManager)
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


def is_straight(arc):
    """Check if arc is straight (not curved).
    
    Checks both the arc class type (CurvedArc) and the is_curved flag
    for regular Arc instances that have been transformed via the handle.
    
    Args:
        arc: Arc instance to check
        
    Returns:
        bool: True if arc is straight (not curved)
    """
    # Check if it's a CurvedArc class (legacy system)
    if isinstance(arc, (CurvedArc, CurvedInhibitorArc, CurvedSignalFlowArc)):
        return False
    
    # Check if regular Arc has is_curved flag set (new system)
    if hasattr(arc, 'is_curved') and arc.is_curved:
        return False
    
    return True


def is_curved(arc):
    """Check if arc is curved.
    
    Checks both the arc class type (CurvedArc) and the is_curved flag
    for regular Arc instances that have been transformed via the handle.
    
    Args:
        arc: Arc instance to check
        
    Returns:
        bool: True if arc is curved
    """
    # Check if it's a CurvedArc class (legacy system)
    if isinstance(arc, (CurvedArc, CurvedInhibitorArc, CurvedSignalFlowArc)):
        return True
    
    # Check if regular Arc has is_curved flag set (new system)
    if hasattr(arc, 'is_curved') and arc.is_curved:
        return True
    
    return False


def is_inhibitor(arc):
    """Check if arc is an inhibitor arc.
    
    Args:
        arc: Arc instance to check
        
    Returns:
        bool: True if arc is inhibitor (InhibitorArc or CurvedInhibitorArc)
    """
    return isinstance(arc, (InhibitorArc, CurvedInhibitorArc))


def is_test(arc):
    """Check if arc is a test arc (read arc).
    
    Args:
        arc: Arc instance to check
        
    Returns:
        bool: True if arc is test arc (TestArc)
    """
    return isinstance(arc, TestArc)


def is_normal(arc):
    """Check if arc is a normal arc (not inhibitor, test, or signal_flow).
    
    Args:
        arc: Arc instance to check
        
    Returns:
        bool: True if arc is normal (Arc or CurvedArc)
    """
    return not isinstance(arc, (InhibitorArc, CurvedInhibitorArc, TestArc, SignalFlowArc))


def is_signal_flow(arc):
    """Check if arc is a signal flow arc (information transfer).
    
    Args:
        arc: Arc instance to check
        
    Returns:
        bool: True if arc is signal flow arc (SignalFlowArc)
    """
    return isinstance(arc, SignalFlowArc)


def convert_to_test(arc):
    """Convert normal arc to test arc (read arc).
    
    Args:
        arc: Arc instance to convert
        
    Returns:
        TestArc: Test version of the arc
        
    Raises:
        ValueError: If arc direction is invalid (test arcs must be Place → Transition)
    """
    from shypn.netobjs.place import Place
    from shypn.netobjs.transition import Transition
    
    # Validate direction (Place → Transition only)
    if isinstance(arc.source, Transition) and isinstance(arc.target, Place):
        raise ValueError(
            "Cannot convert to test arc: Transition → Place is forbidden. "
            "Test arcs must connect Place → Transition only."
        )
    
    # If already test arc, return it
    if isinstance(arc, TestArc):
        return arc
    
    # Create new test arc
    new_arc = TestArc(
        source=arc.source,
        target=arc.target,
        id=arc.id,
        name=arc.name,
        weight=arc.weight
    )
    
    # Apply ColorSchemaManager semantic color for TestArc (blue)
    ColorSchemaManager.reset_arc_color(new_arc)
    
    # Copy all properties (except color - now managed by ColorSchemaManager)
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


def get_arc_type_name(arc):
    """Get human-readable name of arc type.
    
    Args:
        arc: Arc instance
        
    Returns:
        str: Arc type name
    """
    if isinstance(arc, SignalFlowArc):
        return "Signal Flow Arc"
    elif isinstance(arc, TestArc):
        return "Test Arc"
    elif isinstance(arc, CurvedInhibitorArc):
        return "Curved Inhibitor Arc"
    elif isinstance(arc, CurvedArc):
        return "Curved Arc"
    elif isinstance(arc, InhibitorArc):
        return "Inhibitor Arc"
    else:
        return "Arc"


def convert_to_signal_flow(arc):
    """Convert arc to signal flow arc (information transfer).
    
    Signal flow arcs must connect to at least one signal place (Ψ).
    They consume tokens (unlike test arcs) to model signal depletion
    in hierarchical control systems.
    
    Args:
        arc: Arc instance to convert
        
    Returns:
        SignalFlowArc: Signal flow version of the arc
        
    Raises:
        ValueError: If arc doesn't connect to a signal place
    """
    from shypn.netobjs.place import Place
    
    # If already signal flow arc, return it
    if isinstance(arc, SignalFlowArc):
        return arc
    
    # Validate that at least one endpoint is a signal place
    is_source_signal = (isinstance(arc.source, Place) and 
                       getattr(arc.source, 'is_signal_place', False))
    is_target_signal = (isinstance(arc.target, Place) and 
                       getattr(arc.target, 'is_signal_place', False))
    
    if not (is_source_signal or is_target_signal):
        raise ValueError(
            f"Cannot convert to signal flow arc: Neither endpoint is a signal place. "
            f"Source: {arc.source.name} (is_signal_place={is_source_signal}), "
            f"Target: {arc.target.name} (is_signal_place={is_target_signal}). "
            f"Mark a place as signal place first (is_signal_place=True)."
        )
    
    # Create new signal flow arc
    new_arc = SignalFlowArc(
        source=arc.source,
        target=arc.target,
        id=arc.id,
        name=arc.name,
        weight=arc.weight
    )
    
    # Apply ColorSchemaManager semantic color for SignalFlowArc (light gray)
    ColorSchemaManager.reset_arc_color(new_arc)
    
    # Copy all properties (except color - now managed by ColorSchemaManager)
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
