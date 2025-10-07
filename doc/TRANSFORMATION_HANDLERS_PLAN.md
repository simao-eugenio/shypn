# Transformation Handlers Architecture Plan

## Overview
Design and implement an OOP-based transformation handler system for editing Petri Net objects through double-click interaction. This system will provide interactive handles for resize, rotate, expand/shrink operations on selected objects.

**Key Principle**: Code goes under `src/shypn/edit/`, NOT in loader files.

---

## 1. Current State Analysis

### 1.1 Existing Infrastructure
Located in `src/shypn/edit/`:
- ✅ `selection_manager.py` - Manages selection state and edit mode
- ✅ `object_editing_transforms.py` - Renders selection highlights and handles
- ✅ `drag_controller.py` - Handles object dragging
- ✅ `rectangle_selection.py` - Rectangle selection tool
- ✅ `transient_arc.py` - Temporary arc during creation

### 1.2 Current Edit Mode Flow
```
Single Click → Normal Selection (blue highlight only)
Double Click → Edit Mode (blue highlight + bounding box + handles)
```

Currently in `selection_manager.py`:
```python
def enter_edit_mode(self, obj, manager=None):
    """Switch to edit mode for transformation operations."""
    self.selection_mode = SelectionMode.EDIT
    self.edit_target = obj
    # ... triggers redraw to show handles
```

### 1.3 Current Handle Rendering
In `object_editing_transforms.py`:
- Renders 8 corner/edge handles (N, NE, E, SE, S, SW, W, NW)
- Handles are visual only - no interaction yet
- Size: 8x8 pixels, white fill, blue stroke

### 1.4 What's Missing
- ❌ Handle interaction (click detection, drag handling)
- ❌ Transformation logic (resize, rotate, scale)
- ❌ Object-specific transformation constraints
- ❌ Undo/redo for transformations
- ❌ Visual feedback during transformation

---

## 2. Architecture Design

### 2.1 Object-Oriented Structure

```
src/shypn/edit/
├── transformation/                    # NEW DIRECTORY
│   ├── __init__.py
│   ├── transform_handler.py          # Base handler (abstract)
│   ├── resize_handler.py             # Resize operations
│   ├── rotate_handler.py             # Rotate operations (future)
│   ├── scale_handler.py              # Uniform scaling (future)
│   └── handle_detector.py            # Handle hit detection
│
├── selection_manager.py               # EXISTING (minor changes)
├── object_editing_transforms.py       # EXISTING (refactor)
├── drag_controller.py                 # EXISTING (minor integration)
└── ...existing files...
```

### 2.2 Class Hierarchy

```
TransformHandler (ABC)
    │
    ├── ResizeHandler
    │   ├── PlaceResizeHandler
    │   └── TransitionResizeHandler
    │
    ├── RotateHandler (future)
    │   └── TransitionRotateHandler
    │
    └── ScaleHandler (future)
        ├── UniformScaleHandler
        └── ProportionalScaleHandler
```

---

## 3. Detailed Component Design

### 3.1 TransformHandler (Base Class)
**File**: `src/shypn/edit/transformation/transform_handler.py`

**Responsibilities**:
- Define abstract interface for all transformations
- Handle common transformation state (active, dragging)
- Coordinate with selection manager
- Manage undo/redo integration

**Key Methods**:
```python
class TransformHandler(ABC):
    """Abstract base class for object transformation handlers."""
    
    def __init__(self, selection_manager):
        self.selection_manager = selection_manager
        self.is_active = False
        self.drag_start_pos = None
        self.original_state = None
    
    @abstractmethod
    def can_transform(self, obj) -> bool:
        """Check if this handler can transform the given object."""
        pass
    
    @abstractmethod
    def start_transform(self, obj, handle: str, start_x: float, start_y: float):
        """Begin transformation."""
        pass
    
    @abstractmethod
    def update_transform(self, current_x: float, current_y: float):
        """Update transformation during drag."""
        pass
    
    @abstractmethod
    def end_transform(self) -> bool:
        """Complete transformation. Returns True if successful."""
        pass
    
    @abstractmethod
    def cancel_transform(self):
        """Cancel transformation and restore original state."""
        pass
    
    @abstractmethod
    def get_preview_geometry(self) -> dict:
        """Get geometry for preview rendering during transform."""
        pass
```

### 3.2 HandleDetector
**File**: `src/shypn/edit/transformation/handle_detector.py`

**Responsibilities**:
- Detect which handle (if any) is under cursor
- Provide handle positions for rendering
- Support different object types (Place, Transition, Arc)

**Key Methods**:
```python
class HandleDetector:
    """Detects handle clicks and provides handle positions."""
    
    HANDLE_SIZE = 8.0  # pixels
    HANDLE_NAMES = ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw']
    
    def __init__(self):
        self.handle_positions = {}  # Cache of handle positions
    
    def get_handle_positions(self, obj, zoom: float) -> dict:
        """Calculate handle positions for an object.
        
        Returns:
            dict: {handle_name: (screen_x, screen_y), ...}
        """
        pass
    
    def detect_handle_at_position(self, obj, screen_x: float, screen_y: float, 
                                   zoom: float) -> Optional[str]:
        """Detect which handle (if any) is at the given screen position.
        
        Returns:
            Handle name ('n', 'ne', etc.) or None if no handle hit
        """
        pass
    
    def get_cursor_for_handle(self, handle: str) -> str:
        """Get appropriate cursor name for a handle.
        
        Returns:
            GTK cursor name (e.g., 'n-resize', 'ne-resize', etc.)
        """
        cursor_map = {
            'n': 'n-resize',
            'ne': 'ne-resize',
            'e': 'e-resize',
            'se': 'se-resize',
            's': 's-resize',
            'sw': 'sw-resize',
            'w': 'w-resize',
            'nw': 'nw-resize'
        }
        return cursor_map.get(handle, 'default')
```

### 3.3 ResizeHandler
**File**: `src/shypn/edit/transformation/resize_handler.py`

**Responsibilities**:
- Handle resize operations for Places and Transitions
- Maintain object constraints (minimum size, aspect ratio)
- Support different resize modes (corner vs edge)
- Provide visual feedback during resize

**Key Features**:
```python
class ResizeHandler(TransformHandler):
    """Handles resize operations for Petri Net objects."""
    
    def __init__(self, selection_manager):
        super().__init__(selection_manager)
        self.active_handle = None  # 'n', 'ne', 'e', etc.
        self.object_being_resized = None
        self.original_geometry = {}  # Store original dimensions
        
    def can_transform(self, obj) -> bool:
        """Resize supported for Places and Transitions only."""
        from shypn.netobjs import Place, Transition
        return isinstance(obj, (Place, Transition))
    
    def start_transform(self, obj, handle: str, start_x: float, start_y: float):
        """Start resize operation."""
        self.is_active = True
        self.active_handle = handle
        self.object_being_resized = obj
        self.drag_start_pos = (start_x, start_y)
        
        # Store original geometry for undo
        if isinstance(obj, Place):
            self.original_geometry = {
                'x': obj.x,
                'y': obj.y,
                'radius': obj.radius
            }
        elif isinstance(obj, Transition):
            self.original_geometry = {
                'x': obj.x,
                'y': obj.y,
                'width': obj.width,
                'height': obj.height,
                'horizontal': obj.horizontal
            }
    
    def update_transform(self, current_x: float, current_y: float):
        """Update object size during drag."""
        if not self.is_active:
            return
        
        obj = self.object_being_resized
        handle = self.active_handle
        start_x, start_y = self.drag_start_pos
        
        # Calculate delta
        dx = current_x - start_x
        dy = current_y - start_y
        
        # Apply resize based on handle and object type
        if isinstance(obj, Place):
            self._resize_place(obj, handle, dx, dy)
        elif isinstance(obj, Transition):
            self._resize_transition(obj, handle, dx, dy)
    
    def _resize_place(self, place, handle: str, dx: float, dy: float):
        """Resize a Place (change radius)."""
        # All handles resize uniformly (change radius)
        # Use larger delta (dx or dy) for resize
        delta = max(abs(dx), abs(dy))
        if dx < 0 or dy < 0:
            delta = -delta
        
        new_radius = self.original_geometry['radius'] + delta
        
        # Apply constraints
        MIN_RADIUS = 10.0
        MAX_RADIUS = 100.0
        place.radius = max(MIN_RADIUS, min(MAX_RADIUS, new_radius))
    
    def _resize_transition(self, transition, handle: str, dx: float, dy: float):
        """Resize a Transition (change width/height)."""
        orig = self.original_geometry
        
        # Different resize behavior based on handle
        if handle == 'e' or handle == 'w':
            # Horizontal resize
            new_width = orig['width'] + (dx if handle == 'e' else -dx)
            transition.width = max(20.0, min(200.0, new_width))
            
        elif handle == 'n' or handle == 's':
            # Vertical resize
            new_height = orig['height'] + (dy if handle == 's' else -dy)
            transition.height = max(10.0, min(100.0, new_height))
            
        elif handle in ['ne', 'se', 'sw', 'nw']:
            # Corner resize - both dimensions
            if handle == 'ne':
                transition.width = max(20.0, orig['width'] + dx)
                transition.height = max(10.0, orig['height'] - dy)
            elif handle == 'se':
                transition.width = max(20.0, orig['width'] + dx)
                transition.height = max(10.0, orig['height'] + dy)
            elif handle == 'sw':
                transition.width = max(20.0, orig['width'] - dx)
                transition.height = max(10.0, orig['height'] + dy)
            elif handle == 'nw':
                transition.width = max(20.0, orig['width'] - dx)
                transition.height = max(10.0, orig['height'] - dy)
```

### 3.4 Integration with ObjectEditingTransforms
**File**: `src/shypn/edit/object_editing_transforms.py` (REFACTOR)

**Changes**:
1. Add handle detection capability
2. Separate rendering from interaction logic
3. Integrate with HandleDetector

```python
class ObjectEditingTransforms:
    """Manages visual feedback and transformation for selected objects."""
    
    def __init__(self, selection_manager):
        self.selection_manager = selection_manager
        self.handle_detector = None  # Lazy init
        self.active_handler = None   # Current transformation handler
    
    def _init_handle_detector(self):
        """Lazy initialize handle detector."""
        if self.handle_detector is None:
            from shypn.edit.transformation.handle_detector import HandleDetector
            self.handle_detector = HandleDetector()
    
    def check_handle_at_position(self, obj, screen_x: float, screen_y: float, 
                                  zoom: float) -> Optional[str]:
        """Check if a handle is at the given position.
        
        Returns:
            Handle name or None
        """
        if not self.selection_manager.is_edit_mode():
            return None
        
        self._init_handle_detector()
        return self.handle_detector.detect_handle_at_position(
            obj, screen_x, screen_y, zoom
        )
    
    def start_transformation(self, obj, handle: str, screen_x: float, screen_y: float):
        """Start a transformation operation.
        
        Creates appropriate handler based on handle type.
        """
        from shypn.edit.transformation.resize_handler import ResizeHandler
        
        # For now, all handles trigger resize
        # Future: Different handlers for rotate, scale, etc.
        self.active_handler = ResizeHandler(self.selection_manager)
        
        if self.active_handler.can_transform(obj):
            self.active_handler.start_transform(obj, handle, screen_x, screen_y)
            return True
        return False
```

---

## 4. Integration with Canvas Loader

### 4.1 Mouse Event Handling
**Location**: `src/shypn/helpers/model_canvas_loader.py` (MINIMAL CHANGES)

**Current flow**:
```python
def _on_button_press(self, widget, event, manager):
    # ... existing logic ...
    if is_double_click:
        if clicked_obj.selected:
            manager.selection_manager.enter_edit_mode(clicked_obj, manager=manager)
```

**New flow** (add handle detection):
```python
def _on_button_press(self, widget, event, manager):
    # ... existing logic ...
    
    # Check if clicking on a transform handle in edit mode
    if manager.selection_manager.is_edit_mode():
        edit_target = manager.selection_manager.get_edit_target()
        transforms = getattr(manager, 'editing_transforms', None)
        
        if transforms and edit_target:
            handle = transforms.check_handle_at_position(
                edit_target, event.x, event.y, manager.zoom
            )
            
            if handle:
                # Start transformation instead of normal drag
                world_x, world_y = manager.screen_to_world(event.x, event.y)
                transforms.start_transformation(
                    edit_target, handle, world_x, world_y
                )
                state['is_transforming'] = True
                return
    
    # ... rest of existing logic (double-click, drag, etc.) ...
```

**Add motion handler for transformations**:
```python
def _on_motion_notify(self, widget, event, manager):
    # ... existing drag logic ...
    
    # Handle transformation drag
    if state.get('is_transforming'):
        transforms = getattr(manager, 'editing_transforms', None)
        if transforms and transforms.active_handler:
            world_x, world_y = manager.screen_to_world(event.x, event.y)
            transforms.active_handler.update_transform(world_x, world_y)
            widget.queue_draw()
        return
    
    # ... rest of existing motion logic ...
```

### 4.2 Canvas Manager Integration
**Location**: `src/shypn/data/model_canvas_manager.py` (MINIMAL CHANGES)

Add transformation system initialization:
```python
class ModelCanvasManager:
    def __init__(self):
        # ... existing init ...
        self.selection_manager = SelectionManager()
        self.editing_transforms = ObjectEditingTransforms(self.selection_manager)
```

---

## 5. Implementation Phases

### Phase 1: Foundation (Week 1)
**Goal**: Set up base infrastructure

**Tasks**:
1. Create `src/shypn/edit/transformation/` directory
2. Implement `TransformHandler` base class
3. Implement `HandleDetector` with hit testing
4. Add unit tests for handle detection

**Deliverables**:
- `transform_handler.py` with abstract interface
- `handle_detector.py` with position calculations
- Test suite for handle detection
- Documentation updates

### Phase 2: Resize Handler (Week 2)
**Goal**: Implement resize functionality

**Tasks**:
1. Implement `ResizeHandler` base class
2. Implement Place resize (uniform scaling)
3. Implement Transition resize (width/height)
4. Add constraints (min/max size)
5. Add visual feedback (preview during resize)

**Deliverables**:
- `resize_handler.py` fully functional
- Resize works for Places and Transitions
- Visual preview during resize
- Undo/redo support

### Phase 3: Integration (Week 3)
**Goal**: Wire up to canvas events

**Tasks**:
1. Refactor `ObjectEditingTransforms` to use HandleDetector
2. Add handle click detection to button-press event
3. Add transformation drag to motion-notify event
4. Add cursor feedback (change cursor on handle hover)
5. Test with real models

**Deliverables**:
- Full interaction working
- Cursor changes on handle hover
- Smooth resize operation
- No regression in existing features

### Phase 4: Polish & Optimization (Week 4)
**Goal**: Refine and optimize

**Tasks**:
1. Add keyboard modifiers (Shift for constrained resize, Ctrl for center resize)
2. Optimize rendering (dirty rectangles)
3. Add visual feedback improvements
4. Performance testing
5. User documentation

**Deliverables**:
- Polished user experience
- Comprehensive documentation
- Performance benchmarks
- User guide with examples

### Phase 5: Future Enhancements (Future)
**Goal**: Add advanced transformations

**Tasks**:
1. Implement `RotateHandler` for transitions
2. Implement `ScaleHandler` for uniform scaling
3. Add alignment guides (snap to other objects)
4. Add smart guides (show distances)
5. Multi-object transformation

---

## 6. Technical Specifications

### 6.1 Coordinate Systems
- **Screen Coordinates**: Mouse events, handle positions
- **World Coordinates**: Object positions, transformations
- **Conversion**: Use `manager.screen_to_world()` and `manager.world_to_screen()`

### 6.2 Handle Layout
```
      nw ----------- n ----------- ne
      |                             |
      |                             |
      w            obj              e
      |                             |
      |                             |
      sw ----------- s ----------- se
```

### 6.3 Resize Constraints

**Places**:
- Minimum radius: 10.0 units
- Maximum radius: 100.0 units
- All handles resize uniformly (no stretching)

**Transitions**:
- Minimum width: 20.0 units
- Maximum width: 200.0 units
- Minimum height: 10.0 units
- Maximum height: 100.0 units
- Corner handles: resize both dimensions
- Edge handles: resize one dimension

### 6.4 Visual Feedback
- **Handle Hover**: Highlight handle on mouseover
- **Resize Preview**: Show dotted outline during resize
- **Cursor Changes**: Resize cursors (n-resize, ne-resize, etc.)
- **Snap Indicators**: Show snap lines when close to grid/objects

### 6.5 Undo/Redo
Each transformation creates an undo operation:
```python
class ResizeOperation:
    def __init__(self, obj, old_geometry, new_geometry):
        self.obj = obj
        self.old_geometry = old_geometry
        self.new_geometry = new_geometry
    
    def undo(self):
        # Restore old geometry
        pass
    
    def redo(self):
        # Apply new geometry
        pass
```

---

## 7. Testing Strategy

### 7.1 Unit Tests
- Handle detection accuracy
- Resize calculations (min/max constraints)
- Coordinate conversions
- Transform state management

### 7.2 Integration Tests
- Full resize workflow (start → drag → end)
- Multi-object selection behavior
- Undo/redo correctness
- Canvas event handling

### 7.3 Manual Testing
- Resize places to various sizes
- Resize transitions in both orientations
- Test with different zoom levels
- Test with grid snapping enabled
- Test keyboard modifiers

---

## 8. Code Organization

### 8.1 File Structure
```
src/shypn/edit/
├── transformation/
│   ├── __init__.py              # Export main classes
│   ├── transform_handler.py     # Base class (200 lines)
│   ├── handle_detector.py       # Handle detection (150 lines)
│   ├── resize_handler.py        # Resize logic (300 lines)
│   ├── rotate_handler.py        # Future: Rotate logic
│   └── scale_handler.py         # Future: Scale logic
│
├── selection_manager.py         # Minor updates (50 lines added)
├── object_editing_transforms.py # Refactor (100 lines changed)
└── drag_controller.py           # Minor integration (20 lines)
```

### 8.2 Import Pattern
```python
# In loader (minimal):
from shypn.edit.selection_manager import SelectionManager
from shypn.edit.object_editing_transforms import ObjectEditingTransforms

# In transformation modules:
from shypn.edit.transformation.transform_handler import TransformHandler
from shypn.edit.transformation.handle_detector import HandleDetector
from shypn.edit.transformation.resize_handler import ResizeHandler
```

---

## 9. Documentation Requirements

### 9.1 Code Documentation
- All classes with docstrings (Google style)
- All public methods documented
- Complex algorithms explained with comments
- Type hints for all method signatures

### 9.2 User Documentation
- How to enter edit mode (double-click)
- How to resize objects (drag handles)
- Keyboard modifiers explained
- Troubleshooting common issues

### 9.3 Architecture Documentation
- Update `src/shypn/edit/README.md`
- Create transformation system diagram
- Document extension points for new handlers

---

## 10. Success Criteria

### 10.1 Functional Requirements
- ✅ Double-click enters edit mode
- ✅ 8 handles appear on selected object
- ✅ Clicking handle starts resize
- ✅ Dragging handle updates size
- ✅ Releasing mouse completes resize
- ✅ ESC cancels resize
- ✅ Undo/redo works correctly

### 10.2 Non-Functional Requirements
- ✅ Smooth 60fps during resize
- ✅ Handles always visible at any zoom level
- ✅ No flicker or visual artifacts
- ✅ Responsive cursor feedback (<50ms)
- ✅ Code coverage >80%

### 10.3 User Experience
- ✅ Intuitive handle placement
- ✅ Clear visual feedback
- ✅ Predictable resize behavior
- ✅ No accidental transformations
- ✅ Easy to discover and use

---

## 11. Risk Assessment

### 11.1 Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Performance issues with handle rendering | Medium | High | Use dirty rectangles, optimize rendering |
| Coordinate conversion bugs | Low | Medium | Extensive unit tests, visual validation |
| Undo/redo complexity | Medium | Medium | Start simple, iterate |
| GTK cursor changes not working | Low | Low | Fallback to default cursor |

### 11.2 Integration Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking existing drag functionality | Medium | High | Keep drag and transform separate |
| Conflicts with arc creation | Low | Medium | Clear mode separation |
| Selection manager complexity | Medium | Medium | Keep interfaces simple |

---

## 12. Future Enhancements

### 12.1 Advanced Transformations
- **Rotate Handler**: Rotate transitions by angle
- **Scale Handler**: Uniform scaling for multi-select
- **Skew Handler**: Advanced shape manipulation

### 12.2 Smart Features
- **Alignment Guides**: Show when aligned with other objects
- **Distance Guides**: Show spacing between objects
- **Snap to Objects**: Magnetic attraction to nearby objects
- **Smart Resize**: Maintain aspect ratio, snap to standard sizes

### 12.3 Multi-Object Operations
- **Group Resize**: Resize multiple selected objects
- **Proportional Resize**: Maintain relative sizes
- **Distributed Resize**: Adjust spacing while resizing

---

## 13. Summary

This plan provides a comprehensive roadmap for implementing transformation handlers in an OOP architecture under `src/shypn/edit/`. The design:

1. **Respects existing structure**: Builds on current selection and editing systems
2. **Follows OOP principles**: Clear class hierarchy with single responsibility
3. **Minimizes loader changes**: Core logic in dedicated modules, not in loader
4. **Extensible**: Easy to add new transformation types (rotate, scale, etc.)
5. **Testable**: Clear interfaces enable comprehensive unit testing
6. **User-friendly**: Intuitive double-click to edit, drag handles to transform

The phased implementation allows for incremental development with early feedback, while the clear architecture ensures maintainability and extensibility for future enhancements.
