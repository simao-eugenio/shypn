# Arc Transformation Design - Context Menu Approach

## Overview

Instead of having 4 separate arc classes, we use **runtime transformation** via context menu:
- User draws normal Arc
- Right-click → Transform to curved/inhibitor
- System detects parallel arcs and auto-offsets them

## Design Philosophy

### Current Implementation ✅
- **4 Arc Classes**: Arc, InhibitorArc, CurvedArc, CurvedInhibitorArc
- Clean inheritance hierarchy
- Type-safe with `isinstance()` checks
- Each class handles its own rendering

### New UX Layer (To Add) 🆕
- **User draws simple arcs** (Arc or InhibitorArc only)
- **Context menu transformations**:
  - "Make Curved" / "Make Straight"
  - "Convert to Inhibitor Arc" / "Convert to Normal Arc"
- **Automatic parallel arc detection** with offset

## Implementation Strategy

### Phase 1: Keep Current Class Structure ✅ DONE

We keep all 4 classes because:
1. **Separation of concerns**: Each class handles its rendering logic
2. **No complex branching**: No `if is_curved and is_inhibitor` everywhere
3. **Easy testing**: Each class tested independently
4. **Extensibility**: Easy to add ReadArc, ResetArc, etc. later

### Phase 2: Add Context Menu Transformations 🆕

#### A. Arc Context Menu

**File:** `src/shypn/canvas/context_menus.py` (or similar)

```python
class ArcContextMenu:
    """Context menu for arc objects."""
    
    def __init__(self, canvas, arc):
        self.canvas = canvas
        self.arc = arc
        self.menu = Gtk.Menu()
        
        # Build menu based on current arc type
        self._build_menu()
    
    def _build_menu(self):
        """Build context menu with transformation options."""
        from shypn.netobjs import Arc, InhibitorArc, CurvedArc, CurvedInhibitorArc
        
        # Curve transformations
        if isinstance(self.arc, CurvedArc):
            item = Gtk.MenuItem(label="Make Straight")
            item.connect("activate", self._make_straight)
        else:
            item = Gtk.MenuItem(label="Make Curved")
            item.connect("activate", self._make_curved)
        self.menu.append(item)
        
        # Separator
        self.menu.append(Gtk.SeparatorMenuItem())
        
        # Inhibitor transformations
        if isinstance(self.arc, InhibitorArc) or isinstance(self.arc, CurvedInhibitorArc):
            item = Gtk.MenuItem(label="Convert to Normal Arc")
            item.connect("activate", self._convert_to_normal)
        else:
            item = Gtk.MenuItem(label="Convert to Inhibitor Arc")
            item.connect("activate", self._convert_to_inhibitor)
        self.menu.append(item)
        
        # Standard arc operations
        self.menu.append(Gtk.SeparatorMenuItem())
        
        item = Gtk.MenuItem(label="Properties...")
        item.connect("activate", self._show_properties)
        self.menu.append(item)
        
        item = Gtk.MenuItem(label="Delete")
        item.connect("activate", self._delete_arc)
        self.menu.append(item)
        
        self.menu.show_all()
    
    def _make_curved(self, widget):
        """Transform straight arc to curved arc."""
        new_arc = self._transform_arc_type(curved=True)
        self.canvas.replace_arc(self.arc, new_arc)
        self.canvas.queue_draw()
    
    def _make_straight(self, widget):
        """Transform curved arc to straight arc."""
        new_arc = self._transform_arc_type(curved=False)
        self.canvas.replace_arc(self.arc, new_arc)
        self.canvas.queue_draw()
    
    def _convert_to_inhibitor(self, widget):
        """Convert normal arc to inhibitor arc."""
        new_arc = self._transform_arc_type(inhibitor=True)
        self.canvas.replace_arc(self.arc, new_arc)
        self.canvas.queue_draw()
    
    def _convert_to_normal(self, widget):
        """Convert inhibitor arc to normal arc."""
        new_arc = self._transform_arc_type(inhibitor=False)
        self.canvas.replace_arc(self.arc, new_arc)
        self.canvas.queue_draw()
    
    def _transform_arc_type(self, curved=None, inhibitor=None):
        """Transform arc to different type while preserving properties.
        
        Args:
            curved: True=curved, False=straight, None=keep current
            inhibitor: True=inhibitor, False=normal, None=keep current
            
        Returns:
            New arc instance of appropriate type
        """
        from shypn.netobjs import Arc, InhibitorArc, CurvedArc, CurvedInhibitorArc
        
        # Determine current state
        is_curved = isinstance(self.arc, CurvedArc) or isinstance(self.arc, CurvedInhibitorArc)
        is_inhibitor = isinstance(self.arc, InhibitorArc) or isinstance(self.arc, CurvedInhibitorArc)
        
        # Apply transformations
        if curved is not None:
            is_curved = curved
        if inhibitor is not None:
            is_inhibitor = inhibitor
        
        # Select appropriate class
        if is_curved and is_inhibitor:
            arc_class = CurvedInhibitorArc
        elif is_curved:
            arc_class = CurvedArc
        elif is_inhibitor:
            arc_class = InhibitorArc
        else:
            arc_class = Arc
        
        # Create new arc with same properties
        new_arc = arc_class(
            source=self.arc.source,
            target=self.arc.target,
            id=self.arc.id,
            name=self.arc.name,
            weight=self.arc.weight
        )
        
        # Copy all properties
        new_arc.color = self.arc.color
        new_arc.width = self.arc.width
        new_arc.threshold = self.arc.threshold
        new_arc.control_points = self.arc.control_points
        new_arc.label = self.arc.label
        new_arc.description = self.arc.description
        
        return new_arc
    
    def _show_properties(self, widget):
        """Show arc properties dialog."""
        # Open properties dialog (existing implementation)
        pass
    
    def _delete_arc(self, widget):
        """Delete the arc."""
        self.canvas.delete_arc(self.arc)
        self.canvas.queue_draw()
    
    def show(self, event):
        """Show the context menu at mouse position."""
        self.menu.popup(None, None, None, None, event.button, event.time)
```

#### B. Canvas Integration

**File:** `src/shypn/canvas/net_canvas.py` (or similar)

```python
class NetCanvas:
    """Canvas for drawing Petri nets."""
    
    def __init__(self):
        # ... existing code ...
        self.connect("button-press-event", self._on_button_press)
    
    def _on_button_press(self, widget, event):
        """Handle mouse button press events."""
        if event.button == 3:  # Right-click
            # Find object under cursor
            obj = self._find_object_at(event.x, event.y)
            
            if obj is not None:
                from shypn.netobjs import Arc, InhibitorArc, CurvedArc, CurvedInhibitorArc
                
                # Show appropriate context menu
                if isinstance(obj, (Arc, InhibitorArc, CurvedArc, CurvedInhibitorArc)):
                    menu = ArcContextMenu(self, obj)
                    menu.show(event)
                    return True
                elif isinstance(obj, Place):
                    # Show place menu
                    pass
                elif isinstance(obj, Transition):
                    # Show transition menu
                    pass
        
        return False
    
    def replace_arc(self, old_arc, new_arc):
        """Replace an arc with a different type.
        
        Used during arc transformations (curved/straight, normal/inhibitor).
        
        Args:
            old_arc: Arc instance to replace
            new_arc: New arc instance (different class, same properties)
        """
        # Find old arc in list
        try:
            index = self.petri_net.arcs.index(old_arc)
        except ValueError:
            return  # Arc not found
        
        # Replace in list
        self.petri_net.arcs[index] = new_arc
        
        # Update source/target arc lists
        if hasattr(old_arc.source, 'outgoing_arcs'):
            old_arc.source.outgoing_arcs.remove(old_arc)
            old_arc.source.outgoing_arcs.append(new_arc)
        
        if hasattr(old_arc.target, 'incoming_arcs'):
            old_arc.target.incoming_arcs.remove(old_arc)
            old_arc.target.incoming_arcs.append(new_arc)
        
        # Emit change signal
        self.emit('net-modified')
```

### Phase 3: Parallel Arc Detection and Auto-Offset 🆕

#### A. Parallel Arc Detection

```python
class PetriNet:
    """Petri net model."""
    
    def detect_parallel_arcs(self, arc):
        """Find arcs parallel to the given arc (same source/target or reversed).
        
        Args:
            arc: Arc to check for parallels
            
        Returns:
            list: List of parallel arcs (excluding the given arc)
        """
        parallels = []
        
        for other in self.arcs:
            if other == arc:
                continue
            
            # Same direction: same source and target
            if (other.source == arc.source and other.target == arc.target):
                parallels.append(other)
            
            # Opposite direction: reversed source and target
            elif (other.source == arc.target and other.target == arc.source):
                parallels.append(other)
        
        return parallels
    
    def calculate_arc_offset(self, arc, parallels):
        """Calculate offset for arc to avoid overlapping parallels.
        
        For parallel arcs between same nodes, we offset them perpendicular
        to the line connecting the nodes.
        
        Args:
            arc: Arc to calculate offset for
            parallels: List of parallel arcs
            
        Returns:
            float: Offset distance in pixels (positive = counterclockwise)
        """
        if not parallels:
            return 0.0  # No offset needed
        
        # Find arc's position in the set of all parallel arcs
        all_arcs = [arc] + parallels
        all_arcs.sort(key=lambda a: a.id)  # Stable ordering
        
        index = all_arcs.index(arc)
        total = len(all_arcs)
        
        # Calculate offset
        # For 2 arcs: offsets are +15, -15
        # For 3 arcs: offsets are +20, 0, -20
        # For 4 arcs: offsets are +30, +10, -10, -30
        
        if total == 1:
            return 0.0
        elif total == 2:
            return 15.0 if index == 0 else -15.0
        else:
            # Spread arcs evenly
            spacing = 20.0
            center = (total - 1) / 2.0
            return (index - center) * spacing
```

#### B. Curved Arc with Offset

Modify `CurvedArc._calculate_curve_control_point()` to accept offset parameter:

```python
class CurvedArc(Arc):
    """Arc rendered with a bezier curve path."""
    
    def _calculate_curve_control_point(self, offset=None) -> Optional[Tuple[float, float]]:
        """Calculate bezier control point for curved arc.
        
        Creates a curve that bows perpendicular to the straight line
        connecting source and target. Used for opposite arcs.
        
        Args:
            offset: Optional manual offset distance (for parallel arcs)
                   If None, uses default 20% of line length
        
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
        
        # Control point offset
        if offset is None:
            # Default: 20% of line length
            offset = length * self.CURVE_OFFSET_RATIO
        
        # Control point at midpoint + perpendicular offset
        cp_x = mx + perp_x * offset
        cp_y = my + perp_y * offset
        
        return (cp_x, cp_y)
    
    def render(self, cr, transform=None, zoom=1.0):
        """Render curved arc using bezier path.
        
        Automatically detects parallel arcs and applies offset.
        """
        # Check for parallel arcs
        if hasattr(self, '_petri_net') and self._petri_net:
            parallels = self._petri_net.detect_parallel_arcs(self)
            if parallels:
                offset = self._petri_net.calculate_arc_offset(self, parallels)
                control_point = self._calculate_curve_control_point(offset=offset)
            else:
                control_point = self._calculate_curve_control_point()
        else:
            control_point = self._calculate_curve_control_point()
        
        # ... rest of rendering code ...
```

#### C. Straight Arc with Offset

For straight arcs with parallels, we need to offset the **endpoints** slightly:

```python
class Arc(PetriNetObject):
    """A directed arc in a Petri net."""
    
    def render(self, cr, transform=None, zoom=1.0):
        """Render the arc using Cairo.
        
        Automatically detects parallel arcs and applies offset.
        """
        # Get source and target positions in world space
        src_world_x, src_world_y = self.source.x, self.source.y
        tgt_world_x, tgt_world_y = self.target.x, self.target.y
        
        # Calculate direction in world space
        dx_world = tgt_world_x - src_world_x
        dy_world = tgt_world_y - src_world_y
        length_world = math.sqrt(dx_world * dx_world + dy_world * dy_world)
        
        if length_world < 1:
            return  # Too short to draw
        
        # Normalize direction
        dx_world /= length_world
        dy_world /= length_world
        
        # Check for parallel arcs and apply offset
        offset_distance = 0.0
        if hasattr(self, '_petri_net') and self._petri_net:
            parallels = self._petri_net.detect_parallel_arcs(self)
            if parallels:
                offset_distance = self._petri_net.calculate_arc_offset(self, parallels)
        
        if abs(offset_distance) > 1e-6:
            # Apply perpendicular offset to line
            perp_x = -dy_world
            perp_y = dx_world
            
            src_world_x += perp_x * offset_distance
            src_world_y += perp_y * offset_distance
            tgt_world_x += perp_x * offset_distance
            tgt_world_y += perp_y * offset_distance
        
        # Get boundary points in world space
        start_world_x, start_world_y = self._get_boundary_point(
            self.source, src_world_x, src_world_y, dx_world, dy_world)
        end_world_x, end_world_y = self._get_boundary_point(
            self.target, tgt_world_x, tgt_world_y, -dx_world, -dy_world)
        
        # ... rest of rendering code ...
```

## User Workflow Examples

### Example 1: Create Opposite Arcs

**Before:**
```
[Place] -----> [Transition]
```

**User actions:**
1. Draw arc from Place to Transition (creates Arc)
2. Draw arc from Transition to Place (creates Arc)
3. System detects parallel arcs → suggests making them curved

**Result:**
```
        ╭─────╮
[Place]         [Transition]
        ╰─────╯
```

### Example 2: Convert to Inhibitor

**Before:**
```
[Place] -----> [Transition]
```

**User actions:**
1. Right-click on arc
2. Select "Convert to Inhibitor Arc"
3. Arc transforms to InhibitorArc (hollow circle marker)

**Result:**
```
[Place] ----○ [Transition]
```

### Example 3: Multiple Parallel Arcs

**Before:**
```
[Place] -----> [Transition]
[Place] -----> [Transition]
[Place] -----> [Transition]
```

**User actions:**
1. Draw 3 arcs from same Place to same Transition
2. System automatically offsets them (+20, 0, -20)

**Result:**
```
        ------>
[Place] -------> [Transition]
        ------>
```

## Implementation Plan - Phase 2

### Step 1: Add Context Menu Infrastructure
- [ ] Create `ArcContextMenu` class
- [ ] Integrate with canvas right-click handling
- [ ] Add "Make Curved/Straight" menu items
- [ ] Add "Convert to Inhibitor/Normal" menu items

### Step 2: Implement Arc Transformation
- [ ] Add `replace_arc()` method to canvas/petri net
- [ ] Implement `_transform_arc_type()` logic
- [ ] Preserve all arc properties during transformation
- [ ] Emit appropriate signals for undo/redo

### Step 3: Parallel Arc Detection
- [ ] Add `detect_parallel_arcs()` to PetriNet class
- [ ] Add `calculate_arc_offset()` to PetriNet class
- [ ] Store reference to parent PetriNet in arcs

### Step 4: Apply Offsets to Rendering
- [ ] Modify `Arc.render()` to apply straight line offset
- [ ] Modify `CurvedArc._calculate_curve_control_point()` to accept offset
- [ ] Update boundary point calculations for offsets
- [ ] Test with 2, 3, 4+ parallel arcs

### Step 5: User Experience Enhancements
- [ ] Show tooltip: "Right-click to make curved" when hovering arc
- [ ] Highlight parallel arcs when one is selected
- [ ] Add "Auto-curve opposite arcs" preference
- [ ] Add keyboard shortcut: C = toggle curved, I = toggle inhibitor

### Step 6: Testing
- [ ] Test context menu transformations
- [ ] Test parallel arc offset calculations
- [ ] Test with complex net topologies
- [ ] Test serialization preserves arc types after transformation
- [ ] Test undo/redo of transformations

## Benefits of This Approach

### For Users:
✅ **Simple workflow**: Draw normal arcs, transform later
✅ **Visual feedback**: See curves automatically adjust for parallels
✅ **Flexible**: Easy to switch between arc types
✅ **Discoverable**: Right-click reveals options

### For Developers:
✅ **Clean architecture**: 4 classes with clear responsibilities
✅ **No complex state**: No `is_curved` flags scattered in code
✅ **Easy testing**: Each class independently testable
✅ **Extensible**: Easy to add new arc types (ReadArc, ResetArc)

### For Maintenance:
✅ **Type safety**: `isinstance()` checks work correctly
✅ **No branching**: No nested `if` statements for arc types
✅ **Clear inheritance**: Arc → InhibitorArc, Arc → CurvedArc
✅ **Testable**: Each transformation testable separately

## Summary

**Phase 1 (✅ DONE):**
- Created 4 arc classes
- Implemented bezier curve geometry
- Added serialization support
- All tests passing

**Phase 2 (🆕 NEXT):**
- Add context menu for arc transformations
- Implement parallel arc detection
- Add automatic offset calculation
- Apply offsets to rendering

**Phase 3 (Future):**
- Integrate with properties dialog
- Add simulation engine support for inhibitor arcs
- Add undo/redo for transformations
- Add user preferences for auto-curving

---

**Document Version:** 1.0  
**Created:** 2025-10-05  
**Status:** DESIGN APPROVED - Ready for Phase 2 Implementation
