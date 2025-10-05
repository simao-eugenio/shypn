# Arc Types Implementation Plan

## Overview

This document outlines the implementation plan for 4 distinct arc types in the SHYPN Petri net editor:

1. **Normal Arc**: Standard arc with two-line arrowhead (ALREADY IMPLEMENTED)
2. **Curved Opposite Arc**: Normal arc with bezier curve (for parallel opposite arcs)
3. **Inhibitor Arc**: Arc with hollow circle arrowhead (inverted enabling logic)
4. **Curved Inhibitor Arc**: Inhibitor arc with bezier curve

## Current State Analysis

### Existing Implementation (`src/shypn/netobjs/arc.py`)

**Properties:**
- `source`: Source node (Place or Transition)
- `target`: Target node (Transition or Place)
- `weight`: Arc weight (default 1)
- `color`: Arc color (hex string)
- `width`: Line width (default 3.0)
- `threshold`: Firing threshold (for stochastic nets)
- `control_points`: List of (x,y) tuples (UNUSED - curve feature not implemented)

**Rendering:**
- Two-line arrowhead: 15px size, 36° angle (π/5 radians)
- Weight label: Displayed if weight > 1, white background
- Glow effect: For colored arcs
- Zoom compensation: Arrow size and line width scale correctly

**Missing:**
- `arc_type` property
- `is_inhibitor` flag
- Curve rendering implementation
- Hollow circle arrowhead
- Opposite arc detection

## Architecture Design

### 1. Arc Type Enumeration

**Option A: String-based (RECOMMENDED)**
```python
ARC_TYPE_NORMAL = 'normal'
ARC_TYPE_CURVED_OPPOSITE = 'curved_opposite'
ARC_TYPE_INHIBITOR = 'inhibitor'
ARC_TYPE_CURVED_INHIBITOR = 'curved_inhibitor'
```

**Rationale:**
- Easy serialization (JSON-friendly)
- Human-readable in saved files
- Backward compatible (missing arc_type defaults to 'normal')

**Option B: Enum-based**
```python
from enum import Enum

class ArcType(Enum):
    NORMAL = 'normal'
    CURVED_OPPOSITE = 'curved_opposite'
    INHIBITOR = 'inhibitor'
    CURVED_INHIBITOR = 'curved_inhibitor'
```

**Rationale:**
- Type safety
- IDE autocomplete
- More complex serialization

**Decision: Use Option A for simplicity and compatibility**

### 2. Data Model Changes

**Arc Class (`src/shypn/netobjs/arc.py`)**

```python
class Arc(PetriNetObject):
    def __init__(self, source, target, id=None, name=None, description=None,
                 weight=1, color=None, width=None, threshold=None,
                 control_points=None, arc_type='normal'):  # NEW
        # ... existing code ...
        self.arc_type = arc_type  # NEW
    
    @property
    def is_inhibitor(self):
        """Returns True if this is an inhibitor arc."""
        return self.arc_type in ['inhibitor', 'curved_inhibitor']
    
    @property
    def is_curved(self):
        """Returns True if this is a curved arc."""
        return self.arc_type in ['curved_opposite', 'curved_inhibitor']
    
    def to_dict(self):
        """Serialize arc to dictionary."""
        data = super().to_dict()
        data.update({
            'arc_type': self.arc_type,  # NEW
            # ... existing fields ...
        })
        return data
    
    @classmethod
    def from_dict(cls, data, node_map):
        """Deserialize arc from dictionary."""
        return cls(
            arc_type=data.get('arc_type', 'normal'),  # NEW with default
            # ... existing fields ...
        )
```

**Backward Compatibility:**
- Old saved files without `arc_type` default to `'normal'`
- No migration script needed
- Transparent upgrade path

### 3. Rendering Implementation

#### A. Curved Arc Rendering

**Challenge:** Draw smooth bezier curve from source to target

**Implementation:**

```python
def _calculate_curve_control_points(self):
    """Calculate bezier control points for curved arc.
    
    For opposite arcs, creates a curve that bows outward from the
    straight line connecting source and target.
    """
    sx, sy = self._get_source_boundary_point()
    tx, ty = self._get_target_boundary_point()
    
    # Midpoint of straight line
    mx = (sx + tx) / 2
    my = (sy + ty) / 2
    
    # Vector perpendicular to line
    dx = tx - sx
    dy = ty - sy
    length = math.sqrt(dx*dx + dy*dy)
    
    if length < 1e-6:
        return []  # Degenerate case: same point
    
    # Unit perpendicular vector (rotated 90° counterclockwise)
    perp_x = -dy / length
    perp_y = dx / length
    
    # Control point offset: 20% of line length
    offset = length * 0.2
    
    # Single control point at midpoint + perpendicular offset
    cp_x = mx + perp_x * offset
    cp_y = my + perp_y * offset
    
    return [(cp_x, cp_y)]

def _render_curved_path(self, ctx, zoom):
    """Render curved arc path using quadratic bezier."""
    sx, sy = self._get_source_boundary_point()
    tx, ty = self._get_target_boundary_point()
    
    control_points = self._calculate_curve_control_points()
    
    if not control_points:
        # Fallback to straight line
        ctx.move_to(sx, sy)
        ctx.line_to(tx, ty)
        return (sx, sy), (tx, ty)
    
    ctx.move_to(sx, sy)
    cp_x, cp_y = control_points[0]
    ctx.curve_to(cp_x, cp_y, cp_x, cp_y, tx, ty)  # Quadratic bezier
    
    # Calculate curve tangent at target for arrowhead orientation
    # Tangent = derivative at t=1
    t = 1.0
    tangent_x = 2 * (1 - t) * (cp_x - sx) + 2 * t * (tx - cp_x)
    tangent_y = 2 * (1 - t) * (cp_y - sy) + 2 * t * (ty - cp_y)
    
    return (tangent_x, tangent_y), (tx, ty)
```

**Curve Parameters:**
- **Offset**: 20% of line length (configurable constant)
- **Direction**: Perpendicular to straight line
- **Side**: Always counterclockwise (consistent with opposite arc detection)
- **Type**: Quadratic bezier (single control point)

#### B. Inhibitor Arrowhead Rendering

**Challenge:** Draw hollow circle instead of two-line arrowhead

**Implementation:**

```python
def _render_inhibitor_arrowhead(self, ctx, arrow_tip, tangent, zoom):
    """Render hollow circle arrowhead for inhibitor arcs.
    
    Args:
        ctx: Cairo context
        arrow_tip: (x, y) tuple of arrow tip position
        tangent: (dx, dy) tuple of line tangent at tip
        zoom: Current zoom level
    """
    tx, ty = arrow_tip
    dx, dy = tangent
    
    # Normalize tangent
    length = math.sqrt(dx*dx + dy*dy)
    if length < 1e-6:
        return
    dx, dy = dx / length, dy / length
    
    # Circle parameters
    circle_radius = self.ARROW_SIZE / zoom  # 15px compensated for zoom
    
    # Circle center: move back from tip along tangent
    center_x = tx - dx * circle_radius
    center_y = ty - dy * circle_radius
    
    # Draw hollow circle
    ctx.arc(center_x, center_y, circle_radius, 0, 2 * math.pi)
    ctx.set_source_rgb(*self._get_render_color())
    ctx.set_line_width(self.width / zoom)
    ctx.stroke()
    
    # Adjust arc line to end at circle edge
    return (center_x - dx * circle_radius, center_y - dy * circle_radius)

def _render_arrowhead(self, ctx, arrow_tip, tangent, zoom):
    """Render appropriate arrowhead based on arc type."""
    if self.is_inhibitor:
        return self._render_inhibitor_arrowhead(ctx, arrow_tip, tangent, zoom)
    else:
        # Existing two-line arrowhead code
        # ... (lines 256-290 of current implementation)
```

**Circle Parameters:**
- **Radius**: 15px (same as ARROW_SIZE constant)
- **Style**: Hollow (stroke only, no fill)
- **Color**: Same as arc color
- **Line width**: Same as arc line width
- **Position**: Circle center at arrow tip, arc line ends at circle edge

#### C. Unified Render Method

**Modified `render()` method:**

```python
def render(self, ctx, zoom, selected=False, hover=False):
    """Render arc with appropriate style based on arc_type."""
    # ... existing setup code ...
    
    # Render path
    if self.is_curved:
        tangent, arrow_tip = self._render_curved_path(ctx, zoom)
    else:
        # Existing straight line code
        tangent, arrow_tip = self._render_straight_path(ctx, zoom)
    
    ctx.stroke()
    
    # Render arrowhead (branches internally based on is_inhibitor)
    self._render_arrowhead(ctx, arrow_tip, tangent, zoom)
    
    # Render weight (existing code)
    if self.weight > 1:
        self._render_weight(ctx, zoom)
    
    # ... existing highlight/glow code ...
```

### 4. User Interface Changes

#### A. Arc Properties Dialog UI (`ui/dialogs/arc_prop_dialog.ui`)

**Add Arc Type Selector:**

```xml
<!-- After line_width_spinbutton, before threshold section -->
<object class="GtkBox" id="arc_type_box">
  <property name="orientation">vertical</property>
  <property name="spacing">6</property>
  
  <child>
    <object class="GtkLabel">
      <property name="label">Arc Type:</property>
      <property name="xalign">0</property>
    </object>
  </child>
  
  <child>
    <object class="GtkRadioButton" id="arc_type_normal">
      <property name="label">Normal Arc</property>
      <property name="active">True</property>
    </object>
  </child>
  
  <child>
    <object class="GtkRadioButton" id="arc_type_curved_opposite">
      <property name="label">Curved Opposite Arc</property>
      <property name="group">arc_type_normal</property>
    </object>
  </child>
  
  <child>
    <object class="GtkRadioButton" id="arc_type_inhibitor">
      <property name="label">Inhibitor Arc</property>
      <property name="group">arc_type_normal</property>
    </object>
  </child>
  
  <child>
    <object class="GtkRadioButton" id="arc_type_curved_inhibitor">
      <property name="label">Curved Inhibitor Arc</property>
      <property name="group">arc_type_normal</property>
    </object>
  </child>
</object>
```

**Alternative: Dropdown ComboBox**
```xml
<object class="GtkComboBoxText" id="arc_type_combo">
  <items>
    <item>Normal Arc</item>
    <item>Curved Opposite Arc</item>
    <item>Inhibitor Arc</item>
    <item>Curved Inhibitor Arc</item>
  </items>
</object>
```

**Recommendation:** Use **Radio Buttons** for clear visual distinction of 4 mutually exclusive options.

#### B. Arc Properties Dialog Loader (`src/shypn/helpers/arc_prop_dialog_loader.py`)

**Modify `_populate_fields()` method:**

```python
def _populate_fields(self):
    """Populate dialog fields from arc properties."""
    # ... existing code ...
    
    # Populate arc type radio buttons
    arc_type = self.arc.arc_type
    if arc_type == 'normal':
        self.builder.get_object('arc_type_normal').set_active(True)
    elif arc_type == 'curved_opposite':
        self.builder.get_object('arc_type_curved_opposite').set_active(True)
    elif arc_type == 'inhibitor':
        self.builder.get_object('arc_type_inhibitor').set_active(True)
    elif arc_type == 'curved_inhibitor':
        self.builder.get_object('arc_type_curved_inhibitor').set_active(True)
```

**Modify `_apply_changes()` method:**

```python
def _apply_changes(self):
    """Apply dialog changes to arc object."""
    changes = {}
    
    # ... existing code ...
    
    # Get selected arc type
    if self.builder.get_object('arc_type_normal').get_active():
        new_arc_type = 'normal'
    elif self.builder.get_object('arc_type_curved_opposite').get_active():
        new_arc_type = 'curved_opposite'
    elif self.builder.get_object('arc_type_inhibitor').get_active():
        new_arc_type = 'inhibitor'
    elif self.builder.get_object('arc_type_curved_inhibitor').get_active():
        new_arc_type = 'curved_inhibitor'
    else:
        new_arc_type = 'normal'  # Default
    
    if new_arc_type != self.arc.arc_type:
        changes['arc_type'] = new_arc_type
    
    # Apply changes and emit signal
    for key, value in changes.items():
        setattr(self.arc, key, value)
    
    if changes:
        self.emit('properties-changed', self.arc, changes)
```

### 5. Opposite Arc Detection

**Feature:** Automatically suggest curved type when opposite arc exists

**Implementation:**

```python
# In NetCanvas or PetriNet class
def _detect_opposite_arcs(self, new_arc):
    """Check if a reverse arc exists between the same nodes.
    
    Args:
        new_arc: Newly created arc
        
    Returns:
        Opposite arc object if found, None otherwise
    """
    for arc in self.petri_net.arcs:
        if arc == new_arc:
            continue
        if (arc.source == new_arc.target and 
            arc.target == new_arc.source):
            return arc
    return None

def on_arc_created(self, new_arc):
    """Called when user creates new arc."""
    opposite = self._detect_opposite_arcs(new_arc)
    
    if opposite:
        # Show dialog: "Opposite arc detected. Make both curved?"
        dialog = Gtk.MessageDialog(
            parent=self.window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Opposite arc detected"
        )
        dialog.format_secondary_text(
            "Would you like to make both arcs curved to avoid overlap?"
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            # Convert both arcs to curved
            if new_arc.arc_type == 'normal':
                new_arc.arc_type = 'curved_opposite'
            elif new_arc.arc_type == 'inhibitor':
                new_arc.arc_type = 'curved_inhibitor'
            
            if opposite.arc_type == 'normal':
                opposite.arc_type = 'curved_opposite'
            elif opposite.arc_type == 'inhibitor':
                opposite.arc_type = 'curved_inhibitor'
            
            self.queue_draw()
```

### 6. Simulation Engine Integration

**Challenge:** Inhibitor arcs have inverted enabling logic

**Current Logic (Normal Arc):**
```python
# Transition is enabled if:
# - All input places have >= arc.weight tokens
enabled = all(place.tokens >= arc.weight for arc in input_arcs)
```

**New Logic (With Inhibitor Arcs):**
```python
def is_transition_enabled(transition):
    """Check if transition can fire considering inhibitor arcs."""
    for arc in transition.input_arcs:
        place = arc.source
        
        if arc.is_inhibitor:
            # Inhibitor arc: enabled if place has < threshold tokens
            threshold = arc.threshold if arc.threshold else arc.weight
            if place.tokens >= threshold:
                return False  # Inhibited
        else:
            # Normal arc: enabled if place has >= weight tokens
            if place.tokens < arc.weight:
                return False  # Not enough tokens
    
    return True  # All conditions met
```

**File to Modify:** `src/shypn/simulator/engine.py` (or equivalent)

### 7. Testing Strategy

#### Unit Tests

**Test File:** `tests/test_arc_types.py`

```python
import pytest
from src.shypn.netobjs.arc import Arc
from src.shypn.netobjs.place import Place
from src.shypn.netobjs.transition import Transition

class TestArcTypes:
    def test_arc_type_default(self):
        """New arcs default to 'normal' type."""
        place = Place(id='p1', x=0, y=0)
        trans = Transition(id='t1', x=100, y=0)
        arc = Arc(source=place, target=trans)
        assert arc.arc_type == 'normal'
    
    def test_is_inhibitor_property(self):
        """is_inhibitor returns True for inhibitor types."""
        place = Place(id='p1', x=0, y=0)
        trans = Transition(id='t1', x=100, y=0)
        
        arc1 = Arc(source=place, target=trans, arc_type='inhibitor')
        assert arc1.is_inhibitor is True
        
        arc2 = Arc(source=place, target=trans, arc_type='curved_inhibitor')
        assert arc2.is_inhibitor is True
        
        arc3 = Arc(source=place, target=trans, arc_type='normal')
        assert arc3.is_inhibitor is False
    
    def test_serialization_preserves_arc_type(self):
        """Arc type is saved and loaded correctly."""
        place = Place(id='p1', x=0, y=0)
        trans = Transition(id='t1', x=100, y=0)
        arc = Arc(source=place, target=trans, arc_type='inhibitor')
        
        data = arc.to_dict()
        assert data['arc_type'] == 'inhibitor'
        
        # Simulate load
        node_map = {'p1': place, 't1': trans}
        loaded_arc = Arc.from_dict(data, node_map)
        assert loaded_arc.arc_type == 'inhibitor'
    
    def test_backward_compatibility(self):
        """Old saved files without arc_type load as 'normal'."""
        data = {
            'id': 'a1',
            'source_id': 'p1',
            'target_id': 't1',
            'weight': 1,
            # No arc_type field
        }
        
        place = Place(id='p1', x=0, y=0)
        trans = Transition(id='t1', x=100, y=0)
        node_map = {'p1': place, 't1': trans}
        
        arc = Arc.from_dict(data, node_map)
        assert arc.arc_type == 'normal'
```

#### Integration Tests

**Test File:** `tests/test_arc_rendering.py`

```python
def test_inhibitor_arrowhead_renders():
    """Inhibitor arc renders hollow circle arrowhead."""
    # Create mock Cairo context
    # Create inhibitor arc
    # Call render()
    # Verify ctx.arc() was called (circle rendering)
    # Verify ctx.stroke() was called (hollow, not filled)

def test_curved_arc_renders():
    """Curved arc renders bezier curve."""
    # Create curved arc
    # Call render()
    # Verify ctx.curve_to() was called
    # Verify control points calculated correctly
```

#### Manual Testing Checklist

1. **Visual Rendering:**
   - [ ] Normal arc: Two-line arrowhead, straight line
   - [ ] Curved opposite arc: Two-line arrowhead, smooth curve
   - [ ] Inhibitor arc: Hollow circle arrowhead, straight line
   - [ ] Curved inhibitor arc: Hollow circle arrowhead, smooth curve

2. **Zoom Levels:**
   - [ ] All arc types render correctly at 50% zoom
   - [ ] All arc types render correctly at 100% zoom
   - [ ] All arc types render correctly at 200% zoom

3. **Properties Dialog:**
   - [ ] Arc type radio buttons work correctly
   - [ ] Changing arc type updates rendering immediately
   - [ ] Dialog preserves other properties when changing type

4. **Persistence:**
   - [ ] Save file with all 4 arc types
   - [ ] Reload file and verify arc types preserved
   - [ ] Load old file without arc_type (should default to normal)

5. **Simulation:**
   - [ ] Normal arc: Transition fires when tokens >= weight
   - [ ] Inhibitor arc: Transition fires when tokens < threshold
   - [ ] Mixed arcs: Transition logic correct with both types

6. **Opposite Arc Detection:**
   - [ ] Creating opposite arc shows dialog
   - [ ] Both arcs convert to curved when user accepts
   - [ ] User can decline and keep straight arcs

## Implementation Phases

### Phase 1: Core Data Model (1-2 days)
- [ ] Add arc_type property to Arc class
- [ ] Add is_inhibitor and is_curved properties
- [ ] Update to_dict/from_dict for serialization
- [ ] Write unit tests for data model
- [ ] Test backward compatibility

### Phase 2: Inhibitor Rendering (1-2 days)
- [ ] Implement _render_inhibitor_arrowhead method
- [ ] Modify _render_arrowhead to branch on arc_type
- [ ] Test rendering at different zooms
- [ ] Verify line ends at circle edge

### Phase 3: Curved Arc Rendering (2-3 days)
- [ ] Implement _calculate_curve_control_points method
- [ ] Implement _render_curved_path method
- [ ] Update tangent calculation for curved arcs
- [ ] Test curve rendering
- [ ] Fix boundary point calculation for curves

### Phase 4: Properties Dialog (1-2 days)
- [ ] Add radio buttons to arc_prop_dialog.ui
- [ ] Update _populate_fields in dialog loader
- [ ] Update _apply_changes in dialog loader
- [ ] Test dialog with all arc types

### Phase 5: Opposite Arc Detection (1 day)
- [ ] Implement _detect_opposite_arcs method
- [ ] Add dialog prompt for user confirmation
- [ ] Wire up to arc creation event
- [ ] Test with various scenarios

### Phase 6: Simulation Integration (1-2 days)
- [ ] Update transition enablement logic
- [ ] Implement inhibitor arc semantics
- [ ] Test with simple Petri nets
- [ ] Test mixed normal/inhibitor arcs

### Phase 7: Testing & Documentation (2-3 days)
- [ ] Write unit tests (arc_types, rendering, simulation)
- [ ] Manual testing all 4 arc types
- [ ] Create example Petri nets showcasing arc types
- [ ] Update user documentation
- [ ] Update API documentation

**Total Estimated Time: 10-15 days**

## Design Decisions & Rationale

### 1. Why 4 Arc Types Instead of Independent Flags?

**Alternative Considered:**
```python
arc.is_inhibitor = True/False
arc.is_curved = True/False
```

**Why Rejected:**
- Implicit combinations (2^2 = 4 states anyway)
- Less clear in UI (two separate checkboxes)
- More complex serialization logic
- Harder to validate state consistency

**Chosen Approach:**
```python
arc.arc_type = 'normal' | 'curved_opposite' | 'inhibitor' | 'curved_inhibitor'
```

**Benefits:**
- Explicit enumeration of valid states
- Single UI control (radio buttons)
- Clear semantics
- Easy to extend (add new types in future)

### 2. Automatic vs Manual Curve Control

**Automatic (CHOSEN):**
- System calculates control points based on geometry
- User gets "opposite arc" mode that just works
- Simpler UX

**Manual:**
- User drags control points to shape curve
- More flexible but complex UI
- Overkill for most use cases

**Future Enhancement:** Add "Advanced" button in properties dialog for manual control point editing

### 3. Inhibitor Arrowhead Style

**Options Considered:**
1. Hollow circle (CHOSEN)
2. Filled circle with different color
3. Bar/line perpendicular to arc
4. Triangle with different style

**Rationale for Hollow Circle:**
- Standard notation in Petri net literature
- Visually distinct from normal arrowhead
- Easy to implement with Cairo arc+stroke
- Maintains consistency with colored arcs

### 4. Curve Offset Calculation

**20% of line length perpendicular to midpoint**

**Why:**
- Proportional to distance (looks good at any scale)
- Perpendicular ensures symmetric opposite arcs
- 20% provides visible curve without excessive bend
- Midpoint offset is simplest bezier approach

**Alternatives Considered:**
- Fixed pixel offset: Doesn't scale well
- 30%+ offset: Too exaggerated for typical diagrams
- Multiple control points: Unnecessary complexity

## Open Questions & Future Enhancements

### Open Questions for User:
1. **Inhibitor Circle Size:** Use same 15px as arrow size, or different (e.g., 12px)?
2. **Opposite Arc Prompt:** Always show dialog, or add "Don't ask again" preference?
3. **Curve Direction:** Always counterclockwise, or alternate for multiple opposite arcs?
4. **Arc Type Labels:** Use "Inhibitor" or "Test/Reset" (Petri net terminology)?

### Future Enhancements:
1. **Read Arcs:** Third arc type for read-only access (doesn't consume tokens)
2. **Multiple Curves:** Smart routing for >2 arcs between same nodes
3. **Manual Control Points:** Advanced curve editing mode
4. **Arc Animations:** Animate token flow along curved paths during simulation
5. **Arc Styles:** Dashed lines, different arrow styles
6. **Capacity Arcs:** Arcs with bidirectional constraints

## References

- **Petri Net Notation:** ISO/IEC 15909 (High-level Petri Nets)
- **Cairo Graphics:** https://www.cairographics.org/manual/
- **Bezier Curves:** https://pomax.github.io/bezierinfo/
- **GTK+ Radio Buttons:** https://docs.gtk.org/gtk3/class.RadioButton.html

---

**Document Version:** 1.0  
**Created:** 2025-01-XX  
**Last Updated:** 2025-01-XX  
**Author:** GitHub Copilot  
**Status:** DRAFT - Awaiting User Feedback
