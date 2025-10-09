# SwissKnifePalette - Unified Multi-Mode Tool System

**Date:** October 9, 2025  
**Author:** Copilot AI Assistant  
**Status:** Design Phase  

---

## 1. Executive Summary

The **SwissKnifePalette** is a unified, expandable tool interface that consolidates all tools for a single operational mode (Edit OR Simulate) into an animated, multi-category palette system. It replaces the current scattered palette architecture with a cohesive OOP design featuring smooth animations, CSS-styled containers, and minimal loader code.

### Key Design Principles

1. **OOP Architecture**: Classes and subclasses in separate modules
2. **Single Mode Operation**: Palette manages ONE mode at a time (Edit OR Simulate)
3. **Mode Selection External**: User chooses mode via existing [E]/[S] buttons BEFORE palette appears
4. **Animated Transitions**: Smooth sliding sub-palettes that reveal tools
5. **CSS-Styled**: All containers support CSS for consistent theming
6. **Minimal Loader Code**: Business logic in classes, not in loaders
7. **Standalone Test Bed**: Develop under `dev/swissknife_testbed/` with placeholder tools
8. **Extensible**: Easy to add new tools and sub-palettes
9. **Tool Reuse**: Tools can appear in multiple contexts (edit/create, edit/layout)

---

## 2. Current Architecture Analysis

### Existing Palette System

**Current Implementation:**
- **PaletteManager**: Central coordinator for floating palettes
- **BasePalette**: Abstract base class with GtkRevealer + GtkEventBox + GtkBox
- **ToolsPalette**: Place, Transition, Arc tools
- **OperationsPalette**: Select, Lasso, Undo, Redo
- **SimulatePalette**: Mode toggle button [S]
- **SimulateToolsPalette**: Step, Play, Reset, Chart controls

**Strengths:**
✅ Good OOP foundation with abstract base classes  
✅ CSS-enabled containers (GtkEventBox)  
✅ Revealer-based animations  
✅ Clear signal-based communication  
✅ Separation of concerns (palette manager, individual palettes)

**Limitations:**
⚠️ Palettes are independent floating widgets  
⚠️ No unified main palette that groups sub-palettes  
⚠️ Mode switching is handled in loader, not in palette logic  
⚠️ No sub-palette sliding/reveal animations  
⚠️ Tools are duplicated across contexts (no reuse)  
⚠️ Position management is manual  

### Current Mode Switching (in model_canvas_loader.py)

```python
# Edit Mode: Show [E] button, show edit palettes (tools, operations)
# Simulate Mode: Show [S] button, show simulate tools palette
```

**Problem:** Mode logic is in the loader (400+ lines), not in palette classes.

---

## 3. SwissKnifePalette Architecture - REVISED

### 3.1 Key Insight: Mode Selection is External

**IMPORTANT CHANGE:** The SwissKnifePalette does NOT switch between Edit/Simulate modes itself. That choice happens BEFORE the palette appears:

```
User Flow:
1. User clicks [E] button → Enter Edit Mode
   └─> SwissKnifePalette(mode='edit') appears with Edit categories
   
2. User clicks [S] button → Enter Simulate Mode  
   └─> SwissKnifePalette(mode='simulate') appears with Simulate categories
```

**Why this is better:**
- ✅ No redundant mode switcher inside palette
- ✅ Existing [E]/[S] buttons already handle mode choice
- ✅ Simpler architecture: palette manages ONE mode at a time
- ✅ Clearer separation: mode selection (external) vs tool selection (palette)

### 3.2 Big Picture - Single Mode Hierarchy

**When in EDIT Mode:**
```
SwissKnifePalette (Edit Mode)
│
├── Category Buttons:
│   ├── [Create] [Edit] [Layout] [Transform] [View]
│
└── Sub-Palettes (one visible at a time):
    │
    ├── CREATE TOOLS
    │   ├── Place (P)
    │   ├── Transition (T)
    │   └── Arc (A)
    │
    ├── EDIT OPERATIONS
    │   ├── Select (S)
    │   ├── Lasso (L)
    │   ├── Undo (U)
    │   └── Redo (R)
    │
    ├── LAYOUT TOOLS
    │   ├── Auto Layout
    │   ├── Hierarchical
    │   ├── Force-Directed
    │   ├── Circular
    │   └── Orthogonal
    │
    ├── TRANSFORM TOOLS
    │   ├── Parallel Arc
    │   ├── Inhibitor Arc
    │   ├── Read Arc
    │   └── Reset Arc
    │
    └── VIEW TOOLS
        ├── Zoom In
        ├── Zoom Out
        ├── Fit to Window
        └── Center View
```

**When in SIMULATE Mode:**
```
SwissKnifePalette (Simulate Mode)
│
├── Category Buttons:
│   ├── [Control] [Visualize] [Analyze]
│
└── Sub-Palettes (one visible at a time):
    │
    ├── SIMULATION CONTROL
    │   ├── Step
    │   ├── Play/Pause
    │   ├── Reset
    │   └── Speed Control
    │
    ├── VISUALIZATION
    │   ├── Show Tokens
    │   ├── Show Marking
    │   ├── Show Metrics
    │   └── Chart View
    │
    └── ANALYSIS
        ├── Save State
        ├── Load State
        ├── Export Data
        └── Statistics
```

### 3.3 Visual Design - REVISED (No Mode Switcher)

```
User clicks [E] button (existing, outside palette)
    ↓
┌─────────────────────────────────────────────────────┐
│  Canvas (Drawing Area)                              │
│                                                     │
│                                                     │
│  [SwissKnifePalette appears - EDIT MODE]           │
│  ┌───────────────────────────────────────┐         │
│  │ [Create] [Edit] [Layout] [Transform]  │◄── Categories  │
│  └───────────────────────────────────────┘         │
│       ↓ (User clicks "Create")                     │
│  ┌─────────────────────┐                           │
│  │  P  │  T  │  A  │   │ ◄── Sub-palette slides down │
│  └─────────────────────┘                           │
│                                                     │
└─────────────────────────────────────────────────────┘

User clicks [S] button (existing, outside palette)
    ↓
┌─────────────────────────────────────────────────────┐
│  Canvas (Drawing Area)                              │
│                                                     │
│                                                     │
│  [SwissKnifePalette appears - SIMULATE MODE]       │
│  ┌───────────────────────────────────┐             │
│  │ [Control] [Visualize] [Analyze]   │◄── Categories    │
│  └───────────────────────────────────┘             │
│       ↓ (User clicks "Control")                    │
│  ┌────────────────────────────────┐                │
│  │ Step │ Play │ Reset │ Speed    │ ◄── Sub-palette   │
│  └────────────────────────────────┘                │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Key Points:**
- Existing [E] and [S] buttons remain (not part of SwissKnifePalette)
- Palette is instantiated with a specific mode: `SwissKnifePalette(mode='edit')`
- No mode switching inside palette - just category/sub-palette management

### 3.4 Animation Behavior - REVISED (No Mode Animations)

**Sub-Palette Animation (Only Animation Type):**

1. **User clicks category button** (e.g., "Create")
2. **If another sub-palette is open:**
   - Current sub-palette slides DOWN (hide - collapses down)
   - Wait for animation to complete (200ms)
3. **Selected sub-palette slides UP** (reveal - expands upward from bottom)
4. **Category button highlights**

**Animation Direction:**
- **Reveal**: SLIDE_UP (sub-palette grows upward from bottom)
- **Hide**: Collapses down (sub-palette shrinks downward)
- This creates a natural "rising from the bottom" effect

**Smooth Transitions:**
- Use GtkRevealer with SLIDE_UP transition type
- Transition duration: 200ms (fast and fluid)
- Easing: GTK default (ease-out)
- Sequential animations: Hide first, then show (no overlap)

**Example Timeline:**
```
t=0ms:    User clicks "Edit" category
t=0ms:    Current sub-palette ("Create") starts collapsing DOWN
t=200ms:  "Create" sub-palette fully hidden
t=200ms:  "Edit" sub-palette starts sliding UP from bottom
t=400ms:  "Edit" sub-palette fully visible (expanded upward)
Total:    400ms for complete switch
```

**Special Case - Same Category Clicked:**
```
t=0ms:    User clicks already-active "Create" category
t=0ms:    "Create" sub-palette collapses DOWN (toggle off)
t=200ms:  Fully hidden
No show animation (category deactivated)
```

---

## 4. OOP Design - Class Hierarchy - REVISED

### 4.1 Module Structure - SIMPLIFIED

```
src/shypn/dev/swissknife/
├── __init__.py                      # Module exports
├── base.py                          # Abstract base classes
│   ├── BaseTool                     # Individual tool button
│   └── BaseSubPalette              # Sub-palette container
│
├── main_palette.py                  # SwissKnifePalette (main container)
├── animation_controller.py          # Animation orchestration
├── tool_registry.py                 # Tool registration and reuse
│
├── subpalettes/                     # Sub-palette implementations
│   ├── __init__.py
│   # Edit Mode Sub-Palettes:
│   ├── create_tools.py             # Place, Transition, Arc
│   ├── edit_operations.py          # Select, Lasso, Undo, Redo
│   ├── layout_tools.py             # Layout algorithms
│   ├── transform_tools.py          # Arc transformations
│   ├── view_tools.py               # Zoom, Pan, Center
│   # Simulate Mode Sub-Palettes:
│   ├── simulation_control.py       # Step, Play, Reset
│   ├── visualization.py            # Charts, Metrics
│   └── analysis.py                 # Export, Statistics
│
├── tools/                           # Individual tool implementations
│   ├── __init__.py
│   ├── place_tool.py               # Place creation tool
│   ├── transition_tool.py          # Transition creation tool
│   ├── arc_tool.py                 # Arc creation tool
│   ├── select_tool.py              # Selection tool
│   └── ...                         # Other tools
│
└── styles/                          # CSS styling modules
    ├── __init__.py
    ├── base_styles.py              # Global CSS
    ├── edit_styles.py              # Edit mode CSS
    └── simulate_styles.py          # Simulate mode CSS
```

**REMOVED** (no longer needed):
- ❌ `mode_switcher.py` - Redundant, handled externally
- ❌ `modes/` directory - Not needed, mode is constructor parameter
- ❌ `modes/edit_mode.py` - Logic moved into main_palette.py
- ❌ `modes/simulate_mode.py` - Logic moved into main_palette.py

### 4.2 Class Diagram - SIMPLIFIED

```
┌─────────────────────────────────────┐
│       SwissKnifePalette             │
│  (Single mode, manages sub-palettes)│
│  __init__(mode='edit' or 'simulate')│
└─────────────┬───────────────────────┘
              │
              ├─ AnimationController (sequential animations)
              │
              ├─ ToolRegistry (tool reuse)
              │
              └─ SubPalettes (mode-specific)
                  │
                  ├─ IF mode='edit':
                  │   ├─ CreateToolsSubPalette
                  │   ├─ EditOperationsSubPalette
                  │   ├─ LayoutToolsSubPalette
                  │   ├─ TransformToolsSubPalette
                  │   └─ ViewToolsSubPalette
                  │
                  └─ IF mode='simulate':
                      ├─ SimulationControlSubPalette
                      ├─ VisualizationSubPalette
                      └─ AnalysisSubPalette
```

### 4.3 Key Classes - REVISED

#### SwissKnifePalette (main_palette.py)

```python
class SwissKnifePalette(GObject.GObject):
    """Main unified palette for a single operational mode.
    
    Responsibilities:
    - Display category buttons for the specified mode
    - Manage sub-palette lifecycle (show/hide with animations)
    - Handle category button clicks
    - Apply CSS styling
    - Emit signals for tool selection
    
    Signals:
        category-selected(str): Emitted when category button clicked
        tool-activated(str): Emitted when tool is activated
        sub-palette-shown(str): Emitted when sub-palette reveals
        sub-palette-hidden(str): Emitted when sub-palette hides
    """
    
    def __init__(self, mode: str):
        """Initialize SwissKnifePalette for specified mode.
        
        Args:
            mode: 'edit' or 'simulate'
        """
        self.mode = mode
        self.sub_palettes = {}
        self.category_buttons = {}
        self.active_sub_palette = None
        self.animation_controller = AnimationController()
        self.tool_registry = ToolRegistry()
        
        # Create widget structure
        self._create_structure()
        
        # Register mode-specific sub-palettes
        self._register_sub_palettes()
        
        # Apply CSS
        self._apply_css()
    
    def _create_structure(self):
        """Create palette widget hierarchy."""
        # GtkBox (vertical) for category buttons + sub-palette area
        # GtkBox (horizontal) for category buttons
        # GtkRevealer for each sub-palette
        pass
    
    def _register_sub_palettes(self):
        """Register sub-palettes based on mode."""
        if self.mode == 'edit':
            self._register_edit_sub_palettes()
        elif self.mode == 'simulate':
            self._register_simulate_sub_palettes()
    
    def _register_edit_sub_palettes(self):
        """Register Edit mode sub-palettes."""
        from shypn.dev.swissknife.subpalettes import (
            CreateToolsSubPalette,
            EditOperationsSubPalette,
            LayoutToolsSubPalette,
            TransformToolsSubPalette,
            ViewToolsSubPalette
        )
        
        self.sub_palettes['create'] = CreateToolsSubPalette()
        self.sub_palettes['edit'] = EditOperationsSubPalette()
        self.sub_palettes['layout'] = LayoutToolsSubPalette()
        self.sub_palettes['transform'] = TransformToolsSubPalette()
        self.sub_palettes['view'] = ViewToolsSubPalette()
        
        # Create category buttons
        self.category_buttons['create'] = self._create_category_button('Create')
        self.category_buttons['edit'] = self._create_category_button('Edit')
        self.category_buttons['layout'] = self._create_category_button('Layout')
        self.category_buttons['transform'] = self._create_category_button('Transform')
        self.category_buttons['view'] = self._create_category_button('View')
    
    def _register_simulate_sub_palettes(self):
        """Register Simulate mode sub-palettes."""
        from shypn.dev.swissknife.subpalettes import (
            SimulationControlSubPalette,
            VisualizationSubPalette,
            AnalysisSubPalette
        )
        
        self.sub_palettes['control'] = SimulationControlSubPalette()
        self.sub_palettes['visualize'] = VisualizationSubPalette()
        self.sub_palettes['analyze'] = AnalysisSubPalette()
        
        # Create category buttons
        self.category_buttons['control'] = self._create_category_button('Control')
        self.category_buttons['visualize'] = self._create_category_button('Visualize')
        self.category_buttons['analyze'] = self._create_category_button('Analyze')
    
    def show_sub_palette(self, category_id: str):
        """Show sub-palette for category with animation."""
        if category_id not in self.sub_palettes:
            return
        
        target_palette = self.sub_palettes[category_id]
        
        # If clicking same category, toggle off
        if self.active_sub_palette == target_palette:
            self.hide_current_sub_palette()
            return
        
        # Hide current, then show new
        if self.active_sub_palette:
            self.animation_controller.animate_sub_palette_switch(
                from_palette=self.active_sub_palette,
                to_palette=target_palette,
                callback=lambda: self._on_sub_palette_switched(target_palette)
            )
        else:
            # No current palette, just show
            self.animation_controller.animate_sub_palette_show(
                palette=target_palette,
                callback=lambda: self._on_sub_palette_shown(target_palette)
            )
    
    def hide_current_sub_palette(self):
        """Hide currently active sub-palette."""
        if self.active_sub_palette:
            self.animation_controller.animate_sub_palette_hide(
                palette=self.active_sub_palette,
                callback=lambda: self._on_sub_palette_hidden()
            )
    
    def get_widget(self) -> Gtk.Widget:
        """Get root widget (main container)."""
        return self.main_container
```

#### BaseSubPalette (base.py) - NO CHANGES

```python
class BaseSubPalette(ABC):
    """Abstract base class for sub-palettes.
    
    Similar to existing BasePalette, but designed for sub-palette behavior.
    
    Responsibilities:
    - Create tool buttons
    - Handle tool activation
    - Emit tool-selected signals
    - Apply sub-palette-specific CSS
    """
    
    def __init__(self, palette_id: str, category_name: str):
        self.palette_id = palette_id
        self.category_name = category_name
        self.tools = {}
        self.revealer = None
        
        self._create_structure()
        self._create_tools()
        self._connect_signals()
        self._apply_css()
    
    @abstractmethod
    def _create_tools(self):
        """Create tool buttons for this sub-palette."""
        pass
    
    @abstractmethod
    def _connect_signals(self):
        """Connect tool button signals."""
        pass
    
    @abstractmethod
    def _get_css(self) -> bytes:
        """Get CSS styling for this sub-palette."""
        pass
    
    def show(self):
        """Reveal sub-palette with slide-down animation."""
        self.revealer.set_reveal_child(True)
    
    def hide(self):
        """Hide sub-palette with slide-up animation."""
        self.revealer.set_reveal_child(False)
    
    def get_widget(self) -> Gtk.Widget:
        """Get root widget (revealer)."""
        return self.revealer
```

#### BaseTool (base.py) - NO CHANGES

```python
class BaseTool(ABC):
    """Abstract base class for individual tools.
    
    Represents a single tool (e.g., Place tool, Select tool).
    Can be reused across multiple sub-palettes.
    
    Responsibilities:
    - Create tool button
    - Handle tool activation/deactivation
    - Emit tool-specific signals
    - Provide tool metadata (name, icon, tooltip)
    """
    
    def __init__(self, tool_id: str, tool_name: str):
        self.tool_id = tool_id
        self.tool_name = tool_name
        self.button = None
        
        self._create_button()
    
    @abstractmethod
    def _create_button(self) -> Gtk.Widget:
        """Create tool button widget."""
        pass
    
    @abstractmethod
    def get_tooltip(self) -> str:
        """Get tool tooltip text."""
        pass
    
    @abstractmethod
    def on_activated(self):
        """Called when tool is activated."""
        pass
    
    @abstractmethod
    def on_deactivated(self):
        """Called when tool is deactivated."""
        pass
    
    def get_button(self) -> Gtk.Widget:
        """Get tool button widget."""
        return self.button
```

#### AnimationController (animation_controller.py)

```python
class AnimationController:
    """Orchestrates palette animations.
    
    Responsibilities:
    - Queue animation sequences
    - Prevent overlapping animations
    - Coordinate timing
    - Handle animation callbacks
    """
    
    def __init__(self):
        self.animation_queue = []
        self.is_animating = False
    
    def animate_mode_switch(self, from_mode: str, to_mode: str, 
                           from_widget: Gtk.Widget, to_widget: Gtk.Widget,
                           callback: Optional[Callable] = None):
        """Animate mode switch transition."""
        pass
    
    def animate_sub_palette_show(self, palette: BaseSubPalette,
                                 callback: Optional[Callable] = None):
        """Animate sub-palette reveal (slide down)."""
        pass
    
    def animate_sub_palette_hide(self, palette: BaseSubPalette,
                                 callback: Optional[Callable] = None):
        """Animate sub-palette hide (slide up)."""
        pass
    
    def animate_sub_palette_switch(self, from_palette: BaseSubPalette,
                                   to_palette: BaseSubPalette,
                                   callback: Optional[Callable] = None):
        """Animate switching between sub-palettes (hide then show)."""
        pass
```

#### ToolRegistry (tool_registry.py)

```python
class ToolRegistry:
    """Central registry for tool reuse.
    
    Allows tools to appear in multiple sub-palettes without duplication.
    
    Example:
        - Select tool appears in: Edit Operations, View Tools
        - Zoom tools appear in: View Tools, Simulate Visualization
    """
    
    def __init__(self):
        self.tools = {}
    
    def register_tool(self, tool: BaseTool):
        """Register a tool for reuse."""
        self.tools[tool.tool_id] = tool
    
    def get_tool(self, tool_id: str) -> Optional[BaseTool]:
        """Get tool by ID."""
        return self.tools.get(tool_id)
    
    def create_tool_button(self, tool_id: str) -> Optional[Gtk.Widget]:
        """Create a button for a registered tool (can be used multiple times)."""
        tool = self.get_tool(tool_id)
        if tool:
            return tool.get_button()
        return None
    
    def list_tools(self, mode: Optional[str] = None) -> List[str]:
        """List all registered tool IDs, optionally filtered by mode."""
        pass
```

---

## 5. GTK Container Strategy for CSS

### 5.1 Widget Hierarchy

```
GtkOverlay (canvas overlay)
└── GtkBox (vertical) [swissknife-container]
    ├── GtkBox (horizontal) [mode-switcher]
    │   ├── GtkToggleButton [E]
    │   └── GtkToggleButton [S]
    │
    └── GtkStack [mode-stack]
        ├── GtkBox (edit mode) [edit-mode-container]
        │   ├── GtkBox (horizontal) [category-buttons]
        │   │   ├── GtkButton [Create]
        │   │   ├── GtkButton [Edit]
        │   │   ├── GtkButton [Layout]
        │   │   ├── GtkButton [Transform]
        │   │   └── GtkButton [View]
        │   │
        │   └── GtkStack [sub-palette-stack]
        │       ├── GtkRevealer [create-tools-revealer]
        │       │   └── GtkEventBox [create-tools-palette]
        │       │       └── GtkBox [create-tools-content]
        │       │           ├── GtkToggleButton [P]
        │       │           ├── GtkToggleButton [T]
        │       │           └── GtkToggleButton [A]
        │       │
        │       ├── GtkRevealer [edit-operations-revealer]
        │       │   └── ...
        │       │
        │       └── ... (other sub-palettes)
        │
        └── GtkBox (simulate mode) [simulate-mode-container]
            └── ... (similar structure)
```

### 5.2 CSS Class Strategy

**CSS Classes:**
- `.swissknife-container`: Main container styling
- `.mode-switcher`: Mode toggle buttons container
- `.mode-button`: Style for [E] and [S] buttons
- `.mode-button.active`: Active mode button
- `.category-buttons`: Category button bar
- `.category-button`: Individual category button
- `.category-button.active`: Active category button
- `.sub-palette`: Base styling for all sub-palettes
- `.sub-palette.create-tools`: Specific styling for create tools
- `.sub-palette.edit-operations`: Specific styling for edit ops
- `.tool-button`: Base styling for tool buttons
- `.tool-button.toggle`: Toggle-style tool buttons
- `.tool-button.action`: Action-style tool buttons

**CSS File Structure:**
```css
/* base_styles.css - Global SwissKnifePalette styles */
.swissknife-container {
    background: linear-gradient(to bottom, #f5f5f5, #d8d8d8);
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
}

.mode-switcher {
    padding: 4px;
    background: rgba(255, 255, 255, 0.3);
    border-bottom: 1px solid #999;
}

.mode-button {
    min-width: 40px;
    min-height: 40px;
    transition: all 200ms ease;
}

.mode-button.active {
    background: linear-gradient(to bottom, #4a9eff, #2e7ad6);
    color: white;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
}

.category-buttons {
    padding: 4px;
    spacing: 4px;
}

.category-button {
    min-width: 80px;
    min-height: 36px;
    transition: all 200ms ease;
}

.category-button.active {
    background: linear-gradient(to bottom, #6ab04c, #4a9034);
    color: white;
}

.sub-palette {
    margin-top: 4px;
    padding: 8px;
    background: rgba(255, 255, 255, 0.8);
    border-radius: 4px;
}

.tool-button {
    min-width: 40px;
    min-height: 40px;
    margin: 2px;
    transition: all 200ms ease;
}

.tool-button.toggle:checked {
    background: linear-gradient(to bottom, #ffa502, #e67e00);
    color: white;
}

.tool-button:hover {
    background: rgba(255, 255, 255, 0.9);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
```

### 5.3 Why This Container Strategy?

**GtkStack for Mode Switching:**
- Smooth cross-fade between Edit and Simulate modes
- Only one mode visible at a time
- Easy to extend with more modes

**GtkRevealer for Sub-Palettes:**
- Smooth slide-up/slide-down animations
- Built-in animation support
- No manual animation code needed

**GtkEventBox for CSS:**
- Receives events (clicks, hovers)
- Supports all CSS properties
- Better than GtkFrame for custom styling

**GtkBox for Layout:**
- Flexible spacing and alignment
- Easy to add/remove widgets
- Supports both horizontal and vertical orientation

---

## 6. Integration with Existing Code

### 6.1 Minimal Changes to Loader

**Current Loader Code (model_canvas_loader.py):**
```python
# 400+ lines of mode switching, palette management
```

**New Loader Code:**
```python
from shypn.dev.swissknife import SwissKnifePalette

class ModelCanvasLoader:
    def _setup_swissknife_palette(self, overlay, manager):
        """Setup SwissKnifePalette (replaces all palette setup)."""
        
        # Create SwissKnifePalette
        self.swissknife = SwissKnifePalette(overlay)
        
        # Connect signals
        self.swissknife.connect('mode-changed', self._on_mode_changed, manager)
        self.swissknife.connect('tool-activated', self._on_tool_activated, manager)
        
        # Set initial mode
        self.swissknife.set_mode('edit')
    
    def _on_mode_changed(self, palette, mode, manager):
        """Handle mode change."""
        if mode == 'edit':
            # Enable edit-specific canvas handlers
            pass
        elif mode == 'simulate':
            # Enable simulation-specific canvas handlers
            pass
    
    def _on_tool_activated(self, palette, mode, tool_name, manager):
        """Handle tool activation."""
        if tool_name == 'place':
            # Activate place creation mode
            pass
        elif tool_name == 'select':
            # Activate selection mode
            pass
        # ... etc
```

**Result:** ~350 lines removed from loader, moved to palette classes.

### 6.2 Migration Strategy

**Phase 1: Develop SwissKnifePalette in parallel**
- Keep existing palettes working
- Build SwissKnifePalette under `src/shypn/dev/swissknife/`
- Test independently

**Phase 2: Wire up signals**
- Connect SwissKnifePalette signals to existing handlers
- Verify mode switching works
- Verify tool activation works

**Phase 3: Remove old palettes**
- Remove ToolsPalette, OperationsPalette, etc.
- Remove old loader code
- Update imports

**Phase 4: Extend with new tools**
- Add layout tools sub-palette
- Add transform tools sub-palette
- Add analysis tools sub-palette

---

## 7. Implementation Phases - REVISED

### Phase 0: Standalone Test Bed (Week 1)

**Goal:** Validate architecture with minimal risk

**Deliverables:**
- `src/shypn/dev/swissknife_testbed/test_app.py`: Standalone test application
- `src/shypn/dev/swissknife_testbed/placeholder_tools.py`: Simple tool placeholders
- `src/shypn/dev/swissknife_testbed/README.md`: Test bed documentation

**Activities:**
1. Create test window with simulated canvas
2. Add mode switch buttons
3. Add console log area
4. Implement placeholder tools (buttons only)
5. Test signal emission
6. Test GtkRevealer animations

**Success Criteria:**
- ✅ Test app runs independently
- ✅ Placeholder buttons emit signals
- ✅ Console logs all signals
- ✅ Animations smooth (200ms)
- ✅ CSS styling works

**Milestone:** Test bed validates approach, ready for real implementation

---

### Phase 1: Base Infrastructure (Week 2)

**Goal:** Implement core classes without mode-specific logic

**Deliverables:**
- `base.py`: BaseTool, BaseSubPalette (abstract classes)
- `main_palette.py`: SwissKnifePalette (single-mode container)
- `animation_controller.py`: Animation sequencing
- `tool_registry.py`: Tool registration system
- `styles/base_styles.py`: Global CSS

**Tests:**
- Test SwissKnifePalette instantiation (edit and simulate modes)
- Test animation controller sequencing
- Test tool registry (register, retrieve)
- Test CSS application

**Milestone:** Core infrastructure complete, ready for sub-palettes

---

### Phase 2: Edit Mode Sub-Palettes (Week 3)

**Goal:** Implement all Edit mode sub-palettes with real tools

**Deliverables:**
- `subpalettes/create_tools.py`: Place, Transition, Arc
- `subpalettes/edit_operations.py`: Select, Lasso, Undo, Redo
- `subpalettes/layout_tools.py`: Layout algorithms
- `subpalettes/transform_tools.py`: Arc transformations
- `subpalettes/view_tools.py`: Zoom, Center, Fit
- `tools/place_tool.py`, `tools/transition_tool.py`, etc.
- `styles/edit_styles.py`: Edit mode CSS

**Tests:**
- Test each sub-palette independently
- Test tool activation/deactivation
- Test tool reuse (Select in multiple palettes)
- Test category button behavior

**Milestone:** Edit mode fully functional in test bed

---

### Phase 3: Simulate Mode Sub-Palettes (Week 4)

**Goal:** Implement Simulate mode sub-palettes

**Deliverables:**
- `subpalettes/simulation_control.py`: Step, Play, Reset
- `subpalettes/visualization.py`: Charts, Metrics
- `subpalettes/analysis.py`: Export, Statistics
- `styles/simulate_styles.py`: Simulate mode CSS

**Tests:**
- Test Simulate mode sub-palettes
- Test mode switching in test bed
- Test signal flow for simulation controls

**Milestone:** Simulate mode fully functional in test bed

---

### Phase 4: Integration with Main App (Week 5)

**Goal:** Replace old palettes in main application

**Deliverables:**
- Updated `model_canvas_loader.py`: Use SwissKnifePalette
- Remove old palette code
- Wire up real tool handlers
- Integration tests

**Migration Steps:**
1. Add SwissKnifePalette creation in loader
2. Connect signals to existing handlers
3. Test Edit mode integration
4. Test Simulate mode integration
5. Remove old palette code
6. Update documentation

**Tests:**
- Integration tests with real canvas
- Test tool activation in main app
- Test mode switching via [E]/[S] buttons
- Performance tests

**Milestone:** SwissKnifePalette replaces all old palettes

---

### Phase 5: Polish and Documentation (Week 6)

**Goal:** Finalize, optimize, document

**Deliverables:**
- Performance optimization
- User documentation
- Developer documentation
- API reference
- Migration guide
- Video tutorials (optional)

**Activities:**
- Optimize animation performance
- Add keyboard shortcuts
- Improve accessibility
- Write user guide
- Write developer guide
- Create examples

**Success Criteria:**
- ✅ Performance: < 200ms animations
- ✅ Memory: < 5MB for palette system
- ✅ Documentation: Complete and clear
- ✅ Tests: > 80% coverage
- ✅ User feedback: Positive

**Milestone:** Production-ready, fully documented

---

## 8. Tool Organization Matrix

### Tools by Category and Mode

| Tool | Edit/Create | Edit/Edit Ops | Edit/Layout | Edit/Transform | Edit/View | Simulate/Control | Simulate/Viz | Simulate/Analysis |
|------|------------|---------------|-------------|----------------|-----------|------------------|--------------|-------------------|
| Place | ✓ | | | | | | | |
| Transition | ✓ | | | | | | | |
| Arc | ✓ | | | | | | | |
| Select | | ✓ | | | ✓ | | | |
| Lasso | | ✓ | | | | | | |
| Undo | | ✓ | | | | | | |
| Redo | | ✓ | | | | | | |
| Auto Layout | | | ✓ | | | | | |
| Hierarchical | | | ✓ | | | | | |
| Force-Directed | | | ✓ | | | | | |
| Circular | | | ✓ | | | | | |
| Orthogonal | | | ✓ | | | | | |
| Parallel Arc | | | | ✓ | | | | |
| Inhibitor Arc | | | | ✓ | | | | |
| Read Arc | | | | ✓ | | | | |
| Reset Arc | | | | ✓ | | | | |
| Zoom In | | | | | ✓ | | ✓ | |
| Zoom Out | | | | | ✓ | | ✓ | |
| Fit to Window | | | | | ✓ | | | |
| Center View | | | | | ✓ | | | |
| Step | | | | | | ✓ | | |
| Play/Pause | | | | | | ✓ | | |
| Reset | | | | | | ✓ | | |
| Speed Control | | | | | | ✓ | | |
| Show Tokens | | | | | | | ✓ | |
| Show Marking | | | | | | | ✓ | |
| Chart View | | | | | | | ✓ | |
| Export Data | | | | | | | | ✓ |
| Statistics | | | | | | | | ✓ |

**Note:** Tools with multiple checkmarks are registered once and reused.

---

## 9. Signal Architecture - REVISED

### SwissKnifePalette Signals

```python
# Category selection
'category-selected': (str: category_id)
    # Emitted when a category button is clicked
    # category_id: 'create', 'edit', 'layout', etc.

# Tool activation
'tool-activated': (str: tool_id)
    # Emitted when a tool button is activated
    # tool_id: unique tool identifier ('place', 'select', etc.)

# Tool deactivation
'tool-deactivated': (str: tool_id)
    # Emitted when a tool is deactivated

# Sub-palette visibility
'sub-palette-shown': (str: palette_id)
    # Emitted AFTER sub-palette reveal animation completes
    # palette_id: 'create-tools', 'edit-operations', etc.

'sub-palette-hidden': (str: palette_id)
    # Emitted AFTER sub-palette hide animation completes
```

### Signal Flow Example - SIMPLIFIED

**Example 1: User clicks "Create" category (Edit mode)**
```
User clicks [Create] button
    └─> SwissKnifePalette._on_category_clicked('create')
        └─> emit('category-selected', 'create')
        └─> AnimationController.animate_sub_palette_show('create-tools')
            └─> GtkRevealer.set_reveal_child(True)
            └─> Wait 200ms
            └─> emit('sub-palette-shown', 'create-tools')

Expected Timeline:
t=0ms:    Button clicked
t=0ms:    category-selected signal
t=0ms:    Animation starts (SLIDE_DOWN)
t=200ms:  Animation completes
t=200ms:  sub-palette-shown signal
```

**Example 2: User clicks [P] tool button**
```
User clicks [P] button in Create Tools palette
    └─> PlaceTool._on_button_toggled()
        └─> emit('tool-activated', 'place')
            └─> ModelCanvasLoader._on_tool_activated('place')
                └─> Enable place creation mode on canvas
                └─> Set cursor to crosshair
                └─> Wait for canvas clicks
```

**Example 3: Switching sub-palettes**
```
User has "Create" open, clicks "Edit" category
    └─> SwissKnifePalette._on_category_clicked('edit')
        └─> emit('category-selected', 'edit')
        └─> AnimationController.animate_sub_palette_switch(
                from='create-tools',
                to='edit-operations'
            )
            └─> Hide create-tools (SLIDE_UP)
            └─> Wait 200ms
            └─> emit('sub-palette-hidden', 'create-tools')
            └─> Show edit-operations (SLIDE_DOWN)
            └─> Wait 200ms
            └─> emit('sub-palette-shown', 'edit-operations')

Total time: 400ms (sequential animations)
```

**Example 4: Mode switch via external [E]/[S] buttons**
```
User clicks [S] button (external to SwissKnifePalette)
    └─> ModelCanvasLoader._on_simulate_button_clicked()
        └─> Remove old palette: swissknife_edit.destroy()
        └─> Create new palette: swissknife_sim = SwissKnifePalette(mode='simulate')
        └─> Attach to overlay
        └─> Connect signals
        └─> Enter simulation mode

NO mode-changed signal (mode selection is external)
```

### Signal Handlers in Main App

```python
# In model_canvas_loader.py

def _setup_swissknife_palette(self, manager, mode='edit'):
    """Setup SwissKnifePalette for specified mode."""
    self.swissknife = SwissKnifePalette(mode=mode)
    
    # Connect signals
    self.swissknife.connect('category-selected', 
                            self._on_category_selected, manager)
    self.swissknife.connect('tool-activated', 
                            self._on_tool_activated, manager)
    self.swissknife.connect('sub-palette-shown', 
                            self._on_sub_palette_shown)
    self.swissknife.connect('sub-palette-hidden', 
                            self._on_sub_palette_hidden)
    
    # Attach to overlay
    palette_widget = self.swissknife.get_widget()
    self.overlay.add_overlay(palette_widget)

def _on_category_selected(self, palette, category_id, manager):
    """Handle category button click."""
    print(f"Category selected: {category_id}")
    # Optional: Update UI state

def _on_tool_activated(self, palette, tool_id, manager):
    """Handle tool activation."""
    if tool_id == 'place':
        self._activate_place_creation_mode(manager)
    elif tool_id == 'transition':
        self._activate_transition_creation_mode(manager)
    elif tool_id == 'arc':
        self._activate_arc_creation_mode(manager)
    elif tool_id == 'select':
        self._activate_selection_mode(manager)
    elif tool_id == 'layout_auto':
        self._apply_auto_layout(manager)
    # ... etc

def _on_sub_palette_shown(self, palette, palette_id):
    """Handle sub-palette reveal."""
    print(f"Sub-palette shown: {palette_id}")

def _on_sub_palette_hidden(self, palette, palette_id):
    """Handle sub-palette hide."""
    print(f"Sub-palette hidden: {palette_id}")
```

---

## 10. Testing Strategy

### Unit Tests

**Test Files:**
- `tests/test_swissknife_base.py`: Test base classes
- `tests/test_swissknife_main.py`: Test SwissKnifePalette
- `tests/test_swissknife_modes.py`: Test mode controllers
- `tests/test_swissknife_subpalettes.py`: Test sub-palettes
- `tests/test_swissknife_animation.py`: Test animation controller
- `tests/test_swissknife_tools.py`: Test tool registry and tools

**Test Coverage:**
- Mode switching logic
- Sub-palette show/hide
- Tool activation/deactivation
- Animation sequencing
- Tool reuse across palettes
- CSS application
- Signal emission

### Integration Tests

**Test Scenarios:**
1. Launch app → SwissKnifePalette visible
2. Click [E] → Edit mode active, create tools visible
3. Click "Create" → Create tools sub-palette slides down
4. Click [P] → Place tool activated, canvas in place creation mode
5. Click [S] → Simulate mode active, simulation controls visible
6. Click "Control" → Simulation controls sub-palette slides down
7. Switch modes rapidly → No animation glitches

### Performance Tests

**Metrics:**
- Mode switch time: < 200ms
- Sub-palette reveal time: < 200ms
- Tool activation time: < 50ms
- Memory usage: < 5MB for entire palette system
- No frame drops during animations

---

## 11. Documentation

### User Documentation

**Topics:**
- How to switch between Edit and Simulate modes
- How to access sub-palettes (category buttons)
- Tool descriptions and keyboard shortcuts
- Customizing palette appearance (CSS)

### Developer Documentation

**Topics:**
- How to add a new tool
- How to add a new sub-palette
- How to add a new mode
- How to reuse tools across palettes
- CSS styling guide
- Animation customization

### API Reference

**Classes:**
- SwissKnifePalette
- BaseTool, BaseSubPalette, BaseModeController
- EditModeController, SimulateModeController
- AnimationController, ToolRegistry

---

## 12. Future Enhancements

### Phase 6+: Advanced Features

1. **Customizable Palettes**
   - User can rearrange tools
   - User can hide/show sub-palettes
   - Saved preferences per document

2. **Keyboard Navigation**
   - Tab through tools
   - Arrow keys to switch categories
   - Keyboard shortcuts for all tools

3. **Context-Aware Tools**
   - Tools enabled/disabled based on selection
   - Tool suggestions based on workflow

4. **Palette Themes**
   - Light/Dark themes
   - High contrast mode
   - Custom color schemes

5. **Tool Presets**
   - Save tool configurations
   - Quick-switch between presets
   - Share presets with team

6. **Animation Presets**
   - Fast/Normal/Slow animation speeds
   - Different animation styles (slide/fade/zoom)
   - Disable animations for accessibility

7. **Mobile/Tablet Support**
   - Touch-friendly button sizes
   - Swipe gestures for mode switching
   - Responsive layout

---

## 13. Migration Path from Old Palettes

### Compatibility Layer (Optional)

For gradual migration, we can create a compatibility layer:

```python
# src/shypn/dev/swissknife/compat.py

class CompatibilityAdapter:
    """Adapter to make SwissKnifePalette work with old loader code."""
    
    def __init__(self, swissknife: SwissKnifePalette):
        self.swissknife = swissknife
    
    def get_tools_palette(self):
        """Emulate old ToolsPalette interface."""
        return self.swissknife.get_sub_palette('create-tools')
    
    def get_operations_palette(self):
        """Emulate old OperationsPalette interface."""
        return self.swissknife.get_sub_palette('edit-operations')
    
    # ... etc
```

### Deprecation Timeline

**Phase 1 (Week 1-2):** SwissKnifePalette development  
**Phase 2 (Week 3):** Parallel operation (old + new palettes)  
**Phase 3 (Week 4):** SwissKnifePalette becomes default  
**Phase 4 (Week 5):** Remove old palettes  
**Phase 5 (Week 6):** Deprecate compatibility layer  

---

## 14. Success Criteria

### Technical Criteria

✅ OOP architecture with separate modules  
✅ Minimal loader code (< 100 lines)  
✅ CSS-styled containers  
✅ Smooth animations (200ms transitions)  
✅ Tool reuse across sub-palettes  
✅ Mode switching works correctly  
✅ All existing tools migrated  
✅ Unit test coverage > 80%  
✅ No performance regression  

### User Experience Criteria

✅ Intuitive mode switching  
✅ Clear visual feedback for active tools  
✅ Smooth, non-jarring animations  
✅ Discoverable sub-palettes  
✅ Consistent with existing UI style  
✅ Accessible (keyboard navigation, tooltips)  
✅ Fast response (< 200ms)  

### Maintenance Criteria

✅ Easy to add new tools  
✅ Easy to add new sub-palettes  
✅ Easy to customize appearance  
✅ Well-documented code  
✅ Clear separation of concerns  
✅ Extensible architecture  

---

## 15. Next Steps

1. **Review this design document** ✓
2. **Create module structure** under `src/shypn/dev/swissknife/`
3. **Implement Phase 1** (base infrastructure)
4. **Create unit tests** for base classes
5. **Implement Phase 2** (edit mode)
6. **Test integration** with existing canvas loader
7. **Continue phases 3-5** sequentially

**Ready to proceed with implementation? Let me know and I'll start creating the base classes!**

---

## Appendix A: File Checklist

### Files to Create

- [ ] `src/shypn/dev/swissknife/__init__.py`
- [ ] `src/shypn/dev/swissknife/base.py`
- [ ] `src/shypn/dev/swissknife/main_palette.py`
- [ ] `src/shypn/dev/swissknife/mode_switcher.py`
- [ ] `src/shypn/dev/swissknife/animation_controller.py`
- [ ] `src/shypn/dev/swissknife/tool_registry.py`
- [ ] `src/shypn/dev/swissknife/modes/__init__.py`
- [ ] `src/shypn/dev/swissknife/modes/edit_mode.py`
- [ ] `src/shypn/dev/swissknife/modes/simulate_mode.py`
- [ ] `src/shypn/dev/swissknife/subpalettes/__init__.py`
- [ ] `src/shypn/dev/swissknife/subpalettes/create_tools.py`
- [ ] `src/shypn/dev/swissknife/subpalettes/edit_operations.py`
- [ ] `src/shypn/dev/swissknife/subpalettes/layout_tools.py`
- [ ] `src/shypn/dev/swissknife/subpalettes/transform_tools.py`
- [ ] `src/shypn/dev/swissknife/subpalettes/view_tools.py`
- [ ] `src/shypn/dev/swissknife/subpalettes/simulation_control.py`
- [ ] `src/shypn/dev/swissknife/subpalettes/visualization.py`
- [ ] `src/shypn/dev/swissknife/subpalettes/analysis.py`
- [ ] `src/shypn/dev/swissknife/tools/__init__.py`
- [ ] `src/shypn/dev/swissknife/tools/place_tool.py`
- [ ] `src/shypn/dev/swissknife/tools/transition_tool.py`
- [ ] `src/shypn/dev/swissknife/tools/arc_tool.py`
- [ ] `src/shypn/dev/swissknife/tools/select_tool.py`
- [ ] `src/shypn/dev/swissknife/styles/__init__.py`
- [ ] `src/shypn/dev/swissknife/styles/base_styles.py`
- [ ] `src/shypn/dev/swissknife/styles/edit_styles.py`
- [ ] `src/shypn/dev/swissknife/styles/simulate_styles.py`
- [ ] `tests/test_swissknife_base.py`
- [ ] `tests/test_swissknife_main.py`
- [ ] `tests/test_swissknife_modes.py`
- [ ] `tests/test_swissknife_subpalettes.py`
- [ ] `tests/test_swissknife_animation.py`
- [ ] `tests/test_swissknife_tools.py`
- [ ] `doc/SWISSKNIFE_PALETTE_USER_GUIDE.md`
- [ ] `doc/SWISSKNIFE_PALETTE_DEVELOPER_GUIDE.md`
- [ ] `doc/SWISSKNIFE_PALETTE_API_REFERENCE.md`

### Files to Modify

- [ ] `src/shypn/helpers/model_canvas_loader.py` (simplify)
- [ ] `src/shypn/dev/__init__.py` (add swissknife exports)
- [ ] `src/shypn/__init__.py` (add swissknife to public API)

### Files to Remove (Phase 5)

- [ ] `src/shypn/edit/palette_manager.py` (replaced by SwissKnifePalette)
- [ ] `src/shypn/edit/tools_palette_new.py` (replaced by create_tools sub-palette)
- [ ] `src/shypn/edit/operations_palette_new.py` (replaced by edit_operations sub-palette)
- [ ] `src/shypn/helpers/simulate_palette_loader.py` (replaced by simulate mode)

---

---

## 16. Standalone Test Bed (Under dev/) - NEW SECTION

### 16.1 Purpose

Before integrating SwissKnifePalette into the main application, we develop a **standalone test application** under `src/shypn/dev/swissknife_testbed/` that:

✅ Tests animations (slide up/down, timing)  
✅ Tests CSS styling and containers  
✅ Tests signal flow (button clicks → signals → console logs)  
✅ Uses **placeholder tools** (simple buttons, no real functionality)  
✅ Runs independently (no dependencies on main app)  
✅ Validates architecture before integration  

### 16.2 Test Bed Structure

```
src/shypn/dev/swissknife_testbed/
├── README.md                    # Test bed documentation
├── test_app.py                  # Standalone GTK application
├── placeholder_tools.py         # Simple placeholder tool buttons
├── test_subpalettes.py          # Placeholder sub-palettes for testing
└── signal_logger.py             # Log all signals to console
```

### 16.3 Test Application (test_app.py)

**Key Features:**
- Standalone GTK window with simulated canvas
- Mode switch buttons (simulate external [E]/[S])
- Console log area for signal monitoring
- Tests both Edit and Simulate modes
- No main app dependencies

**Usage:**
```bash
$ python3 src/shypn/dev/swissknife_testbed/test_app.py --mode edit
$ python3 src/shypn/dev/swissknife_testbed/test_app.py --mode simulate
```

### 16.4 Test Scenarios

#### Scenario 1: Animation Timing
```
1. Launch test app in edit mode
2. Click "Create" category button
3. Measure: Sub-palette slides DOWN in 200ms ✓
4. Click "Edit" category button
5. Measure: "Create" slides UP (200ms), "Edit" slides DOWN (200ms) ✓
6. Total switch time: 400ms ✓
```

#### Scenario 2: Category Toggle
```
1. Click "Create" → Opens
2. Click "Create" again → Closes (toggle off)
3. Verify: Active category button unhighlighted
4. Verify: No sub-palette visible
```

#### Scenario 3: Signal Flow
```
Expected Console Log:
[SIGNAL] category-selected: 'create'
[ANIMATION] Hiding current sub-palette: None
[ANIMATION] Showing sub-palette: 'create-tools'
[SIGNAL] sub-palette-shown: 'create-tools'
[SIGNAL] tool-activated: 'place'
```

#### Scenario 4: Mode Switching
```
1. Start in Edit mode (5 categories visible)
2. Click "Switch to SIMULATE" button
3. Verify: Old palette removed cleanly
4. Verify: New palette created with 3 categories
5. Verify: All categories work in new mode
```

### 16.5 Placeholder Tools

**Purpose:** Simple buttons that emit signals but don't perform actions.

```python
class PlaceholderTool(BaseTool):
    """Minimal tool for testing."""
    
    def __init__(self, tool_id, label, tooltip):
        self.label = label
        self.tooltip = tooltip
        super().__init__(tool_id, tool_id)
    
    def _create_button(self):
        button = Gtk.Button(label=self.label)
        button.set_tooltip_text(self.tooltip)
        return button
    
    def on_activated(self):
        print(f"[TEST] {self.tool_id} activated")
    
    def on_deactivated(self):
        print(f"[TEST] {self.tool_id} deactivated")
```

### 16.6 Test Checklist

**Animation Tests:**
- [ ] Sub-palette slides down (SLIDE_DOWN, 200ms)
- [ ] Sub-palette slides up (SLIDE_UP, 200ms)
- [ ] Sequential animations (hide then show)
- [ ] Toggle behavior (click same category twice)
- [ ] No animation glitches or jumps

**Signal Tests:**
- [ ] `category-selected` emitted correctly
- [ ] `sub-palette-shown` emitted after animation
- [ ] `sub-palette-hidden` emitted after animation
- [ ] `tool-activated` emitted on button click
- [ ] All signals have correct parameters

**CSS Tests:**
- [ ] Category buttons styled
- [ ] Active category highlighted
- [ ] Tool buttons styled
- [ ] Sub-palette background styled
- [ ] Hover effects work
- [ ] Transitions smooth (200ms)

**Mode Tests:**
- [ ] Edit mode: 5 categories
- [ ] Simulate mode: 3 categories
- [ ] Mode switch works cleanly
- [ ] No widget leaks
- [ ] Palette properly recreated

**Integration Readiness:**
- [ ] Zero dependencies on main app
- [ ] Clean signal architecture
- [ ] OOP design validated
- [ ] Code is modular
- [ ] Ready for model_canvas_loader.py integration

### 16.7 Benefits of Test Bed Approach

✅ **Risk-Free Development:** Test without breaking main app  
✅ **Fast Iteration:** No need to launch full app  
✅ **Clear Validation:** Console logs show all behavior  
✅ **Animation Tuning:** Easily test different timings  
✅ **CSS Experimentation:** Try styles quickly  
✅ **Signal Debugging:** See all signal flow  
✅ **Architecture Proof:** Validates OOP design  

---

**End of Design Document**
