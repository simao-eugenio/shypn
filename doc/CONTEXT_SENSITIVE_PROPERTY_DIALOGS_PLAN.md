# Context-Sensitive Property Dialogs Implementation Plan

**Date**: October 18, 2025  
**Branch**: `feature/property-dialogs-and-simulation-palette`  
**Phase**: 5 - Advanced Property Dialogs

## Overview

Enhance property dialogs to be context-sensitive based on transition type, with dynamic UI adaptation, field synchronization for mathematical expressions, and atomic persistence integration.

## Requirements Analysis

### 1. Context Sensitivity
**Requirement**: Dialogs adapt UI based on object type being edited

**Current State**:
- ✅ Separate dialogs exist: `place_prop_dialog.ui`, `transition_prop_dialog.ui`, `arc_prop_dialog.ui`
- ✅ Transition dialog has type dropdown: `immediate`, `timed`, `stochastic`, `continuous`
- ❌ All fields shown regardless of transition type (not context-sensitive)

**Target State**:
- Show/hide fields based on transition type
- Disable irrelevant fields instead of removing them (preserves data)
- Visual indication of which fields apply to current type

---

### 2. Transition Type Categorization
**Requirement**: UI inputs must be categorized by transition type

**Transition Types** (from `transition.py`):
```python
transition_type = 'continuous'  # Options: immediate, timed, stochastic, continuous
```

**Field Matrix by Type**:

| Field | Immediate | Timed | Stochastic | Continuous |
|-------|-----------|-------|------------|------------|
| **Name** | ✓ (ro) | ✓ (ro) | ✓ (ro) | ✓ (ro) |
| **Label** | ✓ | ✓ | ✓ | ✓ |
| **Priority** | ✓ | ✓ | ✓ | ✓ |
| **Guard** | ✓ | ✓ | ✓ | ✓ |
| **Rate** (basic) | ❌ | ✓ | ✓ | ✓ |
| **Rate Function** (advanced) | ❌ | ✓ | ✓ | ✓ |
| **Firing Policy** (earliest/latest) | ✓ | ✓ | ❌ | ❌ |
| **Distribution** | ❌ | ❌ | ✓ | ❌ |
| **ODE Function** | ❌ | ❌ | ❌ | ✓ |
| **Source** | ✓ | ✓ | ✓ | ✓ |
| **Sink** | ✓ | ✓ | ✓ | ✓ |

**Semantics by Type**:

1. **Immediate Transitions**:
   - Fire instantaneously (zero time)
   - Priority resolves conflicts
   - Firing policy (earliest/latest) for timed enable
   - No rate (fires immediately when enabled)

2. **Timed Transitions**:
   - Deterministic delay
   - Rate = delay duration
   - Firing policy (earliest/latest)
   - Can use expressions for rate

3. **Stochastic Transitions**:
   - Exponential distribution (default)
   - Rate = λ parameter
   - Can specify distribution type
   - Race conditions resolved stochastically

4. **Continuous Transitions**:
   - ODE-based flow
   - Rate function = differential equation
   - No firing policy (continuous flow)
   - Can use complex math expressions

---

### 3. UI Field Synchronization
**Requirement**: Math expressions in advanced fields sync to basic fields

**Example Flow**:
```python
# User enters in Rate Function (TextView):
rate_function = "lambda state: 0.5 * state.get_marking('P1')"

# System should:
# 1. Parse expression
# 2. Validate syntax
# 3. Update basic rate field to show: "[Expression]" or preview value
# 4. Store both: transition.rate = expression, transition.properties['rate_function'] = lambda
```

**Synchronization Rules**:

| Advanced Field | Basic Field | Sync Behavior |
|----------------|-------------|---------------|
| **Rate Function** (TextView) | **Rate** (Entry) | Display "[Expression]" or evaluated preview |
| **Guard Function** (TextView) | N/A | Standalone (no basic equivalent) |
| **ODE Function** (TextView) | **Rate** (Entry) | Display "[ODE]" |

---

### 4. Integrity & Atomic Persistence
**Requirement**: All changes must respect integrity rules and atomic persistence

**Existing Architecture** (from previous work):
```python
# NetObjPersistency - already implemented
- mark_dirty()  # Track unsaved changes
- atomic save operations
- change callbacks for auto-tracking

# DocumentController - already implemented
- set_change_callback()  # Wire object changes
- Object reference architecture (not name strings)
```

**Integration Points**:
1. ✅ Property dialogs already mark document dirty on OK
2. ✅ Change callbacks already wired for transitions
3. ✅ Object references already enforced (not name strings)
4. ✅ Atomic save operations already working

**New Requirements**:
- Validate changes before applying (syntax check for expressions)
- Rollback on cancel (restore original values)
- Emit change signal only after validation succeeds

---

## Implementation Plan

### Phase 5A: Context-Sensitive UI (Week 1)

#### Task 5A.1: Transition Type Field Mapping
**File**: `src/shypn/helpers/transition_prop_dialog_loader.py`

**Changes**:
```python
class TransitionPropDialogLoader:
    # Define field visibility map
    FIELD_VISIBILITY = {
        'immediate': {
            'rate_entry': False,
            'rate_textview': False,
            'firing_policy_combo': True,
            'ode_textview': False,
            'distribution_combo': False,
        },
        'timed': {
            'rate_entry': True,
            'rate_textview': True,
            'firing_policy_combo': True,
            'ode_textview': False,
            'distribution_combo': False,
        },
        'stochastic': {
            'rate_entry': True,
            'rate_textview': True,
            'firing_policy_combo': False,
            'ode_textview': False,
            'distribution_combo': True,
        },
        'continuous': {
            'rate_entry': True,
            'rate_textview': True,
            'firing_policy_combo': False,
            'ode_textview': True,
            'distribution_combo': False,
        }
    }
    
    def _on_type_changed(self, combo):
        """Handle transition type selection - show/hide relevant fields."""
        type_map = {0: 'immediate', 1: 'timed', 2: 'stochastic', 3: 'continuous'}
        selected_type = type_map.get(combo.get_active(), 'continuous')
        
        # Update field visibility
        self._update_field_visibility(selected_type)
        
        # Update help text
        self._update_type_description(selected_type)
    
    def _update_field_visibility(self, transition_type):
        """Show/hide fields based on transition type."""
        visibility_map = self.FIELD_VISIBILITY.get(transition_type, {})
        
        for widget_id, visible in visibility_map.items():
            widget = self.builder.get_object(widget_id)
            if widget:
                widget.set_sensitive(visible)
                # Optionally hide instead of disable:
                # parent_box = widget.get_parent()
                # if parent_box:
                #     parent_box.set_visible(visible)
```

**Deliverables**:
- ✅ Type change handler
- ✅ Field visibility logic
- ✅ Help text updates per type
- ✅ Preserve disabled field values

---

#### Task 5A.2: UI Layout Enhancements
**File**: `ui/dialogs/transition_prop_dialog.ui`

**Changes**:
1. Add description labels for each transition type
2. Group fields into frames by category:
   - General (name, label, type, priority)
   - Timing (rate, rate function, firing policy)
   - Continuous (ODE function)
   - Stochastic (distribution)
   - Conditions (guard function)
   - Behavior (source, sink)

**Example XML** (new structure):
```xml
<object class="GtkFrame" id="timing_frame">
  <property name="visible">True</property>
  <property name="label">Timing Parameters</property>
  <child>
    <object class="GtkBox">
      <!-- Rate entry -->
      <!-- Rate function TextView -->
      <!-- Firing policy combo -->
    </object>
  </child>
</object>

<object class="GtkFrame" id="continuous_frame">
  <property name="visible">False</property><!-- Show only for continuous -->
  <property name="label">Continuous Flow (ODE)</property>
  <child>
    <!-- ODE function TextView -->
  </child>
</object>
```

**Deliverables**:
- ✅ Reorganized UI layout
- ✅ Type-specific help text
- ✅ Visual grouping of fields

---

### Phase 5B: Expression Synchronization (Week 2)

#### Task 5B.1: Expression Parser & Validator
**New File**: `src/shypn/helpers/expression_validator.py`

**Purpose**: Validate and parse mathematical expressions

```python
class ExpressionValidator:
    """Validate mathematical expressions for transition properties."""
    
    ALLOWED_MODULES = {'math', 'numpy', 'scipy'}
    ALLOWED_FUNCTIONS = {'sin', 'cos', 'exp', 'log', 'sqrt', 'abs', 'min', 'max'}
    
    @staticmethod
    def validate_rate_expression(expr_str: str) -> tuple[bool, str, any]:
        """Validate rate expression.
        
        Returns:
            (is_valid, error_message, parsed_expression)
        """
        if not expr_str.strip():
            return (True, "", None)
        
        try:
            # Try to parse as number first
            numeric_value = float(expr_str)
            return (True, "", numeric_value)
        except ValueError:
            pass
        
        # Try to parse as Python expression
        try:
            import ast
            tree = ast.parse(expr_str, mode='eval')
            
            # Validate AST for safety (no imports, no exec, etc.)
            validator = SafeExpressionVisitor()
            validator.visit(tree)
            
            # Compile for syntax check
            compiled = compile(tree, '<string>', 'eval')
            
            return (True, "", compiled)
        except SyntaxError as e:
            return (False, f"Syntax error: {e.msg}", None)
        except Exception as e:
            return (False, f"Invalid expression: {str(e)}", None)
    
    @staticmethod
    def evaluate_preview(expr, state_dict: dict) -> str:
        """Evaluate expression with sample state for preview.
        
        Args:
            expr: Compiled expression or lambda
            state_dict: Sample state {'P1': 10, 'P2': 5, ...}
        
        Returns:
            Preview string like "≈ 2.5" or "[Error]"
        """
        try:
            if callable(expr):
                result = expr(state_dict)
            else:
                result = eval(expr, {"__builtins__": {}}, state_dict)
            
            return f"≈ {result:.3f}"
        except Exception as e:
            return f"[Error: {str(e)}]"


class SafeExpressionVisitor(ast.NodeVisitor):
    """AST visitor to validate expression safety."""
    
    ALLOWED_NODES = {
        ast.Expression, ast.BinOp, ast.UnaryOp,
        ast.Num, ast.Name, ast.Call, ast.Load,
        ast.Add, ast.Sub, ast.Mult, ast.Div,
        ast.Pow, ast.USub, ast.UAdd,
    }
    
    def visit(self, node):
        """Visit node and validate it's allowed."""
        if type(node) not in self.ALLOWED_NODES:
            raise ValueError(f"Forbidden AST node: {type(node).__name__}")
        return super().visit(node)
```

**Deliverables**:
- ✅ Expression validator
- ✅ Safety checker (no eval exploits)
- ✅ Preview evaluator

---

#### Task 5B.2: Field Synchronization Logic
**File**: `src/shypn/helpers/transition_prop_dialog_loader.py`

**Changes**:
```python
class TransitionPropDialogLoader:
    
    def _setup_expression_sync(self):
        """Setup synchronization between advanced and basic fields."""
        # Rate function → Rate entry sync
        rate_textview = self.builder.get_object('rate_textview')
        rate_entry = self.builder.get_object('rate_entry')
        
        if rate_textview and rate_entry:
            buffer = rate_textview.get_buffer()
            buffer.connect('changed', self._on_rate_function_changed, rate_entry)
    
    def _on_rate_function_changed(self, buffer, rate_entry):
        """Sync rate function TextView to basic rate Entry."""
        # Get text from buffer
        start, end = buffer.get_bounds()
        expr_text = buffer.get_text(start, end, True)
        
        # Validate expression
        is_valid, error_msg, parsed = ExpressionValidator.validate_rate_expression(expr_text)
        
        if not is_valid:
            # Show error in status or tooltip
            rate_entry.set_text("[Invalid]")
            rate_entry.set_tooltip_text(error_msg)
            return
        
        # Update basic field
        if parsed is None:
            rate_entry.set_text("")
        elif isinstance(parsed, (int, float)):
            rate_entry.set_text(str(parsed))
        else:
            # It's an expression - show preview
            sample_state = self._get_sample_state()
            preview = ExpressionValidator.evaluate_preview(parsed, sample_state)
            rate_entry.set_text(f"[Expression] {preview}")
        
        rate_entry.set_tooltip_text("Synchronized from Rate Function")
    
    def _get_sample_state(self) -> dict:
        """Get sample state for expression preview.
        
        Uses current marking if available, otherwise defaults.
        """
        if not self.model:
            return {'P1': 10, 'P2': 5}  # Default sample
        
        # Get actual current marking
        marking = {}
        for place in self.model.places:
            marking[place.name] = place.tokens
        
        return marking
```

**Deliverables**:
- ✅ Rate function → Rate entry sync
- ✅ Guard function validation
- ✅ Preview evaluation with current state
- ✅ Error handling with tooltips

---

### Phase 5C: Place & Arc Dialog Enhancements (Week 3)

#### Task 5C.1: Place Dialog Context Sensitivity
**File**: `src/shypn/helpers/place_prop_dialog_loader.py`

**Context**:
- Places are simpler (no types like transitions)
- Context = Initial marking vs. runtime marking
- Show runtime stats if simulation data available

**Changes**:
```python
class PlacePropDialogLoader:
    
    def _populate_fields(self):
        """Populate fields with context awareness."""
        # ... existing code ...
        
        # Show runtime statistics if available
        if self.data_collector:
            self._show_runtime_stats()
    
    def _show_runtime_stats(self):
        """Show runtime marking statistics if simulation running."""
        stats_label = self.builder.get_object('runtime_stats_label')
        if not stats_label:
            return
        
        place_name = self.place_obj.name
        current_marking = self.data_collector.get_current_marking(place_name)
        
        if current_marking is not None:
            stats_text = f"Current marking: {current_marking} tokens"
            stats_label.set_text(stats_text)
            stats_label.set_visible(True)
        else:
            stats_label.set_visible(False)
```

**Deliverables**:
- ✅ Runtime stats display
- ✅ Initial vs. current marking distinction
- ✅ Expression support for capacity

---

#### Task 5C.2: Arc Dialog Context Sensitivity
**File**: `src/shypn/helpers/arc_prop_dialog_loader.py`

**Context**:
- Arc type (normal, inhibitor, reset, test)
- Show source/target info
- Validate weight expressions

**Changes**:
```python
class ArcPropDialogLoader:
    
    def _update_arc_type_fields(self, arc_type):
        """Show/hide fields based on arc type."""
        # Normal arcs: weight
        # Inhibitor arcs: threshold
        # Reset arcs: no weight/threshold
        # Test arcs: weight (non-consuming)
        
        weight_box = self.builder.get_object('weight_box')
        threshold_box = self.builder.get_object('threshold_box')
        
        if arc_type == 'normal' or arc_type == 'test':
            weight_box.set_visible(True)
            threshold_box.set_visible(False)
        elif arc_type == 'inhibitor':
            weight_box.set_visible(False)
            threshold_box.set_visible(True)
        elif arc_type == 'reset':
            weight_box.set_visible(False)
            threshold_box.set_visible(False)
```

**Deliverables**:
- ✅ Arc type-specific fields
- ✅ Source/target info display
- ✅ Weight expression validation

---

### Phase 5D: Atomic Persistence Integration (Week 4)

#### Task 5D.1: Validation Before Apply
**File**: `src/shypn/helpers/transition_prop_dialog_loader.py`

**Changes**:
```python
class TransitionPropDialogLoader:
    
    def _on_response(self, dialog, response_id):
        """Handle dialog response with validation."""
        if response_id != Gtk.ResponseType.OK:
            # Cancel - do nothing (original values preserved)
            dialog.destroy()
            return
        
        # Validate all fields before applying
        validation_errors = self._validate_all_fields()
        
        if validation_errors:
            # Show error dialog
            error_dialog = Gtk.MessageDialog(
                parent=dialog,
                flags=Gtk.DialogFlags.MODAL,
                type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                message_format="Validation Errors"
            )
            error_dialog.format_secondary_text(
                "\n".join(validation_errors)
            )
            error_dialog.run()
            error_dialog.destroy()
            
            # Don't close dialog - let user fix errors
            dialog.stop_emission_by_name('response')
            return
        
        # All valid - apply changes atomically
        try:
            self._apply_changes()
            
            # Mark document dirty
            if self.persistency_manager:
                self.persistency_manager.mark_dirty()
            
            # Emit properties-changed signal
            self.emit('properties-changed')
            
            dialog.destroy()
        except Exception as e:
            # Rollback on error
            self._rollback_changes()
            
            # Show error
            error_dialog = Gtk.MessageDialog(
                parent=dialog,
                flags=Gtk.DialogFlags.MODAL,
                type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                message_format="Failed to apply changes"
            )
            error_dialog.format_secondary_text(str(e))
            error_dialog.run()
            error_dialog.destroy()
            
            dialog.stop_emission_by_name('response')
    
    def _validate_all_fields(self) -> list[str]:
        """Validate all fields and return list of errors."""
        errors = []
        
        # Validate rate expression
        rate_textview = self.builder.get_object('rate_textview')
        if rate_textview:
            buffer = rate_textview.get_buffer()
            start, end = buffer.get_bounds()
            expr_text = buffer.get_text(start, end, True)
            
            is_valid, error_msg, _ = ExpressionValidator.validate_rate_expression(expr_text)
            if not is_valid:
                errors.append(f"Rate function: {error_msg}")
        
        # Validate guard expression
        guard_textview = self.builder.get_object('guard_textview')
        if guard_textview:
            buffer = guard_textview.get_buffer()
            start, end = buffer.get_bounds()
            expr_text = buffer.get_text(start, end, True)
            
            is_valid, error_msg, _ = ExpressionValidator.validate_rate_expression(expr_text)
            if not is_valid:
                errors.append(f"Guard function: {error_msg}")
        
        # Validate type-specific fields
        transition_type = self._get_selected_type()
        if transition_type == 'immediate':
            # Immediate transitions can't have rate
            rate_entry = self.builder.get_object('rate_entry')
            if rate_entry and rate_entry.get_text().strip():
                errors.append("Immediate transitions don't use rate parameter")
        
        return errors
    
    def _apply_changes(self):
        """Apply validated changes to transition object atomically."""
        # Store original values for rollback
        self._original_values = {
            'label': self.transition_obj.label,
            'transition_type': self.transition_obj.transition_type,
            'rate': self.transition_obj.rate,
            'guard': self.transition_obj.guard,
            'priority': self.transition_obj.priority,
            'firing_policy': self.transition_obj.firing_policy,
            'is_source': self.transition_obj.is_source,
            'is_sink': self.transition_obj.is_sink,
            'border_color': self.transition_obj.border_color,
            'properties': dict(self.transition_obj.properties) if self.transition_obj.properties else {},
        }
        
        # Apply all changes
        # ... (existing apply logic) ...
    
    def _rollback_changes(self):
        """Rollback changes if apply fails."""
        if not hasattr(self, '_original_values'):
            return
        
        for attr, value in self._original_values.items():
            if attr == 'properties':
                self.transition_obj.properties = dict(value)
            else:
                setattr(self.transition_obj, attr, value)
```

**Deliverables**:
- ✅ Pre-apply validation
- ✅ Atomic apply with rollback
- ✅ Error reporting UI
- ✅ Document dirty tracking

---

## Testing Plan

### Test Case 1: Immediate Transition
1. Create immediate transition
2. Open properties dialog
3. ✓ Verify: Rate fields disabled
4. ✓ Verify: Firing policy visible
5. Set priority to 5
6. Click OK
7. ✓ Verify: Changes saved, document marked dirty

### Test Case 2: Continuous Transition with Expression
1. Create continuous transition
2. Open properties dialog
3. Enter rate function: `lambda state: 0.5 * state['P1']`
4. ✓ Verify: Basic rate field shows `[Expression] ≈ 5.0`
5. Click OK
6. ✓ Verify: Expression stored in `properties['rate_function']`
7. Reopen dialog
8. ✓ Verify: Expression still visible, preview updated

### Test Case 3: Invalid Expression
1. Open transition dialog
2. Enter invalid expression: `lambda x: import os`
3. ✓ Verify: Error shown in tooltip
4. Click OK
5. ✓ Verify: Validation error dialog appears
6. ✓ Verify: Dialog doesn't close

### Test Case 4: Type Switch
1. Create timed transition with rate = 2.5
2. Open dialog, change type to immediate
3. ✓ Verify: Rate field disabled but value preserved
4. Change type back to timed
5. ✓ Verify: Rate field re-enabled with original value

---

## Success Criteria

✅ **Context Sensitivity**:
- Transition dialog adapts UI for all 4 types
- Fields show/hide or enable/disable appropriately
- Help text updates per type

✅ **Expression Synchronization**:
- Rate function syncs to rate entry with preview
- Guard function validates syntax
- Invalid expressions show errors without crashing

✅ **Atomic Persistence**:
- All changes validated before apply
- Rollback on validation errors
- Document marked dirty only on successful apply
- Change callbacks emit only after apply

✅ **User Experience**:
- Clear visual indication of field availability
- Helpful error messages for invalid input
- Preserve disabled field values when type changes
- No data loss on cancel

---

## Implementation Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | 5A | Context-sensitive UI for transitions |
| 2 | 5B | Expression parser & synchronization |
| 3 | 5C | Place & arc dialog enhancements |
| 4 | 5D | Atomic persistence integration & testing |

**Total Duration**: 4 weeks  
**Status**: **PLANNING COMPLETE - READY TO IMPLEMENT**

---

## Dependencies

**Existing Infrastructure** (already implemented):
- ✅ Property dialog loaders (place, transition, arc)
- ✅ NetObjPersistency with mark_dirty()
- ✅ DocumentController with change callbacks
- ✅ Object reference architecture

**New Dependencies**:
- Expression validator (to be implemented)
- AST safety checker (to be implemented)
- Field visibility manager (to be implemented)

---

## Next Steps

1. **Review this plan** with user for approval
2. **Start Phase 5A**: Implement transition type field mapping
3. **Create feature branch**: `feature/context-sensitive-dialogs` (or continue in current branch)
4. **Implement incrementally**: One task at a time with testing
5. **Document as we go**: Update this plan with actual implementation notes

**Ready to proceed?** 🚀
