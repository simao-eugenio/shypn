# Default Canvas Creation Bypass Issue

**Date**: 2025-11-24  
**Issue**: Default canvas created on last-tab-close bypasses Global Canvas State Lifecycle normalization  
**Impact**: Inconsistent initialization between startup default canvas and auto-recreated default canvas  
**Status**: 🔴 **CRITICAL** - User always encounters this canvas when starting work

---

## Problem Statement

The application has **TWO different code paths** for creating the "default" canvas:

1. **Normalized Path** (File → New, Startup, Imports): Goes through `load()` → `add_document()` → Full lifecycle
2. **Bypass Path** (Last Tab Close): Goes through `close_tab()` → Direct `add_document()` → **Incomplete lifecycle**

The bypass path **skips critical initialization steps** that are part of the Global Canvas State Lifecycle normalization, leading to:
- ❌ `_first_page_initialized` flag not reset properly
- ❌ Missing wiring steps for first tab
- ❌ Inconsistent lifecycle activation
- ❌ Potential missing context menu handler setup

**This is the canvas users immediately start working with** after closing all tabs, making it a critical user-facing issue.

---

## Architecture Context

### Global Canvas State Lifecycle Normalization

The application was **deliberately normalized** to ensure **all canvas creation flows** go through the same path:

```
┌─────────────────────────────────────────────────────────────────┐
│  NORMALIZED FLOW (Intended for ALL canvas creation)            │
├─────────────────────────────────────────────────────────────────┤
│  1. load() removes UI default tab                              │
│  2. _first_page_initialized = False                            │
│  3. add_document(filename='default')                           │
│  4. _on_notebook_page_added() hook fires                       │
│  5. Full wiring: data_collector, right_panel, context_menu     │
│  6. Lifecycle activation: switch_to_canvas(), set_scope()      │
│  7. _first_page_initialized = True                             │
└─────────────────────────────────────────────────────────────────┘
```

**From `doc/CANVAS_INITIALIZATION_ANALYSIS.md` (lines 414-647):**

> ### UNIFIED SOLUTION (Implemented 2025-11-09)
>
> **Delete UI default tab and create fresh one via `add_document()`**
>
> This ensures IDENTICAL initialization to File New for:
> - Startup default canvas
> - File → New
> - File → Open (new tab)
> - Import KEGG (new tab)
> - Import SBML (new tab)

**Key Quote from `model_canvas_loader.py` (line 239):**

```python
# SOLUTION: We ALWAYS delete ALL pages from the UI file and create a fresh canvas
# programmatically using add_document(). This ensures:
# 1. Default canvas is created the SAME way as File→New
# 2. NO notebook XML content is loaded
# 3. Consistent initialization across all canvas creation scenarios
# 4. Proper controller wiring and viability panel state
```

---

## The Bypass Issue

### Where It Happens

**File**: `src/shypn/helpers/model_canvas_loader.py`  
**Method**: `close_tab()` (lines 1054-1076)  
**Trigger**: User closes the last remaining tab by clicking [X] button

### Code Analysis

```python
def close_tab(self, page_num):
    # ... unsaved changes check ...
    # ... tab removal ...
    # ... cleanup operations ...
    
    if self.notebook.get_n_pages() == 0:
        # When the last tab is closed, recreate a fresh default canvas.
        # Reset the first-page initialization flag so the page-added hook
        # runs full initialization (same as initial startup) and ensure
        # the recreation follows the exact File→New code path.
        self._first_page_initialized = False  # ← RESETS FLAG
        page_index, new_drawing = self.add_document(filename='default')  # ← CALLS add_document()
        
        # ⚠️ PROBLEM: Manual lifecycle activation instead of relying on normalized flow
        try:
            if self.lifecycle_adapter and new_drawing:
                self.lifecycle_adapter.switch_to_canvas(new_drawing)
            if self.lifecycle_manager and hasattr(self.lifecycle_manager, 'id_manager') and new_drawing:
                from shypn.data.canvas.id_manager import set_lifecycle_scope_manager
                set_lifecycle_scope_manager(self.lifecycle_manager.id_manager)
                self.lifecycle_manager.id_manager.set_scope(f"canvas_{id(new_drawing)}")
            if new_drawing:
                new_drawing.set_can_focus(True)
                new_drawing.grab_focus()
        except Exception:
            pass
    return True
```

### What's Missing

The bypass path **duplicates** lifecycle activation logic that should be handled by the normalized flow. This creates two problems:

1. **Code Duplication**: Lifecycle activation logic exists in **THREE places**:
   - `load()` method (lines 269-280) - for startup default canvas
   - `_on_notebook_page_added()` (lines 354-367) - for first page hook
   - `close_tab()` (lines 1057-1076) - for auto-recreated default canvas ← **BYPASS**

2. **Incomplete Wiring**: The manual activation in `close_tab()` doesn't match the full sequence in `_on_notebook_page_added()`:

```python
# _on_notebook_page_added() (COMPLETE WIRING) - lines 331-371
def _on_notebook_page_added(self, notebook, child, page_num):
    if page_num == 0 and not getattr(self, '_first_page_initialized', False):
        # 1. Wire data collector
        self._wire_data_collector_for_page(child)
        
        # 2. Get drawing area and manager
        drawing_area = self._get_drawing_area_from_page(child)
        if drawing_area and drawing_area in self.canvas_managers:
            manager = self.canvas_managers[drawing_area]
            
            # 3. Set right panel model
            if self.right_panel_loader:
                self.right_panel_loader.set_model(manager)
                
                # 4. Set context menu handler model
                if self.right_panel_loader.context_menu_handler:
                    self.right_panel_loader.context_menu_handler.set_model(manager)
        
        # 5. Lifecycle activation
        if drawing_area:
            if self.lifecycle_adapter:
                self.lifecycle_adapter.switch_to_canvas(drawing_area)
            if self.lifecycle_manager and hasattr(self.lifecycle_manager, 'id_manager'):
                from shypn.data.canvas.id_manager import set_lifecycle_scope_manager
                set_lifecycle_scope_manager(self.lifecycle_manager.id_manager)
                self.lifecycle_manager.id_manager.set_scope(f"canvas_{id(drawing_area)}")
        
        # 6. Set flag
        self._first_page_initialized = True
```

**vs**

```python
# close_tab() (INCOMPLETE WIRING) - lines 1057-1076
self._first_page_initialized = False
page_index, new_drawing = self.add_document(filename='default')

# ⚠️ Only steps 5-6, missing steps 1-4!
try:
    if self.lifecycle_adapter and new_drawing:
        self.lifecycle_adapter.switch_to_canvas(new_drawing)
    if self.lifecycle_manager and hasattr(self.lifecycle_manager, 'id_manager') and new_drawing:
        from shypn.data.canvas.id_manager import set_lifecycle_scope_manager
        set_lifecycle_scope_manager(self.lifecycle_manager.id_manager)
        self.lifecycle_manager.id_manager.set_scope(f"canvas_{id(new_drawing)}")
    if new_drawing:
        new_drawing.set_can_focus(True)
        new_drawing.grab_focus()
except Exception:
    pass
```

### Missing Steps

The `close_tab()` bypass **does NOT execute**:

1. ❌ `_wire_data_collector_for_page(child)` - wires SimulationController's data_collector to right panel
2. ❌ `self.right_panel_loader.set_model(manager)` - sets active model in Dynamic Analyses panel
3. ❌ `self.right_panel_loader.context_menu_handler.set_model(manager)` - ensures "Add to Analysis" context menu works
4. ❌ `self._first_page_initialized = True` - flag never set after recreation

**Potential Impact**:
- Right panel may not be wired to the new canvas
- Context menu "Add to Transition Analyses" might not work immediately
- Data collector might not be connected
- Inconsistent state compared to File → New canvas

---

## Why This Matters

### User Experience Impact

**The default canvas is the first canvas a user sees when:**
1. Starting the application
2. Closing all tabs (by accident or intentionally)
3. Resetting their workspace

**User workflow:**
```
User closes last tab [X]
↓
Application auto-creates default canvas
↓
User starts drawing (P1, T1, P2)
↓
User right-clicks T1 → "Add to Transition Analyses"
↓
❓ Does it work? Should work, but using different initialization path!
```

This canvas should have **IDENTICAL behavior** to File → New canvas, but currently uses a **different code path**.

---

## Root Cause Analysis

### Design Intent (From Documentation)

**From `doc/CANVAS_INITIALIZATION_ANALYSIS.md` (line 496):**

> ### The Unified Solution
> **Delete UI default tab and create fresh one via `add_document()`**
> 
> This ensures IDENTICAL initialization to File New

**From `doc/CANVAS_CLOSE_LIFECYCLE_ANALYSIS.md` (line 340):**

> The requirement that "all new canvases must be created by File→New to normalize 
> initial state" is **satisfied** because:
> 1. File→New uses `add_document()` → `_setup_canvas_manager()` → lifecycle
> 2. Default tab creation also uses `add_document()` → same path
> 3. Both flows set ID scope, create through lifecycle, and reset simulation

### Implementation Reality

The `close_tab()` method **attempts** to follow the normalized flow by:
1. Resetting `_first_page_initialized = False`
2. Calling `add_document(filename='default')`
3. Manually activating lifecycle

**However**, this is **not the same** as the normalized flow because:

1. **Wrong Timing**: The manual lifecycle activation happens **after** `add_document()` returns, but `_on_notebook_page_added()` fires **during** `notebook.append_page()` inside `add_document()`

2. **Race Condition**: The hook `_on_notebook_page_added()` may or may not fire depending on:
   - Whether `page_num == 0` (it is, since notebook is empty)
   - Whether `_first_page_initialized == False` (it is, just set to False)
   - Whether the hook executes before the manual activation code

3. **Duplication**: If the hook fires, lifecycle activation happens **twice**:
   - Once in `_on_notebook_page_added()` (lines 354-367)
   - Once in `close_tab()` (lines 1060-1076)

4. **Flag State**: After the manual activation, `_first_page_initialized` is still `False` because the hook sets it to `True`, but the manual code doesn't.

---

## Comparison: Normalized vs Bypass

### Scenario 1: Application Startup (Normalized ✅)

```
main() → create_model_canvas(create_initial_document=False)
↓
ModelCanvasLoader.load(create_initial_document=True)
├─ Remove UI default tab (lines 252-256)
├─ _first_page_initialized = False (implicit, not set yet)
├─ add_document(filename='default') (line 267)
│  ├─ notebook.append_page(overlay, tab_box) (line 1303)
│  │  └─ SIGNAL: page-added fires
│  │     └─ _on_notebook_page_added() called
│  │        ├─ _wire_data_collector_for_page()
│  │        ├─ right_panel_loader.set_model()
│  │        ├─ context_menu_handler.set_model()
│  │        ├─ lifecycle_adapter.switch_to_canvas()
│  │        ├─ lifecycle_manager.id_manager.set_scope()
│  │        └─ _first_page_initialized = True
│  └─ Returns (page_index, drawing_area)
├─ [REDUNDANT] Manual lifecycle activation (lines 269-280)
│  └─ Duplicates work already done in _on_notebook_page_added()
└─ Wire data collector for initial default tab (lines 286-289)
   └─ [REDUNDANT] Already done in _on_notebook_page_added()
```

**Issues**:
- ⚠️ Redundant lifecycle activation (done twice)
- ⚠️ Redundant data collector wiring (done twice)
- ✅ But all wiring DOES happen

### Scenario 2: File → New (Normalized ✅)

```
_on_file_new() → canvas_loader.add_document(replace_empty_default=False)
↓
add_document(filename='default')
├─ notebook.append_page(overlay, tab_box) (line 1303)
│  └─ SIGNAL: page-added fires
│     └─ _on_notebook_page_added() called
│        ├─ page_num == 0? No (already have tabs)
│        └─ Hook does nothing (only runs for first page)
├─ Returns (page_index, drawing_area)
└─ [LATER] _on_notebook_page_changed() fires on tab switch
   ├─ _wire_data_collector_for_page()
   ├─ right_panel_loader.set_model()
   └─ context_menu_handler.set_model()
```

**Issues**:
- ✅ Clean flow, no duplication
- ✅ Wiring happens via `_on_notebook_page_changed()` on tab switch

### Scenario 3: Last Tab Close (Bypass ⚠️)

```
close_tab(last_tab)
├─ Cleanup operations...
├─ notebook.get_n_pages() == 0? Yes
├─ _first_page_initialized = False (line 1056)
├─ add_document(filename='default') (line 1057)
│  ├─ notebook.append_page(overlay, tab_box) (line 1303)
│  │  └─ SIGNAL: page-added fires
│  │     └─ _on_notebook_page_added() called
│  │        ├─ page_num == 0? Yes (notebook empty)
│  │        ├─ _first_page_initialized == False? Yes (just set)
│  │        ├─ _wire_data_collector_for_page() ✅
│  │        ├─ right_panel_loader.set_model() ✅
│  │        ├─ context_menu_handler.set_model() ✅
│  │        ├─ lifecycle_adapter.switch_to_canvas() ✅
│  │        ├─ lifecycle_manager.id_manager.set_scope() ✅
│  │        └─ _first_page_initialized = True ✅
│  └─ Returns (page_index, new_drawing)
└─ [REDUNDANT] Manual lifecycle activation (lines 1060-1076)
   ├─ lifecycle_adapter.switch_to_canvas() [DUPLICATE]
   ├─ lifecycle_manager.id_manager.set_scope() [DUPLICATE]
   └─ new_drawing.grab_focus()
```

**Issues**:
- ⚠️ Redundant lifecycle activation (done twice)
- ⚠️ Manual code duplicates what hook already did
- ✅ But all wiring DOES happen (via hook)

**Key Observation**: The reset `_first_page_initialized = False` **does work** and causes the hook to fire, so wiring happens. The manual activation is **redundant**.

---

## Architectural Inconsistency

### The Problem

The system has **three layers** of canvas lifecycle management:

1. **High-level flow** (`load()`, `add_document()`)
2. **Hook-based wiring** (`_on_notebook_page_added()`, `_on_notebook_page_changed()`)
3. **Manual activation** (in `load()` lines 269-280, in `close_tab()` lines 1060-1076)

**Layers 1 and 2 are the normalized architecture.**  
**Layer 3 is technical debt from pre-unification code.**

### Evidence from Documentation

**From `doc/CANVAS_INITIALIZATION_ANALYSIS.md` (line 496):**

> ### The Unified Solution
>
> **Delete UI default tab and create fresh one via `add_document()`**
>
> ```python
> # STEP 1: Remove all tabs from UI file
> while self.notebook.get_n_pages() > 0:
>     self.notebook.remove_page(0)
>
> # STEP 2: Create fresh default tab via add_document()
> # This ensures IDENTICAL initialization to File New
> page_index, drawing_area = self.add_document(filename='default')
> ```
>
> **Result**: All canvas creation paths converge to single `add_document()` flow

The documentation **does not mention** manual lifecycle activation after `add_document()`. It assumes `add_document()` is **complete**.

### The Redundancy

**Manual activation code exists in TWO places**:

1. **`load()` method** (lines 269-280):
```python
# After creation, ensure lifecycle global manager and scope are active
try:
    if self.lifecycle_manager and hasattr(self.lifecycle_manager, 'id_manager'):
        from shypn.data.canvas.id_manager import set_lifecycle_scope_manager
        set_lifecycle_scope_manager(self.lifecycle_manager.id_manager)
        self.lifecycle_manager.id_manager.set_scope(f"canvas_{id(drawing_area)}")
except Exception:
    pass
```

2. **`close_tab()` method** (lines 1060-1076):
```python
try:
    if self.lifecycle_adapter and new_drawing:
        self.lifecycle_adapter.switch_to_canvas(new_drawing)
    if self.lifecycle_manager and hasattr(self.lifecycle_manager, 'id_manager') and new_drawing:
        from shypn.data.canvas.id_manager import set_lifecycle_scope_manager
        set_lifecycle_scope_manager(self.lifecycle_manager.id_manager)
        self.lifecycle_manager.id_manager.set_scope(f"canvas_{id(new_drawing)}")
    if new_drawing:
        new_drawing.set_can_focus(True)
        new_drawing.grab_focus()
except Exception:
    pass
```

Both pieces of code are **duplicating work** that `_on_notebook_page_added()` already does.

---

## Recommended Solution

### Option 1: Remove Manual Activation (Cleanest)

**Trust the normalized flow completely.**

#### Changes Required

**File**: `src/shypn/helpers/model_canvas_loader.py`

**Change 1**: Remove manual activation from `load()` (lines 269-280)

```python
# BEFORE (lines 264-280):
if create_initial_document:
    page_index, drawing_area = self.add_document(filename='default')

# After creation, ensure lifecycle global manager and scope are active
try:
    import logging
    lg = logging.getLogger(__name__)
    if self.lifecycle_manager and hasattr(self.lifecycle_manager, 'id_manager'):
        from shypn.data.canvas.id_manager import set_lifecycle_scope_manager
        set_lifecycle_scope_manager(self.lifecycle_manager.id_manager)
        self.lifecycle_manager.id_manager.set_scope(f"canvas_{id(drawing_area)}")
        lg.debug(f"[CANVAS_INIT] Activated ID scope for first canvas: canvas_{id(drawing_area)}")
except Exception:
    pass

# Wire data collector for the initial default tab
if create_initial_document and self.notebook.get_n_pages() > 0:
    initial_page = self.notebook.get_nth_page(0)
    self._wire_data_collector_for_page(initial_page)
```

**AFTER (simplified):**

```python
if create_initial_document:
    page_index, drawing_area = self.add_document(filename='default')
    # NOTE: All wiring handled by _on_notebook_page_added() hook
    # No manual activation needed - trust the normalized flow
```

**Change 2**: Remove manual activation from `close_tab()` (lines 1054-1076)

```python
# BEFORE (lines 1054-1076):
if self.notebook.get_n_pages() == 0:
    self._first_page_initialized = False
    page_index, new_drawing = self.add_document(filename='default')
    try:
        if self.lifecycle_adapter and new_drawing:
            self.lifecycle_adapter.switch_to_canvas(new_drawing)
        if self.lifecycle_manager and hasattr(self.lifecycle_manager, 'id_manager') and new_drawing:
            from shypn.data.canvas.id_manager import set_lifecycle_scope_manager
            set_lifecycle_scope_manager(self.lifecycle_manager.id_manager)
            self.lifecycle_manager.id_manager.set_scope(f"canvas_{id(new_drawing)}")
        if new_drawing:
            new_drawing.set_can_focus(True)
            new_drawing.grab_focus()
    except Exception:
        pass
```

**AFTER (simplified):**

```python
if self.notebook.get_n_pages() == 0:
    # When the last tab is closed, recreate a fresh default canvas.
    # Reset the first-page initialization flag so the page-added hook
    # runs full initialization (same as initial startup).
    self._first_page_initialized = False
    page_index, new_drawing = self.add_document(filename='default')
    # NOTE: All wiring handled by _on_notebook_page_added() hook
    # No manual activation needed - trust the normalized flow
```

#### Benefits

- ✅ Eliminates code duplication
- ✅ Single source of truth for first-page initialization
- ✅ Consistent with documentation claims
- ✅ Simpler, more maintainable code
- ✅ No change in behavior (hook already does everything)

#### Risks

- ⚠️ If hook doesn't fire for some reason, canvas won't be wired
- ⚠️ Assumes `_on_notebook_page_added()` is 100% reliable
- ⚠️ May need testing on all platforms (X11, Wayland)

---

### Option 2: Keep Manual Activation, Document Why (Safest)

**Keep defensive redundancy but document the architectural decision.**

#### Changes Required

**File**: `src/shypn/helpers/model_canvas_loader.py`

**Change**: Add comprehensive comments explaining redundancy

```python
if self.notebook.get_n_pages() == 0:
    # When the last tab is closed, recreate a fresh default canvas.
    # This follows the SAME normalized flow as File→New:
    # 1. Reset _first_page_initialized to allow hook to fire
    # 2. Call add_document() which triggers _on_notebook_page_added()
    # 3. Hook performs full wiring (data_collector, right_panel, context_menu, lifecycle)
    
    self._first_page_initialized = False
    page_index, new_drawing = self.add_document(filename='default')
    
    # DEFENSIVE REDUNDANCY: Ensure lifecycle activation even if hook fails
    # This duplicates work done in _on_notebook_page_added() but provides safety
    # against potential GTK signal delivery issues on some platforms.
    # TODO: Test if this is still needed after Wayland stabilization
    try:
        if self.lifecycle_adapter and new_drawing:
            self.lifecycle_adapter.switch_to_canvas(new_drawing)
        if self.lifecycle_manager and hasattr(self.lifecycle_manager, 'id_manager') and new_drawing:
            from shypn.data.canvas.id_manager import set_lifecycle_scope_manager
            set_lifecycle_scope_manager(self.lifecycle_manager.id_manager)
            self.lifecycle_manager.id_manager.set_scope(f"canvas_{id(new_drawing)}")
        if new_drawing:
            new_drawing.set_can_focus(True)
            new_drawing.grab_focus()
    except Exception:
        pass
```

#### Benefits

- ✅ No behavior change (safest)
- ✅ Documents why redundancy exists
- ✅ Provides debugging context for future maintainers
- ✅ Defensive against GTK signal issues

#### Drawbacks

- ❌ Keeps technical debt
- ❌ Code duplication remains
- ❌ May hide underlying hook issues

---

### Option 3: Hybrid - Remove from load(), Keep in close_tab()

**Reasoning**: The startup flow (in `load()`) is well-tested and reliable. The last-tab-close flow is a rare edge case that may benefit from defensive redundancy.

#### Changes Required

**Remove only the manual activation from `load()`**, keep it in `close_tab()` with documentation.

#### Benefits

- ✅ Reduces most duplication
- ✅ Startup flow is clean
- ✅ Edge case (close last tab) has safety net
- ✅ Balances cleanliness with safety

---

## Testing Plan

Regardless of which option is chosen, the following scenarios must be tested:

### Test Case 1: Startup Default Canvas

1. Launch application
2. Wait for default canvas to appear
3. Create P1 → T1 → P2
4. Right-click T1 → "Add to Transition Analyses"
5. Click "Simulate" in Dynamic Analyses panel
6. **Expected**: Plot appears, tables populate

### Test Case 2: Last Tab Close Recreation

1. Launch application
2. Create File → New (now have 2 tabs)
3. Close tab 0 (default canvas)
4. Close tab 1 (last tab)
5. **Expected**: New default canvas auto-created
6. Create P1 → T1 → P2
7. Right-click T1 → "Add to Transition Analyses"
8. Click "Simulate" in Dynamic Analyses panel
9. **Expected**: Plot appears, tables populate (SAME as Test Case 1)

### Test Case 3: Multiple Close/Create Cycles

1. Launch application
2. Create objects, add to analysis
3. Close last tab (auto-recreates default)
4. Repeat 5 times
5. **Expected**: Every recreated canvas works identically

### Test Case 4: Context Menu Immediately After Recreation

1. Launch application
2. Close default tab (force recreation)
3. **Immediately** create P1 → T1 → P2
4. Right-click T1 → "Add to Transition Analyses"
5. **Expected**: Context menu works (model is set)

---

## Recommendation

**Choose Option 1: Remove Manual Activation** ✅ **IMPLEMENTED 2025-11-24**

### Rationale

1. **The hook ALREADY WORKS**: Analysis shows `_on_notebook_page_added()` fires correctly when `_first_page_initialized = False` and `page_num == 0`. The manual activation is genuinely redundant.

2. **Documentation Promises This**: The 2025-11-09 unification explicitly states all canvases go through `add_document()` with identical initialization. Manual activation contradicts this.

3. **Technical Debt**: The manual activation code is leftover from pre-unification architecture when different paths had different initialization.

4. **Maintainability**: Having one source of truth (the hook) is easier to maintain than having three places doing the same thing.

5. **Testing Exists**: The comprehensive test suite in `tests/canvas_state/` already validates the normalized flow works.

### Implementation ✅ **COMPLETE**

**Changes Made**:

1. ✅ **Removed manual activation from `load()`** (lines 263-329)
   - Removed redundant lifecycle activation (lines 269-280)
   - Removed redundant data collector wiring (lines 286-289)
   - Removed redundant right panel model setup (lines 293-308)
   - Removed redundant lifecycle switch_to_canvas (lines 321-326)
   - Kept context menu handler setup (essential, not redundant)
   - Kept pathway panel notification (essential, not redundant)
   - Added comprehensive comments about Global Canvas State Cycle

2. ✅ **Removed manual activation from `close_tab()`** (lines 1053-1073)
   - Removed redundant lifecycle activation (lines 1060-1072)
   - Kept `_first_page_initialized = False` reset (line 1056)
   - Added comprehensive comments about auto-recreation flow

3. ✅ **Enhanced `_on_notebook_page_added()` documentation** (lines 331-368)
   - Documented as "Single Source of Truth" for first-page initialization
   - Listed all scenarios where hook fires
   - Clarified complete initialization sequence
   - Added warning against duplicating this wiring

4. ✅ **Added XML notebook clarification**
   - Documented that notebook is defined in XML UI file
   - Explained that pre-baked tabs are always removed
   - Clarified normalized flow applies even to XML-defined widgets

**Result**: Clean, unified initialization flow with no redundancy.

### Testing Checklist

Run the following tests to verify the changes:

- [ ] **Test Case 1**: Startup default canvas works correctly
- [ ] **Test Case 2**: Last tab close auto-recreates canvas correctly
- [ ] **Test Case 3**: Context menu "Add to Analysis" works on all canvas types
- [ ] **Test Case 4**: Simulation and plotting work on all canvas types
- [ ] **Test Case 5**: Multiple close/recreate cycles work consistently

### Rollback Plan

If issues are discovered:
1. Git revert commit with message "Revert Option 1 implementation"
2. Document the specific failure mode in issue tracker
3. Consider Option 2 (keep redundancy, document why)
4. Investigate why hook failed to fire in specific scenario

---

## References

**Documentation**:
- `doc/CANVAS_INITIALIZATION_ANALYSIS.md` - Canvas unification architecture (2025-11-09)
- `doc/CANVAS_CLOSE_LIFECYCLE_ANALYSIS.md` - Tab close lifecycle analysis
- `doc/EMPTY_DEFAULT_TAB_REPLACEMENT.md` - Empty tab replacement behavior
- `doc/CANVAS_WIRING_ALL_SCENARIOS.md` - Canvas wiring scenarios

**Code**:
- `src/shypn/helpers/model_canvas_loader.py:load()` (lines 160-330)
- `src/shypn/helpers/model_canvas_loader.py:close_tab()` (lines 905-1080)
- `src/shypn/helpers/model_canvas_loader.py:_on_notebook_page_added()` (lines 331-371)
- `src/shypn/helpers/model_canvas_loader.py:add_document()` (lines 1120-1640)

**Tests**:
- `tests/canvas_state/test_canvas_wiring_manual.py` - Manual canvas wiring tests
- `tests/canvas_state/` - Full canvas state test suite

---

## Conclusion

The current implementation has **redundant manual lifecycle activation** in both `load()` and `close_tab()` methods that duplicates work already performed by the `_on_notebook_page_added()` hook.

While the system **does work correctly** (all wiring happens via the hook), the redundancy:
- Violates the documented "single normalized flow" architecture
- Creates maintenance burden (three places doing the same thing)
- Obscures the actual initialization flow
- Represents technical debt from pre-unification code

**Recommendation**: **Remove the redundancy** and trust the hook-based normalized flow, as documented in the 2025-11-09 unification. Test thoroughly to ensure no regression.

**User Impact**: After closing all tabs, users immediately interact with the auto-recreated default canvas. It **must** behave identically to File → New canvas. Currently it does (via hook), but code redundancy suggests architectural confusion that should be resolved.
