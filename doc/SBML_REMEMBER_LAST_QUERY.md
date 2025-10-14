# SBML Import: Remember Last BioModels Query

**Date**: October 12, 2025  
**Feature**: Remember last BioModels ID query in SBML import panel  
**Status**: ✅ Implemented

---

## Problem

When importing SBML models from BioModels database, the entry field was empty each time, requiring users to re-type the BioModels ID even for repeated fetches of the same model during testing/development.

**User Request**: "can you verify of the sbml path accepts the last query on fetch entry or its hardcode, make it accepts last query please"

---

## Solution

Implemented workspace settings integration to remember and restore the last BioModels ID query.

### Changes Made

#### 1. Updated `SBMLImportPanel` Class
**File**: `src/shypn/helpers/sbml_import_panel.py`

**Added** workspace_settings parameter:
```python
def __init__(self, builder, model_canvas=None, workspace_settings=None):
    # Store workspace_settings reference
    self.workspace_settings = workspace_settings
    
    # ... existing code ...
    
    # Load last query on initialization
    self._load_last_biomodels_query()
```

**Added** method to load last query:
```python
def _load_last_biomodels_query(self):
    """Load the last BioModels query from workspace settings."""
    if not self.workspace_settings or not self.sbml_biomodels_entry:
        return
    
    try:
        last_query = self.workspace_settings.get_setting(
            "sbml_import", "last_biomodels_id", ""
        )
        if last_query:
            self.sbml_biomodels_entry.set_text(last_query)
            self.logger.debug(f"Loaded last BioModels query: {last_query}")
    except Exception as e:
        self.logger.warning(f"Could not load last BioModels query: {e}")
```

**Added** method to save query:
```python
def _save_biomodels_query(self, biomodels_id: str):
    """Save the BioModels query to workspace settings."""
    if not self.workspace_settings:
        return
    
    try:
        self.workspace_settings.set_setting(
            "sbml_import", "last_biomodels_id", biomodels_id
        )
        self.logger.debug(f"Saved BioModels query: {biomodels_id}")
    except Exception as e:
        self.logger.warning(f"Could not save BioModels query: {e}")
```

**Modified** `_on_fetch_clicked` to save query:
```python
def _on_fetch_clicked(self, button):
    biomodels_id = self.sbml_biomodels_entry.get_text().strip()
    if not biomodels_id:
        self._show_status("Please enter a BioModels ID", error=True)
        return
    
    # Save query to workspace settings (NEW!)
    self._save_biomodels_query(biomodels_id)
    
    # Continue with fetch...
```

#### 2. Updated `PathwayPanelLoader` Class
**File**: `src/shypn/helpers/pathway_panel_loader.py`

**Added** workspace_settings parameter:
```python
def __init__(self, ui_path=None, model_canvas=None, workspace_settings=None):
    self.workspace_settings = workspace_settings
    # ...
```

**Modified** SBML controller instantiation:
```python
self.sbml_import_controller = SBMLImportPanel(
    self.builder,
    self.model_canvas,
    self.workspace_settings  # NEW!
)
```

**Updated** `create_pathway_panel` function:
```python
def create_pathway_panel(ui_path=None, model_canvas=None, workspace_settings=None):
    loader = PathwayPanelLoader(ui_path, model_canvas, workspace_settings)
    loader.load()
    return loader
```

#### 3. Updated Main Application
**File**: `src/shypn.py`

**Modified** pathway panel creation:
```python
pathway_panel_loader = create_pathway_panel(
    model_canvas=model_canvas_loader,
    workspace_settings=workspace_settings  # NEW!
)
```

---

## Workspace Settings Schema

The workspace settings already had support for this feature:

```python
# src/shypn/workspace_settings.py
"sbml_import": {
    "last_biomodels_id": ""  # Remember last BioModels query
}
```

No changes to workspace_settings.py were needed - the infrastructure was already there!

---

## User Experience

### Before (Problem):
```
1. Open SBML import panel
2. Switch to BioModels tab
3. Entry field is EMPTY
4. Type "BIOMD0000000012" (Repressilator)
5. Click Fetch → Success
6. Close and reopen panel
7. Entry field is EMPTY again ❌
8. Must re-type the ID
```

### After (Solution):
```
1. Open SBML import panel
2. Switch to BioModels tab
3. Entry field shows "BIOMD0000000012" ✅ (from last session)
4. Can click Fetch immediately or edit
5. Type new ID "BIOMD0000000064" (Glycolysis)
6. Click Fetch → Success (saves new ID)
7. Close and reopen panel
8. Entry field shows "BIOMD0000000064" ✅ (remembered!)
```

---

## Technical Details

### Save Trigger
The query is saved when user clicks **Fetch** button, not on every keystroke. This ensures:
- Only validated/used queries are remembered
- No unnecessary file I/O
- Clear user intent (they actually want to fetch this model)

### Load Trigger
The last query is loaded when the SBML import panel is initialized (after widgets are created and signals connected). This ensures:
- Entry field is populated before user sees it
- No race conditions with UI initialization
- Clean separation of concerns

### Persistence
- Saved to: `~/.config/shypn/workspace.json`
- Format: `{"sbml_import": {"last_biomodels_id": "BIOMD0000000012"}}`
- Persists across application restarts
- Survives system reboots

### Error Handling
- Gracefully handles missing workspace_settings (optional parameter)
- Logs warnings if load/save fails
- Never crashes - fails silently with logging
- Compatible with test environments (no workspace_settings)

---

## Testing

### Manual Test Steps:
1. ✅ Start Shypn
2. ✅ Open Pathway panel
3. ✅ Switch to SBML Import → BioModels tab
4. ✅ Entry should be empty (first time)
5. ✅ Type "BIOMD0000000012"
6. ✅ Click Fetch
7. ✅ Close Shypn completely
8. ✅ Restart Shypn
9. ✅ Open Pathway panel → SBML → BioModels
10. ✅ Entry should show "BIOMD0000000012"
11. ✅ Type different ID "BIOMD0000000064"
12. ✅ Click Fetch
13. ✅ Entry remembered as "BIOMD0000000064" next time

### Edge Cases:
- ✅ No workspace_settings: Feature disabled gracefully
- ✅ Empty last query: Entry starts empty
- ✅ Invalid model ID: Query still saved (user might retry)
- ✅ Manual file path entry: Not affected (separate field)

---

## Benefits

### For Development/Testing:
- Faster iteration when testing same model repeatedly
- No re-typing model IDs
- Smooth workflow for validation testing

### For Research Use:
- Remember commonly used reference models
- Quick access to favorite pathways
- Reduced typing errors

### For User Experience:
- Intelligent defaults
- Respects user's last action
- Feels responsive and helpful

---

## Related Features

### Current Workspace Settings:
```python
{
    "window_geometry": { ... },
    "sbml_import": {
        "last_biomodels_id": "BIOMD0000000012"
    }
}
```

### Future Enhancements (Ideas):
- Remember last SBML local file path
- Remember SBML import options (spacing, scale)
- History of recent BioModels IDs (dropdown)
- Favorites list for frequently used models
- Recent pathways panel with quick re-import

---

## Files Modified

1. **`src/shypn/helpers/sbml_import_panel.py`**
   - Added workspace_settings parameter
   - Added `_load_last_biomodels_query()` method
   - Added `_save_biomodels_query()` method
   - Modified `_on_fetch_clicked()` to save query

2. **`src/shypn/helpers/pathway_panel_loader.py`**
   - Added workspace_settings parameter to `__init__`
   - Pass workspace_settings to SBMLImportPanel
   - Updated `create_pathway_panel()` function

3. **`src/shypn.py`**
   - Pass workspace_settings to `create_pathway_panel()`

4. **`src/shypn/workspace_settings.py`**
   - No changes (schema already existed!)

**Total**: 3 files modified, ~40 lines added

---

## Conclusion

**Feature Status**: ✅ **Implemented and working**

**User Request**: "accept the current and remember the last, yes"

**Result**: SBML import panel now remembers the last BioModels ID query and pre-fills it on next use, making repeated fetches much faster and more convenient.

This improves the workflow for validation testing (using control models like Repressilator, Glycolysis, etc.) and makes the tool more user-friendly for research use.

---

*Committed with beautiful pathway rendering improvements!* 🎨✅
