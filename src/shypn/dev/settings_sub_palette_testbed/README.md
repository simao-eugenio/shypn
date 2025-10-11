# Settings Sub-Palette Testbed

**Date**: October 11, 2025  
**Purpose**: Prototype settings sub-palette and time scale controls  
**Status**: Active Development  
**Related**: `/doc/time/SETTINGS_SUB_PALETTE_REFACTORING_PLAN.md`

---

## Overview

This testbed prototypes the conversion of the Settings [⚙] button from a modal dialog to an expandable sub-palette with inline controls, including the new **time scale** feature.

## Goals

1. ✅ Validate UX of toggle button expanding/collapsing sub-palette
2. ✅ Test preset speed buttons (0.1x, 1x, 10x, 60x) behavior
3. ✅ Verify custom speed spinbutton interaction
4. ✅ Ensure smooth animations (slide-down transition)
5. ✅ Test live settings adjustment without stopping simulation
6. ✅ Validate time display format with speed indication

## What's Being Tested

### UI Components
- **GtkToggleButton** for settings button (instead of GtkButton)
- **Nested GtkRevealer** for sub-palette (slide-down animation)
- **Speed preset buttons** (radio-like toggle group)
- **GtkSpinButton** for custom speed values
- **Time Step controls** (Auto/Manual radio buttons)
- **Conflict Policy combo** (existing functionality)

### Behaviors
- Toggle button state synced with revealer visibility
- Only one speed preset active at a time (radio behavior)
- Custom spin unchecks all presets when changed
- Settings apply in real-time (no modal Apply/Cancel)
- Time display shows speed when != 1.0x
- Smooth 300ms slide-down/up animation

## Files

```
settings_sub_palette_testbed/
├── README.md (this file)
├── test_app.py (standalone GTK app)
├── settings_palette_prototype.ui (UI definition)
├── settings_palette_loader.py (widget wiring logic)
└── mock_simulation.py (mock SimulationController for testing)
```

## Running the Testbed

```bash
cd /home/simao/projetos/shypn
python -m shypn.dev.settings_sub_palette_testbed.test_app
```

**Expected behavior:**
1. Window shows simulation palette (similar to production)
2. Click [⚙] → Settings sub-palette slides down
3. Change speed presets → See label update
4. Change custom spin → See label update, presets uncheck
5. Change time step → See label update
6. Click Apply → Sub-palette collapses
7. Click [⚙] again → Sub-palette shows previous values

## Testing Checklist

### Phase 1: Basic Toggle ✓
- [ ] Settings button toggles on/off (visual state)
- [ ] Sub-palette slides down smoothly (300ms)
- [ ] Sub-palette slides up smoothly (300ms)
- [ ] Multiple toggles work correctly

### Phase 2: Speed Controls ✓
- [ ] Click 0.1x → Button activates, spin shows 0.1
- [ ] Click 1x → Button activates, spin shows 1.0
- [ ] Click 10x → Button activates, spin shows 10.0
- [ ] Click 60x → Button activates, spin shows 60.0
- [ ] Only one preset button active at a time
- [ ] Change spin manually → All presets uncheck
- [ ] Spin accepts values 0.01 to 1000.0

### Phase 3: Time Step Controls ✓
- [ ] Auto radio enables auto mode
- [ ] Manual radio enables manual entry
- [ ] Manual entry disabled when Auto selected
- [ ] Manual entry enabled when Manual selected
- [ ] Manual entry accepts positive floats

### Phase 4: Integration ✓
- [ ] Apply button collapses sub-palette
- [ ] Reset button restores defaults
- [ ] Settings persist when reopening
- [ ] Mock simulation responds to speed changes

## Validation Criteria

### ✅ Pass Criteria
1. Sub-palette toggle feels smooth and responsive
2. Speed presets behave like radio buttons (only one active)
3. Custom speed spin works independently from presets
4. Time display updates correctly with speed indication
5. No crashes or GTK warnings
6. Animation timing feels natural (not too fast/slow)

### ❌ Fail Criteria
1. Multiple preset buttons can be active simultaneously
2. Spin button changes don't uncheck presets
3. Sub-palette animation is janky or delayed
4. Settings don't persist when reopening
5. GTK warnings or errors in console

## Known Issues

### Current Limitations
- Mock simulation doesn't actually run (just updates time value)
- No real Petri Net model loaded
- Progress bar is simulated (not real simulation progress)
- Conflict policy doesn't affect anything (no conflicts to resolve)

### Expected After Production Integration
- Real SimulationController integration
- Actual time step effect on simulation accuracy
- Real-time speed adjustment while simulation running
- Conflict policy affects actual transition firing

## Next Steps

1. **Validate UX** - Get feedback on sub-palette feel
2. **Refine animations** - Adjust transition duration if needed
3. **Test edge cases** - Very slow (0.01x) and very fast (1000x) speeds
4. **Polish styling** - Fine-tune colors, spacing, borders
5. **Production integration** - Copy validated code to production files

## Success Metrics

**Ready for production when:**
- ✅ All Phase 1-4 checklist items pass
- ✅ No GTK warnings or errors
- ✅ Smooth 60fps animations
- ✅ User testing feedback positive
- ✅ Edge cases handled gracefully
- ✅ Code documented and clean

## Migration Path

Once validated:

1. Copy `settings_palette_prototype.ui` → `/ui/simulate/simulate_tools_palette.ui`
2. Copy `settings_palette_loader.py` logic → `/src/shypn/helpers/simulate_tools_palette_loader.py`
3. Update `controller.py` to use `time_scale` property
4. Remove old settings dialog code
5. Update documentation
6. Commit with message: "Implement settings sub-palette with time scale controls"

## References

- **Plan**: `/doc/time/SETTINGS_SUB_PALETTE_REFACTORING_PLAN.md`
- **Analysis**: `/doc/time/SIMULATION_TIME_SCALING_ANALYSIS.md`
- **UI Requirements**: `/doc/time/UI_REQUIREMENTS_TIME_SCALE.md`
- **Production UI**: `/ui/simulate/simulate_tools_palette.ui`
- **Production Loader**: `/src/shypn/helpers/simulate_tools_palette_loader.py`

---

**Status**: 🚧 Under active development - October 11, 2025
