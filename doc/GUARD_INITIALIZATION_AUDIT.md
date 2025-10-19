# Guard Initialization Audit - Complete Code Path Analysis

**Date**: October 18, 2025  
**Issue**: Ensure all transitions start with `guard = 1` per GSPN scientific convention  
**Status**: ✅ COMPLETE

## Scientific Basis

**Generalized Stochastic Petri Nets (GSPN) Convention**:
- **Guard = 1**: Transition always enabled (default initial state at t=0)
- **Guard = 0**: Transition always disabled
- **Guard = expression**: Conditional enabling based on state/time

Mathematical representation: $E(t) = \text{guard}(t) \times \text{structural\_enabled}(t)$

## Code Paths Audited

### 1. ✅ Interactive Design-Time Creation

**Path**: User creates transition via GUI

```
User Action → ModelCanvasLoader → DocumentCanvas.add_transition()
→ DocumentModel.create_transition() → Transition.__init__()
```

**Files**:
- `src/shypn/helpers/model_canvas_loader.py` (line 1195, 3072)
- `src/shypn/data/canvas/document_canvas.py` (line 299)
- `src/shypn/data/canvas/document_model.py` (line 68-83)
- `src/shypn/netobjs/transition.py` (line 58)

**Result**: ✅ `Transition.__init__()` sets `self.guard = 1`

**Evidence**:
```python
# src/shypn/netobjs/transition.py line 58
self.guard = 1  # Guard function/expression (enables/disables transition) - defaults to 1 (always enabled)
```

---

### 2. ✅ KEGG Import Path

**Path**: Import pathway from KEGG REST API

```
KEGG API → KEGGParser.parse_kgml() → PathwayConverter.convert()
→ ReactionMapper.create_transitions() → Transition.__init__()
```

**Files**:
- `src/shypn/importer/kegg/kgml_parser.py` (parses KGML XML)
- `src/shypn/importer/kegg/pathway_converter.py` (converts to Petri net)
- `src/shypn/importer/kegg/reaction_mapper.py` (line 72, 107, 124)
- `src/shypn/netobjs/transition.py` (line 58)

**Result**: ✅ `Transition.__init__()` sets `self.guard = 1`

**KEGG-specific checks**:
- ✅ Line 72: `Transition(x, y, transition_id, transition_name, label=name)` - no guard override
- ✅ Line 107: `Transition(x - 10, y, forward_id, ...)` - forward transition, no guard override
- ✅ Line 124: `Transition(x + 10, y, backward_id, ...)` - backward transition, no guard override
- ✅ No `transition.guard =` statements in entire KEGG importer codebase

**Evidence**:
```python
# src/shypn/importer/kegg/reaction_mapper.py line 72
transition = Transition(x, y, transition_id, transition_name, label=name)
# Uses default guard = 1 from __init__

# Verified: No guard assignments in KEGG import
$ grep -r "\.guard\s*=" src/shypn/importer/kegg/
# No matches
```

---

### 3. ✅ SBML Import Path

**Path**: Import Systems Biology Markup Language files

```
SBML File → SBMLParser.parse() → PathwayConverter.convert_to_petri_net()
→ DocumentModel.create_transition() → Transition.__init__()
```

**Files**:
- `src/shypn/data/pathway/sbml_parser.py` (parses SBML XML)
- `src/shypn/data/pathway/pathway_converter.py` (line 195)
- `src/shypn/data/canvas/document_model.py` (line 68-83)
- `src/shypn/netobjs/transition.py` (line 58)

**Result**: ✅ `Transition.__init__()` sets `self.guard = 1`

**SBML-specific checks**:
- ✅ Line 195: `self.document.create_transition(x=x, y=y, label=...)` - uses factory method
- ✅ `_configure_transition_kinetics()` sets `rate`, `rate_function`, `transition_type` - **never touches guard**
- ✅ No `transition.guard =` statements in pathway converter

**Evidence**:
```python
# src/shypn/data/pathway/pathway_converter.py line 195-198
transition = self.document.create_transition(
    x=x,
    y=y,
    label=reaction.name or reaction.id
)
# Uses default guard = 1 from __init__

# src/shypn/data/pathway/pathway_converter.py line 226-262
def _configure_transition_kinetics(self, transition: Transition, reaction: Reaction):
    # Sets: transition_type, rate, rate_function
    # NEVER sets: guard
```

---

### 4. ✅ File Load/Deserialize Path

**Path**: Load saved .shy file from disk

```
File System → DocumentModel.load_from_file() → DocumentModel.from_dict()
→ Transition.from_dict() → guard conversion
```

**Files**:
- `src/shypn/data/canvas/document_model.py` (line 440)
- `src/shypn/netobjs/transition.py` (line 616-619)

**Result**: ✅ `None` guards converted to `1` during deserialization

**Backward compatibility**:
- Old files with `"guard": null` → converted to `1`
- Old files without guard field → default `1` from `__init__`
- New files save `"guard": 1` explicitly

**Evidence**:
```python
# src/shypn/netobjs/transition.py line 616-619
if "guard" in data:
    # Convert None to 1 (scientific convention: guards default to enabled)
    guard_value = data["guard"]
    transition.guard = 1 if guard_value is None else guard_value
```

---

### 5. ✅ Property Dialog Edit Path

**Path**: User edits guard via Transition Properties dialog

```
User Input → TransitionPropDialogLoader.apply_changes()
→ Transition.set_guard() → guard validation
```

**Files**:
- `src/shypn/helpers/transition_prop_dialog_loader.py` (line 350)
- `src/shypn/netobjs/transition.py` (line 426-442)

**Result**: ✅ Empty/None guards reset to `1`

**User experience**:
- Empty guard field → `set_guard(None)` → converts to `1`
- "0" → transition disabled
- "1" → transition enabled (explicit)
- Expression → conditional enabling

**Evidence**:
```python
# src/shypn/helpers/transition_prop_dialog_loader.py line 350
self.transition_obj.set_guard(guard_text if guard_text else None)

# src/shypn/netobjs/transition.py line 441
self.guard = 1 if guard_value is None else guard_value
```

---

## Summary Matrix

| Code Path | Entry Point | Factory Method | Final Constructor | Guard Value | Status |
|-----------|-------------|----------------|-------------------|-------------|--------|
| Interactive Design | GUI Click | `create_transition()` | `Transition.__init__()` | `1` | ✅ |
| KEGG Import | API Call | `create_transitions()` | `Transition.__init__()` | `1` | ✅ |
| SBML Import | File Load | `create_transition()` | `Transition.__init__()` | `1` | ✅ |
| File Deserialize | `.shy` Load | `Transition.from_dict()` | N/A (reconstruction) | `None → 1` | ✅ |
| Property Edit | Dialog Apply | `set_guard(None)` | N/A (mutation) | `None → 1` | ✅ |

---

## Test Evidence

### Test: Backward Compatibility

```bash
$ python3 -m pytest tests/validation/immediate/test_guards.py::test_guard_none_treated_as_always_true -v
PASSED [100%]
```

**Result**: ✅ Runtime engine still handles `None` correctly (treats as enabled)

### Test: New Transitions

```python
>>> from shypn.netobjs import Transition
>>> t = Transition(100, 100, "T1", "T1")
>>> t.guard
1
```

**Result**: ✅ Default initialization to `1`

### Test: Guard Reset

```python
>>> t.set_guard(None)
>>> t.guard
1
```

**Result**: ✅ `None` converts to `1`

### Test: File Persistence

```python
# Save
>>> t.guard = 1
>>> data = t.to_dict()
>>> data['guard']
1

# Load old file with null
>>> data_old = {'guard': None, ...}
>>> t2 = Transition.from_dict(data_old)
>>> t2.guard
1
```

**Result**: ✅ Serialization and deserialization preserve scientific convention

---

## Unaudited Code Paths (Scripts - Non-Production)

The following scripts create transitions for testing/demos but are **not production code paths**:

- `scripts/demo_shypn_integration.py` - Demo code
- `scripts/generate_galaxy_model.py` - Test model generator
- `scripts/generate_test_models.py` - Test model generator
- `tests/validation/ui/conftest.py` - Test fixtures

**Action**: None required (test code, not production)

---

## Conclusion

✅ **ALL PRODUCTION CODE PATHS AUDITED AND VERIFIED**

1. **Interactive creation**: Uses `Transition.__init__()` → `guard = 1`
2. **KEGG import**: Uses `Transition.__init__()` → `guard = 1`
3. **SBML import**: Uses `Transition.__init__()` → `guard = 1`
4. **File loading**: Converts `None → 1` in `from_dict()`
5. **User editing**: Converts `None → 1` in `set_guard()`

**Scientific Compliance**: All transitions start with `guard = 1` (always enabled), conforming to GSPN formal definitions.

**Backward Compatibility**: Runtime engine still accepts `None` (treats as enabled), so existing tests and legacy code continue to work.

---

**Audited by**: GitHub Copilot  
**Commits**: 
- 801e3c1: Initial guard = 1 implementation
- This audit: Complete verification

**Next Steps**: None - audit complete ✅
