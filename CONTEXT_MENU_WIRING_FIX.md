# Context Menu Wiring Fix - Dynamic Analyses Panel Refactoring

**Date:** October 29, 2025  
**Branch:** dynamic-analyses-panel-health

## Summary

Fixed context menu handler wiring after refactoring the Dynamic Analyses panel from the old tab-based architecture to the new CategoryFrame-based architecture.

## Problem

After refactoring the Dynamic Analyses panel to use the new CategoryFrame architecture (like Topology and Report panels), the "Add to Analysis" context menu option was not being properly wired. Users could not right-click transitions/places and add them to analysis plots.

## Root Cause

The context menu handler initialization flow was incomplete in the refactored code:

1. `DynamicAnalysesPanel` created the handler in `_setup_context_menu()`
2. `RightPanelLoader._setup_dynamic_analyses_panel()` accessed the handler
3. **BUT**: The handler wasn't being properly updated when `set_model()` was called
4. **AND**: There were no safety checks if the handler wasn't created

## Solution

### Files Modified

1. **`src/shypn/helpers/right_panel_loader.py`**
   - Added safety check and fallback handler creation in `_setup_dynamic_analyses_panel()`
   - Enhanced `set_model()` to update both the panel AND the handler directly
   - Added warning messages for debugging

2. **`src/shypn/ui/panels/dynamic_analyses/dynamic_analyses_panel.py`**
   - Added `import sys` for error logging
   - Enhanced `set_model()` to create handler if it doesn't exist
   - Improved `_setup_context_menu()` with better error logging

### Key Changes

#### 1. RightPanelLoader: Safety Check (Line ~130)

```python
# Get context menu handler (created during panel setup)
self.context_menu_handler = self.dynamic_analyses_panel.context_menu_handler

# If handler was not created yet (shouldn't happen but safety check)
if not self.context_menu_handler:
    print("[WARNING] Context menu handler not created during panel setup, creating now...", file=sys.stderr)
    from shypn.analyses import ContextMenuHandler
    self.context_menu_handler = ContextMenuHandler(
        place_panel=self.place_panel,
        transition_panel=self.transition_panel,
        model=self.model,
        diagnostics_panel=self.diagnostics_panel
    )
    # Update the panel's reference too
    self.dynamic_analyses_panel.context_menu_handler = self.context_menu_handler
```

#### 2. RightPanelLoader: Enhanced set_model() (Line ~175)

```python
def set_model(self, model):
    """Set the model for search functionality."""
    self.model = model
    
    # Update dynamic analyses panel
    if self.dynamic_analyses_panel:
        self.dynamic_analyses_panel.set_model(model)
        
        # Update convenience accessor (panel may have recreated handler)
        self.context_menu_handler = self.dynamic_analyses_panel.context_menu_handler
    
    # Also update the handler directly if it exists
    if self.context_menu_handler:
        self.context_menu_handler.set_model(model)
```

#### 3. DynamicAnalysesPanel: Enhanced set_model() (Line ~160)

```python
def set_model(self, model):
    """Set model for all categories."""
    self.model = model
    
    # Update all categories
    for category in self.categories:
        category.set_model(model)
    
    # Update or create context menu handler
    if self.context_menu_handler:
        self.context_menu_handler.set_model(model)
    else:
        # Context menu handler doesn't exist yet, create it
        self._setup_context_menu()
```

#### 4. DynamicAnalysesPanel: Better Logging (Line ~135)

```python
def _setup_context_menu(self):
    """Set up context menu handler for plot interactions."""
    try:
        from shypn.analyses import ContextMenuHandler
        
        # Get panel references from categories
        place_panel = self.places_category.panel if self.places_category else None
        transition_panel = self.transitions_category.panel if self.transitions_category else None
        diagnostics_panel = self.diagnostics_category.panel if self.diagnostics_category else None
        
        if place_panel and transition_panel:
            self.context_menu_handler = ContextMenuHandler(
                place_panel=place_panel,
                transition_panel=transition_panel,
                model=self.model,
                diagnostics_panel=diagnostics_panel
            )
            print(f"[DYNAMIC_ANALYSES] Context menu handler created successfully", file=sys.stderr)
        else:
            print(f"[DYNAMIC_ANALYSES] Warning: Cannot create context menu handler - panels not ready", file=sys.stderr)
    except Exception as e:
        import traceback
        print(f"[DYNAMIC_ANALYSES] Warning: Could not create context menu handler: {e}", file=sys.stderr)
        traceback.print_exc()
```

## Verification

### Test Script: `test_context_menu_wiring.py`

Created comprehensive test that verifies:
1. ✓ Context menu handler exists after panel creation
2. ✓ Panel references (place_panel, transition_panel, diagnostics_panel) are correct
3. ✓ Handler has correct panel references
4. ✓ set_model() properly updates handler and creates locality detector
5. ✓ add_analysis_menu_items() adds menu items for transitions

### Test Results

```
======================================================================
✓ ALL TESTS PASSED - Context menu handler is properly wired!
======================================================================
```

### Application Startup Log

```
[DYNAMIC_ANALYSES] Context menu handler created successfully
```

## Context Menu Flow (After Fix)

1. **User right-clicks transition on canvas**
2. **`model_canvas_loader` calls `context_menu_handler.add_analysis_menu_items()`**
3. **Handler detects locality** (input/output places)
4. **Menu item added:** "Add to Transition Analysis"
5. **User clicks menu item**
6. **`_add_transition_with_locality()` called:**
   - Adds transition to TRANSITIONS panel
   - Adds all locality places to PLACES panel (via `add_locality_places()`)
7. **Matplotlib canvases update** to plot transition rates and place token counts

## Architecture Alignment

The fix ensures Dynamic Analyses panel follows the same pattern as Topology and Report panels:

| Feature | Topology ✅ | Report ✅ | Dynamic Analyses ✅ |
|---------|------------|----------|---------------------|
| CategoryFrame architecture | Yes | Yes | **Fixed** |
| Context menu integration | Yes | N/A | **Fixed** |
| Proper handler wiring | Yes | N/A | **Fixed** |
| Safety checks | Yes | Yes | **Added** |
| Debug logging | Yes | Yes | **Added** |

## Files Changed

1. `src/shypn/helpers/right_panel_loader.py` - Enhanced handler setup and model updates
2. `src/shypn/ui/panels/dynamic_analyses/dynamic_analyses_panel.py` - Enhanced handler creation and logging
3. `test_context_menu_wiring.py` - New comprehensive test script

## Testing Instructions

1. Clear Python caches:
   ```bash
   cd /home/simao/projetos/shypn
   find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
   ```

2. Run test script:
   ```bash
   python3 test_context_menu_wiring.py
   ```

3. Start application:
   ```bash
   python3 src/shypn.py
   ```
   
4. Look for log message: `[DYNAMIC_ANALYSES] Context menu handler created successfully`

5. Test context menu:
   - Create or load a model
   - Right-click a transition
   - Verify "Add to Transition Analysis" appears
   - Click it
   - Verify transition and locality places are added to plots

## Status

✅ **FIXED AND VERIFIED**

The context menu "Add to Analysis" feature is now fully functional with the refactored Dynamic Analyses panel architecture.
