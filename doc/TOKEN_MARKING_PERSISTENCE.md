# Token Marking Persistence

## Overview

The SHYPN application correctly saves and restores place tokens (markings) across all file operations. This document explains how token persistence works.

## Token Storage

Each Place object maintains two token-related properties:

1. **`tokens`** - Current marking (number of tokens)
2. **`initial_marking`** - Baseline marking for simulation reset

## Persistence Flow

### Saving

When a document is saved (Ctrl+S, Save As, etc.):

1. `DocumentModel.to_dict()` serializes all places
2. `Place.to_dict()` includes:
   ```python
   {
       "marking": self.tokens,          # Current token count
       "initial_marking": self.initial_marking  # Baseline for reset
   }
   ```
3. JSON file is written with both values

### Loading

When a document is loaded:

1. `DocumentModel.load_from_file()` deserializes JSON
2. `Place.from_dict()` restores:
   ```python
   place.tokens = data["marking"]
   place.initial_marking = data["initial_marking"]
   ```
3. If `initial_marking` not present (old format), uses current `marking` as initial

## User Token Editing

### Properties Dialog

When user edits tokens via Place Properties dialog (`place_prop_dialog_loader.py`):

```python
def _apply_changes(self):
    # User enters new token value
    tokens_value = int(tokens_entry.get_text())
    
    # Update both current and initial marking
    self.place_obj.tokens = tokens_value
    self.place_obj.initial_marking = self.place_obj.tokens
    
    # Mark document as dirty (needs save)
    self.persistency_manager.mark_dirty()
```

**Key behavior**: When user manually sets tokens, BOTH `tokens` and `initial_marking` are updated. This makes the new value the baseline for future simulation resets.

## Simulation Token Changes

During simulation, transitions modify tokens:

```python
# Immediate/Timed/Stochastic behaviors
source_place.set_tokens(source_place.tokens - arc.weight)
target_place.set_tokens(target_place.tokens + arc.weight)
```

**Key behavior**: Simulation only updates `tokens`, NOT `initial_marking`. This allows reset to return to user-defined baseline.

## Simulation Reset

When simulation is reset:

```python
def reset_to_initial_marking(self):
    self.tokens = self.initial_marking
```

This restores tokens to the last user-defined value (from properties dialog or file load).

## File Operation Scenarios

### Scenario 1: New Model Creation
1. User creates places with default tokens = 0
2. User edits Place properties, sets tokens = 5
3. Save → stores `marking: 5, initial_marking: 5`
4. Reopen → restores tokens = 5

### Scenario 2: Simulation Run
1. Load model with tokens = 5
2. Run simulation → tokens change to 3
3. Save → stores `marking: 3, initial_marking: 5`
4. Reopen → restores tokens = 3
5. User can reset to initial_marking = 5

### Scenario 3: Token Edit After Simulation
1. Simulation leaves tokens = 3
2. User edits properties, sets tokens = 10
3. Save → stores `marking: 10, initial_marking: 10`
4. Reopen → restores tokens = 10
5. New baseline is 10 (not old value of 5)

## Implementation Files

- **Place model**: `src/shypn/netobjs/place.py`
  - `to_dict()` - Serialization
  - `from_dict()` - Deserialization
  - `set_tokens()` - Update current marking
  - `set_initial_marking()` - Update baseline
  - `reset_to_initial_marking()` - Reset to baseline

- **Properties dialog**: `src/shypn/helpers/place_prop_dialog_loader.py`
  - `_apply_changes()` - Updates both tokens and initial_marking

- **Document model**: `src/shypn/data/canvas/document_model.py`
  - `save_to_file()` - JSON serialization
  - `load_from_file()` - JSON deserialization

- **File operations**: `src/shypn/file/netobj_persistency.py`
  - `save_document()` - Handles Save/Save As
  - `load_document()` - Handles Open

## Verification

To verify token persistence:

1. Create a place
2. Set tokens to 5 via properties dialog
3. Save file
4. Close and reopen file
5. ✅ Place should have 5 tokens

Or:

1. Load existing model
2. Run simulation (tokens change)
3. Save file
4. Reopen file
5. ✅ Tokens should match what they were when saved
6. ✅ Simulation reset should restore to initial_marking

## Conclusion

Token marking persistence is **fully implemented** and working correctly. All save operations (Save, Save As, Auto-save) preserve the current token state and initial marking baseline.
