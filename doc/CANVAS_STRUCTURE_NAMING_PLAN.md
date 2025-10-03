# Canvas Architecture - Directory Structure and Naming Plan

**Date:** October 3, 2025  
**Location:** `src/shypn/data/`

---

## Current Structure (Before)

```
src/shypn/
├── data/
│   ├── model_canvas_manager.py  (1,042 lines - data model + viewport)
│   └── user_model.py             (user settings)
├── helpers/
│   ├── model_canvas_loader.py   (1,372 lines - EVERYTHING)
│   ├── edit_tools_loader.py
│   └── edit_palette_loader.py
└── edit/
    ├── selection_manager.py
    ├── object_editing_transforms.py
    └── rectangle_selection.py
```

---

## Proposed Structure (After)

### Overview
```
src/shypn/
├── data/                        # Data/Model Layer
│   ├── canvas/                  # Canvas-specific data models
│   │   ├── __init__.py
│   │   ├── document_canvas.py   # Main canvas controller
│   │   ├── document_model.py    # Document data model
│   │   └── canvas_state.py      # Canvas state enums and types
│   ├── model_canvas_manager.py  # (existing, will be refactored)
│   └── user_model.py            # (existing)
│
├── controllers/                 # NEW: Business Logic Layer
│   ├── __init__.py
│   ├── editing_controller.py   # Main editing coordinator
│   ├── tools/                   # Tool implementations
│   │   ├── __init__.py
│   │   ├── base_tool.py         # Abstract base class
│   │   ├── select_tool.py       # Selection tool
│   │   ├── place_tool.py        # Place creation
│   │   ├── transition_tool.py   # Transition creation
│   │   └── arc_tool.py          # Arc creation (state machine)
│   └── commands/                # Command pattern (for undo/redo)
│       ├── __init__.py
│       ├── base_command.py
│       ├── create_object_command.py
│       ├── delete_object_command.py
│       └── modify_object_command.py
│
├── renderers/                   # NEW: Rendering Layer
│   ├── __init__.py
│   ├── canvas_renderer.py       # Main rendering orchestrator
│   ├── grid_renderer.py         # Grid rendering
│   ├── object_renderer.py       # Object rendering coordination
│   └── preview_renderer.py      # Transient/preview rendering
│
├── helpers/                     # UI Loaders (simplified)
│   ├── model_canvas_loader.py   # Pure loader/wiring (~200 lines)
│   ├── edit_tools_loader.py     # (existing)
│   └── edit_palette_loader.py   # (existing)
│
├── edit/                        # Editing support (existing)
│   ├── selection_manager.py
│   ├── object_editing_transforms.py
│   └── rectangle_selection.py
│
├── api/                         # Object models (existing)
│   └── netobjs/
│       ├── place.py
│       ├── transition.py
│       └── arc.py
│
└── ui/                          # NEW: UI Builders
    ├── __init__.py
    ├── context_menus/
    │   ├── __init__.py
    │   ├── canvas_menu_builder.py
    │   └── object_menu_builder.py
    └── dialogs/
        ├── __init__.py
        ├── base_properties_dialog.py
        ├── place_properties_dialog.py
        ├── transition_properties_dialog.py
        └── arc_properties_dialog.py
```

---

## Detailed Breakdown - src/shypn/data/canvas/

### Why under `data/`?

The canvas is fundamentally a **data structure** that:
- Manages document state
- Coordinates data operations
- Acts as the central data controller
- Bridges between data layer and UI layer

### File Details:

#### 1. `document_canvas.py` (~400-500 lines)

**Purpose:** Main canvas controller - the "brain" of a document

**Responsibilities:**
- Document lifecycle (new, load, save, close)
- State management (NEW, LOADED, MODIFIED, SAVED)
- Dirty tracking (has_unsaved_changes)
- Event routing (delegates to editing_controller)
- Rendering coordination (delegates to canvas_renderer)
- Viewport management (pan, zoom, transforms)

**Key Classes:**
```python
class DocumentCanvas:
    """Main canvas controller for a Petri net document.
    
    This is the primary interface between the UI layer and the
    data/editing layers. It coordinates all canvas operations.
    """
    
    def __init__(self, filename=None):
        # Core components
        self.document_model = DocumentModel()
        self.canvas_state = CanvasState()
        
        # Collaborators
        self.renderer = None  # Set by loader
        self.editing_controller = None  # Set by loader
        
        # Document metadata
        self.filename = filename
        self.title = "Untitled"
        self.is_dirty = False
        
        # Viewport state
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.zoom = 1.0
    
    # Document lifecycle
    def new_document(self): ...
    def load_document(self, filepath): ...
    def save_document(self, filepath=None): ...
    def close_document(self) -> bool: ...
    
    # State management
    def mark_dirty(self): ...
    def mark_clean(self): ...
    def has_unsaved_changes(self) -> bool: ...
    
    # Event routing (delegates to editing_controller)
    def handle_button_press(self, event): ...
    def handle_motion(self, event): ...
    def handle_scroll(self, event): ...  # Canvas handles zoom directly
    
    # Rendering (delegates to renderer)
    def render(self, cr, width, height): ...
    def queue_redraw(self): ...
    
    # Viewport (canvas responsibility)
    def zoom_at_point(self, x, y, delta): ...
    def pan_by(self, dx, dy): ...
    def screen_to_world(self, x, y): ...
    def world_to_screen(self, x, y): ...
```

---

#### 2. `document_model.py` (~200-300 lines)

**Purpose:** Pure data model for a Petri net document

**Responsibilities:**
- Store Petri net objects (places, transitions, arcs)
- Provide object queries (find at position, get all)
- Manage object IDs and names
- Object CRUD operations

**Key Classes:**
```python
class DocumentModel:
    """Data model for a Petri net document.
    
    Stores all document objects and provides query operations.
    This is a pure data structure with no UI concerns.
    """
    
    def __init__(self):
        self.places = []        # List[Place]
        self.transitions = []   # List[Transition]
        self.arcs = []          # List[Arc]
        
        # ID counters for unique naming
        self._place_counter = 0
        self._transition_counter = 0
        self._arc_counter = 0
    
    # Object management
    def add_place(self, x, y, **kwargs) -> Place: ...
    def add_transition(self, x, y, **kwargs) -> Transition: ...
    def add_arc(self, source, target, **kwargs) -> Arc: ...
    
    def remove_place(self, place): ...
    def remove_transition(self, transition): ...
    def remove_arc(self, arc): ...
    
    # Queries
    def get_all_objects(self) -> list: ...
    def find_object_at(self, x, y) -> Optional[PetriNetObject]: ...
    def find_object_by_id(self, obj_id) -> Optional[PetriNetObject]: ...
    def find_object_by_name(self, name) -> Optional[PetriNetObject]: ...
    
    # Bulk operations
    def clear_all(self): ...
    def get_bounds(self) -> Tuple[float, float, float, float]: ...
    
    # Serialization support
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> 'DocumentModel': ...
```

---

#### 3. `canvas_state.py` (~100 lines)

**Purpose:** State enums, types, and state-related data structures

**Responsibilities:**
- Define canvas state enums
- Define viewport state
- Define tool state types

**Key Classes/Enums:**
```python
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Tuple

class DocumentState(Enum):
    """Document lifecycle states."""
    NEW = auto()        # New, never saved
    LOADED = auto()     # Loaded from file, unchanged
    MODIFIED = auto()   # Has unsaved changes
    SAVED = auto()      # Recently saved
    CLOSING = auto()    # In process of closing

class EditMode(Enum):
    """Canvas editing modes."""
    NORMAL = auto()     # Normal mode - selection allowed
    EDIT = auto()       # Edit mode - transform handles visible
    DRAG = auto()       # Dragging object(s)
    PAN = auto()        # Panning viewport

@dataclass
class ViewportState:
    """Viewport transformation state."""
    pan_x: float = 0.0
    pan_y: float = 0.0
    zoom: float = 1.0
    width: int = 800
    height: int = 600
    
    def screen_to_world(self, x: float, y: float) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates."""
        world_x = (x - self.width / 2) / self.zoom - self.pan_x
        world_y = (y - self.height / 2) / self.zoom - self.pan_y
        return (world_x, world_y)
    
    def world_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        """Convert world coordinates to screen coordinates."""
        screen_x = (x + self.pan_x) * self.zoom + self.width / 2
        screen_y = (y + self.pan_y) * self.zoom + self.height / 2
        return (screen_x, screen_y)

@dataclass
class DragState:
    """State for drag operations."""
    active: bool = False
    start_x: float = 0.0
    start_y: float = 0.0
    current_x: float = 0.0
    current_y: float = 0.0
    objects: list = None  # Objects being dragged
    
    def __post_init__(self):
        if self.objects is None:
            self.objects = []
```

---

## Migration from Existing Code

### What happens to `model_canvas_manager.py`?

**Current responsibilities:**
1. ✅ Grid rendering → Move to `renderers/grid_renderer.py`
2. ✅ Viewport transforms → Move to `data/canvas/canvas_state.py` (ViewportState)
3. ✅ Object storage → Move to `data/canvas/document_model.py`
4. ✅ Selection management → Already in `edit/selection_manager.py`
5. ✅ Basic zoom/pan → Move to `data/canvas/document_canvas.py`

**After migration:**
- `model_canvas_manager.py` can be **deprecated** or kept as a thin wrapper
- All its functionality distributed to proper layers

---

## Naming Conventions

### Module Names (snake_case)
- `document_canvas.py` - Main canvas controller
- `document_model.py` - Data model
- `canvas_state.py` - State types and enums

### Class Names (PascalCase)
- `DocumentCanvas` - Main controller
- `DocumentModel` - Data model
- `DocumentState` - Enum
- `ViewportState` - Dataclass

### Why "Document"?
- Emphasizes that each canvas is a **document**
- Aligns with multi-document interface (tabs)
- Clear distinction: "Document" = data, "Canvas" = view/controller

---

## Directory Creation Order

### Phase 1: Create Structure
```bash
# 1. Create canvas subdirectory under data
mkdir -p src/shypn/data/canvas
touch src/shypn/data/canvas/__init__.py

# 2. Create files
touch src/shypn/data/canvas/canvas_state.py       # Start here (no dependencies)
touch src/shypn/data/canvas/document_model.py     # Next (depends on canvas_state)
touch src/shypn/data/canvas/document_canvas.py    # Last (depends on both)
```

### Phase 2: Create Controllers (later)
```bash
mkdir -p src/shypn/controllers/tools
touch src/shypn/controllers/__init__.py
touch src/shypn/controllers/editing_controller.py
# ... etc
```

### Phase 3: Create Renderers (later)
```bash
mkdir -p src/shypn/renderers
touch src/shypn/renderers/__init__.py
touch src/shypn/renderers/canvas_renderer.py
# ... etc
```

---

## Import Hierarchy

```
UI Layer (helpers/model_canvas_loader.py)
    ↓ imports and uses
data/canvas/document_canvas.py
    ↓ uses
data/canvas/document_model.py (data storage)
data/canvas/canvas_state.py (state types)
controllers/editing_controller.py (editing logic)
renderers/canvas_renderer.py (rendering)
    ↓ uses
edit/selection_manager.py
api/netobjs/* (Place, Transition, Arc)
```

**Key principle:** Data layer depends on nothing but API objects and state types.

---

## Alternative Considered: `src/shypn/canvas/`

**Pros:**
- Shorter path
- Clear top-level organization

**Cons:**
- Canvas is fundamentally a data structure
- `data/` already exists and holds model code
- Would create confusion: is canvas UI or data?

**Decision:** Keep under `src/shypn/data/canvas/` because:
1. Canvas manages document **data state**
2. Aligns with existing `data/` directory
3. Clear separation: `data/` = models, `helpers/` = UI loaders

---

## Summary

### Proposed Structure:
```
src/shypn/data/canvas/
├── __init__.py
├── canvas_state.py          # ~100 lines - State enums and types
├── document_model.py         # ~250 lines - Pure data model
└── document_canvas.py        # ~450 lines - Main canvas controller
```

### Total: ~800 lines (well-organized, single responsibility each)

### Benefits:
- ✅ Clear separation of concerns
- ✅ Each file has one purpose
- ✅ Easy to find where logic lives
- ✅ Testable in isolation
- ✅ Follows existing directory structure

---

## Next Steps

1. **Create directory structure** ✋ (waiting for your approval)
2. Implement `canvas_state.py` (enums and types)
3. Implement `document_model.py` (data model)
4. Implement `document_canvas.py` (controller)
5. Update loader to use `DocumentCanvas`

**Do you approve this structure and naming?** Any changes you'd like?
