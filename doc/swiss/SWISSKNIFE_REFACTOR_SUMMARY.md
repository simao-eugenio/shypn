# SwissKnifePalette Refactor - Executive Summary

**Date:** October 22, 2025  
**Status:** Ready for Implementation  
**Priority:** CRITICAL - Constant Height Architecture  
**Wayland Safety:** 10/10 ✅ (No reparenting operations)

---

## Strategic Decisions Made

### ✅ APPROVED
1. **Constant height main palette** - 114px always (never jumps)
2. **Parameter panels above sub-palettes** - Universal pattern for all tools
3. **All sub-palettes 50px fixed** - SimulateToolsPalette settings extracted
4. **Modular architecture** - Split 582-line monolith into 6 classes

### ❌ REJECTED
- **Floating palette feature** - Insufficient benefit vs complexity (discarded)

---

## Problem Statement

### Current Issues
1. **Variable height sub-palettes** - Height jumps 70px when switching to Simulate
2. **SimulateToolsPalette internal micro-panel** - Settings inside sub-palette (wrong architecture)
3. **No universal parameter panel pattern** - Each tool implements settings differently
4. **Monolithic 582-line class** - Hard to extend and maintain

### Space Usage Problem
```
Edit category:    139px (12.9% of 1080p)
Simulate category: 209px (19.4% of 1080p) ⚠️ +70px jump!
Layout category:   139px (12.9% of 1080p)
```

**User Impact:** Palette height jumps up/down when switching categories → poor UX

---

## Solution Architecture

### Constant Height Pattern
```
SwissKnifePalette Container (VERTICAL)
├─ 1. Parameter Panel Revealer (TOP, variable height, ABOVE palette)
│   └─ [Dynamic panels for any tool] - slides UP from below
├─ 2. Sub-Palette Area (MIDDLE, 50px FIXED)
│   ├─ Edit sub-palette (50px)
│   ├─ Simulate sub-palette (50px - settings REMOVED)
│   └─ Layout sub-palette (50px)
└─ 3. Category Buttons (BOTTOM, 44px fixed)
    └─ [Edit] [Simulate] [Layout]

Total Main Palette Height: 114px CONSTANT ✅
```

### Key Innovation: Universal Parameter Panel Pattern

**Any tool can register parameter panel:**
```python
# In tool initialization:
def create_my_settings_panel():
    panel = Gtk.Box()
    # Add controls...
    return panel

palette.parameter_panel_manager.register_parameter_panel(
    'my_tool_settings',
    create_my_settings_panel  # Factory function
)

# In tool UI:
settings_button.connect('clicked', lambda b: 
    palette.parameter_panel_manager.toggle_panel('my_tool_settings')
)
```

**Behavior:**
- Click settings button → panel slides UP above sub-palette (400ms animation)
- Click again → panel slides DOWN (toggle)
- Switch category → panel auto-hides
- Main palette height stays 114px (panel is ABOVE it)

---

## Implementation Plan

### Phase 1: Modular Refactoring (4 hours)
**Goal:** Split monolithic class into modules

**Components:**
- `SwissKnifePaletteUI` - Widget construction
- `SwissKnifePaletteAnimator` - State machine for animations
- `SwissKnifePaletteController` - Signal coordination
- `ParameterPanelManager` - **NEW** - Universal panel lifecycle
- `SubPaletteRegistry` - Plugin management

**Validation:** All existing functionality works unchanged

### Phase 2: Constant Height Sub-Palettes (3 hours) - CRITICAL
**Goal:** Force all sub-palettes to 50px

**Tasks:**
1. Set `sub_palette_area.set_size_request(-1, 50)` - force 50px height
2. **Refactor SimulateToolsPaletteLoader:**
   - Remove internal `settings_revealer`
   - Extract `create_settings_panel()` factory method
   - Keep only simulation controls [Step][Reset][Play]
3. Verify all sub-palettes now 50px

**Validation:**
- Edit: 50px ✅
- Simulate: 50px ✅ (was 120px)
- Layout: 50px ✅

### Phase 3: Parameter Panel Architecture (5 hours) - CRITICAL
**Goal:** Implement universal parameter panel pattern

**Tasks:**
1. Create `ParameterPanelManager` class
   - Panel registry (tool_id → factory function)
   - `show_panel(tool_id)` - slides UP with animation
   - `hide_panel()` - slides DOWN with animation
   - `toggle_panel(tool_id)` - show/hide toggle
   - Auto-hide on category switch

2. Integrate parameter panel revealer in UI
   ```python
   # TOP: Parameter panel revealer
   self.parameter_panel_revealer = Gtk.Revealer()
   self.parameter_panel_revealer.set_transition_type(SLIDE_UP)
   container.pack_start(parameter_panel_revealer, False, False, 0)
   
   # MIDDLE: Sub-palette area (50px fixed)
   self.sub_palette_area.set_size_request(-1, 50)
   container.pack_start(sub_palette_area, False, False, 0)
   
   # BOTTOM: Category buttons
   container.pack_end(category_box, False, False, 0)
   ```

3. Wire SimulateToolsPalette settings
   - Register settings panel factory
   - Connect [⚙] button to `toggle_panel('simulate_settings')`

**Validation:**
- Open Simulate → 50px height
- Click [⚙] → panel slides UP above
- Click [⚙] again → panel slides DOWN
- Switch to Edit → panel auto-hides
- Main palette height: 114px constant ✅

### Phase 4: Plugin Architecture (3 hours)
**Goal:** Extensible sub-palette system

**Interface:**
```python
class SubPalettePlugin(ABC):
    def create_widget(self) -> Gtk.Widget: pass
    def get_fixed_height(self) -> int: return 50
    def has_parameter_panel(self) -> bool: return False
    def create_parameter_panel(self) -> Optional[Gtk.Widget]: return None
```

### Phase 5: CSS Externalization (2 hours)
**Goal:** External CSS file + parameter panel styling

---

## Timeline

| Phase | Duration | Critical Path |
|-------|----------|---------------|
| Phase 1: Modular Refactoring | 4 hours | ✅ Start |
| Phase 2: Constant Height | 3 hours | ✅ Critical |
| Phase 3: Parameter Panels | 5 hours | ✅ Critical |
| Phase 4: Plugin Architecture | 3 hours | - |
| Phase 5: CSS | 2 hours | - |
| Testing & Docs | 3 hours | ✅ End |

**Total:** 20 hours (2.5 working days)

---

## Success Criteria

### Must Have ✅
- [ ] Main palette height: 114px constant (never changes)
- [ ] All sub-palettes: 50px fixed
- [ ] Parameter panels slide UP/DOWN above sub-palettes
- [ ] SimulateToolsPalette refactored (settings extracted)
- [ ] No height jumps when switching categories
- [ ] Wayland-safe (no reparenting)

### Nice to Have
- [ ] Plugin architecture for new categories
- [ ] External CSS file
- [ ] Unit tests 80% coverage

---

## Space Optimization

### Before (Variable Height)
```
Edit:     139px (12.9%)
Simulate: 209px (19.4%) ⚠️ +70px
Layout:   139px (12.9%)
```

### After (Constant Height)
```
Edit:     139px (12.9%)
Simulate: 139px (12.9%) ✅ -70px savings!
Layout:   139px (12.9%)

With settings panel open:
139px (main palette) + [variable panel above]
(Main palette still 139px - panel is ABOVE it)
```

**Key Wins:**
- 33% space savings on Simulate category (209px → 139px)
- No height jumps (stable 139px always)
- Better UX (predictable palette position)

---

## Wayland Safety

### ✅ Safe Operations Used
- Widget creation in overlay (build once, add once)
- Revealer animations (within same parent)
- Parameter panel lifecycle (build/destroy in parameter_panel_revealer)
- Show/hide widgets (`set_reveal_child()`)

### ❌ Forbidden Operations (NOT Used)
- Widget reparenting (`parent1.remove()` + `parent2.add()`)
- GtkSocket/GtkPlug
- Window embedding
- `attach_to()` methods

**Wayland Safety Score: 10/10** ✅

---

## Files to Modify

### Core Implementation
1. **src/shypn/helpers/swissknife_palette.py** - Split into modules
2. **src/shypn/helpers/simulate_tools_palette_loader.py** - Extract settings
3. **src/shypn/helpers/swissknife_palette_ui.py** - NEW
4. **src/shypn/helpers/swissknife_palette_animator.py** - NEW
5. **src/shypn/helpers/parameter_panel_manager.py** - NEW (critical)

### Integration
6. **src/shypn/helpers/model_canvas_loader.py** - Wire new signals
7. **ui/styles/swissknife_palette.css** - NEW (external CSS)

### Testing
8. **tests/test_swissknife_parameter_panels.py** - NEW
9. **tests/test_swissknife_constant_height.py** - NEW

---

## Next Steps

1. ✅ Review and approval (DONE - decisions made)
2. Create feature branch: `feature/swissknife-constant-height`
3. Begin Phase 1 (Modular Refactoring)
4. Daily progress review
5. Integration testing after Phase 3

---

## Conclusion

**Core Innovation:** Universal parameter panel pattern
- Constant 114px main palette height
- Parameter panels slide above sub-palettes
- Extensible to any tool needing settings
- 100% Wayland-safe

**Implementation:** 20 hours, 5 phases, high confidence  
**Benefit:** Better UX, 33% space savings, stable palette height  
**Risk:** Low (proven GTK patterns, no reparenting)

**Ready for implementation!** 🚀
