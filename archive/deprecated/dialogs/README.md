# Deprecated Property Dialogs

This directory contains archived property dialog implementations from different refactoring attempts.

## Refactoring History

### Version 1: Original Monolithic (DEPRECATED Oct 18, 2025)
**File**: `transition_prop_dialog_loader_original.py` (524 lines)

**Issues**:
1. **Monolithic**: All logic in one large class
2. **No Modularity**: Hard to reuse code
3. **Mixed Concerns**: UI + validation + business logic together

### Version 2: OOP Architecture (DEPRECATED Oct 18, 2025 - Same Day!)
**File**: `transition_prop_dialog_loader_oop_wrapper.py` (89 lines wrapper)
**Also Removed**: ~1280 lines in `src/shypn/ui/dialogs/` directory structure

**Why Deprecated So Quickly**:
1. **Violated Project Architecture**: Put business logic in UI layer (`src/shypn/ui/dialogs/`)
2. **Ignored Project Pattern**: Didn't follow existing thin loader pattern
3. **Premature Abstraction**: Created abstract base classes for only 3 dialogs
4. **Wrong Location**: Business logic should be in data layer, not UI layer

**Key Lesson**: The OOP refactoring looked good in isolation but violated the project's core principle:
> **"UI code only if strictly necessary"**
> 
> Loaders in `helpers/` should be thin bridges between UI files and data objects.
> Business logic belongs in the data layer where it can be tested and reused.

### Version 3: Thin Loader with Data Layer Logic (CURRENT - Oct 18, 2025)
**File**: `src/shypn/helpers/transition_prop_dialog_loader.py` (382 lines)

**Follows Project Architecture**:
1. **Business Logic in Data Layer**: 
   - `Transition.get_editable_fields()` - Which fields to show
   - `Transition.get_type_description()` - Help text
   - `Transition.set_rate()` - Validation
   - `Transition.set_guard()` - Validation

2. **Validation in Data Layer**: 
   - `src/shypn/data/validation/expression_validator.py`
   - Business logic, not UI concern

3. **Thin Loader in Helpers**: 
   - Just UI binding and widget management
   - No business logic
   - Simple data binding pattern

4. **Consistent Pattern**: 
   - Matches `place_prop_dialog_loader.py` (~200 lines)
   - Matches `arc_prop_dialog_loader.py` (~200 lines)
   - All loaders follow same thin pattern

## Project Architecture (Correct Pattern)

```
/ui/                           # Glade UI files (.ui XML) - NO PYTHON
    dialogs/
        transition_prop_dialog.ui
        place_prop_dialog.ui
        arc_prop_dialog.ui

/src/shypn/helpers/            # Thin loaders (UI ↔ data bridge)
    transition_prop_dialog_loader.py  (~380 lines)
    place_prop_dialog_loader.py       (~200 lines)
    arc_prop_dialog_loader.py         (~200 lines)

/src/shypn/data/               # Business logic
    validation/
        expression_validator.py
    
/src/shypn/netobjs/            # Data model with business logic
    transition.py
        └── get_editable_fields()
        └── get_type_description()
        └── set_rate()
        └── set_guard()
```

## What Each Layer Does

### UI Files (`/ui/`)
- **Purpose**: GTK widget definitions only
- **Format**: XML (Glade files)
- **No Python**: Just UI structure

### Helpers (`/src/shypn/helpers/`)
- **Purpose**: Bridge UI ↔ Data
- **Pattern**: Load UI → Populate → Apply
- **Rules**:
  - No business logic
  - No validation logic
  - Just data binding
  - Delegate to data objects

### Data Layer (`/src/shypn/data/`, `/src/shypn/netobjs/`)
- **Purpose**: Business logic
- **Contains**:
  - Validation
  - Type-specific behavior
  - Constraints
  - Calculations
- **Testable**: Can test without UI

## Files in This Archive

### `transition_prop_dialog_loader_original.py`
- Original monolithic version (524 lines)
- Archived: Oct 18, 2025
- All logic in one class

### `transition_prop_dialog_loader_oop_wrapper.py`
- OOP architecture wrapper (89 lines)
- Archived: Oct 18, 2025 (same day as created!)
- Delegated to `src/shypn/ui/dialogs/` (removed)
- Violated project architecture

## Lessons Learned

### What Went Wrong (Version 2)

1. **Over-engineered**: Created abstract base class for 3 dialogs
2. **Mixed Concerns**: Put business logic in UI layer (`src/shypn/ui/dialogs/`)
3. **Ignored Existing Pattern**: Didn't look at `place_prop_dialog_loader.py` first
4. **Premature Optimization**: Abstracted before seeing real patterns

### What to Do Instead

1. **Follow Existing Patterns**: Look at similar code first
2. **Keep It Simple**: Don't abstract until you have 5+ similar cases
3. **Respect Architecture**: UI code only if strictly necessary
4. **Business Logic in Data Layer**: Always

### Key Principle

> **"UI code only if strictly necessary"**
> 
> - Loaders should be thin (~200-400 lines)
> - Business logic in data objects (can be tested)
> - Validation in data layer (reusable)
> - UI just binds widgets to data

## Current Implementation Benefits

1. **Follows Project Pattern**: Consistent with other loaders
2. **Clear Separation**: Business logic in data layer, UI in helpers
3. **Easier to Understand**: No abstract base classes, simple code
4. **Context-Sensitive**: Still works, logic in `Transition.get_editable_fields()`
5. **Expression Validation**: Still works, moved to `data/validation/`
6. **YAGNI**: Don't abstract until we have 5+ dialogs with shared logic

## Migration Path (If Needed)

Old code using the OOP version (none exists yet):
```python
from shypn.ui.dialogs.transition import TransitionPropertyDialog
dialog = TransitionPropertyDialog(net_object=t, ...)
```

New code (current):
```python
from shypn.helpers.transition_prop_dialog_loader import TransitionPropDialogLoader
loader = TransitionPropDialogLoader(t, parent, ...)
loader.run()
```

The API is the same, so no migration needed if code was using the wrapper.

---

**Archived**: October 18, 2025  
**Reason**: Architectural corrections - moved business logic to data layer  
**Status**: Superseded by thin loader with data layer business logic
