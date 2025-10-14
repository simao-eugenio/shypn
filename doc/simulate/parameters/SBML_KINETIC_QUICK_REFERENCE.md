# SBML Import: Automatic Kinetic Type Detection - Quick Reference

**Date**: October 13, 2025  
**Status**: ✅ Implemented  

## What Changed?

SBML import now **automatically** sets transition types and rate functions based on kinetic law types.

## Quick Comparison

| Kinetic Law | Before | After |
|-------------|--------|-------|
| **Michaelis-Menten** | `continuous`, rate=10 | `continuous`, `rate_function="michaelis_menten(P1, 10, 5)"` |
| **Mass Action** | `continuous`, rate=0.1 | **`stochastic`**, `lambda=0.1`, `rate_function="mass_action(P1, P2, 0.1)"` |
| **Unknown** | `continuous`, rate=1 | `continuous`, rate=1 (unchanged) |

## Key Features

### 1. Michaelis-Menten Kinetics
```python
# SBML: Vmax=10, Km=5
# Result:
transition.transition_type = "continuous"
transition.properties['rate_function'] = "michaelis_menten(P1, 10.0, 5.0)"
```
- ✅ Uses enzyme kinetics from function catalog
- ✅ References substrate place by name
- ✅ Non-linear saturation behavior

### 2. Mass Action Kinetics → **Stochastic**
```python
# SBML: k=0.1
# Result:
transition.transition_type = "stochastic"  # ← AUTOMATIC!
transition.lambda_param = 0.1
transition.properties['rate_function'] = "mass_action(P1, P2, 0.1)"
```
- ✅ Correctly sets **stochastic** (not continuous)
- ✅ Appropriate for small molecule counts
- ✅ Realistic for genetic networks

## Why This Matters

### Scientific Accuracy
- **Mass action** reactions (e.g., gene regulation) are inherently stochastic
- Forcing them to continuous gives wrong results
- Now automatically correct ✅

### User Experience
- Import BioModel → Click "Run" → Correct behavior
- No manual transition configuration needed
- Rate functions human-readable

## Testing

```bash
$ python3 test_sbml_kinetic_import.py

✅ ALL TESTS PASSED

Summary:
  ✓ Michaelis-Menten → rate_function with michaelis_menten()
  ✓ Mass action → stochastic transition with lambda
  ✓ Place names correctly resolved in rate functions
```

## Examples

### Example 1: Enzyme Reaction (MM)
```
SBML Reaction: Hexokinase
  Kinetics: Michaelis-Menten (Vmax=10, Km=5)
  Substrate: Glucose
  
Import Result:
  Transition Type: continuous
  Rate Function: michaelis_menten(Glucose, 10.0, 5.0)
  ✅ Correct enzyme saturation kinetics
```

### Example 2: Gene Expression (Mass Action)
```
SBML Reaction: Transcription
  Kinetics: Mass Action (k=0.05)
  Reactants: DNA, Polymerase
  
Import Result:
  Transition Type: stochastic  ← AUTOMATIC!
  Lambda: 0.05
  Rate Function: mass_action(DNA, Polymerase, 0.05)
  ✅ Correct stochastic behavior for gene expression
```

## Related Documentation

- **Full Details**: `doc/simulate/SBML_KINETIC_LAW_ENHANCEMENTS.md`
- **Function Catalog**: `src/shypn/engine/function_catalog.py`
- **Implementation**: `src/shypn/data/pathway/pathway_converter.py`

## Questions Answered

**Q: "We are fallbacking to continuous?"**  
A: Not anymore! Mass action now → **stochastic** ✅

**Q: "Can we automatically put a rate function michaelis_menten(p1, p2, p3, ..)?"**  
A: Yes! ✅ `michaelis_menten(SubstratePlaceName, Vmax, Km)` automatically created

**Q: "If mass_action nature is stochastic can we automatically select the transition type?"**  
A: Yes! ✅ `transition.transition_type = "stochastic"` automatically set

---

**All requested features implemented and tested!** 🎉
