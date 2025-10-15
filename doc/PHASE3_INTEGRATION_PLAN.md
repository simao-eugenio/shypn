# Phase 3: Integration & Facade Implementation Plan

**Date:** October 14, 2025  
**Status:** 🚀 IN PROGRESS  
**Branch:** feature/property-dialogs-and-simulation-palette

## Objective

Wire up all extracted modules (ViewportController, DocumentController, CoordinateTransform, ArcGeometryService, GridRenderer) with the existing ModelCanvasManager while maintaining **100% backward compatibility**.

## Strategy: Facade Pattern

Use the **Facade pattern** to maintain the existing ModelCanvasManager API while delegating to the extracted modules internally. This ensures:
- ✅ Zero breaking changes for existing code
- ✅ Gradual migration path
- ✅ All tests continue to pass
- ✅ New code uses clean extracted modules

## Implementation Approach

### Phase 3A: Refactor ModelCanvasManager to Use Extracted Modules

**Goal:** Replace internal implementations with delegation to extracted modules.

**Steps:**
1. Import extracted modules
2. Create controller instances in `__init__`
3. Replace method implementations with delegation
4. Maintain exact same public API
5. Keep all existing properties as proxies

**Benefits:**
- Immediate code quality improvement
- Easier testing (can test controllers independently)
- Reduced duplication
- Clear separation of concerns

### Phase 3B: Update Existing Code (If Needed)

**Goal:** Update any code that directly instantiates or uses ModelCanvasManager.

**Areas to Check:**
- UI loaders (canvas_loader.py, etc.)
- Main application initialization
- File persistence code
- Test files

**Strategy:**
- Check if any code breaks
- Make minimal changes only where needed
- Preserve existing behavior

## Detailed Implementation Plan

### Step 1: Refactor ModelCanvasManager Initialization

**Current:**
```python
def __init__(self, canvas_width=2000, canvas_height=2000, filename="default"):
    # Many individual properties
    self.zoom = 1.0
    self.pan_x = 0.0
    self.pan_y = 0.0
    self.places = []
    self.transitions = []
    # etc...
```

**Refactored:**
```python
def __init__(self, canvas_width=2000, canvas_height=2000, filename="default"):
    # Create controller instances
    self.viewport = ViewportController(filename=filename)
    self.document = DocumentController(filename=filename)
    
    # Keep existing properties as proxies for backward compatibility
    # (delegate to controllers)
    
    # Keep managers
    self.selection_manager = SelectionManager()
    # etc...
```

### Step 2: Add Property Proxies

For backward compatibility, expose controller state as properties:

```python
# Viewport properties (delegate to ViewportController)
@property
def zoom(self):
    return self.viewport.zoom

@zoom.setter
def zoom(self, value):
    self.viewport.zoom = value

@property
def pan_x(self):
    return self.viewport.pan_x

@pan_x.setter
def pan_x(self, value):
    self.viewport.pan_x = value

# Document properties (delegate to DocumentController)
@property
def places(self):
    return self.document.places

@property
def transitions(self):
    return self.document.transitions

@property
def arcs(self):
    return self.document.arcs
```

### Step 3: Delegate Method Calls

Replace implementations with simple delegation:

```python
# Viewport methods
def zoom_in(self, center_x=None, center_y=None):
    """Delegate to ViewportController."""
    self.viewport.zoom_in(center_x, center_y)
    self.mark_dirty()

def zoom_out(self, center_x=None, center_y=None):
    """Delegate to ViewportController."""
    self.viewport.zoom_out(center_x, center_y)
    self.mark_dirty()

def pan(self, dx, dy):
    """Delegate to ViewportController."""
    self.viewport.pan(dx, dy)
    self.mark_dirty()

# Document methods
def add_place(self, x, y, **kwargs):
    """Delegate to DocumentController."""
    place = self.document.add_place(x, y, **kwargs)
    self.mark_dirty()
    return place

def remove_place(self, place):
    """Delegate to DocumentController."""
    self.document.remove_place(place)
    self.mark_dirty()
```

### Step 4: Use Extracted Services

Replace inline implementations with service calls:

```python
# Coordinate transformations
def screen_to_world(self, screen_x, screen_y):
    """Use CoordinateTransform service."""
    from shypn.core.services import screen_to_world
    return screen_to_world(screen_x, screen_y, 
                          self.viewport.zoom, 
                          self.viewport.pan_x, 
                          self.viewport.pan_y)

def world_to_screen(self, world_x, world_y):
    """Use CoordinateTransform service."""
    from shypn.core.services import world_to_screen
    return world_to_screen(world_x, world_y,
                          self.viewport.zoom,
                          self.viewport.pan_x,
                          self.viewport.pan_y)

# Grid rendering
def draw_grid(self, cr):
    """Use GridRenderer service."""
    from shypn.rendering import draw_grid, get_adaptive_grid_spacing
    from shypn.core.services import mm_to_pixels
    
    # Get adaptive spacing
    base_spacing_px = mm_to_pixels(1.0, self.screen_dpi)
    spacing = get_adaptive_grid_spacing(self.viewport.zoom, base_spacing_px)
    
    # Get visible bounds
    min_x, min_y = self.screen_to_world(0, 0)
    max_x, max_y = self.screen_to_world(self.viewport.viewport_width, 
                                        self.viewport.viewport_height)
    
    # Draw grid
    draw_grid(cr, self.grid_style, spacing, self.viewport.zoom,
             min_x, min_y, max_x, max_y)

# Arc geometry
def detect_parallel_arcs(self, arc):
    """Use ArcGeometryService."""
    from shypn.core.services import detect_parallel_arcs
    return detect_parallel_arcs(arc, self.document.arcs)

def calculate_arc_offset(self, arc, parallels):
    """Use ArcGeometryService."""
    from shypn.core.services import calculate_arc_offset
    return calculate_arc_offset(arc, parallels)
```

## Migration Checklist

### Phase 3A Tasks

- [ ] Import extracted modules at top of ModelCanvasManager
- [ ] Create controller instances in `__init__`
- [ ] Add property proxies for backward compatibility
- [ ] Delegate viewport methods to ViewportController
- [ ] Delegate document methods to DocumentController
- [ ] Replace coordinate transform implementations with service calls
- [ ] Replace grid rendering implementation with service calls
- [ ] Replace arc geometry implementations with service calls
- [ ] Update redraw flag management
- [ ] Test that existing tests still pass

### Phase 3B Tasks (If Needed)

- [ ] Check canvas_loader.py for compatibility
- [ ] Check main application initialization
- [ ] Check file persistence code
- [ ] Update any broken tests
- [ ] Verify UI still works correctly

## Testing Strategy

### Unit Tests
- All existing tests should continue to pass
- Controllers can be tested independently
- Services already have comprehensive tests

### Integration Tests
- Test ModelCanvasManager with new implementation
- Verify all public methods work correctly
- Test file save/load workflows
- Test UI interactions

### Regression Tests
- Run full application
- Test all features manually
- Verify no visual regressions
- Check performance

## Success Criteria

- [ ] All existing tests pass (no failures)
- [ ] ModelCanvasManager code reduced by ~50%
- [ ] All delegation working correctly
- [ ] No breaking changes to public API
- [ ] UI works correctly
- [ ] File save/load works correctly
- [ ] Performance maintained or improved

## Benefits After Integration

1. **Cleaner Code**
   - ModelCanvasManager becomes thin facade
   - Clear separation of concerns
   - Single responsibility maintained

2. **Easier Testing**
   - Test controllers independently
   - Test services with pure functions
   - Less mocking needed

3. **Better Maintainability**
   - Changes isolated to specific modules
   - Easy to understand and modify
   - Clear dependencies

4. **Reusability**
   - Controllers can be used independently
   - Services are pure functions
   - No tight coupling

## Timeline

- **Step 1-2 (Refactor + Proxies):** 2-3 hours
- **Step 3-4 (Delegate + Services):** 2-3 hours
- **Testing:** 1-2 hours
- **Bug fixes:** 1-2 hours

**Total Estimated:** 6-10 hours (1-2 days)

## Risk Mitigation

### Risks

1. **Breaking existing code**
   - Mitigation: Maintain exact API, use property proxies
   
2. **Tests failing**
   - Mitigation: Run tests frequently, fix immediately
   
3. **Performance degradation**
   - Mitigation: Benchmark before/after
   
4. **Hidden dependencies**
   - Mitigation: Thorough testing, check all code paths

### Rollback Plan

If integration fails:
1. Keep extracted modules (they're independent)
2. Revert ModelCanvasManager changes
3. Fix issues incrementally
4. Try again with smaller steps

## Next Steps After Phase 3

1. **Phase 4: Additional Extractions**
   - Extract remaining god classes
   - Apply same pattern to other areas
   
2. **Phase 5: Event System Integration**
   - Wire up event system from Phase 1
   - Add observer pattern throughout
   
3. **Phase 6: UI Refactoring**
   - Apply BasePanel to all UI panels
   - Use PanelLoader consistently

## Conclusion

Phase 3 will complete the refactoring by integrating all extracted modules back into the existing codebase. The facade pattern ensures backward compatibility while gaining all the benefits of clean architecture.

**Ready to begin implementation!**

---

**Document Created:** October 14, 2025  
**Author:** GitHub Copilot  
**Status:** Ready for Implementation
