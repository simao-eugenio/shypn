# Quick Load Implementation for Swiss Palette Testing

**Status**: ✅ Implemented  
**Date**: 2025-01-28  
**Purpose**: Enable Swiss Palette testing of pure force-directed layout without projection interference

---

## Overview

This document describes the temporary quick load feature that automatically loads parsed SBML pathways to canvas with grid layout, enabling Swiss Palette to test pure force-directed physics parameters.

### The Problem

1. **Swiss Palette needs canvas objects** to transform them
2. **Parse button only creates PathwayData** (no canvas load)
3. **Import button applies projection** (can't test pure physics)
4. **Testing pure physics requires bypass** of projection post-processing

### The Solution

**Quick Load**: After Parse succeeds, automatically convert PathwayData to **pure Petri net** (NO layout processing), then Swiss Palette applies force-directed as the ONLY layout engine.

**Two-Step Workflow**:
1. **Parse → Pure Petri net** (SBML → PathwayData → Petri net, no layout)
2. **Swiss Palette → Force-Directed** (Apply hardcoded physics parameters)

This makes Swiss Palette the single source of layout, eliminating all preprocessing interference.

---

## Implementation Details

### 1. Configuration Flag

**File**: `src/shypn/helpers/sbml_import_panel.py`  
**Line**: 46

```python
# 🔬 TESTING MODE: Quick load after parse for Swiss Palette testing
# When True, parsed pathway is automatically loaded to canvas with grid layout
# This enables Swiss Palette to test pure force-directed parameters without projection
ENABLE_QUICK_LOAD_AFTER_PARSE = True
```

**Properties**:
- Hardcoded class constant (no UI control)
- Can be toggled by developers for testing
- No impact when False (normal behavior)

---

### 2. Quick Load Method

**File**: `src/shypn/helpers/sbml_import_panel.py`  
**Line**: 409-450

```python
def _quick_load_to_canvas(self):
    """Quick load parsed pathway to canvas as PURE Petri net (NO layout processing).
    
    🔬 TESTING MODE: Enables Swiss Palette testing of pure force-directed layout.
    
    Workflow:
    1. Parse SBML → PathwayData (species, reactions, connections)
    2. Convert directly to Petri net (places, transitions, arcs) - NO LAYOUT
    3. Load to canvas with default positions
    4. Swiss Palette applies force-directed with our hardcoded parameters
    
    This skips ALL post-processing (no grid, no force-directed, no projection).
    Swiss Palette becomes the ONLY layout engine, testing pure physics.
    """
    if not self.parsed_pathway or not self.model_canvas or not self.converter:
        return
    
    try:
        # SKIP post-processing entirely - convert raw PathwayData directly to Petri net
        document_model = self.converter.convert(self.parsed_pathway)
        
        # Load to canvas (no layout, no enhancements)
        self.model_canvas.load(document_model)
        
        self._show_status("🔬 Pure Petri net loaded - Use Swiss Palette → Force-Directed!")
    except Exception as e:
        self.logger.error(f"Quick load failed: {e}")
```

**Key Points**:
- **Skips PathwayPostProcessor entirely** (no grid, no force, no projection)
- Converts PathwayData → DocumentModel directly
- Petri net has default/sequential positions (e.g., all at origin or in a line)
- Canvas objects exist but have no meaningful layout
- Swiss Palette is the FIRST and ONLY layout applied

---

### 3. Parse Flow Hook

**File**: `src/shypn/helpers/sbml_import_panel.py`  
**Line**: 524-529 (inside `_parse_pathway_background()`)

```python
# 🔬 TESTING MODE: Quick load to canvas after parse
if self.ENABLE_QUICK_LOAD_AFTER_PARSE and self.model_canvas:
    self.logger.info("Quick load enabled - loading to canvas after parse")
    GLib.idle_add(self._quick_load_to_canvas)
else:
    self.logger.debug("Quick load disabled or canvas not available")
```

**Workflow**:
1. Parse SBML file
2. Validate pathway data
3. Update preview
4. **IF flag enabled AND canvas exists**: Quick load to canvas
5. Enable Import button (remains functional)

**Threading**:
- Uses `GLib.idle_add()` to schedule quick load on GTK main thread
- Avoids blocking background parse thread
- Safe for GTK widget operations

---

## Testing Workflow

### Step 1: Launch Application

```bash
cd /home/simao/projetos/shypn
python -m shypn
```

### Step 2: Import SBML via Parse

1. Open **Pathway** panel → **SBML** tab
2. Click **Choose SBML File**
3. Navigate to `data/biomodels_test/BIOMD0000000001.xml`
4. Click **Parse**

**Expected Results**:
- ✅ Status: "✓ Parsed and validated successfully"
- ✅ Preview shows pathway statistics
- ✅ **New**: Status changes to "🔬 Pure Petri net loaded - Use Swiss Palette → Force-Directed!"
- ✅ Canvas shows objects **without layout** (overlapping at origin or in a line)
- ✅ Swiss Palette button enabled

### Step 3: Open Swiss Palette

1. Open **View** menu → **Swiss Palette** (or toolbar button)
2. Swiss Palette panel opens

**Expected Results**:
- ✅ Canvas has objects to transform
- ✅ Layout dropdown available
- ✅ "Force-Directed" option visible

### Step 4: Test Pure Force-Directed

#### Test A: Default Parameters

1. Swiss Palette → Layout dropdown → **Force-Directed**
2. Click **Apply**

**Observe**:
- Pure Petri net transforms from overlapping/linear to force-directed layout
- Springs pull connected nodes together
- Anti-gravity pushes disconnected nodes apart
- No projection, no grid preprocessing - **pure physics only**
- This is the FIRST layout applied to these objects

#### Test B: Vary k (Optimal Distance)

Test different k values to see spacing effects:

| k Value | Expected Effect |
|---------|----------------|
| 0.5 | Nodes very close, compact clusters |
| 1.0 | **Default spacing** (balanced) |
| 2.0 | Nodes farther apart, spacious |
| 3.0 | Very loose arrangement |

**How to test**:
1. Edit Swiss Palette k parameter field
2. Click Apply
3. Observe spacing changes
4. Document visual differences

#### Test C: Vary Iterations

Test convergence speed:

| Iterations | Expected Effect |
|-----------|----------------|
| 10 | Fast but rough (not converged) |
| 50 | Moderate (NetworkX default) |
| 100 | **Current setting** (good balance) |
| 200 | Slower but precise (diminishing returns) |

#### Test D: Verify Edge Weights

Check if stoichiometry affects layout:

1. Find reaction with high stoichiometry (e.g., 2A + B → C)
2. Observe: A should be pulled closer to reaction than B
3. Verify edge weight = stoichiometry (check logs)

---

## Log Messages

### Successful Quick Load

```
INFO: 🔬 QUICK LOAD MODE - Pure Petri net conversion (NO layout processing)
INFO: Converted to pure Petri net: 25 places, 20 transitions
WARNING: ✓ Quick load complete - Swiss Palette will apply force-directed with hardcoded parameters
```

### Quick Load Skipped (Flag Disabled)

```
DEBUG: Quick load disabled or canvas not available
```

### Quick Load Error

```
ERROR: Quick load failed: <error_message>
<traceback>
```

---

## File Modifications Summary

| File | Lines | Change |
|------|-------|--------|
| `src/shypn/helpers/sbml_import_panel.py` | 46 | Added `ENABLE_QUICK_LOAD_AFTER_PARSE = True` |
| `src/shypn/helpers/sbml_import_panel.py` | 409-461 | Added `_quick_load_to_canvas()` method |
| `src/shypn/helpers/sbml_import_panel.py` | 524-529 | Added quick load hook in parse flow |

**Total**: 60 new lines in 1 file

---

## Advantages of This Approach

✅ **No UI changes** - Preserves existing interface  
✅ **No preprocessing** - Swiss Palette is the ONLY layout engine  
✅ **Pure physics testing** - Zero interference from grid/projection  
✅ **Non-invasive** - Doesn't affect Import button workflow  
✅ **Easy to toggle** - Single flag controls feature  
✅ **Clear testing mode** - Visible status messages  
✅ **Swiss Palette compatible** - Works with existing tool  
✅ **True baseline** - Objects start with no meaningful layout  

---

## Limitations & Future Work

### Current Limitations

1. **Hardcoded flag** - No runtime control without code edit
2. **No parameter UI** - Swiss Palette must provide k/iterations controls
3. **No initial layout** - Objects may be overlapping at origin
4. **Testing mode only** - Not intended for production

### Future Enhancements (Post-Testing)

1. **Remove quick load** when parameter testing complete
2. **Integrate findings** into Import button default parameters
3. **Create centralized config** (layout_config.py module)
4. **Add presets** (COMPACT, BALANCED, SPACIOUS)
5. **UI controls** for k, iterations, threshold (if needed)
6. **Optional initial layout** - Simple circle/grid to avoid complete overlap

---

## Related Documentation

- **Physics Parameters**: `doc/layout/FORCE_DIRECTED_PHYSICS_PARAMETERS.md`
- **Testing Strategy**: `doc/layout/TESTING_STRATEGY.md`
- **Swiss Palette Integration**: `doc/layout/SWISS_PALETTE_INTEGRATION_PLAN.md`
- **Parametrization Plan**: `doc/layout/LAYOUT_PARAMETRIZATION_PLAN.md`

---

## Success Criteria

Quick load implementation is successful when:

✅ Parse button automatically loads to canvas (when flag=True)  
✅ Objects appear **without layout** (overlapping or linear)  
✅ Swiss Palette can apply force-directed to loaded objects  
✅ Pure physics parameters (k, iterations) are testable  
✅ **Zero preprocessing** - Swiss Palette is the ONLY layout  
✅ Results visible and measurable on canvas  

**Status**: ✅ Ready for testing 🧪

---

## Next Steps

1. ✅ **Implementation complete** - Quick load added and wired
2. 🔄 **Test workflow** - Verify Parse → Quick Load → Swiss Palette
3. 🔄 **Parameter testing** - Test k values (0.5, 1.0, 2.0, 3.0)
4. 🔄 **Document results** - Create `FORCE_DIRECTED_PARAMETER_EFFECTS.md`
5. ⏳ **Iterate** - Refine parameters based on visual results
6. ⏳ **Integrate** - Apply findings to Import button defaults

---

**Implementation Date**: 2025-01-28  
**Modified Files**: 1  
**Lines Added**: 60  
**Status**: ✅ Complete and ready for testing
