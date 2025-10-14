# Lasso Selection - Quick Reference

## What's New

The lasso selection system is now fully functional with complete keyboard shortcut support and drag capabilities.

## How to Use

### 1. Select Objects with Lasso

1. Click the **Lasso button** (🔵) in the Edit palette
2. **Click and drag** to draw a freeform path around objects
3. **Release mouse** - objects inside the polygon are selected
4. Press **Escape** to cancel while drawing

### 2. Keyboard Shortcuts (All Standard)

| Shortcut | Action | Works On |
|----------|--------|----------|
| **Ctrl+X** | Cut | Selected objects |
| **Ctrl+C** | Copy | Selected objects |
| **Ctrl+V** | Paste | Clipboard (30px offset) |
| **Delete** | Delete | Selected objects |
| **Ctrl+Z** | Undo | Last operation |
| **Ctrl+Shift+Z** or **Ctrl+Y** | Redo | Last undone operation |

### 3. Drag Selected Objects

1. Select objects with lasso (or rectangle, or Ctrl+Click)
2. **Click and drag any selected object**
3. **All selected objects move together** as a group
4. Release to complete - recorded in undo history

## Key Features

✅ **Lasso completes automatically** - No need to click finish  
✅ **Smart clipboard** - Only copies arcs when both endpoints selected  
✅ **Unique names** - Pasted objects get new names (Place1 → Place2)  
✅ **Group drag** - All selected objects move together  
✅ **Full undo/redo** - All operations reversible  
✅ **Preserves geometry** - Curved arcs keep their shape  

## Example Workflow

```
1. Draw lasso around 3 places and 2 transitions
2. Press Ctrl+C to copy
3. Press Ctrl+V to paste (appears 30px offset)
4. Drag the pasted group to new position
5. Press Ctrl+Z twice to undo (move + paste)
6. Press Ctrl+Y twice to redo
```

## Tips

- **Escape** cancels lasso while drawing
- **Ctrl+Click** adds individual objects to selection
- **Shift+Drag** for rectangle selection (alternative to lasso)
- Objects must have **center inside** lasso polygon to be selected
- Arcs automatically follow when dragging connected places/transitions

## Technical Details

See **`doc/LASSO_SELECTION_COMPLETE.md`** for full documentation including:
- Architecture and implementation details
- Testing scenarios
- Performance considerations
- Future enhancement ideas

---

**Status**: ✅ Complete and ready to use  
**Date**: October 12, 2025
