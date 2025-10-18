# Deprecated Dialog Code

This directory contains the original implementations of property dialogs before the OOP refactoring.

## What Was Moved Here

### `transition_prop_dialog_loader_original.py`
- **Original Location**: `src/shypn/helpers/transition_prop_dialog_loader.py`
- **Date Moved**: October 18, 2025
- **Reason**: Replaced with modular OOP architecture
- **New Location**: `src/shypn/ui/dialogs/transition/transition_property_dialog.py`
- **Lines of Code**: ~524 lines (old monolithic implementation)

## Why This Code Was Deprecated

The original dialog loaders had several issues:
1. **Monolithic Design**: All logic in single large class (500+ lines)
2. **No Separation of Concerns**: UI loading, validation, and business logic mixed
3. **Hard to Extend**: Adding new transition types required modifying large class
4. **Code Duplication**: Similar code repeated across place/transition/arc dialogs
5. **No Type-Specific Behavior**: All transition types used same fields (not context-sensitive)

## New Architecture

The refactored code follows clean OOP principles:

```
src/shypn/ui/dialogs/
├── base/
│   ├── property_dialog_base.py       # Abstract base class (~350 lines)
│   └── expression_validator.py       # Shared validation (~250 lines)
├── transition/
│   └── transition_property_dialog.py # Type-aware dialog (~450 lines)
├── place/
│   └── place_property_dialog.py      # Place-specific (future)
└── arc/
    └── arc_property_dialog.py        # Arc-specific (future)
```

### Benefits of New Architecture:

1. **Modular**: Each component has single responsibility
2. **Extensible**: Add new transition types by subclassing
3. **Context-Sensitive**: UI adapts to transition type
4. **DRY**: Common logic in base class, no duplication
5. **Testable**: Each component can be tested independently
6. **Type-Safe**: Expression validation with AST checking
7. **Maintainable**: Smaller, focused classes easier to understand

## Backward Compatibility

The new `transition_prop_dialog_loader.py` is a thin wrapper (~90 lines) that:
- Maintains old API for existing code
- Delegates to new OOP implementation
- Marked as `DEPRECATED` to guide migration
- Zero functional changes - fully compatible

## Migration Guide

**Old Code:**
```python
from shypn.helpers.transition_prop_dialog_loader import TransitionPropDialogLoader

dialog = TransitionPropDialogLoader(
    transition_obj=transition,
    parent_window=window,
    persistency_manager=persistency,
    model=canvas_manager
)
dialog.run()
```

**New Code (Recommended):**
```python
from shypn.ui.dialogs.transition import TransitionPropertyDialog

dialog = TransitionPropertyDialog(
    net_object=transition,
    parent_window=window,
    persistency_manager=persistency,
    model=canvas_manager
)
dialog.run()
```

The only difference is the import path and `net_object` parameter name (was `transition_obj`).

## What's Next

Future work will:
1. Refactor Place and Arc dialogs to use same base class
2. Add type-specific subclasses for each transition type:
   - `ImmediateTransitionDialog`
   - `TimedTransitionDialog`
   - `StochasticTransitionDialog`
   - `ContinuousTransitionDialog`
3. Remove backward compatibility wrappers in v3.0
4. Update all calling code to use new API

## Files in This Directory

- **transition_prop_dialog_loader_original.py**: Original 524-line monolithic implementation
- **place_prop_dialog_loader_original.py**: (Future) Original place dialog
- **arc_prop_dialog_loader_original.py**: (Future) Original arc dialog

These files are kept for reference and can be safely deleted after v3.0 release.

---

**Branch**: `feature/property-dialogs-and-simulation-palette`  
**Refactoring Phase**: 5A - Context-Sensitive Property Dialogs  
**Date**: October 18, 2025
