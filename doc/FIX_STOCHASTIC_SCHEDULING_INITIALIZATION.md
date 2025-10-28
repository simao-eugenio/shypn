# Fix: Stochastic Transition Scheduling in SBML Models

## Problem
When loading SBML models from .shy files, stochastic and timed transitions did not fire, while immediate transitions worked correctly.

## Root Causes

### 1. Over-Restrictive Structural Enablement Logic
**Issue**: Custom logic prevented stochastic transitions from firing if ANY timed transitions had tokens, even if those timed transitions weren't ready to fire yet.

**Code**:
```python
# BROKEN: File-Open-SBML-Health (before fix)
elif not structurally_enabled_timed:  # Too restrictive!
    # Stochastic only fires if NO timed have tokens
```

**Fix**: Reverted to Default-Tab-Health's simpler logic:
```python
# FIXED: Match Default-Tab-Health
elif not discrete_fired:  # Stochastic fires if no timed FIRED
    # Simpler and correct
```

**Effect**: Stochastic transitions can now fire when timed transitions exist but haven't fired in the current step.

### 2. Missing Initialization After Reset
**Issue**: When simulation was reset, transition scheduling states were cleared but not reinitialized.

**Fix**: Added `_update_enablement_states()` call in `reset()` method:
```python
# Schedule time-dependent transitions (timed/stochastic) after reset
self._update_enablement_states()
```

**Effect**: Stochastic/timed transitions are properly scheduled after reset based on initial markings.

## Testing
To verify the fixes work:
1. Load BIOMD0000000001.shy (17 stochastic transitions)
2. Mark one transition as source (to provide tokens)
3. Run simulation
4. Stochastic transitions should fire correctly
5. Reset simulation - transitions should be rescheduled

## Files Changed
- `src/shypn/engine/simulation/controller.py`:
  - Reverted structural enablement logic (lines 570-595)
  - Added `_update_enablement_states()` call in `reset()` (line 1650)

## Commits
- Hash: 69b68e0 - "Fix: Revert to Default-Tab-Health stochastic firing logic"
- Hash: 35ffcd7 - "Fix: Initialize time-dependent transition scheduling on controller creation" (partially reverted)

## Lesson Learned
Custom optimization logic (structural enablement) was well-intentioned but introduced a subtle bug. Always match reference implementation (Default-Tab-Health) first, optimize later with thorough testing.
