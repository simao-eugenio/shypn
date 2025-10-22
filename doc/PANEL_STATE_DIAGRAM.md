# Panel State Diagram - The Simple Truth

## 🎯 Current Problem (What's Happening)

```
STARTUP:
┌──────────────────┐
│  Panel Window    │
│  ┌────────────┐  │
│  │  Content   │  │ ← Panel starts here
│  └────────────┘  │
└──────────────────┘
        ↓
   load() moves content
        ↓
┌──────────────────┐
│   Main Window    │
│  ┌────────────┐  │
│  │ GtkStack   │  │
│  │ ┌────────┐ │  │
│  │ │Content │ │  │ ← Content moved BEFORE show_all() ✅
│  │ └────────┘ │  │
│  └────────────┘  │
└──────────────────┘
        ↓
  window.show_all() ✅
        ↓
USER CLICKS BUTTON:
        ↓
┌──────────────────────────────────────┐
│  attach_to() tries to add content    │ ← ERROR! Widget already has parent
│  container.add(self.content)         │ ← Wayland sees reparenting
│  ❌ Error 71 - Protocol Error        │
└──────────────────────────────────────┘
```

---

## ✅ The Fix (What Should Happen)

```
STARTUP:
┌──────────────────┐
│  Panel Window    │
│  ┌────────────┐  │
│  │  Content   │  │
│  └────────────┘  │
└──────────────────┘
        ↓
   load() - ONE TIME MOVE
        ↓
┌──────────────────┐
│   Main Window    │
│  ┌────────────┐  │
│  │ GtkStack   │  │
│  │ ┌────────┐ │  │
│  │ │Content │ │  │ ← Content lives here permanently
│  │ └────────┘ │  │    (unless user clicks Float)
│  └────────────┘  │
└──────────────────┘
        ↓
  window.show_all()
        ↓
RUNTIME - Panel never leaves stack unless floating:

SHOW FILES:
    left_dock_stack.set_visible_child_name('files')
    left_dock_stack.set_visible(True)
    ✅ NO widget movement

SHOW ANALYSES:
    left_dock_stack.set_visible_child_name('analyses')
    left_dock_stack.set_visible(True)
    ✅ NO widget movement

HIDE PANEL:
    left_dock_stack.set_visible(False)
    ✅ NO widget movement
```

---

## 🔄 State Transitions (The ONLY Two Moves)

### Move 1: Stack → Window (Float)
```
┌──────────────────┐         ┌──────────────────┐
│   Main Window    │         │  Panel Window    │
│  ┌────────────┐  │         │  ┌────────────┐  │
│  │ GtkStack   │  │  Float  │  │  Content   │  │
│  │ ┌────────┐ │  │ ──────→ │  └────────────┘  │
│  │ │Content │ │  │  button │                  │
│  │ └────────┘ │  │         │                  │
│  └────────────┘  │         └──────────────────┘
└──────────────────┘

Code:
    stack.remove(content)     # Remove from stack
    window.add(content)       # Add to window
    window.show_all()         # Show window
```

### Move 2: Window → Stack (Attach)
```
┌──────────────────┐         ┌──────────────────┐
│  Panel Window    │         │   Main Window    │
│  ┌────────────┐  │ Attach  │  ┌────────────┐  │
│  │  Content   │  │ ──────→ │  │ GtkStack   │  │
│  └────────────┘  │  button │  │ ┌────────┐ │  │
│                  │         │  │ │Content │ │  │
└──────────────────┘         │  │ └────────┘ │  │
                              │  └────────────┘  │
                              └──────────────────┘

Code:
    window.hide()             # Hide window
    window.remove(content)    # Remove from window
    stack.add(content)        # Add to stack
    stack.set_visible(True)   # Show stack
```

---

## ❌ What NOT To Do (Common Mistakes)

### Mistake 1: Re-adding to Same Parent
```
┌──────────────────┐
│  │ GtkStack   │  │
│  │ ┌────────┐ │  │
│  │ │Content │ │  │ ← Already in stack
│  │ └────────┘ │  │
│  └────────────┘  │
└──────────────────┘
        ↓
    stack.add(content)  ❌ ERROR!
    # Widget already has parent!
```

### Mistake 2: Removing Without Adding
```
┌──────────────────┐
│  │ GtkStack   │  │
│  │ ┌────────┐ │  │
│  │ │Content │ │  │
│  │ └────────┘ │  │
│  └────────────┘  │
└──────────────────┘
        ↓
    stack.remove(content)
        ↓
┌────────┐
│Content │ ← ORPHANED! No parent!
└────────┘  ❌ Can't be shown again
```

### Mistake 3: Multiple Reparenting Cycles
```
Window → Stack → Window → Stack → Window
  ↓        ↓        ↓        ↓        ↓
Error    Error    Error    Error    Error
  71       71       71       71       71
```

---

## ✅ The Golden Rules (Print This Out!)

### Rule 1: ONE HOME AT A TIME
```
Content lives in EXACTLY ONE place:
    - GtkStack (when attached) OR
    - Panel Window (when floating)

NEVER:
    - No parent (orphaned)
    - Multiple parents
    - Temporary storage
```

### Rule 2: ATOMIC MOVES ONLY
```
When moving content between parents:
    1. Remove from old parent
    2. IMMEDIATELY add to new parent
    3. Update visibility

NEVER:
    - Remove without adding
    - Add without removing
    - Delay between remove and add
```

### Rule 3: CHECK PARENT BEFORE OPERATIONS
```python
# Before attach:
if content.get_parent() == stack:
    # Already attached - just update visibility
    stack.set_visible_child_name('files')
    return  # Don't re-add!

# Before float:
if content.get_parent() == window:
    # Already floating - just show window
    window.show_all()
    return  # Don't re-add!
```

---

## 🎯 Panel Loader State Machine

```
┌─────────────────────────────────────────────────┐
│                   PANEL STATE                    │
└─────────────────────────────────────────────────┘
                        │
                        ↓
              ┌─────────────────┐
              │   INITIALIZED   │
              │  (no parent)    │
              └─────────────────┘
                        │
                   load() called
                        │
                        ↓
              ┌─────────────────┐
              │    IN STACK     │ ← DEFAULT STATE
              │  (is_attached)  │    Panel starts here
              └─────────────────┘
                   ↗         ↘
            attach()       float()
                 ↗             ↘
                ↗               ↘
        ┌─────────────┐   ┌─────────────┐
        │  IN STACK   │   │  IN WINDOW  │
        │  (visible)  │   │  (floating) │
        └─────────────┘   └─────────────┘
                ↖             ↙
            hide()       hide()
                 ↖           ↙
                   ↖       ↙
              ┌─────────────────┐
              │    HIDDEN       │
              │ (stays in parent│
              │  just invisible)│
              └─────────────────┘
```

---

## 🔍 Debug Checklist (When Something Breaks)

### Check 1: Parent Sanity
```python
print(f"Content parent: {self.content.get_parent()}")
# Should be EITHER:
#   - self.stack_container (if attached)
#   - self.window (if floating)
# Should NEVER be:
#   - None (orphaned)
#   - Something else
```

### Check 2: State Consistency
```python
if self.is_attached:
    assert self.content.get_parent() == self.stack_container
else:
    assert self.content.get_parent() == self.window
```

### Check 3: No Duplicate Operations
```python
# Before add():
if widget.get_parent() == target_parent:
    print("WARNING: Widget already in target parent!")
    return  # Don't re-add!
```

---

## 📊 Expected Call Sequence (Startup)

```
main()
  ├─> create_left_panel()
  │     └─> loader.load()
  │           ├─> Load UI from XML
  │           ├─> content = builder.get('left_panel_content')
  │           ├─> window.remove(content)
  │           ├─> stack_container.add(content)  ✅ BEFORE show_all
  │           └─> return loader
  │
  ├─> create_right_panel()
  │     └─> (same as left panel)
  │
  ├─> create_pathway_panel()
  │     └─> (same as left panel)
  │
  ├─> create_topology_panel()
  │     └─> (same as left panel)
  │
  ├─> window.show_all()  ✅ All widgets in place
  │
  └─> GLib.timeout_add(1000, activate_files_panel)
        └─> master_palette.set_active('files', True)
              └─> on_left_toggle(True)
                    ├─> stack.set_visible(True)
                    ├─> stack.set_visible_child_name('files')
                    └─> left_panel_loader.attach()
                          └─> self.is_attached = True  ✅ NO reparenting!
```

---

## 🎯 Summary (TL;DR)

**Problem:**
- Panels reparenting widgets after `window.show_all()` → Wayland Error 71

**Solution:**
- Content moves to stack ONCE at startup (before show_all)
- Runtime: Just toggle visibility, NO widget movement
- Float/Attach: Only TWO moves allowed (stack↔window)

**Fix:**
- Simplify `attach()` - update state, NO reparenting
- Simplify `float()` - move from stack to window atomically
- Simplify `hide()` - hide parent, NO widget removal

**Result:**
- ✅ Zero Wayland errors
- ✅ Zero orphaned widgets
- ✅ Zero crashes
- ✅ Simple, maintainable code
