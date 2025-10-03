# Canvas Architecture Revision Plan

**Date:** October 3, 2025  
**Purpose:** Redesign canvas architecture based on proper separation of concerns

---

## Core Canvas Responsibilities Analysis

### What IS the Canvas Role?

A **Document Canvas** is responsible for:

1. ✅ **Interface Creation** - Provide a surface for user interaction with the document
2. ✅ **State Management** - Maintain document state (initialization → production → modified)
3. ✅ **Dirty State Tracking** - Know when content has changed (for save prompts, undo/redo)
4. ✅ **Redraw Management** - Keep visual representation synchronized with document state
5. ✅ **Data Persistence Interface** - Coordinate with persistence layer (load/save operations)
6. ✅ **Viewport Management** - Handle pan, zoom, visible region calculations
7. ✅ **Document Metadata** - Track filename, title, modification time, author
8. ✅ **Coordinate Transformations** - Screen ↔ World coordinate conversions
9. ✅ **Object Queries** - Find objects at position, get all objects, spatial queries
10. ✅ **Rendering Pipeline** - Orchestrate rendering of grid, objects, overlays

### What is NOT the Canvas Role?

❌ **Editing Operations** - Should be in separate editing layer/controllers  
❌ **Tool Behavior** - Should be in tool controllers  
❌ **UI Widget Creation** - Should be in loader/UI builders  
❌ **Event Interpretation** - Should be in event handlers/controllers  
❌ **Dialog Management** - Should be in UI layer  
❌ **Context Menu Creation** - Should be in UI builders  

---

## Current Architecture Problems

### Problem 1: Loader is Doing Canvas Work

**Current:** `model_canvas_loader.py` contains:
- Event handling logic (button press, motion, etc.)
- Tool behavior implementation (arc creation, object placement)
- Selection logic (double-click detection, multi-select)
- Context menu creation
- Dialog management

**Issue:** Loader should only **load and wire**, not implement behavior.

---

### Problem 2: Canvas Manager is Too Thin

**Current:** `ModelCanvasManager` (model_canvas_manager.py) is mostly:
- Data storage (places, transitions, arcs)
- Grid rendering
- Coordinate transforms
- Basic zoom/pan operations

**Missing from Canvas:**
- Dirty state tracking
- Document lifecycle management
- Event routing/coordination
- Command history (undo/redo infrastructure)
- Persistence coordination

---

### Problem 3: No Editing Layer

**Current:** Editing logic is scattered in loader event handlers.

**Missing:** A separate editing layer that:
- Implements tool behaviors
- Handles selection operations
- Manages edit modes (normal, edit, drag)
- Provides editing commands (create, delete, move, modify)
- Maintains editing state machines

---

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     UI Layer (GTK)                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Loader: Loads UI, wires signals to Canvas           │  │
│  │  • load_ui()                                          │  │
│  │  • create_widgets()                                   │  │
│  │  • connect_signals() → Routes to Canvas              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  UI Builders: Create menus, dialogs, palettes        │  │
│  │  • ContextMenuBuilder                                 │  │
│  │  • DialogFactory                                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (GTK Events)
┌─────────────────────────────────────────────────────────────┐
│                    Canvas Layer                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  DocumentCanvas: Main canvas controller              │  │
│  │  • State management (new → modified → saved)         │  │
│  │  • Dirty tracking (has_unsaved_changes)              │  │
│  │  • Redraw coordination (queue_redraw)                │  │
│  │  • Event routing (route_event → Editing Layer)       │  │
│  │  • Persistence coordination (load/save)              │  │
│  │  • Viewport management (pan, zoom, clamp)            │  │
│  │  • Rendering pipeline (render_all)                   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  CanvasRenderer: Rendering orchestration             │  │
│  │  • render_grid()                                      │  │
│  │  • render_objects()                                   │  │
│  │  • render_overlays() (selection, handles)            │  │
│  │  • render_transients() (arc preview, drag preview)   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (Canvas Events)
┌─────────────────────────────────────────────────────────────┐
│                   Editing Layer                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  EditingController: Route to active tool/mode        │  │
│  │  • handle_event(event, canvas) → active_tool         │  │
│  │  • set_active_tool(tool)                              │  │
│  │  • get_active_mode() → NORMAL / EDIT / DRAG          │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Tool Controllers: Implement tool behaviors          │  │
│  │  • SelectTool: Selection, double-click, rect select  │  │
│  │  • PlaceTool: Create places on click                 │  │
│  │  • TransitionTool: Create transitions on click       │  │
│  │  • ArcTool: Two-click arc creation state machine     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Edit Commands: Encapsulate operations (undoable)    │  │
│  │  • CreateObjectCommand(obj_type, x, y)               │  │
│  │  • DeleteObjectCommand(obj)                           │  │
│  │  • MoveObjectCommand(obj, dx, dy)                    │  │
│  │  • ModifyPropertyCommand(obj, prop, value)           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (Commands)
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Document Model: Petri net object collections        │  │
│  │  • places: List[Place]                                │  │
│  │  • transitions: List[Transition]                      │  │
│  │  • arcs: List[Arc]                                    │  │
│  │  • add_object(obj), remove_object(obj)                │  │
│  │  • find_object_at(x, y) → obj                         │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Persistence: Save/load operations                    │  │
│  │  • save_to_file(document, path)                       │  │
│  │  • load_from_file(path) → document                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Component Responsibilities

### 1. **DocumentCanvas** (NEW - Core Canvas Controller)

**Location:** `src/shypn/canvas/document_canvas.py`

**Responsibilities:**
```python
class DocumentCanvas:
    """Core document canvas controller.
    
    Manages document state, coordinates rendering, routes events to editing layer.
    This is the main interface that the loader interacts with.
    """
    
    # State Management
    def __init__(self, filename=None):
        self.document_model = DocumentModel()  # Data layer
        self.renderer = CanvasRenderer()       # Rendering
        self.editing_controller = EditingController()  # Editing
        
        self.filename = filename
        self.title = "Untitled"
        self.is_dirty = False
        self.state = DocumentState.NEW  # NEW, LOADED, MODIFIED
    
    # Document Lifecycle
    def new_document(self):
        """Create a new empty document."""
        
    def load_document(self, filepath):
        """Load document from file."""
        
    def save_document(self, filepath=None):
        """Save document to file."""
        
    def close_document(self) -> bool:
        """Close document (returns False if user cancels)."""
    
    # Dirty State Tracking
    def mark_dirty(self):
        """Mark document as modified."""
        
    def mark_clean(self):
        """Mark document as saved."""
        
    def has_unsaved_changes(self) -> bool:
        """Check if document has unsaved changes."""
    
    # Event Routing (delegates to editing layer)
    def handle_button_press(self, event):
        """Route button press to editing controller."""
        return self.editing_controller.handle_button_press(event, self)
    
    def handle_button_release(self, event):
        """Route button release to editing controller."""
        
    def handle_motion(self, event):
        """Route motion to editing controller."""
    
    def handle_scroll(self, event):
        """Handle zoom (canvas responsibility, not editing)."""
        self.zoom_at_point(event.x, event.y, event.delta)
        self.queue_redraw()
    
    def handle_key_press(self, event):
        """Route key press to editing controller."""
    
    # Rendering Pipeline (orchestrates, delegates to renderer)
    def render(self, cr, width, height):
        """Main rendering pipeline."""
        # Apply viewport transform
        cr.save()
        self.apply_viewport_transform(cr)
        
        # Render in layers
        self.renderer.render_grid(cr, self)
        self.renderer.render_objects(cr, self.document_model)
        self.renderer.render_overlays(cr, self.editing_controller)
        self.renderer.render_transients(cr, self.editing_controller)
        
        cr.restore()
    
    def queue_redraw(self):
        """Request a redraw (signals GTK widget)."""
        if self.on_redraw_requested:
            self.on_redraw_requested()
    
    # Viewport Management (canvas responsibility)
    def zoom_at_point(self, x, y, delta):
        """Zoom canvas at specific point."""
        
    def pan_by(self, dx, dy):
        """Pan canvas by delta."""
        
    def screen_to_world(self, x, y) -> tuple:
        """Convert screen coords to world coords."""
        
    def world_to_screen(self, x, y) -> tuple:
        """Convert world coords to screen coords."""
    
    # Object Queries (delegates to document model)
    def find_object_at(self, x, y):
        """Find object at world position."""
        return self.document_model.find_object_at(x, y)
    
    def get_all_objects(self) -> list:
        """Get all document objects."""
        return self.document_model.get_all_objects()
    
    # Tool Management (delegates to editing controller)
    def set_active_tool(self, tool_name):
        """Set the active editing tool."""
        self.editing_controller.set_active_tool(tool_name)
    
    def get_active_tool(self) -> str:
        """Get the active editing tool."""
        return self.editing_controller.get_active_tool()
```

---

### 2. **EditingController** (NEW - Editing Layer Coordinator)

**Location:** `src/shypn/controllers/editing_controller.py`

**Responsibilities:**
```python
class EditingController:
    """Coordinates editing operations and tool behavior.
    
    Routes events to the appropriate tool based on active tool state.
    """
    
    def __init__(self):
        # Tool registry
        self.tools = {
            'select': SelectTool(),
            'place': PlaceTool(),
            'transition': TransitionTool(),
            'arc': ArcTool()
        }
        self.active_tool = None  # None = default select behavior
        
        # Editing state
        self.selection_manager = SelectionManager()
        self.drag_state = DragState()
    
    def set_active_tool(self, tool_name):
        """Activate a tool."""
        self.active_tool = self.tools.get(tool_name)
        if self.active_tool:
            self.active_tool.on_activated()
    
    def get_active_tool(self) -> str:
        """Get active tool name."""
        if self.active_tool:
            return self.active_tool.name
        return 'select'  # Default
    
    def handle_button_press(self, event, canvas):
        """Route button press to active tool."""
        tool = self.active_tool or self.tools['select']
        return tool.handle_button_press(event, canvas, self)
    
    def handle_button_release(self, event, canvas):
        """Route button release to active tool."""
        tool = self.active_tool or self.tools['select']
        return tool.handle_button_release(event, canvas, self)
    
    def handle_motion(self, event, canvas):
        """Route motion to active tool."""
        tool = self.active_tool or self.tools['select']
        return tool.handle_motion(event, canvas, self)
    
    def handle_key_press(self, event, canvas):
        """Route key press to active tool."""
        # Handle global keys (Escape, Delete, etc.)
        if event.keyval == Gdk.KEY_Escape:
            self.exit_edit_mode(canvas)
            return True
        elif event.keyval == Gdk.KEY_Delete:
            self.delete_selected_objects(canvas)
            return True
        
        # Route to active tool
        tool = self.active_tool or self.tools['select']
        return tool.handle_key_press(event, canvas, self)
```

---

### 3. **Tool Base Class and Implementations**

**Location:** `src/shypn/controllers/tools/`

```python
class Tool(ABC):
    """Base class for editing tools."""
    
    def __init__(self, name):
        self.name = name
    
    @abstractmethod
    def handle_button_press(self, event, canvas, editing_controller):
        """Handle button press event."""
        pass
    
    @abstractmethod
    def handle_button_release(self, event, canvas, editing_controller):
        """Handle button release event."""
        pass
    
    @abstractmethod
    def handle_motion(self, event, canvas, editing_controller):
        """Handle motion event."""
        pass
    
    def on_activated(self):
        """Called when tool becomes active."""
        pass
    
    def on_deactivated(self):
        """Called when tool becomes inactive."""
        pass


class ArcTool(Tool):
    """Arc creation tool - implements two-click arc creation."""
    
    def __init__(self):
        super().__init__('arc')
        self.source = None
        self.cursor_pos = None
    
    def handle_button_press(self, event, canvas, editing_controller):
        """Handle click for arc creation."""
        world_x, world_y = canvas.screen_to_world(event.x, event.y)
        clicked_obj = canvas.find_object_at(world_x, world_y)
        
        if clicked_obj is None:
            # Click on empty: reset
            self.source = None
            canvas.queue_redraw()
            return True
        
        if self.source is None:
            # First click: set source
            if isinstance(clicked_obj, (Place, Transition)):
                self.source = clicked_obj
                canvas.queue_redraw()
            return True
        else:
            # Second click: create arc
            try:
                cmd = CreateArcCommand(self.source, clicked_obj)
                cmd.execute(canvas.document_model)
                canvas.mark_dirty()
                canvas.queue_redraw()
            except ValueError as e:
                print(f"Cannot create arc: {e}")
            finally:
                self.source = None
            return True
    
    def handle_motion(self, event, canvas, editing_controller):
        """Update cursor position for preview."""
        if self.source:
            world_x, world_y = canvas.screen_to_world(event.x, event.y)
            self.cursor_pos = (world_x, world_y)
            canvas.queue_redraw()
        return False
    
    def render_preview(self, cr, canvas):
        """Render arc preview line."""
        if self.source and self.cursor_pos:
            # Render preview line from source to cursor
            pass
```

---

### 4. **CanvasRenderer** (NEW - Rendering Orchestration)

**Location:** `src/shypn/canvas/canvas_renderer.py`

**Responsibilities:**
```python
class CanvasRenderer:
    """Orchestrates canvas rendering in layers.
    
    Keeps rendering logic separate from canvas controller.
    """
    
    def render_grid(self, cr, canvas):
        """Render the grid layer."""
        # Grid rendering logic (from ModelCanvasManager)
        pass
    
    def render_objects(self, cr, document_model):
        """Render all document objects."""
        for obj in document_model.get_all_objects():
            obj.render(cr)
    
    def render_overlays(self, cr, editing_controller):
        """Render editing overlays (selection, handles)."""
        # Render selection highlights
        editing_controller.selection_manager.render_selection(cr)
        
        # Render transform handles (if in EDIT mode)
        if editing_controller.selection_manager.is_edit_mode():
            editing_controller.selection_manager.render_handles(cr)
    
    def render_transients(self, cr, editing_controller):
        """Render transient/preview elements."""
        # Render active tool's preview
        active_tool = editing_controller.active_tool
        if active_tool and hasattr(active_tool, 'render_preview'):
            active_tool.render_preview(cr, editing_controller)
        
        # Render rectangle selection
        if editing_controller.rectangle_selection.active:
            editing_controller.rectangle_selection.render(cr)
```

---

### 5. **Loader Simplified**

**Location:** `src/shypn/helpers/model_canvas_loader.py`

**New responsibilities (ONLY):**
```python
class ModelCanvasLoader:
    """Loads canvas UI and wires signals to DocumentCanvas.
    
    This is a pure loader - no business logic, only UI loading and wiring.
    """
    
    def __init__(self, ui_path=None):
        self.ui_path = ui_path
        self.builder = None
        self.notebook = None
        self.canvases = {}  # {drawing_area: DocumentCanvas}
    
    def load(self):
        """Load UI file and setup notebook."""
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        self.notebook = self.builder.get_object('model_notebook')
        
        # Connect notebook signals
        self.notebook.connect('switch-page', self._on_page_switched)
        
        return self.notebook
    
    def add_document(self, title=None, filename=None):
        """Add a new document tab."""
        # Create canvas
        canvas = DocumentCanvas(filename=filename)
        
        # Create GTK widgets
        drawing_area = Gtk.DrawingArea()
        drawing_area.set_can_focus(True)
        
        # Wire canvas to GTK widget
        canvas.on_redraw_requested = drawing_area.queue_draw
        
        # Connect GTK signals to canvas
        drawing_area.connect('button-press-event', 
            lambda w, e: canvas.handle_button_press(e))
        drawing_area.connect('button-release-event',
            lambda w, e: canvas.handle_button_release(e))
        drawing_area.connect('motion-notify-event',
            lambda w, e: canvas.handle_motion(e))
        drawing_area.connect('scroll-event',
            lambda w, e: canvas.handle_scroll(e))
        drawing_area.connect('key-press-event',
            lambda w, e: canvas.handle_key_press(e))
        drawing_area.connect('draw',
            lambda w, cr: canvas.render(cr, w.get_allocated_width(), 
                                           w.get_allocated_height()))
        
        # Enable events
        drawing_area.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.SCROLL_MASK |
            Gdk.EventMask.KEY_PRESS_MASK
        )
        
        # Add to notebook
        scroll_window = Gtk.ScrolledWindow()
        scroll_window.add(drawing_area)
        
        page_num = self.notebook.append_page(scroll_window, 
            Gtk.Label(label=title or "Untitled"))
        
        # Store canvas reference
        self.canvases[drawing_area] = canvas
        
        # Show and switch to new tab
        self.notebook.show_all()
        self.notebook.set_current_page(page_num)
        
        return canvas
    
    def get_current_canvas(self) -> DocumentCanvas:
        """Get canvas for current tab."""
        page_num = self.notebook.get_current_page()
        if page_num >= 0:
            page = self.notebook.get_nth_page(page_num)
            # Navigate: notebook → scroll_window → drawing_area
            drawing_area = page.get_child()
            return self.canvases.get(drawing_area)
        return None
    
    # That's it! ~150 lines total
```

---

## Migration Strategy

### Phase 1: Create New Structure (Week 1)

**Step 1.1: Create DocumentCanvas**
```bash
mkdir -p src/shypn/canvas
touch src/shypn/canvas/__init__.py
touch src/shypn/canvas/document_canvas.py
touch src/shypn/canvas/canvas_renderer.py
```

**Step 1.2: Create EditingController**
```bash
mkdir -p src/shypn/controllers/tools
touch src/shypn/controllers/__init__.py
touch src/shypn/controllers/editing_controller.py
touch src/shypn/controllers/tools/__init__.py
touch src/shypn/controllers/tools/base.py
touch src/shypn/controllers/tools/select_tool.py
touch src/shypn/controllers/tools/arc_tool.py
touch src/shypn/controllers/tools/place_tool.py
touch src/shypn/controllers/tools/transition_tool.py
```

**Step 1.3: Extract Logic from Loader**
- Move event handling logic → tools
- Move rendering logic → CanvasRenderer
- Move state management → DocumentCanvas

---

### Phase 2: Implement DocumentCanvas (Week 2)

**Step 2.1: Document Lifecycle**
- Implement new_document(), load_document(), save_document()
- Implement dirty state tracking
- Add document metadata

**Step 2.2: Event Routing**
- Implement handle_button_press() → route to EditingController
- Implement handle_motion() → route to EditingController
- Keep handle_scroll() → canvas responsibility (viewport)

**Step 2.3: Rendering Pipeline**
- Implement render() method
- Create CanvasRenderer and delegate rendering

---

### Phase 3: Implement Editing Layer (Week 3)

**Step 3.1: Create Tool Base Class**
- Define Tool interface
- Implement tool activation/deactivation

**Step 3.2: Implement Each Tool**
- SelectTool: Selection, double-click, rectangle select
- PlaceTool: Create places on click
- TransitionTool: Create transitions on click
- ArcTool: Two-click arc creation

**Step 3.3: Create EditingController**
- Route events to active tool
- Manage tool switching
- Handle global keys (Escape, Delete)

---

### Phase 4: Simplify Loader (Week 4)

**Step 4.1: Remove Business Logic**
- Delete all tool implementation code
- Delete all event handling logic
- Delete all rendering logic

**Step 4.2: Pure Wiring**
- Keep only UI loading
- Keep only signal connections to DocumentCanvas
- Keep only widget creation

**Step 4.3: Verification**
- Loader should be ~150-200 lines
- No business logic in loader
- All logic in Canvas or Editing layer

---

### Phase 5: Testing & Documentation (Week 5)

**Step 5.1: Unit Tests**
- Test DocumentCanvas in isolation
- Test each Tool in isolation
- Test EditingController routing

**Step 5.2: Integration Tests**
- Test complete editing workflows
- Test document lifecycle
- Test persistence

**Step 5.3: Documentation**
- Update architecture docs
- Create developer guide
- Document canvas API

---

## Expected Results

### Before (Current State):
```
model_canvas_loader.py:  1,372 lines (EVERYTHING)
model_canvas_manager.py:  1,042 lines (thin data storage)
```

### After (Target State):
```
# UI Layer
model_canvas_loader.py:     ~200 lines (pure loading/wiring)

# Canvas Layer
document_canvas.py:         ~400 lines (state, lifecycle, routing)
canvas_renderer.py:         ~200 lines (rendering orchestration)

# Editing Layer
editing_controller.py:      ~150 lines (event routing)
tools/select_tool.py:       ~200 lines (selection logic)
tools/arc_tool.py:          ~150 lines (arc creation)
tools/place_tool.py:        ~100 lines (place creation)
tools/transition_tool.py:   ~100 lines (transition creation)

# Data Layer (existing)
model_canvas_manager.py:    ~800 lines (data model, cleanup)
```

---

## Benefits

1. **Clear Separation of Concerns**
   - Loader: UI loading and wiring
   - Canvas: Document lifecycle and coordination
   - Editing: Tool behavior and commands
   - Data: Object storage and queries

2. **Testability**
   - Canvas can be tested without GTK
   - Tools can be tested in isolation
   - Commands are naturally testable

3. **Maintainability**
   - Each component has single responsibility
   - Easy to find where logic lives
   - Easy to modify tool behavior

4. **Extensibility**
   - Add new tools by implementing Tool interface
   - Add new commands for undo/redo
   - Add new rendering layers easily

5. **Reusability**
   - DocumentCanvas can be used in different UI frameworks
   - Tools can be reused across different canvas types
   - Commands can be shared and composed

---

## Next Steps

Would you like me to:
1. Start implementing Phase 1 (create structure)?
2. Begin with DocumentCanvas implementation?
3. Start with EditingController and tools?
4. Create a proof-of-concept with one tool first?

Please advise on the preferred starting point!
