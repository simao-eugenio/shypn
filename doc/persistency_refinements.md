# NetObjPersistency Refinements

## Date
October 4, 2025

## Refinements Overview

Two important refinements to file operations behavior:

### 1. File Operations Root Directory: `repo_root/models` 📁

**Requirement:** "File operations must point to repo root/models as the root for file operations"

**Implementation:**
- File dialogs (Save/Open) now default to `repo_root/models` directory
- Models directory is automatically created if it doesn't exist
- Organizes all Petri net files in one centralized location
- Separates models from code, documentation, and other files

**Benefits:**
- ✅ **Organization:** All Petri nets in one place
- ✅ **Consistency:** Always starts in same location
- ✅ **Clean separation:** Models folder separate from src, doc, tests
- ✅ **User-friendly:** Users know where their files are
- ✅ **Version control friendly:** Easy to .gitignore or track models separately

### 2. No Default Filename 🚫

**Requirement:** "Default file name must trigger user to enter a real file name"

**Implementation:**
- Removed automatic "petri_net.json" default filename
- User MUST type a filename when saving new documents
- Only pre-fills filename for "Save As" on existing files
- Prevents accidental auto-save without user confirmation

**Benefits:**
- ✅ **Intentional naming:** Users choose meaningful filenames
- ✅ **No accidental saves:** Can't accidentally save as "petri_net.json"
- ✅ **Better organization:** Users create descriptive filenames
- ✅ **Safe:** No auto-save without explicit user action

## Implementation Details

### NetObjPersistency Constructor

**Before:**
```python
def __init__(self, parent_window: Optional[Gtk.Window] = None):
    self.parent_window = parent_window
    self.current_filepath = None
    self._is_dirty = False
    self._last_directory = None  # No default
```

**After:**
```python
def __init__(self, parent_window: Optional[Gtk.Window] = None, 
             models_directory: Optional[str] = None):
    self.parent_window = parent_window
    self.current_filepath = None
    self._is_dirty = False
    
    # Setup models directory (repo_root/models)
    if models_directory is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
        models_directory = os.path.join(repo_root, 'models')
    
    self.models_directory = models_directory
    
    # Create models directory if it doesn't exist
    if not os.path.exists(self.models_directory):
        os.makedirs(self.models_directory)
    
    # Last directory starts at models directory
    self._last_directory = self.models_directory
```

### Save Dialog

**Before:**
```python
def _show_save_dialog(self):
    dialog = Gtk.FileChooserDialog(...)
    
    # Set default filename
    if self.current_filepath:
        dialog.set_filename(self.current_filepath)
    else:
        dialog.set_current_name("petri_net.json")  # ❌ Auto-default
    
    # Set initial directory
    if self._last_directory and os.path.isdir(self._last_directory):
        dialog.set_current_folder(self._last_directory)
```

**After:**
```python
def _show_save_dialog(self):
    dialog = Gtk.FileChooserDialog(...)
    
    # Set initial directory to models directory or last used
    if self._last_directory and os.path.isdir(self._last_directory):
        dialog.set_current_folder(self._last_directory)
    elif os.path.isdir(self.models_directory):
        dialog.set_current_folder(self.models_directory)  # ✅ Models dir
    
    # Set filename only for existing files (Save As)
    if self.current_filepath:
        dialog.set_filename(self.current_filepath)
    else:
        # ✅ No default filename - user MUST enter a name
        pass
    
    # Update last directory after selection
    if filepath:
        self._last_directory = os.path.dirname(filepath)
```

### Open Dialog

**Before:**
```python
def _show_open_dialog(self):
    dialog = Gtk.FileChooserDialog(...)
    
    # Set initial directory
    if self._last_directory and os.path.isdir(self._last_directory):
        dialog.set_current_folder(self._last_directory)
```

**After:**
```python
def _show_open_dialog(self):
    dialog = Gtk.FileChooserDialog(...)
    
    # Set initial directory to models directory or last used
    if self._last_directory and os.path.isdir(self._last_directory):
        dialog.set_current_folder(self._last_directory)
    elif os.path.isdir(self.models_directory):
        dialog.set_current_folder(self.models_directory)  # ✅ Models dir
    
    # Update last directory after selection
    if filepath:
        self._last_directory = os.path.dirname(filepath)
```

### create_persistency_manager Function

**Before:**
```python
def create_persistency_manager(parent_window=None):
    return NetObjPersistency(parent_window)
```

**After:**
```python
def create_persistency_manager(parent_window=None, models_directory=None):
    return NetObjPersistency(parent_window, models_directory)
```

## Usage Examples

### Default Behavior (repo_root/models)

```python
# Create persistency manager with default models directory
persistency = create_persistency_manager(parent_window=window)

# Save dialog will open in: /home/user/project/models/
# User must type filename (no default)
persistency.save_document(document)

# Open dialog will open in: /home/user/project/models/
# Shows all .json files in models directory
document, filepath = persistency.load_document()
```

### Custom Models Directory

```python
# Use custom models directory
custom_models = "/home/user/my_petri_nets"
persistency = create_persistency_manager(
    parent_window=window,
    models_directory=custom_models
)

# Save/Open will use custom directory
persistency.save_document(document)
```

### Directory Memory

```python
persistency = create_persistency_manager(parent_window=window)

# First save: opens in /home/user/project/models/
# User saves to: /home/user/project/models/subfolder/model1.json
persistency.save_document(document)

# Second save: opens in /home/user/project/models/subfolder/
# (Remembers last used directory)
persistency.save_document(another_document)

# Open: also opens in /home/user/project/models/subfolder/
# (Uses same last directory)
document, filepath = persistency.load_document()
```

## User Experience

### First Save (New Document)

1. User clicks [Save] button
2. File chooser dialog opens in `repo_root/models/`
3. **Filename field is EMPTY** - user must type a name
4. User types: "producer_consumer"
5. System auto-adds `.json` extension
6. File saved to: `repo_root/models/producer_consumer.json`

### Subsequent Save

1. User clicks [Save] button
2. **No dialog** - saves to same location
3. File updated: `repo_root/models/producer_consumer.json`

### Save As

1. User clicks [Save As] button
2. File chooser dialog opens in `repo_root/models/` (or last used directory)
3. **Filename pre-filled** with current name: "producer_consumer.json"
4. User can change name: "producer_consumer_v2"
5. File saved to: `repo_root/models/producer_consumer_v2.json`

### Open

1. User clicks [Open] button
2. File chooser dialog opens in `repo_root/models/` (or last used directory)
3. Shows all `.json` files in models directory
4. User selects file
5. Document loaded in new tab

## File Organization

```
project_root/
├── models/                       ← File operations root
│   ├── producer_consumer.json
│   ├── dining_philosophers.json
│   ├── mutex.json
│   └── experiments/
│       ├── test1.json
│       └── test2.json
├── src/
│   └── shypn/
│       └── file/
│           └── netobj_persistency.py
├── doc/
├── tests/
└── ui/
```

## Testing

**Test File:** `tests/test_persistency_refinements.py`

**Results:** All 5 tests pass! 🎉

```
✅ Models directory configuration
✅ File dialogs use models directory
✅ No default filename
✅ create_persistency_manager signature
✅ Models directory path calculation
```

## Benefits Summary

### For Users

- 🎯 **Know where files are:** Always in `models/` directory
- 📝 **Meaningful names:** Must type descriptive filenames
- 🛡️ **Safe:** No accidental auto-saves
- 🔍 **Easy to find:** All models in one place
- 📂 **Organized:** Can create subdirectories in `models/`

### For Developers

- 🧹 **Clean separation:** Models separate from code
- 🔧 **Easy to configure:** Can override models directory
- 📦 **Version control:** Easy to .gitignore or track separately
- 🧪 **Testable:** Directory behavior well-defined
- 📚 **Documented:** Clear behavior and expectations

### For Project Organization

- ✅ **Consistent structure:** All projects use same layout
- ✅ **Portable:** Models directory moves with project
- ✅ **Shareable:** Easy to share just the models directory
- ✅ **Backup-friendly:** One directory to backup
- ✅ **CI/CD friendly:** Known location for test models

## Comparison: Before vs After

| Aspect | Before | After |
|--------|--------|-------|
| **Save dialog location** | Last used (anywhere) | `models/` directory |
| **Open dialog location** | Last used (anywhere) | `models/` directory |
| **Default filename** | "petri_net.json" | None (must type) |
| **File organization** | Scattered | Centralized in `models/` |
| **User awareness** | Where did I save? | Always in `models/` |
| **Accidental saves** | Easy to auto-save | Must confirm name |

## Migration Notes

### Existing Projects

If you have existing Petri net files outside the `models/` directory:

1. Create `models/` directory in project root
2. Move existing `.json` files to `models/`
3. Update any hardcoded paths in scripts/tests
4. Persistency manager will use `models/` automatically

### Custom Locations

If you need a different location:

```python
# Use custom directory
persistency = create_persistency_manager(
    parent_window=window,
    models_directory="/path/to/custom/location"
)
```

## Conclusion

Both refinements improve the user experience and project organization:

1. **Models directory root** ensures all files are organized in one place
2. **No default filename** ensures users create meaningful, intentional filenames

These changes make the application more professional, user-friendly, and maintainable.

✅ **Refinements implemented and tested successfully!**
