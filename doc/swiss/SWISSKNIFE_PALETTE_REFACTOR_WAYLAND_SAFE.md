# SwissKnifePalette Refactoring Plan - Parameter Panels Architecture

**Date:** October 22, 2025  
**Status:** Planning Phase  
**Priority:** High - Space Optimization + Parameter Panel Pattern  
**Wayland Safety:** 10/10 ✅ (No reparenting operations)

---

## Executive Summary

The **SwissKnifePalette** requires refactoring to implement a **universal parameter panel pattern**. Currently, the SimulateToolsPaletteLoader has an internal micro-panel for settings, but this should be externalized to a standardized architecture.

### Core Requirements

1. **Constant height main palette** - Main palette + sub-palette height **never changes**
2. **Parameter panels above sub-palettes** - Settings panels slide up/down above tools
3. **Universal pattern** - All tools needing parameters use same architecture
4. **No floating mode** - Main palette stays permanently attached to canvas
5. **Modular architecture** - Easy addition of new tool categories with parameters

### Architecture Decision

**DISCARDED:** Floating palette feature (insufficient benefit vs complexity)  
**FOCUS:** Parameter panel architecture as universal pattern for all tools

---

## 1. Current Architecture Analysis

### 1.1 Existing Structure (582 lines, monolithic)

**File:** `src/shypn/helpers/swissknife_palette.py`

```
SwissKnifePalette (GObject.GObject)
├── main_container (Gtk.Box VERTICAL)
│   ├── sub_palette_area (Gtk.Box VERTICAL) - FIRST (on top)
│   │   ├── edit_revealer (GtkRevealer SLIDE_UP, 600ms)
│   │   │   └── tools_box [P][T][A][S][L]
│   │   ├── simulate_revealer (GtkRevealer SLIDE_UP, 600ms)
│   │   │   └── SimulateToolsPaletteLoader (widget palette)
│   │   └── layout_revealer (GtkRevealer SLIDE_UP, 600ms)
│   │       └── tools_box [Auto][Hier][Force]
│   └── category_box (Gtk.Box HORIZONTAL) - LAST (bottom, fixed)
│       ├── [Edit] button
│       ├── [Simulate] button
│       └── [Layout] button
```

**Current Positioning:**
- **Canvas Integration:** `overlay_widget.add_overlay(swissknife_widget)`
- **Alignment:** `CENTER` horizontal, `END` vertical
- **Margin:** `margin_bottom=20` (20px from canvas bottom)
- **State:** Permanently attached to canvas overlay

### 1.2 Key Issues Identified

| Issue | Impact | Wayland Risk | Priority |
|-------|--------|--------------|----------|
| **SimulateToolsPalette internal micro-panel** | Parameter panel inside sub-palette (wrong architecture) | ❌ None | **CRITICAL** |
| **No universal parameter panel pattern** | Each tool implements settings differently | ❌ None | **HIGH** |
| **Variable height sub-palettes** | Height changes when switching categories | ❌ None | **HIGH** |
| **Monolithic 582-line class** | Hard to extend, test, maintain | ❌ None | **MEDIUM** |
| **Animation state machine brittle** | `animation_in_progress` flag prone to edge cases | ❌ None | **MEDIUM** |

### 1.3 Current Parameter Panel Implementation Issue

**File:** `src/shypn/helpers/simulate_tools_palette_loader.py`

**Current Architecture (INCORRECT):**
```
SimulateToolsPaletteLoader
├── simulate_tools_revealer (sub-palette)
│   └── simulation controls [Step][Reset][Play]
└── settings_revealer (parameter panel - INSIDE loader)
    └── time scale controls, token speed, etc.
```

**Problem:**
- Parameter panel is **inside** SimulateToolsPaletteLoader
- When settings revealed, sub-palette height **increases**
- Other sub-palettes (Edit, Layout) have **different heights**
- User experience: Main palette jumps up/down when switching categories

**Required Architecture (CORRECT):**
```
SwissKnifePalette
├── parameter_panel_revealer (ABOVE sub-palettes)
│   └── [Dynamic parameter panels for any tool]
├── sub_palette_area (CONSTANT HEIGHT)
│   ├── edit_sub_palette (50px fixed)
│   ├── simulate_sub_palette (50px fixed - no internal settings)
│   └── layout_sub_palette (50px fixed)
└── category_buttons (44px fixed)
```

**Benefit:**
- All sub-palettes have **same height** (50px)
- Parameter panels slide above sub-palettes
- Total height: 20px margin + 50px sub-palette + 44px categories = **114px constant**

---

## 2. Requirements Analysis

### 2.1 User Requirements (From Description)

| # | Requirement | Current Status | Priority |
|---|-------------|----------------|----------|
| 1 | Many tools organized by categories | ✅ Working | - |
| 2 | Main palette with category buttons | ✅ Working (3 categories) | - |
| 3 | Sub-palettes reveal on category click | ✅ Working (SLIDE_UP animation) | - |
| 4 | Sub-palettes can have many tools | ✅ Working (variable width) | - |
| 5 | Sub-palette width varies by tool count | ✅ Working | - |
| 6 | Only main + 1 sub-palette visible | ✅ Working (exclusive reveal) | - |
| 7 | **Height constant (main + sub-palette)** | ❌ **NOT WORKING** | **CRITICAL** |
| 8 | **Floating capability** | ❌ **DISCARDED** (insufficient benefit) | ~~**DROPPED**~~ |
| 9 | **Parameter panels above sub-palettes** | ❌ **NOT WORKING** | **CRITICAL** |
| 10 | Parameter panels slide up/down above tools | ❌ **NOT WORKING** | **CRITICAL** |
| 11 | Universal pattern for all tools w/ parameters | ❌ **NOT WORKING** | **HIGH** |
| 12 | Minimal workspace pollution | ⚠️ Partial (constant height needed) | **HIGH** |
| 13 | Easy addition of new tool categories | ⚠️ Hard (monolithic code) | **MEDIUM** |
| 14 | Built as overlay on canvas | ✅ Working | - |

### 2.2 Technical Requirements

**Constant Height Architecture:**
- All sub-palettes: **50px fixed height** (1 row of buttons + padding)
- Parameter panels: **Separate revealer above sub-palettes**
- Main palette + sub-palette: **114px constant** (never changes)
- Parameter panels: **Variable height** (content-dependent, outside main height)

**Universal Parameter Panel Pattern:**
- Any tool can request parameter panel
- Panel slides up above sub-palette (400ms animation)
- Panel slides down when:
  - User clicks settings button again (toggle)
  - User switches to different category
  - User activates different tool
- Multiple tools can share parameter panel design

**Wayland Safety:**
- All operations within single overlay context ✅
- No widget reparenting ✅
- No floating windows (feature dropped) ✅
- Parameter panels built/destroyed in same parent ✅

**Extensibility:**
- Plugin architecture for new categories
- Registry-based tool management
- Standardized parameter panel interface

---

## 3. Proposed Architecture - Modular Components

### 3.1 Component Breakdown

```
┌─────────────────────────────────────────────────────────────────┐
│                    SwissKnifePalette                            │
│                   (Facade/Coordinator)                          │
└──┬──────────────────────────────────────────────────────────┬───┘
   │                                                          │
   ├─ SwissKnifePaletteUI ──────────────┐                   │
   │  (Widget construction)              │                   │
   │  - create_main_container()          │                   │
   │  - create_parameter_panel_revealer()│                   │
   │  - create_sub_palette_area()        │                   │
   │  - create_category_buttons()        │                   │
   │                                     │                   │
   ├─ SwissKnifePaletteAnimator ────────┤                   │
   │  (Animation state machine)          │                   │
   │  - show_sub_palette(category_id)    │                   │
   │  - hide_sub_palette(category_id)    │                   │
   │  - switch_sub_palette(from, to)     │                   │
   │  States: IDLE, SHOWING, HIDING,     │                   │
   │          SWITCHING                  │                   │
   │                                     │                   │
   ├─ SwissKnifePaletteController ──────┤                   │
   │  (Signal coordination)              │                   │
   │  - on_category_clicked()            │                   │
   │  - on_tool_activated()              │                   │
   │  - on_settings_button_clicked()     │                   │
   │  - forward_simulation_signals()     │                   │
   │                                     │                   │
   ├─ SubPaletteRegistry ────────────────┤                   │
   │  (Plugin management)                │                   │
   │  - register_sub_palette()           │                   │
   │  - get_sub_palette()                │                   │
   │  - list_categories()                │                   │
   │                                     │                   │
   └─ ParameterPanelManager ─────────────┘                   │
      (Panel lifecycle - CRITICAL)                           │
      - show_panel(tool_id, panel_widget)                    │
      - hide_panel()                                         │
      - get_active_panel() -> Optional[Widget]               │
      - auto_hide_on_category_switch()                       │
                                                             │
┌──────────────────────────────────────────────────────────────┘
│
└─ SubPalettePlugin (Interface) ──────────────────────────────┐
   - create_widget() -> Gtk.Widget                            │
   - get_fixed_height() -> int (ALWAYS 50px)                  │
   - get_tools() -> List[Tool]                                │
   - has_parameter_panel() -> bool                            │
   - create_parameter_panel() -> Optional[Gtk.Widget]         │
   │                                                           │
   ├─ SimpleButtonSubPalette ──────────────────────────────────┤
   │  (Edit, Layout categories)                               │
   │  - Fixed height: 50px                                    │
   │  - No parameter panels                                   │
   │                                                           │
   ├─ SimulateSubPalette ───────────────────────────────────────┤
   │  (Simulate category - REFACTORED)                        │
   │  - Fixed height: 50px (settings revealer REMOVED)        │
   │  - Has parameter panel (time scale, token speed)         │
   │  - Settings button triggers ParameterPanelManager        │
   │                                                           │
   └─ CustomToolSubPalette ────────────────────────────────────┘
      (Future: Analysis, Export, etc.)
      - Fixed height: 50px
      - Optional parameter panels
```

### 3.2 Class Responsibilities

#### SwissKnifePalette (Facade - 120 lines)
```python
class SwissKnifePalette(GObject.GObject):
    """Main palette coordinator (facade pattern).
    
    Constant Height Architecture:
    - All sub-palettes: 50px (fixed)
    - Parameter panels: Above sub-palettes (variable, separate revealer)
    - Total main palette height: 114px constant
    """
    
    __gsignals__ = {
        'category-selected': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'tool-activated': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'parameter-panel-shown': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'parameter-panel-hidden': (GObject.SignalFlags.RUN_FIRST, None, ()),
        # ... other signals
    }
    
    def __init__(self, mode='edit', model=None, tool_registry=None):
        super().__init__()
        self.ui = SwissKnifePaletteUI()
        self.animator = SwissKnifePaletteAnimator()
        self.controller = SwissKnifePaletteController(self)
        self.sub_palette_registry = SubPaletteRegistry()
        self.parameter_panel_manager = ParameterPanelManager(self.ui)
        
        # Register default sub-palettes (all 50px height)
        self._register_default_sub_palettes(mode, model, tool_registry)
        
        # Wire parameter panel auto-hide on category switch
        self.connect('category-selected', self._on_category_switch)
    
    def get_widget(self) -> Gtk.Widget:
        """Get main container widget."""
        return self.ui.get_main_container()
    
    def _on_category_switch(self, palette, new_category_id):
        """Auto-hide parameter panel when switching categories."""
        self.parameter_panel_manager.hide_panel()
```

#### SwissKnifePaletteUI (100 lines)
```python
class SwissKnifePaletteUI:
    """Pure UI construction (no business logic).
    
    Widget Hierarchy (bottom to top):
    1. Category buttons (44px fixed) - BOTTOM
    2. Sub-palette area (50px fixed) - MIDDLE  
    3. Parameter panel revealer (variable) - TOP
    """
    
    def create_main_container(self) -> Gtk.Box:
        """Create vertical container with constant-height architecture."""
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        container.get_style_context().add_class('swissknife-container')
        
        # 1. Parameter panel revealer (FIRST = TOP when revealed)
        # Slides UP from below, appears ABOVE sub-palettes
        self.parameter_panel_revealer = Gtk.Revealer()
        self.parameter_panel_revealer.set_transition_type(
            Gtk.RevealerTransitionType.SLIDE_UP
        )
        self.parameter_panel_revealer.set_transition_duration(400)  # 400ms animation
        self.parameter_panel_revealer.set_reveal_child(False)  # Hidden by default
        container.pack_start(self.parameter_panel_revealer, False, False, 0)
        
        # 2. Sub-palette area (SECOND = MIDDLE, 50px constant height)
        self.sub_palette_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sub_palette_area.set_size_request(-1, 50)  # Force 50px height
        self.sub_palette_area.set_margin_bottom(25)  # Spacing above categories
        container.pack_start(self.sub_palette_area, False, False, 0)
        
        # 3. Category buttons (LAST = BOTTOM, 44px fixed)
        self.category_box = self._create_category_box()
        container.pack_end(self.category_box, False, False, 0)
        
        return container
    
    def add_sub_palette_revealer(self, category_id: str, widget: Gtk.Widget):
        """Add sub-palette revealer (all 50px height)."""
        revealer = Gtk.Revealer()
        revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        revealer.set_transition_duration(600)
        revealer.set_size_request(-1, 50)  # Force 50px height
        revealer.add(widget)
        revealer.set_reveal_child(False)
        
        self.sub_palette_area.pack_start(revealer, False, False, 0)
        return revealer
```

#### SwissKnifePaletteAnimator (120 lines)
```python
class SwissKnifePaletteAnimator:
    """Animation state machine with queue support."""
    
    class State(Enum):
        IDLE = 0
        SHOWING = 1
        HIDING = 2
        SWITCHING = 3
    
    def __init__(self):
        self.state = State.IDLE
        self.animation_queue = []
        self.active_revealer = None
    
    def show_sub_palette(self, revealer: Gtk.Revealer, 
                        on_complete: Callable):
        """Enqueue show animation."""
        if self.state != State.IDLE:
            self.animation_queue.append(('show', revealer, on_complete))
            return
        
        self._start_show(revealer, on_complete)
    
    def _start_show(self, revealer, on_complete):
        self.state = State.SHOWING
        revealer.set_reveal_child(True)
        GLib.timeout_add(600, self._finish_show, revealer, on_complete)
    
    def _finish_show(self, revealer, on_complete):
        self.state = State.IDLE
        on_complete()
        self._process_queue()
        return False
    
    def _process_queue(self):
        """Process next animation in queue."""
        if self.animation_queue and self.state == State.IDLE:
            action, revealer, callback = self.animation_queue.pop(0)
            if action == 'show':
                self._start_show(revealer, callback)
            elif action == 'hide':
                self._start_hide(revealer, callback)
```

#### ParameterPanelManager (100 lines) - CRITICAL COMPONENT
```python
class ParameterPanelManager:
    """Manages parameter panels above sub-palettes.
    
    Universal pattern for all tools needing parameter settings.
    Panel slides UP from below, appearing ABOVE sub-palettes.
    Main palette + sub-palette height remains constant (114px).
    """
    
    def __init__(self, ui: SwissKnifePaletteUI, parent_palette):
        self.ui = ui
        self.parent_palette = parent_palette
        self.active_panel = None
        self.active_tool_id = None
        self.panel_registry = {}  # tool_id -> panel_widget factory
    
    def register_parameter_panel(self, tool_id: str, 
                                 panel_factory: Callable[[], Gtk.Widget]):
        """Register parameter panel factory for a tool.
        
        Args:
            tool_id: Tool identifier (e.g., 'simulate_settings')
            panel_factory: Function that creates panel widget on demand
        
        Example:
            def create_simulation_settings_panel():
                panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                # Add time scale slider, token speed, etc.
                return panel
            
            manager.register_parameter_panel(
                'simulate_settings', 
                create_simulation_settings_panel
            )
        """
        self.panel_registry[tool_id] = panel_factory
    
    def show_panel(self, tool_id: str):
        """Show parameter panel for specified tool.
        
        Args:
            tool_id: Tool identifier
        """
        # If same panel already open, do nothing
        if self.active_tool_id == tool_id and self.active_panel:
            return
        
        # Hide existing panel first
        if self.active_panel:
            self.hide_panel()
        
        # Get panel factory
        panel_factory = self.panel_registry.get(tool_id)
        if not panel_factory:
            print(f"Warning: No parameter panel registered for tool '{tool_id}'")
            return
        
        # Create panel widget
        panel_widget = panel_factory()
        panel_widget.get_style_context().add_class('parameter-panel')
        
        self.active_panel = panel_widget
        self.active_tool_id = tool_id
        
        # Add to revealer and reveal
        self.ui.parameter_panel_revealer.add(panel_widget)
        self.ui.parameter_panel_revealer.set_reveal_child(True)
        
        # Emit signal
        self.parent_palette.emit('parameter-panel-shown', tool_id)
    
    def hide_panel(self):
        """Hide currently visible parameter panel."""
        if not self.active_panel:
            return
        
        # Start hide animation
        self.ui.parameter_panel_revealer.set_reveal_child(False)
        
        # Remove panel after animation completes
        GLib.timeout_add(400, self._remove_panel)
    
    def toggle_panel(self, tool_id: str):
        """Toggle parameter panel visibility.
        
        If panel is shown, hide it.
        If panel is hidden, show it.
        """
        if self.active_tool_id == tool_id and self.active_panel:
            self.hide_panel()
        else:
            self.show_panel(tool_id)
    
    def _remove_panel(self):
        """Remove panel widget after hide animation completes."""
        if self.active_panel:
            self.ui.parameter_panel_revealer.remove(self.active_panel)
            self.active_panel.destroy()  # Clean up
            self.active_panel = None
            tool_id = self.active_tool_id
            self.active_tool_id = None
            
            # Emit signal
            self.parent_palette.emit('parameter-panel-hidden')
        
        return False  # Don't repeat timeout
```

#### FloatingPaletteManager (150 lines)
```python
class FloatingPaletteManager:
    """Wayland-safe floating window manager (Dual Build Pattern)."""
    
    def __init__(self, source_palette: SwissKnifePalette):
        self.source_palette = source_palette
        self.floating_window = None
        self.floating_palette_instance = None
        self.sync_active = False
    
    def show_floating_window(self):
        """Create floating window with DUPLICATE palette instance."""
        # Create new window
        self.floating_window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.floating_window.set_title("SwissKnife Tools")
        self.floating_window.set_decorated(True)
        self.floating_window.set_keep_above(True)
        self.floating_window.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        
        # Add titlebar with [Dock] button
        headerbar = Gtk.HeaderBar()
        headerbar.set_show_close_button(True)
        headerbar.set_title("SwissKnife Tools")
        
        dock_button = Gtk.Button(label="⚓ Dock")
        dock_button.connect('clicked', self._on_dock_clicked)
        headerbar.pack_start(dock_button)
        
        self.floating_window.set_titlebar(headerbar)
        
        # ✅ WAYLAND-SAFE: Create NEW palette instance (not reparent)
        mode = self.source_palette.mode
        model = self.source_palette.model
        tool_registry = self.source_palette.tool_registry
        
        self.floating_palette_instance = SwissKnifePalette(
            mode=mode,
            model=model,
            tool_registry=tool_registry
        )
        
        # Copy current state from source
        self._sync_state_to_floating()
        
        # Wire bidirectional sync signals
        self._wire_sync_signals()
        
        # Add to window
        self.floating_window.add(self.floating_palette_instance.get_widget())
        self.floating_window.show_all()
        
        # Hide source palette in overlay
        self.source_palette.get_widget().hide()
        
        # Connect window close handler
        self.floating_window.connect('delete-event', self._on_window_close)
    
    def _sync_state_to_floating(self):
        """Copy source palette state to floating instance."""
        self.sync_active = True  # Prevent feedback loops
        
        # Copy active category
        if self.source_palette.active_category:
            cat_id = self.source_palette.active_category
            # Trigger category reveal in floating palette
            self.floating_palette_instance.controller.activate_category(cat_id)
        
        # Copy active tool
        active_tool_id = self.source_palette.tool_registry.get_active_tool_id()
        if active_tool_id:
            self.floating_palette_instance.tool_registry.set_active_tool(active_tool_id)
        
        self.sync_active = False
    
    def _wire_sync_signals(self):
        """Wire bidirectional state synchronization."""
        # Floating → Source
        self.floating_palette_instance.connect(
            'tool-activated', 
            self._on_floating_tool_activated
        )
        
        # Source → Floating (source already emitting signals to main app)
        self.source_palette.connect(
            'tool-activated',
            self._on_source_tool_activated
        )
    
    def _on_floating_tool_activated(self, palette, tool_id):
        """Sync tool activation from floating to source."""
        if self.sync_active:
            return
        
        self.sync_active = True
        # Update source palette tool state
        self.source_palette.tool_registry.set_active_tool(tool_id)
        # Emit signal through source palette (so main app sees it)
        self.source_palette.emit('tool-activated', tool_id)
        self.sync_active = False
    
    def _on_source_tool_activated(self, palette, tool_id):
        """Sync tool activation from source to floating."""
        if self.sync_active or not self.floating_palette_instance:
            return
        
        self.sync_active = True
        self.floating_palette_instance.tool_registry.set_active_tool(tool_id)
        self.sync_active = False
    
    def hide_floating_window(self):
        """Close floating window and restore source palette."""
        if self.floating_window:
            self.floating_window.destroy()
            self.floating_window = None
            self.floating_palette_instance = None
        
        # Show source palette in overlay
        self.source_palette.get_widget().show()
    
    def _on_dock_clicked(self, button):
        """Handle [Dock] button click."""
        self.hide_floating_window()
    
    def _on_window_close(self, window, event):
        """Handle window close button."""
        self.hide_floating_window()
        return True  # Prevent default destroy
```

---

## 4. Wayland Safety Analysis

### 4.1 Current Implementation Safety ✅

**File:** `src/shypn/helpers/model_canvas_loader.py` (lines 720-740)

```python
# ✅ SAFE: Palette created and added to overlay (never reparented)
swissknife_widget = swissknife_palette.get_widget()
swissknife_widget.set_halign(Gtk.Align.CENTER)
swissknife_widget.set_valign(Gtk.Align.END)
swissknife_widget.set_margin_bottom(20)
overlay_widget.add_overlay(swissknife_widget)
```

**Analysis:**
- Widget built once
- Added to overlay once
- Never removed or reparented
- **Wayland Safety Score: 10/10** ✅

### 4.2 Parameter Panel Safety (Refactored Architecture)

**Parameter panels built on-demand within same overlay:**

```python
# ✅ SAFE: Panel created in parameter_panel_revealer (same parent)
panel = simulation_settings_factory()  # Fresh widget instance
parameter_panel_revealer.add(panel)
parameter_panel_revealer.set_reveal_child(True)  # Slide UP animation

# ✅ SAFE: Panel removed after animation (same parent)
parameter_panel_revealer.set_reveal_child(False)  # Slide DOWN animation
GLib.timeout_add(400, lambda: parameter_panel_revealer.remove(panel))
```

**Wayland Safety Checklist:**

| Action | Risk | Solution |
|--------|------|----------|
| Create palette in overlay | ✅ Safe | Standard GTK pattern |
| Create sub-palette revealer | ✅ Safe | Within main container |
| Reveal/hide sub-palette | ✅ Safe | `set_reveal_child()` |
| Create parameter panel | ✅ Safe | Built in parameter_panel_revealer |
| Show parameter panel | ✅ Safe | Reveal animation within same parent |
| Hide parameter panel | ✅ Safe | Hide animation, then remove |
| Destroy parameter panel | ✅ Safe | `widget.destroy()` within same parent |
| Switch categories | ✅ Safe | Hide/show revealers, no reparenting |

**No Wayland risks** - All operations within single overlay context ✅

### 4.3 SimulateToolsPaletteLoader Refactoring Safety

**Current (INCORRECT - but Wayland-safe):**
```python
# File: simulate_tools_palette_loader.py
class SimulateToolsPaletteLoader:
    def __init__(self):
        # Settings revealer INSIDE loader (wrong architecture)
        self.settings_revealer = Gtk.Revealer()
        # This works but causes variable sub-palette height
```

**Refactored (CORRECT - still Wayland-safe):**
```python
# File: simulate_tools_palette_loader.py (refactored)
class SimulateToolsPaletteLoader:
    def __init__(self):
        # NO internal settings revealer
        # Only simulation controls [Step][Reset][Play]
        # Height: 50px fixed
    
    def create_settings_panel(self) -> Gtk.Widget:
        """Factory method for parameter panel (called by ParameterPanelManager)."""
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        # Time scale slider
        # Token flow speed
        # Visualization options
        return panel  # Built fresh each time

# In SwissKnifePalette initialization:
simulate_loader = SimulateToolsPaletteLoader(model)
palette.parameter_panel_manager.register_parameter_panel(
    'simulate_settings',
    simulate_loader.create_settings_panel  # Factory function
)
```

**Wayland Safety Analysis:**
- ✅ No widget reparenting (settings panel built fresh each time)
- ✅ All widgets created in same overlay context
- ✅ Panel destroyed before rebuilding (no stale references)
- ✅ **Wayland Safety Score: 10/10** ✅

---

## 5. Implementation Phases

### Phase 1: Modular Refactoring (4 hours)

**Goal:** Split monolithic class without changing functionality

**Tasks:**
1. Extract `SwissKnifePaletteUI` class (1 hour)
   - Move all widget creation code
   - Keep existing structure identical
   - Test: Palette looks and behaves the same

2. Extract `SwissKnifePaletteAnimator` class (1 hour)
   - Move animation logic
   - Add state machine enum
   - Test: Animations still work

3. Extract `SwissKnifePaletteController` class (1 hour)
   - Move signal handlers
   - Keep signal signatures identical
   - Test: Tool activation works

4. Update main `SwissKnifePalette` to use modules (1 hour)
   - Instantiate sub-components
   - Delegate method calls
   - Test: Full integration test

**Validation:**
- ✅ Run existing application
- ✅ Click all category buttons
- ✅ Activate all tools
- ✅ Verify animations smooth
- ✅ Check signal emission

### Phase 2: Constant Height Sub-Palettes (3 hours) - CRITICAL

**Goal:** Force all sub-palettes to 50px fixed height

**Tasks:**
1. Modify UI structure (1 hour)
   ```python
   # Force 50px height for sub-palette area
   self.sub_palette_area.set_size_request(-1, 50)
   
   # Force 50px height for each revealer
   revealer.set_size_request(-1, 50)
   ```

2. Refactor SimulateToolsPaletteLoader (1.5 hours)
   - **Remove internal settings_revealer**
   - Keep only simulation controls [Step][Reset][Play]
   - Extract `create_settings_panel()` factory method
   - Test: Simulate sub-palette now 50px (not 120px)

3. Verify all sub-palettes same height (30 min)
   - Edit: 50px ✅
   - Simulate: 50px ✅ (settings removed)
   - Layout: 50px ✅

**Validation:**
- ✅ Open Edit category → measure 50px height
- ✅ Switch to Simulate → still 50px height (settings hidden)
- ✅ Switch to Layout → still 50px height
- ✅ Main palette + sub-palette = 114px constant

### Phase 3: Parameter Panel Architecture (5 hours) - CRITICAL

**Goal:** Implement universal parameter panel pattern

**Tasks:**
1. Create `ParameterPanelManager` class (2 hours)
   - Panel registry (tool_id → factory function)
   - Show/hide with animation
   - Auto-hide on category switch
   - Toggle support (click settings button again to hide)

2. Integrate parameter panel revealer in UI (1 hour)
   ```python
   # In SwissKnifePaletteUI.create_main_container()
   # 1. Parameter panel revealer (TOP)
   self.parameter_panel_revealer = Gtk.Revealer()
   self.parameter_panel_revealer.set_transition_type(SLIDE_UP)
   container.pack_start(self.parameter_panel_revealer, False, False, 0)
   
   # 2. Sub-palette area (MIDDLE, 50px fixed)
   self.sub_palette_area.set_size_request(-1, 50)
   container.pack_start(self.sub_palette_area, False, False, 0)
   
   # 3. Category buttons (BOTTOM)
   container.pack_end(self.category_box, False, False, 0)
   ```

3. Refactor SimulateToolsPaletteLoader settings integration (1.5 hours)
   - Register settings panel factory
   - Wire [⚙] button to ParameterPanelManager.toggle_panel()
   - Remove old settings revealer code
   - Test: Settings panel slides UP above sub-palette

4. Test parameter panel lifecycle (30 min)
   - Click [⚙] → panel slides up
   - Click [⚙] again → panel slides down
   - Switch category → panel auto-hides
   - Switch back to Simulate → panel stays hidden (not auto-shown)

**Validation:**
- ✅ Open Simulate category (50px height)
- ✅ Click [⚙] settings button
- ✅ Panel slides UP above sub-palette
- ✅ Sub-palette stays 50px (height unchanged)
- ✅ Adjust settings (time scale, token speed)
- ✅ Click [⚙] again → panel slides DOWN
- ✅ Switch to Edit category → panel auto-hides
- ✅ Main palette height: 114px constant (never changes)

### Phase 4: Plugin Architecture (3 hours)

**Goal:** Easy addition of new tool categories

**Tasks:**
1. Create `SubPalettePlugin` interface (1 hour)
   ```python
   class SubPalettePlugin(ABC):
       @abstractmethod
       def create_widget(self) -> Gtk.Widget: pass
       
       def get_fixed_height(self) -> int:
           return 50  # All sub-palettes 50px
       
       def has_parameter_panel(self) -> bool:
           return False
       
       def create_parameter_panel(self) -> Optional[Gtk.Widget]:
           return None
   ```

2. Refactor existing sub-palettes to plugins (1.5 hours)
   - `EditSubPalette(SubPalettePlugin)`
   - `SimulateSubPalette(SubPalettePlugin)` - with parameter panel
   - `LayoutSubPalette(SubPalettePlugin)`

3. Create plugin registry (30 min)
   ```python
   registry = SubPaletteRegistry()
   registry.register('edit', EditSubPalette(...))
   registry.register('simulate', SimulateSubPalette(...))
   registry.register('custom', MyCustomSubPalette(...))
   ```

**Validation:**
- ✅ All existing categories work
- ✅ Add test custom category
- ✅ Verify plugin lifecycle

### Phase 5: CSS Externalization (2 hours)

**Goal:** Move CSS to external file with theme support

**Tasks:**
1. Create CSS file (30 min)
   - `ui/styles/swissknife_palette.css`
   - Extract all CSS from `_apply_css()`

2. Create CSS loader utility (30 min)
   ```python
   class CSSLoader:
       @staticmethod
       def load_from_file(css_path: str):
           provider = Gtk.CssProvider()
           provider.load_from_path(css_path)
           Gtk.StyleContext.add_provider_for_screen(...)
   ```

3. Add parameter panel CSS (1 hour)
   ```css
   .parameter-panel {
       background: rgba(236, 240, 241, 0.98);
       border: 2px solid rgba(52, 152, 219, 0.6);
       border-radius: 6px;
       padding: 12px;
       margin: 4px 8px;
       box-shadow: 0 -3px 8px rgba(0, 0, 0, 0.3);
   }
   ```

**Validation:**
- ✅ Load CSS from file → palette looks same
- ✅ Parameter panel has distinctive styling
- ✅ Hover effects work

---

## 6. Space Optimization Metrics

### 6.1 Current Space Usage (Variable Height - PROBLEM)

**Measurement Setup:**
- Canvas: 1920x1080px
- SwissKnifePalette: `margin_bottom=20`

**Current Heights (Variable):**
- Category buttons: 36px + 8px padding = 44px
- Sub-palette margin: 25px
- **Edit sub-palette:** 50px (1 row buttons)
- **Simulate sub-palette:** 120px (with internal settings panel) ⚠️
- **Layout sub-palette:** 50px (1 row buttons)

**Total Occupied (varies by category):**
```
Edit category:
20px (margin) + 44px (categories) + 25px (spacing) + 50px (sub-palette) = 139px

Simulate category:
20px (margin) + 44px (categories) + 25px (spacing) + 120px (sub-palette) = 209px ⚠️

Layout category:
20px (margin) + 44px (categories) + 25px (spacing) + 50px (sub-palette) = 139px
```

**Problem:** Height **jumps** by 70px when switching to Simulate category!

### 6.2 Refactored Space Usage (Constant Height - SOLUTION)

**With Constant Height Architecture:**
- All sub-palettes: **50px fixed** (settings moved to parameter panel)
- Parameter panels: **Above sub-palettes** (separate revealer)

**Total Occupied (constant across all categories):**
```
Any category:
20px (margin) + 44px (categories) + 25px (spacing) + 50px (sub-palette) = 139px ✅

With parameter panel open:
139px (main palette) + [variable panel height] above
(Main palette height still 139px - parameter panel is ABOVE it)
```

**Benefit:**
- **Main palette height: 139px constant** (never changes)
- **No jumping** when switching categories
- Parameter panels don't affect main palette footprint
- Better UX: Predictable palette position

### 6.3 Canvas Space Comparison

| State | Current (Variable) | Refactored (Constant) | Improvement |
|-------|-------------------|----------------------|-------------|
| **Edit category** | 139px (12.9%) | 139px (12.9%) | Same |
| **Simulate category** | 209px (19.4%) ⚠️ | 139px (12.9%) ✅ | **-70px (-33%)** |
| **Simulate + Settings** | 209px (19.4%) ⚠️ | 139px + panel above | **Height stable** |
| **Layout category** | 139px (12.9%) | 139px (12.9%) | Same |

**Key Win:** Simulate category no longer eats 70px extra canvas space!

---

## 7. Testing Strategy

### 7.1 Unit Tests

**File:** `tests/test_swissknife_palette_refactor.py`

```python
def test_ui_component_creation():
    """Test SwissKnifePaletteUI creates correct widget hierarchy."""
    ui = SwissKnifePaletteUI()
    container = ui.create_main_container()
    
    assert container is not None
    assert isinstance(container, Gtk.Box)
    assert container.get_orientation() == Gtk.Orientation.VERTICAL

def test_animator_state_machine():
    """Test animation state transitions."""
    animator = SwissKnifePaletteAnimator()
    assert animator.state == SwissKnifePaletteAnimator.State.IDLE
    
    revealer = Gtk.Revealer()
    animator.show_sub_palette(revealer, lambda: None)
    assert animator.state == SwissKnifePaletteAnimator.State.SHOWING

def test_parameter_panel_manager():
    """Test parameter panel show/hide."""
    ui = SwissKnifePaletteUI()
    manager = ParameterPanelManager(ui)
    
    panel = Gtk.Box()
    manager.show_panel('simulate', panel)
    assert manager.active_panel == panel
    
    manager.hide_panel()
    assert manager.active_panel is None

def test_floating_manager_dual_build():
    """Test floating window creates separate instance."""
    source_palette = SwissKnifePalette(mode='edit')
    floating_manager = FloatingPaletteManager(source_palette)
    
    floating_manager.show_floating_window()
    
    # Verify separate instances
    assert floating_manager.floating_palette_instance is not None
    assert floating_manager.floating_palette_instance != source_palette
    
    # Verify source hidden
    assert not source_palette.get_widget().get_visible()
```

### 7.2 Integration Tests

**File:** `tests/test_swissknife_integration.py`

```python
def test_palette_in_overlay():
    """Test palette integration with canvas overlay."""
    loader = ModelCanvasLoader()
    canvas_manager = MockCanvasManager()
    drawing_area = Gtk.DrawingArea()
    overlay = Gtk.Overlay()
    
    loader._setup_edit_palettes(overlay, canvas_manager, drawing_area, None)
    
    # Verify palette added to overlay
    overlays = overlay.get_children()
    assert any('swissknife' in str(child) for child in overlays)

def test_wayland_safety_no_reparenting():
    """Test no widget reparenting occurs during float."""
    palette = SwissKnifePalette(mode='edit')
    original_widget = palette.get_widget()
    original_parent = original_widget.get_parent()
    
    palette.float_palette()
    
    # Original widget should still have same parent (not reparented)
    assert original_widget.get_parent() == original_parent
```

### 7.3 Manual Testing Checklist

**Test Environment:**
- Wayland compositor (GNOME Wayland, Sway, or Weston)
- X11 session (for comparison)
- Dual monitor setup (for floating tests)

**Test Scenarios:**

✅ **Variable Height:**
1. Open Edit category → measure height with ruler
2. Switch to Simulate → verify height increases
3. Switch to Layout → verify height decreases

✅ **Parameter Panels:**
1. Open Simulate category
2. Click [⚙] settings button
3. Panel slides up above sub-palette
4. Adjust settings → changes reflected
5. Click [⚙] again → panel slides down
6. Switch category → panel auto-hides

✅ **Floating (Wayland):**
1. Click [Float] button
2. Floating window appears
3. Click tool in floating window
4. Main app responds correctly
5. Click [Dock] button
6. Palette returns to overlay
7. **Verify no Error 71 crashes**

✅ **Tool Activation:**
1. Click Edit → [P] button
2. Canvas enters place mode
3. Click [T] button
4. Canvas switches to transition mode
5. Verify tool visual feedback (active state)

✅ **Animation Smoothness:**
1. Rapidly click categories (stress test)
2. Animations queue properly (no visual glitches)
3. No frozen states or stuck revealers

---

## 8. Migration Path

### 8.1 Backward Compatibility

**Existing Code:**
```python
# In model_canvas_loader.py (line 726)
swissknife_palette = SwissKnifePalette(
    mode='edit',
    model=canvas_manager,
    tool_registry=tool_registry
)
```

**After Refactoring:**
```python
# Same API - no changes needed!
swissknife_palette = SwissKnifePalette(
    mode='edit',
    model=canvas_manager,
    tool_registry=tool_registry
)
```

**Signal Compatibility:**
- All existing signals preserved
- Signal signatures unchanged
- Handlers work without modification

### 8.2 Optional New Features

**Add floating capability:**
```python
# Add [Float] button to main app
def _add_float_button(self):
    float_button = Gtk.Button(label="🪟 Float")
    float_button.connect('clicked', self._on_float_clicked)
    toolbar.pack_start(float_button, False, False, 0)

def _on_float_clicked(self, button):
    swissknife_palette.float_palette()
```

**Add custom category:**
```python
# Register custom sub-palette
from my_tools import AnalysisSubPalette

palette.sub_palette_registry.register(
    'analysis',
    AnalysisSubPalette(model=canvas_manager)
)
```

---

## 9. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Wayland Error 71 during float** | Low | Critical | Use Dual Build Pattern (tested) |
| **Animation glitches during refactor** | Medium | Medium | Extensive testing, keep state machine simple |
| **State sync issues between instances** | Medium | High | Bidirectional sync with feedback prevention |
| **Performance with many sub-palettes** | Low | Low | Lazy loading, only build visible palettes |
| **CSS conflicts with existing styles** | Low | Low | Scoped CSS classes (`swissknife-*`) |
| **Breaking existing tool handlers** | Low | High | Keep signal API unchanged |

---

## 10. Success Criteria

### Functional Requirements ✅
- [ ] Variable height sub-palettes (space-aware)
- [ ] Parameter panels slide above sub-palettes
- [ ] Floating window works on Wayland (no Error 71)
- [ ] Bidirectional state sync between float/dock
- [ ] Easy plugin registration for new categories
- [ ] External CSS with theme support

### Performance Requirements ✅
- [ ] Category switch < 650ms (600ms animation + 50ms overhead)
- [ ] Float/dock transition < 300ms
- [ ] No memory leaks over 1000 float/dock cycles
- [ ] Smooth animations at 60fps

### Code Quality Requirements ✅
- [ ] Modular architecture (< 200 lines per class)
- [ ] 80% unit test coverage
- [ ] All Wayland safety checks pass
- [ ] Documentation for plugin development
- [ ] Migration guide for existing integrations

### User Experience Requirements ✅
- [ ] 33% reduction in canvas space usage
- [ ] No visual glitches during animations
- [ ] Intuitive float/dock controls
- [ ] Settings persist across sessions
- [ ] Responsive on resize/multi-monitor

---

## 11. Implementation Timeline

| Phase | Duration | Dependencies | Deliverable |
|-------|----------|--------------|-------------|
| **Phase 1: Modular Refactoring** | 4 hours | None | Split classes, tests pass |
| **Phase 2: Variable Heights** | 3 hours | Phase 1 | Sub-palettes content-aware |
| **Phase 3: Parameter Panels** | 4 hours | Phase 2 | Settings panels working |
| **Phase 4: Floating Window** | 5 hours | Phase 1 | Wayland-safe float/dock |
| **Phase 5: Plugin Architecture** | 3 hours | Phase 1 | Registry + interface |
| **Phase 6: CSS Externalization** | 2 hours | Phase 1 | Theme support |
| **Testing & Documentation** | 3 hours | All | Release-ready |

**Total Estimated Time:** **24 hours** (3 full working days)

---

## 12. Wayland Safety Guarantee Summary

### ✅ Safe Operations (Used)
1. **Widget creation in overlay** - Build once, add once
2. **Widget hide/show** - `widget.hide()` / `widget.show()`
3. **Dual Build Pattern** - Separate instances for float
4. **Signal-based sync** - No direct widget manipulation
5. **Window creation** - `Gtk.Window(TOPLEVEL)`
6. **Revealer animations** - Within same parent container

### ❌ Forbidden Operations (Never Used)
1. **Widget reparenting** - `parent1.remove()` + `parent2.add()`
2. **GtkSocket/GtkPlug** - Deprecated, Wayland-incompatible
3. **Direct window embedding** - Not supported on Wayland
4. **`attach_to()` methods** - Same widget across windows

### 🎯 Wayland Safety Score: **10/10** ✅

**Rationale:**
- Zero widget reparenting
- Dual Build Pattern proven safe (Master Palette addendum)
- All operations within single window contexts
- Bidirectional sync via signals only
- Tested on GNOME Wayland, Sway, Weston

---

## 13. Next Steps

**Immediate Actions:**
1. Review this plan with team
2. Create feature branch: `feature/swissknife-refactor`
3. Set up test environment (Wayland + X11)
4. Begin Phase 1 (Modular Refactoring)

**Questions to Resolve:**
1. Which theme should be default (dark vs light)?
2. Should floating be enabled by default or opt-in?
3. Any additional tool categories planned?
4. Preferred keyboard shortcuts for float/dock?

**Documentation Needs:**
1. Plugin development guide
2. API reference for new classes
3. Migration guide for custom integrations
4. User guide for floating feature

---

## 14. Conclusion

The **SwissKnifePalette refactoring** addresses all user requirements while maintaining **100% Wayland safety**:

✅ **Variable height** - Saves 33% canvas space  
✅ **Floating capability** - Dual Build Pattern (no reparenting)  
✅ **Parameter panels** - Contextual settings above sub-palettes  
✅ **Modular architecture** - Easy extension with plugins  
✅ **Theme support** - External CSS with variants  
✅ **Backward compatible** - Existing code unchanged  

**Implementation:** 24 hours across 6 phases  
**Benefit:** Better UX, more workspace, multi-monitor support  
**Risk:** Low (proven patterns, extensive testing planned)  

**Ready to proceed with Phase 1!** 🚀
