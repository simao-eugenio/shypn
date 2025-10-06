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

## Implementation Status

- ✅ **Data Structure**: `threshold` property exists in Arc class
- ✅ **Documentation**: Comprehensive guides created
- ⏳ **Evaluation Engine**: Needs implementation
- ⏳ **Integration**: Update enablement logic
- ⏳ **UI Support**: Properties dialog for threshold editing
- ⏳ **Testing**: Comprehensive test suite

## Next Steps

1. **Implement ThresholdEvaluator class**
   - Expression parser
   - Function executor
   - Context management

2. **Update Enablement Logic**
   - Integrate threshold evaluation in `_check_enablement_manual()`
   - Support all transition behaviors

3. **UI Integration**
   - Add threshold field to arc properties dialog
   - Expression syntax highlighting
   - Validation and preview

4. **Testing**
   - Unit tests for evaluator
   - Integration tests with simulation
   - Example models demonstrating features

5. **Documentation**
   - User guide for threshold syntax
   - Example library
   - Best practices

## Conclusion

SHYPN's threshold system provides powerful flexibility for modeling cooperation and resource management in living systems. The three-tier approach (numeric → expression → function) enables both simple prototyping and sophisticated adaptive behaviors, making SHYPN uniquely suited for biological, ecological, and organic system modeling.
