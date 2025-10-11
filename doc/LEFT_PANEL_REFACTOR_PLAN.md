# Left Panel Crash Analysis & Refactor Plan

**Date**: 2025-10-10  
**Issue**: Every operation on left panel causes application crash on Wayland  
**Root Cause**: Parent window initialization sequence broken

---

## Problem Summary

### Symptoms
1. ✗ **Toolbar buttons crash** (New, Open, Save, Save As)
2. ✗ **Project buttons crash** (New Project, Open Project)
3. ✗ **Float/Attach crashes** after first operation
4. ✗ **Missing buttons** (Open Project, Project Settings, Quit appear/disappear)
5. ⚠️ **Wayland Error 71** (Protocol error) on most operations

### Architecture Issues Discovered

```
Current (BROKEN):
┌─────────────────────────────────────┐
│ shypn.py (Main Application)         │
│  - Creates left_panel_loader        │
│  - Creates persistency manager      │
│  - Calls attach_to(main_window)     │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ LeftPanelLoader.load()               │
│  - Loads UI from left_panel.ui      │
│  - Creates self.window (hidden)     │
│  - Creates FileExplorerPanel        │
│  - Creates ProjectActionsController │
│    ❌ parent_window = None           │  ← PROBLEM 1: No parent set
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ ProjectActionsController.__init__()  │
│  - parent_window = None             │  ← PROBLEM 2: Dialogs have no parent
│  - Creates ProjectDialogManager     │
│    with parent_window=None          │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ FileExplorerPanel.__init__()         │
│  - persistency = None               │  ← PROBLEM 3: Set later, may be None
│  - Buttons connected to methods     │     when buttons clicked
└─────────────────────────────────────┘
```

### Timeline of Parent Window Issues

1. **Initialization** (shypn.py line 164):
   ```python
   left_panel_loader = create_left_panel()  # No parent yet
   ```
   - Panel window created but hidden
   - ProjectActionsController created with `parent_window=None`
   - FileExplorerPanel created, no persistency

2. **Wiring** (shypn.py line 178):
   ```python
   file_explorer.set_persistency_manager(persistency)
   ```
   - Persistency wired to FileExplorer
   - But persistency's parent_window is main window
   - FileExplorer buttons already connected to methods

3. **Attachment** (shypn.py line 267):
   ```python
   left_panel_loader.attach_to(left_dock_area, parent_window=window)
   ```
   - Tries to set project_controller.parent_window = window
   - Tries to set persistency.parent_window = window
   - BUT widgets were initialized before this!

### Specific Crash Points

#### Crash 1: Toolbar Buttons (New, Open, Save, Save As)
```python
# file_explorer_panel.py line 184-190
self.new_button.connect('clicked', lambda btn: self.new_document())
self.open_button.connect('clicked', lambda btn: self.open_document())
```
- Buttons call methods that use `self.persistency`
- Persistency creates dialogs with parent window
- **Issue**: When panel floats, persistency parent may be stale

#### Crash 2: Project Buttons (New Project, Open Project, Settings)
```python
# project_actions_controller.py line 86-96
def _connect_buttons(self):
    self.new_project_button.connect('clicked', self._on_new_project_clicked)
    self.open_project_button.connect('clicked', self._on_open_project_clicked)
```
- Buttons call dialog_manager methods
- dialog_manager.parent_window set during __init__ (None!)
- **Issue**: Parent window never properly initialized

#### Crash 3: Float/Attach Operations
```python
# left_panel_loader.py line 227-230
if parent and self.project_controller:
    self.project_controller.set_parent_window(parent)
```
- Tries to update parent on each float/attach
- **Issue**: Tooltips (14 in UI!) create popups before window mapped
- Wayland requires strict parent-child hierarchy

---

## Root Cause Analysis

### The Core Problem: Initialization Order

The left panel has a **chicken-and-egg problem**:

1. Panel needs to be created before main window attachment
2. Project controller needs main window as parent for dialogs
3. Main window isn't available until AFTER panel is created
4. Solution tried: Set parent_window after creation
5. **Failure**: GTK widgets already connected, parent references frozen

### Why Right Panel Works

```python
# right_panel_loader.py - WORKS
def float(self, parent_window=None):
    if parent_window:
        self.window.set_transient_for(parent_window)
    self.window.show_all()  # Simple, no complex wiring
```

**Differences**:
- ✓ Right panel: Only 1 tooltip, simple UI
- ✓ Right panel: No persistent dialogs (analyses panels)
- ✗ Left panel: 14 tooltips, complex button wiring
- ✗ Left panel: Multiple dialog systems (persistency + projects)

---

## Solution Architecture

### Approach 1: Deferred Initialization (RECOMMENDED)

**Concept**: Delay sub-controller creation until parent window available

```python
class LeftPanelLoader:
    def __init__(self, ui_path=None, base_path=None):
        self.ui_path = ui_path
        self.base_path = base_path
        # DON'T load UI yet
        self.builder = None
        self.window = None
        self.project_controller = None
        self.file_explorer = None
    
    def load(self, parent_window=None):
        """Load UI with proper parent window reference."""
        # Load UI first
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        self.window = self.builder.get_object('left_panel_window')
        
        # NOW create sub-controllers with parent window
        if parent_window:
            self.project_controller = ProjectActionsController(
                self.builder, 
                parent_window=parent_window  # ← CORRECT PARENT
            )
        
        self.file_explorer = FileExplorerPanel(self.builder, ...)
        
        return self.window
```

**Pros**:
- ✓ Clean separation of concerns
- ✓ Parent window set correctly from start
- ✓ No need for post-init updates

**Cons**:
- ⚠️ Changes initialization API
- ⚠️ Requires updates in shypn.py

### Approach 2: Lazy Dialog Creation

**Concept**: Don't create dialogs until they're needed

```python
class ProjectDialogManager:
    def __init__(self, parent_window=None):
        self.parent_window = parent_window
        self._new_project_dialog = None  # Create on demand
    
    def show_new_project_dialog(self):
        # Get current parent (may have changed)
        parent = self.parent_window
        
        # Create dialog fresh each time
        dialog = self._build_new_project_dialog(parent)
        response = dialog.run()
        dialog.destroy()
```

**Pros**:
- ✓ Always uses current parent window
- ✓ Less memory usage (dialogs destroyed after use)
- ✓ Minimal API changes

**Cons**:
- ⚠️ Slight performance cost (rebuild each time)
- ⚠️ May not fix tooltip issue

### Approach 3: Hybrid (BEST)

Combine both approaches:

1. **Deferred initialization** for project controller
2. **Lazy dialogs** for persistency manager
3. **Tooltip fix**: Disable tooltips during float, re-enable after

```python
# Step 1: Modify left_panel_loader.py
class LeftPanelLoader:
    def attach_to(self, container, parent_window=None):
        # Load UI if not loaded
        if self.window is None:
            self.load()
        
        # NOW create project controller (first time only)
        if not self.project_controller and parent_window:
            self.project_controller = ProjectActionsController(
                self.builder, 
                parent_window=parent_window
            )
            self._connect_project_callbacks()
        
        # Update parent for sub-controllers
        if parent_window:
            self.parent_window = parent_window
            if self.project_controller:
                self.project_controller.set_parent_window(parent_window)
            if self.file_explorer and self.file_explorer.persistency:
                self.file_explorer.persistency.parent_window = parent_window
        
        # ... rest of attach logic
    
    def float(self, parent_window=None):
        # Temporarily disable tooltips during transition
        if self.window:
            self.window.set_has_tooltip(False)
        
        # ... float logic ...
        
        # Re-enable tooltips after window is mapped
        GLib.idle_add(self._restore_tooltips)
    
    def _restore_tooltips(self):
        if self.window:
            self.window.set_has_tooltip(True)
        return False
```

---

## Implementation Plan

### Phase 1: Fix Initialization Order (HIGH PRIORITY)

**Files to modify**:
1. `src/shypn/helpers/left_panel_loader.py`
2. `src/shypn.py` (minimal changes)

**Changes**:
```python
# left_panel_loader.py
def load(self):
    """Load UI but DON'T create sub-controllers yet."""
    self.builder = Gtk.Builder.new_from_file(self.ui_path)
    self.window = self.builder.get_object('left_panel_window')
    self.content = self.builder.get_object('left_panel_content')
    self.float_button = self.builder.get_object('float_button')
    
    # Create FileExplorerPanel (doesn't need parent for dialogs yet)
    self.file_explorer = FileExplorerPanel(self.builder, ...)
    
    # DON'T create ProjectActionsController here!
    self.project_controller = None
    
    return self.window

def attach_to(self, container, parent_window=None):
    """Attach panel and initialize sub-controllers with proper parent."""
    if self.window is None:
        self.load()
    
    # First-time initialization of project controller
    if self.project_controller is None and parent_window:
        self.project_controller = ProjectActionsController(
            self.builder,
            parent_window=parent_window  # ← CORRECT!
        )
        self._wire_project_callbacks()
    
    # Rest of attach logic...
```

### Phase 2: Fix Tooltip Crash (MEDIUM PRIORITY)

**Strategy**: Disable tooltips during window transitions

```python
def float(self, parent_window=None):
    # Disable tooltips temporarily
    self._disable_all_tooltips()
    
    # ... existing float logic ...
    
    # Re-enable after window is shown
    GLib.idle_add(self._enable_all_tooltips)

def _disable_all_tooltips(self):
    """Temporarily disable all tooltips in panel."""
    if self.content:
        for widget in self._walk_widgets(self.content):
            if widget.get_has_tooltip():
                widget.set_has_tooltip(False)
                # Store original state
                widget._tooltip_disabled = True

def _enable_all_tooltips(self):
    """Re-enable tooltips after window transition."""
    if self.content:
        for widget in self._walk_widgets(self.content):
            if hasattr(widget, '_tooltip_disabled'):
                widget.set_has_tooltip(True)
                del widget._tooltip_disabled
    return False  # Don't repeat

def _walk_widgets(self, container):
    """Recursively walk all widgets in container."""
    for child in container.get_children():
        yield child
        if isinstance(child, Gtk.Container):
            yield from self._walk_widgets(child)
```

### Phase 3: Fix Persistency Dialog Parents (LOW PRIORITY)

**Current issue**: Persistency manager's parent window may be stale

**Solution**: Make dialogs lazy (create on demand)

```python
# netobj_persistency.py
def save_document(self, document, save_as=False, is_default_filename=False):
    # Get CURRENT parent (may have changed since init)
    parent = self.parent_window if self.parent_window else None
    
    # Create dialog fresh with current parent
    if save_as or is_default_filename:
        dialog = Gtk.FileChooserDialog(
            title="Save Document",
            transient_for=parent,  # ← Always current
            action=Gtk.FileChooserAction.SAVE
        )
        # ... rest of dialog logic
```

---

## Testing Checklist

After implementing fixes:

### Test 1: Initialization
- [ ] Start application
- [ ] Left panel should be attached and visible
- [ ] All buttons should be present (New, Open, Save, Save As, New Project, Open Project, Project Settings, Quit)
- [ ] No Wayland errors in console

### Test 2: Toolbar Buttons (Attached State)
- [ ] Click "New" button → should work
- [ ] Click "Open" button → should show file dialog
- [ ] Click "Save" button → should save or show dialog
- [ ] Click "Save As" button → should show file dialog

### Test 3: Project Buttons (Attached State)
- [ ] Click "New Project" button → should show project dialog
- [ ] Click "Open Project" button → should show open dialog
- [ ] Click "Project Settings" button → should show settings dialog
- [ ] Click "Quit" button → should prompt to save

### Test 4: Float/Attach Cycle
- [ ] Click float button → panel detaches
- [ ] All buttons still visible
- [ ] Click attach button → panel reattaches
- [ ] Repeat 5 times → no crashes

### Test 5: Buttons While Floating
- [ ] Float the panel
- [ ] Click "New" button → should work
- [ ] Click "New Project" button → should work
- [ ] All dialogs should appear correctly positioned

### Test 6: Context Menu
- [ ] Right-click in file tree → context menu appears
- [ ] Select menu items → should work
- [ ] No Wayland errors

---

## Summary of Required Changes

| File | Change | Priority | Effort |
|------|--------|----------|--------|
| `left_panel_loader.py` | Defer project controller creation | HIGH | 1h |
| `left_panel_loader.py` | Add tooltip disable/enable | MEDIUM | 30m |
| `left_panel_loader.py` | Fix float/attach parent logic | HIGH | 30m |
| `project_actions_controller.py` | Verify parent window handling | LOW | 15m |
| `netobj_persistency.py` | Make dialogs lazy (optional) | LOW | 1h |
| `shypn.py` | Update initialization sequence | MEDIUM | 30m |

**Total estimated effort**: 3-4 hours

---

## Next Steps

1. **Implement Phase 1** (initialization fix) - this should fix most crashes
2. **Test thoroughly** with checklist above
3. **If still crashing**: Implement Phase 2 (tooltip fix)
4. **If dialogs still buggy**: Implement Phase 3 (lazy dialogs)

---

## Expected Outcome

After implementing these fixes:
- ✓ No crashes on button clicks
- ✓ No crashes on float/attach
- ✓ All buttons visible and working
- ✓ Clean Wayland operation (no Error 71)
- ✓ Dialogs properly parented to main window
