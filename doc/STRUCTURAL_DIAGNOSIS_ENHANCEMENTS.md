# Structural Diagnosis Enhancements

## Overview
Enhanced structural category with **intelligent Petri net diagnosis** providing specific, actionable suggestions.

## New Diagnosis Engine

### `_diagnose_dead_transition(kb, trans_id)`
Smart analyzer that determines **WHY** a transition is dead and suggests **specific fixes**.

## Diagnosis Categories

### 1️⃣ **Source Transitions (No Inputs)**
**Detection**: Transition has no input arcs
**Cause**: Missing firing rate
**Suggestion**:
```python
{
    'action': 'check_rate',
    'parameters': {'transition_id': 'T6', 'suggested_rate': 1.0},
    'reasoning': 'Source transitions need firing rate > 0 to generate tokens'
}
```

### 2️⃣ **Input Places Empty**
**Detection**: One or more input places have 0 tokens
**Cause**: No initial marking
**Suggestion**:
```python
{
    'action': 'add_initial_marking',
    'parameters': {
        'place_ids': ['P5', 'P7'],
        'tokens': 2  # Matches maximum arc weight
    },
    'reasoning': 'Input places P5, P7 have 0 tokens (need ≥ 2)'
}
```

### 3️⃣ **Insufficient Tokens vs Arc Weights**
**Detection**: Place has tokens but less than arc weight requires
**Cause**: Stoichiometry mismatch
**Suggestions** (multiple options):

**Option A - Add Tokens**:
```python
{
    'action': 'add_initial_marking',
    'parameters': {'place_id': 'P5', 'tokens': 3},
    'reasoning': 'Place P5 has 2 tokens but needs 5 (add 3)'
}
```

**Option B - Reduce Arc Weight**:
```python
{
    'action': 'reduce_arc_weight',
    'parameters': {
        'arc_id': 'P5→T6',
        'from_weight': 5,
        'to_weight': 2
    },
    'reasoning': 'Reduce arc weight from 5 to 2 to match available tokens'
}
```

### 4️⃣ **High Arc Weights**
**Detection**: Arc weights > 1 (potential stoichiometry issue)
**Cause**: Incorrect biological stoichiometry or modeling error
**Suggestion**:
```python
{
    'action': 'reduce_arc_weight',
    'parameters': {
        'arc_id': 'P5→T6',
        'from_weight': 10,
        'to_weight': 1
    },
    'reasoning': 'Arc weight 10 is high - verify stoichiometry or reduce to 1'
}
```

### 5️⃣ **Priority Conflicts**
**Detection**: Multiple transitions competing for same input tokens
**Cause**: Another transition always fires first, consuming tokens
**Suggestions** (multiple options):

**Option A - Increase Target Priority**:
```python
{
    'action': 'adjust_priority',
    'parameters': {
        'transition_id': 'T6',
        'from_priority': 0,
        'to_priority': 10,
        'reason': 'competing_with_T12'
    },
    'reasoning': 'Increase priority to fire before competing transition T12'
}
```

**Option B - Decrease Competitor Priority**:
```python
{
    'action': 'adjust_priority',
    'parameters': {
        'transition_id': 'T12',
        'from_priority': 0,
        'to_priority': -10,
        'reason': 'yield_to_T6'
    },
    'reasoning': 'Reduce priority of T12 to let T6 fire first'
}
```

### 6️⃣ **Unknown Cause**
**Detection**: Has tokens, no obvious issue
**Cause**: Complex interaction (rates, timing, guards)
**Suggestion**:
```python
{
    'action': 'add_initial_marking',
    'parameters': {'place_id': 'P5', 'tokens': 5},
    'reasoning': 'General suggestion: add tokens to enable firing',
    'confidence': 0.5  # Low confidence
}
```

## Helper Functions

### `_find_competing_transitions(kb, trans_id, input_arcs)`
Identifies transitions that compete for same input tokens by:
1. Finding shared input places
2. Returning list of competitor IDs

## Confidence Scoring

Each suggestion includes confidence level:
- **0.9** - High confidence (clear diagnosis, e.g., zero tokens)
- **0.7-0.8** - Medium confidence (multiple possible fixes)
- **0.5-0.6** - Low confidence (uncertain cause)

## Actions Defined

New action types for Petri net modifications:
1. `add_initial_marking` - Add tokens to place(s)
2. `reduce_arc_weight` - Modify arc weight
3. `adjust_priority` - Change transition priority
4. `check_rate` - Verify/set firing rate

## Future Enhancements

### Guard Conditions
```python
{
    'action': 'modify_guard',
    'parameters': {
        'transition_id': 'T6',
        'guard_expression': 'P5 > 10',
        'suggested_change': 'P5 > 5'
    },
    'reasoning': 'Guard condition too restrictive - reduce threshold'
}
```

### Inhibitor Arcs
```python
{
    'action': 'adjust_inhibitor',
    'parameters': {
        'arc_id': 'P10⊸T6',
        'from_threshold': 5,
        'to_threshold': 10
    },
    'reasoning': 'Inhibitor arc threshold too low - increase to allow firing'
}
```

### Reset Arcs
```python
{
    'action': 'remove_reset_arc',
    'parameters': {'arc_id': 'T6⇢P5'},
    'reasoning': 'Reset arc may be preventing proper token flow'
}
```

## Example Output

**Before** (generic):
```
❌ Transition T6 is DEAD
   → Add 5 tokens to input place
```

**After** (specific):
```
❌ Transition T6 is DEAD: Insufficient tokens
   Place P5 has 2 tokens but arc requires 5
   
   Option 1: Add 3 tokens to P5 (confidence: 70%)
   Option 2: Reduce arc weight from 5 to 2 (confidence: 80%) ⭐
   Option 3: Check if competing transition T12 has higher priority
```

## Benefits

1. ✅ **Actionable** - Specific parameters (not "fix this")
2. ✅ **Multiple options** - User can choose best approach
3. ✅ **Root cause analysis** - Explains WHY it's dead
4. ✅ **Confidence scoring** - Shows reliability of diagnosis
5. ✅ **Petri net aware** - Uses proper PN concepts (priority, weights, etc.)
