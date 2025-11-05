# Simulation Hang Fix - Attribute Name Mismatch

**Date:** January 2025  
**Status:** ✅ FIXED  
**Severity:** CRITICAL  
**Impact:** Users can now run simulations after applying heuristic parameters

---

## Problem

After applying heuristic parameters to transitions, simulation hung when user tried to step/run.
No error messages were shown, and the simulation simply stopped progressing.

## Root Cause

**Simple typo in attribute name:**

In `src/shypn/ui/panels/pathway_operations/heuristic_parameters_category.py`:
- Line 44: Stores as `self.model_canvas_loader`
- Lines 447-462: Uses as `self.canvas_loader`

This meant the reset method never executed because the attribute check failed.

## Impact

Without the reset:
- Simulation controller's behavior cache contained stale `TransitionBehavior` instances
- Old parameter values (Km, Vmax, rate functions) were cached
- Transitions fired with incorrect rates or hung
- Enablement checks used outdated state

## Fix

Changed all occurrences in `_reset_simulation_after_parameter_changes()`:
```python
# BEFORE:
self.canvas_loader  # Wrong attribute name - doesn't exist

# AFTER:
self.model_canvas_loader  # Correct attribute name
```

**Files modified:**
- `src/shypn/ui/panels/pathway_operations/heuristic_parameters_category.py` (6 lines)

## Test Coverage

Created `tests/test_simulation_reset_after_parameters.py` with 5 unit tests:
1. ✅ Attribute name consistency
2. ✅ Reset called after parameter application
3. ✅ Fallback to basic reset if canvas_manager missing
4. ✅ Graceful handling when simulation controller missing
5. ✅ Graceful handling when model_canvas_loader is None

**All tests pass.**

## Historical Context

The reset code was already correctly implemented:
- Used comprehensive `reset_for_new_model()` (not just basic `reset()`)
- Had detailed documentation and comments
- Referenced past behavior cache bugs (commits 864ae92, df037a6, be02ff5)

But it never executed due to the attribute name typo.

## Verification

Manual testing recommended:
1. Load KEGG model
2. Analyze and apply heuristic parameters
3. Run simulation
4. Verify transitions fire correctly
5. Verify no hang or freeze

## Lessons Learned

1. **Integration Tests**: Would have caught this bug immediately
2. **Manual Testing**: Should test the complete workflow after implementation
3. **Code Review**: Simple typos are easy to catch during review
4. **Attribute Naming**: Use consistent naming patterns throughout class

## Related Documentation

- `doc/TODO_ACTIVE_ITEMS.md` - Updated with fix status
- `doc/HEURISTIC_PARAMETERS_COMPLETE.md` - Heuristic parameters feature
- `doc/CANVAS_STATE_ISSUES_COMPARISON.md` - Historical behavior cache issues

## Next Steps

1. ✅ Fix implemented and tested
2. ✅ Regression test created
3. ⏭️ Manual verification with real KEGG models
4. ⏭️ Consider adding integration tests for complete workflow
5. ⏭️ Document best practices for parameter application
