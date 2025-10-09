# Graph Layout - Quick Test Guide

**Date**: October 9, 2025  
**Status**: Temporary Context Menu Integration (Testing)

---

## 🧪 How to Test the Graph Layout Algorithms

The graph layout algorithms are now available through the **canvas context menu** for testing purposes.

### Quick Test Steps:

1. **Launch the application**:
   ```bash
   python3 src/shypn.py
   ```

2. **Create some objects**:
   - Add 5-10 places (circles)
   - Add 5-10 transitions (rectangles)
   - Connect them with arcs

3. **Right-click on empty canvas area**

4. **Try the layout options**:
   - **Layout: Auto (Best)** - Automatically selects best algorithm
   - **Layout: Hierarchical** - Top-to-bottom layers
   - **Layout: Force-Directed** - Physics-based natural layout
   - **Layout: Circular** - Arranges in circles (good for cycles)
   - **Layout: Orthogonal** - Grid-aligned with right angles

### Example Test Scenarios:

#### Test 1: Simple Linear Flow (Hierarchical)
1. Create: Place1 → Transition1 → Place2 → Transition2 → Place3
2. Right-click → "Layout: Auto (Best)"
3. **Expected**: Should choose Hierarchical layout, top-to-bottom flow

#### Test 2: Complex Network (Force-Directed)
1. Create many nodes with lots of connections
2. Connect randomly (create a mesh-like structure)
3. Right-click → "Layout: Auto (Best)"
4. **Expected**: Should choose Force-Directed, balanced distribution

#### Test 3: Cyclic Pathway (Circular)
1. Create a cycle: P1 → T1 → P2 → T2 → P3 → T3 → P1
2. Add some branches from the cycle
3. Right-click → "Layout: Circular"
4. **Expected**: Main cycle arranged in circle, branches outside

#### Test 4: Grid-Like Structure (Orthogonal)
1. Create a hierarchical structure
2. Right-click → "Layout: Orthogonal"
3. **Expected**: Nodes snap to grid, clean right-angle layout

---

## 📊 Context Menu Structure

The canvas context menu now includes:

```
Reset Zoom (100%)
Zoom In
Zoom Out
Fit to Window
─────────────────
Grid: Line Style
Grid: Dot Style
Grid: Cross Style
─────────────────
Layout: Auto (Best)          ← NEW
Layout: Hierarchical         ← NEW
Layout: Force-Directed       ← NEW
Layout: Circular             ← NEW
Layout: Orthogonal           ← NEW
─────────────────
Center View
Clear Canvas
```

---

## 🔍 What to Look For

### Auto Layout (Best Algorithm):
- Console message shows which algorithm was selected and why
- Example: `"Applied hierarchical layout - Moved 10 objects - Reason: Graph is acyclic with clear flow"`

### Layout Quality:
- ✅ No overlapping nodes
- ✅ Edges don't cross unnecessarily
- ✅ Clear visual structure
- ✅ Reasonable spacing between nodes

### Performance:
- Small graphs (< 20 nodes): Instant (< 0.1s)
- Medium graphs (20-50 nodes): Fast (< 0.5s)
- Large graphs (50-100 nodes): Acceptable (< 2s)

---

## 💬 Console Output

The layout system prints messages to the console:

```
[Graph Layout] Applied hierarchical layout
[Graph Layout] Moved 10 objects
[Graph Layout] Reason: Graph is acyclic with clear directional flow (15 nodes, 14 edges). Hierarchical layout emphasizes this flow.
```

Watch the console to see:
- Which algorithm was selected
- How many objects were moved
- Why that algorithm was chosen (for Auto mode)

---

## 🐛 Known Limitations (Temporary Implementation)

Since this is a temporary testing integration:

1. **No Undo**: Layout changes cannot be undone yet
   - *Solution*: Save your file before testing layouts

2. **Console Messages Only**: No UI feedback dialogs
   - *Solution*: Watch the terminal/console for messages

3. **No Parameter Customization**: Uses default spacing
   - *Solution*: Later UI will have sliders for spacing, iterations, etc.

4. **No Preview**: Applied immediately without preview
   - *Solution*: Later UI will have preview mode

5. **No Layout Persistence**: Layout settings not saved
   - *Solution*: Future feature

---

## 🔧 Troubleshooting

### Problem: Menu items not showing
**Solution**: Make sure you right-click on **empty canvas area**, not on an object

### Problem: "No objects to layout"
**Solution**: Create at least 2 objects (places or transitions) before applying layout

### Problem: Objects disappear after layout
**Solution**: 
- Use "Fit to Window" to see all objects
- Use "Center View" to reset view position

### Problem: Layout looks bad
**Solution**: Try different algorithms - what works depends on your graph structure:
- Linear flow → Hierarchical
- Complex mesh → Force-Directed
- Cycles → Circular
- Want grid → Orthogonal

---

## 🎯 Import KEGG and Test

The best test is with real biological pathways:

1. **File → Import KEGG Pathway**
2. Enter pathway ID (e.g., "hsa00010" for glycolysis)
3. Import with "Include Cofactors" unchecked
4. Right-click canvas → "Layout: Auto (Best)"
5. **Expected**: Beautiful hierarchical layout of the metabolic pathway

---

## 🚀 Next Steps

After testing proves the algorithms work:

1. **Create dedicated Layout Palette** (multi-tools Swiss Army knife)
2. **Add UI controls** (parameter sliders, preview mode)
3. **Integrate undo/redo** for layout operations
4. **Add toolbar button** for quick access
5. **Save layout preferences** with document
6. **Add keyboard shortcuts** (e.g., Ctrl+L for auto-layout)

---

## 📝 Feedback

While testing, note:
- Which algorithm worked best for your use case?
- Were the default parameters (spacing, etc.) good?
- How was the performance on your graphs?
- Any unexpected behavior?

This feedback will guide the final UI design!

---

**Temporary Integration Complete** ✅

Right-click the canvas and try the layout algorithms! The console will show you what's happening.
