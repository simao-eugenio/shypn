# TreeView Context Menu - Visual Guide

## Context Menu Structure

```
┌─────────────────────────────┐
│  File Explorer Context Menu │
├─────────────────────────────┤
│ 📂 Open                     │  ← Opens .shy file in canvas
│ 📄 New File                 │  ← Creates new .shy file (inline edit)
│ 📁 New Folder               │  ← Creates new folder (inline edit)
│ 💾 Save                     │  ← Saves current document
│ 💾 Save As...               │  ← Save with new name
├─────────────────────────────┤  ← SEPARATOR: File Operations
│ ✏️  Rename                  │  ← Renames selected item
│ 🗑️  Delete                  │  ← Deletes selected item
│ 📋 Duplicate                │  ← Creates copy of item
├─────────────────────────────┤  ← SEPARATOR: File Modifications
│ ✂️  Cut                     │  ← Cuts to clipboard
│ 📄 Copy                     │  ← Copies to clipboard
│ 📌 Paste                    │  ← Pastes from clipboard
├─────────────────────────────┤  ← SEPARATOR: Editing Operations
│ 🔄 Refresh                  │  ← Reloads directory
│ ℹ️  Properties              │  ← Shows item properties
└─────────────────────────────┘
```

## Inline Editing Flow

### Creating a New File

```
1. Initial State:
   ┌────────────────────┐
   │ 📁 my_project      │
   │   📁 models        │
   │   📄 readme.md     │
   └────────────────────┘

2. Right-click on "models" → Select "New File"
   ┌────────────────────┐
   │ 📁 my_project      │
   │   📁 models        │
   │     📄 [new_file.shy]  ← Editable!
   │   📄 readme.md     │
   └────────────────────┘

3. Type name "traffic_light" and press Enter
   ┌────────────────────┐
   │ 📁 my_project      │
   │   📁 models        │
   │     📄 traffic_light.shy  ← Created!
   │   📄 readme.md     │
   └────────────────────┘
```

### Creating a New Folder

```
1. Initial State:
   ┌────────────────────┐
   │ 📁 my_project      │
   │   📁 models        │
   │   📄 readme.md     │
   └────────────────────┘

2. Right-click on empty space → Select "New Folder"
   ┌────────────────────┐
   │ 📁 my_project      │
   │   📁 models        │
   │   📄 readme.md     │
   │   📁 [New Folder]   ← Editable!
   └────────────────────┘

3. Type name "experiments" and press Enter
   ┌────────────────────┐
   │ 📁 my_project      │
   │   📁 experiments   ← Created!
   │   📁 models        │
   │   📄 readme.md     │
   └────────────────────┘
```

## Keyboard Shortcuts

```
┌────────────────┬─────────────────────────────┐
│ Key            │ Action                      │
├────────────────┼─────────────────────────────┤
│ Right-click    │ Show context menu           │
│ Enter          │ Confirm inline edit         │
│ Escape         │ Cancel inline edit          │
│ F2             │ Rename selected item        │
│ Delete         │ Delete selected item        │
└────────────────┴─────────────────────────────┘
```

## Context-Aware Behavior

### When Right-Clicking on a File

```
Selected: 📄 my_model.shy
Context: File in "models" folder

Menu Behavior:
✅ Open           → Opens this file
✅ New File       → Creates sibling in same folder
✅ New Folder     → Creates sibling folder
✅ Save           → Saves current canvas document
✅ Save As        → Save As current document
✅ Rename         → Renames this file
✅ Delete         → Deletes this file
✅ Duplicate      → Creates copy
✅ Cut/Copy       → Operates on this file
```

### When Right-Clicking on a Folder

```
Selected: 📁 models
Context: Folder in project

Menu Behavior:
✅ Open           → Navigates into folder
✅ New File       → Creates file INSIDE this folder
✅ New Folder     → Creates folder INSIDE this folder
✅ Save           → Saves current canvas document
✅ Save As        → Save As current document
✅ Rename         → Renames this folder
✅ Delete         → Deletes this folder
✅ Duplicate      → Creates copy
✅ Cut/Copy       → Operates on this folder
```

### When Right-Clicking on Empty Space

```
Selected: (nothing)
Context: Current directory

Menu Behavior:
✅ New File       → Creates file in current directory
✅ New Folder     → Creates folder in current directory
✅ Save           → Saves current canvas document
✅ Save As        → Save As current document
✅ Paste          → Pastes clipboard to current directory
✅ Refresh        → Reloads tree view
❌ Open/Rename/Delete/Duplicate → Disabled
```

## File Operations Integration

```
┌──────────────────────────────────────────────────────────┐
│                  User Action Flow                         │
└──────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│              Right-Click Context Menu                     │
│  [Groups: File Ops | Modifications | Editing | View]     │
└──────────────────────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌─────────────────┐ ┌──────────────┐ ┌────────────────┐
│  Inline Edit    │ │ File System  │ │   Canvas       │
│  Operations     │ │  Operations  │ │  Operations    │
└─────────────────┘ └──────────────┘ └────────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────────┐ ┌──────────────┐ ┌────────────────┐
│ • New File      │ │ • Cut/Copy   │ │ • Open         │
│ • New Folder    │ │ • Paste      │ │ • Save         │
│ • Rename        │ │ • Delete     │ │ • Save As      │
└─────────────────┘ └──────────────┘ └────────────────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           ▼
              ┌────────────────────────┐
              │  FileExplorerPanel     │
              │  (Controller)          │
              └────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌─────────────────┐ ┌──────────────┐ ┌────────────────┐
│ DocumentModel   │ │ os/shutil    │ │ Canvas Loader  │
│ (Persistence)   │ │ (File Sys)   │ │ (Canvas Mgmt)  │
└─────────────────┘ └──────────────┘ └────────────────┘
```

## Error Handling Examples

### Duplicate Name
```
User tries to create: "my_model.shy"
But file already exists!

Result:
┌─────────────────────────────────────┐
│ ⚠️  Error                           │
├─────────────────────────────────────┤
│ 'my_model.shy' already exists       │
│                                     │
│              [ OK ]                 │
└─────────────────────────────────────┘
```

### Empty Name
```
User presses Enter without typing anything

Result:
• Temporary row silently removed
• No error message
• Tree view unchanged
```

### Invalid File Type
```
User tries to open: "document.pdf"

Result:
┌─────────────────────────────────────┐
│ ⚠️  Error                           │
├─────────────────────────────────────┤
│ Can only open .shy Petri net files  │
│                                     │
│              [ OK ]                 │
└─────────────────────────────────────┘
```

## Implementation Details

### TreeStore Structure
```
Column 0: icon_name (str)     → "folder" or "text-x-generic"
Column 1: name (str)          → "my_model.shy"
Column 2: path (str)          → "/home/user/project/my_model.shy"
Column 3: is_dir (bool)       → False
```

### Inline Edit State
```python
self.editing_iter        # TreeIter being edited
self.editing_parent_dir  # "/home/user/project/models"
self.editing_is_folder   # False (for files) or True (for folders)
```

### Cell Renderer Configuration
```python
text_renderer.set_property("editable", False)  # Default
# Only set to True when starting inline edit
text_renderer.set_property("editable", True)   # During edit
```

## Benefits Summary

✅ **User Experience**
- Faster file creation (no dialogs)
- Clear menu organization
- Context-aware behavior

✅ **Integration**
- Seamless with existing file operations
- Works with ModelCanvasManager
- Uses DocumentModel for persistence

✅ **Error Prevention**
- Validates names before creation
- Prevents duplicates
- Shows clear error messages

✅ **Maintainability**
- Clean separation of concerns
- Well-documented code
- Extensible architecture
