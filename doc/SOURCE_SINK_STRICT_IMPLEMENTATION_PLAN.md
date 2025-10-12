# Source/Sink Strict Formalism Implementation Plan

**Date**: October 11, 2025  
**Approach**: Option A - Pure Structural (Strict)

---

## 1. Formal Definitions (Enforced)

```
Source Transition t:
  • •t = ∅ (NO input arcs - ENFORCED)
  • t• ≠ ∅ (at least one output arc)
  • Always structurally enabled
  • Minimal locality: {p ∈ t•} (only output places)

Sink Transition t:
  • •t ≠ ∅ (at least one input arc)
  • t• = ∅ (NO output arcs - ENFORCED)
  • Enabled when: ∀p ∈ •t: M(p) ≥ Pre(p,t)
  • Minimal locality: {p ∈ •t} (only input places)
```

---

## 2. Implementation Changes

### A. Transition Model (transition.py)

**Add validation method:**
```python
def validate_source_sink_structure(self, model):
    """Validate that source/sink structure matches formal definition.
    
    Returns:
        (bool, str): (is_valid, error_message)
    """
    if self.is_source:
        input_arcs = [arc for arc in model.arcs if arc.target == self]
        if len(input_arcs) > 0:
            return False, f"Source transition '{self.name}' cannot have input arcs (has {len(input_arcs)})"
        output_arcs = [arc for arc in model.arcs if arc.source == self]
        if len(output_arcs) == 0:
            return False, f"Source transition '{self.name}' must have at least one output arc"
    
    if self.is_sink:
        output_arcs = [arc for arc in model.arcs if arc.source == self]
        if len(output_arcs) > 0:
            return False, f"Sink transition '{self.name}' cannot have output arcs (has {len(output_arcs)})"
        input_arcs = [arc for arc in model.arcs if arc.target == self]
        if len(input_arcs) == 0:
            return False, f"Sink transition '{self.name}' must have at least one input arc"
    
    return True, ""
```

### B. Transition Properties Dialog Loader

**Add validation before applying changes:**
```python
def _apply_changes(self):
    # Get new values
    is_source = self.is_source_check.get_active()
    is_sink = self.is_sink_check.get_active()
    
    # Validate structure if marking as source/sink
    if is_source or is_sink:
        valid, error = self.transition.validate_source_sink_structure(self.model)
        if not valid:
            # Show error dialog
            self._show_validation_error(error, is_source, is_sink)
            return False  # Don't close dialog
    
    # Apply changes...
```

**Add error dialog with auto-fix:**
```python
def _show_validation_error(self, error, is_source, is_sink):
    dialog = Gtk.MessageDialog(
        transient_for=self.dialog,
        modal=True,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.NONE,
        text="Invalid Source/Sink Structure"
    )
    dialog.format_secondary_text(
        f"{error}\n\n"
        f"Would you like to automatically fix this?\n\n"
        f"{'• Remove all input arcs' if is_source else ''}\n"
        f"{'• Remove all output arcs' if is_sink else ''}"
    )
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Fix Automatically", Gtk.ResponseType.YES)
    
    response = dialog.run()
    dialog.destroy()
    
    if response == Gtk.ResponseType.YES:
        self._auto_fix_structure(is_source, is_sink)
        # Try again
        self._apply_changes()
```

### C. Independence Detection (controller.py)

**Update locality detection for source/sink:**
```python
def _get_all_places_for_transition(self, transition) -> set:
    """Get all places involved in a transition's locality.
    
    Special handling for source/sink transitions:
    - Source: Only output places (•t = ∅)
    - Sink: Only input places (t• = ∅)
    - Normal: Both input and output places
    """
    behavior = self._get_behavior(transition)
    place_ids = set()
    
    # Check if source or sink
    is_source = getattr(transition, 'is_source', False)
    is_sink = getattr(transition, 'is_sink', False)
    
    # Get input places (skip for source)
    if not is_source:
        for arc in behavior.get_input_arcs():
            if hasattr(arc, 'source_id'):
                place_ids.add(arc.source_id)
            elif hasattr(arc, 'source') and hasattr(arc.source, 'id'):
                place_ids.add(arc.source.id)
    
    # Get output places (skip for sink)
    if not is_sink:
        for arc in behavior.get_output_arcs():
            if hasattr(arc, 'target_id'):
                place_ids.add(arc.target_id)
            elif hasattr(arc, 'target') and hasattr(arc.target, 'id'):
                place_ids.add(arc.target.id)
    
    return place_ids
```

### D. Arc Creation Validation

**Prevent creating invalid arcs:**
```python
# In arc creation handler
def on_arc_created(self, source, target):
    # Check if target is a source transition
    if isinstance(target, Transition) and target.is_source:
        self._show_error(
            "Cannot create input arc to source transition",
            f"Transition '{target.name}' is marked as a source.\n"
            f"Source transitions cannot have input arcs.\n\n"
            f"Either:\n"
            f"• Create arc from transition to place (output)\n"
            f"• Unmark transition as source"
        )
        return False
    
    # Check if source is a sink transition
    if isinstance(source, Transition) and source.is_sink:
        self._show_error(
            "Cannot create output arc from sink transition",
            f"Transition '{source.name}' is marked as a sink.\n"
            f"Sink transitions cannot have output arcs.\n\n"
            f"Either:\n"
            f"• Create arc from place to transition (input)\n"
            f"• Unmark transition as sink"
        )
        return False
    
    # Proceed with arc creation
    return True
```

---

## 3. Minimal Locality Recognition

### Source Transitions as Minimal Localities

```python
def _is_minimal_locality(self, transition) -> bool:
    """Check if transition represents a minimal locality.
    
    Minimal localities:
    1. Source transitions (only outputs, no inputs)
    2. Sink transitions (only inputs, no outputs)
    3. Transitions with single input and single output (trivial)
    
    These are always independent from other transitions
    (unless they share the same places).
    """
    is_source = getattr(transition, 'is_source', False)
    is_sink = getattr(transition, 'is_sink', False)
    
    # Source/sink are minimal by definition
    if is_source or is_sink:
        return True
    
    # Check for trivial locality
    behavior = self._get_behavior(transition)
    input_count = len(behavior.get_input_arcs())
    output_count = len(behavior.get_output_arcs())
    
    return input_count <= 1 and output_count <= 1
```

### Independence with Source/Sink

```python
def _are_independent(self, t1, t2) -> bool:
    """Check if two transitions are independent.
    
    Enhanced for source/sink:
    - Source transitions only conflict on output places
    - Sink transitions only conflict on input places
    - Two sources can never conflict (unless same output place)
    - Two sinks can never conflict (unless same input place)
    """
    # Get localities (respects source/sink structure)
    places_t1 = self._get_all_places_for_transition(t1)
    places_t2 = self._get_all_places_for_transition(t2)
    
    # Check for intersection
    shared_places = places_t1 & places_t2
    
    # Independent if NO shared places
    return len(shared_places) == 0
```

---

## 4. Testing Strategy

### Test Cases

**Test 1: Source Structure Validation**
```python
def test_source_validation():
    # Create: P1 → T1(source) → P2
    # Should FAIL: source cannot have input arc from P1
    
    # Create: T1(source) → P2
    # Should PASS: source with only output
```

**Test 2: Sink Structure Validation**
```python
def test_sink_validation():
    # Create: P1 → T1(sink) → P2
    # Should FAIL: sink cannot have output arc to P2
    
    # Create: P1 → T1(sink)
    # Should PASS: sink with only input
```

**Test 3: Independence Detection**
```python
def test_source_independence():
    # T1(source) → P1, T2(source) → P2
    # Should be INDEPENDENT (different output places)
    
    # T1(source) → P1, T2(source) → P1
    # Should be DEPENDENT (same output place)
```

**Test 4: Auto-fix**
```python
def test_auto_fix():
    # Create: P1 → T1 → P2
    # Mark T1 as source
    # Should offer to remove P1→T1 arc
    # After fix: T1 → P2 only
```

---

## 5. Migration Strategy

### Backward Compatibility

**For existing models with incorrect structure:**

```python
def _validate_and_migrate_model(model):
    """Check model for invalid source/sink structures and offer migration."""
    issues = []
    
    for transition in model.transitions:
        if transition.is_source or transition.is_sink:
            valid, error = transition.validate_source_sink_structure(model)
            if not valid:
                issues.append((transition, error))
    
    if issues:
        # Show migration dialog
        _show_migration_dialog(issues)
```

---

## 6. Implementation Order

1. ✅ Research formal definitions (DONE)
2. ⏳ Add `validate_source_sink_structure()` to Transition
3. ⏳ Update dialog loader with validation
4. ⏳ Add auto-fix functionality
5. ⏳ Update arc creation to prevent invalid structures
6. ⏳ Update independence detection for source/sink
7. ⏳ Add minimal locality recognition
8. ⏳ Create comprehensive tests
9. ⏳ Update documentation
10. ⏳ Test with existing models

---

## 7. Files to Modify

1. `src/shypn/netobjs/transition.py` - Add validation
2. `src/shypn/helpers/transition_prop_dialog_loader.py` - Add UI validation
3. `src/shypn/engine/simulation/controller.py` - Update independence
4. `src/shypn/edit/handlers/arc_tool_handler.py` - Prevent invalid arcs
5. `tests/test_source_sink_strict.py` - New comprehensive tests
6. `doc/SOURCE_SINK_FORMAL_DEFINITIONS.md` - Already created ✅

---

**Status**: Ready to implement  
**Next Step**: Start with Transition validation method

