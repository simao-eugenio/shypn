# SBML Import: Default Continuous Transitions

**Date**: October 12, 2025  
**Status**: ✅ Implemented  
**File**: `src/shypn/data/pathway/pathway_converter.py`

## Change

Modified the default transition type for SBML reactions without kinetic laws from **"immediate"** to **"continuous"**.

## Rationale

Biochemical pathways imported from SBML typically represent **continuous processes** (enzyme kinetics, chemical reactions) rather than discrete/immediate events. Using continuous transitions by default:

1. ✅ **More realistic** - Matches biological reality of metabolic reactions
2. ✅ **Better for simulation** - Continuous transitions work with ODE solvers
3. ✅ **Expected behavior** - Users importing SBML expect continuous dynamics

## Transition Type Logic

When converting SBML reactions to Petri net transitions, the type is determined as follows:

```python
if reaction.kinetic_law:
    if kinetic_law.rate_type == "michaelis_menten":
        transition_type = "continuous"  # Enzyme kinetics
    elif kinetic_law.rate_type == "mass_action":
        transition_type = "stochastic"  # Chemical kinetics
    else:
        transition_type = "timed"       # Other kinetic types
else:
    # DEFAULT: No kinetic law specified
    transition_type = "continuous"  # ← Changed from "immediate"
    rate = 1.0
```

## Impact

### Before (immediate transitions)
- Reactions fire instantaneously when enabled
- Discrete token movement
- Not suitable for ODE-based simulation
- Requires stochastic simulation

### After (continuous transitions)
- Reactions have continuous flow rates
- Suitable for ODE-based simulation
- Can model enzyme kinetics
- More appropriate for metabolic pathways

## Related Files

- `src/shypn/data/pathway/pathway_converter.py` - Conversion logic (line ~194)
- `doc/SOURCE_SINK_TRANSITION_TYPES_ANALYSIS.md` - Transition types documentation

## Testing

Import any SBML file and check transition properties:
1. Open SBML file in Shypn
2. Right-click on any transition (reaction)
3. Check "Transition Type" property
4. Should show "continuous" for reactions without explicit kinetic laws

## Notes

- Reactions **with** kinetic laws still get their type from the kinetic law
- Rate is set to 1.0 by default (can be modified in transition properties)
- This only affects SBML import, not manual transition creation
- Users can still change transition type after import via properties dialog

## Commit Message Suggestion

```
SBML import: Default to continuous transitions

Change default transition type for SBML reactions without kinetic
laws from "immediate" to "continuous". This better reflects the
continuous nature of biochemical pathways and makes SBML imports
work better with ODE-based simulation.
```
