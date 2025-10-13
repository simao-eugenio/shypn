# Transition Type Default Changed to Continuous

**Date**: October 12, 2025  
**Change**: Default transition type changed from 'immediate' to 'continuous'  
**Status**: ✅ **COMPLETE** - All paths updated

## Summary

Changed the default transition type throughout the entire codebase from `'immediate'` to `'continuous'`. This affects new transition creation, fallback values in getattr/get operations, and UI dialog defaults.

## Rationale

Continuous transitions (Stochastic Hybrid Petri Nets - SHPN) are more suitable for:
- Biochemical pathway modeling (enzyme kinetics)
- Continuous flow systems
- Rate-based dynamics
- Hybrid systems combining discrete and continuous behavior

Making continuous the default aligns with the primary use case of modeling biochemical pathways where reactions have continuous rates.

## Files Modified

### Core Object Model
1. **`src/shypn/netobjs/transition.py`** (line 56)
   - Changed: `self.transition_type = 'continuous'`
   - Comment updated: "(default: continuous)"

### Behavior System
2. **`src/shypn/engine/behavior_factory.py`** (line 42)
   - Changed: `getattr(transition, 'transition_type', 'continuous')`
   - Comment updated: "default to 'continuous' if not specified"

3. **`src/shypn/engine/simulation/controller.py`** (line 212)
   - Changed: `getattr(transition, 'transition_type', 'continuous')`

### Edit Operations
4. **`src/shypn/edit/snapshots.py`** (2 locations)
   - Line 59: `getattr(transition, 'transition_type', 'continuous')`
   - Line 169: `snapshot.get('transition_type', 'continuous')`

5. **`src/shypn/edit/undo_operations.py`** (line 326)
   - Changed: `snapshot.get('transition_type', 'continuous')`

### UI and Dialogs
6. **`src/shypn/helpers/model_canvas_loader.py`** (2 locations)
   - Line 1683: Context menu type detection
   - Line 2365: Type change handler

7. **`src/shypn/helpers/transition_prop_dialog_loader.py`** (line 219)
   - Changed default fallback to `'continuous'`
   - Changed combo box default index to 3 (continuous)
   - Comment: "Default to continuous"

### Analysis Panels
8. **`src/shypn/analyses/plot_panel.py`** (2 locations)
   - Line 270: UI list display
   - Line 398: Plot legend labels

9. **`src/shypn/analyses/transition_rate_panel.py`** (3 locations)
   - Line 398: Type detection for source/sink display
   - Line 533: Waiting state message
   - Line 616: Plot legend labels

### Diagnostics
10. **`src/shypn/diagnostic/locality_runtime.py`** (line 276)
    - Changed: `getattr(transition, 'transition_type', 'continuous')`

## Behavior Changes

### Before:
```python
# Creating a new transition
t = Transition(x=100, y=100, id=1, name='T1')
print(t.transition_type)  # → 'immediate'

# Loading from snapshot without type
transition_type = snapshot.get('transition_type', 'immediate')

# Property dialog dropdown
type_combo.set_active(0)  # Immediate selected by default
```

### After:
```python
# Creating a new transition
t = Transition(x=100, y=100, id=1, name='T1')
print(t.transition_type)  # → 'continuous'

# Loading from snapshot without type
transition_type = snapshot.get('transition_type', 'continuous')

# Property dialog dropdown
type_combo.set_active(3)  # Continuous selected by default
```

## Backward Compatibility

✅ **Fully backward compatible**:
- Existing saved files with explicit `transition_type` values are preserved
- Old files with `'immediate'` transitions continue to work correctly
- The change only affects:
  - New transitions created after this change
  - Fallback values when type is missing/None
  - Default selection in property dialogs

## Testing Checklist

After applying these changes, verify:

### Test 1: New Transition Creation
1. Launch application
2. Create new Petri net
3. Add a transition
4. ✅ **Verify**: New transition has `transition_type = 'continuous'`
5. ✅ **Verify**: Transition properties dialog shows "Continuous" selected

### Test 2: Existing Files
1. Load an existing .shy file with various transition types
2. ✅ **Verify**: All transitions preserve their original types
3. ✅ **Verify**: Immediate transitions still show as "IMM" in analysis panels
4. ✅ **Verify**: Continuous transitions show as "CON"

### Test 3: Simulation
1. Create new transition (should be continuous by default)
2. Set rate = 2.0
3. Add input/output places
4. Run simulation
5. ✅ **Verify**: Transition fires with continuous behavior
6. ✅ **Verify**: Analysis panels show rate curve (not cumulative count)

### Test 4: Type Changes
1. Create transition (continuous by default)
2. Right-click → Change Type → Immediate
3. ✅ **Verify**: Type changes correctly
4. ✅ **Verify**: Simulation behavior changes to immediate
5. ✅ **Verify**: Analysis panels show cumulative count (not rate curve)

### Test 5: SBML Import
1. Import SBML file
2. ✅ **Verify**: Transitions from biochemical reactions are continuous
3. ✅ **Verify**: Pathway converter still respects kinetics-based type detection

### Test 6: Undo/Redo
1. Create transition (continuous by default)
2. Change type to immediate
3. Undo
4. ✅ **Verify**: Type reverts to continuous
5. Redo
6. ✅ **Verify**: Type changes back to immediate

## Migration Notes

For users with existing workflows:
- No action required - existing files work as before
- **New behavior**: Newly created transitions will default to continuous
- **Recommendation**: For discrete event nets (classical Petri nets), explicitly set type to 'immediate' or 'timed' after creation
- **Best practice**: Use continuous for biochemical/hybrid systems, immediate/timed for discrete event systems

## Documentation Updates Needed

Consider updating:
- User manual: Mention default transition type is continuous
- Tutorial examples: Update screenshots showing property dialogs
- API documentation: Update docstrings mentioning default type
- Quick start guide: Explain when to use each transition type

## Related Changes

This change complements:
- Continuous transition rate function implementation (sigmoid, exponential, linear)
- Source/sink transition markers for continuous systems
- Matplotlib plotting with rate curves for continuous transitions
- SBML import mapping biochemical reactions to continuous transitions

## Files NOT Modified

The following files contain transition type references but were **intentionally not modified**:
- Documentation files (`.md`) - kept as historical examples
- Test files - preserve explicit type specifications
- Legacy files - maintain backward compatibility examples
- Pathway converter - uses explicit type assignment based on kinetics

## Summary

**Total files modified**: 10 core source files  
**Total changes**: 15 individual replacements  
**Scope**: Entire codebase default transition type  
**Impact**: Low (backward compatible, affects only new creations)  
**Testing**: Requires verification of new transition creation and property dialogs

---

**Change Applied**: October 12, 2025  
**Status**: ✅ Ready for testing  
**Priority**: Medium (workflow improvement, not a bug fix)
