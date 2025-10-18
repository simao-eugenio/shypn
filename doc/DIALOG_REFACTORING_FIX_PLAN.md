# Dialog Refactoring Fix Plan

**Date**: October 18, 2025  
**Issue**: Property dialogs refactoring violates project's UI/implementation decoupling rule

## Problem Analysis

### Current Refactoring Issues

The OOP refactoring (commit `c52a145`) added **too much logic in UI layer**:

```
src/shypn/ui/dialogs/
├── base/
│   ├── property_dialog_base.py       # 420 lines - TOO MUCH UI LOGIC
│   └── expression_validator.py       # 280 lines - BUSINESS LOGIC
└── transition/
    └── transition_property_dialog.py # 530 lines - MIXED UI/BUSINESS
```

**Problems**:
1. **PropertyDialogBase** has business logic (validation framework, rollback, persistence)
2. **ExpressionValidator** is business logic, not UI code
3. **TransitionPropertyDialog** has type-specific logic (should be in data layer)
4. Violates project's **"UI code only if strictly necessary"** rule

### Project's Architectural Pattern

Looking at existing code:

**Good Examples** (thin loaders):
- `place_prop_dialog_loader.py` - 193 lines, simple data binding
- `arc_prop_dialog_loader.py` - Similar pattern
- Pattern: Load UI → Populate → Apply → Done

**Architecture Rule**:
```
/ui/ (repo root)           → Glade UI files (.ui XML)
/src/shypn/helpers/        → Thin UI loaders (bridge UI ↔ data)
/src/shypn/ui/             → UI state management (NOT loaders)
/src/shypn/data/           → Business logic
```

## Solution: Move Logic to Data Layer

### Step 1: Move ExpressionValidator to Data Layer

**From**: `src/shypn/ui/dialogs/base/expression_validator.py`  
**To**: `src/shypn/data/validation/expression_validator.py`

**Reason**: Expression validation is **business logic**, not UI concern.

### Step 2: Move Type-Specific Logic to Transition Class

**From**: `TransitionPropertyDialog.FIELD_VISIBILITY` dict  
**To**: `Transition` class methods in data layer

```python
# In src/shypn/data/petri_net_objects.py
class Transition:
    def get_editable_fields(self) -> Dict[str, bool]:
        """Return which fields are editable for this transition type."""
        if self.transition_type == 'immediate':
            return {'rate': False, 'firing_policy': True}
        elif self.transition_type == 'timed':
            return {'rate': True, 'firing_policy': True}
        # ...
    
    def get_type_description(self) -> str:
        """Return description of this transition type."""
        descriptions = {
            'immediate': "Fires instantly when enabled...",
            # ...
        }
        return descriptions.get(self.transition_type, "")
```

### Step 3: Simplify Loaders to Follow Project Pattern

**Goal**: Make loaders as thin as `place_prop_dialog_loader.py`

```python
# src/shypn/helpers/transition_prop_dialog_loader.py
class TransitionPropDialogLoader(GObject.GObject):
    """Thin loader - just data binding."""
    
    def __init__(self, transition_obj, parent_window=None, ...):
        # Load UI
        # Populate fields
        # Done
    
    def _populate_fields(self):
        # Get editable fields from transition object
        editable = self.transition_obj.get_editable_fields()
        
        # Show/hide widgets based on object's info
        if not editable['rate']:
            self.rate_entry.set_visible(False)
    
    def _apply_changes(self):
        # Simple data binding back to object
        # Validation done by object itself
        try:
            self.transition_obj.set_rate(rate_text)
        except ValueError as e:
            # Show error dialog
            pass
```

### Step 4: Delete Unnecessary Abstraction

**Remove**:
- `src/shypn/ui/dialogs/base/property_dialog_base.py` - Premature abstraction
- `src/shypn/ui/dialogs/` directory structure - Not needed yet

**Why**: 
- Only have 3 dialogs (place, transition, arc)
- They're different enough that shared base class adds complexity
- Follow YAGNI principle
- Project pattern is simple loaders, not class hierarchies

## Revised Architecture

### Directory Structure

```
/ui/dialogs/                           # Glade UI files
├── place_prop_dialog.ui
├── transition_prop_dialog.ui
└── arc_prop_dialog.ui

/src/shypn/helpers/                    # Thin loaders
├── place_prop_dialog_loader.py        # ~200 lines
├── transition_prop_dialog_loader.py   # ~250 lines
└── arc_prop_dialog_loader.py          # ~200 lines

/src/shypn/data/                       # Business logic
├── petri_net_objects.py               # Place, Transition, Arc classes
│   └── Transition.get_editable_fields()
│   └── Transition.validate_rate()
│   └── Transition.get_type_description()
└── validation/
    └── expression_validator.py        # Moved from UI layer
```

### Loader Pattern (Simplified)

```python
class TransitionPropDialogLoader(GObject.GObject):
    """Thin loader following project pattern."""
    
    __gsignals__ = {
        'properties-changed': (GObject.SignalFlags.RUN_FIRST, None, ())
    }
    
    def __init__(self, transition_obj, parent_window=None, ui_dir=None,
                 persistency_manager=None):
        super().__init__()
        
        # Resolve UI path (same as other loaders)
        if ui_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            ui_dir = os.path.join(project_root, 'ui', 'dialogs')
        
        self.ui_path = os.path.join(ui_dir, 'transition_prop_dialog.ui')
        self.transition_obj = transition_obj
        self.parent_window = parent_window
        self.persistency_manager = persistency_manager
        
        # Load and setup
        self._load_ui()
        self._setup_color_picker()
        self._populate_fields()
        self._update_field_visibility()  # Based on transition type
    
    def _load_ui(self):
        """Load UI file - same pattern as place_prop_dialog_loader."""
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f"UI file not found: {self.ui_path}")
        
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        self.dialog = self.builder.get_object('transition_properties_dialog')
        
        if self.dialog is None:
            raise ValueError("Dialog not found in UI file")
        
        if self.parent_window:
            self.dialog.set_transient_for(self.parent_window)
        
        self.dialog.connect('response', self._on_response)
    
    def _populate_fields(self):
        """Populate fields from object - simple data binding."""
        # Name (read-only)
        name_entry = self.builder.get_object('name_entry')
        if name_entry:
            name_entry.set_text(str(self.transition_obj.name))
            name_entry.set_editable(False)
        
        # Type combo
        type_combo = self.builder.get_object('prop_transition_type_combo')
        if type_combo:
            type_map = {'immediate': 0, 'timed': 1, 'stochastic': 2, 'continuous': 3}
            type_combo.set_active(type_map.get(self.transition_obj.transition_type, 3))
            type_combo.connect('changed', self._on_type_changed)
        
        # Rate
        rate_entry = self.builder.get_object('rate_entry')
        if rate_entry:
            rate_entry.set_text(str(self.transition_obj.rate or ''))
        
        # ... other fields
    
    def _update_field_visibility(self):
        """Update field visibility based on transition type.
        
        Delegates to transition object for logic.
        """
        editable = self.transition_obj.get_editable_fields()
        
        # Show/hide based on object's info
        rate_entry = self.builder.get_object('rate_entry')
        if rate_entry:
            rate_entry.set_visible(editable.get('rate', True))
        
        firing_policy = self.builder.get_object('firing_policy_combo')
        if firing_policy:
            firing_policy.set_visible(editable.get('firing_policy', True))
    
    def _on_type_changed(self, combo):
        """Handle type change - update visibility."""
        type_list = ['immediate', 'timed', 'stochastic', 'continuous']
        new_type = type_list[combo.get_active()]
        
        # Update object temporarily (not persisted until OK)
        old_type = self.transition_obj.transition_type
        self.transition_obj.transition_type = new_type
        
        # Update UI
        self._update_field_visibility()
        
        # Update description
        desc_label = self.builder.get_object('type_description_label')
        if desc_label:
            desc_label.set_text(self.transition_obj.get_type_description())
    
    def _apply_changes(self):
        """Apply changes - let object validate."""
        # Type
        type_combo = self.builder.get_object('prop_transition_type_combo')
        if type_combo:
            type_list = ['immediate', 'timed', 'stochastic', 'continuous']
            self.transition_obj.transition_type = type_list[type_combo.get_active()]
        
        # Rate - let object validate
        rate_entry = self.builder.get_object('rate_entry')
        if rate_entry:
            try:
                self.transition_obj.set_rate(rate_entry.get_text().strip())
            except ValueError as e:
                self._show_error(f"Invalid rate: {e}")
                return False
        
        # ... other fields
        return True
    
    def _on_response(self, dialog, response_id):
        """Handle OK/Cancel."""
        if response_id == Gtk.ResponseType.OK:
            if self._apply_changes():
                if self.persistency_manager:
                    self.persistency_manager.mark_dirty()
                self.emit('properties-changed')
        
        dialog.destroy()
    
    def run(self):
        """Run dialog modally."""
        return self.dialog.run()
```

**Key Points**:
- ~250 lines (vs. 530 in OOP version)
- No abstract base class
- Business logic in `Transition` class
- Simple, readable, follows project pattern

## Migration Plan

### Phase 1: Move Business Logic to Data Layer ✅

1. Create `src/shypn/data/validation/` directory
2. Move `expression_validator.py` there
3. Add `get_editable_fields()` to `Transition` class
4. Add `get_type_description()` to `Transition` class
5. Add `set_rate()` with validation to `Transition` class

### Phase 2: Simplify Loaders ✅

1. Rewrite `transition_prop_dialog_loader.py` following place loader pattern
2. Keep it in `src/shypn/helpers/` (not `src/shypn/ui/dialogs/`)
3. Remove abstract base class usage
4. Simple data binding only

### Phase 3: Clean Up ✅

1. Delete `src/shypn/ui/dialogs/` directory
2. Update imports in any code using the dialogs
3. Update documentation
4. Test all three property dialogs

### Phase 4: Archive ✅

1. Keep archived code for reference
2. Update archive README explaining the revert

## Benefits of Simplified Approach

### Advantages

1. **Follows Project Pattern**: Consistent with existing loaders
2. **Clear Separation**: Business logic in data layer, UI in helpers
3. **Easier to Understand**: No abstract base classes, simple code
4. **Less Code**: ~250 lines vs. 530 lines per dialog
5. **YAGNI**: Don't abstract until we have 5+ dialogs with shared logic

### What We Keep

1. **Context-Sensitive UI**: Still works, logic in data layer
2. **Expression Validation**: Still works, moved to data layer
3. **Field Visibility**: Still works, driven by object methods
4. **Type Descriptions**: Still works, returned by object

### What We Remove

1. **Abstract Base Classes**: Premature abstraction
2. **Deep Directory Structure**: Unnecessary for 3 dialogs
3. **UI Layer Business Logic**: Violates architecture
4. **Complex Metaclass Magic**: Not needed for simple loaders

## Validation

### Test Cases

After refactoring:

1. ✅ Open transition properties dialog
2. ✅ Change transition type
3. ✅ Verify fields show/hide correctly
4. ✅ Edit rate value
5. ✅ Verify validation works
6. ✅ Apply changes
7. ✅ Verify object updated correctly
8. ✅ Verify document marked dirty

### Code Quality

- [ ] All loaders follow same pattern
- [ ] No business logic in helpers
- [ ] Business logic in data layer
- [ ] Simple, readable code
- [ ] No premature abstraction

## Timeline

**Estimated Time**: 2-3 hours

1. **Move business logic** (30 min)
2. **Rewrite transition loader** (60 min)
3. **Test and fix** (30 min)
4. **Clean up and document** (30 min)

## Lessons Learned

### What Went Wrong

1. **Over-engineered**: Created abstract base class for 3 dialogs
2. **Mixed Concerns**: Put business logic in UI layer
3. **Ignored Project Pattern**: Didn't follow existing loader examples
4. **Premature Optimization**: Abstracted before seeing patterns

### What to Do Differently

1. **Follow Existing Patterns**: Look at similar code first
2. **Keep It Simple**: Don't abstract until you have 5+ similar cases
3. **Respect Architecture**: UI code only if strictly necessary
4. **Business Logic in Data Layer**: Always

### Key Principle

> **"UI code only if strictly necessary"**
> 
> Loaders should be thin bridges between UI files and data objects.
> All business logic, validation, and type-specific behavior belongs
> in the data layer where it can be tested and reused.

---

**Status**: PLAN READY  
**Next**: Implement Phase 1-4
