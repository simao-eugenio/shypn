# Continuous Transition Minimum Threshold Fix

## Problem Description

### Symptom
Continuous transitions in imported SBML/KEGG models stop firing when token counts reach approximately 0.1, even though mathematically they should continue at lower rates.

### Root Cause
When continuous transitions have **Michaelis-Menten kinetics** or similar rate functions:
```
rate = P / (Km + P)
```

At low token values, the rate becomes very small:
- When `P = 0.1`, `Km = 0.1`: rate = 0.1 / 0.2 = 0.5
- When `P = 0.01`, `Km = 0.1`: rate = 0.01 / 0.11 ≈ 0.09
- When `P = 0.001`, `Km = 0.1`: rate = 0.001 / 0.101 ≈ 0.01

This creates two issues:
1. **Numerical precision**: Very small token flows can be lost to floating-point rounding
2. **Computational inefficiency**: Simulating infinitesimally small rates wastes CPU cycles

## Solution

### Implementation
Added `min_token_threshold` parameter to `ContinuousBehavior`:

**File**: `src/shypn/engine/continuous_behavior.py`

```python
# In __init__:
self.min_token_threshold = float(props.get('min_token_threshold', 0.0))

# In can_fire():
if source_place.tokens <= self.min_token_threshold:
    return False, f"input-place-below-threshold-P{arc.source_id}"

# In integrate_step():
effective_min_rate = max(self.min_rate, self.min_token_threshold * 1e-3)
if rate <= effective_min_rate:
    return True, {..., 'reason': 'rate-below-threshold'}
```

### Configuration

#### Default Behavior (No Change)
```python
# Transitions stop only at exactly 0 tokens
transition.properties = {
    'rate_function': 'P1 / (0.1 + P1)',
    'min_token_threshold': 0.0  # Default
}
```

#### Recommended for Imported Models
```python
# Stop when tokens drop below 0.01 (1% of typical initial marking)
transition.properties = {
    'rate_function': 'P1 / (0.1 + P1)',
    'min_token_threshold': 0.01
}
```

#### For High-Precision Simulations
```python
# Only prevent floating-point underflow
transition.properties = {
    'rate_function': 'P1 / (0.1 + P1)',
    'min_token_threshold': 1e-10
}
```

## Usage Examples

### Example 1: Interactive Model
For the Interactive.shy model with Michaelis-Menten rates:

**Before** (transitions slow to crawl at 0.1 tokens):
```
T1: rate = P2 / (0.1 + P2)
T2: rate = P4 / (0.1 + P4)
T3: rate = P1 / (0.1 + P1)
T4: rate = P3 / (0.1 + P3)
```

**After** (transitions stop cleanly at 0.1 tokens):
```python
for transition in [T1, T2, T3, T4]:
    transition.properties['min_token_threshold'] = 0.1
```

### Example 2: SBML Import
For SBML models with complex kinetics:

```python
# During SBML import, automatically set threshold
# based on initial marking statistics

def import_sbml(sbml_file):
    model = parse_sbml(sbml_file)
    
    # Calculate average initial marking
    avg_marking = sum(p.initial_marking for p in model.places) / len(model.places)
    
    # Set threshold to 1% of average
    threshold = avg_marking * 0.01
    
    for transition in model.transitions:
        if transition.transition_type == 'continuous':
            transition.properties['min_token_threshold'] = threshold
    
    return model
```

### Example 3: Manual Configuration
For specific transitions that need higher thresholds:

```python
# T1 handles enzyme catalysis - stop below 0.5 nM
t1.properties['min_token_threshold'] = 0.5

# T2 handles diffusion - continue to near zero
t2.properties['min_token_threshold'] = 1e-6
```

## Testing

### Test Case 1: Verify Threshold Works
```python
def test_min_token_threshold():
    # Create model with threshold
    p1 = Place(id=1, tokens=1.0)
    t1 = Transition(id=1, transition_type='continuous')
    t1.properties = {
        'rate_function': 'P1',
        'min_token_threshold': 0.1
    }
    p2 = Place(id=2, tokens=0.0)
    
    model.add_arc(p1, t1)
    model.add_arc(t1, p2)
    
    behavior = ContinuousBehavior(t1, model)
    controller = SimulationController(model)
    
    # Run until threshold reached
    while p1.tokens > 0.1:
        controller.step(0.01)
    
    # Should stop at threshold
    assert p1.tokens >= 0.1, "Should stop at threshold"
    assert p1.tokens < 0.15, "Should stop near threshold"
    
    # Should be disabled
    can_fire, reason = behavior.can_fire()
    assert not can_fire, "Should be disabled below threshold"
    assert 'threshold' in reason
```

### Test Case 2: Interactive Model Convergence
```python
def test_interactive_model_threshold():
    model = load_model('workspace/projects/Interactive/models/Interactive.shy')
    
    # Set thresholds on all continuous transitions
    for t in model.transitions:
        if t.transition_type == 'continuous':
            t.properties['min_token_threshold'] = 0.1
    
    controller = SimulationController(model)
    
    # Run simulation
    for _ in range(1000):
        controller.step(0.01)
    
    # Check all places either above threshold or at zero
    for p in model.places:
        if p.tokens > 0:
            # If any continuous transition uses this place, check threshold
            for t in model.transitions:
                if t.transition_type == 'continuous':
                    for arc in model.arcs:
                        if arc.source_id == p.id and arc.target_id == t.id:
                            assert p.tokens >= 0.1, \
                                f"Place {p.id} should be above threshold"
```

## Benefits

### 1. Prevents Numerical Issues
- Avoids floating-point underflow
- Eliminates infinitesimally small token flows
- Reduces rounding errors

### 2. Improves Performance
- Stops wasteful computation of negligible flows
- Reduces simulation time for models with many continuous transitions
- Allows larger time steps near equilibrium

### 3. Preserves Correctness
- Default threshold = 0.0 maintains exact behavior
- Higher thresholds are scientifically justified (below detection limits)
- User has full control over tradeoff

## Migration Guide

### For Existing Models
No changes required! Default threshold = 0.0 preserves exact behavior.

### For Imported SBML Models
Add this to your SBML importer:

```python
# In sbml_importer.py, after creating transitions:

# Calculate threshold based on model statistics
min_marking = min(p.initial_marking for p in model.places if p.initial_marking > 0)
threshold = min_marking * 0.01  # 1% of smallest initial marking

for transition in model.transitions:
    if transition.transition_type == 'continuous':
        if 'min_token_threshold' not in transition.properties:
            transition.properties['min_token_threshold'] = threshold
```

### For Interactive Testing
Add threshold configuration to property dialogs:

```python
# In transition_rate_panel.py:

self.threshold_entry = Gtk.Entry()
self.threshold_entry.set_text(str(props.get('min_token_threshold', 0.0)))
self.threshold_entry.set_placeholder_text("0.0 = strict zero, 0.1 = practical threshold")

# On save:
props['min_token_threshold'] = float(self.threshold_entry.get_text())
```

## References

- **Numerical Precision**: [IEEE 754 floating-point standard](https://en.wikipedia.org/wiki/IEEE_754)
- **Michaelis-Menten Kinetics**: [Enzyme Kinetics](https://en.wikipedia.org/wiki/Michaelis%E2%80%93Menten_kinetics)
- **Continuous Petri Nets**: [Hybrid Petri Nets](https://en.wikipedia.org/wiki/Hybrid_Petri_net)

## Changelog

### 2025-11-01
- ✅ Added `min_token_threshold` parameter to `ContinuousBehavior`
- ✅ Updated `can_fire()` to check threshold
- ✅ Updated `integrate_step()` to skip negligible rates
- ✅ Default threshold = 0.0 (no behavior change)
- ✅ Documented usage and testing
