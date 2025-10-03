"""
Petri Net Connection Rules
===========================

This document describes the fundamental connection rules for Petri nets
as learned from the legacy implementation and enforced in the current codebase.

## Bipartite Graph Property

Petri nets are **bipartite graphs**, meaning they consist of two disjoint sets of nodes:
1. **Places** (P): Circular nodes representing conditions/states
2. **Transitions** (T): Rectangular nodes representing events/actions

## Valid Connections

Arcs can ONLY connect between these two sets:

### Place → Transition (P→T)
- **Source**: Place
- **Target**: Transition
- **Meaning**: Input arc - place provides tokens to enable the transition
- **Example**: P1 → T1 (Place P1 feeds into Transition T1)

### Transition → Place (T→P)
- **Source**: Transition  
- **Target**: Place
- **Meaning**: Output arc - transition produces tokens in the place
- **Example**: T1 → P2 (Transition T1 outputs to Place P2)

## Invalid Connections

The following connections are **NOT allowed**:

❌ **Place → Place (P→P)**: Places cannot connect directly to other places
❌ **Transition → Transition (T→T)**: Transitions cannot connect directly to other transitions

## Connection Validation

The Arc class validates connections during creation:

```python
# Valid examples:
arc1 = Arc(source=place1, target=transition1, ...)  # P→T ✓
arc2 = Arc(source=transition1, target=place2, ...)   # T→P ✓

# Invalid examples (would raise ValueError):
arc3 = Arc(source=place1, target=place2, ...)        # P→P ✗
arc4 = Arc(source=transition1, target=transition2, ...) # T→T ✗
```

## Implementation Reference

From `legacy/shypnpy/core/model.py` (lines 103-120):

```python
def add_arc(self, source_id: int, target_id: int, weight: int = 1) -> Arc:
    if source_id not in self.places and source_id not in self.transitions:
        raise ValueError("Invalid source id")
    if target_id not in self.places and target_id not in self.transitions:
        raise ValueError("Invalid target id")
    
    # Enforce bipartite property
    src_is_place = source_id in self.places
    tgt_is_place = target_id in self.places
    if src_is_place == tgt_is_place:
        raise ValueError("Arcs must connect place to transition")
    
    # Create arc...
```

The key insight: `if src_is_place == tgt_is_place` checks that source and target
are of **different types**. If both are places or both are transitions, the
connection is invalid.

## Special Arc Types

### InhibitorArc
Inherits from Arc and follows the same connection rules:
- Typically **Place → Transition** (P→T)
- Prevents transition from firing when source place has tokens
- Rendered with circular marker instead of arrowhead

### Arc Weight
- All arcs have a weight (multiplicity) property
- Default weight: 1
- Weight determines how many tokens are consumed/produced

## Visual Representation

```
  ┌─────┐
  │  P1 │  (Place - Circle)
  └──┬──┘
     │ (Arc with arrowhead)
     ↓
  ┌─────┐
  │  T1 │  (Transition - Rectangle)
  └──┬──┘
     │ (Arc with arrowhead)
     ↓
  ┌─────┐
  │  P2 │  (Place - Circle)
  └─────┘
```

## Default Colors

All objects use **black** as the primary color:
- **Place**: White fill, black border (2.0 width)
- **Transition**: Black fill, black border (1.0 width)
- **Arc**: Black line (3.0 width)
- **InhibitorArc**: Black line (3.0 width) with black-bordered circular marker

## Summary

✓ Place → Transition (valid)
✓ Transition → Place (valid)
✗ Place → Place (invalid - not bipartite)
✗ Transition → Transition (invalid - not bipartite)
"""
