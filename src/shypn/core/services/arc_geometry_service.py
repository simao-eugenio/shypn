"""Arc geometry service for parallel arc detection and offset calculation.

This module provides:
- Standalone functions (module-level) for pure parallel-arc calculations.
- ``AbstractArcGeometryService`` (ABC) — typed public contract.
- ``ArcGeometryService`` (concrete) — full implementation including arc-mutation
  helpers that require access to the manager's arcs list and callbacks.

Parallel arcs occur when:
- Same direction: Multiple arcs from A → B
- Opposite direction: Arcs in both directions (A → B and B → A)

These arcs need visual offsets to avoid overlapping and maintain clarity.
"""
from __future__ import annotations

import math
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional, Tuple

logger = logging.getLogger(__name__)


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
            pass
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


# =============================================================================
# OOP LAYER — AbstractArcGeometryService + ArcGeometryService
# =============================================================================

class AbstractArcGeometryService(ABC):
    """Abstract contract for arc geometry operations.

    Defines the interface for detecting parallel arcs, computing visual
    offsets, converting straight arcs to curved arcs, and maintaining
    arc-manager cross-references.
    """

    # ------------------------------------------------------------------ #
    # Query operations (read-only)                                         #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def detect_parallel_arcs(self, arc: Any) -> List[Any]:
        """Return arcs parallel to *arc* (same or reversed endpoints)."""
        ...

    @abstractmethod
    def calculate_arc_offset(self, arc: Any, parallels: List[Any]) -> float:
        """Return perpendicular pixel offset for *arc* given its parallels."""
        ...

    @abstractmethod
    def validate_arc_references(self, arc: Any) -> bool:
        """Return True if arc has valid, positioned source and target."""
        ...

    # ------------------------------------------------------------------ #
    # Mutation operations (modify arcs list)                               #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def auto_convert_parallel_arcs_to_curved(self, new_arc: Any) -> None:
        """Convert *new_arc* and its parallels to curved arcs when needed."""
        ...

    @abstractmethod
    def replace_arc(self, old_arc: Any, new_arc: Any) -> None:
        """Replace *old_arc* in the arcs list with *new_arc*."""
        ...

    @abstractmethod
    def ensure_arc_references(self) -> None:
        """Repair missing ``_manager`` / ``on_changed`` refs on all arcs."""
        ...


class ArcGeometryService(AbstractArcGeometryService):
    """Concrete arc geometry service.

    Encapsulates the 19 arc-geometry methods previously inline in
    ``ModelCanvasManager``.  Requires a reference to the manager so it can
    access ``manager.arcs`` and invoke ``manager.mark_modified()`` /
    ``manager.mark_dirty()`` / ``manager._on_object_changed``.

    Args:
        manager: The ``ModelCanvasManager`` instance that owns this service.
    """

    def __init__(self, manager: Any) -> None:
        self._manager = manager

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    @property
    def _arcs(self) -> List[Any]:
        return self._manager.arcs  # type: ignore[no-any-return]

    # ------------------------------------------------------------------ #
    # Query operations                                                     #
    # ------------------------------------------------------------------ #

    def detect_parallel_arcs(self, arc: Any) -> List[Any]:
        """Find arcs parallel to *arc* (same endpoints or reversed).

        Args:
            arc: Arc to check for parallels.

        Returns:
            List of parallel arcs, excluding *arc* itself.
        """
        parallels: List[Any] = []
        for other in self._arcs:
            if other is arc:
                continue
            if other.source == arc.source and other.target == arc.target:
                parallels.append(other)
            elif other.source == arc.target and other.target == arc.source:
                parallels.append(other)
        return parallels

    def validate_arc_references(self, arc: Any) -> bool:
        """Return True if arc has valid, positioned source and target."""
        if not hasattr(arc, "source") or arc.source is None:
            return False
        if not hasattr(arc, "target") or arc.target is None:
            return False
        if not hasattr(arc.source, "x") or not hasattr(arc.source, "y"):
            return False
        if not hasattr(arc.target, "x") or not hasattr(arc.target, "y"):
            return False
        return True

    # ------------------------------------------------------------------ #
    # Static math helpers                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _compute_direction_vector(arc: Any) -> Tuple[float, float, float]:
        """Return ``(dx, dy, length)`` for *arc*'s endpoint vector."""
        dx: float = arc.target.x - arc.source.x
        dy: float = arc.target.y - arc.source.y
        length: float = math.sqrt(dx * dx + dy * dy)
        return dx, dy, length

    @staticmethod
    def _normalize_vector(dx: float, dy: float, length: float) -> Tuple[float, float]:
        """Return unit vector from ``(dx, dy)`` with given *length*."""
        return dx / length, dy / length

    @staticmethod
    def _compute_perpendicular_vector(dx: float, dy: float) -> Tuple[float, float]:
        """Return 90° rotation of normalised vector ``(dx, dy)``."""
        return -dy, dx

    @staticmethod
    def _compute_offset_pair(
        arc1: Any,
        arc2: Any,
        perp_x: float,
        perp_y: float,
        offset_distance: float,
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Return ``(offset1, offset2)`` with mirrored perpendicular offsets.

        The arc with the lower ID gets the positive offset so the result is
        deterministic regardless of insertion order.
        """
        if arc1.id < arc2.id:
            offset1: Tuple[float, float] = (perp_x * offset_distance, perp_y * offset_distance)
            offset2: Tuple[float, float] = (-perp_x * offset_distance, -perp_y * offset_distance)
        else:
            offset1 = (-perp_x * offset_distance, -perp_y * offset_distance)
            offset2 = (perp_x * offset_distance, perp_y * offset_distance)
        return offset1, offset2

    @staticmethod
    def _separate_parallel_arcs(
        arc: Any, parallels: List[Any]
    ) -> Tuple[List[Any], List[Any]]:
        """Split *parallels* into same-direction and opposite-direction lists."""
        same: List[Any] = []
        opposite: List[Any] = []
        for other in parallels:
            if other.source == arc.source and other.target == arc.target:
                same.append(other)
            elif other.source == arc.target and other.target == arc.source:
                opposite.append(other)
        return same, opposite

    @staticmethod
    def _calculate_opposite_direction_offset(arc: Any, opposite_arc: Any) -> float:
        """Return ±50 px offset for an opposite-direction pair (mirror symmetry)."""
        return 50.0 if arc.id < opposite_arc.id else -50.0

    @staticmethod
    def _calculate_same_direction_offset(arc: Any, all_arcs: List[Any]) -> float:
        """Distribute same-direction arcs evenly around centre (0).

        Pattern:
            2 arcs  →  ±15 px
            3 arcs  →  +20, 0, −20 px
            4 arcs  →  +30, +10, −10, −30 px
        """
        total = len(all_arcs)
        if total <= 1:
            return 0.0
        all_arcs_sorted = sorted(all_arcs, key=lambda a: a.id)
        index = all_arcs_sorted.index(arc)
        if total == 2:
            return 15.0 if index == 0 else -15.0
        spacing = 10.0
        centre = (total - 1) / 2.0
        return (index - centre) * spacing

    # ------------------------------------------------------------------ #
    # Offset calculation                                                   #
    # ------------------------------------------------------------------ #

    def _calculate_perpendicular_offset(
        self, arc1: Any, arc2: Any, offset_distance: float = 50.0
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Return perpendicular offset pair for an opposite-direction arc pair."""
        dx, dy, length = self._compute_direction_vector(arc1)
        if length <= 1:
            return (0.0, 0.0), (0.0, 0.0)
        dx, dy = self._normalize_vector(dx, dy, length)
        perp_x, perp_y = self._compute_perpendicular_vector(dx, dy)
        return self._compute_offset_pair(arc1, arc2, perp_x, perp_y, offset_distance)

    def calculate_arc_offset(self, arc: Any, parallels: List[Any]) -> float:
        """Return pixel offset for *arc* to avoid overlapping its parallels.

        Returns:
            Positive → curve counter-clockwise, negative → clockwise, 0 → straight.
        """
        if not parallels:
            return 0.0
        same, opposite = self._separate_parallel_arcs(arc, parallels)
        if len(opposite) == 1 and len(same) == 0:
            return self._calculate_opposite_direction_offset(arc, opposite[0])
        all_arcs = [arc] + parallels
        return self._calculate_same_direction_offset(arc, all_arcs)

    # ------------------------------------------------------------------ #
    # Mutation helpers                                                     #
    # ------------------------------------------------------------------ #

    def _find_opposite_direction_arc(
        self, arc: Any, parallels: List[Any]
    ) -> Optional[Any]:
        """Return the first arc in *parallels* that runs opposite to *arc*."""
        for p in parallels:
            if p.source == arc.target and p.target == arc.source:
                return p
        return None

    def _replace_arc_in_list(self, old_arc: Any, new_arc: Any) -> None:
        """Swap *old_arc* for *new_arc* in the arcs list and wire callbacks."""
        try:
            index = self._arcs.index(old_arc)
            self._arcs[index] = new_arc
            new_arc._manager = self._manager
            new_arc.on_changed = self._manager._on_object_changed
        except ValueError:
            pass  # Already replaced or not found

    def _convert_loop_arc(self, arc: Any) -> bool:
        """Convert a loop arc (source == target) to a curved arc.

        Returns:
            True if converted, False if already curved.
        """
        from shypn.netobjs import Arc, CurvedArc, CurvedInhibitorArc  # type: ignore[import]
        from shypn.utils.arc_transform import make_curved  # type: ignore[import]

        if isinstance(arc, Arc) and not isinstance(arc, (CurvedArc, CurvedInhibitorArc)):
            curved = make_curved(arc)
            curved.control_offset_x = 60.0
            curved.control_offset_y = -60.0
            self._replace_arc_in_list(arc, curved)
            return True
        return False

    def _convert_opposite_direction_pair(
        self, new_arc: Any, opposite_arc: Any
    ) -> None:
        """Curve both arcs in an opposite-direction pair with perpendicular offsets."""
        from shypn.netobjs import Arc, CurvedArc, CurvedInhibitorArc, InhibitorArc  # type: ignore[import]
        from shypn.utils.arc_transform import make_curved  # type: ignore[import]

        (offset1, offset2) = self._calculate_perpendicular_offset(new_arc, opposite_arc)

        if isinstance(new_arc, Arc) and not isinstance(new_arc, (CurvedArc, CurvedInhibitorArc)):
            curved_new = make_curved(new_arc)
            curved_new.control_offset_x = offset1[0]
            curved_new.control_offset_y = offset1[1]
            self._replace_arc_in_list(new_arc, curved_new)

        if isinstance(opposite_arc, (Arc, InhibitorArc)) and not isinstance(
            opposite_arc, (CurvedArc, CurvedInhibitorArc)
        ):
            curved_opp = make_curved(opposite_arc)
            curved_opp.control_offset_x = offset2[0]
            curved_opp.control_offset_y = offset2[1]
            self._replace_arc_in_list(opposite_arc, curved_opp)

    def _convert_same_direction_parallels(
        self, new_arc: Any, parallels: List[Any]
    ) -> None:
        """Curve all same-direction parallels (and *new_arc* itself)."""
        from shypn.netobjs import Arc, CurvedArc, CurvedInhibitorArc, InhibitorArc  # type: ignore[import]
        from shypn.utils.arc_transform import make_curved  # type: ignore[import]

        for p in parallels:
            if isinstance(p, (Arc, InhibitorArc)) and not isinstance(
                p, (CurvedArc, CurvedInhibitorArc)
            ):
                self._replace_arc_in_list(p, make_curved(p))

        if isinstance(new_arc, Arc) and not isinstance(
            new_arc, (CurvedArc, CurvedInhibitorArc)
        ):
            self._replace_arc_in_list(new_arc, make_curved(new_arc))

    # ------------------------------------------------------------------ #
    # Public mutation methods (AbstractArcGeometryService contract)        #
    # ------------------------------------------------------------------ #

    def auto_convert_parallel_arcs_to_curved(self, new_arc: Any) -> None:
        """Convert *new_arc* and any parallel arcs to curved arcs.

        Handles three cases:
          1. Loop arc (source == target) → fixed offset curve.
          2. Opposite-direction pair → perpendicular mirror curves.
          3. Same-direction parallels → evenly distributed curves.
        """
        if not self.validate_arc_references(new_arc):
            return

        is_loop = new_arc.source is new_arc.target
        parallels = self.detect_parallel_arcs(new_arc)

        if is_loop:
            self._convert_loop_arc(new_arc)
            self._manager.mark_dirty()
            return

        if parallels:
            opposite = self._find_opposite_direction_arc(new_arc, parallels)
            if opposite:
                self._convert_opposite_direction_pair(new_arc, opposite)
            else:
                self._convert_same_direction_parallels(new_arc, parallels)
            self._manager.mark_dirty()

    def replace_arc(self, old_arc: Any, new_arc: Any) -> None:
        """Replace *old_arc* with *new_arc* and mark the document as modified.

        Used for arc-type transformations (straight ↔ curved, normal ↔ inhibitor).
        """
        try:
            index = self._arcs.index(old_arc)
            self._arcs[index] = new_arc
            new_arc._manager = self._manager
            new_arc.on_changed = self._manager._on_object_changed
            self._manager.mark_modified()
            self._manager.mark_dirty()
        except ValueError:
            pass  # Arc already removed

    def ensure_arc_references(self) -> None:
        """Repair missing ``_manager`` / ``on_changed`` references on all arcs."""
        for arc in self._arcs:
            if not getattr(arc, "_manager", None):
                arc._manager = self._manager
            if not getattr(arc, "on_changed", None):
                arc.on_changed = self._manager._on_object_changed
