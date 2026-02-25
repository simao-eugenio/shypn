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

# ---------------------------------------------------------------------------
# Dispatch tables — single source of truth for arc-type→name and flag→class
# ---------------------------------------------------------------------------

# Ordered: most-specific subclasses first so isinstance short-circuits correctly.
_ARC_TYPE_NAMES: tuple = (
    (CurvedInhibitorArc, "Curved Inhibitor Arc"),
    (CurvedArc,          "Curved Arc"),
    (CurvedSignalFlowArc, "Curved Signal Flow Arc"),
    (SignalFlowArc,       "Signal Flow Arc"),
    (TestArc,             "Test Arc"),
    (InhibitorArc,        "Inhibitor Arc"),
)

# Keys: (is_curved, is_inhibitor, is_signal)
_ARC_CLASS_MAP: dict = {
    (True,  True,  False): CurvedInhibitorArc,
    (True,  False, True):  CurvedSignalFlowArc,
    (True,  False, False): CurvedArc,
    (False, True,  False): InhibitorArc,
    (False, False, True):  SignalFlowArc,
    (False, False, False): Arc,
}


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
        if not (isinstance(arc.source, Place) and isinstance(arc.target, Transition)):
            source_type = type(arc.source).__name__
            target_type = type(arc.target).__name__
            raise ValueError(
                f"Cannot convert to inhibitor arc: {source_type} → {target_type} is forbidden. "
                "Inhibitor arcs must connect Place → Transition only."
            )
    
    # Select appropriate target class via dispatch table
    target_class = _ARC_CLASS_MAP.get((is_curved, is_inhibitor, is_signal), Arc)
    
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
    
    # Apply ColorSchemaManager to ensure each arc type gets its proper color
    # This includes: InhibitorArc (black), TestArc (blue), SignalFlowArc (gray), Normal (black)
    ColorSchemaManager.reset_arc_color(new_arc)
    
    # Copy other properties (NOT color - already set by ColorSchemaManager)
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
    
    # FLUSH cached type information that might interfere with successive transformations
    # Clear any internal type caches on both old and new arc
    if hasattr(arc, '_cached_arc_type'):
        delattr(arc, '_cached_arc_type')
    if hasattr(new_arc, '_cached_arc_type'):
        delattr(new_arc, '_cached_arc_type')
    
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
    
    # FLUSH cached type information
    if hasattr(arc, '_cached_arc_type'):
        delattr(arc, '_cached_arc_type')
    if hasattr(new_arc, '_cached_arc_type'):
        delattr(new_arc, '_cached_arc_type')
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
    """Check if arc is a signal flow arc (information transfer + token flow).

    Args:
        arc: Arc instance to check

    Returns:
        bool: True if arc is a signal flow arc (SignalFlowArc or CurvedSignalFlowArc)
    """
    return isinstance(arc, (SignalFlowArc, CurvedSignalFlowArc))


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
    if not (isinstance(arc.source, Place) and isinstance(arc.target, Transition)):
        source_type = type(arc.source).__name__
        target_type = type(arc.target).__name__
        raise ValueError(
            f"Cannot convert to test arc: {source_type} → {target_type} is forbidden. "
            "Test arcs must connect Place → Transition only (catalyst semantics)."
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
    
    # FLUSH cached type information
    if hasattr(arc, '_cached_arc_type'):
        delattr(arc, '_cached_arc_type')
    if hasattr(new_arc, '_cached_arc_type'):
        delattr(new_arc, '_cached_arc_type')
    
    return new_arc


def get_arc_type_name(arc):
    """Get human-readable name of arc type.
    
    Args:
        arc: Arc instance
        
    Returns:
        str: Arc type name
    """
    for cls, name in _ARC_TYPE_NAMES:
        if isinstance(arc, cls):
            return name
    return "Arc"


def convert_to_signal_flow(arc):
    """Convert arc to signal flow arc (dual-role: consumes/produces tokens AND
    informs the vertical decision hierarchy layers).

    Unlike test arcs (which are purely catalytic), signal flow arcs transfer
    mass AND propagate information upward through control hierarchies.
    The one structural restriction: every Place endpoint must be a signal place
    (is_signal_place=True).  A ValueError is raised if this condition is not met.

    Curvature is preserved: a curved source arc produces CurvedSignalFlowArc;
    a straight source arc produces SignalFlowArc.

    Args:
        arc: Arc instance to convert

    Returns:
        SignalFlowArc or CurvedSignalFlowArc: Signal flow version of the arc
    """
    # If already signal flow arc, return it
    if isinstance(arc, (SignalFlowArc, CurvedSignalFlowArc)):
        return arc

    # Determine target class based on current curvature
    arc_is_curved = isinstance(arc, (CurvedArc, CurvedInhibitorArc, CurvedSignalFlowArc))
    target_class = CurvedSignalFlowArc if arc_is_curved else SignalFlowArc

    # Create new arc of target type
    new_arc = target_class(
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
    
    # FLUSH cached type information
    if hasattr(arc, '_cached_arc_type'):
        delattr(arc, '_cached_arc_type')
    if hasattr(new_arc, '_cached_arc_type'):
        delattr(new_arc, '_cached_arc_type')
    
    return new_arc
