# Palette Architecture - Comprehensive Analysis

## Current State (October 6, 2025)

### UI Files in `ui/palettes/`

1. **edit_palette.ui** - [E] toggle button (bottom center)
   - Status: ✅ KEEP - Controls visibility of tools
   
2. **edit_tools_palette.ui** - [S][P][T][A] tool selection buttons
   - Status: ⚠️ TO BE REPLACED by combined_tools_palette.ui
   - Contains: Select, Place, Transition, Arc tools
   
3. **editing_operations_palette.ui** - [U][R][L][D][A][X][C][V] operation buttons
   - Status: ⚠️ TO BE REPLACED by combined_tools_palette.ui
   - Contains: Undo, Redo, Lasso, Duplicate, Align, Cut, Copy, Paste
   
4. **combined_tools_palette.ui** - NEW unified palette
   - Status: ✅ CREATED but NOT WIRED
   - Contains: All tools in ONE horizontal line
   - Layout: [S][P][T][A] | [U][R] | [L] | [D][A] | [X][C][V]

5. **zoom.ui** - Zoom controls (top left)
   - Status: ✅ KEEP - Independent functionality

6. **simulate_palette.ui** - Simulation mode toggle
   - Status: ✅ KEEP - Independent functionality

7. **simulate_tools_palette.ui** - Simulation tools
   - Status: ✅ KEEP - Independent functionality

8. **mode_palette.ui** - Edit/Simulate mode switcher
   - Status: ✅ KEEP - Independent functionality

---

## Python Loader Classes

### Current Loaders (TO BE CONSOLIDATED)

1. **EditToolsLoader** (`src/shypn/helpers/edit_tools_loader.py`)
   - Loads: `edit_tools_palette.ui`
   - Manages: [S][P][T][A] buttons
   - Signals: 'tool-changed' when tool is selected
   - Status: ⚠️ NEEDS REFACTORING to use combined palette

2. **EditingOperationsPaletteLoader** (`src/shypn/edit/editing_operations_palette_loader.py`)
   - Loads: `editing_operations_palette.ui`
   - Manages: [U][R][L][D][A][X][C][V] buttons
   - Status: ⚠️ NEEDS REFACTORING to use combined palette

3. **EditingOperationsPalette** (`src/shypn/edit/editing_operations_palette.py`)
   - Business logic for operations
   - Status: ✅ KEEP - Logic is still valid

### Needed Loader (TO CREATE)

4. **CombinedToolsPaletteLoader** (NEW)
   - Will load: `combined_tools_palette.ui`
   - Will manage: ALL tools in one revealer
   - Will emit: 'tool-changed' signal
   - Will have methods for: show(), hide(), get_widget()

---

## Integration Points

### In `canvas_overlay_manager.py`

**Current Setup:**
```python
def setup_overlays():
    _setup_editing_operations_palette()  # Creates editing ops
    _setup_edit_palettes()               # Creates edit + edit_tools
    _setup_simulate_palettes()
    _setup_mode_palette()
```

**Current Problems:**
1. TWO separate palettes (`edit_tools` + `editing_operations`)
2. Both try to position independently
3. Edit palette wires to BOTH loaders separately
4. Causes positioning conflicts

**Needed Refactoring:**
```python
def setup_overlays():
    _setup_combined_tools_palette()  # ONE unified palette
    _setup_edit_palette()            # Just the [E] button
    _setup_simulate_palettes()
    _setup_mode_palette()
```

### In `edit_palette_loader.py`

**Current Wiring:**
```python
def _on_edit_toggled(toggle_button):
    if tools_palette_loader:
        tools_palette_loader.show() / hide()
    
    if editing_operations_palette_loader:
        editing_operations_palette_loader.show() / hide()
```

**Needed Wiring:**
```python
def _on_edit_toggled(toggle_button):
    if combined_tools_palette_loader:
        combined_tools_palette_loader.show() / hide()
```

---

## Architecture Comparison

### OLD (Current - Broken)

```
[E] Button (edit_palette)
    │
    ├─> controls ─> edit_tools_revealer (separate)
    │                   └─> [S][P][T][A]
    │
    └─> controls ─> editing_operations_revealer (separate)
                        └─> [U][R][L][D][A][X][C][V]

Problem: Two independent revealers fight for position
```

### NEW (Desired - Clean)

```
[E] Button (edit_palette)
    │
    └─> controls ─> combined_tools_revealer (single)
                        └─> [S][P][T][A] | [U][R] | [L] | [D][A] | [X][C][V]

Solution: ONE revealer, all buttons together, clean positioning
```

---

## Required Changes

### Step 1: Create CombinedToolsPaletteLoader
- [x] UI file created: `combined_tools_palette.ui`
- [ ] Create loader class: `src/shypn/helpers/combined_tools_palette_loader.py`
- [ ] Implement methods: load(), show(), hide(), get_widget()
- [ ] Handle BOTH tool selection AND operation buttons
- [ ] Emit 'tool-changed' signal for tool buttons
- [ ] Connect operation button click handlers

### Step 2: Update CanvasOverlayManager
- [ ] Add import for CombinedToolsPaletteLoader
- [ ] Create `_setup_combined_tools_palette()` method
- [ ] Remove `_setup_edit_tools_palette()` call
- [ ] Remove `_setup_editing_operations_palette()` call
- [ ] Wire combined palette to edit palette

### Step 3: Update EditPaletteLoader
- [ ] Remove `set_tools_palette_loader()` method (or keep for compatibility)
- [ ] Remove `set_editing_operations_palette_loader()` method
- [ ] Add `set_combined_tools_palette_loader()` method
- [ ] Update `_on_edit_toggled()` to control single combined palette

### Step 4: Update ModelCanvasLoader (if needed)
- [ ] Update tool-changed signal connection
- [ ] Ensure EditOperations instance is passed to combined loader

### Step 5: Deprecate Old Files
- [ ] Mark `edit_tools_palette.ui` as deprecated (or delete)
- [ ] Mark `editing_operations_palette.ui` as deprecated (or delete)
- [ ] Keep old loader classes for reference, mark deprecated

---

## Signal Flow

### Tool Selection (EditToolsLoader functionality)
```
User clicks [P]
    ↓
Combined Palette: _on_place_toggled()
    ↓
Emit: 'tool-changed' signal with 'place'
    ↓
ModelCanvasLoader: receives signal
    ↓
CanvasManager: set_mode('place')
```

### Operation Button (EditingOperationsPalette functionality)
```
User clicks [U]
    ↓
Combined Palette: _on_undo_clicked()
    ↓
EditOperations: undo()
    ↓
Canvas: refresh
```

---

## Benefits of Unified Architecture

### Before (Current)
- ❌ Two separate revealers
- ❌ Complex positioning with margins
- ❌ Two loaders to manage
- ❌ Edit palette controls two palettes
- ❌ Potential for overlap/conflicts
- ❌ GTK warnings about negative widths

### After (Unified)
- ✅ Single revealer
- ✅ Clean centered positioning
- ✅ One loader to manage
- ✅ Edit palette controls one palette
- ✅ No positioning conflicts
- ✅ Clean GTK layout
- ✅ All tools in logical sequence
- ✅ Visual separators between groups

---

## Visual Layout Comparison

### Current (Trying to achieve):
```
[E] OFF:    [E]

[E] ON:     [S][P][T][A]       [U][R][L][D][A][X][C][V]
            ↑ edit_tools       ↑ editing_operations
            (separate revealers trying to position independently)
```

### Proposed (Clean):
```
[E] OFF:    [E]

[E] ON:     [S][P][T][A] | [U][R] | [L] | [D][A] | [X][C][V]
            ↑ single combined_tools_revealer
            (centered, all together, logical groups)
```

---

## Implementation Priority

### High Priority (Blocking)
1. ✅ Create combined_tools_palette.ui
2. ⏳ Create CombinedToolsPaletteLoader class
3. ⏳ Wire to CanvasOverlayManager
4. ⏳ Update EditPaletteLoader
5. ⏳ Test show/hide functionality

### Medium Priority (Cleanup)
6. ⏳ Remove old edit_tools_palette.ui
7. ⏳ Remove old editing_operations_palette.ui
8. ⏳ Update documentation

### Low Priority (Optional)
9. ⏳ Mark old loaders as deprecated
10. ⏳ Add migration notes for external code

---

## Testing Checklist

### Functional Tests
- [ ] [E] button shows combined palette
- [ ] [E] button hides combined palette
- [ ] Tool selection works ([S][P][T][A])
- [ ] Tool-changed signal emitted correctly
- [ ] Operation buttons respond ([U][R][L][D][A][X][C][V])
- [ ] Keyboard shortcuts still work
- [ ] Mode switching (edit/simulate) works

### Visual Tests
- [ ] Palette centered at bottom
- [ ] All buttons visible
- [ ] Separators show logical groups
- [ ] No overlap with [E] button
- [ ] No GTK warnings in console
- [ ] Smooth show/hide (no animation lag)

### Integration Tests
- [ ] Works with file operations
- [ ] Works with canvas rendering
- [ ] Works with undo/redo system
- [ ] Works with selection system

---

## Next Actions

1. **IMMEDIATE**: Create `CombinedToolsPaletteLoader` class
   - Combine functionality from EditToolsLoader + EditingOperationsPaletteLoader
   - Handle both tool buttons and operation buttons
   - Single revealer management

2. **NEXT**: Update CanvasOverlayManager
   - Replace dual palette setup with single combined palette

3. **THEN**: Update EditPaletteLoader
   - Simplify to control single palette

4. **FINALLY**: Test and cleanup
   - Remove old files
   - Update documentation

---

## File Status Summary

| File | Status | Action |
|------|--------|--------|
| `combined_tools_palette.ui` | ✅ Created | Wire to loader |
| `edit_tools_palette.ui` | ⚠️ Active | Replace |
| `editing_operations_palette.ui` | ⚠️ Active | Replace |
| `CombinedToolsPaletteLoader` | ❌ Missing | CREATE |
| `EditToolsLoader` | ⚠️ Active | Deprecate |
| `EditingOperationsPaletteLoader` | ⚠️ Active | Deprecate |
| `canvas_overlay_manager.py` | ⚠️ Dual setup | Refactor |
| `edit_palette_loader.py` | ⚠️ Dual control | Simplify |

---

**Analysis Date:** October 6, 2025  
**Status:** Architecture defined, ready for implementation  
**Blocker:** Need to create CombinedToolsPaletteLoader class
