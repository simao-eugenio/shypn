# Simple Panel Fix Plan - Wayland Error 71

**Date:** October 21, 2025  
**Problem:** Malformed parenting, orphaned widgets, create/destroy causing Wayland crashes  
**Goal:** Simple, clean panel show/hide without widget reparenting

---

## 🎯 THE CORE PROBLEM (In Simple Terms)

**What You Have:**
- 4 Panels: Files, Analyses, Pathways, Topology
- Each panel can: **Attach** (dock to main window) or **Float** (separate window)
- Master Palette buttons control which panel is visible

**What's Breaking:**
```
Widget reparenting after window.show_all() → Wayland Error 71 → Crash
```

**Why It Happens:**
1. Panel content starts in a GtkWindow (`left_panel_window`)
2. At startup, content moves to GtkStack container (GOOD - happens before show_all)
3. User clicks button → Code tries to `container.add(self.content)` (BAD - after show_all)
4. Wayland sees widget moving between parents → Protocol Error 71

---

## 🔍 CURRENT ARCHITECTURE (What You Built)

### Panel States

**State 1: Attached (Docked)**
```
Main Window
└── GtkStack (left_dock_stack)
    ├── files_panel_container ← Panel content lives here
    ├── analyses_panel_container
    ├── pathways_panel_container
    └── topology_panel_container
```

**State 2: Floating (Separate Window)**
```
Panel Window
└── Panel content moved here
```

**State 3: Hidden**
```
Content removed from both → ORPHANED WIDGET!
```

---

## ❌ WHAT'S BROKEN

### Problem 1: Widget Reparenting
```python
# In attach_to() - WRONG APPROACH (still in code)
if self.content.get_parent() == self.window:
    self.window.remove(self.content)  # Remove from window
container.add(self.content)  # Add to container ← CRASH on Wayland
```

### Problem 2: Orphaned Widgets
```python
# In hide() - Creates orphaned widgets
self.parent_container.remove(self.content)  # Widget has NO parent now
# Content is orphaned → Can't be shown again
```

### Problem 3: Multiple Add/Remove Cycles
```python
# Float → Attach → Float → Attach
# Each cycle does add/remove → Multiple Wayland errors
```

---

## ✅ THE SIMPLE FIX

### Rule #1: Widget Lives in ONE Place
**Panel content has ONLY TWO permanent homes:**
1. **Stack container** (when attached)
2. **Panel window** (when floating)

**NEVER remove widget unless immediately adding to other parent!**

### Rule #2: No Reparenting After show_all()
**All initial setup happens BEFORE window.show_all():**
```python
# In shypn.py - startup sequence
loader.load()  # Loads UI, moves content to stack
# ... setup all 4 panels ...
window.show_all()  # NOW show window (widgets already in place)
```

### Rule #3: Show/Hide via Visibility, Not Reparenting
**Instead of add/remove, just toggle visibility:**
```python
# WRONG - causes Error 71
container.remove(widget)
container.add(widget)

# RIGHT - no reparenting
stack.set_visible_child_name('files')  # Show Files panel
stack.set_visible(False)  # Hide all panels
```

---

## 📋 IMPLEMENTATION PLAN

### Phase 1: Clean Up Panel Loader API (2 hours)

**Simplify to 3 operations:**

#### 1. `attach()` - Show panel in main window
```python
def attach(self, parent_window=None):
    """Show panel attached to main window (in GtkStack).
    
    NO widget reparenting - content already in stack!
    Just update state and notify callbacks.
    """
    if self.is_attached:
        return  # Already attached
    
    # If floating, move content back to stack (ONE TIME operation)
    if self.window.get_visible():
        self.window.hide()
        self.window.remove(self.content)
        self.stack_container.add(self.content)
    
    self.is_attached = True
    
    # Update float button if exists
    if self.float_button:
        self.float_button.set_active(False)
    
    # Store parent for dialogs
    if parent_window:
        self.parent_window = parent_window
    
    # Notify callback (for paned position)
    if self.on_attach_callback:
        self.on_attach_callback()
```

#### 2. `float()` - Show panel in separate window
```python
def float(self, parent_window=None):
    """Show panel in separate floating window.
    
    Moves content from stack to window (ONE TIME operation).
    """
    if not self.is_attached:
        # Already floating or hidden
        if self.window.get_visible():
            return  # Already floating
    
    # Move from stack to window (ONE TIME operation)
    if self.content.get_parent() == self.stack_container:
        self.stack_container.remove(self.content)
        self.window.add(self.content)
    
    self.is_attached = False
    self.window.set_transient_for(parent_window)
    self.window.show_all()
    
    # Update float button
    if self.float_button:
        self.float_button.set_active(True)
    
    # Notify callback
    if self.on_float_callback:
        self.on_float_callback()
```

#### 3. `hide()` - Hide panel (keep in current parent)
```python
def hide(self):
    """Hide panel without reparenting.
    
    CRITICAL: Widget stays in its current parent (stack or window).
    Just hide the parent container!
    """
    if self.is_attached:
        # Panel is in stack - hide the stack
        # Main code handles this by calling stack.set_visible(False)
        pass
    else:
        # Panel is floating - hide the window
        if self.window.get_visible():
            self.window.hide()
```

### Phase 2: Fix Master Palette Integration (1 hour)

**Simplify toggle handlers in shypn.py:**

```python
def on_left_toggle(is_active):
    """Handle Files panel toggle."""
    if is_active:
        # Deactivate other buttons
        master_palette.set_active('pathways', False)
        master_palette.set_active('analyses', False)
        master_palette.set_active('topology', False)
        
        # Hide other panels
        right_panel_loader.hide()
        pathway_panel_loader.hide()
        topology_panel_loader.hide()
        
        # Show Files panel
        left_dock_stack.set_visible(True)
        left_dock_stack.set_visible_child_name('files')
        left_panel_loader.attach(parent_window=window)  # Just updates state
        
        # Adjust paned
        left_paned.set_position(250)
    else:
        # Hide Files panel
        left_dock_stack.set_visible(False)
        left_panel_loader.hide()
        left_paned.set_position(0)
```

### Phase 3: Remove All Complexity (1 hour)

**Delete these overcomplicated mechanisms:**

1. ❌ `_attach_in_progress` flag - Not needed with simple API
2. ❌ `_do_attach()` idle callbacks - Not needed, do it synchronously
3. ❌ `attach_to(container)` parameter - Container is always the stack
4. ❌ `unattach()` method - Use `float()` instead
5. ❌ Multiple `attach_to()` calls - One `attach()` is enough

**Keep only:**
- ✅ `load()` - Load UI and add to stack (happens ONCE at startup)
- ✅ `attach()` - Show in stack (moves from window if floating)
- ✅ `float()` - Show in window (moves from stack if attached)
- ✅ `hide()` - Hide current parent (NO widget removal)

---

## 🎯 THE GOLDEN RULES

### Rule 1: Widget Lifecycle
```
Panel Created
    ↓
Content added to Stack (BEFORE show_all)
    ↓
Window shown (widget realized with parent)
    ↓
User clicks buttons:
    - Attach: Content in Stack (show stack)
    - Float: Content in Window (show window)
    - Hide: Content stays in parent (hide parent)
```

### Rule 2: State Transitions (ONLY 2 moves allowed)
```
Stack → Window (float)
Window → Stack (attach)
```

**NEVER:**
```
Stack → Orphan → Window  ❌
Window → Orphan → Stack  ❌
Stack → Stack (re-add)   ❌
```

### Rule 3: Parent Always Set
```python
# Widget ALWAYS has a parent:
assert self.content.get_parent() is not None

# Widget parent is EITHER stack OR window:
assert self.content.get_parent() in [self.stack_container, self.window]
```

---

## 📝 IMPLEMENTATION CHECKLIST

### Left Panel Loader (`left_panel_loader.py`)
- [ ] Simplify `attach()` - no container parameter, just update state
- [ ] Simplify `float()` - move from stack to window in one operation
- [ ] Simplify `hide()` - NO widget removal, just hide parent
- [ ] Remove `_attach_in_progress` flag
- [ ] Remove `_do_attach()` method
- [ ] Remove `attach_to()` method (or make it call `attach()`)
- [ ] Remove `unattach()` method

### Right Panel Loader (`right_panel_loader.py`)
- [ ] Same changes as Left Panel

### Pathway Panel Loader (`pathway_panel_loader.py`)
- [ ] Same changes as Left/Right Panel

### Topology Panel Loader (`topology_panel_loader.py`)
- [ ] Same changes as Left/Right Panel

### Main Window Integration (`shypn.py`)
- [ ] Remove `attach_to(container, window)` calls
- [ ] Use simple `attach(parent_window)` calls
- [ ] Ensure stack visibility controlled by toggle handlers only
- [ ] Remove duplicate attach protection code
- [ ] Remove idle callback delays

---

## 🧪 TESTING STRATEGY

### Test 1: Startup (No Errors)
```bash
python3 src/shypn.py 2>&1 | grep -i error
# Expected: NO Error 71
```

### Test 2: Panel Switching
```
Click Files → Click Analyses → Click Pathways → Click Topology
# Expected: Smooth switching, no errors
```

### Test 3: Float/Attach Cycle
```
Click Files → Float → Attach → Float → Attach
# Expected: No errors, panel moves correctly
```

### Test 4: Rapid Clicking
```
Rapidly click: Files → Analyses → Files → Pathways → Files
# Expected: No crashes, clean state transitions
```

---

## 🎯 SUCCESS CRITERIA

✅ **Zero Wayland Error 71**  
✅ **Zero orphaned widgets**  
✅ **Zero crashes**  
✅ **Clean attach/float/hide operations**  
✅ **Simple, maintainable code (< 50 lines per method)**

---

## 🚀 NEXT STEPS

1. **Backup current state** (tar.gz)
2. **Implement Phase 1** - Simplify panel loaders
3. **Test each panel** individually
4. **Implement Phase 2** - Fix Master Palette handlers
5. **Implement Phase 3** - Remove complexity
6. **Full integration test**
7. **Commit clean solution**

---

**Key Insight:** The problem isn't the Master Palette. It's the panel loaders doing widget reparenting when they should just be updating state. Fix the loaders, fix the problem.
