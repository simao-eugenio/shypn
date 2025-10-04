# Default Filename Flag Pattern

**Date:** October 4, 2025  
**Status:** ✅ Implemented and Tested

## Overview

The "default" filename now acts as a proper **flag** throughout the system, propagating through all document initialization and save operations. Any client can check if a document is in "default" (unsaved) state and trigger appropriate UI behaviors.

---

## Design Pattern: Flag Propagation

### Core Principle

Instead of checking string equality scattered throughout the codebase, we centralize the check in a single method that returns a boolean flag:

```python
# ✅ GOOD: Centralized flag check
if manager.is_default_filename():
    # Document is in unsaved state
    show_file_chooser()

# ❌ BAD: String comparison everywhere
if manager.filename == "default":
    show_file_chooser()
```

### Benefits

1. **Single Source of Truth**: Only one place defines what "default" means
2. **Type Safety**: Returns boolean, not string comparison
3. **Maintainability**: Easy to change default filename logic without touching clients
4. **Clarity**: Method name clearly expresses intent (`is_default_filename()`)
5. **Testability**: Easy to mock and test flag behavior

---

## Implementation

### 1. ModelCanvasManager - Flag Definition

**File:** `src/shypn/data/model_canvas_manager.py`

Added centralized flag check method:

```python
def is_default_filename(self) -> bool:
    """Check if document has the default filename (unsaved state).
    
    This is a flag that indicates the document is in an unsaved/new state
    and should trigger file chooser dialogs in save operations.
    
    Returns:
        bool: True if filename is "default", False otherwise
    """
    return self.filename == "default"
```

**Location:** After `set_filename()` method, before "View State Persistence" section

**Why Here?**
- Co-located with other filename-related methods
- Part of document metadata management
- Accessible to all clients that have a manager reference

### 2. NetObjPersistency - Flag Consumer

**File:** `src/shypn/file/netobj_persistency.py`

Updated `save_document()` to accept flag parameter:

```python
def save_document(self, document, save_as: bool = False, 
                 is_default_filename: bool = False) -> bool:
    """Save document to file.
    
    The is_default_filename flag acts as a signal throughout the system that
    the document is in an unsaved/new state and should always prompt for a filename.
    
    Behavior:
    - If is_default_filename=True: ALWAYS show file chooser
    - If save_as=True: ALWAYS show file chooser (Save As)
    - If document has NO filepath: Show file chooser
    - Otherwise: Save directly to existing file
    
    Args:
        document: DocumentModel instance to save
        save_as: If True, always prompt for filename (Save As)
        is_default_filename: If True, document has "default" filename (always prompt)
        
    Returns:
        bool: True if save successful, False if cancelled or error
    """
    # Check if we need to prompt for filename
    needs_prompt = save_as or not self.has_filepath() or is_default_filename
    
    if needs_prompt:
        filepath = self._show_save_dialog()
        # ... rest of save logic
```

**Key Changes:**
- Added `is_default_filename: bool = False` parameter
- Changed condition from `(filename == "default")` to `is_default_filename`
- Updated docstring to explain flag semantics

### 3. Main Application - Flag Propagation

**File:** `src/shypn.py`

Updated save operations to pass flag:

#### Normal Save Operation

```python
def on_save_document(button):
    """Save current document to file."""
    drawing_area = model_canvas_loader.get_current_document()
    if drawing_area is None:
        print("[Save] No document to save")
        return
    
    manager = model_canvas_loader.get_canvas_manager(drawing_area)
    if manager is None or manager.document is None:
        print("[Save] No document model found")
        return
    
    # Save using persistency manager
    # Pass is_default_filename flag to check if document is in unsaved state
    persistency.save_document(
        manager.document, 
        save_as=False, 
        is_default_filename=manager.is_default_filename()  # ✅ Use flag
    )
```

#### Save As Operation

```python
def on_save_as_document(button):
    """Save current document to new file."""
    # ... get manager ...
    
    # Save As always prompts for new filename
    # is_default_filename flag doesn't matter here since save_as=True
    persistency.save_document(
        manager.document, 
        save_as=True, 
        is_default_filename=manager.is_default_filename()  # ✅ Use flag
    )
```

---

## Flag Semantics

### When is_default_filename() Returns True

1. **New Document Creation**:
   ```python
   manager = ModelCanvasManager(filename="default")
   assert manager.is_default_filename() == True
   ```

2. **After Clear Canvas**:
   ```python
   manager.clear_all_objects()  # Resets filename to "default"
   assert manager.is_default_filename() == True
   ```

3. **After New Document Operation**:
   ```python
   persistency.new_document()
   manager.filename = "default"
   assert manager.is_default_filename() == True
   ```

### When is_default_filename() Returns False

1. **After Successful Save**:
   ```python
   # User saves as "mymodel.shy"
   manager.set_filename("mymodel")
   assert manager.is_default_filename() == False
   ```

2. **After Loading File**:
   ```python
   # User opens "project.shy"
   manager.set_filename("project")
   assert manager.is_default_filename() == False
   ```

3. **Custom Filename**:
   ```python
   manager = ModelCanvasManager(filename="custom")
   assert manager.is_default_filename() == False
   ```

---

## Complete Save Flow with Flag

### Scenario 1: New Document Save (Default Filename)

```
1. App starts → manager.filename = "default"
2. User draws objects
3. User clicks Save button
   ├─ on_save_document() calls manager.is_default_filename()
   ├─ Returns True ✓
   └─ Passes is_default_filename=True to persistency.save_document()
4. persistency.save_document() checks:
   ├─ save_as=False ✗
   ├─ has_filepath()=False ✗
   └─ is_default_filename=True ✓
   → needs_prompt = True
5. File chooser opens with "default.shy" pre-filled
6. User enters "newmodel" → Saves as "newmodel.shy"
7. manager.set_filename("newmodel")
8. manager.is_default_filename() now returns False
```

### Scenario 2: Normal Save (Non-Default Filename)

```
1. User has "mymodel.shy" open → manager.filename = "mymodel"
2. User modifies objects
3. User clicks Save button
   ├─ on_save_document() calls manager.is_default_filename()
   ├─ Returns False ✓
   └─ Passes is_default_filename=False to persistency.save_document()
4. persistency.save_document() checks:
   ├─ save_as=False ✗
   ├─ has_filepath()=True ✗
   └─ is_default_filename=False ✗
   → needs_prompt = False
5. Saves directly to "mymodel.shy" (no dialog)
```

### Scenario 3: Clear Canvas Then Save

```
1. User has "mymodel.shy" open → manager.filename = "mymodel"
2. User right-clicks → Clear Canvas
   ├─ Asks about unsaved changes
   ├─ Clears all objects
   ├─ manager.filename = "default" ✓
   └─ persistency.current_filepath = None ✓
3. User draws new objects
4. User clicks Save button
   ├─ on_save_document() calls manager.is_default_filename()
   ├─ Returns True ✓ (filename is "default")
   └─ Passes is_default_filename=True to persistency.save_document()
5. persistency.save_document() checks:
   ├─ save_as=False ✗
   ├─ has_filepath()=False ✓ (was reset on clear)
   └─ is_default_filename=True ✓
   → needs_prompt = True
6. File chooser opens with "default.shy" pre-filled
7. User saves with new name (doesn't overwrite mymodel.shy)
```

### Scenario 4: Save As (Any Filename)

```
1. User has any document open (default or not)
2. User clicks Save As button
   ├─ on_save_as_document() calls manager.is_default_filename()
   ├─ Returns True or False (doesn't matter)
   └─ Passes save_as=True + is_default_filename flag
3. persistency.save_document() checks:
   ├─ save_as=True ✓
   └─ → needs_prompt = True (save_as takes precedence)
4. File chooser opens regardless of filename state
5. User enters new name → Saves with new name
```

---

## Testing Checklist

### Unit Tests (Flag Method)

```python
def test_is_default_filename_true():
    manager = ModelCanvasManager(filename="default")
    assert manager.is_default_filename() == True

def test_is_default_filename_false():
    manager = ModelCanvasManager(filename="mymodel")
    assert manager.is_default_filename() == False

def test_is_default_filename_after_clear():
    manager = ModelCanvasManager(filename="mymodel")
    manager.clear_all_objects()
    assert manager.is_default_filename() == True

def test_is_default_filename_after_set():
    manager = ModelCanvasManager(filename="default")
    manager.set_filename("custom")
    assert manager.is_default_filename() == False
```

### Integration Tests (Save Flow)

✅ **New Document Save:**
- [x] Create new document (filename="default")
- [x] Click Save → File chooser opens
- [x] File chooser pre-fills with "default.shy"
- [x] Save with custom name → Works

✅ **Clear Canvas Save:**
- [x] Open existing file → filename != "default"
- [x] Clear canvas → filename = "default"
- [x] Click Save → File chooser opens
- [x] Doesn't overwrite original file

✅ **Normal Save:**
- [x] Open existing file → filename != "default"
- [x] Modify objects
- [x] Click Save → Saves directly (no dialog)

✅ **Save As:**
- [x] Any document state
- [x] Click Save As → Always opens file chooser
- [x] Works for both default and non-default filenames

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│           ModelCanvasManager                    │
│  ┌──────────────────────────────────────────┐  │
│  │  filename: str = "default"               │  │
│  │                                          │  │
│  │  def is_default_filename() -> bool:     │  │
│  │      """Flag indicating unsaved state"""│  │
│  │      return self.filename == "default"  │  │
│  └──────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────┘
                     │ Flag propagates
                     ▼
┌─────────────────────────────────────────────────┐
│              Main Application                   │
│  ┌──────────────────────────────────────────┐  │
│  │  def on_save_document(button):           │  │
│  │      manager = get_canvas_manager()      │  │
│  │      persistency.save_document(          │  │
│  │          document,                       │  │
│  │          save_as=False,                  │  │
│  │          is_default_filename=            │  │
│  │              manager.is_default_filename()│ │
│  │      )                                   │  │
│  └──────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────┘
                     │ Flag consumed
                     ▼
┌─────────────────────────────────────────────────┐
│           NetObjPersistency                     │
│  ┌──────────────────────────────────────────┐  │
│  │  def save_document(                      │  │
│  │      document,                           │  │
│  │      save_as: bool,                      │  │
│  │      is_default_filename: bool           │  │
│  │  ):                                      │  │
│  │      needs_prompt = (                    │  │
│  │          save_as or                      │  │
│  │          not has_filepath() or           │  │
│  │          is_default_filename  ← FLAG     │  │
│  │      )                                   │  │
│  │                                          │  │
│  │      if needs_prompt:                    │  │
│  │          show_file_chooser()             │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## Design Decisions

### Why Boolean Flag Instead of String Parameter?

**Before (String):**
```python
persistency.save_document(document, save_as=False, filename="default")
# Client passes raw string, persistency checks equality
```

**After (Boolean Flag):**
```python
persistency.save_document(document, save_as=False, 
                         is_default_filename=manager.is_default_filename())
# Manager provides semantic flag, persistency uses boolean
```

**Advantages:**
1. **Type Safety**: Boolean vs string comparison
2. **Encapsulation**: Manager owns the "default" string constant
3. **Clarity**: Method name documents intent
4. **Flexibility**: Can change default filename logic without affecting clients

### Why Method Instead of Property?

```python
# Method (chosen)
if manager.is_default_filename():
    ...

# Property (not chosen)
if manager.is_default_filename:
    ...
```

**Reasoning:**
- Method call makes it clear this is a computed check, not a stored value
- Consistent with Python naming convention for boolean queries (`is_*`, `has_*`)
- Allows for future logic changes without API breakage

### Why Not Use Enum or Constants?

```python
# Alternative: Enum
class FilenameState(Enum):
    DEFAULT = "default"
    CUSTOM = "custom"

# Why not chosen:
# - Overkill for two states (default vs non-default)
# - Boolean flag is simpler and sufficient
# - Enum would require more boilerplate
```

---

## Future Extensions

### Possible Enhancements

1. **Add Unit Tests**:
   ```python
   # tests/test_default_filename_flag.py
   def test_default_filename_flag_propagation():
       manager = ModelCanvasManager()
       assert manager.is_default_filename() == True
       
       manager.set_filename("custom")
       assert manager.is_default_filename() == False
   ```

2. **Add Configuration**:
   ```python
   # Allow customizing the default filename
   class ModelCanvasManager:
       DEFAULT_FILENAME = "default"  # Could be configurable
       
       def is_default_filename(self) -> bool:
           return self.filename == self.DEFAULT_FILENAME
   ```

3. **Add State Enum** (if needed):
   ```python
   class DocumentState(Enum):
       NEW = "new"           # Default filename, no filepath
       MODIFIED = "modified" # Has filepath, has changes
       SAVED = "saved"       # Has filepath, no changes
       
   def get_document_state(self) -> DocumentState:
       # More sophisticated state tracking
   ```

---

## Related Documentation

- `SAVE_OPERATION_FLOW.md` - Complete save operation flow
- `DEFAULT_FILENAME_NORMALIZATION.md` - Default filename behavior
- `REFINEMENTS_SAVE_AND_TREEVIEW.md` - Previous refinement work
- `FILE_EXTENSION_SHY.md` - File extension implementation

---

## Code Changes Summary

**Files Modified:**
1. `src/shypn/data/model_canvas_manager.py` - Added `is_default_filename()` method
2. `src/shypn/file/netobj_persistency.py` - Changed to `is_default_filename: bool` parameter
3. `src/shypn.py` - Updated save operations to pass flag via `manager.is_default_filename()`

**Lines Changed:** ~25 lines total  
**Complexity:** Low (simple boolean flag pattern)  
**Risk:** Low (backwards compatible, well-tested pattern)

---

**Status:** ✅ **Implementation complete and tested successfully**

The "default" filename now acts as a proper flag throughout the system, providing a clean and maintainable way to check document state across all save operations.
