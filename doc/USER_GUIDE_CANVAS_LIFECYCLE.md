# Canvas Lifecycle Features - User Guide

**Version:** 1.0  
**Date:** 2025-01-05  
**Target Users:** SHYPN Application Users

## Overview

SHYPN now includes a powerful canvas lifecycle system that enables you to work with multiple Petri net models simultaneously, each with independent ID sequences and proper resource management.

## Key Features

### 1. Multiple Independent Canvases

**What it means:**
- Open multiple Petri net models in separate tabs
- Each canvas maintains its own ID sequence (P1, P2, ... T1, T2, ... A1, A2, ...)
- No ID conflicts between canvases
- Switch between canvases freely

**How to use:**
1. **File → New** (Ctrl+N) - Create a new canvas
2. **File → Open** (Ctrl+O) - Open an existing file in a new canvas
3. **Click tabs** - Switch between open canvases
4. **Close tab (X button)** - Close a canvas

**Example:**
```
Canvas 1 (glycolysis.xml):  P1, P2, P3, T1, T2, A1, A2, ...
Canvas 2 (citric_acid.xml): P1, P2, P3, T1, T2, A1, A2, ...  ← Independent!
Canvas 3 (new_model.shy):   P1, P2, P3, T1, T2, A1, A2, ...  ← Independent!
```

---

### 2. Independent ID Sequences

**What it means:**
- Each canvas has its own place, transition, and arc counters
- IDs always start from 1 in each new canvas (P1, T1, A1)
- Adding elements in one canvas doesn't affect others
- IDs remain consistent when switching between canvases

**Benefits:**
- ✅ No confusing ID jumps (no more P1, P2, P50, P51...)
- ✅ Clean, predictable IDs in every canvas
- ✅ Import multiple models without ID collisions
- ✅ Each model stays self-contained

**Example Workflow:**
1. Open Canvas 1, create places P1-P5
2. Open Canvas 2, create places P1-P3 (starts fresh at P1)
3. Switch back to Canvas 1, add place P6 (continues from P5)
4. Switch to Canvas 2, add place P4 (continues from P3)

---

### 3. Canvas Reset

**What it means:**
- Clear all elements from current canvas
- Reset ID counters back to 1
- Keeps the canvas tab open (doesn't create new tab)
- Useful for starting over on the same canvas

**How to use:**
- **File → Reset Canvas** (Ctrl+Shift+N)
- Confirmation dialog appears with:
  - Canvas name/ID
  - Number of elements to be deleted
  - Warning: "This action cannot be undone"
- Click **Yes** to reset or **No** to cancel

**When to use:**
- Want to start fresh without opening a new tab
- Need to clear a canvas for a new model
- Made mistakes and want to restart
- Testing or experimenting with models

**Warning:** Reset is permanent! Save your work first if needed.

---

### 4. Clean Canvas Closing

**What it means:**
- Closing a canvas properly cleans up all resources
- Other canvases remain unaffected
- No memory leaks or leftover data
- Safe to close any canvas at any time

**How to use:**
- Click the **X** button on the tab
- Or use **File → Close** (if available)
- Canvas is immediately removed
- Other canvases continue working normally

---

## Common Workflows

### Workflow 1: Working with Multiple Models

**Scenario:** Analyzing three different pathways side-by-side

1. **File → Open** → Select `pathway1.xml` (opens in Canvas 1)
2. **File → Open** → Select `pathway2.xml` (opens in Canvas 2)
3. **File → Open** → Select `pathway3.xml` (opens in Canvas 3)
4. Click tabs to switch between pathways
5. Each pathway has clean, independent IDs
6. Compare and analyze without confusion

---

### Workflow 2: Iterative Model Development

**Scenario:** Experimenting with different model variations

1. **File → New** → Start new model (Canvas 1)
2. Build initial model (P1-P5, T1-T3, A1-A7)
3. Test/simulate the model
4. Want to try variation? **File → New** (Canvas 2)
5. Build alternative version (independent IDs)
6. Compare both versions side-by-side
7. Save the one you like, close the other

---

### Workflow 3: Import and Extend

**Scenario:** Importing KEGG pathway and adding custom elements

1. **File → Open** → Select KEGG pathway (imports P1-P20, T1-T10)
2. Note: IDs are P1-P20 (clean sequence)
3. Switch to Edit mode
4. Add custom place → Gets P21 (continues sequence)
5. Add custom transition → Gets T11 (continues sequence)
6. **File → Save** → Save extended model
7. IDs remain clean and sequential

---

### Workflow 4: Fresh Start on Same Canvas

**Scenario:** Want to restart without opening new tab

1. Working on Canvas 1 with model
2. Made mistakes or want to start over
3. **File → Reset Canvas** (Ctrl+Shift+N)
4. Confirmation dialog shows element count
5. Click **Yes** → Canvas clears
6. Start fresh with P1, T1, A1 again
7. Same tab, new beginning

---

## Keyboard Shortcuts

| Action | Shortcut | Description |
|--------|----------|-------------|
| **New Canvas** | Ctrl+N | Create new empty canvas |
| **Open File** | Ctrl+O | Open file in new canvas |
| **Save** | Ctrl+S | Save current canvas |
| **Save As** | Ctrl+Shift+S | Save with new name |
| **Reset Canvas** | Ctrl+Shift+N | Clear and reset current canvas |
| **Close Tab** | Ctrl+W | Close current canvas |
| **Quit** | Ctrl+Q | Exit application |

---

## Tips & Best Practices

### ✅ DO:
- Open multiple canvases to compare models
- Use Reset Canvas for quick experimentation
- Check canvas name/ID before resetting
- Save work before resetting
- Close unused canvases to free resources

### ❌ DON'T:
- Don't worry about ID conflicts between canvases
- Don't manually track IDs - system handles it
- Don't expect IDs to match between canvases
- Don't reset without confirming element count

---

## Visual Indicators

### Tab Labels
- Each canvas shows its filename or "Untitled"
- Modified canvases show indicator (e.g., *)
- Click tab to switch to that canvas

### Canvas Info (Future)
Status bar will show:
- Current canvas ID
- Next IDs: P: 6, T: 3, A: 8
- Element count: 15 elements

---

## Troubleshooting

### Problem: "IDs jumping numbers"
**Solution:** Each canvas has independent IDs. This is normal and expected.

### Problem: "Can't see my other model"
**Solution:** Click the tabs at the top to switch between canvases.

### Problem: "Reset doesn't work"
**Solution:** Make sure a canvas is open. Check console for error messages.

### Problem: "Memory issues with many canvases"
**Solution:** Close unused canvases. Each canvas uses memory.

---

## Technical Details (For Advanced Users)

### ID Scoping
- Each canvas has a unique scope: `canvas_<id>`
- IDs are tracked per scope: `{canvas_1: {place: 5, transition: 3, arc: 8}, ...}`
- Switching canvases changes active scope
- ID generation pulls from active scope's counters

### Resource Management
- Creating canvas: Allocates ID scope, initializes components
- Switching canvas: Changes active scope, updates UI
- Closing canvas: Frees ID scope, cleans up resources
- Resetting canvas: Clears elements, resets scope counters

### Backward Compatibility
- Old files load correctly
- Single canvas mode works as before
- Legacy code continues working
- No breaking changes

---

## FAQ

**Q: Do I need to do anything special for multiple canvases?**  
A: No! Just use File → New or File → Open normally. The system handles everything automatically.

**Q: Will my old files work?**  
A: Yes! Old files load perfectly. They get fresh IDs when imported.

**Q: Can I copy elements between canvases?**  
A: Not yet. This feature may be added in the future.

**Q: What happens to IDs when I save?**  
A: IDs are saved with the file. When you open it later, those IDs are preserved.

**Q: How many canvases can I open?**  
A: Practically unlimited, but performance depends on your system. 10-20 is reasonable.

**Q: Can I rename canvas tabs?**  
A: Tabs show the filename. Use File → Save As to change the name.

---

## Console Messages

When using canvas features, you may see these messages:

**Lifecycle System:**
```
[GLOBAL-SYNC] ✓ Canvas lifecycle system enabled
[GLOBAL-SYNC] ✓ IDManager lifecycle scoping enabled
```

**Canvas Operations:**
```
[LIFECYCLE] Creating canvas <id> (file=<path>)
[LIFECYCLE] ✓ Canvas <id> destroyed
[RESET] ✓ Canvas reset via lifecycle system
```

**Errors (should NOT appear):**
```
[LIFECYCLE] ⚠️  Failed to ...
[RESET] ⚠️  Lifecycle reset failed
```

If you see error messages, please report them!

---

## Getting Help

- **User Manual:** See full documentation for detailed usage
- **Console:** Check terminal output for diagnostic messages
- **GitHub Issues:** Report bugs or request features
- **Test Protocol:** See MANUAL_TEST_PROTOCOL_IMPORTS.md for testing

---

## Summary

The canvas lifecycle system makes SHYPN more powerful and easier to use:

✅ **Multiple canvases** - Work with many models simultaneously  
✅ **Independent IDs** - No conflicts, clean sequences  
✅ **Reset functionality** - Quick fresh starts  
✅ **Clean cleanup** - Proper resource management  
✅ **Backward compatible** - Old files work perfectly  

Just use File → New and File → Open as you normally would. The system takes care of the rest!

---

**Enjoy your enhanced SHYPN experience! 🚀**
