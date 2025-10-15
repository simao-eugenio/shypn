# OOP Refactoring Guide - Clean Architecture

**Project**: Shypn OOP Restructuring  
**Goal**: Proper class hierarchy, minimal loader code, clean separation of concerns  
**Status**: Planning Phase  
**Date**: October 14, 2025

---

## Executive Summary

### Architecture Note: UI/Implementation Separation

**CRITICAL**: This project uses **complete UI/implementation decoupling**:
- **UI Definitions** (`.ui` files): Located in `/ui/` at repo root
- **Python Implementation**: Located in `src/shypn/ui/` 
- **Business Logic**: Located in `src/shypn/core/`

The `.ui` files are GTK/Glade XML definitions created with a visual designer.
Python code loads these files and adds behavior (event handlers, controllers).

**Benefits**:
- Designers can edit UI without touching Python code
- UI changes don't require code changes (unless adding new widgets)
- Easy to swap UI implementations (GTK → Qt → Web)
- Clear separation: visual design vs behavior

### Current Problems

1. **Loaders do too much** - Business logic mixed with UI loading
2. **Flat module structure** - No clear class hierarchy
3. **God classes** - `ModelCanvasManager` has 1,266 lines!
4. **Tight coupling** - Components directly reference each other
5. **No interfaces** - Abstract base classes rarely used
6. **Code duplication** - Similar patterns repeated

### Solution Principles

1. **Loaders = UI Only** - Load GTK widgets, wire signals, that's all
2. **Business Logic = Separate Classes** - One responsibility per class
3. **Class Hierarchy** - Base classes, interfaces, inheritance
4. **Dependency Injection** - Pass dependencies via constructors
5. **Module Organization** - Logical grouping by domain

---

## Target Architecture

### Directory Structure (Proposed)

**IMPORTANT**: UI files (.ui) are in `/ui/` at repo root, completely decoupled from Python implementation!

```
ui/                                # UI DEFINITIONS (Glade/GTK files) - REPO ROOT
├── main/
│   └── main_window.ui             # Main window UI definition
├── panels/
│   ├── left_panel.ui              # Left panel UI definition
│   ├── right_panel.ui             # Right panel UI definition
│   └── pathway_panel.ui           # Pathway panel UI definition
├── canvas/
│   └── model_canvas.ui            # Canvas UI definition
├── dialogs/
│   ├── place_prop_dialog.ui       # Place properties dialog
│   ├── transition_prop_dialog.ui  # Transition properties dialog
│   └── arc_prop_dialog.ui         # Arc properties dialog
├── palettes/
│   ├── edit_palette.ui            # Edit palette UI
│   ├── zoom.ui                    # Zoom palette UI
│   └── edit_tools_palette.ui      # Edit tools palette UI
└── simulate/
    ├── simulate_palette.ui        # Simulate palette UI
    └── simulate_tools_palette.ui  # Simulate tools palette UI

src/shypn/                         # PYTHON IMPLEMENTATION
├── core/                          # Core business logic
│   ├── __init__.py
│   ├── state/                     # State management
│   │   ├── __init__.py
│   │   ├── canvas_state.py        # CanvasStateManager
│   │   ├── document_state.py      # DocumentState
│   │   ├── viewport_state.py      # ViewportState
│   │   ├── application_state.py   # ApplicationState (mode, tool)
│   │   └── simulation_state.py    # SimulationState
│   │
│   ├── models/                    # Data models
│   │   ├── __init__.py
│   │   ├── document.py            # Document model
│   │   ├── viewport.py            # Viewport calculations
│   │   └── project.py             # Project (multiple documents)
│   │
│   ├── controllers/               # Business logic controllers
│   │   ├── __init__.py
│   │   ├── canvas_controller.py   # Canvas operations
│   │   ├── selection_controller.py # Selection management
│   │   ├── zoom_controller.py     # Zoom/pan operations
│   │   └── mode_controller.py     # Mode coordination
│   │
│   └── services/                  # Application services
│       ├── __init__.py
│       ├── file_service.py        # File operations
│       ├── export_service.py      # Export operations
│       └── validation_service.py  # Model validation
│
├── ui/                            # UI Python implementation (loads from /ui/)
│   ├── __init__.py
│   ├── base/                      # Base UI classes
│   │   ├── __init__.py
│   │   ├── base_panel.py          # Abstract panel base
│   │   ├── base_dialog.py         # Abstract dialog base
│   │   └── base_palette.py        # Abstract palette base
│   │
│   ├── panels/                    # Panel Python implementations
│   │   ├── __init__.py
│   │   ├── left_panel.py          # LeftPanel class (loads /ui/panels/left_panel.ui)
│   │   ├── right_panel.py         # RightPanel class (loads /ui/panels/right_panel.ui)
│   │   ├── pathway_panel.py       # PathwayPanel class (loads /ui/panels/pathway_panel.ui)
│   │   └── canvas_panel.py        # CanvasPanel class (loads /ui/canvas/model_canvas.ui)
│   │
│   ├── dialogs/                   # Dialog Python implementations
│   │   ├── __init__.py
│   │   ├── properties_dialog.py   # Properties dialog (loads /ui/dialogs/*.ui)
│   │   ├── settings_dialog.py     # Settings dialog
│   │   └── about_dialog.py        # About dialog
│   │
│   ├── palettes/                  # Palette Python implementations
│   │   ├── __init__.py
│   │   ├── swiss_palette.py       # SwissKnifePalette class
│   │   ├── edit_palette.py        # EditPalette class (loads /ui/palettes/edit_palette.ui)
│   │   └── simulate_palette.py    # SimulatePalette class (loads /ui/simulate/simulate_palette.ui)
│   │
│   └── widgets/                   # Custom widgets
│       ├── __init__.py
│       ├── canvas_widget.py       # Custom canvas drawing widget
│       ├── property_editor.py     # Property editor widget
│       └── color_picker.py        # Color picker widget
│
├── loaders/                       # MINIMAL loaders (UI loading only)
│   ├── __init__.py
│   ├── panel_loader.py            # Generic panel loader (loads from /ui/)
│   ├── dialog_loader.py           # Generic dialog loader (loads from /ui/)
│   └── main_window_loader.py      # Main window loader (loads from /ui/)
│
├── observers/                     # Observer pattern implementations
│   ├── __init__.py
│   ├── base_observer.py           # Abstract observer
│   ├── ui_observer.py             # UI update observer
│   ├── persistence_observer.py    # Auto-save observer
│   └── validation_observer.py     # Validation observer
│
├── events/                        # Event system
│   ├── __init__.py
│   ├── base_event.py              # Abstract event
│   ├── document_events.py         # Document-related events
│   ├── selection_events.py        # Selection events
│   └── mode_events.py             # Mode change events
│
├── data/                          # Data layer (keep existing)
│   ├── canvas/                    # Canvas data structures
│   ├── pathway/                   # Pathway data structures
│   └── simulation/                # Simulation data structures
│
└── helpers/                       # DEPRECATED - migrate out
    └── (move code to proper modules)
```

**Key Separation**:
- **UI Definitions** (`/ui/*.ui`) = GTK/Glade XML files (visual design)
- **Python Implementation** (`src/shypn/ui/*.py`) = Business logic + event handlers
- **Controllers** (`src/shypn/core/controllers/`) = Pure business logic
- **Loaders** (`src/shypn/loaders/`) = Load .ui files, create instances, minimal glue

---

## Refactoring Principles

### 1. Loaders = UI Loading ONLY

**Bad (Current)**:
```python
# helpers/model_canvas_loader.py (500+ lines!)
class ModelCanvasLoader:
    def __init__(self):
        self.manager = ModelCanvasManager()  # Creates business logic
        self._setup_canvas()
        self._setup_tools()
        self._setup_simulation()
        self._handle_file_operations()
        # ... 400 more lines of business logic
```

**Good (Target)**:
```python
# loaders/panel_loader.py (50 lines max!)
import os
from pathlib import Path

class PanelLoader:
    """Generic panel loader - UI construction only.
    
    Loads .ui files from /ui/ directory at repo root.
    """
    
    def __init__(self, ui_root: Path = None):
        """Initialize loader with UI root directory.
        
        Args:
            ui_root: Path to UI root (defaults to /ui/ at repo root)
        """
        if ui_root is None:
            # Get repo root: src/shypn/loaders -> ../../..
            repo_root = Path(__file__).parent.parent.parent.parent
            ui_root = repo_root / "ui"
        self.ui_root = ui_root
    
    def load_panel(self, ui_file: str, panel_class: Type[BasePanel], 
                   **dependencies) -> BasePanel:
        """Load UI and create panel instance with dependencies.
        
        Args:
            ui_file: Relative path from UI root (e.g., "panels/left_panel.ui")
            panel_class: Panel class to instantiate
            **dependencies: Dependencies to inject
        
        Returns:
            Panel instance with loaded UI
        """
        # Build full path: /ui/panels/left_panel.ui
        ui_path = self.ui_root / ui_file
        
        # Load GTK builder from .ui file
        builder = Gtk.Builder.new_from_file(str(ui_path))
        
        # Create panel instance with injected dependencies
        panel = panel_class(builder=builder, **dependencies)
        
        # Wire GTK signals to panel methods
        panel.connect_signals()
        
        return panel

# Usage:
loader = PanelLoader()  # Auto-finds /ui/ at repo root
canvas_panel = loader.load_panel(
    ui_file="canvas/model_canvas.ui",  # Loads from /ui/canvas/model_canvas.ui
    panel_class=CanvasPanel,
    state_manager=state_manager,
    controller=canvas_controller
)
```

---

### 2. Clear Class Hierarchy

**Base Classes** (Abstract):
```python
# ui/base/base_panel.py
from abc import ABC, abstractmethod
from gi.repository import Gtk

class BasePanel(ABC):
    """Abstract base class for all panels.
    
    Responsibilities:
    - Manage GTK builder and widgets
    - Wire signals to handlers
    - Coordinate with injected controllers
    - UI-only logic (no business logic!)
    """
    
    def __init__(self, builder: Gtk.Builder, **dependencies):
        """Initialize panel with GTK builder and dependencies.
        
        Args:
            builder: GTK builder with loaded UI
            **dependencies: Injected dependencies (controllers, services, etc.)
        """
        self.builder = builder
        self._dependencies = dependencies
        self._widgets = {}
        
        self._load_widgets()
        self._setup_ui()
    
    @abstractmethod
    def _load_widgets(self):
        """Load widgets from builder (must implement)."""
        pass
    
    @abstractmethod
    def connect_signals(self):
        """Connect GTK signals to handlers (must implement)."""
        pass
    
    @abstractmethod
    def _setup_ui(self):
        """Setup initial UI state (must implement)."""
        pass
    
    def get_widget(self, widget_id: str) -> Gtk.Widget:
        """Get widget by ID from builder."""
        if widget_id not in self._widgets:
            self._widgets[widget_id] = self.builder.get_object(widget_id)
        return self._widgets[widget_id]
    
    def get_dependency(self, dep_name: str):
        """Get injected dependency by name."""
        return self._dependencies.get(dep_name)
```

**Concrete Implementation**:
```python
# ui/panels/canvas_panel.py
from shypn.ui.base import BasePanel
from shypn.core.controllers import CanvasController

class CanvasPanel(BasePanel):
    """Canvas panel implementation.
    
    Loads UI from /ui/canvas/model_canvas.ui at repo root.
    
    Responsibilities:
    - Display canvas widget
    - Handle mouse/keyboard events
    - Delegate business logic to CanvasController
    """
    
    def __init__(self, builder, state_manager, canvas_controller):
        self.state_manager = state_manager
        self.canvas_controller = canvas_controller
        super().__init__(builder, 
                        state_manager=state_manager,
                        canvas_controller=canvas_controller)
    
    def _load_widgets(self):
        """Load canvas-specific widgets from /ui/canvas/model_canvas.ui."""
        self.drawing_area = self.get_widget('drawing_area')
        self.toolbar = self.get_widget('canvas_toolbar')
    
    def connect_signals(self):
        """Wire GTK signals."""
        self.drawing_area.connect('draw', self._on_draw)
        self.drawing_area.connect('button-press-event', self._on_button_press)
        self.drawing_area.connect('button-release-event', self._on_button_release)
        self.drawing_area.connect('motion-notify-event', self._on_motion)
        self.drawing_area.connect('scroll-event', self._on_scroll)
    
    def _setup_ui(self):
        """Setup initial canvas state."""
        self.drawing_area.set_size_request(800, 600)
        self.drawing_area.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.SCROLL_MASK
        )
    
    # Event Handlers - UI only, delegate to controller
    def _on_draw(self, widget, cr):
        """Handle draw event - delegate to controller."""
        self.canvas_controller.render(cr, widget)
    
    def _on_button_press(self, widget, event):
        """Handle button press - delegate to controller."""
        self.canvas_controller.handle_button_press(event)
    
    def _on_scroll(self, widget, event):
        """Handle scroll - delegate to controller."""
        self.canvas_controller.handle_scroll(event)
```

---

### 3. Controllers = Business Logic

**Canvas Controller** (Business Logic):
```python
# core/controllers/canvas_controller.py
from shypn.core.state import CanvasStateManager
from shypn.observers import BaseObserver

class CanvasController:
    """Canvas business logic controller.
    
    Responsibilities:
    - Coordinate canvas operations
    - Manage object creation/deletion
    - Handle tool operations
    - Notify state changes
    
    Does NOT:
    - Know about GTK widgets
    - Handle UI events directly
    - Contain rendering code
    """
    
    def __init__(self, state_manager: CanvasStateManager):
        self.state = state_manager
        self._current_tool = None
        self._temp_objects = []  # For preview during creation
    
    def set_tool(self, tool_name: str):
        """Set active tool."""
        self._current_tool = tool_name
        self.state.app_state.current_tool = tool_name
        self.state.notify_observers(ToolChangedEvent(tool_name))
    
    def handle_button_press(self, event):
        """Handle canvas click - business logic only."""
        # Convert screen to world coordinates
        world_x, world_y = self.state.viewport.screen_to_world(
            event.x, event.y
        )
        
        # Delegate to tool handler
        if self._current_tool == 'place':
            self._create_place(world_x, world_y)
        elif self._current_tool == 'transition':
            self._create_transition(world_x, world_y)
        elif self._current_tool == 'arc':
            self._handle_arc_creation(world_x, world_y, event)
        else:
            self._handle_selection(world_x, world_y, event)
    
    def _create_place(self, x: float, y: float):
        """Create place at coordinates."""
        place = self.state.add_place(x, y)
        # State manager notifies observers automatically
    
    def handle_scroll(self, event):
        """Handle zoom via scroll."""
        if event.direction == Gdk.ScrollDirection.UP:
            self.zoom_in(event.x, event.y)
        elif event.direction == Gdk.ScrollDirection.DOWN:
            self.zoom_out(event.x, event.y)
    
    def zoom_in(self, center_x: float, center_y: float):
        """Zoom in at point."""
        new_zoom = self.state.viewport.zoom * 1.1
        self.state.viewport.zoom_at_point(new_zoom, center_x, center_y)
        self.state.notify_observers(ViewportChangedEvent('zoom', new_zoom))
    
    def render(self, cr, widget):
        """Render canvas - delegates to renderer."""
        from shypn.rendering import CanvasRenderer
        
        renderer = CanvasRenderer(self.state)
        renderer.render(cr, widget)
```

---

### 4. Services = Stateless Operations

**File Service**:
```python
# core/services/file_service.py
from pathlib import Path
from typing import Optional
from shypn.core.state import CanvasStateManager

class FileService:
    """File operations service.
    
    Responsibilities:
    - Save/load files
    - Handle file formats
    - Manage file paths
    
    Stateless - operates on provided state manager.
    """
    
    def __init__(self):
        self.supported_formats = ['.shy', '.pnml', '.sbml']
    
    def save(self, state_manager: CanvasStateManager, 
             filepath: Path) -> bool:
        """Save state to file.
        
        Args:
            state_manager: State to save
            filepath: Target file path
            
        Returns:
            True if successful
        """
        try:
            # Get complete state
            data = state_manager.to_dict()
            
            # Serialize based on format
            if filepath.suffix == '.shy':
                self._save_shy(data, filepath)
            elif filepath.suffix == '.pnml':
                self._save_pnml(data, filepath)
            else:
                raise ValueError(f"Unsupported format: {filepath.suffix}")
            
            # Update state metadata
            state_manager.metadata.mark_saved(str(filepath))
            
            return True
        
        except Exception as e:
            print(f"Save failed: {e}")
            return False
    
    def load(self, filepath: Path) -> Optional[CanvasStateManager]:
        """Load state from file.
        
        Args:
            filepath: File to load
            
        Returns:
            Loaded state manager or None if failed
        """
        try:
            # Deserialize based on format
            if filepath.suffix == '.shy':
                data = self._load_shy(filepath)
            elif filepath.suffix == '.pnml':
                data = self._load_pnml(filepath)
            else:
                raise ValueError(f"Unsupported format: {filepath.suffix}")
            
            # Reconstruct state
            state_manager = CanvasStateManager.from_dict(data)
            
            return state_manager
        
        except Exception as e:
            print(f"Load failed: {e}")
            return None
    
    def _save_shy(self, data: dict, filepath: Path):
        """Save as .shy format (JSON)."""
        import json
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_shy(self, filepath: Path) -> dict:
        """Load .shy format (JSON)."""
        import json
        with open(filepath, 'r') as f:
            return json.load(f)
```

---

### 5. Observer Pattern

**Base Observer**:
```python
# observers/base_observer.py
from abc import ABC, abstractmethod
from shypn.events import BaseEvent

class BaseObserver(ABC):
    """Abstract base class for observers.
    
    Observers respond to state changes via events.
    """
    
    @abstractmethod
    def on_event(self, event: BaseEvent):
        """Handle state change event.
        
        Args:
            event: Event describing the state change
        """
        pass
    
    def can_handle(self, event: BaseEvent) -> bool:
        """Check if this observer handles this event type.
        
        Override to filter events.
        
        Args:
            event: Event to check
            
        Returns:
            True if this observer handles this event type
        """
        return True
```

**UI Observer** (Updates UI):
```python
# observers/ui_observer.py
from shypn.observers import BaseObserver
from shypn.events import ObjectAddedEvent, ObjectRemovedEvent, ViewportChangedEvent

class StatusBarObserver(BaseObserver):
    """Observer that updates status bar on state changes."""
    
    def __init__(self, status_bar):
        self.status_bar = status_bar
        self.context_id = status_bar.get_context_id("main")
    
    def can_handle(self, event):
        """Only handle specific event types."""
        return isinstance(event, (ObjectAddedEvent, ObjectRemovedEvent, 
                                 ViewportChangedEvent))
    
    def on_event(self, event):
        """Update status bar text."""
        if isinstance(event, ObjectAddedEvent):
            self._update_status(f"Added {event.obj.name}")
        
        elif isinstance(event, ObjectRemovedEvent):
            self._update_status(f"Removed {event.obj.name}")
        
        elif isinstance(event, ViewportChangedEvent):
            if event.property == 'zoom':
                self._update_status(f"Zoom: {event.value*100:.0f}%")
    
    def _update_status(self, message: str):
        """Push message to status bar."""
        self.status_bar.pop(self.context_id)
        self.status_bar.push(self.context_id, message)


class CanvasRedrawObserver(BaseObserver):
    """Observer that triggers canvas redraw on visual changes."""
    
    def __init__(self, drawing_area):
        self.drawing_area = drawing_area
    
    def on_event(self, event):
        """Queue redraw for any visual change."""
        self.drawing_area.queue_draw()
```

---

### 6. Event System

**Base Event**:
```python
# events/base_event.py
from abc import ABC
from datetime import datetime
from typing import Any

class BaseEvent(ABC):
    """Abstract base class for all events."""
    
    def __init__(self):
        self.timestamp = datetime.now()
    
    @property
    def event_type(self) -> str:
        """Get event type name."""
        return self.__class__.__name__


# events/document_events.py
from shypn.netobjs import PetriNetObject

class ObjectAddedEvent(BaseEvent):
    """Fired when object is added to document."""
    
    def __init__(self, obj: PetriNetObject):
        super().__init__()
        self.obj = obj


class ObjectRemovedEvent(BaseEvent):
    """Fired when object is removed from document."""
    
    def __init__(self, obj: PetriNetObject):
        super().__init__()
        self.obj = obj


class SelectionChangedEvent(BaseEvent):
    """Fired when selection changes."""
    
    def __init__(self, selected_objects: list):
        super().__init__()
        self.selected_objects = selected_objects


# events/mode_events.py
class ModeChangedEvent(BaseEvent):
    """Fired when application mode changes."""
    
    def __init__(self, old_mode: str, new_mode: str):
        super().__init__()
        self.old_mode = old_mode
        self.new_mode = new_mode
```

---

## Migration Strategy

### Phase 1: Create Infrastructure (Week 1)

1. **Create Base Classes**:
   ```
   src/shypn/ui/base/base_panel.py
   src/shypn/ui/base/base_dialog.py
   src/shypn/ui/base/base_palette.py
   ```

2. **Create Event System**:
   ```
   src/shypn/events/base_event.py
   src/shypn/events/document_events.py
   src/shypn/events/selection_events.py
   ```

3. **Create Observer System**:
   ```
   src/shypn/observers/base_observer.py
   src/shypn/observers/ui_observer.py
   ```

### Phase 2: Extract Controllers (Week 2-3)

1. **Extract from ModelCanvasManager**:
   ```python
   # Move business logic to controllers:
   ModelCanvasManager (1266 lines) →
       CanvasController (200 lines)
       SelectionController (100 lines)
       ZoomController (100 lines)
       ToolController (100 lines)
       RenderController (150 lines)
   
   # Keep only rendering:
   ModelCanvasManager → CanvasRenderer (300 lines)
   ```

2. **Create Controllers**:
   ```
   src/shypn/core/controllers/canvas_controller.py
   src/shypn/core/controllers/selection_controller.py
   src/shypn/core/controllers/zoom_controller.py
   src/shypn/core/controllers/tool_controller.py
   ```

### Phase 3: Extract Services (Week 4)

1. **Extract File Operations**:
   ```python
   # From helpers/persistency_manager.py →
   src/shypn/core/services/file_service.py
   ```

2. **Create Services**:
   ```
   src/shypn/core/services/file_service.py
   src/shypn/core/services/export_service.py
   src/shypn/core/services/validation_service.py
   ```

### Phase 4: Refactor Panels (Week 5-6)

1. **Convert Loaders to Panels**:
   ```python
   # helpers/model_canvas_loader.py (500 lines) →
   loaders/panel_loader.py (50 lines - generic)
   ui/panels/canvas_panel.py (150 lines - specific)
   ```

2. **Apply Pattern to All Panels**:
   - LeftPanel
   - RightPanel
   - PathwayPanel
   - SimulationPanel

### Phase 5: Cleanup (Week 7)

1. **Remove helpers/** directory
2. **Update imports throughout codebase**
3. **Update tests**
4. **Update documentation**

---

## Code Comparison

### Before (Current - BAD)

```python
# helpers/model_canvas_loader.py (500+ lines)
class ModelCanvasLoader:
    def __init__(self, ui_path=None):
        # Load UI
        self.builder = Gtk.Builder.new_from_file(ui_path)
        
        # Create business logic (WRONG - should be injected!)
        self.manager = ModelCanvasManager()
        
        # Load widgets
        self.notebook = self.builder.get_object('canvas_notebook')
        self.drawing_area = Gtk.DrawingArea()
        
        # Setup tools (WRONG - should be in controller!)
        self.current_tool = None
        self.tools = {}
        self._setup_tools()
        
        # Setup rendering (WRONG - should be separate!)
        self.drawing_area.connect('draw', self._on_draw)
        
        # Setup file operations (WRONG - should be in service!)
        self.persistency = None
        
        # ... 400 more lines of mixed concerns
    
    def _on_draw(self, widget, cr):
        """Rendering logic mixed with UI handling (WRONG!)"""
        # 100+ lines of cairo rendering code
        pass
    
    def _on_button_press(self, widget, event):
        """Business logic in UI handler (WRONG!)"""
        x, y = event.x, event.y
        
        # Coordinate transformation (should be in viewport!)
        world_x = (x / self.manager.zoom) - self.manager.pan_x
        
        # Object creation (should be in controller!)
        if self.current_tool == 'place':
            place = self.manager.add_place(world_x, world_y)
            # ... more business logic
```

### After (Target - GOOD)

```python
# loaders/panel_loader.py (50 lines - MINIMAL)
class PanelLoader:
    """Generic panel loader - UI construction ONLY."""
    
    def load_panel(self, ui_file, panel_class, **dependencies):
        """Load UI file and create panel with dependencies."""
        builder = Gtk.Builder.new_from_file(ui_file)
        panel = panel_class(builder=builder, **dependencies)
        panel.connect_signals()
        return panel


# ui/panels/canvas_panel.py (150 lines - UI ONLY)
class CanvasPanel(BasePanel):
    """Canvas panel - UI handling ONLY."""
    
    def __init__(self, builder, canvas_controller):
        self.canvas_controller = canvas_controller
        super().__init__(builder, canvas_controller=canvas_controller)
    
    def _load_widgets(self):
        self.drawing_area = self.get_widget('drawing_area')
    
    def connect_signals(self):
        self.drawing_area.connect('draw', self._on_draw)
        self.drawing_area.connect('button-press-event', self._on_button_press)
    
    def _on_draw(self, widget, cr):
        """Delegate to controller."""
        self.canvas_controller.render(cr, widget)
    
    def _on_button_press(self, widget, event):
        """Delegate to controller."""
        self.canvas_controller.handle_button_press(event)


# core/controllers/canvas_controller.py (200 lines - BUSINESS LOGIC)
class CanvasController:
    """Canvas business logic - coordinates operations."""
    
    def __init__(self, state_manager, renderer):
        self.state = state_manager
        self.renderer = renderer
    
    def handle_button_press(self, event):
        """Business logic for button press."""
        # Get world coordinates from state
        world_x, world_y = self.state.viewport.screen_to_world(
            event.x, event.y
        )
        
        # Delegate to appropriate handler
        tool = self.state.app_state.current_tool
        if tool == 'place':
            self._create_place(world_x, world_y)
    
    def _create_place(self, x, y):
        """Business logic for place creation."""
        place = self.state.add_place(x, y)
        # State notifies observers automatically
    
    def render(self, cr, widget):
        """Delegate to renderer."""
        self.renderer.render(cr, widget, self.state)


# rendering/canvas_renderer.py (300 lines - RENDERING ONLY)
class CanvasRenderer:
    """Canvas rendering - Cairo code ONLY."""
    
    def render(self, cr, widget, state):
        """Render canvas from state."""
        # Grid
        self._render_grid(cr, state.viewport)
        
        # Objects
        for place in state.document.places:
            self._render_place(cr, place, state.viewport)
        
        for transition in state.document.transitions:
            self._render_transition(cr, transition, state.viewport)
```

---

## Benefits Summary

### Before Refactoring ❌
- **500+ line loaders** - do everything
- **God classes** - ModelCanvasManager 1,266 lines
- **Mixed concerns** - UI + business + rendering + persistence
- **Tight coupling** - hard to test
- **No reuse** - everything is custom
- **Hard to maintain** - unclear responsibilities

### After Refactoring ✅
- **50 line loaders** - just load UI
- **Small classes** - 100-200 lines each
- **Clear separation** - UI / business / rendering / persistence
- **Loose coupling** - dependency injection
- **High reuse** - base classes, services
- **Easy to maintain** - one responsibility per class

### Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Loader LOC | 500+ | 50 | 90% reduction |
| Max Class LOC | 1,266 | 300 | 76% reduction |
| Classes >500 LOC | 3 | 0 | 100% elimination |
| Test Coverage | ~30% | >90% | 3x increase |
| Coupling | High | Low | Dependency injection |

---

## Quick Start Checklist

### Week 1: Setup
- [ ] Create `src/shypn/ui/base/` directory
- [ ] Create `src/shypn/core/controllers/` directory
- [ ] Create `src/shypn/core/services/` directory
- [ ] Create `src/shypn/observers/` directory
- [ ] Create `src/shypn/events/` directory
- [ ] Write base classes (BasePanel, BaseObserver, BaseEvent)

### Week 2: Extract Controllers
- [ ] Extract CanvasController from ModelCanvasLoader
- [ ] Extract SelectionController
- [ ] Extract ZoomController
- [ ] Test controllers independently

### Week 3: Extract Services
- [ ] Extract FileService from persistency_manager
- [ ] Extract ValidationService
- [ ] Test services independently

### Week 4: Refactor First Panel
- [ ] Convert model_canvas_loader to CanvasPanel
- [ ] Create minimal PanelLoader
- [ ] Test integration
- [ ] Document pattern

### Week 5-6: Apply to All Panels
- [ ] LeftPanel
- [ ] RightPanel
- [ ] PathwayPanel
- [ ] Test all panels

### Week 7: Cleanup
- [ ] Remove helpers/ directory
- [ ] Update all imports
- [ ] Update tests
- [ ] Final review

---

## Success Criteria

- [ ] All loaders <100 lines
- [ ] No class >500 lines
- [ ] All classes have single responsibility
- [ ] >90% test coverage
- [ ] Zero tight coupling
- [ ] All business logic in controllers/services
- [ ] All UI logic in panels/widgets
- [ ] Complete documentation

---

**Document Status**: Complete  
**Next Steps**: Begin Week 1 setup  
**Owner**: TBD  
**Date**: October 14, 2025
