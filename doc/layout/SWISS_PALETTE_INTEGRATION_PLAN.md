# SBML Import Flow Analysis & Temporary Solution

**Date**: October 14, 2025  
**Goal**: Enable Swiss Palette testing of pure force-directed layout on imported SBML

---

## Current Flow

### Button 1: **Parse File** (SBML Panel)
```
Parse Button Click
    ↓
_parse_pathway_background()
    ↓
SBMLParser.parse_file()     ← Parse XML
    ↓
PathwayValidator.validate() ← Check validity
    ↓
Store: self.parsed_pathway  ← RAW PathwayData (no positions)
    ↓
Enable "Import to Canvas" button
```

**Output**: `parsed_pathway` (PathwayData object)
- ✅ Species, reactions, parameters
- ❌ No positions yet
- ❌ No colors yet
- ❌ Not converted to Petri net

### Button 2: **Import to Canvas** (SBML Panel)
```
Import Button Click
    ↓
_import_pathway_background()
    ↓
PathwayPostProcessor.process()  ← Layout + Colors + Normalization
    ├─ LayoutProcessor           ← Force-directed + Projection
    ├─ ColorProcessor
    ├─ UnitNormalizer
    └─ ...
    ↓
PathwayConverter.convert()      ← PathwayData → DocumentModel
    ↓
EnhancementPipeline (optional)  ← Layout optimization
    ↓
model_canvas.load()             ← Load into canvas
```

**Output**: Fully processed pathway on canvas
- ✅ Positions (with force-directed + projection)
- ✅ Colors
- ✅ Converted to Petri net (Places/Transitions/Arcs)
- ✅ Loaded on canvas

---

## Swiss Palette Flow (Already Exists)

### Layout Button → Force-Directed
```
Swiss Palette: Layout Button
    ↓
"Force-Directed" option selected
    ↓
Applies to CURRENT canvas objects
    ↓
Re-calculates positions using NetworkX
    ↓
Updates canvas (objects already exist)
```

**Key**: Swiss Palette operates on **existing DocumentModel** objects already loaded on canvas.

---

## The Problem

**Swiss Palette needs objects on canvas to transform:**
```
Parse → Import (full pipeline) → Canvas
                ↑
        (Projection applied here)
                ↓
        Swiss Palette ← Can't test pure physics!
```

Currently:
1. Parse only creates PathwayData (no canvas objects)
2. Import applies full pipeline (force-directed + projection + conversion)
3. Swiss Palette can transform, but projection already applied

**We can't test pure force-directed because projection happens BEFORE Swiss Palette!**

---

## Proposed Solution: Temporary "Quick Import" on Parse Button

### New Flow for Parse Button:

```
Parse Button Click (with Shift held)
    ↓
_parse_pathway_background()
    ├─ Parse SBML (existing)
    ├─ Validate (existing)
    └─ **NEW**: Quick import to canvas
        ↓
    PathwayPostProcessor.process()
        use_raw_force_directed=True  ← BYPASS projection!
        ↓
    PathwayConverter.convert()
        ↓
    model_canvas.load()  ← Simple grid positions
        ↓
    Swiss Palette now available! ← Test pure force-directed
```

### Alternative: Add "Quick Load" Button

Add a third button between Parse and Import:
```
[Parse File] → [Quick Load (Testing)] → [Import to Canvas (Full)]
     ↓               ↓                          ↓
 PathwayData    Canvas (minimal)         Canvas (optimized)
```

---

## Implementation Options

### Option A: Modify Parse Button (Shift+Click) ⭐ RECOMMENDED

**Pros**:
- ✅ No UI changes needed
- ✅ Temporary solution (easy to remove later)
- ✅ Advanced users can test immediately

**Cons**:
- ❌ Hidden feature (not discoverable)
- ❌ Shift-click might not work on all platforms

**Implementation**:
```python
def _on_parse_clicked(self, button, event=None):
    # Check if Shift key held
    is_shift = event and (event.state & Gdk.ModifierType.SHIFT_MASK)
    
    if is_shift:
        # Quick load mode - parse + minimal import
        self._quick_load_for_testing()
    else:
        # Normal parse only
        self._parse_pathway_background()
```

### Option B: Add "Quick Load" Button

**Pros**:
- ✅ Discoverable
- ✅ Clear intent
- ✅ Easy to use

**Cons**:
- ❌ UI changes needed
- ❌ More permanent (harder to remove)
- ❌ Might confuse users

**UI Layout**:
```
Action Buttons:
  [Parse File] [Quick Load (Testing)] [Import to Canvas]
       ↓              ↓                      ↓
  Parse only    Parse + Load (grid)   Full pipeline
```

### Option C: Checkbox "Skip Post-Processing" ⭐ BEST LONG-TERM

**Pros**:
- ✅ Explicit control
- ✅ Works with existing Import button
- ✅ Scales to future options

**Cons**:
- ❌ UI changes needed
- ❌ Needs documentation

**UI Layout**:
```
Import Options:
  ☑ Skip layout post-processing (for testing)
  ☐ Use spiral layout
  
[Import to Canvas]  ← Respects checkbox
```

---

## Recommended Implementation: Option A (Quick Hack)

For **temporary testing**, implement Option A:

### Step 1: Add Quick Load Method

```python
def _quick_load_for_testing(self):
    """Quick load parsed pathway with grid layout (no post-processing).
    
    Shift+Click on Parse button activates this mode.
    Allows testing Swiss Palette with pure force-directed.
    """
    if not self.parsed_pathway:
        self._show_status("No pathway to load", error=True)
        return
    
    if not self.model_canvas or not self.converter:
        self._show_status("Error: Canvas not available", error=True)
        return
    
    self._show_status("🔬 Quick loading for testing (no post-processing)...")
    
    try:
        # Minimal processing: just grid layout
        from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
        
        postprocessor = PathwayPostProcessor(
            spacing=150.0,
            scale_factor=1.0,
            use_tree_layout=False,      # Disable hierarchical
            use_spiral_layout=False,    # Disable spiral
            use_raw_force_directed=False # Grid fallback (no force-directed yet)
        )
        
        processed = postprocessor.process(self.parsed_pathway)
        
        # Convert to Petri net
        document_model = self.converter.convert(processed)
        
        # Load to canvas (no enhancements)
        self.model_canvas.load(document_model)
        
        self._show_status("✓ Quick loaded! Use Swiss Palette → Force-Directed to test")
        
    except Exception as e:
        self._show_status(f"Quick load failed: {e}", error=True)
        import traceback
        traceback.print_exc()
```

### Step 2: Modify Parse Button Handler

```python
def _on_parse_clicked(self, button):
    """Handle parse button click.
    
    Normal click: Parse and validate only
    Shift+Click: Parse + Quick load to canvas (testing mode)
    """
    # Get current event to check modifiers
    event = Gtk.get_current_event()
    is_shift = event and (event.get_state()[1] & Gdk.ModifierType.SHIFT_MASK)
    
    if is_shift:
        self.logger.info("🔬 Shift+Parse detected - Quick load mode")
        # Parse first
        GLib.idle_add(self._parse_then_quick_load)
    else:
        # Normal parse
        GLib.idle_add(self._parse_pathway_background)

def _parse_then_quick_load(self):
    """Parse pathway then immediately quick load."""
    # Parse
    result = self._parse_pathway_background()
    
    # If parse succeeded, quick load
    if self.parsed_pathway:
        self._quick_load_for_testing()
    
    return False  # Stop GLib.idle_add
```

---

## Testing Workflow

### With Quick Load (Shift+Parse):

1. **Open SBML Import tab**
2. **Select file** (e.g., BIOMD0000000001)
3. **Shift+Click "Parse File"** ← Quick load mode
4. ✅ Pathway appears on canvas with grid layout
5. **Open Swiss Palette** (View menu or toolbar)
6. **Select "Force-Directed"** layout option
7. **Adjust parameters** (k, iterations, etc)
8. **Click Apply**
9. ✅ See pure force-directed physics (no projection)
10. **Iterate** - adjust params and re-apply

### Compare with Full Pipeline:

1. **Import same file** using "Import to Canvas" button
2. ✅ See force-directed + projection result
3. **Compare** layouts side-by-side

---

## Flow Diagram

```
┌─────────────────────────────────────┐
│        SBML Import Panel            │
└─────────────────────────────────────┘
           ↓
    [Parse File]
           ↓
    ┌─────┴─────┐
    │ Normal    │ Shift+Click
    ↓           ↓
Parse Only   Parse + Quick Load
    ↓           ↓
PathwayData  Grid Layout on Canvas
    ↓           ↓
[Import]     Swiss Palette
    ↓           ↓
Full Pipeline  Pure Force-Directed ← TEST HERE!
    ↓
Canvas
```

---

## Benefits of This Approach

✅ **No UI changes** - Just hidden Shift+Click  
✅ **Temporary** - Easy to remove when config system complete  
✅ **Enables testing** - Swiss Palette works on loaded objects  
✅ **Pure physics** - No projection interference  
✅ **Quick iteration** - Load once, test many parameter sets  

---

## After Testing Complete

Once we've characterized force-directed parameters:

1. **Remove Shift+Click hack**
2. **Implement proper config system** (layout_config.py)
3. **Add UI controls** for physics params (optional)
4. **Re-enable projection** with separate config
5. **Swiss Palette** becomes permanent feature with param controls

---

## Summary

**Current State**:
- Parse button: Only parses, no canvas load
- Import button: Full pipeline (projection included)
- Swiss Palette: Can't test pure physics

**Proposed Temporary Solution**:
- **Shift+Parse**: Quick load with grid layout
- **Swiss Palette**: Apply pure force-directed
- **Test & iterate**: Parameter experimentation

**Long-term Solution**:
- Config system with parameter presets
- UI controls for physics parameters
- Swiss Palette integrated with config

---

**Next Action**: Implement Shift+Click quick load in sbml_import_panel.py
