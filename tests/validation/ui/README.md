# Dialog UI Validation Test Suite

**Purpose**: Validate property dialog UI behavior, persistence, and dynamic updates.

**Status**: 🚧 In Development  
**Target**: 56 tests across 4 categories  

## Quick Start

```bash
# Run all UI validation tests
pytest tests/validation/ui/ -v

# Run specific category
pytest tests/validation/ui/test_transition_type_switching.py -v

# Run with coverage
pytest tests/validation/ui/ --cov=src/shypn/helpers --cov=src/shypn/netobjs -v
```

## Test Categories

### 1. Dynamic UI Behavior (P0 - CRITICAL)
Tests real-time UI updates when properties change within dialogs.

**Files**:
- `test_transition_type_switching.py` - Transition type changes (immediate/timed/stochastic/continuous)
- `test_arc_type_switching.py` - Arc type changes (normal ↔ inhibitor)
- `test_field_visibility_updates.py` - Field show/hide based on type
- `test_validation_constraints.py` - Min/max value enforcement

**Key Tests**:
- Type switching updates field visibility
- Properties preserved during type changes
- Invalid values rejected with clear errors
- UI matches business logic (get_editable_fields())

### 2. Data Persistence (P2 - MEDIUM)
Tests that properties persist across dialog open/close cycles.

**Files**:
- `test_place_persistency.py` - Place properties (tokens, capacity, radius, width)
- `test_arc_persistency.py` - Arc properties (weight, color, line width, type)
- `test_transition_persistency.py` - Transition properties (rate, guard, priority, type)
- `test_project_persistency.py` - Project metadata (name, description)

### 3. Mode Switching (P2 - MEDIUM)
Tests design ↔ simulation mode transitions.

**Files**:
- `test_design_to_simulation.py` - Properties carry to simulation
- `test_simulation_to_design.py` - Simulation doesn't affect design
- `test_dialog_behavior_in_modes.py` - Mode-specific UI behavior

### 4. Multi-Object Editing (P3 - LOW)
Tests editing multiple objects without data loss.

**Files**:
- `test_object_switching.py` - Switch between objects
- `test_concurrent_dialogs.py` - Multiple dialogs open (if supported)

## Testing Approach

### Non-GTK Testing (Preferred)
Fast tests that don't require GTK windows:

```python
def test_type_logic():
    """Test business logic without UI."""
    trans = Transition(x=100, y=100, name='T1')
    trans.transition_type = 'immediate'
    
    fields = trans.get_editable_fields()
    assert fields['rate'] == False  # Hidden for immediate
```

### Loader-Level Testing (UI without Display)
Test dialog loaders without showing windows:

```python
def test_loader_behavior():
    """Test loader without run()."""
    trans = create_transition()
    loader = TransitionPropDialogLoader(trans, parent_window=None)
    
    # Test internal state
    type_combo = loader.builder.get_object('prop_transition_type_combo')
    assert type_combo is not None
```

### Integration Testing (Optional)
Full dialog display tests (manual verification):

```python
@pytest.mark.manual
def test_full_interaction():
    """Requires human interaction."""
    pass
```

## Common Fixtures (conftest.py)

### Manager Fixtures
- `manager` - ModelCanvasManager instance
- `document_controller` - For creating net objects
- `simulation_controller` - For mode switching

### Object Creation Fixtures
- `create_place()` - Create place with defaults
- `create_transition(type='immediate')` - Create transition
- `create_arc(direction='place_to_transition')` - Create arc

### Dialog Fixtures
- `mock_window` - GTK window for dialog parents (when needed)

## Architecture Alignment

These tests follow the project's architecture principles:

```
Business Logic (Data Layer)
    ↓ delegates to
Loaders (UI Layer)
    ↓ tested by
UI Validation Tests
```

**What We Test**:
- ✅ Loaders correctly bind UI to data
- ✅ Business logic returns correct values
- ✅ UI updates match business logic changes
- ✅ Data persists correctly

**What We DON'T Test**:
- ❌ GTK internals (trust GTK)
- ❌ Visual appearance (manual testing)
- ❌ Mouse/keyboard events (not relevant)

## Known Behaviors

### Type Switching is Non-Destructive
Changing transition type preserves properties (rate, guard, etc.) even if hidden:

```python
trans.transition_type = 'immediate'
trans.rate = 2.5  # Set rate
trans.transition_type = 'timed'  # Switch type
# Rate is still 2.5 (preserved)
```

### Arc Transformation Validates Direction
Inhibitor arcs must be Place → Transition:

```python
arc.direction = 'transition_to_place'
convert_to_inhibitor(arc)  # Raises ValueError
```

### Field Visibility Driven by Business Logic
UI visibility matches `get_editable_fields()`:

```python
trans.transition_type = 'immediate'
fields = trans.get_editable_fields()
# UI should hide fields where fields[name] == False
```

## Troubleshooting

### GTK Warnings
If you see GTK warnings, ensure:
- gi.require_version('Gtk', '3.0') is called before importing GTK
- Tests don't show actual windows (use parent_window=None)

### Loader Creation Fails
If loader creation fails:
- Check UI file exists in `ui/dialogs/`
- Verify builder.get_object() IDs match UI file
- Ensure object has required attributes (name, x, y)

### Type Switching Doesn't Update UI
If UI doesn't update on type change:
- Verify _on_type_changed handler is connected
- Check _update_field_visibility() is called
- Ensure get_editable_fields() returns correct dict

## Success Criteria

✅ All P0 tests pass (type switching)  
✅ All P1 tests pass (field visibility, validation)  
✅ All P2 tests pass (persistence, mode switching)  
✅ Tests run in < 15 seconds  
✅ Zero GTK errors/warnings  
✅ Clear error messages on failures  

## Contributing

When adding new tests:
1. Follow existing patterns (see test examples)
2. Use fixtures from conftest.py
3. Test business logic separately from UI
4. Add docstrings explaining what's tested
5. Keep tests fast (<1s each)

---

**Created**: October 18, 2025  
**Status**: 🚧 In Development  
**Priority**: P0 (Type Switching), P1 (Validation), P2 (Persistence)
