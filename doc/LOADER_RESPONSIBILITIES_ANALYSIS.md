# Loader Responsibilities Analysis

**Date:** October 3, 2025  
**Purpose:** Analyze if loader modules are assuming roles that should belong to other modules

## Executive Summary

**CRITICAL FINDING:** `model_canvas_loader.py` has grown into a **1,372-line monolithic module** that violates the Single Responsibility Principle. It has assumed multiple roles beyond loading/preparing UI components.

### Key Issues:

1. **Business Logic in Loader** (Should be in Controllers/Handlers)
2. **Rendering Logic in Loader** (Should be in Renderer modules)
3. **Event Handling Logic** (Should be in separate Event Handler classes)
4. **Context Menu Creation** (Should be in UI builders)
5. **Dialog Management** (Should be in Dialog modules)

---

## Analysis by Module

### 1. ✅ `edit_tools_loader.py` (378 lines)

**Status: ACCEPTABLE** - Mostly within loader scope

#### Current Responsibilities:
- ✅ Load UI file (`edit_tools_palette.ui`)
- ✅ Connect button signals to internal handlers
- ✅ Manage tool button state (radio button behavior)
- ✅ Emit `tool-changed` signal
- ✅ Apply CSS styling

#### Assessment:
This loader is **well-scoped**. It handles UI loading, internal state management (which tool is active), and emits signals for external consumers. The signal-based architecture keeps it decoupled from business logic.

**No refactoring needed.**

---

### 2. ✅ `edit_palette_loader.py` (214 lines)

**Status: ACCEPTABLE** - Properly scoped

#### Current Responsibilities:
- ✅ Load UI file
- ✅ Connect button signals
- ✅ Manage palette visibility
- ✅ Emit signals for external consumers

#### Assessment:
**Well-designed loader.** Follows the same pattern as `edit_tools_loader`. Clean separation of concerns.

**No refactoring needed.**

---

### 3. ⚠️ **CRITICAL:** `model_canvas_loader.py` (1,372 lines)

**Status: NEEDS REFACTORING** - Violates Single Responsibility Principle

#### Current Responsibilities (TOO MANY):

##### ✅ **Legitimate Loader Duties:**
1. Load UI files (`model_canvas.ui`)
2. Create notebook structure (tabs for multiple documents)
3. Wire up event connections (GTK signal connections)
4. Initialize canvas managers
5. Manage document lifecycle (add/close tabs)

##### ❌ **VIOLATIONS - Should Be Moved:**

#### A. **Business Logic** (Lines 390-820+)
**Location:** `_on_button_press()`, `_on_button_release()`, `_on_motion_notify()`

**Problems:**
```python
# Example: Arc creation logic embedded in event handler
if event.button == 1 and manager.is_tool_active() and manager.get_tool() == 'arc':
    # Arc tool: two-click arc creation
    world_x, world_y = manager.screen_to_world(event.x, event.y)
    clicked_obj = manager.find_object_at_position(world_x, world_y)
    
    if clicked_obj is None:
        # Click on empty space: reset arc source
        if arc_state['source'] is not None:
            arc_state['source'] = None
            widget.queue_draw()
        return True
    
    if arc_state['source'] is None:
        # First click: set source
        if isinstance(clicked_obj, (Place, Transition)):
            arc_state['source'] = clicked_obj
            print(f"Arc creation: source {clicked_obj.name} selected")
```

**Why It's Wrong:**
- Arc creation state machine logic belongs in a `ArcCreationController` or `ToolController`
- Loader should only connect events, not implement tool behavior
- Makes testing tool behavior difficult (must mock GTK events)

**Should Be:** 
```python
# In loader (only connects):
def _on_button_press(self, widget, event, manager):
    self.tool_controller.handle_button_press(event, manager)

# In src/shypn/controllers/tool_controller.py:
class ToolController:
    def handle_button_press(self, event, manager):
        # Arc creation logic here
```

---

#### B. **Object Creation Logic** (Lines 450-468)
**Location:** `_on_button_press()`

**Problems:**
```python
if tool == 'place':
    # Create place at click position
    place = manager.add_place(world_x, world_y)
    print(f"Created {place.name} at ({world_x:.1f}, {world_y:.1f})")
    widget.queue_draw()
elif tool == 'transition':
    # Create transition at click position
    transition = manager.add_transition(world_x, world_y)
    print(f"Created {transition.name} at ({world_x:.1f}, {world_y:.1f})")
    widget.queue_draw()
```

**Why It's Wrong:**
- Object creation commands should be in a command/action layer
- Violates MVC pattern (mixing view logic with model operations)

**Should Be:**
```python
# In src/shypn/controllers/creation_controller.py:
class CreationController:
    def create_object_at_position(self, tool_type, world_x, world_y, manager):
        if tool_type == 'place':
            return manager.add_place(world_x, world_y)
        elif tool_type == 'transition':
            return manager.add_transition(world_x, world_y)
```

---

#### C. **Selection Logic** (Lines 470-608)
**Location:** `_on_button_press()`

**Problems:**
```python
# Selection mode: active when no tool OR select tool is active
tool = manager.get_tool() if manager.is_tool_active() else None
is_selection_mode = (tool is None or tool == 'select')

if event.button == 1 and is_selection_mode:
    # Left-click: toggle selection OR start rectangle selection
    world_x, world_y = manager.screen_to_world(event.x, event.y)
    clicked_obj = manager.find_object_at_position(world_x, world_y)
    
    # Check for Ctrl key (multi-select)
    is_ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
    
    # Double-click detection
    click_state = self._click_state[widget]
    current_time = time.time()
    time_since_last = current_time - click_state['last_click_time']
    is_double_click = (...)
    
    # Complex selection state machine...
```

**Why It's Wrong:**
- 200+ lines of selection logic in an event handler
- Double-click timing logic mixed with loader
- Selection state machine should be separate

**Should Be:**
```python
# In src/shypn/controllers/selection_controller.py:
class SelectionController:
    def handle_click(self, event, manager):
        world_pos = manager.screen_to_world(event.x, event.y)
        clicked_obj = manager.find_object_at_position(*world_pos)
        
        if self.is_double_click(clicked_obj):
            self.enter_edit_mode(clicked_obj, manager)
        else:
            self.toggle_selection(clicked_obj, event.modifiers, manager)
```

---

#### D. **Rendering Logic** (Lines 820-888)
**Location:** `_draw_arc_preview()`

**Problems:**
```python
def _draw_arc_preview(self, cr, arc_state, manager):
    """Draw orange preview line for arc creation."""
    source = arc_state['source']
    cursor_x, cursor_y = arc_state['cursor_pos']
    
    # Get source position in world space
    src_x, src_y = source.x, source.y
    
    # Calculate direction vector
    dx = cursor_x - src_x
    dy = cursor_y - src_y
    dist = math.sqrt(dx * dx + dy * dy)
    
    # ... 50+ lines of Cairo rendering code
    
    # Draw orange preview line (legacy style)
    cr.set_source_rgba(0.95, 0.5, 0.1, 0.85)
    cr.set_line_width(2.0)
    cr.move_to(start_sx, start_sy)
    cr.line_to(end_sx, end_sy)
    cr.stroke()
```

**Why It's Wrong:**
- Rendering logic belongs with other rendering code
- Should be in `TransientArc` or a `PreviewRenderer` class
- Duplicates logic already in `Arc` rendering

**Should Be:**
```python
# In src/shypn/edit/transient_arc.py:
class TransientArc:
    def render_preview(self, cr, source, cursor_pos, manager):
        # All preview rendering logic here
        pass

# In loader (only calls):
def _on_draw(self, drawing_area, cr, width, height, manager):
    # ... other rendering
    if arc_state['source']:
        arc_preview = TransientArc(arc_state['source'])
        arc_preview.render_preview(cr, arc_state['cursor_pos'], manager)
```

---

#### E. **Context Menu Creation** (Lines 889-968, 1043-1142)
**Location:** `_show_object_context_menu()`, `_setup_canvas_context_menu()`

**Problems:**
```python
def _show_object_context_menu(self, x, y, drawing_area, manager, obj):
    """Show object-specific context menu."""
    from shypn.netobjs import Place, Transition, Arc
    
    # Create context menu
    menu = Gtk.Menu()
    
    # Determine object type for title
    if isinstance(obj, Place):
        obj_type = "Place"
        # Add place-specific items
        edit_marking = Gtk.MenuItem(label="Edit Marking...")
        edit_marking.connect('activate', 
            lambda m: self._on_edit_place_marking(obj, manager, drawing_area))
        menu.append(edit_marking)
    
    elif isinstance(obj, Transition):
        # Add transition items...
    elif isinstance(obj, Arc):
        # Add arc items...
    
    # Add common items
    edit_properties = Gtk.MenuItem(label="Edit Properties...")
    # ... 80+ lines of menu creation
```

**Why It's Wrong:**
- UI construction should be in dedicated UI builder classes
- Mixing GTK widget creation with loader logic
- Makes it hard to test menu behavior
- Hard to customize menus per object type

**Should Be:**
```python
# In src/shypn/ui/context_menus/object_menu_builder.py:
class ObjectMenuBuilder:
    def build_menu(self, obj, manager, drawing_area):
        menu = Gtk.Menu()
        
        if isinstance(obj, Place):
            return self._build_place_menu(obj, manager, drawing_area)
        elif isinstance(obj, Transition):
            return self._build_transition_menu(obj, manager, drawing_area)
        # ...

# In loader (only shows):
def _show_object_context_menu(self, x, y, drawing_area, manager, obj):
    menu = self.menu_builder.build_menu(obj, manager, drawing_area)
    menu.popup(None, None, None, None, 3, Gtk.get_current_event_time())
```

---

#### F. **Dialog Management** (Lines 1197-1305)
**Location:** `_on_object_properties()`

**Problems:**
```python
def _on_object_properties(self, obj, manager, drawing_area):
    """Show properties dialog for object."""
    from shypn.netobjs import Place, Transition, Arc
    
    dialog = Gtk.Dialog(
        title=f"{obj.name} Properties",
        parent=self.parent_window,
        flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
    )
    
    # ... 100+ lines of dialog creation and handling
    
    if isinstance(obj, Place):
        # Add marking field
        marking_label = Gtk.Label(label="Marking (tokens):")
        marking_entry = Gtk.SpinButton.new_with_range(0, 999, 1)
        marking_entry.set_value(obj.tokens)
        # ... more fields
```

**Why It's Wrong:**
- Dialog creation is a UI concern, not loader concern
- Each object type should have its own dialog class
- Violates Open/Closed Principle (adding new object types requires modifying loader)

**Should Be:**
```python
# In src/shypn/ui/dialogs/place_properties_dialog.py:
class PlacePropertiesDialog(Gtk.Dialog):
    def __init__(self, place, parent):
        super().__init__(title=f"{place.name} Properties", parent=parent)
        self._setup_ui(place)
    
    def get_values(self):
        return {
            'marking': self.marking_entry.get_value(),
            'label': self.label_entry.get_text()
        }

# In loader (only calls):
def _on_object_properties(self, obj, manager, drawing_area):
    dialog = self.dialog_factory.create_dialog(obj, self.parent_window)
    if dialog.run() == Gtk.ResponseType.OK:
        values = dialog.get_values()
        obj.update_properties(values)
        drawing_area.queue_draw()
    dialog.destroy()
```

---

## Recommended Refactoring

### Phase 1: Extract Controllers (High Priority)

```
src/shypn/controllers/
├── __init__.py
├── tool_controller.py        # Arc creation, Place/Transition creation logic
├── selection_controller.py   # Selection state machine, double-click detection
└── drag_controller.py         # Pan/drag logic
```

**Benefits:**
- Business logic can be unit tested without GTK
- Tool behavior can be modified without touching loader
- Clear separation of concerns

---

### Phase 2: Extract UI Builders (Medium Priority)

```
src/shypn/ui/
├── context_menus/
│   ├── __init__.py
│   ├── object_menu_builder.py   # Context menu creation
│   └── canvas_menu_builder.py   # Canvas context menu
└── dialogs/
    ├── __init__.py
    ├── place_properties_dialog.py
    ├── transition_properties_dialog.py
    └── arc_properties_dialog.py
```

**Benefits:**
- Easier to customize menus/dialogs
- Dialog code can be reused elsewhere
- Follows Single Responsibility Principle

---

### Phase 3: Extract Renderers (Medium Priority)

```
src/shypn/renderers/
├── __init__.py
├── arc_preview_renderer.py     # Arc preview rendering
└── selection_preview_renderer.py  # Rectangle selection rendering
```

**Benefits:**
- Rendering logic stays with other rendering code
- Easier to test rendering without full GTK setup
- Can optimize rendering separately

---

### Phase 4: Slim Down Loader (Final)

After extractions, `model_canvas_loader.py` should be **~300-400 lines** focused on:

1. ✅ Load UI files
2. ✅ Create notebook and documents
3. ✅ Initialize controllers (dependency injection)
4. ✅ Connect GTK signals to controllers
5. ✅ Manage document lifecycle

**Example of clean loader:**
```python
class ModelCanvasLoader:
    def __init__(self, ui_path=None):
        self.ui_path = ui_path
        self.tool_controller = ToolController()
        self.selection_controller = SelectionController()
        self.menu_builder = ObjectMenuBuilder()
        self.dialog_factory = DialogFactory()
    
    def _setup_event_controllers(self, drawing_area, manager):
        """Wire up event connections to controllers."""
        drawing_area.connect('button-press-event', 
            lambda w, e: self._dispatch_button_press(w, e, manager))
        # ... other connections
    
    def _dispatch_button_press(self, widget, event, manager):
        """Route event to appropriate controller."""
        tool = manager.get_tool()
        
        if tool in ('place', 'transition', 'arc'):
            return self.tool_controller.handle_button_press(event, manager)
        else:
            return self.selection_controller.handle_button_press(event, manager)
```

---

## Migration Strategy

### Step 1: Create Controller Structure (Week 1)
- Create `src/shypn/controllers/` directory
- Extract `ToolController` with arc creation logic
- Extract `SelectionController` with selection logic
- Update loader to use controllers

### Step 2: Extract UI Builders (Week 2)
- Create `src/shypn/ui/context_menus/` and `src/shypn/ui/dialogs/`
- Move context menu creation to builders
- Move dialog creation to dedicated dialog classes
- Update loader to use builders

### Step 3: Extract Renderers (Week 3)
- Move arc preview rendering to `TransientArc` or `ArcPreviewRenderer`
- Move rectangle selection rendering to `RectangleSelectionRenderer`
- Update draw handlers to use renderers

### Step 4: Final Cleanup (Week 4)
- Remove all business logic from loader
- Loader should be ~300-400 lines
- Update tests to test controllers/builders directly
- Update documentation

---

## Conclusion

### Current State:
- ✅ `edit_tools_loader.py`: **Well-designed**, no changes needed
- ✅ `edit_palette_loader.py`: **Well-designed**, no changes needed
- ❌ `model_canvas_loader.py`: **Needs refactoring**, violates SRP

### Recommended Actions:
1. **Immediate:** Create `controllers/` directory and start extracting business logic
2. **Short-term:** Extract UI builders (menus, dialogs)
3. **Medium-term:** Extract rendering logic
4. **Long-term:** Reduce loader to ~300-400 lines of pure loading/wiring

### Expected Benefits:
- **Testability:** Controllers can be unit tested without GTK
- **Maintainability:** Clear separation of concerns
- **Extensibility:** Easy to add new tools, objects, menus
- **Readability:** Each module has a single, clear purpose

---

**Next Steps:** Begin Phase 1 extraction of `ToolController` and `SelectionController`.
