# Zoom and Scaling - Quick Testing Guide

## Testing Procedure

### 1. Start the Application
```bash
cd /home/simao/projetos/shypn
python3 src/shypn.py
```

### 2. Create Test Objects

**Create a few objects to test zoom**:
1. Click **[P]** button → Click canvas to create places (create 3-4)
2. Click **[T]** button → Click canvas to create transitions (create 3-4)
3. Click **[A]** button → Click place → Click transition to create arcs

**Expected**: You should have a small Petri net with several connected objects.

---

## Test Cases

### ✅ Test 1: Basic Zoom In/Out

**Steps**:
1. Position cursor over an object
2. Scroll wheel **UP** (or trackpad pinch out)
3. Observe objects zoom in (get larger)
4. Scroll wheel **DOWN** (or trackpad pinch in)
5. Observe objects zoom out (get smaller)

**Expected Results**:
- ✅ Objects scale smoothly (bigger/smaller)
- ✅ Line widths stay constant (3px borders always)
- ✅ Text stays readable (12pt/14pt font)
- ✅ Object under cursor stays at same screen position

**Common Issues**:
- ❌ Objects jump around → Coordinate transformation bug
- ❌ Lines get thicker/thinner → Missing zoom compensation
- ❌ Text becomes huge/tiny → Font size not compensated

---

### ✅ Test 2: Pointer-Centered Zoom

**Steps**:
1. Position cursor at **canvas center** → Scroll to zoom
2. Position cursor at **top-left corner** → Scroll to zoom
3. Position cursor over **specific place** → Scroll to zoom

**Expected Results**:
- ✅ Zoom always centers on cursor position
- ✅ Object under cursor doesn't move in screen space
- ✅ Rest of canvas scales around cursor

**Test Verification**:
- At center: Canvas expands/contracts from center
- At corner: Corner stays fixed, rest scales away
- Over object: Object stays under cursor, others scale

---

### ✅ Test 3: Extreme Zoom Levels

**Steps**:
1. Zoom in **as far as possible** (10+ scroll ups)
2. Check that zoom stops at maximum (1000%)
3. Zoom out **as far as possible** (10+ scroll downs)
4. Check that zoom stops at minimum (10%)

**Expected Results**:
- ✅ Maximum zoom: Objects very large, lines still 3px
- ✅ Minimum zoom: Objects very small, lines still 3px
- ✅ Zoom clamps at limits (no further zooming)
- ✅ No visual artifacts or rendering errors

---

### ✅ Test 4: Object Scaling

**At 100% Zoom** (default):
- Place radius: ~20px
- Transition size: ~40x20px
- Arc line width: 3px
- Border width: 3px

**At 200% Zoom** (zoom in twice):
- Place radius: ~40px (2x)
- Transition size: ~80x40px (2x)
- Arc line width: **3px** (same!)
- Border width: **3px** (same!)

**At 50% Zoom** (zoom out twice):
- Place radius: ~10px (0.5x)
- Transition size: ~20x10px (0.5x)
- Arc line width: **3px** (same!)
- Border width: **3px** (same!)

**Expected**: Objects scale, lines don't!

---

### ✅ Test 5: Selection at Different Zoom Levels

**Steps**:
1. Zoom to **200%**
2. Deselect tool (click canvas in pan mode)
3. Left-click objects to select them
4. Verify blue highlight appears

**Repeat at**:
- 100% zoom
- 50% zoom
- 25% zoom

**Expected Results**:
- ✅ Selection works at all zoom levels
- ✅ Blue highlight always 3px thick
- ✅ Hit testing accurate (click on object → selects)
- ✅ Click near object but not on it → no selection

---

### ✅ Test 6: Arc Creation with Zoom

**Steps**:
1. Zoom to **200%**
2. Click **[A]** button (arc tool)
3. Click a **place** (source selected)
4. Move mouse → Observe orange preview line
5. Click a **transition** (arc created)

**Expected Results**:
- ✅ Orange preview line appears
- ✅ Preview line is 2px thick (constant width)
- ✅ Preview follows cursor smoothly
- ✅ Arc created successfully
- ✅ Final arc has 3px line width

**Repeat at different zoom levels** (100%, 50%)

---

### ✅ Test 7: Trackpad Smooth Scroll

**Steps** (if you have a trackpad):
1. Use **two-finger scroll** on trackpad
2. Scroll up → Zoom in
3. Scroll down → Zoom out

**Expected Results**:
- ✅ Smooth zoom (not discrete steps)
- ✅ Same pointer-centered behavior
- ✅ No lag or jitter

**Note**: If smooth scroll doesn't work, discrete scroll wheel should still work.

---

### ✅ Test 8: Panning at Different Zoom Levels

**Steps**:
1. Zoom to **200%**
2. **Right-click + drag** to pan
3. Observe canvas moves smoothly

**Repeat at**:
- 100% zoom
- 50% zoom

**Expected Results**:
- ✅ Panning works at all zoom levels
- ✅ Pan speed feels natural
- ✅ No drift or jumping

---

## Troubleshooting

### Issue: Objects Jump When Zooming

**Symptoms**: Object under cursor moves around instead of staying fixed.

**Likely Cause**: Coordinate transformation bug.

**Check**:
```python
# In model_canvas_manager.py:
world_x = (screen_x / self.zoom) - self.pan_x  # Should have MINUS
screen_x = (world_x + self.pan_x) * self.zoom  # Should have PLUS
```

---

### Issue: Lines Get Thicker/Thinner with Zoom

**Symptoms**: Border lines change width when zooming.

**Likely Cause**: Missing zoom compensation in render methods.

**Check**:
```python
# In place.py, transition.py, arc.py:
cr.set_line_width(self.border_width / max(zoom, 1e-6))  # Should have /zoom
```

---

### Issue: Text Becomes Huge/Tiny

**Symptoms**: Labels and token counts scale with zoom.

**Likely Cause**: Font size not compensated.

**Check**:
```python
# In place.py, transition.py, arc.py:
cr.set_font_size(12 / zoom)  # Should have /zoom
```

---

### Issue: Selection Doesn't Work at High Zoom

**Symptoms**: Can't select objects when zoomed in.

**Likely Cause**: Hit testing uses wrong coordinates.

**Check**: Selection code should use `screen_to_world()` to convert click position.

---

## Expected Console Output

**On startup**:
```
GTK3 interface initialized
Model canvas manager created
Drawing area configured
```

**During zoom**:
```
(No console output expected - zoom is silent)
```

**On errors** (shouldn't happen):
```
ERROR: <error message>
Traceback...
```

---

## Performance Notes

### Good Performance
- Zoom in/out: Smooth, no lag
- Panning: Responsive
- Rendering: Instant redraw

### Poor Performance (Possible Issues)
- Lag when zooming → Too many objects or complex rendering
- Stuttering → Grid rendering too heavy
- Memory usage growing → Memory leak in render loop

**Note**: Current implementation should perform well with <100 objects.

---

## Acceptance Criteria

### ✅ PASS: All These Work
- [x] Scroll wheel zooms in/out
- [x] Trackpad smooth scroll works
- [x] Zoom centered at cursor
- [x] Objects scale proportionally
- [x] Line widths stay constant (3px)
- [x] Text stays readable (12pt/14pt)
- [x] Selection works at all zoom levels
- [x] Arc creation works at all zoom levels
- [x] Panning works at all zoom levels
- [x] No visual artifacts

### ❌ FAIL: Any of These Happen
- [ ] Objects jump when zooming
- [ ] Lines change thickness with zoom
- [ ] Text becomes unreadable
- [ ] Selection doesn't work
- [ ] Arc preview disappears
- [ ] Application crashes
- [ ] Memory leaks

---

## Next Steps After Testing

### If Everything Works ✅
1. Mark zoom implementation as complete
2. Move on to next feature
3. Consider optional enhancements (zoom buttons, zoom-to-fit)

### If Issues Found ❌
1. Note specific test case that failed
2. Report symptoms and expected vs actual behavior
3. Check likely causes from troubleshooting section
4. Fix and re-test

---

## Quick Command Summary

```bash
# Start application
cd /home/simao/projetos/shypn
python3 src/shypn.py

# Create objects
[P] → Click  # Place
[T] → Click  # Transition
[A] → Click place → Click transition  # Arc

# Zoom
Scroll wheel up    # Zoom in
Scroll wheel down  # Zoom out
Trackpad pinch     # Smooth zoom

# Pan
Right-click + drag  # Pan canvas

# Select
Deselect tool → Left-click object  # Toggle selection
```

---

## Documentation

- **Analysis**: `doc/ZOOM_AND_SCALING_ANALYSIS.md` (7000+ lines, detailed)
- **Implementation**: `doc/ZOOM_AND_SCALING_IMPLEMENTATION.md` (2000+ lines, summary)
- **This Guide**: `doc/ZOOM_TESTING_GUIDE.md` (quick reference)

Happy testing! 🚀
