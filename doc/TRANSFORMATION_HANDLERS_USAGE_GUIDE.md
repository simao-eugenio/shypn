# Transformation Handlers - Quick Start Guide

## 🎯 How to Use Interactive Resize

### Step 1: Enter Edit Mode
**Double-click** any Place or Transition to enter edit mode.

```
Normal Mode (single click):       Edit Mode (double-click):
                                  
    ┌─────────┐                      ┌─────────────┐
    │         │                      │ ■     ■     ■
    │  Place  │          →           │ ■   Place   ■
    │         │                      │ ■     ■     ■
    └─────────┘                      └─────────────┘
                                     8 handles appear!
```

### Step 2: Resize by Dragging Handles

#### Places (Circular Objects)
All handles have the same effect - they change the radius uniformly:

```
Before resize:                After dragging handle:
    
     ■   ■   ■                       ■     ■     ■
   ■    ●    ■                     ■       ●       ■
     ■   ■   ■        →              ■     ■     ■
   
  radius = 20                      radius = 30
```

#### Transitions (Rectangular Objects)

**Edge Handles** (N, E, S, W) - Resize ONE dimension:

```
Drag East handle →               Drag North handle ↑

    ■─────────■                      ■─────────■
    │         │                      │         │
■───┼────T────┼───■      OR      ■───┼────T────┼───■
    │         │                      │         │
    ■─────────■                      ■─────────■
    
  Width increases                  Height decreases
  Height unchanged                 Width unchanged
```

**Corner Handles** (NE, SE, SW, NW) - Resize BOTH dimensions:

```
Drag Southeast handle ↘

    ■─────────■                      ■─────────────■
    │         │                      │             │
    │    T    │          →           │      T      │
    │         │                      │             │
    ■─────────■                      │             │
                                     ■─────────────■
                                     
    Both width AND height increase
```

### Step 3: Commit or Cancel

**Option A - Commit the change:**
- Release the mouse button ✓
- The new size is saved

**Option B - Cancel the change:**
- Press **ESC** key 🚫
- Object returns to original size

---

## 🎨 Visual Feedback

### Handle Types
```
Corner Handles (resize both dimensions):
    ■ NW        N        NE ■
    
    W          obj           E
    
    ■ SW        S        SE ■

Edge Handles (resize one dimension):
    Only N/S for vertical
    Only E/W for horizontal
```

### Selection States
```
┌──────────────────────────────────────┐
│ NORMAL MODE (single click)           │
├──────────────────────────────────────┤
│  • Blue highlight around object      │
│  • No handles                        │
│  • Can drag object                   │
│  • Can create arcs                   │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ EDIT MODE (double-click)             │
├──────────────────────────────────────┤
│  • Blue highlight around object      │
│  • Dashed bounding box              │
│  • 8 resize handles (■)             │
│  • Can resize by dragging handles   │
│  • Press ESC to exit edit mode      │
└──────────────────────────────────────┘
```

---

## ⚙️ Size Constraints

The system enforces minimum and maximum sizes:

### Places
```
Minimum radius: 10 units  ⚫ (smallest)
Maximum radius: 100 units ⭕ (largest)
```

### Transitions
```
Width:  20 units (min)  to  200 units (max)
Height: 10 units (min)  to  100 units (max)

Smallest: ┌─┐    Largest: ┌────────────┐
          │ │             │            │
          └─┘             │            │
                          └────────────┘
```

If you try to resize beyond these limits, the object will stop at the boundary.

---

## 🎹 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Double-click** | Enter edit mode (show handles) |
| **ESC** | Cancel transformation / Exit edit mode |
| **Mouse drag** | Resize object (when handle grabbed) |
| **Single-click** | Exit edit mode (return to normal) |

---

## 📋 Common Workflows

### Workflow 1: Make a Place Larger
1. Double-click the Place → Edit mode
2. Drag any handle outward → Radius increases
3. Release mouse → Done ✓

### Workflow 2: Make a Transition Wider
1. Double-click the Transition → Edit mode
2. Drag **East** or **West** handle → Width changes
3. Release mouse → Done ✓

### Workflow 3: Make a Transition Taller and Wider
1. Double-click the Transition → Edit mode
2. Drag a **corner handle** (NE, SE, SW, or NW) → Both dimensions change
3. Release mouse → Done ✓

### Workflow 4: Try Different Sizes
1. Double-click object → Edit mode
2. Drag handle to resize → See preview
3. Don't like it? Press **ESC** → Returns to original size
4. Try again with different handle → Different effect
5. Happy with result? Release mouse → Saved ✓

---

## 🐛 Troubleshooting

### "I double-clicked but no handles appear"
- Make sure you're clicking directly on the object
- The object should show a blue highlight first (single-click)
- Then double-click while it's highlighted

### "I can't drag the handle"
- Make sure you're clicking directly on the handle (small square)
- Handles are 8×8 pixels, so click precisely in the center

### "The object won't shrink/grow anymore"
- You've hit the size constraints (min/max limits)
- This is intentional to prevent objects from becoming too small or too large

### "I want to cancel but already released the mouse"
- Unfortunately, once released, the change is committed
- Future versions will add undo/redo support
- For now, resize again to adjust, or reload the file without saving

---

## 🚀 Pro Tips

1. **Uniform Place Sizing**: All handles on a Place do the same thing, so use whichever is most convenient

2. **Precise Transition Sizing**: 
   - Need to adjust width only? Use E or W handles
   - Need to adjust height only? Use N or S handles
   - Need both? Use corner handles

3. **Quick Exit**: Single-click anywhere (not on the object) to exit edit mode quickly

4. **Preview Before Committing**: Drag the handle around to see the preview, then press ESC if you don't like it

5. **Multiple Attempts**: You can enter edit mode multiple times - don't worry about getting it perfect on the first try!

---

## 🎓 Technical Details (for developers)

### Handle Names
```
Compass-based naming:
    nw ─── n ─── ne
    │             │
    w     obj     e
    │             │
    sw ─── s ─── se
```

### Handle Positions
- **Places**: Handles at radius distance from center, at 8 compass points (45° apart)
- **Transitions**: Handles at corners and edge midpoints of bounding box

### Transformation Process
1. **Detection**: HandleDetector calculates handle positions
2. **Hit Test**: Check if click is within 8×8 pixel handle area
3. **Start**: ResizeHandler stores original geometry
4. **Update**: Calculate delta from start position, apply to object
5. **End/Cancel**: Commit changes or restore original

### File Locations
- Core logic: `src/shypn/edit/transformation/`
- Integration: `src/shypn/edit/object_editing_transforms.py`
- Event handling: `src/shypn/helpers/model_canvas_loader.py`

---

**Implementation Status**: ✅ Phase 1 Complete  
**Next Steps**: Visual preview, cursor changes, undo/redo, rotation support
