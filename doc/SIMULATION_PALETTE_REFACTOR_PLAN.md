# Simulation Palette Refactor Plan - [S] Button Transformation

**Date**: October 7, 2025
**Status**: Planning Phase
**Objective**: Refactor [S] simulation button to match [E] edit button style (purple container with [ ][S][ ] layout)

---

## Overview

Transform the current standalone [S] button (36×36px, red gradient) into a purple container with three-position layout [ ][S][ ], matching the successful [E] edit button refactor.

---

## Current State Analysis

### Existing Structure
```
Current [S] Button:
┌─────┐
│  S  │  ← 36×36px red button
└─────┘
```

**Files**:
- `ui/simulate/simulate_palette.ui` - Contains simple [S] toggle button
- `src/shypn/helpers/simulate_palette_loader.py` - Loads UI, applies red gradient CSS

**Current CSS**:
- Background: Red gradient (#e74c3c → #c0392b)
- Border: 2px solid #a93226
- Size: 36×36px
- Font: 16px bold, white color
- Shadow: Multi-layer for depth effect

**Current Behavior**:
- Toggle button controls simulation tools palette visibility
- Red color indicates "simulation mode" (distinct from edit's purple)
- Located in mode palette next to [E] button
- Emits 'tools-toggled' signal when clicked

---

## Target State (Matching [E] Edit Button)

### Target Structure
```
New [S] Button Container:
┌─────────────────────────────────┐
│  [ ]        [S]        [ ]      │  ← Purple container with 3 positions
└─────────────────────────────────┘
    ↑          ↑          ↑
  Left      Center      Right
  Placeholder  Button   Placeholder
```

**Dimensions**:
- Container width: 100px (same as [E] edit palette)
- Container height: 38px (28px button + 2×3px padding + 2×2px border)
- Button size: 28×28px (same as [E] button)
- Spacing: 8px between buttons/placeholders
- Padding: 3px inside container
- Border: 2px solid #5568d3

**Layout**:
```
simulate_palette_container (GtkBox vertical)
  └─ simulate_control (GtkBox horizontal) [NEW INNER BOX]
       ├─ left_placeholder (GtkBox) [NEW]
       │    - 28×28px invisible box
       ├─ simulate_toggle_button [EXISTING - RESIZED]
       │    - 28×28px button with [S]
       └─ right_placeholder (GtkBox) [NEW]
            - 28×28px invisible box
```

---

## Design Specifications

### Container CSS (Purple Gradient)
```css
.simulate-palette-control {
    /* Purple gradient matching edit/mode/zoom */
    background: linear-gradient(to bottom, #667eea 0%, #764ba2 100%);
    border: 2px solid #5568d3;
    border-radius: 8px;
    padding: 3px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),
                0 2px 4px rgba(0, 0, 0, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.simulate-palette-control:hover {
    border-color: #5568d3;
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.45),
                0 3px 6px rgba(0, 0, 0, 0.35),
                0 0 12px rgba(102, 126, 234, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.3);
}
```

### Button CSS (White Gradient)
```css
.simulate-button {
    /* White gradient button (matches edit button style) */
    background: linear-gradient(to bottom, #ffffff 0%, #f0f0f5 100%);
    border: 1px solid #b0b0b0;
    border-radius: 4px;
    font-size: 14px;
    font-weight: bold;
    color: #333333;
    min-width: 28px;
    min-height: 28px;
    padding: 0;
    margin: 0;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.simulate-button:hover {
    background: linear-gradient(to bottom, #f8f8f8 0%, #e8e8ee 100%);
    border-color: #999999;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.25),
                0 0 4px rgba(102, 126, 234, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.simulate-button:active,
.simulate-button:checked {
    /* Red/orange active state (indicates simulation mode) */
    background: linear-gradient(to bottom, #e74c3c 0%, #c0392b 100%);
    border-color: #a93226;
    color: white;
    box-shadow: inset 0 2px 3px rgba(0, 0, 0, 0.3),
                0 0 6px rgba(231, 76, 60, 0.4);
}
```

**Key Design Decisions**:
1. **Container**: Purple gradient (matches edit/mode/zoom for consistency)
2. **Button inactive**: White gradient (visible against purple, professional look)
3. **Button active**: Red gradient (indicates simulation mode is active)
4. **Size**: 28×28px button in 100px container (matches edit palette exactly)

---

## Implementation Phases

### Phase 1: UI File Restructuring ✅
**File**: `ui/simulate/simulate_palette.ui`

**Tasks**:
1. Add inner `simulate_control` GtkBox (horizontal orientation)
2. Add `left_placeholder` GtkBox (28×28px, invisible)
3. Modify `simulate_toggle_button` (resize to 28×28px)
4. Add `right_placeholder` GtkBox (28×28px, invisible)
5. Update container properties (remove direct button styling)
6. Add `.simulate-palette-control` style class to inner box

**Expected Result**:
```xml
<object class="GtkBox" id="simulate_palette_container">
  <child>
    <object class="GtkBox" id="simulate_control">
      <property name="orientation">horizontal</property>
      <property name="spacing">8</property>
      <style>
        <class name="simulate-palette-control"/>
      </style>
      
      <child>
        <object class="GtkBox" id="left_placeholder">
          <property name="width-request">28</property>
          <property name="height-request">28</property>
        </object>
      </child>
      
      <child>
        <object class="GtkToggleButton" id="simulate_toggle_button">
          <property name="label">S</property>
          <property name="width-request">28</property>
          <property name="height-request">28</property>
          <style>
            <class name="simulate-button"/>
          </style>
        </object>
      </child>
      
      <child>
        <object class="GtkBox" id="right_placeholder">
          <property name="width-request">28</property>
          <property name="height-request">28</property>
        </object>
      </child>
    </object>
  </child>
</object>
```

---

### Phase 2: Loader Refactoring ✅
**File**: `src/shypn/helpers/simulate_palette_loader.py`

**Tasks**:
1. Add widget references for new elements:
   ```python
   self.simulate_control = None  # Inner box
   self.left_placeholder = None
   self.right_placeholder = None
   ```

2. Update `_load_ui()` to get new widget references
3. Refactor `_apply_styling()` with new CSS:
   - Container CSS (`.simulate-palette-control`)
   - Button CSS (`.simulate-button` - updated to white gradient)
4. Optional: Add dynamic sizing based on font metrics (like edit palette)
5. Update docstrings and comments

**Key Changes**:
```python
def _apply_styling(self):
    """Apply purple container + white button styling."""
    css = """
    .simulate-palette-control {
        background: linear-gradient(to bottom, #667eea 0%, #764ba2 100%);
        border: 2px solid #5568d3;
        border-radius: 8px;
        padding: 3px;
        ...
    }
    
    .simulate-button {
        background: linear-gradient(to bottom, #ffffff 0%, #f0f0f5 100%);
        ...
    }
    
    .simulate-button:checked {
        background: linear-gradient(to bottom, #e74c3c 0%, #c0392b 100%);
        color: white;
        ...
    }
    """
```

---

### Phase 3: Positioning Adjustments ✅
**File**: `src/shypn/helpers/model_canvas_loader.py`

**Current Mode Palette Positioning**:
- Both [E] and [S] buttons in same mode palette container
- Located at bottom-left of canvas
- Container margin_bottom: 24px

**Required Changes**:
1. The mode palette container now holds two 100px-wide palette controls
2. Update mode palette positioning if needed (container width increased)
3. Verify spacing between [E] and [S] containers
4. Test visual alignment with edit palette above

**Expected Layout**:
```
Bottom-left corner:
┌───────────────────┐  ┌───────────────────┐
│  [ ] [E] [ ]      │  │  [ ] [S] [ ]      │
└───────────────────┘  └───────────────────┘
   Edit palette          Simulate palette
   (100px wide)          (100px wide)
```

**Positioning Code** (likely in mode_palette_loader.py or model_canvas_loader.py):
- Horizontal spacing: 12px between [E] and [S]
- Vertical: margin_bottom 24px from canvas edge
- Alignment: left side of canvas

---

### Phase 4: Integration Testing ✅
**Verification checklist**:

1. **Visual Appearance**:
   - [ ] [S] button in purple container with [ ][S][ ] layout
   - [ ] Container matches [E] edit palette exactly (100px × 38px)
   - [ ] White button visible against purple background
   - [ ] Active state shows red gradient (simulation mode active)
   - [ ] Hover effects work on container and button
   - [ ] Multi-layer shadows provide depth

2. **Positioning**:
   - [ ] [S] container aligned with [E] container horizontally
   - [ ] 12px spacing between containers
   - [ ] Both centered/aligned at bottom-left
   - [ ] No overlap with other UI elements

3. **Functionality**:
   - [ ] [S] button toggles simulation tools palette
   - [ ] Toggle state (checked/unchecked) works correctly
   - [ ] 'tools-toggled' signal emitted properly
   - [ ] Simulation tools show/hide with animation
   - [ ] Mode switching (Edit ↔ Simulate) still works

4. **Consistency**:
   - [ ] Purple container matches edit/mode/zoom/tools/operations palettes
   - [ ] Button size (28×28px) matches edit palette
   - [ ] Font size matches other palette buttons
   - [ ] Border/shadow style consistent across all palettes

---

### Phase 5: Documentation & Cleanup ✅
**Tasks**:
1. Create `SIMULATION_PALETTE_REFACTOR_COMPLETE.md` with:
   - Before/after screenshots description
   - CSS specifications
   - Layout diagrams
   - Testing results
   - Design rationale

2. Update existing documentation:
   - Reference new [S] button design
   - Update mode palette description
   - Note consistency across all 6 palettes now

3. Code cleanup:
   - Remove old CSS for red gradient standalone button
   - Update comments to reflect [ ][S][ ] layout
   - Ensure no dead code remains

---

## Technical Considerations

### Sizing Strategy
**Option A**: Fixed size (like current implementation)
- Container: 100px × 38px (hardcoded)
- Button: 28px × 28px (hardcoded)
- Simple, matches edit palette exactly

**Option B**: Dynamic sizing (like edit palette has option for)
- Calculate based on font metrics (Pango layout)
- Scale to 1.3× 'W' character height
- More complex but flexible

**Recommendation**: Use **Option A** (fixed size) for consistency with edit palette's current fixed implementation.

---

### Color Philosophy

**Container Color**: Purple (#667eea → #764ba2)
- **Rationale**: All palettes should have same container color for visual consistency
- Creates unified "control zone" appearance
- Professional, modern look

**Button Inactive**: White (#ffffff → #f0f0f5)
- **Rationale**: High contrast against purple background
- Clear clickable element
- Matches edit palette button style

**Button Active**: Red/Orange (#e74c3c → #c0392b)
- **Rationale**: Red indicates "simulation running" or "simulation mode active"
- Distinct from edit mode (no active color on [E])
- Maintains original simulation identity while updating container

**Result**: Purple container + white button + red active state = Best of both worlds!

---

### Placeholder Purpose

The [ ][S][ ] layout with placeholders serves multiple purposes:

1. **Visual Balance**: Centered [S] button looks intentional, not "lonely"
2. **Future Expansion**: Placeholders reserve space for potential future buttons
3. **Consistency**: Matches [E] edit palette design exactly
4. **Width Standardization**: All palette controls are 100px wide
5. **Professional Look**: Symmetric layout appears polished

**Note**: Placeholders are invisible (no background/border) but occupy space.

---

## Dependencies & Interactions

### Files to Modify
1. `ui/simulate/simulate_palette.ui` - Add [ ][S][ ] structure
2. `src/shypn/helpers/simulate_palette_loader.py` - Update loader + CSS
3. `src/shypn/helpers/mode_palette_loader.py` - May need positioning updates (verify)
4. `src/shypn/helpers/model_canvas_loader.py` - May need layout adjustments (verify)

### Files to Review (no changes likely)
- `ui/simulate/simulate_tools_palette.ui` - Tools palette (unchanged)
- `src/shypn/helpers/simulate_tools_palette_loader.py` - Tools palette loader (unchanged)
- `ui/simulate/simulate_palette_controller.py` - Controller logic (unchanged)

### Potential Side Effects
1. **Mode palette width increase**: Container now wider (2 × 100px + spacing)
2. **Visual hierarchy shift**: [S] button no longer stands out with red (purple container)
3. **Active state visibility**: Red active state now on button, not container
4. **Layout reflow**: Wider mode palette might affect positioning

**Mitigation**: Test in running application, adjust positioning as needed.

---

## Rollback Plan

If issues arise, revert changes:

1. **Restore `simulate_palette.ui`**:
   ```bash
   git checkout HEAD -- ui/simulate/simulate_palette.ui
   ```

2. **Restore `simulate_palette_loader.py`**:
   ```bash
   git checkout HEAD -- src/shypn/helpers/simulate_palette_loader.py
   ```

3. **Restore positioning files** (if modified):
   ```bash
   git checkout HEAD -- src/shypn/helpers/model_canvas_loader.py
   git checkout HEAD -- src/shypn/helpers/mode_palette_loader.py
   ```

**Backup Strategy**: Create feature branch before starting:
```bash
git checkout -b feature/simulate-palette-refactor
```

---

## Success Criteria

### Must Have ✓
- [S] button in purple container with [ ][S][ ] layout
- Container matches [E] edit palette (100px × 38px)
- Button size matches edit palette (28×28px)
- White button visible against purple background
- Red active state when simulation mode active
- All functionality preserved (toggle tools palette)
- No visual glitches or layout issues

### Nice to Have ✓
- Smooth hover effects on container and button
- Multi-layer shadows for depth
- Active state glow effect (red halo)
- Dynamic sizing option (future enhancement)
- Consistent spacing with edit palette

### Performance
- No performance degradation
- CSS applies without flicker
- Animations remain smooth (revealer)

---

## Comparison: Before vs After

### Before (Current State)
```
Mode Palette (bottom-left):
┌─────┐ ┌─────┐
│  E  │ │  S  │  ← Two standalone 36×36px buttons
└─────┘ └─────┘
Purple   Red
```

**Characteristics**:
- [E]: Purple gradient, 36×36px
- [S]: Red gradient, 36×36px
- Different colors indicate different modes
- Simple, functional but inconsistent

### After (Target State)
```
Mode Palette (bottom-left):
┌─────────────────────────────────┐  ┌─────────────────────────────────┐
│     [ ]    [E]    [ ]           │  │     [ ]    [S]    [ ]           │
└─────────────────────────────────┘  └─────────────────────────────────┘
Purple container (100px × 38px)       Purple container (100px × 38px)

Inactive: White buttons on purple
Active:   [E] stays white (edit has no "active" state)
          [S] turns red (simulation mode active)
```

**Characteristics**:
- Both [E] and [S]: Purple containers (consistent!)
- Both: 100px × 38px containers with [ ][X][ ] layout
- Both: 28×28px white buttons (inactive)
- [S] only: Red button when active (simulation running)
- Professional, unified appearance
- Future-proof (placeholders for expansion)

---

## Timeline Estimate

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1 | UI file restructuring | 10 minutes |
| Phase 2 | Loader refactoring | 15 minutes |
| Phase 3 | Positioning adjustments | 10 minutes |
| Phase 4 | Integration testing | 15 minutes |
| Phase 5 | Documentation & cleanup | 10 minutes |
| **Total** | | **~60 minutes** |

**Note**: Actual time may vary based on testing discoveries and positioning adjustments.

---

## Open Questions

1. **Mode palette layout**: How are [E] and [S] currently arranged in mode palette?
   - Answer needed: Check `mode_palette_loader.py` or mode palette UI structure

2. **Positioning**: Will mode palette container width change affect other UI elements?
   - Answer needed: Test in running application

3. **Active state behavior**: Should [S] button be "checked" when simulation mode is active, or only when simulation is running?
   - Answer needed: Review current behavior and user expectations

4. **Color semantics**: Does red active state need to be preserved for simulation identity?
   - Current assumption: Yes, red indicates "simulation active" (important distinction)

---

## Next Steps

1. ✅ Review plan with user
2. ✅ Check mode palette structure (how [E] and [S] are related)
3. ✅ Begin Phase 1: UI file restructuring
4. ✅ Continue through phases sequentially
5. ✅ Test thoroughly after each phase
6. ✅ Document results in completion document

---

**Plan Status**: Ready for implementation
**Approval needed**: User confirmation to proceed
**First action**: Investigate current mode palette structure

