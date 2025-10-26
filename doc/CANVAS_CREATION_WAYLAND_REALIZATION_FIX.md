# Canvas Creation Wayland Realization Fix

## Problem Summary

Property dialogs crash with Wayland errors on:
- ✗ File→New canvases
- ✗ Imported canvases (KEGG/SBML)
- ✓ Default startup canvas (works)
- ✓ File→Open loaded canvases (works)

The pattern revealed the root cause: **widget realization**.

## Root Cause Analysis

### Three Canvas Creation Paths

#### 1. Default Startup Canvas (WORKS)
```python
# In load() method:
self.builder = Gtk.Builder.new_from_file(self.ui_path)
self.container = self.builder.get_object('model_canvas_container')
self.notebook = self.builder.get_object('canvas_notebook')
# ... setup first canvas from UI file
```

**Why it works:**
- Widgets defined in UI file
- Loaded by Gtk.Builder
- Added to main window container
- **Automatically realized when main window.show_all() is called**
- By the time user clicks objects, widgets are fully realized

#### 2. File→New Canvas (FAILS)
```python
# In add_document() method:
overlay = Gtk.Overlay()
scrolled = Gtk.ScrolledWindow()
drawing = Gtk.DrawingArea()
# ... build widget tree programmatically
overlay.show_all()  # Makes widgets visible
self._setup_canvas_manager(drawing, ...)  # Enables dialogs
```

**Why it fails:**
- Widgets created programmatically
- `show_all()` makes them visible but doesn't realize them
- **Not realized yet** (no GdkWindow/GdkSurface on Wayland)
- When property dialog tries to use parent, Wayland rejects unrealized window

#### 3. Import Canvas (FAILS - same as File→New)
```python
# Import handlers call:
self.canvas_loader.add_document(filename=pathway_id)
# ... then load objects into the canvas
```

**Same failure mode as File→New** because both use `add_document()`.

### Widget Realization vs. Visibility

**show() / show_all():**
- Makes widget visible on screen
- Queues drawing operations
- Does NOT create native window resources

**realize():**
- Creates GdkWindow (X11) or GdkSurface (Wayland)
- Allocates native display protocol resources
- **Required for Wayland parent-child dialog relationships**

### Wayland Strict Requirements

On Wayland, when you call:
```python
dialog.set_transient_for(parent_window)
```

The parent_window **MUST**:
1. Be visible (`show_all()` called)
2. Be realized (`.realize()` called or auto-realized)
3. Have a valid GdkSurface for protocol negotiation

If parent is not realized, Wayland protocol fails:
- Error 71: Protocol error
- Broken pipe
- Dialog crash

## The Fix

### Code Change

**File:** `src/shypn/helpers/model_canvas_loader.py`
**Method:** `add_document()`
**Location:** After `overlay.show_all()`, before `_setup_canvas_manager()`

```python
overlay.show_all()

# WAYLAND FIX: Realize the widget before setup to ensure proper parent window hierarchy
# On Wayland, dialogs require their parent to be realized (have a GdkWindow/GdkSurface)
# Default canvas works because it's loaded from UI file and realized when main window shows
# File→New/Import canvases are created programmatically and need explicit realization
if not overlay.get_realized():
    overlay.realize()
    print(f"[CANVAS] Realized overlay for page_index={page_index}", file=sys.stderr)

self._setup_canvas_manager(drawing, overlay_box, overlay, filename=filename)
```

### Why This Works

**Sequence for File→New/Import:**
1. Create widgets programmatically
2. `overlay.show_all()` - makes visible
3. **`overlay.realize()` - creates Wayland surface** ← NEW STEP
4. `_setup_canvas_manager()` - enables property dialogs
5. User clicks object → property dialog created
6. Dialog calls `set_transient_for(parent_window)`
7. Parent window is realized → Wayland accepts protocol
8. Dialog shows successfully ✓

**Sequence for Default Canvas:**
1. Load widgets from UI file
2. Add to main window
3. `main_window.show_all()` - shows everything
4. **Widgets auto-realized as part of window showing**
5. `_setup_canvas_manager()` - enables property dialogs
6. Dialog creation works because parent already realized ✓

## Testing Verification

### Before Fix
- Default canvas property dialogs: ✓ Work
- File→New property dialogs: ✗ Wayland Error 71 / Broken pipe
- Import property dialogs: ✗ Wayland Error 71 / Broken pipe

### After Fix
- Default canvas property dialogs: ✓ Work (unchanged)
- File→New property dialogs: ✓ Work (FIXED)
- Import property dialogs: ✓ Work (FIXED)

## Why Previous Fixes Weren't Enough

### Previous Attempts
1. ✓ Canvas state initialization (mark_clean, set_filepath)
2. ✓ Defensive parent validation (if parent_window else None)
3. ✓ Parent propagation to topology tab
4. ✓ Dialog realize() before run()
5. ✓ Method call fixes (get_pathways_dir())

**All were necessary but not sufficient.**

The core issue was that the parent window itself (the canvas container/overlay) wasn't realized on Wayland when dialogs tried to attach to it.

### Layer Analysis

```
Layer 1: Canvas State ✓ - Fixed initialization
Layer 2: Parent Validation ✓ - Defensive checks added
Layer 3: Dialog Lifecycle ✓ - realize() before run()
Layer 4: Parent Propagation ✓ - Topology tab fixed
Layer 5: Widget Realization ← THIS FIX
```

Each layer was necessary, but Layer 5 (widget realization) was the final missing piece for Wayland compatibility.

## Technical Details

### GTK Widget Lifecycle

```
Created → Shown → Realized → Mapped → Visible
   ↓         ↓        ↓         ↓        ↓
  new()  show_all() realize()  map()   visible
```

**For dialogs on Wayland:**
- Parent must be at least **Realized** stage
- Visibility alone is not enough
- Native window resources must exist

### GdkWindow vs GdkSurface

- **X11:** Uses GdkWindow for all windows
- **Wayland:** Uses GdkSurface (protocol-specific)
- Both created by `realize()` call
- Required for `set_transient_for()` protocol negotiation

## Related Files

- `src/shypn/helpers/model_canvas_loader.py` - Main fix location
- `src/shypn/helpers/kegg_import_panel.py` - Import canvas creation
- `src/shypn/helpers/sbml_import_panel.py` - Import canvas creation
- `doc/CANVAS_STATE_ANALYSIS_IMPORTED_VS_LOADED.md` - State analysis
- `doc/GTK_PARENT_WINDOW_AUDIT.md` - Parent window patterns

## Commit Message

```
Fix Wayland Error 71: realize() canvas before enabling dialogs

Root cause: File→New and imported canvases are created programmatically
and need explicit realize() call before dialogs can attach. Default canvas
works because it's loaded from UI file and auto-realized when main window
shows.

The fix calls overlay.realize() in add_document() after show_all() but
before _setup_canvas_manager(). This ensures the canvas has a Wayland
surface when property dialogs try to use it as parent.

Fixes crash pattern:
✓ Default canvas dialogs work (auto-realized)
✗ File→New dialogs crash (not realized) → NOW FIXED
✗ Import dialogs crash (not realized) → NOW FIXED
```

## Lessons Learned

1. **Wayland is stricter than X11** about widget realization
2. **Programmatic widget creation** requires explicit realize()
3. **UI file widgets** are auto-realized when parent shows
4. **show_all() ≠ realize()** - visibility ≠ native window allocation
5. **Multi-layer debugging** required checking state, parents, lifecycle, AND realization
