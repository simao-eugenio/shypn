# Threshold Implementation Summary

## Completed Changes

### 1. Arc Class - Added Threshold Property
**File**: `src/shypn/netobjs/arc.py`

Added `threshold` property to store formula expressions:
```python
# Behavioral properties (formula support)
self.threshold = None  # Threshold formula (can be dict, expression, or value)
```

### 2. Transition Class - Added Guard and Rate Properties
**File**: `src/shypn/netobjs/transition.py`

Added behavioral properties:
```python
# Behavioral properties
self.enabled = True  # Can this transition fire?
self.guard = None  # Guard function/expression (enables/disables transition)
self.rate = None  # Rate function for consumption/production dynamics
```

### 3. Arc Dialog Loader - Threshold Support
**File**: `src/shypn/helpers/arc_prop_dialog_loader.py`

**Added imports**:
```python
import json  # For formatting dicts
import ast   # For safe parsing
```

**Added methods**:

#### `_format_threshold_for_display(threshold)`
Formats threshold for UI display:
- `None` → empty string
- `dict` → JSON formatted (indented for readability)
- `number` → string representation
- `string` → as-is

#### `_parse_threshold(text)`
Parses threshold text from UI:
- Empty → `None`
- Number string → numeric value (`int` or `float`)
- Dict string `{...}` → parsed dict (using `ast.literal_eval`)
- Other → kept as string expression

**Updated `_populate_fields()`**:
Loads threshold from arc object to UI TextView

**Updated `_apply_changes()`**:
Saves threshold from UI to arc object with logging

### 4. Transition Dialog Loader - Guard and Rate Support
**File**: `src/shypn/helpers/transition_prop_dialog_loader.py`

**Updated `_populate_fields()`**:
- Loads `guard` from transition to TextView
- Loads `rate` from transition to TextView
- Made name field read-only

**Updated `_apply_changes()`**:
- Saves `guard` from UI to transition
- Saves `rate` from UI to transition
- Added debug logging

## Usage Examples

### Arc Threshold Examples

User can input in the arc properties dialog threshold field:

**1. Simple numeric value:**
```
5
```
Stored as: `arc.threshold = 5`

**2. Expression string:**
```
P1 >= 5
```
Stored as: `arc.threshold = "P1 >= 5"`

**3. Dictionary with expressions:**
```
{'threshold': 'P1 >= 5', 'weight': 'min(P1, P2)'}
```
Stored as: `arc.threshold = {'threshold': 'P1 >= 5', 'weight': 'min(P1, P2)'}`

**4. Complex formula:**
```
{'value': 5, 'comparator': '>=', 'mode': 'instant'}
```
Stored as structured dict

### Transition Guard/Rate Examples

**Guard (enable/disable condition):**
```
P1 >= 2 and P2 > 0
```

**Rate (firing rate function):**
```
lambda_rate * np.exp(-t/10)
```

**Dictionary format:**
```
{'condition': 'P1 > 5', 'priority': 'P1 + P2'}
```

## Round-Trip Verification

The implementation ensures proper round-trip:

1. **Save**: User enters `{'threshold': 'P1 >= 5'}` in UI
2. **Parse**: Parsed as dict and stored in `arc.threshold`
3. **Reopen**: Dialog displays formatted JSON:
   ```json
   {
     "threshold": "P1 >= 5"
   }
   ```
4. **Edit**: User can modify and save again

## Testing Checklist

### Arc Threshold
- [ ] Open arc properties dialog
- [ ] Threshold field appears
- [ ] Enter simple number (e.g., `5`)
- [ ] Save and reopen → number appears
- [ ] Enter expression (e.g., `P1 >= 5`)
- [ ] Save and reopen → expression appears
- [ ] Enter dict (e.g., `{'threshold': 'P1 * 2'}`)
- [ ] Save and reopen → formatted JSON appears
- [ ] Verify arc object has correct threshold value
- [ ] Verify persistency (save file, reload)

### Transition Guard/Rate
- [ ] Open transition properties dialog
- [ ] Guard field appears in Behavior tab
- [ ] Rate field appears in Behavior tab
- [ ] Enter guard expression
- [ ] Save and reopen → guard appears
- [ ] Enter rate expression
- [ ] Save and reopen → rate appears
- [ ] Verify transition object has correct values
- [ ] Verify persistency (save file, reload)

## Current Limitations

1. **No validation**: User can enter invalid expressions
2. **No evaluation**: Expressions are stored but not evaluated yet
3. **No autocomplete**: No helper for place names or functions
4. **No syntax highlighting**: Plain text input
5. **No error checking**: Invalid dicts accepted silently

## Next Steps (Future Work)

### Priority 1: Formula Evaluator
Create `src/shypn/utils/formula_evaluator.py`:
```python
class FormulaEvaluator:
    @staticmethod
    def evaluate(formula, context: Dict[str, Any]) -> Any:
        """Evaluate formula with runtime context"""
        # Implementation from legacy code
```

### Priority 2: Validation
Add real-time validation:
- Check syntax as user types
- Highlight errors
- Show available place names
- Validate dict structure

### Priority 3: Context Helper
Provide context popup:
- List available places (P1, P2, etc.)
- Show available functions (sigmoid, hill, etc.)
- Display examples

### Priority 4: File Persistence
Ensure threshold/guard/rate saved to/loaded from files:
- JSON serialization
- XML serialization (if used)
- Migration from old format

### Priority 5: Runtime Evaluation
Integrate with simulation:
- Evaluate thresholds when checking arc conditions
- Evaluate guards when enabling transitions
- Evaluate rates for timing

## Security Note

⚠️ **Current implementation stores expressions as strings without validation**

Before enabling runtime evaluation:
1. Use `ast.literal_eval()` for dicts (already done ✅)
2. Restrict eval namespace (remove `__builtins__`)
3. Whitelist allowed functions
4. Consider using `asteval` or `sympy` for safer evaluation
5. Sandbox execution environment

## Debug Logging

All operations are logged with `[ArcPropDialogLoader]` and `[TransitionPropDialogLoader]` prefixes:
- Threshold/guard/rate loading
- Value changes (old → new)
- Parse operations
- Save operations

Check terminal output for debugging.

## Documentation

- Full analysis: `doc/THRESHOLD_ANALYSIS.md`
- Implementation summary: `doc/THRESHOLD_IMPLEMENTATION.md` (this file)
- Legacy reference: `legacy/shypnpy/simple_formula_dictionary.py`
