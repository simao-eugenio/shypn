# SwissKnifePalette Test Bed

**Purpose:** Standalone test application for validating SwissKnifePalette architecture before integration.

## Overview

This test bed allows us to:
- Test sub-palette animations (slide up/down, 200ms timing)
- Test CSS styling and container hierarchy
- Test signal flow (button clicks → signals → console logs)
- Use placeholder tools (simple buttons, no real functionality)
- Run independently (no main app dependencies)

## Structure

```
swissknife_testbed/
├── README.md              # This file
├── test_app.py            # Standalone GTK application
├── placeholder_palette.py # Test palette with placeholders
└── placeholder_tools.py   # Simple placeholder tool buttons
```

## Usage

### Test Edit Mode
```bash
python3 src/shypn/dev/swissknife_testbed/test_app.py --mode edit
```

### Test Simulate Mode
```bash
python3 src/shypn/dev/swissknife_testbed/test_app.py --mode simulate
```

### Test Both Modes
```bash
python3 src/shypn/dev/swissknife_testbed/test_app.py --mode edit
# Then click "Switch to SIMULATE" button in the UI
```

## What to Test

### 1. Animation Timing
- Click category buttons
- Verify sub-palettes slide UP from bottom in 200ms (smooth, natural "rising" effect)
- Click different category
- Verify first palette collapses DOWN (200ms), second slides UP (200ms)
- Total switch time should be 400ms

### 2. Category Toggle
- Click active category button
- Verify sub-palette slides UP and closes
- Category button should become inactive

### 3. Signal Flow
Watch console output for:
```
[SIGNAL] category-selected: 'create'
[ANIMATION] Showing sub-palette: 'create-tools'
[SIGNAL] sub-palette-shown: 'create-tools'
[SIGNAL] tool-activated: 'place'
```

### 4. CSS Styling
- Category buttons should have hover effects
- Active category button should be highlighted
- Tool buttons should have hover effects
- Sub-palette should have gradient background
- All transitions should be smooth (200ms)

### 5. Mode Switching
- Click "Switch to SIMULATE" button
- Old palette should be cleanly removed
- New palette should appear with different categories
- No memory leaks or widget artifacts

## Test Checklist

**Animation Tests:**
- [ ] Sub-palette slides up from bottom (SLIDE_UP, 200ms)
- [ ] Sub-palette collapses down when hidden (200ms)
- [ ] Sequential animations don't overlap (hide then show, 400ms total)
- [ ] Toggle behavior works (click same category closes it)
- [ ] No animation glitches or jumps

**Signal Tests:**
- [ ] `category-selected` emitted when category clicked
- [ ] `sub-palette-shown` emitted after reveal animation
- [ ] `sub-palette-hidden` emitted after hide animation
- [ ] `tool-activated` emitted when tool clicked
- [ ] All signals logged to console

**CSS Tests:**
- [ ] Category buttons styled with hover effects
- [ ] Active category highlighted (green gradient)
- [ ] Tool buttons styled correctly
- [ ] Sub-palette background gradient visible
- [ ] All transitions smooth (200ms)

**Mode Tests:**
- [ ] Edit mode shows 5 categories
- [ ] Simulate mode shows 3 categories
- [ ] Mode switch removes old palette cleanly
- [ ] Mode switch creates new palette correctly
- [ ] No widget leaks

## Expected Behavior

### Edit Mode Categories
1. **Create** → Place (P), Transition (T), Arc (A)
2. **Edit** → Select (S), Lasso (L), Undo (U), Redo (R)
3. **Layout** → Auto, Hierarchical, Force-Directed
4. **Transform** → Parallel, Inhibitor, Read, Reset
5. **View** → Zoom In, Zoom Out, Fit, Center

### Simulate Mode Categories
1. **Control** → Step, Play, Reset, Speed
2. **Visualize** → Tokens, Marking, Chart, Metrics
3. **Analyze** → Export, Statistics

## Console Output Example

```
========================================================
SwissKnifePalette Test Application
========================================================
Initial Mode: EDIT

Instructions:
  1. Click category buttons to reveal sub-palettes
  2. Watch animations (slide up/down)
  3. Click tools to test signal emission
  4. Use mode switch buttons to change modes
  5. Check console for signal logs
========================================================

Creating SwissKnifePalette(mode='edit')
✓ SwissKnifePalette created and attached

```
[SIGNAL] category-selected: 'create'
[ANIMATION] No current sub-palette, showing: 'create-tools'
[ANIMATION] Slide UP animation started (rising from bottom, 200ms)
[ANIMATION] Animation complete
[SIGNAL] sub-palette-shown: 'create-tools'

[SIGNAL] tool-activated: 'place'
[PlaceholderTool] Place activated

[SIGNAL] category-selected: 'edit'
[ANIMATION] Switching from 'create-tools' to 'edit-operations'
[ANIMATION] Hiding 'create-tools' (collapse down, 200ms)
[ANIMATION] Hide animation complete
[SIGNAL] sub-palette-hidden: 'create-tools'
[ANIMATION] Showing 'edit-operations' (slide UP, 200ms)
[ANIMATION] Show animation complete
[SIGNAL] sub-palette-shown: 'edit-operations'
```
```

## Known Limitations (Test Bed)

- Tools are placeholders (no real functionality)
- No actual Petri Net canvas (just gray box)
- No real tool actions (just signal emission)
- No undo/redo stack (just button clicks)
- No real simulation (just placeholder controls)

These are intentional - this is a **test bed for architecture validation only**.

## Success Criteria

✅ Animations are smooth (200ms, no jumps)  
✅ Signals are emitted correctly  
✅ CSS styling works  
✅ Mode switching works  
✅ No memory leaks  
✅ No GTK warnings/errors  
✅ Architecture validated  

**Once all tests pass, we can confidently implement the real SwissKnifePalette.**

## Next Steps

1. Run all tests in this test bed
2. Fix any issues found
3. Optimize animation timing if needed
4. Adjust CSS if needed
5. Once validated, implement real SwissKnifePalette under `src/shypn/dev/swissknife/`
6. Integrate into main app (`model_canvas_loader.py`)

## Troubleshooting

**Problem:** Animations are jerky or slow  
**Solution:** Check GTK version, adjust timing, test on different hardware

**Problem:** Signals not emitted  
**Solution:** Check signal connections in test_app.py

**Problem:** CSS not applied  
**Solution:** Check CSS provider priority, verify class names

**Problem:** Mode switch crashes  
**Solution:** Check widget cleanup in _on_switch_mode()

**Problem:** Memory usage grows  
**Solution:** Check for widget leaks, verify destroy() calls
