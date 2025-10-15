# ModelCanvasManager Analysis & Extraction Plan

**Date**: October 14, 2025  
**File**: `src/shypn/data/model_canvas_manager.py`  
**Current Size**: 1,266 lines  
**Target**: Extract into controllers, services, and renderer

---

## Current Responsibilities (God Class Anti-Pattern)

The ModelCanvasManager currently handles **EVERYTHING**:

### 1. Document Management (~100 lines)
- Petri net object collections (places, transitions, arcs)
- Object creation/deletion (add_place, add_transition, add_arc)
- Object ID counters
- Document metadata (filename, modified flag, timestamps)
- Document state serialization

### 2. Viewport Management (~150 lines)
- Zoom operations (zoom_in, zoom_out, zoom_by_factor, set_zoom)
- Pan operations (pan, pan_to, pan_relative)
- Viewport size tracking
- Coordinate transformations (screen_to_world, world_to_screen)
- DPI handling

### 3. Selection Management (~50 lines)
- SelectionManager integration
- clear_all_selections
- find_object_at_position

### 4. Tool Management (~50 lines)
- Current tool tracking
- set_tool, get_tool, clear_tool
- is_tool_active

### 5. Arc Geometry (~200 lines)
- Parallel arc detection
- Arc offset calculation
- Auto-convert parallel arcs to curved
- Arc replacement logic

### 6. Grid Rendering (~200 lines)
- Grid configuration (spacing, subdivision, styles)
- DPI-aware grid calculations
- draw_grid method with adaptive spacing
- Multiple grid styles (line, dot, cross)

### 7. State Management (~100 lines)
- Modified flag tracking
- Document state serialization
- Validation
- mark_dirty, mark_clean

### 8. Utility Methods (~100 lines)
- get_all_objects
- clear_all_objects
- get_info
- create_test_objects

---

## Extraction Strategy

### Target Architecture

```
Current: ModelCanvasManager (1,266 lines - god class)
↓
Extract into:
├── DocumentController (~200 lines)      # Object management
├── ViewportController (~150 lines)      # Zoom/pan operations
├── SelectionController (~100 lines)     # Selection logic
├── ArcGeometryService (~200 lines)      # Arc calculations
├── GridRenderer (~200 lines)            # Grid drawing
├── DocumentState (~100 lines)           # State management
└── CoordinateTransform (~50 lines)      # Screen ↔ world
```

**Total**: ~1,000 lines across 7 focused modules (vs 1,266 in one file)  
**Reduction**: 21% code reduction + clear separation

---

## Phase 2A: Extract Core Controllers

### Step 1: Create DocumentController

**Responsibility**: Manage Petri net objects (places, transitions, arcs)

**Methods to Extract**:
- `__init__` - Object collections, ID counters
- `add_place(x, y, **kwargs)` - Create place
- `add_transition(x, y, **kwargs)` - Create transition
- `add_arc(source, target, **kwargs)` - Create arc
- `remove_place(place)` - Delete place
- `remove_transition(transition)` - Delete transition
- `remove_arc(arc)` - Delete arc
- `get_all_objects()` - Get all objects
- `clear_all_objects()` - Clear document
- `ensure_arc_references()` - Fix references

**Dependencies**:
- Needs: ArcGeometryService (for parallel arc handling)
- Needs: Events (fire ObjectAdded, ObjectRemoved)
- Provides: Object collections to ViewportController

**Target File**: `src/shypn/core/controllers/document_controller.py`

---

### Step 2: Create ViewportController

**Responsibility**: Manage viewport transformations (zoom, pan, coordinates)

**Methods to Extract**:
- Zoom operations:
  - `zoom_in(center_x, center_y)`
  - `zoom_out(center_x, center_y)`
  - `zoom_by_factor(factor, center_x, center_y)`
  - `set_zoom(zoom_level, center_x, center_y)`
  - `zoom_at_point(factor, center_x, center_y)`
  
- Pan operations:
  - `pan(dx, dy)`
  - `pan_to(world_x, world_y)`
  - `pan_relative(dx, dy)`
  - `clamp_pan()`
  
- Coordinate transformations:
  - `screen_to_world(screen_x, screen_y)`
  - `world_to_screen(world_x, world_y)`
  
- Viewport management:
  - `set_viewport_size(width, height)`
  - `get_visible_bounds()`
  - `set_pointer_position(x, y)`

**State**:
- `zoom` - Current zoom level
- `pan_x`, `pan_y` - Pan offsets
- `viewport_width`, `viewport_height` - Viewport size
- `pointer_x`, `pointer_y` - Pointer position
- `screen_dpi` - DPI for calculations

**Dependencies**:
- Needs: Events (fire ZoomChanged, PanChanged)
- Independent: No dependencies on Document

**Target File**: `src/shypn/core/controllers/viewport_controller.py`

---

### Step 3: Create SelectionController

**Responsibility**: Manage object selection

**Methods to Extract**:
- `find_object_at_position(x, y)` - Hit testing
- `clear_all_selections()` - Clear selections
- Integration with SelectionManager

**State**:
- `selection_manager` - SelectionManager instance

**Dependencies**:
- Needs: DocumentController (to query objects)
- Needs: ViewportController (for coordinate transforms)
- Needs: Events (fire SelectionChanged)

**Target File**: `src/shypn/core/controllers/selection_controller.py`

---

### Step 4: Create ArcGeometryService

**Responsibility**: Arc geometry calculations (stateless)

**Methods to Extract**:
- `detect_parallel_arcs(arc)` - Find parallel arcs
- `calculate_arc_offset(arc, parallels)` - Calculate curve offset
- `_auto_convert_parallel_arcs_to_curved(new_arc)` - Auto-curve
- `replace_arc(old_arc, new_arc)` - Replace arc

**Dependencies**:
- Stateless: Pure geometric calculations
- No events needed (called by DocumentController)

**Target File**: `src/shypn/core/services/arc_geometry_service.py`

---

### Step 5: Create GridRenderer

**Responsibility**: Grid rendering (no state)

**Methods to Extract**:
- `get_grid_spacing()` - Calculate adaptive spacing
- `draw_grid(cr)` - Render grid
- `set_grid_style(style)` - Set grid style

**State**:
- `grid_style` - Current grid style
- Grid configuration constants

**Dependencies**:
- Needs: ViewportController (for zoom, visible bounds)
- Stateless rendering logic

**Target File**: `src/shypn/rendering/grid_renderer.py`

---

### Step 6: Create CoordinateTransform

**Responsibility**: Coordinate system utilities (stateless)

**Methods**:
- `screen_to_world(screen_x, screen_y, zoom, pan_x, pan_y)`
- `world_to_screen(world_x, world_y, zoom, pan_x, pan_y)`
- `get_mm_to_pixels(screen_dpi)`

**Dependencies**:
- Pure functions (no state)

**Target File**: `src/shypn/core/services/coordinate_transform.py`

---

### Step 7: Create DocumentState

**Responsibility**: Document metadata and state

**Methods to Extract**:
- `get_document_state()` - Serialize state
- `mark_modified()` - Set modified flag
- `set_filename(filename)` - Set filename
- `create_new_document(filename)` - Reset state
- `validate_initial_state()` - Validate

**State**:
- `filename` - Document filename
- `modified` - Modified flag
- `created_at`, `modified_at` - Timestamps

**Dependencies**:
- Needs: DocumentController (for object state)
- Needs: ViewportController (for viewport state)

**Target File**: `src/shypn/core/state/document_state.py`

---

## Migration Order

### Week 2: Foundation

1. **Day 1-2**: Create directory structure
   ```
   src/shypn/core/controllers/
   src/shypn/core/services/
   src/shypn/rendering/
   ```

2. **Day 3**: Extract CoordinateTransform (simplest, no dependencies)
   - Pure functions
   - Easy to test
   - Used by others

3. **Day 4**: Extract ArcGeometryService (stateless service)
   - No external dependencies
   - Used by DocumentController

4. **Day 5**: Extract GridRenderer (rendering logic)
   - Depends on ViewportController
   - But can work with interface

### Week 3: Core Controllers

5. **Day 1-2**: Extract ViewportController
   - Critical: Many dependencies on this
   - Add event firing
   - Test thoroughly

6. **Day 3-4**: Extract DocumentController
   - Uses ArcGeometryService
   - Fires document events
   - Integrates with ViewportController

7. **Day 5**: Extract SelectionController
   - Uses DocumentController
   - Uses ViewportController
   - Fires selection events

### Week 4: Integration & Cleanup

8. **Day 1**: Extract DocumentState
   - Coordinates other controllers
   - Serialization logic

9. **Day 2-3**: Create ModelCanvasFacade
   - Thin adapter wrapping controllers
   - Maintains old API temporarily
   - Allows gradual migration

10. **Day 4-5**: Update ModelCanvasLoader
    - Use new controllers
    - Wire events to observers
    - Test integration

---

## Testing Strategy

### Unit Tests (Each Controller)

**ViewportController**:
```python
def test_zoom_in_increases_zoom():
def test_zoom_centers_on_pointer():
def test_pan_moves_viewport():
def test_screen_to_world_transformation():
def test_clamp_pan_keeps_in_bounds():
def test_zoom_fires_event():
```

**DocumentController**:
```python
def test_add_place_creates_place():
def test_add_arc_connects_objects():
def test_remove_place_deletes_arcs():
def test_object_creation_fires_event():
def test_id_counters_increment():
```

**SelectionController**:
```python
def test_find_object_at_position():
def test_clear_selections():
def test_selection_fires_event():
```

### Integration Tests

```python
def test_zoom_and_selection_together():
def test_create_object_then_select():
def test_pan_then_add_object():
```

---

## API Compatibility

### Old API (ModelCanvasManager)
```python
manager = ModelCanvasManager()
manager.add_place(10, 20)
manager.zoom_in(center_x=100, center_y=100)
place = manager.find_object_at_position(10, 20)
```

### New API (Controllers)
```python
# Direct controller usage
doc_ctrl = DocumentController()
viewport_ctrl = ViewportController()
selection_ctrl = SelectionController(doc_ctrl, viewport_ctrl)

doc_ctrl.add_place(10, 20)
viewport_ctrl.zoom_in(center_x=100, center_y=100)
place = selection_ctrl.find_object_at_position(10, 20)
```

### Facade (Temporary Migration)
```python
# Maintains old API during migration
facade = ModelCanvasFacade(doc_ctrl, viewport_ctrl, selection_ctrl)
facade.add_place(10, 20)  # Delegates to doc_ctrl
facade.zoom_in(100, 100)  # Delegates to viewport_ctrl
```

---

## Benefits

### Before Refactoring ❌
- 1,266 lines in one file
- Mixed responsibilities
- Hard to test
- Tight coupling
- No events
- Global state

### After Refactoring ✅
- 7 focused modules (~150 lines each)
- Single responsibility
- Easy to test
- Loose coupling (via events)
- Observer pattern
- Clean separation

### Metrics

| Aspect | Before | After | Improvement |
|--------|--------|-------|-------------|
| Max file size | 1,266 | ~200 | 84% reduction |
| Responsibilities per class | 8+ | 1 | Clear SRP |
| Test coverage | ~10% | >90% | 9x increase |
| Coupling | Tight | Loose | Events |
| Maintainability | Low | High | Small classes |

---

## Next Steps

1. ✅ Complete this analysis
2. Create directory structure
3. Extract CoordinateTransform (Day 1)
4. Extract ArcGeometryService (Day 2)
5. Extract GridRenderer (Day 3)
6. Extract ViewportController (Day 4-5)
7. Extract DocumentController (Week 3)
8. Extract SelectionController
9. Create facade and integrate

---

**Document Status**: Complete  
**Next Action**: Create directory structure and begin extraction  
**Estimated Time**: 2-3 weeks for complete extraction
