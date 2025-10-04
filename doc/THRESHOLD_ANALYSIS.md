# Threshold and Formula System Analysis

## Overview

Based on legacy code analysis, the threshold system supports flexible formula input using dictionary structures that can contain:
- Simple numeric values
- String expressions to be evaluated
- Function definitions

## Data Structure

### Arc Threshold Format

Arcs can have a `threshold` property stored in a dictionary with flexible formats:

```python
# 1. Simple dictionary with expressions
arc.properties = {
    'threshold': "{'value': 5}",  # Simple numeric threshold
    # or
    'threshold': "{'expr': 'P1 * 2 + P2'}",  # Expression-based
    # or  
    'threshold': "{'func': 'sigmoid(P1, k=0.5)'}",  # Function-based
}

# 2. Complex multi-key dictionary
arc.properties = {
    'threshold': "{'weight': 'max(1, P1/2)', 'threshold': 'P3 * 2'}"
}

# 3. Structured threshold with metadata
arc.properties = {
    'threshold': {
        "mode": "numeric",  # or "expression", "function"
        "measure": "instant",  # or "integrated", "average"
        "comparator": ">=",  # comparison operator
        "value": 5  # or expression string
    }
}
```

### Transition Guard/Rate Format

Transitions support similar formula dictionaries:

```python
transition.guard = "P1 >= 2 and P2 > 0"
transition.rate = "lambda_rate * np.exp(-t/10)"

# Can also be dictionaries:
transition.properties = {
    'guard': "{'condition': 'P1 > 5', 'priority': 'P1 + P2'}",
    'rate': "{'base_rate': '0.5', 'modifier': 'np.tanh((P1-5)/3)'}"
}
```

## Implementation Components

### 1. SimpleDictionaryParser (legacy/shypnpy/simple_formula_dictionary.py)

**Purpose**: Parse and validate dictionary strings from UI text inputs

**Key Methods**:
- `parse_dict_string(dict_string: str) -> Dict[str, str]` - Safely parse dictionary using ast.literal_eval
- `validate_dict_string(dict_string: str) -> Tuple[bool, str]` - Validate syntax
- `evaluate_expression(expression: str, context: Dict) -> Any` - Evaluate with runtime context

**Supported Functions**:
- Math: sigmoid, logistic, hill, inv_hill
- Enzyme kinetics: michaelis_menten, competitive_inhibition, noncompetitive_inhibition
- NumPy functions: np.exp, np.log, np.tanh, np.maximum, etc.
- Boolean logic: and, or, not, comparisons

### 2. FormulaIntegration (legacy/shypnpy/formula_integration.py)

**Purpose**: Integration layer between UI dialogs and formula system

**Key Methods**:
```python
def validate_and_parse_formula(text: str, dialog_type: str) -> tuple[bool, Any]
    # Returns (success, parsed_dict_or_error_message)

def evaluate_formula(formula_dict: Dict[str, str], context: Dict) -> Dict[str, Any]
    # Evaluates all expressions in dict with given context

def format_formula_for_display(value: Any) -> str
    # Formats for UI display (JSON, string, or numeric)
```

### 3. Dialog Integration

**Arc Dialog**:
```python
class ArcDialogFormulas:
    def setup_threshold_validation(threshold_view: Gtk.TextView, arc_obj)
        # Real-time validation as user types
    
    def load_arc_formulas(arc_obj, threshold_view)
        # Load from arc.properties['threshold'] to UI
    
    def save_arc_formulas(arc_obj, threshold_view)
        # Parse UI text and save to arc.properties
```

## Storage Format

### In Memory (Runtime)
```python
# Arc object
arc.properties = {
    'threshold': {  # Parsed dictionary object
        'weight': 'max(1, P1/2)',
        'threshold': 'P3 * 2'
    }
}
```

### In UI (TextView/Entry)
```
User sees and edits as string:
"{'weight': 'max(1, P1/2)', 'threshold': 'P3 * 2'}"
```

### In Files (JSON serialization)
```json
{
    "arcs": [
        {
            "id": 1,
            "properties": {
                "threshold": "{'weight': 'max(1, P1/2)', 'threshold': 'P3 * 2'}"
            }
        }
    ]
}
```

## Evaluation Context

When evaluating formulas, the context includes:

```python
context = {
    'P1': 5,          # Place token counts (by name)
    'P2': 10,
    't': 42.5,        # Current simulation time
    'lambda_rate': 0.5,  # Named constants
    'np': numpy,      # NumPy module
    'math': math,     # Math module
    # Helper functions available directly:
    'sigmoid': sigmoid_func,
    'hill': hill_func,
    # etc.
}
```

## Implementation Plan for Current System

### Step 1: Add Properties to Net Objects

**Arc** (already has partial support):
```python
class Arc:
    def __init__(self, ...):
        self.threshold = None  # Can be string, dict, or expression
        self.properties = {}   # For additional formula properties
```

**Transition** (need to add):
```python
class Transition:
    def __init__(self, ...):
        self.guard = None  # Guard expression/dict ✅ ALREADY ADDED
        self.rate = None   # Rate expression/dict ✅ ALREADY ADDED
        self.properties = {}  # For additional properties
```

### Step 2: Update Dialog Loaders

**Arc Dialog Loader** (src/shypn/helpers/arc_prop_dialog_loader.py):
```python
def _populate_fields(self):
    # ... existing fields ...
    
    # Threshold field (TextView)
    threshold_textview = self.builder.get_object('threshold_textview')
    if threshold_textview and hasattr(self.arc_obj, 'threshold'):
        buffer = threshold_textview.get_buffer()
        threshold_text = self._format_for_display(self.arc_obj.threshold)
        buffer.set_text(threshold_text)

def _apply_changes(self):
    # ... existing fields ...
    
    # Threshold field
    threshold_textview = self.builder.get_object('threshold_textview')
    if threshold_textview:
        buffer = threshold_textview.get_buffer()
        start, end = buffer.get_bounds()
        text = buffer.get_text(start, end, True).strip()
        self.arc_obj.threshold = self._parse_formula(text)

def _format_for_display(self, value):
    """Format threshold for display in UI"""
    if value is None:
        return ""
    elif isinstance(value, dict):
        return json.dumps(value)
    else:
        return str(value)

def _parse_formula(self, text):
    """Parse formula text (can be dict string, expression, or number)"""
    if not text:
        return None
    
    try:
        # Try to parse as dictionary
        return ast.literal_eval(text)
    except:
        # Return as string (will be evaluated at runtime)
        return text
```

**Transition Dialog Loader** (src/shypn/helpers/transition_prop_dialog_loader.py):
- Already updated with guard and rate fields ✅
- Same pattern as arc threshold

### Step 3: Add Formula Evaluation System

Create `src/shypn/utils/formula_evaluator.py`:
```python
class FormulaEvaluator:
    """Evaluate formula expressions with context"""
    
    @staticmethod
    def evaluate(formula, context: Dict[str, Any]) -> Any:
        """
        Evaluate a formula (dict, expression, or value)
        
        Args:
            formula: Can be:
                - Number: returned as-is
                - String expression: "P1 * 2 + P2"
                - Dict: {"value": 5} or {"expr": "P1 * 2"}
            context: Runtime values (place tokens, time, etc.)
        
        Returns:
            Evaluated result
        """
        if formula is None:
            return None
        
        # Simple numeric value
        if isinstance(formula, (int, float)):
            return formula
        
        # Dictionary format
        if isinstance(formula, dict):
            if 'value' in formula:
                return formula['value']
            elif 'expr' in formula:
                return eval(formula['expr'], {"__builtins__": {}}, context)
            elif 'func' in formula:
                return eval(formula['func'], {"__builtins__": {}}, context)
        
        # String expression
        if isinstance(formula, str):
            try:
                # Try numeric conversion
                return float(formula)
            except:
                # Evaluate as expression
                return eval(formula, {"__builtins__": {}}, context)
        
        return formula
```

### Step 4: Update UI Files

Add threshold field to arc_prop_dialog.ui (if not present)
- Already has fields for weight, label, etc.
- Need to add threshold TextView/Entry

## Usage Examples

### Setting Threshold in UI

User opens arc properties and types:
```
{'threshold': 'P1 >= 5', 'weight': 'min(P1, P2)'}
```

When saved:
```python
arc.threshold = {'threshold': 'P1 >= 5', 'weight': 'min(P1, P2)'}
```

### Evaluating at Runtime

```python
from shypn.utils.formula_evaluator import FormulaEvaluator

context = {
    'P1': 7,
    'P2': 3
}

# Evaluate threshold condition
result = FormulaEvaluator.evaluate(arc.threshold['threshold'], context)
# result = True (since 7 >= 5)

# Evaluate weight
weight = FormulaEvaluator.evaluate(arc.threshold['weight'], context)
# weight = 3 (min of 7 and 3)
```

## Security Considerations

⚠️ **IMPORTANT**: Using `eval()` on user input is dangerous!

**Mitigation strategies**:
1. Use `ast.literal_eval()` for dictionary parsing (safe)
2. Restrict eval namespace (no __builtins__)
3. Whitelist allowed functions and modules
4. Validate expressions before evaluation
5. Sandbox execution environment

**Better alternative** (for future):
- Use a proper expression parser (e.g., `sympy`, `asteval`)
- Build safe AST evaluation system
- Implement formula validation with whitelist

## Next Steps

1. ✅ Add `threshold` property to Arc class
2. ✅ Add `guard` and `rate` properties to Transition class
3. ⏳ Add threshold field to arc_prop_dialog.ui
4. ⏳ Update arc_prop_dialog_loader.py to handle threshold
5. ⏳ Create formula_evaluator.py utility
6. ⏳ Add validation and error handling
7. ⏳ Test round-trip (save → load → edit → save)
8. ⏳ Add documentation and examples

## References

- Legacy implementation: `legacy/shypnpy/simple_formula_dictionary.py`
- Integration layer: `legacy/shypnpy/formula_integration.py`
- Test cases: `legacy/shypnpy/tests/test_threshold_dialog_roundtrip.py`
