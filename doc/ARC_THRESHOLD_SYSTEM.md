# Arc Threshold System - Advanced Weight Specification

## Overview

SHYPN provides a **flexible threshold system** for arc weights, supporting three specification methods:

1. **Simple Numeric** (via `weight` property) - Fixed integer values
2. **Expression** (via `threshold` property) - Dynamic formulas
3. **Function** (via `threshold` property) - Complex computational logic

This enables both simple fixed-weight models and sophisticated adaptive cooperation systems.

## Architecture

### Properties

Every Arc object has two threshold-related properties:

```python
class Arc:
    def __init__(self, source, target, id, name, weight=1):
        self.weight = weight        # Default: dual purpose (enablement + consumption)
        self.threshold = None       # When set: SUPERSEDES weight for enablement
```

### Critical Behavior: Threshold Supersedes Weight

**The `threshold` property OVERRIDES `weight` for enablement checking when specified.**

| Property Set | Enablement Check Uses | Token Consumption Uses |
|--------------|----------------------|------------------------|
| Only `weight` | `weight` | `weight` |
| Only `threshold` | `threshold` *(supersedes default weight=1!)* | `weight` (default=1) |
| Both `weight` and `threshold` | `threshold` *(supersedes weight!)* | `weight` |

**Examples:**

```python
# Case 1: Only weight (traditional)
arc.weight = 5
arc.threshold = None
# → Enablement: tokens >= 5
# → Consumption: 5 tokens

# Case 2: Only threshold (supersedes default weight=1!)
arc.weight = 1  # default
arc.threshold = "P1.tokens * 0.3"
# → Enablement: tokens >= P1.tokens * 0.3  (NOT >= 1!)
# → Consumption: 1 token

# Case 3: Both (threshold supersedes weight for enablement)
arc.weight = 10
arc.threshold = "P1.tokens * 0.5"
# → Enablement: tokens >= P1.tokens * 0.5  (NOT >= 10!)
# → Consumption: 10 tokens
```

**Why This Design?**

1. **Backward Compatibility**: Existing models with only `weight` work as before
2. **Separation of Concerns**: Different logic for "when to fire" vs "how much to transfer"
3. **Flexibility**: Can have low consumption (weight=1) but high threshold (30% of capacity)
4. **Living Systems**: Natural modeling of "maintain reserves but transfer small amounts"

### Evaluation Priority

**When `threshold` is specified, it SUPERSEDES the `weight` property.**

During enablement checking:
```python
if arc.threshold is not None:
    # Threshold OVERRIDES weight completely
    effective_weight = evaluate_threshold(arc.threshold, context)
else:
    # Fallback to simple numeric weight (default=1)
    effective_weight = arc.weight
```

**Important**: 
- `arc.weight` is used for **token consumption** (always)
- `arc.threshold` (when set) is used for **enablement checking** (overrides weight)
- If only `weight` is set, it serves both purposes
- If both are set, they serve different purposes:
  - `weight` → how many tokens to consume
  - `threshold` → when to enable (supersedes weight for enablement)

## Method 1: Simple Numeric (weight)

The standard approach for fixed thresholds. When only `weight` is specified, it serves dual purpose:
- **Enablement**: Check if `tokens >= weight`
- **Consumption**: Consume `weight` tokens on firing

```python
# Place→Transition inhibitor arc (default weight=1)
arc = InhibitorArc(source=place, target=transition)
# Enablement: tokens >= 1, Consumption: 1 token

# With explicit weight
arc = InhibitorArc(source=place, target=transition, weight=5)
# Enablement: tokens >= 5, Consumption: 5 tokens
```

**Use Cases:**
- Fixed cooperation thresholds
- Simple resource management
- Standard Petri net models
- Quick prototyping

**Example:**
```python
food_storage = Place(tokens=100)
share_transition = Transition(behavior="immediate")
arc = InhibitorArc(food_storage, share_transition, weight=20)

# Result: 
# - Enable when: storage >= 20 units
# - Consume: 20 units per firing
```

## Method 2: Expression (threshold)

Dynamic formulas evaluated at runtime based on current system state.

**When `threshold` is set, it SUPERSEDES `weight` for enablement checking.**

```python
# Default: weight=1 used for enablement AND consumption
arc = InhibitorArc(source=place, target=transition)

# Set threshold: OVERRIDES weight for enablement
arc.threshold = "P1.tokens * 0.3"  # String expression

# Result:
# - Enablement: place.tokens >= evaluate("P1.tokens * 0.3")  [threshold supersedes!]
# - Consumption: 1 token (weight still used for consumption)
```

**Key Behavior:**
- `threshold` expression **replaces** the default `weight=1` for enablement
- `weight` is still used for token consumption
- This separates enablement logic from consumption amount

**Expression Syntax:**
- Place references: `P1.tokens`, `P2.tokens`, etc.
- Operators: `+`, `-`, `*`, `/`, `**` (power)
- Functions: `min()`, `max()`, `abs()`, `round()`
- Constants: Numeric literals

**Use Cases:**
- Proportional reserve requirements
- Adaptive cooperation based on system state
- Dynamic resource management
- Multi-place dependencies

**Examples:**

### Example 1: Proportional Reserve
```python
# Energy system: maintain 30% reserve
arc = InhibitorArc(energy_place, share_transition, weight=1)
arc.threshold = "Energy.tokens * 0.3"

# At 100 tokens → threshold = 30 → enabled if tokens >= 30
# At 50 tokens  → threshold = 15 → enabled if tokens >= 15
# Consumption: 1 token per firing (weight=1)
# 
# Note: threshold SUPERSEDES the default weight=1 for enablement!
```

### Example 2: Multi-Place Dependency
```python
# Share only if both sources have surplus
arc.threshold = "min(P1.tokens * 0.5, P2.tokens * 0.5)"

# Threshold adapts to weakest link
```

### Example 3: Conditional Reserve
```python
# Higher reserve when system is stressed
arc.threshold = "P1.tokens * (0.2 if P2.tokens > 50 else 0.5)"

# P2 healthy (>50) → 20% reserve
# P2 stressed (≤50) → 50% reserve (higher protection)
```

## Method 3: Function (threshold)

Complex computational logic using dictionary specification.

**When `threshold` function is set, it SUPERSEDES `weight` for enablement.**

```python
arc = InhibitorArc(source=place, target=transition, weight=1)
arc.threshold = {
    "type": "function",
    "formula": "lambda P1, P2, P3: (P1.tokens + P2.tokens) / P3.tokens",
    "dependencies": ["P1", "P2", "P3"]
}

# Result:
# - Enablement: uses function result (threshold supersedes weight=1!)
# - Consumption: 1 token (weight still used)
```

**Use Cases:**
- Complex multi-factor calculations
- Statistical aggregations
- State-dependent logic
- Advanced cooperation strategies

**Examples:**

### Example 1: Average-Based Threshold
```python
arc.threshold = {
    "type": "function",
    "formula": "lambda places: sum(p.tokens for p in places) / len(places)",
    "dependencies": ["P1", "P2", "P3", "P4"]
}

# Share only if above system average
```

### Example 2: Weighted Cooperation
```python
arc.threshold = {
    "type": "function",
    "formula": """
        lambda P1, P2, priority:
            P1.tokens * 0.3 if priority == 'high' else P1.tokens * 0.5
    """,
    "dependencies": ["P1", "P2"],
    "parameters": {"priority": "high"}
}
```

### Example 3: Time-Dependent Reserve
```python
arc.threshold = {
    "type": "function",
    "formula": "lambda P1, time: P1.tokens * (0.5 + 0.3 * sin(time / 100))",
    "dependencies": ["P1"],
    "parameters": {"time": "simulation.time"}
}

# Cyclic reserve requirement (biological rhythms)
```

## Implementation Details

### Evaluation Engine

The threshold system requires an evaluation engine (to be implemented):

```python
class ThresholdEvaluator:
    def __init__(self, model):
        self.model = model  # Access to all places/transitions
    
    def evaluate(self, threshold, context):
        """Evaluate threshold specification.
        
        Args:
            threshold: Expression string or function dict
            context: Current simulation state
        
        Returns:
            float: Evaluated threshold value
        """
        if isinstance(threshold, str):
            return self._evaluate_expression(threshold, context)
        elif isinstance(threshold, dict):
            return self._evaluate_function(threshold, context)
        else:
            raise ValueError(f"Invalid threshold type: {type(threshold)}")
    
    def _evaluate_expression(self, expr, context):
        # Parse and evaluate string expression
        # Access places: P1.tokens, P2.tokens, etc.
        pass
    
    def _evaluate_function(self, func_spec, context):
        # Execute function with dependencies
        pass
```

### Integration with Enablement Check

Update `_check_enablement_manual()` to support threshold evaluation:

```python
def _check_enablement_manual(self) -> bool:
    """Check enablement with threshold evaluation support."""
    for arc in self.get_input_arcs():
        source_place = arc.source
        
        # Determine effective threshold
        if arc.threshold is not None:
            # Dynamic threshold
            evaluator = ThresholdEvaluator(self.get_model())
            effective_threshold = evaluator.evaluate(arc.threshold, self.context)
        else:
            # Simple numeric weight
            effective_threshold = arc.weight
        
        # Living systems semantics: all arcs check surplus
        if source_place.tokens < effective_threshold:
            return False
    
    return True
```

## Use Case Scenarios

### Scenario 1: Fixed Reserve System
```python
# Simple: Food storage with 20-unit minimum
food = Place(tokens=100)
share = Transition()
arc = InhibitorArc(food, share, weight=20)

# Result: 
# - Enable when: food >= 20
# - Consume: 20 tokens per firing
# (weight serves both purposes when threshold not set)
```

### Scenario 2: Proportional Reserve System
```python
# Adaptive: Maintain 25% reserve
energy = Place(tokens=100)
consume = Transition()
arc = InhibitorArc(energy, consume, weight=1)  # Consume 1 per firing
arc.threshold = "Energy.tokens * 0.25"  # SUPERSEDES weight=1 for enablement!

# At 100 tokens:
#   - Threshold = 25 (not 1!)
#   - Enable when >= 25
#   - Can fire 75 times (consuming 1 each)
# At 40 tokens:
#   - Threshold = 10
#   - Enable when >= 10
#   - Can fire 30 times
```

### Scenario 3: Multi-Source Cooperation
```python
# Complex: Share when both sources healthy
p1 = Place(tokens=50)
p2 = Place(tokens=30)
share = Transition()
arc = InhibitorArc(p1, share, weight=1)
arc.threshold = {
    "type": "function",
    "formula": "lambda P1, P2: min(P1.tokens * 0.3, P2.tokens * 0.5)",
    "dependencies": ["P1", "P2"]
}

# Threshold adapts to weakest link
```

### Scenario 4: Emergency Override
```python
# Conditional: Lower reserve in emergencies
supply = Place(tokens=100)
emergency_flag = Place(tokens=0)  # 0=normal, 1=emergency
distribute = Transition()
arc = InhibitorArc(supply, distribute, weight=1)
arc.threshold = "Supply.tokens * (0.1 if Emergency.tokens > 0 else 0.5)"

# Normal: 50% reserve
# Emergency: 10% reserve (more sharing)
```

## Benefits of Threshold System

### 1. **Simplicity for Simple Cases**
Fixed weights work out-of-the-box: `weight=5`

### 2. **Flexibility for Complex Cases**
Dynamic thresholds enable sophisticated behaviors without code changes

### 3. **Declarative Modeling**
Express cooperation logic directly in the model (not hardcoded)

### 4. **Runtime Adaptation**
Thresholds adjust automatically based on system state

### 5. **Biological Realism**
Mimics adaptive strategies in living systems

## Testing Recommendations

### Test 1: Simple Numeric
```python
arc.weight = 5
assert evaluate_threshold(arc) == 5
```

### Test 2: Expression Evaluation
```python
P1.tokens = 100
arc.threshold = "P1.tokens * 0.3"
assert evaluate_threshold(arc) == 30
```

### Test 3: Function Evaluation
```python
P1.tokens = 50
P2.tokens = 30
arc.threshold = {"type": "function", "formula": "lambda P1, P2: (P1.tokens + P2.tokens) / 2"}
assert evaluate_threshold(arc) == 40  # (50+30)/2
```

### Test 4: Threshold Supersedes Weight
```python
# When threshold is None, use weight
arc.weight = 10
arc.threshold = None
assert evaluate_threshold(arc) == 10

# When threshold is set, it SUPERSEDES weight
arc.weight = 10  # Only used for consumption now
arc.threshold = "P1.tokens * 0.5"  # OVERRIDES weight=10 for enablement
# If P1.tokens = 100, threshold = 50 (not 10!)
```

## Implementation Status (Foundation-Testing Branch)

| Component | Status | Location | Notes |
|-----------|--------|----------|-------|
| **Arc `threshold` property** | ✅ Exists | Arc base class | Property defined but not evaluated |
| **Fixed numeric thresholds** | ✅ Working | Via `weight` property | Default behavior |
| **Expression-based thresholds** | 📝 Documented | This file | Awaiting implementation |
| **Function-based thresholds** | 📝 Documented | This file | Awaiting implementation |
| **ThresholdEvaluator class** | ⏳ To implement | `src/shypn/utils/` | See Phase 1 below |
| **Engine integration** | ⏳ To implement | `transition_behavior.py` | See Phase 2 below |
| **JSON serialization** | ⏳ To implement | Model loaders | See Phase 3 below |
| **UI threshold editor** | ⏳ To implement | Properties dialog | See Phase 4 below |
| **Test suite** | ⏳ To implement | `tests/` | See Phase 5 below |

**Related Documentation**:
- Multi-level inhibition: `doc/foundation/DUAL_LAYER_INHIBITION.md` (Section 6)
- Inhibitor arc logic: `doc/INHIBITOR_ARC_SIMULATION_LOGIC.md`
- Continuous behavior: `doc/CONTINUOUS_TRANSITION_RATE_FUNCTIONS.md`

## Implementation Roadmap

### Phase 1: Core Threshold Evaluator (Priority: HIGH)

**Create**: `src/shypn/utils/threshold_evaluator.py`

**Purpose**: Evaluate dynamic thresholds with expression/function support

**Key Features**:
- Parse string expressions (`"4.0 * (1.0 + AMP / 0.1)"`)
- Execute lambda functions with dependencies
- Resolve place references (P1, P2, names)
- Safe evaluation context (no arbitrary code execution)
- Caching for repeated expressions

**Implementation Outline**:
```python
class ThresholdEvaluator:
    def __init__(self, model):
        self.model = model
        self._expression_cache = {}
    
    def evaluate(self, arc, context: Dict) -> float:
        """Returns effective threshold (supersedes weight if threshold set)."""
        if arc.threshold is None:
            return arc.weight  # Backward compatible
        
        if isinstance(arc.threshold, (int, float)):
            return float(arc.threshold)
        elif isinstance(arc.threshold, str):
            return self._evaluate_expression(arc.threshold, context)
        elif isinstance(arc.threshold, dict):
            return self._evaluate_function(arc.threshold, context)
        else:
            raise ValueError(f"Invalid threshold type")
    
    def _evaluate_expression(self, expr: str, context: Dict) -> float:
        # Build context: places (P1, P2, names), time, math functions
        # Use eval() with restricted builtins
        pass
    
    def _evaluate_function(self, func_spec: Dict, context: Dict) -> float:
        # Extract formula, dependencies
        # Resolve dependencies to place objects
        # Execute lambda
        pass
```

**Dependencies**: None (pure Python, uses standard library)

**Testing**: Unit tests in `tests/utils/test_threshold_evaluator.py`

### Phase 2: Engine Integration (Priority: HIGH)

**Modify**: `src/shypn/engine/transition_behavior.py`

**Changes**:
1. Import `ThresholdEvaluator` in `_check_enablement_manual()`
2. Create evaluator instance with model reference
3. Replace `arc.weight` with `evaluator.evaluate(arc, context)`
4. Preserve backward compatibility (threshold=None → use weight)

**Code Changes**:
```python
def _check_enablement_manual(self) -> bool:
    from shypn.utils.threshold_evaluator import ThresholdEvaluator
    
    evaluator = ThresholdEvaluator(self.model)
    context = {'time': self._get_current_time()}
    
    for arc in input_arcs:
        effective_threshold = evaluator.evaluate(arc, context)  # NEW
        
        if isinstance(arc, InhibitorArc):
            if source_place.tokens >= effective_threshold:  # Was arc.weight
                return False
        # ... rest of checks
```

**Also Update**:
- `continuous_behavior.py:can_fire()` (line 404-419) - inhibitor arc checks
- `immediate_behavior.py` - if custom enablement exists
- `timed_behavior.py` - if custom enablement exists
- `stochastic_behavior.py` - if custom enablement exists

**Testing**: Integration tests in `tests/engine/test_threshold_evaluation.py`

### Phase 3: File Format Support (Priority: MEDIUM)

**Modify**: `src/shypn/io/model_canvas_loader.py`

**Add to `_arc_to_dict()`**:
```python
def _arc_to_dict(self, arc) -> dict:
    data = {
        # ... existing fields ...
        'weight': arc.weight,
    }
    
    # NEW: Serialize threshold if present
    if hasattr(arc, 'threshold') and arc.threshold is not None:
        data['threshold'] = arc.threshold
    
    return data
```

**Add to `_dict_to_arc()`**:
```python
def _dict_to_arc(self, data: dict, places, transitions):
    # ... existing arc creation ...
    
    # NEW: Deserialize threshold
    if 'threshold' in data:
        arc.threshold = data['threshold']
        # Validate threshold format
        self._validate_threshold(arc.threshold)
    
    return arc
```

**Validation**:
```python
def _validate_threshold(self, threshold_spec) -> bool:
    """Validate threshold specification on load."""
    if isinstance(threshold_spec, (int, float)):
        return threshold_spec >= 0
    elif isinstance(threshold_spec, str):
        try:
            compile(threshold_spec, '<threshold>', 'eval')
            return True
        except SyntaxError:
            raise ValueError(f"Invalid threshold expression: {threshold_spec}")
    elif isinstance(threshold_spec, dict):
        required = {'type', 'formula'}
        if not required.issubset(threshold_spec.keys()):
            raise ValueError(f"Threshold function missing required keys: {required}")
        return True
    return False
```

**Testing**: File I/O tests in `tests/io/test_threshold_persistence.py`

### Phase 4: UI Properties Dialog (Priority: LOW)

**Modify**: `src/shypn/ui/properties/arc_properties.py` (or similar)

**Add Threshold Editor Panel**:
```python
class ArcPropertiesDialog:
    def _build_threshold_section(self):
        # Threshold type selector
        self.threshold_type = ComboBoxText()
        self.threshold_type.append_text("Use weight (default)")
        self.threshold_type.append_text("Expression")
        self.threshold_type.append_text("Function")
        
        # Expression editor
        self.expression_entry = Entry()
        self.expression_entry.set_placeholder_text("4.0 * (1.0 + AMP / 0.1)")
        
        # Place name autocomplete
        self.place_completion = EntryCompletion()
        # Populate with available place names
        
        # Real-time validation
        self.expression_entry.connect('changed', self._validate_threshold)
        
        # Preview evaluation
        self.preview_button = Button("Test Evaluation")
        self.preview_button.connect('clicked', self._preview_threshold)
    
    def _validate_threshold(self, entry):
        """Show validation status."""
        expr = entry.get_text()
        try:
            compile(expr, '<threshold>', 'eval')
            self.validation_icon.set_from_icon_name("emblem-ok")
        except SyntaxError as e:
            self.validation_icon.set_from_icon_name("dialog-error")
            self.validation_label.set_text(str(e))
```

**Testing**: UI tests (manual or automated with GTK test framework)

### Phase 5: Comprehensive Testing (Priority: MEDIUM)

**Test Files**:
1. `tests/utils/test_threshold_evaluator.py` - Evaluator unit tests
2. `tests/engine/test_threshold_integration.py` - Engine integration tests
3. `tests/io/test_threshold_persistence.py` - File I/O tests
4. `tests/examples/test_dynamic_threshold_models.py` - Example models

**Test Coverage**:
- ✅ Fixed numeric thresholds
- ✅ Expression evaluation (place references, math functions)
- ✅ Function evaluation (dependencies, lambdas)
- ✅ Threshold supersedes weight for enablement
- ✅ Weight still used for consumption
- ✅ Backward compatibility (threshold=None)
- ✅ Error handling (invalid expressions, missing places)
- ✅ Persistence (save/load with threshold)

## Next Steps Summary

1. **Implement ThresholdEvaluator** (`src/shypn/utils/threshold_evaluator.py`)
   - Expression parser with place resolution
   - Function executor with dependency injection
   - Safe evaluation context

2. **Integrate with Engine** (`src/shypn/engine/transition_behavior.py`)
   - Modify `_check_enablement_manual()` to use evaluator
   - Update all behavior classes (continuous, immediate, timed, stochastic)

3. **Add File Format Support** (`src/shypn/io/model_canvas_loader.py`)
   - Serialize/deserialize threshold property
   - Validation on load

4. **Build UI Editor** (properties dialog)
   - Threshold specification interface
   - Syntax validation and preview

5. **Create Test Suite**
   - Unit, integration, and example tests
   - Document test models demonstrating features

**Estimated Effort**: 2-3 days for full implementation and testing
   - Example library
   - Best practices

## Conclusion

SHYPN's threshold system provides powerful flexibility for modeling cooperation and resource management in living systems. The three-tier approach (numeric → expression → function) enables both simple prototyping and sophisticated adaptive behaviors, making SHYPN uniquely suited for biological, ecological, and organic system modeling.
