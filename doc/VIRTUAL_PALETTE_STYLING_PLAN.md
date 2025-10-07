# Tools & Operations Palette Styling Refactor Plan

**Date**: October 7, 2025  
**Objective**: Add purple gradient containers to tools and operations palettes to match edit palette's zoom-style appearance

---

## Overview

Currently, the tools and operations palettes have transparent backgrounds with only the buttons styled. We need to add purple gradient containers (like edit/mode/zoom palettes) to give them a unified, professional appearance.

---

## Visual Comparison

### Current (Transparent Background)
```
[P] [T] [A]       [S] [L] [U] [R]
↑ Buttons only, no container
```

### Target (Purple Gradient Containers) ✨
```
╔═══════════╗     ╔═══════════════╗
║ [P][T][A] ║     ║ [S][L][U][R]  ║
╚═══════════╝     ╚═══════════════╝
↑ Purple gradient containers (like edit/mode/zoom)
```

---

## Implementation Strategy

The palettes are created programmatically (no UI files), extending `BasePalette`. We need to modify the CSS in `_get_css()` methods to add container styling.

---

## Phase 1: Tools Palette Styling 🛠️

**File**: `src/shypn/edit/tools_palette_new.py`

**Current CSS Structure**:
```python
def _get_css(self) -> bytes:
    return b"""
    .palette-tools {
        /* Currently has no background */
    }
    
    .palette-tools .tool-button {
        /* White gradient buttons */
    }
    """
```

**Target CSS Structure**:
```python
def _get_css(self) -> bytes:
    return b"""
    /* Purple gradient container (match edit/mode/zoom) */
    .palette-tools {
        background: linear-gradient(to bottom, #667eea 0%, #764ba2 100%);
        border: 2px solid #5568d3;
        border-radius: 8px;
        padding: 3px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),
                    0 2px 4px rgba(0, 0, 0, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }
    
    .palette-tools .tool-button {
        /* Keep existing white gradient buttons */
        background: linear-gradient(to bottom, #ffffff 0%, #f0f0f5 100%);
        border: 2px solid #999999;
        border-radius: 5px;
        /* ... rest of button styling ... */
    }
    """
```

**Changes**:
1. Add purple gradient background to `.palette-tools` class
2. Add border, border-radius, padding
3. Add multi-layer box-shadow for depth
4. Keep button styling unchanged (already looks good)

---

## Phase 2: Operations Palette Styling ⚙️

**File**: `src/shypn/edit/operations_palette_new.py`

**Current CSS Structure**:
```python
def _get_css(self) -> bytes:
    return b"""
    .palette-operations {
        /* Currently has no background */
    }
    
    .palette-operations .operation-button {
        /* White gradient buttons */
    }
    """
```

**Target CSS Structure**:
```python
def _get_css(self) -> bytes:
    return b"""
    /* Purple gradient container (match edit/mode/zoom) */
    .palette-operations {
        background: linear-gradient(to bottom, #667eea 0%, #764ba2 100%);
        border: 2px solid #5568d3;
        border-radius: 8px;
        padding: 3px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),
                    0 2px 4px rgba(0, 0, 0, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }
    
    .palette-operations .operation-button,
    .palette-operations .select-button {
        /* Keep existing white gradient buttons */
        background: linear-gradient(to bottom, #ffffff 0%, #f0f0f5 100%);
        border: 2px solid #999999;
        border-radius: 5px;
        /* ... rest of button styling ... */
    }
    """
```

**Changes**:
1. Add purple gradient background to `.palette-operations` class
2. Add border, border-radius, padding
3. Add multi-layer box-shadow for depth
4. Keep button styling unchanged

---

## CSS Specifications

### Container Styling (Match Edit/Mode/Zoom Palettes)

```css
.palette-tools,
.palette-operations {
    /* Purple gradient background */
    background: linear-gradient(to bottom, #667eea 0%, #764ba2 100%);
    
    /* Border styling */
    border: 2px solid #5568d3;
    border-radius: 8px;
    
    /* Internal padding for button spacing */
    padding: 3px;
    
    /* Multi-layer shadow for depth */
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),      /* Outer shadow (dark) */
                0 2px 4px rgba(0, 0, 0, 0.3),      /* Medium shadow */
                inset 0 1px 0 rgba(255, 255, 255, 0.2);  /* Inner highlight */
}
```

### Button Spacing (No Changes Needed)
- Buttons already have proper spacing via `content_box` packing
- 3px padding in container provides buffer around buttons
- Buttons maintain their current dimensions (36×36px or 40×40px)

---

## Implementation Details

### Tools Palette Changes

**File**: `src/shypn/edit/tools_palette_new.py`

**Location**: `_get_css()` method (around line 127-215)

**Action**: Add container CSS to `.palette-tools` selector

**Before**:
```python
def _get_css(self) -> bytes:
    return b"""
    .palette-tools {
        /* Currently empty or minimal */
    }
    """
```

**After**:
```python
def _get_css(self) -> bytes:
    return b"""
    /* Purple gradient container */
    .palette-tools {
        background: linear-gradient(to bottom, #667eea 0%, #764ba2 100%);
        border: 2px solid #5568d3;
        border-radius: 8px;
        padding: 3px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),
                    0 2px 4px rgba(0, 0, 0, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }
    
    /* Keep existing button styles unchanged */
    .palette-tools .tool-button {
        /* ... existing styles ... */
    }
    """
```

---

### Operations Palette Changes

**File**: `src/shypn/edit/operations_palette_new.py`

**Location**: `_get_css()` method (around line 160-260)

**Action**: Add container CSS to `.palette-operations` selector

**Before**:
```python
def _get_css(self) -> bytes:
    return b"""
    .palette-operations {
        /* Currently empty or minimal */
    }
    """
```

**After**:
```python
def _get_css(self) -> bytes:
    return b"""
    /* Purple gradient container */
    .palette-operations {
        background: linear-gradient(to bottom, #667eea 0%, #764ba2 100%);
        border: 2px solid #5568d3;
        border-radius: 8px;
        padding: 3px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),
                    0 2px 4px rgba(0, 0, 0, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }
    
    /* Keep existing button styles unchanged */
    .palette-operations .operation-button,
    .palette-operations .select-button {
        /* ... existing styles ... */
    }
    """
```

---

## Expected Visual Result

### Before (Current)
```
Screen layout:
                [P] [T] [A]       [S] [L] [U] [R]
                ↑ Transparent       ↑ Transparent
                
                    ╔═══════════════╗
                    ║  [ ] [E] [ ]  ║  ← Purple container
                    ╚═══════════════╝
```

### After (Target) ✨
```
Screen layout:
        ╔═══════════╗     ╔═══════════════╗
        ║ [P][T][A] ║     ║ [S][L][U][R]  ║  ← Purple containers
        ╚═══════════╝     ╚═══════════════╝
        
            ╔═══════════════╗
            ║  [ ] [E] [ ]  ║  ← Purple container
            ╚═══════════════╝
            
All three palettes now have matching purple gradient containers!
```

---

## Geometry Verification

### Container Dimensions

**Tools Palette**:
- Buttons: 3 × 36px = 108px width
- Padding: 3px × 2 = 6px
- Border: 2px × 2 = 4px
- **Total width**: ~118px (approximately 148px with spacing)

**Operations Palette**:
- Buttons: 4 × 40px = 160px width
- Padding: 3px × 2 = 6px
- Border: 2px × 2 = 4px
- **Total width**: ~170px (approximately 194px with spacing)

**Edit Palette**:
- Buttons: 3 × 28px = 84px width
- Spacing: 2 × 3px = 6px
- Padding: 3px × 2 = 6px
- Border: 2px × 2 = 4px
- **Total width**: ~100px ✓

All palettes will have consistent purple containers!

---

## Testing Checklist

After implementation:
- [ ] Tools palette has purple gradient container
- [ ] Operations palette has purple gradient container
- [ ] Containers match edit palette color (#667eea → #764ba2)
- [ ] Border radius is 8px (rounded corners)
- [ ] Box-shadow provides depth effect
- [ ] Buttons inside containers are clearly visible (white gradient)
- [ ] Button hover/active states still work correctly
- [ ] No visual artifacts or overlap
- [ ] Consistent appearance across all three palettes

---

## Files to Modify

1. **src/shypn/edit/tools_palette_new.py** (~line 127-215)
   - Modify `_get_css()` method
   - Add container CSS to `.palette-tools`

2. **src/shypn/edit/operations_palette_new.py** (~line 160-260)
   - Modify `_get_css()` method
   - Add container CSS to `.palette-operations`

---

## Success Criteria

| Criterion | Target | Verification |
|-----------|--------|--------------|
| Container color | Purple gradient (#667eea → #764ba2) | Visual inspection |
| Border style | 2px solid #5568d3, 8px radius | Visual inspection |
| Shadow depth | Multi-layer box-shadow | Visual inspection |
| Button visibility | White buttons clearly visible | Visual inspection |
| Consistency | Match edit/mode/zoom palettes | Side-by-side comparison |
| No regressions | All button functionality works | Functional testing |

---

## Timeline

- **Phase 1** (Tools palette CSS): ~5 minutes
- **Phase 2** (Operations palette CSS): ~5 minutes
- **Testing**: ~5 minutes
- **Documentation**: ~5 minutes

**Total**: ~20 minutes

---

**Ready to implement?** 🚀
