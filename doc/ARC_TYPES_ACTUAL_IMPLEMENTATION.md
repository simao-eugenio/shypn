# Arc Types - Actual Implementation Plan (Revised)

## Discovery: Existing Architecture

After examining the codebase, I found that **the arc system already has some foundation**:

### Existing Classes

1. **`Arc`** (`src/shypn/netobjs/arc.py`) - ✅ COMPLETE
   - Base class for all arcs
   - Two-line arrowhead rendering (15px, π/5 angle)
   - Weight labels, color support, glow effects
   - Properties: source, target, weight, color, width, threshold, control_points (unused)
   - Bipartite validation (Place↔Transition only)
   - Serialization support

2. **`InhibitorArc`** (`src/shypn/netobjs/inhibitor_arc.py`) - ✅ COMPLETE
   - Inherits from `Arc`
   - Overrides `_render_arrowhead()` to draw hollow circle marker
   - Marker: 8px radius, white fill + colored ring
   - Already exported in `__init__.py`

### What's Missing

3. **`CurvedArc`** - 🆕 NEED TO CREATE
   - Inherits from `Arc`
   - Adds bezier curve rendering
   - Keeps two-line arrowhead (from Arc)
   
4. **`CurvedInhibitorArc`** - 🆕 NEED TO CREATE
   - Multiple inheritance: `CurvedArc` + bezier logic
   - Inherits hollow circle marker from `InhibitorArc`
   - Combines curve path + inhibitor marker

## Revised Implementation Strategy

### Object-Oriented Design (Class Hierarchy)

Instead of adding an `arc_type` property to a single Arc class, we use **inheritance and composition**:

```
PetriNetObject (base)
    │
    └── Arc (base arc class)
         ├── InhibitorArc (hollow circle marker) ✅ EXISTS
         ├── CurvedArc (bezier curve) 🆕 CREATE
         └── CurvedInhibitorArc (curve + marker) 🆕 CREATE
```

### Benefits of This Approach

1. **Separation of Concerns**: Each class has a single responsibility
2. **Code Reuse**: Curved classes reuse Arc/InhibitorArc rendering logic
3. **Extensibility**: Easy to add new arc types (ReadArc, ResetArc, etc.)
4. **Type Safety**: `isinstance(arc, InhibitorArc)` clearly identifies inhibitors
5. **No Branching**: No `if arc_type == 'inhibitor'` checks scattered in code

### Implementation Plan

## Phase 1: Create CurvedArc Class

**File:** `src/shypn/netobjs/curved_arc.py`

```python
#!/usr/bin/env python3
"""CurvedArc - Arc with bezier curve path.

Inherits from Arc but renders with a smooth curve instead of straight line.
Useful for parallel opposite arcs to avoid visual overlap.
"""
import math
from typing import Tuple
from .arc import Arc


class CurvedArc(Arc):
    """Arc rendered with a bezier curve path.
    
    Uses quadratic bezier curve with automatic control point calculation:
    - Control point at midpoint perpendicular to straight line
    - Offset is 20% of line length (configurable)
    - Keeps two-line arrowhead from Arc base class
    
    Inherits all properties from Arc but overrides path rendering.
    """
    
    # Curve offset as percentage of line length
    CURVE_OFFSET_RATIO = 0.20  # 20% of line length
    
    def __init__(self, source, target, id: int, name: str, weight: int = 1):
        """Initialize a curved arc.
        
        Args:
            source: Source PetriNetObject
            target: Target PetriNetObject
            id: Unique integer identifier (immutable, system-assigned)
            name: Unique name in format "C1", "C2", etc. (immutable, system-assigned)
            weight: Arc weight (default: 1)
        """
        super().__init__(source, target, id, name, weight)
    
    def _calculate_curve_control_point(self) -> Tuple[float, float]:
        """Calculate bezier control point for curved arc.
        
        Creates a curve that bows perpendicular to the straight line
        connecting source and target. Used for opposite arcs.
        
        Returns:
            tuple: (x, y) control point coordinates, or None if degenerate
        """
        # Get source and target positions
        sx, sy = self.source.x, self.source.y
        tx, ty = self.target.x, self.target.y
        
        # Calculate midpoint
        mx = (sx + tx) / 2
        my = (sy + ty) / 2
        
        # Vector from source to target
        dx = tx - sx
        dy = ty - sy
        length = math.sqrt(dx*dx + dy*dy)
        
        if length < 1e-6:
            return None  # Degenerate case: same point
        
        # Unit perpendicular vector (rotated 90° counterclockwise)
        perp_x = -dy / length
        perp_y = dx / length
        
        # Control point offset: 20% of line length
        offset = length * self.CURVE_OFFSET_RATIO
        
        # Control point at midpoint + perpendicular offset
        cp_x = mx + perp_x * offset
        cp_y = my + perp_y * offset
        
        return (cp_x, cp_y)
    
    def render(self, cr, transform=None, zoom=1.0):
        """Render curved arc using bezier path.
        
        Overrides Arc.render() to draw a quadratic bezier curve
        instead of a straight line.
        
        Args:
            cr: Cairo context (with zoom transformation already applied)
            transform: Optional function (deprecated, for backward compatibility)
            zoom: Current zoom level for line width compensation
        """
        # Get source and target positions in world space
        src_world_x, src_world_y = self.source.x, self.source.y
        tgt_world_x, tgt_world_y = self.target.x, self.target.y
        
        # Calculate control point
        control_point = self._calculate_curve_control_point()
        
        if control_point is None:
            # Degenerate case: fall back to straight line
            super().render(cr, transform, zoom)
            return
        
        cp_x, cp_y = control_point
        
        # Calculate direction for boundary points
        # For curves, use tangent at endpoints
        dx_start = cp_x - src_world_x
        dy_start = cp_y - src_world_y
        length_start = math.sqrt(dx_start*dx_start + dy_start*dy_start)
        
        if length_start < 1e-6:
            super().render(cr, transform, zoom)
            return
        
        dx_start /= length_start
        dy_start /= length_start
        
        dx_end = tgt_world_x - cp_x
        dy_end = tgt_world_y - cp_y
        length_end = math.sqrt(dx_end*dx_end + dy_end*dy_end)
        
        if length_end < 1e-6:
            super().render(cr, transform, zoom)
            return
        
        dx_end /= length_end
        dy_end /= length_end
        
        # Get boundary points in world space
        start_world_x, start_world_y = self._get_boundary_point(
            self.source, src_world_x, src_world_y, dx_start, dy_start)
        end_world_x, end_world_y = self._get_boundary_point(
            self.target, tgt_world_x, tgt_world_y, dx_end, dy_end)
        
        # Add glow effect for colored arcs
        if self.color != self.DEFAULT_COLOR:
            cr.move_to(start_world_x, start_world_y)
            cr.curve_to(cp_x, cp_y, cp_x, cp_y, end_world_x, end_world_y)
            r, g, b = self.color
            cr.set_source_rgba(r, g, b, 0.3)  # Semi-transparent color
            cr.set_line_width((self.width + 2) / max(zoom, 1e-6))
            cr.stroke()
        
        # Draw curve in world coordinates
        cr.move_to(start_world_x, start_world_y)
        cr.curve_to(cp_x, cp_y, cp_x, cp_y, end_world_x, end_world_y)
        cr.set_source_rgb(*self.color)
        cr.set_line_width(self.width / max(zoom, 1e-6))
        cr.stroke()
        
        # Draw arrowhead at target (using tangent at end)
        self._render_arrowhead(cr, end_world_x, end_world_y, dx_end, dy_end, zoom)
        
        # Draw weight label if > 1
        if self.weight > 1:
            self._render_weight(cr, start_world_x, start_world_y, end_world_x, end_world_y, zoom)
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is near this curved arc.
        
        Uses bezier curve distance calculation instead of straight line.
        
        Args:
            x, y: Point coordinates (world space)
            
        Returns:
            bool: True if point is near the arc curve
        """
        # Calculate control point
        control_point = self._calculate_curve_control_point()
        
        if control_point is None:
            # Degenerate case: use straight line check
            return super().contains_point(x, y)
        
        cp_x, cp_y = control_point
        
        # Sample points along bezier curve and find minimum distance
        # Quadratic bezier: B(t) = (1-t)²*P0 + 2(1-t)t*P1 + t²*P2
        sx, sy = self.source.x, self.source.y
        tx, ty = self.target.x, self.target.y
        
        min_dist_sq = float('inf')
        samples = 20  # Number of samples along curve
        
        for i in range(samples + 1):
            t = i / samples
            
            # Quadratic bezier formula
            b0 = (1 - t) * (1 - t)
            b1 = 2 * (1 - t) * t
            b2 = t * t
            
            curve_x = b0 * sx + b1 * cp_x + b2 * tx
            curve_y = b0 * sy + b1 * cp_y + b2 * ty
            
            # Distance to sampled point
            dist_sq = (x - curve_x) ** 2 + (y - curve_y) ** 2
            min_dist_sq = min(min_dist_sq, dist_sq)
        
        # Tolerance: 10 pixels in world space
        tolerance = 10.0
        
        return min_dist_sq <= (tolerance * tolerance)
    
    def __repr__(self):
        """String representation of the curved arc."""
        return (f"CurvedArc(id={self.id}, source={self.source.id}, "
                f"target={self.target.id}, weight={self.weight})")
```

## Phase 2: Create CurvedInhibitorArc Class

**File:** `src/shypn/netobjs/curved_inhibitor_arc.py`

```python
#!/usr/bin/env python3
"""CurvedInhibitorArc - Inhibitor arc with bezier curve path.

Combines curved path from CurvedArc with hollow circle marker from InhibitorArc.
"""
from .curved_arc import CurvedArc
from .inhibitor_arc import InhibitorArc


class CurvedInhibitorArc(CurvedArc):
    """Inhibitor arc rendered with a bezier curve path.
    
    Inherits:
    - Bezier curve rendering from CurvedArc
    - Uses InhibitorArc's marker rendering method
    
    This class combines the best of both:
    - Smooth curve to avoid overlap with opposite arcs
    - Hollow circle marker for inhibitor semantics
    """
    
    def __init__(self, source, target, id: int, name: str, weight: int = 1):
        """Initialize a curved inhibitor arc.
        
        Args:
            source: Source PetriNetObject
            target: Target PetriNetObject
            id: Unique integer identifier (immutable, system-assigned)
            name: Unique name in format "CI1", "CI2", etc. (immutable, system-assigned)
            weight: Arc weight (default: 1)
        """
        super().__init__(source, target, id, name, weight)
    
    def _render_arrowhead(self, cr, x: float, y: float, dx: float, dy: float, zoom: float = 1.0):
        """Render hollow circle marker instead of two-line arrowhead.
        
        Delegates to InhibitorArc's implementation to avoid code duplication.
        
        Args:
            cr: Cairo context
            x, y: Marker center position (world coords)
            dx, dy: Direction vector (for future use with line trimming)
            zoom: Current zoom level for size compensation
        """
        # Use InhibitorArc's marker rendering
        # This is composition through method delegation
        InhibitorArc._render_arrowhead(self, cr, x, y, dx, dy, zoom)
    
    def __repr__(self):
        """String representation of the curved inhibitor arc."""
        return (f"CurvedInhibitorArc(id={self.id}, source={self.source.id}, "
                f"target={self.target.id}, weight={self.weight})")
```

## Phase 3: Update Exports

**File:** `src/shypn/netobjs/__init__.py`

```python
"""Petri Net Object Primitives.

This package contains the core Petri net modeling primitives:
- PetriNetObject: Base class for all Petri net objects
- Place: Circular nodes that hold tokens
- Transition: Rectangular bars representing events/actions
- Arc: Directed arrows connecting places and transitions (straight line)
- InhibitorArc: Inhibitor arcs with hollow circle marker (straight line)
- CurvedArc: Regular arcs with bezier curve (two-line arrowhead)
- CurvedInhibitorArc: Inhibitor arcs with bezier curve (hollow circle marker)

All classes are exported at the package level for convenient importing.
"""
from shypn.netobjs.petri_net_object import PetriNetObject
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.netobjs.curved_arc import CurvedArc
from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc

__all__ = [
    'PetriNetObject',
    'Place',
    'Transition',
    'Arc',
    'InhibitorArc',
    'CurvedArc',
    'CurvedInhibitorArc'
]
```

## Phase 4: Serialization Support

Each class needs to save/load correctly. We'll use a `class_name` field in JSON:

### Arc Serialization (already exists in Arc class)

```python
def to_dict(self) -> dict:
    data = super().to_dict()
    data.update({
        "type": "arc",  # This becomes "inhibitor_arc", "curved_arc", etc.
        # ... other fields
    })
    return data
```

### Factory Pattern for Deserialization

**Location:** Add to Arc class or create separate factory

```python
@classmethod
def create_from_dict(cls, data: dict, places: dict, transitions: dict):
    """Factory method to create appropriate arc subclass.
    
    Args:
        data: Dictionary containing arc properties
        places: Dictionary mapping place IDs to Place instances
        transitions: Dictionary mapping transition IDs to Transition instances
        
    Returns:
        Arc subclass instance (Arc, InhibitorArc, CurvedArc, or CurvedInhibitorArc)
    """
    arc_type = data.get("type", "arc")
    
    # Map type string to class
    class_map = {
        "arc": Arc,
        "inhibitor_arc": InhibitorArc,
        "curved_arc": CurvedArc,
        "curved_inhibitor_arc": CurvedInhibitorArc
    }
    
    arc_class = class_map.get(arc_type, Arc)  # Default to Arc for backward compatibility
    
    # Use the appropriate class's from_dict method
    return arc_class.from_dict(data, places, transitions)
```

### Update Subclass to_dict Methods

```python
# In InhibitorArc
def to_dict(self) -> dict:
    data = super().to_dict()
    data["type"] = "inhibitor_arc"  # Override type
    return data

# In CurvedArc
def to_dict(self) -> dict:
    data = super().to_dict()
    data["type"] = "curved_arc"
    return data

# In CurvedInhibitorArc
def to_dict(self) -> dict:
    data = super().to_dict()
    data["type"] = "curved_inhibitor_arc"
    return data
```

## Phase 5: Testing

### Unit Tests

**File:** `tests/test_arc_classes.py`

```python
import pytest
from src.shypn.netobjs import Arc, InhibitorArc, CurvedArc, CurvedInhibitorArc
from src.shypn.netobjs import Place, Transition


class TestArcHierarchy:
    """Test arc class hierarchy and inheritance."""
    
    def setup_method(self):
        """Create test fixtures."""
        self.place = Place(id=1, name="P1", x=0, y=0, tokens=0)
        self.transition = Transition(id=2, name="T1", x=100, y=0)
    
    def test_arc_is_base_class(self):
        """Arc is base class for all arc types."""
        arc = Arc(self.place, self.transition, id=10, name="A1")
        assert isinstance(arc, Arc)
        assert type(arc) == Arc
    
    def test_inhibitor_arc_inherits_from_arc(self):
        """InhibitorArc inherits from Arc."""
        arc = InhibitorArc(self.place, self.transition, id=11, name="I1")
        assert isinstance(arc, Arc)
        assert isinstance(arc, InhibitorArc)
        assert type(arc) == InhibitorArc
    
    def test_curved_arc_inherits_from_arc(self):
        """CurvedArc inherits from Arc."""
        arc = CurvedArc(self.place, self.transition, id=12, name="C1")
        assert isinstance(arc, Arc)
        assert isinstance(arc, CurvedArc)
        assert type(arc) == CurvedArc
    
    def test_curved_inhibitor_inherits_from_curved(self):
        """CurvedInhibitorArc inherits from CurvedArc."""
        arc = CurvedInhibitorArc(self.place, self.transition, id=13, name="CI1")
        assert isinstance(arc, Arc)
        assert isinstance(arc, CurvedArc)
        assert isinstance(arc, CurvedInhibitorArc)
        assert type(arc) == CurvedInhibitorArc
    
    def test_serialization_preserves_type(self):
        """Each arc type serializes with correct type field."""
        arcs = [
            (Arc(self.place, self.transition, 10, "A1"), "arc"),
            (InhibitorArc(self.place, self.transition, 11, "I1"), "inhibitor_arc"),
            (CurvedArc(self.place, self.transition, 12, "C1"), "curved_arc"),
            (CurvedInhibitorArc(self.place, self.transition, 13, "CI1"), "curved_inhibitor_arc")
        ]
        
        for arc, expected_type in arcs:
            data = arc.to_dict()
            assert data["type"] == expected_type


class TestCurvedArcGeometry:
    """Test curved arc bezier calculations."""
    
    def setup_method(self):
        """Create test fixtures."""
        self.place = Place(id=1, name="P1", x=0, y=0, tokens=0)
        self.transition = Transition(id=2, name="T1", x=100, y=0)
        self.arc = CurvedArc(self.place, self.transition, id=10, name="C1")
    
    def test_control_point_calculation(self):
        """Control point is perpendicular to line at 20% offset."""
        cp = self.arc._calculate_curve_control_point()
        
        assert cp is not None
        cp_x, cp_y = cp
        
        # Control point should be at midpoint perpendicular
        # Midpoint: (50, 0)
        # Line vector: (100, 0)
        # Perpendicular: (0, 1) or (0, -1)
        # Offset: 100 * 0.20 = 20
        
        assert abs(cp_x - 50) < 1e-6  # X should be at midpoint
        assert abs(abs(cp_y) - 20) < 1e-6  # Y should be ±20 (20% of 100)
    
    def test_degenerate_case(self):
        """Arcs with same source/target return None control point."""
        place = Place(id=3, name="P2", x=50, y=50, tokens=0)
        arc = CurvedArc(place, place, id=11, name="C2")
        
        cp = arc._calculate_curve_control_point()
        assert cp is None
```

### Manual Testing Checklist

```bash
# 1. Create test script
cat > test_arc_rendering.py << 'EOF'
#!/usr/bin/env python3
"""Manual test for arc rendering."""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import cairo

from src.shypn.netobjs import Place, Transition, Arc, InhibitorArc, CurvedArc, CurvedInhibitorArc


class ArcTestWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Arc Types Test")
        self.set_default_size(800, 600)
        
        # Create drawing area
        self.draw_area = Gtk.DrawingArea()
        self.draw_area.connect("draw", self.on_draw)
        self.add(self.draw_area)
        
        # Create test objects
        self.place1 = Place(1, "P1", x=100, y=300, tokens=0)
        self.trans1 = Transition(2, "T1", x=300, y=300)
        self.place2 = Place(3, "P2", x=500, y=300, tokens=0)
        
        # Create all 4 arc types
        self.arcs = [
            Arc(self.place1, self.trans1, 10, "A1", weight=1),
            InhibitorArc(self.trans1, self.place2, 11, "I1", weight=1),
            CurvedArc(self.place2, self.trans1, 12, "C1", weight=2),
            CurvedInhibitorArc(self.place1, self.trans1, 13, "CI1", weight=3)
        ]
    
    def on_draw(self, widget, cr):
        # White background
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
        
        # Render objects and arcs
        zoom = 1.0
        
        # Render places
        self.place1.render(cr, zoom=zoom)
        self.place2.render(cr, zoom=zoom)
        
        # Render transition
        self.trans1.render(cr, zoom=zoom)
        
        # Render all arc types
        for arc in self.arcs:
            arc.render(cr, zoom=zoom)


if __name__ == "__main__":
    win = ArcTestWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
EOF

# 2. Run test
python3 test_arc_rendering.py
```

**Expected Results:**
- Arc: Straight line, two-line arrowhead
- InhibitorArc: Straight line, hollow circle
- CurvedArc: Curved line, two-line arrowhead
- CurvedInhibitorArc: Curved line, hollow circle

## Summary of Changes

### Files to Create
1. `src/shypn/netobjs/curved_arc.py` (new)
2. `src/shypn/netobjs/curved_inhibitor_arc.py` (new)
3. `tests/test_arc_classes.py` (new)

### Files to Modify
1. `src/shypn/netobjs/__init__.py` - Add new exports
2. `src/shypn/netobjs/arc.py` - Add factory method for deserialization
3. `src/shypn/netobjs/inhibitor_arc.py` - Add to_dict override

### Files to Review (No Changes Yet)
- `src/shypn/helpers/arc_prop_dialog_loader.py` - DEFER until Phase 2
- `ui/dialogs/arc_prop_dialog.ui` - DEFER until Phase 2

## Next Steps

1. ✅ Review existing Arc and InhibitorArc classes
2. ⏳ Create CurvedArc class with bezier rendering
3. ⏳ Create CurvedInhibitorArc class
4. ⏳ Update __init__.py exports
5. ⏳ Add serialization support (to_dict overrides)
6. ⏳ Write unit tests
7. ⏳ Manual testing with rendering script
8. ⏳ Update documentation

## Questions Resolved

1. **Use subclasses instead of arc_type property** ✅
   - More object-oriented
   - Cleaner inheritance
   - Better type safety

2. **InhibitorArc already exists** ✅
   - Reuse existing implementation
   - No need to modify Arc base class

3. **Curve implementation** ✅
   - Quadratic bezier (single control point)
   - 20% perpendicular offset
   - Automatic calculation

4. **No loader changes yet** ✅
   - Focus on core classes first
   - UI integration is Phase 2

---

**Document Version:** 2.0 (Revised after code review)  
**Created:** 2025-10-05  
**Status:** READY FOR IMPLEMENTATION
