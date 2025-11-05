# Real Auto-Load Issue - Root Cause Analysis

## The Sequence

```
1. KEGG import creates document_model with places/transitions/arcs
2. Auto-load calls canvas_manager.load_objects(places, transitions, arcs)
3. load_objects() adds objects to manager.places/transitions/arcs
4. fit_to_page(deferred=True) schedules fit for next draw event
5. mark_needs_redraw() triggers a draw event
6. _ensure_simulation_reset() calls controller.reset()
7. controller.reset() does: place.tokens = place.initial_marking
```

## THE PROBLEM

**When load_objects() is called**, it adds Place objects to the manager.
These Place objects come from document_model.

**Question**: Do these places have `initial_marking` set?

If places don't have `initial_marking` properly set, then:
- controller.reset() tries to do `place.tokens = place.initial_marking`
- If initial_marking is None or not set → places get 0 tokens
- Model appears "empty" even though objects exist!

## Need to Check

1. Does KEG import set initial_marking on places?
2. Does load_objects() preserve initial_marking?
3. Does controller.reset() handle missing initial_marking correctly?

## Alternative Issue

Maybe the problem is simpler:
- Objects ARE loaded
- fit_to_page IS scheduled
- BUT: Canvas never redraws?

Need to check if mark_needs_redraw() actually triggers a draw when called
during auto-load (might be suppressed by some flag).
