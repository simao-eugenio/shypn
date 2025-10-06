# Arc Transformation Debugging Guide

## Issue Reported
"no transformation take effect"

## Fixes Applied

### 1. Fixed `_calculate_curve_control_point` Method Signature ✅

**Problem:** The method didn't accept an `offset` parameter but we were trying to pass it.

**File:** `src/shypn/netobjs/curved_arc.py`

**Before:**
```python
def _calculate_curve_control_point(self) -> Optional[Tuple[float, float]]:
    # ...
    offset = length * self.CURVE_OFFSET_RATIO
```

**After:**
```python
def _calculate_curve_control_point(self, offset=None) -> Optional[Tuple[float, float]]:
    # ...
    # Control point offset: use provided offset or default to 20% of line length
    if offset is None:
        offset = length * self.CURVE_OFFSET_RATIO
```

**Impact:** This allows parallel arcs to pass custom offsets for proper curve positioning.

### 2. Added Debug Output for Transformations ✅

**Files Modified:**
- `src/shypn/helpers/model_canvas_loader.py` - Added debug prints to transformation callbacks
- `src/shypn/data/model_canvas_manager.py` - Added debug prints to `replace_arc()` method

**Debug Output Shows:**
- Current arc type before transformation
- New arc type after transformation
- Whether arc was found and replaced in manager
- Whether model was marked dirty
- Whether redraw was triggered

## Testing Procedure

### 1. Launch Application
```bash
cd /home/simao/projetos/shypn
python3 src/shypn.py
```

### 2. Create Test Scenario
1. Create a new document or open existing
2. Draw a Place (P1)
3. Draw a Transition (T1)
4. Draw an Arc from P1 to T1

### 3. Test Each Transformation

#### Test A: Make Curved
1. Right-click the arc
2. Select "Transform Arc ►" → "Make Curved"
3. **Expected debug output:**
   ```
   [Transform] Making A1 curved (type=Arc)
   [Transform] Created new arc: type=CurvedArc
   [Manager] Replacing arc at index 0: Arc -> CurvedArc
   [Manager] Arc replaced successfully, model marked dirty
   [Transform] Replaced arc in manager, triggering redraw
   ```
4. **Expected visual result:** Arc should now have a curved bezier path

#### Test B: Make Straight (after Test A)
1. Right-click the curved arc
2. Select "Transform Arc ►" → "Make Straight"
3. **Expected debug output:**
   ```
   [Transform] Making A1 straight (type=CurvedArc)
   [Transform] Created new arc: type=Arc
   [Manager] Replacing arc at index 0: CurvedArc -> Arc
   [Manager] Arc replaced successfully, model marked dirty
   [Transform] Replaced arc in manager, triggering redraw
   ```
4. **Expected visual result:** Arc should be straight again

#### Test C: Convert to Inhibitor
1. Right-click the arc
2. Select "Transform Arc ►" → "Convert to Inhibitor Arc"
3. **Expected debug output:**
   ```
   [Transform] Converting A1 to inhibitor (type=Arc)
   [Transform] Created new arc: type=InhibitorArc
   [Manager] Replacing arc at index 0: Arc -> InhibitorArc
   [Manager] Arc replaced successfully, model marked dirty
   [Transform] Replaced arc in manager, triggering redraw
   ```
4. **Expected visual result:** Arrowhead replaced with hollow circle

#### Test D: Convert to Normal (after Test C)
1. Right-click the inhibitor arc
2. Select "Transform Arc ►" → "Convert to Normal Arc"
3. **Expected debug output:**
   ```
   [Transform] Converting A1 to normal (type=InhibitorArc)
   [Transform] Created new arc: type=Arc
   [Manager] Replacing arc at index 0: InhibitorArc -> Arc
   [Manager] Arc replaced successfully, model marked dirty
   [Transform] Replaced arc in manager, triggering redraw
   ```
4. **Expected visual result:** Hollow circle replaced with arrowhead

### 4. Test All Combinations

| Start Type | Transform 1 | Result 1 | Transform 2 | Result 2 |
|------------|-------------|----------|-------------|----------|
| Arc | Make Curved | CurvedArc | Convert to Inhibitor | CurvedInhibitorArc |
| Arc | Convert to Inhibitor | InhibitorArc | Make Curved | CurvedInhibitorArc |
| CurvedArc | Make Straight | Arc | Convert to Inhibitor | InhibitorArc |
| InhibitorArc | Convert to Normal | Arc | Make Curved | CurvedArc |

## Common Issues and Solutions

### Issue 1: Arc Not Transforming Visually

**Symptoms:**
- Debug output shows transformation happening
- Model marked dirty
- But arc looks the same

**Possible Causes:**
1. **Canvas not redrawing:** Check if `drawing_area.queue_draw()` is called
2. **Wrong arc being rendered:** Old arc reference might be cached somewhere
3. **Zoom/transform issues:** Arc might be rendering outside visible area

**Solutions:**
- Verify debug output shows "triggering redraw"
- Check console for Cairo errors
- Try zooming out to see if arc is visible elsewhere
- Save and reload document to force full refresh

### Issue 2: Menu Items Not Appearing

**Symptoms:**
- Right-click arc shows menu but no "Transform Arc ►" option

**Possible Causes:**
1. Arc not properly detected (isinstance check failing)
2. Import errors in arc_transform module

**Solutions:**
- Check if arc is actually an Arc instance: `print(type(obj))`
- Verify imports: `from shypn.utils.arc_transform import is_straight, is_curved, ...`
- Check console for import errors

### Issue 3: Transformation Creates Wrong Type

**Symptoms:**
- Transform creates arc of wrong type
- Debug shows: `type=Arc` when should be `type=CurvedArc`

**Possible Causes:**
1. Logic error in `transform_arc()` function
2. isinstance checks not working correctly

**Solutions:**
- Check inheritance: `isinstance(arc, (CurvedArc, CurvedInhibitorArc))`
- Verify target_class selection logic
- Add debug prints in `transform_arc()` function

### Issue 4: Properties Not Preserved

**Symptoms:**
- Arc transforms but loses weight, color, etc.

**Possible Causes:**
1. Properties not being copied in `transform_arc()`
2. New arc instance not initialized correctly

**Solutions:**
- Verify all property assignments in `transform_arc()`:
  ```python
  new_arc.color = arc.color
  new_arc.width = arc.width
  new_arc.weight = arc.weight
  new_arc.threshold = arc.threshold
  ```
- Check if properties exist on source arc

### Issue 5: Error in Console

**Symptoms:**
- Exception thrown during transformation
- Menu item click does nothing

**Possible Causes:**
1. Import error: `ModuleNotFoundError: No module named 'shypn.utils.arc_transform'`
2. Method signature mismatch
3. Missing attribute on arc

**Solutions:**
- Verify arc_transform.py exists: `ls src/shypn/utils/arc_transform.py`
- Check file permissions
- Verify all imports in transformation callbacks
- Check if arc has required attributes (source, target, weight, etc.)

## Verification Commands

### Check File Existence
```bash
# Verify all required files exist
ls -la src/shypn/netobjs/arc.py
ls -la src/shypn/netobjs/curved_arc.py
ls -la src/shypn/netobjs/inhibitor_arc.py
ls -la src/shypn/netobjs/curved_inhibitor_arc.py
ls -la src/shypn/utils/arc_transform.py
ls -la src/shypn/helpers/model_canvas_loader.py
ls -la src/shypn/data/model_canvas_manager.py
```

### Check Syntax
```bash
# Compile all modified files
python3 -m py_compile src/shypn/netobjs/curved_arc.py
python3 -m py_compile src/shypn/utils/arc_transform.py
python3 -m py_compile src/shypn/helpers/model_canvas_loader.py
python3 -m py_compile src/shypn/data/model_canvas_manager.py
```

### Test Imports
```bash
# Test if imports work
python3 -c "
import sys
sys.path.insert(0, 'src')
from shypn.netobjs import Arc, InhibitorArc, CurvedArc, CurvedInhibitorArc
from shypn.utils.arc_transform import make_curved, is_curved
print('All imports successful!')
"
```

### Manual Test in Python
```python
# Run from project root
import sys
sys.path.insert(0, 'src')

from shypn.netobjs import Arc, CurvedArc, Place, Transition
from shypn.utils.arc_transform import make_curved, is_straight, is_curved

# Create test objects
p1 = Place(100, 100, 1, "P1")
t1 = Transition(200, 100, 1, "T1")
arc = Arc(p1, t1, 1, "A1", weight=2)

# Test transformation
print(f"Before: {type(arc).__name__}, is_straight={is_straight(arc)}, is_curved={is_curved(arc)}")
new_arc = make_curved(arc)
print(f"After: {type(new_arc).__name__}, is_straight={is_straight(new_arc)}, is_curved={is_curved(new_arc)}")
print(f"Weight preserved: {new_arc.weight}")
```

## Expected Results Summary

### Visual Changes:
- **Arc → CurvedArc:** Line becomes curved bezier path
- **CurvedArc → Arc:** Curve becomes straight line
- **Arc → InhibitorArc:** Arrowhead becomes hollow circle
- **InhibitorArc → Arc:** Hollow circle becomes arrowhead
- **Parallel arcs:** Automatically offset to avoid overlap

### Property Preservation:
- ✅ Weight (critical for Petri net semantics)
- ✅ Color (visual customization)
- ✅ Line width (visual customization)
- ✅ Threshold (inhibitor semantics)
- ✅ ID and name (object identity)
- ✅ Source and target (connectivity)

### State Changes:
- ✅ Model marked modified (dirty flag)
- ✅ Canvas queued for redraw
- ✅ Arc replaced in manager's arc list
- ✅ Manager reference maintained

## Next Steps if Still Not Working

1. **Capture full debug output:**
   - Run app from terminal
   - Perform transformation
   - Copy all console output
   - Look for errors or warnings

2. **Check arc selection:**
   - Add debug in `_show_object_context_menu`:
     ```python
     print(f"Right-clicked object: type={type(obj).__name__}, name={obj.name}")
     ```

3. **Verify arc list update:**
   - Add debug after transformation:
     ```python
     print(f"Arc list types: {[type(a).__name__ for a in manager.arcs]}")
     ```

4. **Test with minimal example:**
   - Create new document
   - Add exactly 1 place, 1 transition, 1 arc
   - Try transformation on that arc only
   - Eliminates complexity of multiple objects

5. **Check GTK event handling:**
   - Verify menu item activation fires callback
   - Add debug at start of callback:
     ```python
     print("Callback fired!")
     ```

## Clean State Test

If all else fails, test with clean state:

```bash
# Backup current state
git stash

# Apply only necessary changes
git stash pop

# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Run fresh
python3 src/shypn.py
```

---

**Status:** Debug output added, method signature fixed  
**Date:** October 5, 2025  
**Next:** Run application and check console output during transformations
