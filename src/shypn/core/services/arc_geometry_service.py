"""Arc geometry service for parallel arc detection and offset calculation.

This module provides stateless functions for managing arc geometry,
particularly for handling parallel arcs (multiple arcs between same nodes).

Parallel arcs occur when:
- Same direction: Multiple arcs from A → B
- Opposite direction: Arcs in both directions (A → B and B → A)

These arcs need visual offsets to avoid overlapping and maintain clarity.
"""

from typing import List, Any


def detect_parallel_arcs(arc: Any, all_arcs: List[Any]) -> List[Any]:
    """Find arcs parallel to the given arc (same source/target or reversed).
    
    Parallel arcs are arcs that connect the same two nodes, either in the
    same direction or opposite direction. These need visual offset to
    avoid overlapping.
    
    Args:
        arc: Arc to check for parallels
        all_arcs: List of all arcs to search through
        
    Returns:
        List of parallel arcs (excluding the given arc)
    
    Example:
        # Find parallel arcs
        parallels = detect_parallel_arcs(my_arc, manager.arcs)
        if parallels:
            offset = calculate_arc_offset(my_arc, parallels)
    """
    parallels = []
    
    for other in all_arcs:
        if other == arc:
            continue
        
        # Same direction: same source and target
        if (other.source == arc.source and other.target == arc.target):
            parallels.append(other)
        
        # Opposite direction: reversed source and target
        elif (other.source == arc.target and other.target == arc.source):
            parallels.append(other)
    
    return parallels


def calculate_arc_offset(arc: Any, parallels: List[Any]) -> float:
    """Calculate offset for arc to avoid overlapping parallels.
    
    For parallel arcs between same nodes, we offset them perpendicular
    to the line connecting the nodes. The offset is calculated to
    distribute arcs evenly on both sides of the center line.
    
    For opposite direction arcs (A→B, B→A), they curve in opposite
    directions to create mirror symmetry.
    
    Algorithm:
    - 2 arcs (opposite): ±50px (mirror symmetry)
    - 2 arcs (same): ±15px
    - 3+ arcs: Distribute evenly with 10px spacing around center
    
    Args:
        arc: Arc to calculate offset for
        parallels: List of parallel arcs (from detect_parallel_arcs)
        
    Returns:
        Offset distance in pixels:
        - Positive = counterclockwise curve
        - Negative = clockwise curve
        - Zero = no offset (straight line)
    
    Example:
        parallels = detect_parallel_arcs(arc, all_arcs)
        offset = calculate_arc_offset(arc, parallels)
        # Use offset in arc rendering to curve the arc
    """
    if not parallels:
        return 0.0  # No offset needed for single arc
    
    # Separate same-direction and opposite-direction arcs
    same_direction = []
    opposite_direction = []
    
    for other in parallels:
        if other.source == arc.source and other.target == arc.target:
            same_direction.append(other)
        elif other.source == arc.target and other.target == arc.source:
            opposite_direction.append(other)
    
    # Special case: Two arcs in opposite directions (most common: A→B, B→A)
    if len(opposite_direction) == 1 and len(same_direction) == 0:
        # Two arcs in opposite directions - mirror each other
        # Use a deterministic rule: arc with lower ID gets positive offset
        other = opposite_direction[0]
        if arc.id < other.id:
            return 50.0  # Curve counterclockwise
        else:
            return -50.0  # Curve clockwise (mirror)
    
    # General case: Same-direction arcs or mixed cases
    # Use stable ordering by ID to ensure consistent offsets
    all_arcs = [arc] + parallels
    all_arcs.sort(key=lambda a: a.id)  # Stable ordering by ID
    
    index = all_arcs.index(arc)
    total = len(all_arcs)
    
    # Calculate offset based on number of parallel arcs
    # Pattern: distribute evenly around center (0)
    if total == 1:
        return 0.0
    elif total == 2:
        # Simple case: ±15 pixels
        return 15.0 if index == 0 else -15.0
    else:
        # General case: distribute evenly with 10px spacing
        # For 3 arcs: +20, 0, -20
        # For 4 arcs: +30, +10, -10, -30
        spacing = 10.0
        center = (total - 1) / 2.0
        return (index - center) * spacing


def count_parallel_arcs(arc: Any, all_arcs: List[Any]) -> int:
    """Count how many arcs are parallel to the given arc.
    
    Convenience function that returns the count instead of the list.
    
    Args:
        arc: Arc to check
        all_arcs: List of all arcs
        
    Returns:
        Number of parallel arcs (excluding the given arc)
    
    Example:
        if count_parallel_arcs(arc, all_arcs) > 0:
    """
    return len(detect_parallel_arcs(arc, all_arcs))


def has_parallel_arcs(arc: Any, all_arcs: List[Any]) -> bool:
    """Check if arc has any parallel arcs.
    
    Convenience function for boolean check.
    
    Args:
        arc: Arc to check
        all_arcs: List of all arcs
        
    Returns:
        True if arc has parallels, False otherwise
    
    Example:
        if has_parallel_arcs(arc, all_arcs):
            offset = calculate_arc_offset(arc, detect_parallel_arcs(arc, all_arcs))
    """
    return len(detect_parallel_arcs(arc, all_arcs)) > 0


def get_arc_offset_for_rendering(arc: Any, all_arcs: List[Any]) -> float:
    """Get arc offset for rendering (combines detection and calculation).
    
    Convenience function that performs both parallel detection and
    offset calculation in one call.
    
    Args:
        arc: Arc to get offset for
        all_arcs: List of all arcs
        
    Returns:
        Offset distance in pixels for rendering
    
    Example:
        # In rendering code:
        offset = get_arc_offset_for_rendering(arc, all_arcs)
        # Apply offset to arc curve
    """
    parallels = detect_parallel_arcs(arc, all_arcs)
    return calculate_arc_offset(arc, parallels)


def separate_parallel_arcs_by_direction(arc: Any, parallels: List[Any]) -> tuple:
    """Separate parallel arcs into same-direction and opposite-direction groups.
    
    Args:
        arc: Reference arc
        parallels: List of parallel arcs
        
    Returns:
        Tuple of (same_direction_arcs, opposite_direction_arcs)
    
    Example:
        same, opposite = separate_parallel_arcs_by_direction(arc, parallels)
    """
    same_direction = []
    opposite_direction = []
    
    for other in parallels:
        if other.source == arc.source and other.target == arc.target:
            same_direction.append(other)
        elif other.source == arc.target and other.target == arc.source:
            opposite_direction.append(other)
    
    return same_direction, opposite_direction
