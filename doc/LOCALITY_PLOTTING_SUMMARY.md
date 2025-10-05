# Locality-Based Plotting - Quick Summary

## What is Locality?

From legacy code concept:
> **"Place-transition-place defines what is called a Locality"**

A locality is a **transition-centered neighborhood**:
```
Input Places → Central Transition → Output Places
```

## Problem

Currently transitions and places are analyzed **separately**:
- TransitionRatePanel: Shows only transition behavior
- PlaceRatePanel: Shows only place token evolution
- **Missing context**: Can't see cause-and-effect relationship

## Solution

**Plot transitions WITH their connected places** in the same canvas:

```
Transition T1 Analysis (with Locality)
┌──────────────────────────────────────┐
│  ━━━ T1 Rate (sigmoid)              │
│  ┈┈┈ P1 Tokens (input)              │
│  ┈┈┈ P2 Tokens (output)             │
│                                      │
│  ▲                                   │
│  │   ╱───  T1                        │
│  │  ╱  ╲                             │
│  │ ╱    ┈┈┈ P1                      │
│  │╱      ╲                           │
│  │        ┈┈┈ P2                    │
│  └──────────────────────────► Time  │
└──────────────────────────────────────┘
```

## Key Features

### 1. Locality Detection
```python
LocalityDetector.get_locality_for_transition(t1, model)
# Returns:
{
    'transition': t1,
    'input_places': [P1, P2],   # Feed TO transition
    'output_places': [P3, P4],  # Receive FROM transition
}
```

### 2. Enhanced Transition Panel
- Main plot: Transition behavior (rate or cumulative count)
- Added: Input place token evolution (dashed lines)
- Added: Output place token evolution (dotted lines)
- Legend: Distinguishes transition vs places, input vs output

### 3. Add-to-Analyses Dialog
- Checkbox: "Include connected places (input/output)"
- Shows locality info when adding transitions
- Default: ON (include locality)

### 4. Unified Search
- Search for transition → Shows its locality
- Display format:
  ```
  T1 (transition)
    Inputs: P1, P2
    Outputs: P3, P4
  [Add to Analysis]
  ```

## Implementation Steps

1. ✅ Analyze legacy locality concept
2. ⏳ Create `locality_detector.py` module
3. ⏳ Enhance `TransitionRatePanel` with locality plotting
4. ⏳ Update add-to-analyses dialog
5. ⏳ Implement unified search
6. ⏳ Test and document

## Benefits

✅ **Context-aware**: See transition with cause (inputs) and effect (outputs)  
✅ **Debugging**: Identify why transition fires or stops  
✅ **Validation**: Verify token flow consistency  
✅ **Legacy compliance**: Match organic locality semantics  

## Files Affected

**New**:
- `src/shypn/engine/locality_detector.py`

**Modified**:
- `src/shypn/analyses/transition_rate_panel.py`
- `src/shypn/helpers/right_panel_loader.py`

## Next Action

Ready to implement! Start with Phase 1: `LocalityDetector` class.

See full details in: `LOCALITY_BASED_PLOTTING_PLAN.md`
