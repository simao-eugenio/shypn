# Simulation Issue Analysis - Manual vs Imported Objects

**User Report:** 
> "imported a model from kegg, added 5 stochastics source transition, run, nothing runs, 
> the I created a t-p on the canvas, run, everything runned"

---

## Analysis

### Lifecycle Investigation

After reviewing the code, I found that `_ensure_simulation_reset()` **IS** being called after File → Open:

**File:** `src/shypn/helpers/file_explorer_panel.py` (line 1905-1907)
```python
# CRITICAL: Ensure simulation is reset after loading file
if hasattr(self.canvas_loader, '_ensure_simulation_reset'):
    drawing_area = self.canvas_loader.get_current_document()
    self.canvas_loader._ensure_simulation_reset(drawing_area)
```

This means:
1. User imports KEGG model → Saves to file
2. User opens file → `_ensure_simulation_reset()` called ✓
3. Simulation controller should be in clean state ✓

### So What's the Real Problem?

The user said:
- Added 5 stochastic source transitions **manually** → Run → **Nothing runs**
- Created transition-place pair → Run → **Everything runs**

This suggests the issue is **NOT** with the simulation controller reset, but with how **stochastic source transitions** are handled after being manually added to an imported model.

### Hypothesis: Stochastic Sources Need Initial State

Stochastic source transitions need:
1. `is_source = True` attribute set
2. Proper `transition_type = 'stochastic'` 
3. **Initial enablement state** set in `controller.transition_states`

When manually creating a source transition, these might not be properly initialized.

### Check: Are Source Transitions Auto-Enabled?

From `controller.py` (lines 272-293):
```python
# If a new transition was created, initialize its state and enablement
if isinstance(obj, Transition):
    if obj.id not in self.transition_states:
        self.transition_states[obj.id] = TransitionState()
    
    # Immediately update enablement for the new transition
    behavior = self._get_behavior(obj)
    is_source = getattr(obj, 'is_source', False)
    
    if is_source:
        # Source transitions are always enabled
        state = self.transition_states[obj.id]
        state.enablement_time = self.time
        if hasattr(behavior, 'set_enablement_time'):
            behavior.set_enablement_time(self.time)
```

This shows that source transitions **ARE** automatically enabled when created.

### Alternative Hypothesis: Initial Markings Not Set

After importing, places have their `initial_marking` values. But when adding new source transitions manually, they produce tokens into places that already exist. If those places have `initial_marking=0`, the simulation might behave strangely.

### Most Likely Issue: New reset() Method Conflict

I just added a `reset()` method to SimulationController, but the code calls `reset_for_new_model()`. Let me verify this isn't causing issues.

---

## Recommended Actions

1. **Verify the user's exact workflow:**
   - Did they use File → Open after KEGG import? Or did they skip this step?
   - Did the KEGG import auto-load into canvas (old behavior) or save only?
   
2. **Test stochastic source transitions specifically:**
   - Create new model
   - Add 5 stochastic source transitions manually
   - Run simulation
   - Do they fire?

3. **Check if the new reset() method I added conflicts with reset_for_new_model()**

4. **Verify that manually added transitions to imported models get proper initialization**

---

## Immediate Fix: Update Documentation

The analysis document I created (`CRITICAL_SIMULATION_INIT_IMPORT_BUG.md`) assumes the reset wasn't happening, but the code shows it **is** happening via `_ensure_simulation_reset()` → `reset_for_new_model()`.

However, the new `reset()` method I just added might be useful for other scenarios, so it's good to have both:
- `reset()` - Simple reset without changing model reference
- `reset_for_new_model(manager)` - Full reset with new model reference

---

## Updated Hypothesis

The real issue might be:
1. User imports KEGG model but **doesn't open it** (just sees it saved)
2. User continues working in the **old canvas** (still has previous model loaded)
3. Adds source transitions to **wrong/old model**
4. Runs simulation on old model → Nothing works
5. Creates new T-P pair → This invalidates cache and forces rebuild → Works

**Action:** Ask user to clarify their exact workflow.
