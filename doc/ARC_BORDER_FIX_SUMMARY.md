# Arc Border Width Fix - Applied! ✅

**Date**: 2025-10-10  
**Issue**: User requirement - "arrow must touch perimeter minus half of the border"  
**Status**: ✅ **FIXED**

---

## What Was Wrong

Arcs were connecting to the **mathematical perimeter** of objects (center of border stroke), but they should connect to the **inner edge of border** for a clean visual appearance.

### The Problem:
```
BEFORE FIX:
    Place (radius=25, border_width=3)
         ●━━━━━━━━►
         ↑
    Arc touched at radius=25
    But border extends from 23.5 to 26.5
    Arc appeared to START INSIDE the border!
```

---

## What Was Fixed

Updated `src/shypn/netobjs/arc.py` method `_get_boundary_point()`:

### For Place (Circle):
```python
# Now accounts for border width
border_offset = border_width / 2 = 3.0 / 2 = 1.5 pixels
effective_radius = radius - border_offset
                 = 25.0 - 1.5 = 23.5 pixels

Arc touches at 23.5 (inner edge of border) ✅
```

### For Transition (Rectangle):
```python
# Now insets by border width
border_offset = 1.5 pixels
effective_half_width = width/2 - 1.5
effective_half_height = height/2 - 1.5

Arc touches at inset edges (inner border edge) ✅
```

---

## Result

```
AFTER FIX:
    Place (radius=25, border_width=3)
         ●━━━━━━━━►
          ↑
    Arc touches at radius=23.5 (inner edge)
    Clean connection, no overlap! ✅
```

---

## What to Test

### Close and Reopen Application
The fix requires restarting the application to load the updated code.

### Test Steps:
1. **Close** current application instance
2. **Reopen**: Run `/usr/bin/python3 /home/simao/projetos/shypn/src/shypn.py`
3. Create **Place** at (100, 100)
4. Create **Transition** at (300, 100)
5. Draw **arc** from Place to Transition
6. **Zoom in** to 200-400% to inspect connection
7. **Check**: Arc should touch at inner edge of border (1.5px inside outer edge)

### Expected Result:
- ✅ Clean connection at border inner edge
- ✅ No overlap with border stroke
- ✅ No visible gap

---

## Benefits

### All Arc Types Fixed:
- ✅ `Arc` (straight, normal)
- ✅ `InhibitorArc` (with circle at end)
- ✅ `CurvedArc` (Bezier curve)
- ✅ `CurvedInhibitorArc` (both curved and inhibitor)

All inherit from Arc and use the same `_get_boundary_point()` method!

---

## Documentation

Full technical details: `doc/BUGFIX_ARC_BORDER_WIDTH_ACCOUNTING.md`

---

## Ready to Test! 🚀

**Next Step**: Close and reopen the application, then run Test 1 to verify the fix works correctly!
