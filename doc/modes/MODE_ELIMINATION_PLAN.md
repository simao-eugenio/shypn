# Mode Elimination - Implementation Plan

**Date**: October 18, 2025  
**Objective**: Eliminate explicit edit/simulate modes in favor of context-aware, transparent behavior  
**Status**: Planning Phase

---

## Overview

This document outlines the step-by-step plan to eliminate the mode system and implement context-aware behavior that automatically adapts to what the user is doing.

**Core Principle**: The system should detect user intent and simulation state, not require explicit mode switching.

---

## Implementation Phases

### Phase 1: Foundation - Simulation State Detection ⚡

**Goal**: Create infrastructure to detect simulation state without explicit modes

**Duration**: 1-2 days

#### 1.1 Create SimulationStateDetector

**File**: `src/shypn/engine/simulation/state_detector.py` (NEW)

```python
"""Simulation State Detection - Context-aware simulation state tracking."""

from enum import Enum
from typing import Optional

class SimulationState(Enum):
    """Simulation states."""
    IDLE = "idle"              # No simulation, ready to edit
    STARTED = "started"         # Simulation started but paused
    RUNNING = "running"         # Simulation actively running
    COMPLETED = "completed"     # Simulation finished

class SimulationStateDetector:
    """Detects simulation state for context-aware behavior.
    
    Replaces explicit mode checking with state detection:
    - IDLE: Full editing capability
    - STARTED/PAUSED: View-only for structure, can manipulate tokens
    - RUNNING: Interactive simulation
    - COMPLETED: Can view results, must reset to edit
    """
    
    def __init__(self, controller):
        """Initialize with simulation controller reference."""
        self.controller = controller
        self._state = SimulationState.IDLE
    
    @property
    def state(self) -> SimulationState:
        """Get current simulation state."""
        if self.controller.time == 0.0:
            return SimulationState.IDLE
        elif self.controller.running:
            return SimulationState.RUNNING
        else:
            return SimulationState.STARTED
    
    def is_idle(self) -> bool:
        """Check if simulation is idle (ready to edit)."""
        return self.state == SimulationState.IDLE
    
    def is_running(self) -> bool:
        """Check if simulation is actively running."""
        return self.state == SimulationState.RUNNING
    
    def has_started(self) -> bool:
        """Check if simulation has been started (time > 0)."""
        return self.controller.time > 0.0
    
    def can_edit_structure(self) -> bool:
        """Check if structure editing is allowed."""
        return self.is_idle()
    
    def can_manipulate_tokens(self) -> bool:
        """Check if token manipulation is allowed."""
        return True  # Always allowed (design or interactive simulation)
    
    def can_move_objects(self) -> bool:
        """Check if objects can be moved."""
        return self.is_idle()
    
    def get_restriction_message(self, action: str) -> Optional[str]:
        """Get user-friendly message for why action is restricted."""
        if action in ['create', 'delete', 'move']:
            if self.has_started():
                return "Reset simulation to edit structure"
        return None
```

**Integration Points**:
- Wire to `SimulationController`
- Add to `ModelCanvasManager`
- Use in event handlers

#### 1.2 Update SimulationController

**File**: `src/shypn/engine/simulation/controller.py` (MODIFY)

**Changes**:
```python
class SimulationController:
    """Add state change signals and queries."""
    
    __gsignals__ = {
        'state-changed': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        # Emits SimulationState enum value
    }
    
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.time = 0.0
        self.running = False
        
        # NEW: State detector
        from shypn.engine.simulation.state_detector import SimulationStateDetector
        self.state_detector = SimulationStateDetector(self)
    
    def start(self):
        """Start simulation."""
        self.running = True
        self.emit('state-changed', self.state_detector.state)
    
    def pause(self):
        """Pause simulation."""
        self.running = False
        self.emit('state-changed', self.state_detector.state)
    
    def reset(self):
        """Reset simulation to initial state."""
        self.time = 0.0
        self.running = False
        self.emit('state-changed', self.state_detector.state)
    
    # NEW: Query methods
    def is_running(self) -> bool:
        """Check if simulation is running."""
        return self.running
    
    def has_started(self) -> bool:
        """Check if simulation has started."""
        return self.time > 0.0
    
    def can_edit_structure(self) -> bool:
        """Check if structure editing is allowed."""
        return self.state_detector.can_edit_structure()
```

#### 1.3 Wire to ModelCanvasManager

**File**: `src/shypn/data/model_canvas_manager.py` (MODIFY)

**Changes**:
```python
class ModelCanvasManager:
    """Add simulation state queries."""
    
    def __init__(self, ...):
        # Existing code...
        self.simulation_controller = None  # Set externally
    
    def set_simulation_controller(self, controller):
        """Set simulation controller reference."""
        self.simulation_controller = controller
    
    def can_edit_structure(self) -> bool:
        """Check if structure can be edited."""
        if self.simulation_controller:
            return self.simulation_controller.can_edit_structure()
        return True  # No simulation = can edit
    
    def can_move_objects(self) -> bool:
        """Check if objects can be moved."""
        if self.simulation_controller:
            return self.simulation_controller.state_detector.can_move_objects()
        return True
    
    def get_simulation_state(self):
        """Get current simulation state."""
        if self.simulation_controller:
            return self.simulation_controller.state_detector.state
        return None
```

**Testing**:
- Create unit tests for `SimulationStateDetector`
- Verify state transitions: IDLE → RUNNING → STARTED → IDLE
- Test restriction queries

---

### Phase 2: Parameter Persistence System 🔒 **[CRITICAL - DATA INTEGRITY]**

**Goal**: Ensure simulation parameter changes are atomic, validated, and reliable

**Duration**: 2-3 days

**Priority**: CRITICAL - Must implement before production use

**Problem**: Without this, rapid UI changes (sliders, spinners) during simulation create race conditions where:
- Simulation reads inconsistent parameter values mid-update
- Results become unreliable and non-reproducible
- Data integrity is compromised

**Solution**: Buffered writes with explicit commit points

#### 2.1 Create BufferedSimulationSettings

**File**: `src/shypn/engine/simulation/buffered_settings.py` (NEW)

**Purpose**: Wrap SimulationSettings with transaction support

```python
"""Buffered Simulation Settings - Atomic Parameter Updates."""

class BufferedSimulationSettings:
    """Settings wrapper with buffered writes and atomic commits.
    
    Key Features:
    - Write buffering: UI changes write to buffer, not live settings
    - Explicit commit: Changes only applied when commit() called
    - Validation before commit: All validation before any change
    - Rollback support: Can undo uncommitted changes
    - Thread-safe: Lock protects concurrent access
    
    Usage:
        # Create buffered wrapper
        buffered = BufferedSimulationSettings(controller.settings)
        
        # UI changes write to buffer (not live)
        buffered.buffer.time_scale = 10.0
        buffered.buffer.duration = 60.0
        buffered.mark_dirty()
        
        # Commit atomically (or rollback on validation error)
        if buffered.commit():
            print("Applied")
        else:
            print("Validation failed, rolled back")
    """
    
    def __init__(self, live_settings: SimulationSettings):
        self._live = live_settings
        self._buffer = None
        self._lock = threading.Lock()
        self._dirty = False
    
    @property
    def live(self) -> SimulationSettings:
        """Get live settings (used by simulation engine)."""
        return self._live
    
    @property
    def buffer(self) -> SimulationSettings:
        """Get buffer for editing (changes not yet committed)."""
        if self._buffer is None:
            self._buffer = self._clone_settings(self._live)
        return self._buffer
    
    def commit(self) -> bool:
        """Atomically commit buffered changes."""
        if not self._dirty:
            return True
        
        with self._lock:
            try:
                self._validate_buffer()
                self._apply_buffer_to_live()
                self._buffer = None
                self._dirty = False
                return True
            except ValueError:
                return False
    
    def rollback(self):
        """Discard uncommitted changes."""
        self._buffer = None
        self._dirty = False


class SettingsTransaction:
    """Context manager for atomic transactions.
    
    Usage:
        with SettingsTransaction(buffered_settings) as txn:
            txn.settings.time_scale = 10.0
            txn.settings.duration = 60.0
            # Auto-commits on success, auto-rolls-back on exception
    """
    
    def __init__(self, buffered_settings):
        self.buffered = buffered_settings
        self.settings = buffered_settings.buffer
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            success = self.buffered.commit()
            if not success:
                self.buffered.rollback()
        else:
            self.buffered.rollback()
        return False
```

#### 2.2 Create Debounced UI Controls

**File**: `src/shypn/ui/controls/debounced_parameter.py` (NEW)

**Purpose**: Prevent rapid UI changes from spamming simulation

```python
"""Debounced Parameter Controls - Prevent Rapid Update Spam."""

class DebouncedSpinButton:
    """Spin button with debounced value changes.
    
    Fires callback only after user stops changing value for
    specified delay (default 300ms).
    
    Prevents: 100 events during slider drag
    Ensures: Only final value committed
    
    Usage:
        spin = DebouncedSpinButton(
            adjustment=time_scale_adjustment,
            delay_ms=300,
            on_commit=lambda v: buffered_settings.buffer.time_scale = v
        )
    """
    
    def __init__(self, adjustment, delay_ms=300, on_commit=None):
        self.adjustment = adjustment
        self.delay_ms = delay_ms
        self.on_commit = on_commit
        self._pending_timeout = None
        
        adjustment.connect('value-changed', self._on_value_changed)
    
    def _on_value_changed(self, adjustment):
        """Handle value changed (debounced)."""
        # Cancel pending timeout
        if self._pending_timeout:
            GLib.source_remove(self._pending_timeout)
        
        # Schedule commit after delay
        new_value = adjustment.get_value()
        self._pending_timeout = GLib.timeout_add(
            self.delay_ms,
            self._commit_value,
            new_value
        )
    
    def _commit_value(self, value):
        """Commit value after debounce delay."""
        self._pending_timeout = None
        if self.on_commit:
            self.on_commit(value)
        return False  # Remove timeout


class DebouncedEntry:
    """Entry field with debounced text changes.
    
    Features:
    - Validates input before committing
    - Reverts to last valid value on error
    - Fires callback only after user stops typing
    
    Usage:
        entry = DebouncedEntry(
            gtk_entry=dt_manual_entry,
            delay_ms=500,
            validator=lambda t: float(t) > 0,
            on_commit=lambda t: buffered_settings.buffer.dt_manual = float(t)
        )
    """
    
    def __init__(self, gtk_entry, delay_ms=500, validator=None, on_commit=None):
        self.entry = gtk_entry
        self.delay_ms = delay_ms
        self.validator = validator
        self.on_commit = on_commit
        self._pending_timeout = None
        self._last_valid_text = gtk_entry.get_text()
        
        gtk_entry.connect('changed', self._on_text_changed)
    
    def _commit_text(self, text):
        """Commit text after validation."""
        if self.validator:
            try:
                if not self.validator(text):
                    self.entry.set_text(self._last_valid_text)
                    return False
            except Exception:
                self.entry.set_text(self._last_valid_text)
                return False
        
        self._last_valid_text = text
        if self.on_commit:
            self.on_commit(text)
        return False
```

#### 2.3 Update Settings Dialog with Transactions

**File**: `src/shypn/dialogs/simulation_settings_dialog.py` (MODIFY)

**Changes**:
```python
class SimulationSettingsDialog(Gtk.Dialog):
    """Dialog with atomic transaction support."""
    
    def __init__(self, buffered_settings, parent=None):
        super().__init__(...)
        
        # Work with BUFFER, not live settings
        self.buffered_settings = buffered_settings
        self.settings = buffered_settings.buffer
        
        # Use debounced controls
        self.time_scale_control = DebouncedSpinButton(
            adjustment=self.time_scale_adjustment,
            on_commit=lambda v: self._update_buffer('time_scale', v)
        )
    
    def _update_buffer(self, property_name, value):
        """Update buffer and mark dirty."""
        setattr(self.settings, property_name, value)
        self.buffered_settings.mark_dirty()
    
    def run_and_apply(self):
        """Run dialog with transaction support."""
        response = self.run()
        
        if response == Gtk.ResponseType.OK:
            # Force commit pending debounced changes
            self.time_scale_control.force_commit()
            
            # Try atomic commit
            success = self.buffered_settings.commit()
            
            if not success:
                self._show_error("Invalid Settings", "Validation failed")
            
            self.destroy()
            return success
        else:
            # Cancelled - rollback
            self.buffered_settings.rollback()
            self.destroy()
            return False
```

#### 2.4 Wire to Simulation Controller

**File**: `src/shypn/engine/simulation/controller.py` (MODIFY)

**Changes**:
```python
class SimulationController:
    """Controller with buffered settings support."""
    
    def __init__(self, model):
        # Create live settings
        self._settings = SimulationSettings()
        
        # Wrap in buffered settings for safe UI updates
        self.buffered_settings = BufferedSimulationSettings(self._settings)
    
    @property
    def settings(self):
        """Get LIVE settings (used by simulation engine).
        
        WARNING: UI should use buffered_settings.buffer, not this!
        """
        return self._settings
    
    def step(self):
        """Execute step using LIVE settings only."""
        dt = self._settings.get_effective_dt()  # Read from live, not buffer
        self._execute_step(dt)
```

#### 2.5 Add UI Commit/Revert Buttons

**Pattern**: Show pending changes indicator when buffer dirty

```
┌────────────────────────────────────────┐
│ Simulation Controls                    │
│                                        │
│ Time Scale: [====●====] 10.0x         │
│ Duration:   [========] 60.0 s         │
│                                        │
│ ⚠️  Changes pending                    │
│ [Apply Changes]  [Revert]             │
└────────────────────────────────────────┘
```

**Behavior**:
- User adjusts sliders → Buffer updated, indicator appears
- Click "Apply Changes" → `buffered_settings.commit()`
- Click "Revert" → `buffered_settings.rollback()`

**Testing**:
- Test rapid slider drag → Only final value committed
- Test settings dialog Cancel → Rollback works
- Test invalid value → Validation prevents commit
- Test multi-property change → Atomic (all or nothing)

---

### Phase 3: Unify Click Behavior 🖱️

**Goal**: Make canvas clicks context-aware instead of mode-dependent

**Duration**: 2-3 days

#### 3.1 Create Unified Click Handler

**File**: `src/shypn/canvas/unified_interaction.py` (NEW)

```python
"""Unified Canvas Interaction - Context-aware click and drag handling."""

class UnifiedInteractionHandler:
    """Handles canvas interactions in a context-aware manner.
    
    Replaces mode-based branching with intent detection:
    - Detects what user clicked (place, transition, arc, empty space)
    - Detects simulation state
    - Determines appropriate behavior
    """
    
    def __init__(self, manager, simulation_controller):
        self.manager = manager
        self.sim_controller = simulation_controller
        self.active_tool = 'select'  # Current tool
    
    def handle_click(self, x, y, event):
        """Unified click handler - context-aware."""
        
        # Find what was clicked
        clicked_obj = self.manager.find_object_at(x, y)
        
        # No object clicked - empty space
        if clicked_obj is None:
            return self._handle_empty_click(x, y, event)
        
        # Object clicked - determine behavior
        obj_type = type(clicked_obj).__name__
        
        if obj_type == 'Place':
            return self._handle_place_click(clicked_obj, event)
        elif obj_type == 'Transition':
            return self._handle_transition_click(clicked_obj, event)
        elif obj_type == 'Arc':
            return self._handle_arc_click(clicked_obj, event)
    
    def _handle_place_click(self, place, event):
        """Context-aware place click.
        
        Behavior depends on:
        - Current tool
        - Modifier keys (Shift, Ctrl)
        - Simulation state
        """
        
        # Token manipulation (works in any state)
        if event.shift_held:
            # Shift+click: Remove token
            place.tokens = max(0, place.tokens - 1)
            return 'token_removed'
        elif event.ctrl_held:
            # Ctrl+click: Add token
            place.tokens += 1
            return 'token_added'
        
        # Simple click: Selection or token addition
        if self.active_tool == 'select':
            self.manager.selection_manager.select(place)
            return 'selected'
        elif self.active_tool == 'token':
            # Token tool: Click to add
            place.tokens += 1
            return 'token_added'
        
        # Arc tool: Create arc from place
        elif self.active_tool == 'arc':
            if self.sim_controller.can_edit_structure():
                self.start_arc_creation(place)
                return 'arc_started'
            else:
                self.show_restriction_message('create arc')
                return 'restricted'
    
    def _handle_empty_click(self, x, y, event):
        """Click on empty canvas.
        
        Behavior:
        - Place tool: Create place
        - Transition tool: Create transition
        - Select tool: Clear selection
        """
        
        if self.active_tool == 'place':
            if self.sim_controller.can_edit_structure():
                self.manager.add_place(x, y)
                return 'place_created'
            else:
                self.show_restriction_message('create place')
                return 'restricted'
        
        elif self.active_tool == 'transition':
            if self.sim_controller.can_edit_structure():
                self.manager.add_transition(x, y)
                return 'transition_created'
            else:
                self.show_restriction_message('create transition')
                return 'restricted'
        
        elif self.active_tool == 'select':
            self.manager.selection_manager.clear()
            return 'cleared'
    
    def handle_drag(self, obj, dx, dy):
        """Context-aware drag handler."""
        
        if self.sim_controller.can_move_objects():
            obj.x += dx
            obj.y += dy
            return 'moved'
        else:
            self.show_restriction_message('move objects')
            return 'restricted'
    
    def show_restriction_message(self, action):
        """Show user-friendly restriction message."""
        msg = self.sim_controller.state_detector.get_restriction_message(action)
        if msg:
            # Show in status bar or notification
            print(f"[Restriction] {msg}")
```

#### 3.2 Replace Mode-Based Click Handlers

**Files to Modify**:
- `src/shypn/canvas/model_canvas.py` (or wherever canvas events are handled)
- Remove `if current_mode == 'edit':` branches
- Replace with `unified_handler.handle_click()`

**Before**:
```python
def on_button_press(self, widget, event):
    if self.current_mode == 'edit':
        # Edit mode click behavior
        obj = self.find_object_at(event.x, event.y)
        if obj:
            self.select_object(obj)
    elif self.current_mode == 'simulate':
        # Simulation mode click behavior
        place = self.find_place_at(event.x, event.y)
        if place:
            place.tokens += 1
```

**After**:
```python
def on_button_press(self, widget, event):
    self.unified_handler.handle_click(event.x, event.y, event)
```

**Testing**:
- Test click on place: selects in idle, adds token in simulation
- Test click on empty: creates object when allowed, shows message when restricted
- Test drag: moves object when allowed, shows message when restricted

---

### Phase 4: Always-Visible Simulation Controls 🎮

**Goal**: Make simulation controls always visible, grayed when not applicable

**Duration**: 1-2 days

#### 4.1 Redesign Simulation Palette

**File**: `src/shypn/helpers/simulate_palette_loader.py` (MODIFY)

**Changes**:
```python
class SimulatePaletteLoader:
    """Always-visible simulation controls (not mode-dependent)."""
    
    def __init__(self):
        # Remove mode tracking
        # self.current_mode = 'simulate'  # DELETE THIS
        
        # Add simulation state listener
        self.simulation_controller = None
    
    def set_simulation_controller(self, controller):
        """Wire to simulation controller."""
        self.simulation_controller = controller
        controller.connect('state-changed', self._on_state_changed)
    
    def _on_state_changed(self, controller, state):
        """Update button states based on simulation state."""
        
        # IDLE: Play enabled, others disabled
        if state == SimulationState.IDLE:
            self.play_button.set_sensitive(True)
            self.pause_button.set_sensitive(False)
            self.stop_button.set_sensitive(False)
        
        # RUNNING: Pause enabled, play disabled
        elif state == SimulationState.RUNNING:
            self.play_button.set_sensitive(False)
            self.pause_button.set_sensitive(True)
            self.stop_button.set_sensitive(True)
        
        # STARTED (paused): Play and stop enabled
        elif state == SimulationState.STARTED:
            self.play_button.set_sensitive(True)
            self.pause_button.set_sensitive(False)
            self.stop_button.set_sensitive(True)
```

**Visual Design**:
```
┌─────────────────────────────────────────┐
│ Simulation Controls                     │
│                                         │
│  ⏵ Play  ⏸ Pause  ⏹ Reset  ⏱ 0.00s   │
│  [Grayed when not applicable]          │
└─────────────────────────────────────────┘
```

#### 4.2 Update Canvas Overlay Manager

**File**: `src/shypn/canvas/canvas_overlay_manager.py` (MODIFY)

**Remove**:
```python
# DELETE mode-based show/hide logic
def _on_mode_changed(self, mode_palette, new_mode):
    if new_mode == 'edit':
        self._hide_simulate_palettes()  # DELETE
    elif new_mode == 'sim':
        self._show_simulate_palettes()  # DELETE
```

**Add**:
```python
# Simulation controls always visible (at top or bottom)
def _setup_simulation_controls(self):
    """Add always-visible simulation controls."""
    self.sim_palette = SimulatePaletteLoader()
    sim_widget = self.sim_palette.load()
    
    # Position at bottom center (always visible)
    self.overlay.add_overlay(sim_widget)
    self.overlay.set_overlay_pass_through(sim_widget, True)
    
    # Halign/valign to position
    sim_widget.set_halign(Gtk.Align.CENTER)
    sim_widget.set_valign(Gtk.Align.END)
```

**Testing**:
- Verify controls visible on app start
- Test state transitions (buttons enable/disable correctly)
- Verify grayed buttons don't respond to clicks

---

### Phase 5: Deprecate Mode Palette 🗑️

**Goal**: Remove mode switcher UI and related code

**Duration**: 1 day

#### 5.1 Remove Mode Palette from UI

**File**: `src/shypn/canvas/canvas_overlay_manager.py` (MODIFY)

**Remove**:
```python
# DELETE mode palette creation
def _create_mode_palette(self):
    from ui.palettes.mode.mode_palette_loader import create_mode_palette
    self.mode_palette = create_mode_palette()  # DELETE
    # ... connection and positioning code ... # DELETE
```

#### 5.2 Mark Mode Files as Deprecated

**File**: `src/ui/palettes/mode/mode_palette_loader.py` (MODIFY)

Add deprecation notice:
```python
"""DEPRECATED: Mode palette no longer needed with context-aware system.

This file is kept for reference but should not be used in new code.
The application now uses simulation state detection instead of explicit modes.

See: doc/modes/MODE_ELIMINATION_PLAN.md
"""

import warnings
warnings.warn(
    "mode_palette_loader is deprecated. Use simulation state detection instead.",
    DeprecationWarning,
    stacklevel=2
)
```

#### 5.3 Remove Mode Change Events

**File**: `src/shypn/events/mode_events.py` (MODIFY)

```python
# Deprecate ModeChangedEvent
class ModeChangedEvent(BaseEvent):
    """DEPRECATED: Use SimulationStateChangedEvent instead."""
    
    def __init__(self, old_mode, new_mode):
        warnings.warn(
            "ModeChangedEvent is deprecated",
            DeprecationWarning
        )
        super().__init__()
        self.old_mode = old_mode
        self.new_mode = new_mode
```

**Add**:
```python
# NEW event for simulation state
class SimulationStateChangedEvent(BaseEvent):
    """Event fired when simulation state changes."""
    
    def __init__(self, old_state, new_state):
        super().__init__()
        self.old_state = old_state  # SimulationState enum
        self.new_state = new_state
```

**Testing**:
- Verify app starts without mode palette
- Verify simulation controls work without mode switcher
- Verify editing works without mode switcher

---

### Phase 6: Clean Up Selection Manager Naming 🏷️

**Goal**: Rename object "edit mode" to "transform mode" to avoid confusion

**Duration**: 1 day

#### 6.1 Rename SelectionManager Methods

**File**: `src/shypn/edit/selection_manager.py` (MODIFY)

**Rename**:
```python
class SelectionManager:
    # Old names (confusing)
    def enter_edit_mode(self, obj):         # RENAME
    def exit_edit_mode(self):               # RENAME
    def is_edit_mode(self) -> bool:         # RENAME
    def get_edit_target(self):              # RENAME
    
    # New names (clear)
    def enter_transform_mode(self, obj):
        """Enter transform mode for object (shows handles)."""
        self.exit_transform_mode()
        self.transform_target = obj
    
    def exit_transform_mode(self):
        """Exit transform mode (hides handles)."""
        self.transform_target = None
    
    def is_transform_mode(self) -> bool:
        """Check if object is in transform mode."""
        return self.transform_target is not None
    
    def get_transform_target(self):
        """Get object in transform mode."""
        return self.transform_target
```

#### 6.2 Update References

**Files to Update**:
- `src/shypn/edit/object_editing_transforms.py`
- `src/shypn/canvas/*.py` (canvas interaction files)
- Any file referencing `selection_manager.enter_edit_mode()`

**Find and Replace**:
```bash
# Find all references
grep -r "enter_edit_mode\|exit_edit_mode\|is_edit_mode" src/

# Replace:
enter_edit_mode → enter_transform_mode
exit_edit_mode → exit_transform_mode
is_edit_mode → is_transform_mode
edit_target → transform_target
```

**Testing**:
- Test double-click object → Transform handles appear
- Test ESC key → Transform mode exits
- Verify transform mode independent of simulation state

---

### Phase 7: Update Tool Palette 🔧

**Goal**: Show tool availability based on context, not mode

**Duration**: 1-2 days

#### 7.1 Context-Aware Tool Graying

**File**: `src/shypn/edit/tools_palette_new.py` (MODIFY)

**Changes**:
```python
class ToolsPaletteNew:
    """Tools palette with context-aware availability."""
    
    def __init__(self):
        self.simulation_controller = None
        self.tools = {
            'select': self.select_button,
            'place': self.place_button,
            'transition': self.transition_button,
            'arc': self.arc_button,
            'token': self.token_button,
        }
    
    def set_simulation_controller(self, controller):
        """Wire to simulation controller for state updates."""
        self.simulation_controller = controller
        controller.connect('state-changed', self._update_tool_availability)
    
    def _update_tool_availability(self, controller, state):
        """Update which tools are available based on state."""
        
        # IDLE: All tools available
        if state == SimulationState.IDLE:
            for tool_button in self.tools.values():
                tool_button.set_sensitive(True)
                tool_button.set_tooltip_text("")
        
        # RUNNING or STARTED: Only select and token tools available
        else:
            for tool_name, tool_button in self.tools.items():
                if tool_name in ['select', 'token']:
                    tool_button.set_sensitive(True)
                    tool_button.set_tooltip_text("")
                else:
                    tool_button.set_sensitive(False)
                    tool_button.set_tooltip_text(
                        "Reset simulation to use this tool"
                    )
```

**Visual Feedback**:
```
┌─────────────────────────┐
│ Tools                   │
│  [👆] Select   (active) │
│  [○] Place     (grayed) │
│  [□] Transition(grayed) │
│  [→] Arc       (grayed) │
│  [●] Token     (active) │
└─────────────────────────┘
```

**Testing**:
- Start simulation → Place/Transition/Arc tools gray out
- Reset simulation → All tools available again
- Hover grayed tool → Tooltip explains why disabled

---

### Phase 8: Comprehensive Testing 🧪

**Goal**: Ensure all interactions work without explicit modes

**Duration**: 2-3 days

#### 8.1 Integration Test Suite

**File**: `tests/integration/test_mode_elimination.py` (NEW)

```python
"""Integration tests for mode-free operation."""

class TestModeElimination:
    """Test that app works without explicit modes."""
    
    def test_click_place_in_idle_state(self):
        """Clicking place in idle state selects it."""
        # Setup
        manager = create_test_manager()
        place = manager.add_place(100, 100)
        
        # Click place
        handler = UnifiedInteractionHandler(manager, sim_controller)
        result = handler.handle_click(100, 100, mock_event)
        
        # Assert selected
        assert result == 'selected'
        assert place in manager.selection_manager.selected
    
    def test_click_place_during_simulation(self):
        """Clicking place during simulation is still selection."""
        # Setup
        manager = create_test_manager()
        place = manager.add_place(100, 100)
        sim_controller = SimulationController(manager)
        sim_controller.start()
        
        # Click place
        handler = UnifiedInteractionHandler(manager, sim_controller)
        result = handler.handle_click(100, 100, mock_event)
        
        # Assert selected (not added token - use Ctrl+click for that)
        assert result == 'selected'
    
    def test_ctrl_click_adds_token_anytime(self):
        """Ctrl+click adds token in any state."""
        # Idle state
        place = manager.add_place(100, 100)
        place.tokens = 5
        handler.handle_click(100, 100, ctrl_event)
        assert place.tokens == 6
        
        # Running state
        sim_controller.start()
        handler.handle_click(100, 100, ctrl_event)
        assert place.tokens == 7
    
    def test_create_place_blocked_during_simulation(self):
        """Creating place blocked when simulation started."""
        sim_controller.start()
        handler.active_tool = 'place'
        result = handler.handle_click(100, 100, mock_event)
        
        assert result == 'restricted'
        # Verify no place created
    
    def test_move_object_blocked_during_simulation(self):
        """Moving objects blocked when simulation started."""
        place = manager.add_place(100, 100)
        sim_controller.start()
        
        result = handler.handle_drag(place, 50, 50)
        
        assert result == 'restricted'
        assert place.x == 100  # Didn't move
    
    def test_simulation_controls_state_transitions(self):
        """Simulation controls update based on state."""
        palette = SimulatePaletteLoader()
        palette.set_simulation_controller(sim_controller)
        
        # IDLE: Play enabled, others disabled
        assert palette.play_button.get_sensitive() == True
        assert palette.pause_button.get_sensitive() == False
        
        # Start simulation
        sim_controller.start()
        
        # RUNNING: Pause enabled, play disabled
        assert palette.play_button.get_sensitive() == False
        assert palette.pause_button.get_sensitive() == True
```

#### 8.2 Manual Test Checklist

**Workflow Tests**:
- [ ] Start app → Canvas loads without mode palette
- [ ] Click place → Place selected (no mode switch needed)
- [ ] Ctrl+click place → Token added
- [ ] Click Play → Simulation starts
- [ ] Try to create place → Shows restriction message
- [ ] Click Pause → Simulation pauses
- [ ] Move object → Shows restriction message
- [ ] Click Reset → Simulation resets
- [ ] Move object → Object moves (editing unlocked)

**Tool Tests**:
- [ ] Select tool → Works in all states
- [ ] Place tool → Works in idle, grayed during simulation
- [ ] Transition tool → Works in idle, grayed during simulation
- [ ] Arc tool → Works in idle, grayed during simulation
- [ ] Token tool → Works in all states (Ctrl+click equivalent)

**Edge Cases**:
- [ ] Start simulation → Pause → Reset → Should return to full editing
- [ ] Create place → Start sim → Reset → Create another place
- [ ] Select object → Double-click → Transform handles appear
- [ ] During simulation → Double-click → Transform handles hidden

---

### Phase 9: Documentation & Cleanup 📚

**Goal**: Update documentation and remove obsolete code

**Duration**: 1-2 days

#### 9.1 Update User Documentation

**Files to Create**:
- `doc/user/INTERACTION_GUIDE.md` - How to interact without modes
- `doc/user/SIMULATION_WORKFLOW.md` - New simulation workflow

**Key Points**:
- No mode switching needed
- Click to select, Ctrl+click to manipulate tokens
- Simulation controls always visible
- Clear restrictions (shown when needed)

#### 9.2 Update Developer Documentation

**Files to Create**:
- `doc/dev/CONTEXT_AWARE_DESIGN.md` - Design principles
- `doc/dev/SIMULATION_STATE_API.md` - API reference

#### 9.3 Remove Obsolete Code

**Files to Delete**:
- `src/ui/palettes/mode/mode_palette_loader.py`
- `src/ui/palettes/mode/mode_palette.ui`
- `tests/test_mode_palette.py`

**Files to Clean**:
- Remove mode-related CSS
- Remove mode-related comments
- Update ARCHITECTURE.md

#### 9.4 Migration Guide

**File**: `doc/MIGRATION_FROM_MODES.md` (NEW)

For any external code or plugins:
```markdown
# Migration from Mode System

## What Changed

- Removed: Explicit edit/simulate mode switching
- Added: Context-aware behavior based on simulation state

## API Changes

### Before:
```python
if canvas.current_mode == 'edit':
    # Edit behavior
elif canvas.current_mode == 'simulate':
    # Simulate behavior
```

### After:
```python
if simulation_controller.can_edit_structure():
    # Edit behavior
else:
    # Show restriction
```

## Method Renames

| Old | New | Notes |
|-----|-----|-------|
| `enter_edit_mode()` | `enter_transform_mode()` | Clearer naming |
| `is_edit_mode()` | `is_transform_mode()` | Object transformation |
| `ModeChangedEvent` | `SimulationStateChangedEvent` | Different concept |
```

---

## Success Criteria

### Phase 1 (Foundation)
- ✅ `SimulationStateDetector` implemented and tested
- ✅ Context-aware restriction queries working

### Phase 2 (Parameter Persistence) **[CRITICAL]**
- ✅ `BufferedSimulationSettings` implemented
- ✅ Debounced UI controls working
- ✅ Settings dialog with transactions
- ✅ Commit/rollback UI tested
- ✅ No race conditions in parameter updates

### Phase 3 (Click Unification)
- ✅ Click behavior unified (no mode checks)
- ✅ Context-aware interactions working

### Phase 4-5 (UI Updates)
- ✅ Simulation controls always visible
- ✅ Controls update based on state (grayed when not applicable)
- ✅ Mode palette removed from UI

### Phase 6-7 (Refinements)
- ✅ Selection manager renamed (no "edit mode" confusion)
- ✅ Tool palette shows availability dynamically
- ✅ Tooltips explain restrictions

### Phase 8 (Validation)
- ✅ Integration tests pass
- ✅ Manual test checklist complete
- ✅ No regression in existing features
- ✅ Parameter persistence tests pass

### Phase 9 (Finalization)
- ✅ Documentation updated
- ✅ Obsolete code removed
- ✅ Migration guide published

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Foundation | 1-2 days | None |
| **Phase 2: Parameter Persistence** | **2-3 days** | **Phase 1** |
| Phase 3: Click Unification | 2-3 days | Phase 1 |
| Phase 4: Always-Visible Controls | 1-2 days | Phase 1, 2 |
| Phase 5: Deprecate Mode Palette | 1 day | Phase 3, 4 |
| Phase 6: Rename Selection Manager | 1 day | Phase 5 |
| Phase 7: Update Tool Palette | 1-2 days | Phase 1, 2 |
| Phase 8: Testing | 2-3 days | All phases |
| Phase 9: Documentation | 1-2 days | Phase 8 |

**Total Estimated Time**: 12-19 days (2.5-4 weeks)

**Critical Path**: Phase 1 → Phase 2 → Phase 4 → Testing

---

## Risk Management

### High-Risk Areas
1. **Parameter race conditions** - Race conditions in parameter updates during simulation
2. **Click behavior changes** - Thoroughly test all interactions
3. **Simulation state transitions** - Verify all edge cases
4. **Tool availability logic** - Test graying/enabling
5. **Data integrity** - Ensure results reproducible and reliable

### Mitigation Strategies
1. **Parameter persistence FIRST** - Implement Phase 2 before allowing production use
2. **Feature flag** - Add `USE_MODE_FREE=True/False` to toggle old/new system
3. **Phased rollout** - Enable for beta testers first
4. **Rollback plan** - Keep mode system code in git history
5. **User feedback** - Collect feedback early, iterate
6. **Extensive testing** - Integration tests for parameter updates

### Rollback Triggers
- **Data integrity issues** - Simulation results not reproducible
- **Race conditions** - Parameter corruption during updates
- Major bugs in click handling
- User confusion about restrictions
- Performance issues with state detection
- Regression in core features

---

## Next Actions

1. ✅ Review this plan with team
2. **Start Phase 1**: Implement `SimulationStateDetector`
3. **START PHASE 2 IMMEDIATELY**: Implement `BufferedSimulationSettings` (CRITICAL for data integrity)
4. **Prototype**: Create proof-of-concept for unified clicks
5. **User Testing**: Test prototype with sample users (especially parameter persistence)
6. **Proceed or Iterate**: Based on feedback

## Critical Dependencies

⚠️ **BLOCKER**: Phase 2 (Parameter Persistence) must complete before production use
- Without this: Simulation results unreliable
- Data integrity compromised
- Cannot reproduce results
- Scientific validity questionable

✅ **Safe to release** only after:
- Phase 1 (State Detection) complete
- Phase 2 (Parameter Persistence) complete and tested
- Integration tests pass for parameter updates
- Manual testing confirms no race conditions

---

**Status**: Ready to Implement  
**Estimated Start**: After plan approval  
**Document**: MODE_ELIMINATION_PLAN.md
