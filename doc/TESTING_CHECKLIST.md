# Testing Checklist for Selection and Arc Creation

## Quick Test Guide

Run the application:
```bash
cd /home/simao/projetos/shypn
python3 src/shypn.py
```

---

## ✅ Test 1: Basic Object Creation

**Steps**:
1. Click [P] button (place tool)
2. Click on canvas → Should create place
3. Click [T] button (transition tool)  
4. Click on canvas → Should create transition

**Expected Terminal Output**:
```
Created P1 at (x, y)
Created T1 at (x, y)
```

**Visual Check**:
- ✓ Hollow circle (place) appears
- ✓ Black rectangle (transition) appears

**Status**: ✅ WORKS (already tested successfully)

---

## ✅ Test 2: Object Selection

**Steps**:
1. Create P1 and T1 (as above)
2. Click [P] or [T] button again to deselect tool (button should uncheck)
3. Left-click on P1 → Should select
4. Left-click on P1 again → Should deselect
5. Left-click on T1 → Should select

**Expected Terminal Output**:
```
P1 selected
P1 deselected
T1 selected
```

**Visual Check**:
- ✓ Blue highlight appears around selected object (4px wider)
- ✓ Highlight disappears when deselected
- ✓ Can select multiple objects (both P1 and T1 at same time)

**Status**: 🔄 READY TO TEST (fix applied)

---

## ✅ Test 3: Arc Creation (Valid P→T)

**Steps**:
1. Create P1 at one location
2. Create T1 at another location
3. Deselect place/transition tools
4. Click [A] button (arc tool)
5. Click on P1 → Should see "Arc creation: source P1 selected"
6. Move mouse toward T1 → Should see orange preview line
7. Click on T1 → Should create arc

**Expected Terminal Output**:
```
Arc creation: source P1 selected
Created A1: P1 → T1
```

**Visual Check**:
- ✓ Orange preview line from P1 to cursor
- ✓ Preview line starts at P1 boundary (not center)
- ✓ Small arrowhead at cursor position
- ✓ Preview disappears after clicking T1
- ✓ Final arc appears with two-line arrowhead (15px, π/5 angle)

**Status**: 🔄 READY TO TEST (fix applied)

---

## ✅ Test 4: Arc Creation (Valid T→P)

**Steps**:
1. Create T1 and P1
2. Click [A] button
3. Click T1 first (transition as source)
4. Click P1 second (place as target)

**Expected Terminal Output**:
```
Arc creation: source T1 selected
Created A1: T1 → P1
```

**Visual Check**:
- ✓ Arc created in reverse direction
- ✓ Arrowhead points toward P1

**Status**: 🔄 READY TO TEST

---

## ✅ Test 5: Bipartite Validation (P→P Invalid)

**Steps**:
1. Create P1 and P2 (two places)
2. Click [A] button
3. Click P1
4. Click P2 → Should show error

**Expected Terminal Output**:
```
Arc creation: source P1 selected
Cannot create arc: Invalid connection: Place → Place. Arcs must connect Place↔Transition (bipartite property). Valid connections: Place→Transition or Transition→Place.
```

**Visual Check**:
- ✓ Orange preview line shows while hovering
- ✓ NO arc is created after clicking P2
- ✓ Error message in terminal
- ✓ Can start new arc (source reset)

**Status**: 🔄 READY TO TEST

---

## ✅ Test 6: Bipartite Validation (T→T Invalid)

**Steps**:
1. Create T1 and T2 (two transitions)
2. Try to create arc T1 → T2

**Expected Terminal Output**:
```
Arc creation: source T1 selected
Cannot create arc: Invalid connection: Transition → Transition. Arcs must connect Place↔Transition (bipartite property). Valid connections: Place→Transition or Transition→Place.
```

**Status**: 🔄 READY TO TEST

---

## ✅ Test 7: Arc Creation Reset

**Steps**:
1. Create P1
2. Click [A] button
3. Click P1 → Source selected
4. Click on EMPTY SPACE → Should reset

**Expected Terminal Output**:
```
Arc creation: source P1 selected
(No error, just resets silently)
```

**Visual Check**:
- ✓ Orange preview line disappears
- ✓ Can click P1 again to start new arc

**Status**: 🔄 READY TO TEST

---

## ✅ Test 8: Preview Line Geometry

**Steps**:
1. Create P1 (place with radius ~20px)
2. Click [A] button
3. Click P1
4. Move cursor in circle around P1
5. Observe where preview line starts

**Visual Check**:
- ✓ Preview line starts at BOUNDARY of P1 (20px from center)
- ✓ Line always points toward cursor
- ✓ Arrowhead rotates smoothly
- ✓ Orange color clearly visible (RGB: 0.95, 0.5, 0.1)

**Status**: 🔄 READY TO TEST

---

## ✅ Test 9: Multiple Arcs

**Steps**:
1. Create: P1, T1, P2, T2
2. Create arcs:
   - P1 → T1
   - T1 → P2
   - P2 → T2
   - T2 → P1 (creates cycle)

**Expected Terminal Output**:
```
Created A1: P1 → T1
Created A2: T1 → P2
Created A3: P2 → T2
Created A4: T2 → P1
```

**Visual Check**:
- ✓ All 4 arcs visible
- ✓ Arcs render BEHIND places/transitions
- ✓ No visual overlaps
- ✓ All arrowheads point correctly

**Status**: 🔄 READY TO TEST

---

## ✅ Test 10: Selection + Arc Creation

**Steps**:
1. Create P1, T1
2. Select P1 (left-click, see blue highlight)
3. Switch to arc tool [A]
4. Create arc from P1 to T1

**Expected Behavior**:
- Selection highlight should remain during arc creation
- Arc should be created successfully

**Status**: 🔄 READY TO TEST

---

## Bug Fixes Applied

### ✅ Fix 1: Missing Imports (COMPLETED)

**Error**:
```
NameError: name 'Place' is not defined
```

**Fix**:
Added imports in `model_canvas_loader.py`:
```python
import math  # For sqrt, atan2, cos, sin in preview rendering
from shypn.api import Place, Transition, Arc  # For isinstance checks
```

**Files Modified**:
- `src/shypn/helpers/model_canvas_loader.py`

**Status**: ✅ FIXED

---

## Current Status

### Implemented Features ✅
- ✅ Object selection (left-click toggle)
- ✅ Arc creation (two-click with [A] tool)
- ✅ Arc preview line (orange, follows cursor)
- ✅ Bipartite validation (P↔T only)
- ✅ Hit testing (find object at position)
- ✅ Preview line geometry (starts at boundary)

### Known Issues
- None currently (fix applied)

### Ready for Testing
All features are now ready for comprehensive testing!

---

## How to Report Issues

If you find any issues during testing, please note:

1. **Exact steps** to reproduce
2. **Expected behavior**
3. **Actual behavior**
4. **Terminal output** (copy/paste)
5. **Visual description** (what you see on screen)

Example:
```
Issue: Preview line doesn't appear

Steps:
1. Created P1
2. Clicked [A] button
3. Clicked P1
4. Moved mouse

Expected: Orange line from P1 to cursor
Actual: No preview line visible

Terminal: "Arc creation: source P1 selected" (correct message)
```

---

## Success Criteria

All tests above should pass with:
- ✓ Correct terminal output
- ✓ Correct visual appearance
- ✓ No errors or warnings
- ✓ Smooth user experience

Ready to test! 🚀
