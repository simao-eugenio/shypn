# Test 5: Interactive Curve Toggle

**Current Test**: Verify interactive curve/straight transformation via handle

---

## ✅ Previous Tests: ALL PASSED!

- ✅ Test 1: Perimeter connection with border accounting
- ✅ Test 2: Context menu working
- ✅ Test 3: Arc transformation with smart validation
- ✅ Test 4: Weight label display

---

## Test 5: Curve Toggle via Handle

### What to Do:

**Step 1**: **Select the arc**
- Click on the arc to select it
- Arc should highlight (show it's selected)
- Look for a **small square handle** at the arc midpoint

**Step 2**: **Toggle to curved**
- **Click the handle once**
- Arc should become curved (Bezier curve)

**Step 3**: **Toggle back to straight**
- **Click the handle again**
- Arc should return to straight line

**Step 4**: **Adjust curve** (optional)
- Make arc curved again
- **Drag the handle** up/down or side to side
- Curve amount should adjust interactively

---

## What to Check:

### ✅ Handle Visibility:
- Small square handle appears at arc midpoint when selected?
- Handle is easy to see and click?

### ✅ Toggle Functionality:
- First click: Straight → Curved?
- Second click: Curved → Straight?
- No errors or crashes?

### ✅ Drag Adjustment:
- Can drag handle to adjust curve?
- Curve updates smoothly as you drag?
- Curve looks good (smooth Bezier)?

### ✅ Connection Quality:
- Curved arc still connects at object edges?
- No gaps or overlaps even with curve?

---

## Visual Comparison:

**Straight Arc**:
```
Place ━━━━━━━━━━━━━►■ Transition
           □
      Handle at midpoint
```

**Curved Arc** (after clicking handle):
```
Place ━━━╮           
        ╰━━━━━━━━►■ Transition
           □
      Handle (can drag to adjust)
```

---

## How to Report:

**Option 1** - Everything works:
> ✅ "Handle appears, toggle works, can drag to adjust curve, looks good"

**Option 2** - Partial issues:
> ⚠️ "Toggle works but [describe issue: handle hard to see, drag doesn't work, etc.]"

**Option 3** - Handle not visible:
> ❌ "No handle appears when arc is selected"

**Option 4** - Toggle not working:
> ❌ "Handle visible but clicking doesn't change arc"

---

## After This Test:

Remaining tests:
- Test 6: Undo/redo transformation
- Test 7-8: Vertical/diagonal arcs
- Test 9-10: Parallel arcs

---

**Ready?** Select the arc, look for the handle, and try the curve toggle! 🚀

**Tip**: If you don't see a handle, make sure the arc is actually selected (should be highlighted).
