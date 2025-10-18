# Mode System Analysis - Current State

**Date**: October 18, 2025  
**Objective**: Analyze the current mode system to plan its elimination in favor of transparent, context-aware behavior

---

## Executive Summary

The current Shypn application uses an **explicit mode system** with two distinct modes:
- **Edit Mode**: For designing and editing Petri nets
- **Simulation Mode**: For running simulations

**Problem**: Users must manually switch between modes, even though they need to constantly design and simulate. This creates friction and interrupts workflow.

**Goal**: Eliminate explicit modes and make the system **context-aware** - automatically detecting when the user is editing vs. simulating and adjusting behavior transparently.

---

## Current Mode System Architecture

### 1. Mode State Management

#### Mode Events (`src/shypn/events/mode_events.py`)
```python
class ModeChangedEvent(BaseEvent):
    """Event fired when application mode changes."""
    def __init__(self, old_mode: str, new_mode: str):
        self.old_mode = old_mode  # 'edit' or 'simulate'
        self.new_mode = new_mode  # 'edit' or 'simulate'
```

**Current Modes**:
- `'edit'`: Normal editing mode
- `'simulate'`: Simulation mode

#### Mode Palette (`src/ui/palettes/mode/mode_palette_loader.py`)
```python
class ModePaletteLoader:
    __gsignals__ = {
        'mode-changed': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        'edit-palettes-toggled': (GObject.SIGNAL_RUN_FIRST, None, (bool,))
    }
    
    def __init__(self):
        self.current_mode = 'edit'  # Start in edit mode
        self.edit_palettes_visible = False
```

**UI Components**:
- Two toggle buttons: `[E]` (Edit) and `[S]` (Simulate)
- Mutually exclusive - only one can be active
- Located in overlay palette on canvas

---

### 2. Mode-Dependent Behaviors

#### A. Palette Visibility

**Edit Mode Palettes** (shown when in edit mode):
- Tools Palette (Place, Transition, Arc creation)
- Operations Palette (Select, Lasso, Move, etc.)
- Transform handles for selected objects
- Property dialogs

**Simulation Mode Palettes** (shown when in simulation mode):
- Simulate Palette (`[S]` button)
- Simulation controls (play, pause, step, reset)
- Time display
- Token animation controls

**Code Location**: `src/shypn/canvas/canvas_overlay_manager.py`
```python
def _on_mode_changed(self, mode_palette, new_mode):
    if new_mode == 'edit':
        # Hide simulate palettes
        self._hide_simulate_palettes()
    elif new_mode == 'sim':
        # Show simulate palettes
        self._show_simulate_palettes()
```

#### B. Mouse/Click Behavior

**Edit Mode**:
- Click to select objects
- Drag to move objects
- Double-click to enter transform mode
- Right-click for context menu
- Tool-based creation (Place, Transition, Arc)

**Simulation Mode**:
- Click on place to add/remove tokens (interactive simulation)
- No object movement allowed
- No object creation allowed
- Simulation playback controls active

#### C. Object Editing

**Selection Manager** (`src/shypn/edit/selection_manager.py`):
```python
def enter_edit_mode(self, obj):
    """Enter edit mode for a single object."""
    # Shows transform handles (rotate, scale, etc.)
    self.edit_target = obj

def is_edit_mode(self) -> bool:
    """Check if currently in edit mode."""
    return self.edit_target is not None
```

**Note**: This is actually "transform mode" for individual objects, separate from application-level edit/simulate mode (confusing naming).

---

### 3. Simulation Controller Integration

**Simulation Controller** (`src/shypn/engine/simulation/controller.py`):
```python
class SimulationController:
    """Manages simulation of Petri net model."""
    
    def __init__(self, model):
        self.model = model  # ModelCanvasManager
        self.time = 0.0
        self.running = False  # Simulation state
```

**Key Points**:
- Simulation controller doesn't actually track "mode"
- It has its own state: `running` (True/False)
- Can run simulation steps regardless of UI mode
- Mode affects **UI interactions**, not simulation capability

---

### 4. Canvas Interaction Flow

```
User Action → Mode Check → Behavior Branch
     ↓             ↓              ↓
   Click      'edit' mode?   → Edit behavior (select/move)
   Click      'simulate' mode? → Simulation behavior (add token)
```

**Current Implementation**:
```python
# Hypothetical click handler
def on_canvas_click(self, event):
    if self.current_mode == 'edit':
        # Handle as editing click
        self.select_object(event.x, event.y)
    elif self.current_mode == 'simulate':
        # Handle as simulation click
        self.add_token_at(event.x, event.y)
```

---

## Problems with Current Mode System

### 1. **Workflow Friction**
Users must manually switch modes when they want to:
- Design a bit → Test simulation → Adjust design → Test again
- This requires constant mode switching: `[E]` → `[S]` → `[E]` → `[S]`

### 2. **Cognitive Overhead**
Users must remember:
- Which mode they're in
- What each mode allows/disallows
- To switch modes before doing certain actions

### 3. **Rigid Separation**
Some actions could reasonably work in both modes:
- Viewing object properties
- Zooming/panning canvas
- Undoing changes
- Saving file

### 4. **Naming Confusion**
"Edit mode" used in two ways:
- Application-level edit mode (vs simulate mode)
- Object-level edit mode (transform handles for single object)

### 5. **Palette Proliferation**
Mode system requires:
- Mode palette (switcher)
- Edit-specific palettes
- Simulation-specific palettes
- Logic to show/hide based on mode

---

## What Actually Needs to Be Different?

### Truly Mode-Specific Behaviors

| Behavior | Edit Mode | Simulate Mode | Can Unify? |
|----------|-----------|---------------|------------|
| **Object Creation** | Create place/transition/arc | Disabled | ⚠️ Partial |
| **Object Movement** | Drag to move | Disabled | ⚠️ Partial |
| **Token Manipulation** | Via properties | Click to add/remove | ✅ **YES** |
| **Simulation Control** | N/A | Play/pause/step | ✅ **YES** |
| **Selection** | Select for editing | Select for inspection | ✅ **YES** |
| **Properties** | Edit properties | View properties | ⚠️ Partial |
| **Transform Handles** | Show for selected | Hide | ⚠️ Partial |
| **Zoom/Pan** | Enabled | Enabled | ✅ **Already Unified** |
| **Save/Load** | Enabled | Enabled | ✅ **Already Unified** |
| **Undo/Redo** | Enabled | Limited | ⚠️ Partial |

**Key Insight**: Most behaviors can be unified or made context-aware!

---

## Context-Aware Alternative

### Core Principle
**Replace "What mode am I in?" with "What is the user trying to do?"**

### Detection Mechanisms

#### 1. **Simulation State Detection**
```python
def is_simulation_running(self) -> bool:
    """Detect if simulation is actively running."""
    return self.simulation_controller.running

def has_simulation_started(self) -> bool:
    """Detect if simulation has been started (time > 0)."""
    return self.simulation_controller.time > 0
```

#### 2. **User Intent Detection**
```python
def detect_intent(self, action):
    """Detect what user is trying to do."""
    if action == 'click_on_place':
        if self.is_simulation_running():
            return 'add_token'  # Simulation interaction
        else:
            return 'select_place'  # Editing interaction
    
    if action == 'drag_object':
        if self.has_simulation_started():
            return 'disabled'  # Can't move during simulation
        else:
            return 'move_object'  # Normal editing
```

#### 3. **Tool Context**
```python
def get_active_tool(self):
    """Current tool determines behavior."""
    return self.tools_palette.active_tool  # 'select', 'place', 'arc', etc.

def can_create_object(self):
    """Allow creation if not simulating."""
    return not self.is_simulation_running()
```

---

## Proposed Unified Behavior Model

### 1. **No Mode Palette**
Remove the `[E]` / `[S]` mode switcher entirely.

### 2. **Always-Available Actions**

**Selection & Inspection**:
- Click object → Always selects
- Double-click object → Always opens properties
- Right-click → Always shows context menu

**Canvas Navigation**:
- Zoom, pan, grid → Always available
- File operations (save, load) → Always available

### 3. **Context-Sensitive Actions**

**Token Manipulation**:
```python
# Current: Only in simulation mode
# Proposed: Always available via click
def on_place_click(self, place):
    # Simple click adds token (natural interaction)
    place.tokens += 1
    
    # Shift+click removes token
    if event.shift_held:
        place.tokens = max(0, place.tokens - 1)
```

**Object Creation**:
```python
# Current: Only in edit mode
# Proposed: Disabled if simulation active
def create_place(self, x, y):
    if self.is_simulation_running():
        self.show_notification("Pause simulation to create objects")
        return
    
    # Otherwise, create normally
    place = self.add_place(x, y)
```

**Object Movement**:
```python
# Current: Only in edit mode
# Proposed: Disabled if simulation has started
def move_object(self, obj, x, y):
    if self.has_simulation_started():
        self.show_notification("Reset simulation to move objects")
        return
    
    # Otherwise, move normally
    obj.x, obj.y = x, y
```

### 4. **Simulation Controls Always Visible**

Instead of hiding simulation controls:
- Show them always (like a media player)
- Gray out when not applicable
- Natural affordance: If controls are visible, user knows they can simulate

**Visual State**:
```
┌─────────────────────────────────┐
│  ⏵ Play  ⏸ Pause  ⏹ Stop  ⏱ 0.0s │
│  (grayed when not started)      │
└─────────────────────────────────┘
```

### 5. **Smart Tool Behavior**

**Place Tool**:
- Active: Shows place preview cursor
- Simulation running: Tool grayed out, shows message

**Select Tool**:
- Always active (default)
- During simulation: Selection still works, movement disabled

**Arc Tool**:
- Active: Shows arc preview
- Simulation running: Tool grayed out

---

## Implementation Strategy

### Phase 1: Analysis & Planning ✅ (Current)
- Document current mode system
- Identify mode dependencies
- Design context-aware alternatives

### Phase 2: Create Context Detection Layer
- Implement `SimulationStateDetector` class
- Add `is_simulation_running()`, `has_simulation_started()` methods
- Wire to simulation controller

### Phase 3: Refactor Click Handlers
- Replace mode checks with context checks
- Unify object selection (works in all contexts)
- Make token manipulation context-aware

### Phase 4: Simplify Palette System
- Remove mode palette
- Make simulation controls always visible
- Update tool palette to show availability

### Phase 5: Update Object Editing
- Rename object "edit mode" to "transform mode"
- Make transform handles context-aware
- Update selection manager API

### Phase 6: Comprehensive Testing
- Test all interactions without explicit modes
- Verify simulation doesn't break editing
- Verify editing restrictions during simulation

### Phase 7: Documentation & Migration
- Update user documentation
- Remove mode-related code
- Clean up event system

---

## Key Design Decisions

### Decision 1: When to Disable Editing?

**Option A**: Disable when simulation is **running** (playing)
- Pro: Can pause and edit
- Con: Might cause inconsistencies

**Option B**: Disable when simulation has **started** (time > 0)
- Pro: Cleaner separation, no inconsistencies
- Con: Must reset to edit

**Recommendation**: **Option B** - Require reset to edit structure
- Clear mental model: "If you've simulated, you're in simulation session"
- Prevents confusing state (edited during simulation)
- Matches scientific workflow: design → simulate → analyze → redesign

### Decision 2: Token Manipulation

**Current**: Only in simulation mode via clicks
**Proposed**: Always available via properties panel

**Alternative**: Click to manipulate tokens anytime
- In design phase: Sets initial marking
- During simulation: Interactive simulation step

**Recommendation**: Click to add tokens **always works**, context-aware:
- Before simulation: Sets initial marking
- During simulation: Adds tokens (like injecting resources)

### Decision 3: Simulation Controls Visibility

**Current**: Only visible in simulation mode
**Proposed**: Always visible, grayed when not applicable

**Benefits**:
- Discovery: Users see they can simulate
- Consistency: Controls don't appear/disappear
- Natural state: Play button shows if simulation ready

---

## Code Changes Required

### Files to Modify

#### High-Impact Changes:
1. **`src/shypn/canvas/canvas_overlay_manager.py`**
   - Remove mode-based palette show/hide
   - Make simulation controls always visible

2. **`src/ui/palettes/mode/mode_palette_loader.py`**
   - Mark as deprecated
   - Eventually remove

3. **`src/shypn/events/mode_events.py`**
   - Deprecate `ModeChangedEvent`
   - Add `SimulationStateChangedEvent` (running/paused/stopped)

4. **`src/shypn/helpers/model_canvas_loader.py`**
   - Remove mode tracking
   - Add simulation state queries

5. **`src/shypn/edit/selection_manager.py`**
   - Rename "edit mode" → "transform mode"
   - Add context-aware restrictions

#### Medium-Impact Changes:
6. **`src/shypn/edit/object_editing_transforms.py`**
   - Update transform handle visibility logic

7. **`src/shypn/engine/simulation/controller.py`**
   - Add `state_changed` signal
   - Expose `is_running()`, `has_started()` methods

8. **Mouse/Event Handlers** (various canvas files)
   - Replace `if current_mode == 'edit'` with context checks
   - Implement unified click behavior

#### Low-Impact Changes:
9. **Documentation updates**
10. **Test updates**
11. **CSS cleanup** (remove mode-specific styling)

---

## Benefits of Unified Approach

### 1. **Better User Experience**
- No mode switching required
- Natural interactions: click to select, click to add tokens
- Fewer UI elements = cleaner interface

### 2. **Simplified Codebase**
- Remove mode tracking logic
- Fewer conditionals
- Single code path for most behaviors

### 3. **Clearer Mental Model**
- "Am I simulating?" → Look at simulation controls (playing?)
- "Can I edit?" → Natural restrictions (can't move during simulation)
- No hidden state (current mode) to track

### 4. **Better Workflow**
- Design → Click play → See results → Adjust tokens → Continue
- No mode switching friction
- Faster iteration

### 5. **Reduced Complexity**
- One less system to maintain
- Fewer edge cases
- Clearer code organization

---

## Risks & Mitigation

### Risk 1: Users Expect Distinct Modes
**Mitigation**: 
- Clear visual feedback (simulation controls state)
- Helpful messages ("Pause simulation to edit structure")
- Progressive disclosure (show what's available)

### Risk 2: Accidental Edits During Simulation
**Mitigation**:
- Lock structure editing when simulation started
- Allow token manipulation (expected interaction)
- Clear reset button to restart

### Risk 3: Confusion About State
**Mitigation**:
- Visual indicators (simulation time, controls state)
- Status bar messages
- Undo/redo still work

### Risk 4: Breaking Existing Workflows
**Mitigation**:
- Phased rollout
- Feature flag to enable/disable
- User testing before full deployment

---

## Next Steps

1. ✅ **Complete analysis** (this document)
2. **Create detailed implementation plan** (next document)
3. **Design simulation state detector**
4. **Prototype unified click behavior**
5. **User testing with prototype**
6. **Full implementation**
7. **Remove mode system**

---

## Appendix: Mode System Code Inventory

### Core Mode Files:
- `src/shypn/events/mode_events.py` - Mode change events
- `src/ui/palettes/mode/mode_palette_loader.py` - Mode switcher UI
- `src/ui/palettes/mode/mode_palette.ui` - Mode switcher GTK UI

### Mode-Dependent Files:
- `src/shypn/canvas/canvas_overlay_manager.py` - Palette visibility logic
- `src/shypn/edit/selection_manager.py` - Selection and transform mode
- `src/shypn/edit/object_editing_transforms.py` - Transform handles
- `src/shypn/helpers/simulate_palette_loader.py` - Simulation palette

### Mode References:
```bash
# Found 50+ references to "mode" in codebase
grep -r "current_mode\|mode.*edit\|mode.*sim" src/
```

---

**Status**: Analysis Complete  
**Next**: Implementation Plan  
**Document**: MODE_SYSTEM_ANALYSIS.md
