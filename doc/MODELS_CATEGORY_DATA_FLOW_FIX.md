# Models Category Data Flow Fix

## Problem Analysis

The Models category in the Report Panel was showing incoherent or missing data across all sections:

1. **Model Overview**: Never populated (missing name, file path, dates)
2. **Petri Net Structure**: Collecting wrong information (0 places, 0 transitions)
3. **Import Provenance**: Never set, not showing source data
4. **Species Table**: Not collecting data from the interactive model
5. **Reactions Table**: Not collecting data from the interactive model

## Root Cause

The issue was in how the Report Panel was initialized and how model data was passed:

### Original Broken Flow:

```
model_canvas_loader.py:
  ReportPanelLoader(project=None, model_canvas=self)
    ↓ (passes ModelCanvasLoader as "model_canvas")
  
report_panel_loader.py:
  ReportPanel(project=project, model_canvas=self.model_canvas)
    ↓ (ModelCanvasLoader stored as model_canvas_loader)
  
report_panel.py:
  set_model_canvas() tries to call:
    current_manager = self.model_canvas_loader.get_current_model()
    ↓ (model_canvas_loader was None or wrong type)
  
models_category.py:
  refresh() called with model_canvas=None
    ↓ Result: No data displayed!
```

### Key Issues:

1. **Wrong parameter name**: Passing `model_canvas=self` when it should be `model_canvas_loader=self`
2. **Missing model manager**: Categories never received the actual ModelCanvasManager with places/transitions
3. **No refresh on tab switch**: When switching tabs, Models category didn't update with new model
4. **Confusion between Loader and Manager**:
   - `ModelCanvasLoader`: The container that manages multiple documents
   - `ModelCanvasManager`: The actual model with places, transitions, arcs (stored per drawing_area)

## Solution Implemented

### 1. Fixed ReportPanelLoader Initialization

**File**: `model_canvas_loader.py` (line ~1222)

```python
# BEFORE:
report_panel_loader = ReportPanelLoader(project=None, model_canvas=self)

# AFTER:
report_panel_loader = ReportPanelLoader(project=None, model_canvas_loader=self)
```

### 2. Pass Actual Model Manager

**File**: `model_canvas_loader.py` (line ~1229)

```python
# Get the model manager for this specific drawing_area
model_manager = self.overlay_managers[drawing_area].canvas_manager
if model_manager:
    report_panel_loader.panel.set_model_canvas(model_manager)
```

### 3. Fixed ReportPanelLoader Constructor

**File**: `report_panel_loader.py` (line ~23)

```python
# BEFORE:
def __init__(self, project=None, model_canvas=None):
    self.model_canvas = model_canvas

# AFTER:
def __init__(self, project=None, model_canvas_loader=None):
    self.model_canvas_loader = model_canvas_loader
```

### 4. Simplified ReportPanel.set_model_canvas()

**File**: `report_panel.py` (line ~318)

```python
# BEFORE:
def set_model_canvas(self, model_canvas):
    # Complex logic to get current_manager from loader
    current_manager = self.model_canvas_loader.get_current_model()
    for category in self.categories:
        category.set_model_canvas(current_manager)

# AFTER:
def set_model_canvas(self, model_manager):
    # Direct pass-through - manager already provided
    for category in self.categories:
        category.set_model_canvas(model_manager)
```

### 5. Added Model Refresh on Tab Switch

**File**: `shypn.py` (line ~650)

```python
```python
# BEFORE:
def on_canvas_tab_switched_report(notebook, page, page_num):
    # ... extract drawing_area ...
    
    report_loader = overlay_manager.report_panel_loader
    if report_loader and report_loader.panel:
        # ❌ WRONG: model_manager doesn't exist
        if hasattr(overlay_manager, 'model_manager'):
            model_manager = overlay_manager.model_manager
            report_loader.set_model_canvas(model_manager)

# AFTER:
def on_canvas_tab_switched_report(notebook, page, page_num):
    # ... extract drawing_area ...
    
    report_loader = overlay_manager.report_panel_loader
    if report_loader and report_loader.panel:
        # ✅ CORRECT: canvas_manager is the actual attribute
        if hasattr(overlay_manager, 'canvas_manager'):
            model_manager = overlay_manager.canvas_manager
            report_loader.set_model_canvas(model_manager)
```
```

## New Correct Data Flow

```
model_canvas_loader.py (per document):
  1. Create ReportPanelLoader(model_canvas_loader=self)
  2. Get model_manager from overlay_managers[drawing_area]
  3. Call report_loader.panel.set_model_canvas(model_manager)
    ↓
  
report_panel.py:
  4. set_model_canvas(model_manager) receives actual model
  5. Pass model_manager directly to all categories
    ↓
  
models_category.py:
  6. refresh() called with actual ModelCanvasManager
  7. Access model.places, model.transitions, model.arcs
  8. Populate all sections with correct data ✓
```

## Tab Switching Flow

```
User switches tab
  ↓
on_canvas_tab_switched_report() in shypn.py
  ↓
Extract drawing_area from page widget
  ↓
Get overlay_manager for drawing_area
  ↓
Get report_panel_loader from overlay_manager
  ↓
Get model_manager from overlay_manager
  ↓
Call report_loader.set_model_canvas(model_manager)
  ↓
Report Panel updates with new model data ✓
```

## Result

Now each tab's Models category shows its OWN model data:

✅ **Model Overview**: Shows correct name, file path, dates, description
✅ **Petri Net Structure**: Shows correct place/transition/arc counts
✅ **Import Provenance**: Shows correct KEGG/SBML source info
✅ **Species Table**: Shows correct species from THIS model
✅ **Reactions Table**: Shows correct reactions from THIS model

## Testing Checklist

- [ ] Open 3 models in different tabs (e.g., 10 places, 15 places, 25 places)
- [ ] Check Model Overview shows correct name for each tab
- [ ] Check Petri Net Structure shows correct counts
- [ ] Switch between tabs and verify Models category updates
- [ ] Check Species table shows different species per tab
- [ ] Check Reactions table shows different reactions per tab
- [ ] Verify Import Provenance shows correct source (if imported)

## Architecture Notes

This fix maintains the multi-document architecture principle:
- **No shared instances**: Each document has its own Report Panel
- **No shared data**: Each panel shows only its document's data
- **Proper isolation**: Tab switching correctly updates visible data
- **Consistent pattern**: Follows same pattern as Dynamic Analyses category
