# File Explorer - Project vs File Operations

**Date**: 2025-01-08  
**Question**: Can file operations be done over projects or only over files?  

## Current Status: ✅ Operations Work on Both

The file explorer **already supports operations on both files AND directories (projects)**. However, there are some important distinctions and limitations.

---

## Available Operations

### Context Menu Options

When you right-click in the file explorer, you get:

```
┌─────────────────────────┐
│ Open                    │  ← Files only
│ New File                │
│ New Folder              │
├─────────────────────────┤
│ Rename                  │  ← Files AND folders ✅
│ Delete                  │  ← Files AND folders ✅
├─────────────────────────┤
│ Refresh                 │
│ Properties              │  ← Files AND folders ✅
└─────────────────────────┘
```

---

## Operation Details

### 1. ✅ Rename - Works on Both Files and Folders

**Code**: `FileExplorer.rename_item(old_path, new_name)`

**Capabilities**:
- ✅ Rename .shy files
- ✅ Rename folders (projects)
- ✅ Sanitizes names (removes /, \)
- ✅ Prevents conflicts (checks if name exists)

**Example Usage**:
```
Right-click on: workspace/projects/OldProjectName/
Select: Rename
Enter: NewProjectName
Result: ✅ Project folder renamed
```

**Limitations**:
- Cannot rename if target name already exists
- Cannot use special characters in names

---

### 2. ✅ Delete - Works on Both Files and Folders

**Code**: `FileExplorer.delete_item(path)`

**Capabilities**:
- ✅ Delete .shy files
- ✅ Delete folders (projects) - **ONLY IF EMPTY**
- ✅ Safety check for non-empty directories
- ✅ Permission checking

**For Files**:
```
Right-click on: model.shy
Select: Delete
Confirmation: "This file will be permanently deleted."
Result: ✅ File deleted
```

**For Folders (Empty)**:
```
Right-click on: EmptyProjectFolder/
Select: Delete
Confirmation: "This folder will be deleted. Only empty folders can be deleted."
Result: ✅ Empty folder deleted
```

**For Folders (Non-Empty)**:
```
Right-click on: MyProject/ (contains files)
Select: Delete
Confirmation dialog appears
Click Yes
Result: ❌ Error: "Cannot delete non-empty folder"
```

**Safety Measure**:
```python
def delete_item(self, path: str) -> bool:
    if os.path.isdir(path):
        # Check if directory is empty
        if os.listdir(path):
            if self.on_error:
                self.on_error("Cannot delete non-empty folder")
            return False  # ← Prevents accidental project deletion
        os.rmdir(path)
```

---

### 3. ✅ Properties - Works on Both Files and Folders

**Code**: `FileExplorer.get_file_info(path)`

**For Files**:
```
Name: model.shy
Type: File
Location: /workspace/projects/MyProject/models/
Size: 4.2 KB
Modified: 2025-01-08 14:30
Created: 2025-01-07 10:15
Permissions: rw-r--r--
Access: Read, Write
```

**For Folders (Projects)**:
```
Name: MyProject
Type: Folder
Location: /workspace/projects/
Items: 15
Modified: 2025-01-08 14:30
Created: 2025-01-07 10:15
Permissions: rwxr-xr-x
Access: Read, Write, Execute
```

---

### 4. ❌ Open - Files Only

**Limitation**: The "Open" action only works on `.shy` files, not folders.

**Code**:
```python
def _on_context_open_clicked(self, button):
    """Handle 'Open' from context menu - opens file in canvas."""
    if self.selected_item_path and (not self.selected_item_is_dir):
        if not self.selected_item_path.endswith('.shy'):
            if self.explorer.on_error:
                self.explorer.on_error('Can only open .shy Petri net files')
            return
        # ... open file logic ...
```

**Behavior**:
- Right-click on `.shy` file → Open ✅ (opens in canvas)
- Right-click on folder → Open is available but does nothing ❌
- Double-click on folder → Navigates into folder ✅

---

### 5. ✅ New File / New Folder - Works Anywhere

**Create in Current Directory**:
```
Right-click on empty space
Select: New Folder
Result: ✅ Creates folder in current directory
```

**Create Inside Selected Folder**:
```
Right-click on: MyProject/
Select: New Folder
Result: ✅ Creates folder inside MyProject/
```

**Inline Editing**:
- Creates temporary entry in tree
- User edits name inline
- Creates actual folder/file on Enter
- Cancels on Escape

---

## Project-Specific Operations

### Creating a Project Structure

**Current Way** (Manual):
```
1. Right-click in workspace/projects/
2. Select: New Folder
3. Name it: MyNewProject
4. Navigate into MyNewProject/
5. Right-click → New Folder → "models"
6. Right-click → New Folder → "pathways"
7. Right-click → New Folder → "simulations"
etc.
```

### Renaming a Project

**Works!** ✅
```
Right-click on: workspace/projects/OldName/
Select: Rename
Enter: NewName
Result: Project folder renamed
```

**Considerations**:
- Project references in `project_index.json` need manual update
- Recent projects list won't update automatically
- Open files from old project path will break

### Deleting a Project

**Partial Support** ⚠️
```
Empty Project:
Right-click → Delete → ✅ Works

Non-Empty Project:
Right-click → Delete → ❌ "Cannot delete non-empty folder"
```

**To Delete Non-Empty Project**:
1. Delete all files inside (manually)
2. Delete all subfolders (manually)
3. Then delete project folder

---

## What's Missing for Full Project Support

### 1. ❌ "Open Project" Action

**Current**: No way to "activate" a project from file explorer  
**Desired**: Right-click project folder → "Open Project"

**Would do**:
- Load `project.shy` metadata
- Set as current project in ProjectManager
- Update persistency to use project's models directory
- Show project info in UI

### 2. ❌ "Create New Project" Action

**Current**: Must manually create folder structure  
**Desired**: Right-click → "New Project..."

**Would do**:
- Show dialog for project name/description
- Create folder structure automatically:
  ```
  MyProject/
  ├── project.shy
  ├── models/
  ├── pathways/
  ├── simulations/
  ├── exports/
  └── metadata/
  ```
- Register in `project_index.json`
- Set as current project

### 3. ❌ "Delete Project" (Recursive)

**Current**: Can only delete empty folders  
**Desired**: Right-click project → "Delete Project..."

**Would do**:
- Show warning about contents
- Recursively delete all contents
- Remove from `project_index.json`
- Remove from recent projects

### 4. ❌ Project-Aware Context Menu

**Current**: Same menu for all items  
**Desired**: Different menu for project folders

**Project Context Menu** (proposed):
```
┌──────────────────────────┐
│ Open Project             │  ← Activate project
│ Close Project            │  ← Deactivate
├──────────────────────────┤
│ New Model                │  ← Create in models/
│ New Pathway              │  ← Create in pathways/
├──────────────────────────┤
│ Rename Project           │  ← Updates references
│ Delete Project           │  ← Recursive delete
├──────────────────────────┤
│ Project Properties       │  ← Show project.shy info
│ Export Project           │  ← Archive project
└──────────────────────────┘
```

### 5. ❌ Visual Project Indication

**Current**: Projects look like regular folders  
**Desired**: Special icon/badge for project folders

**Could show**:
- Different icon for project folders
- Badge/emblem indicating active project
- Color coding for project types

---

## Recommendations

### Short-Term (Easy Improvements)

1. **Detect Project Folders**
```python
def is_project_folder(path: str) -> bool:
    """Check if folder is a project (contains project.shy)."""
    project_file = os.path.join(path, 'project.shy')
    return os.path.exists(project_file)
```

2. **Add "Open Project" to Context Menu**
```python
# In _setup_context_menu()
if self.selected_item_is_dir and is_project_folder(self.selected_item_path):
    menu_item = Gtk.MenuItem(label='Open Project')
    menu_item.connect('activate', self._on_open_project_clicked)
    self.context_menu.append(menu_item)
```

3. **Distinguish Projects Visually**
```python
# Different icon for projects
if is_project_folder(full_path):
    icon_name = 'folder-documents'  # or 'application-x-archive'
else:
    icon_name = 'folder'
```

### Medium-Term (More Complex)

4. **Project Creation Wizard**
   - Dialog with name/description fields
   - Auto-create folder structure
   - Register in project_index.json

5. **Smart Project Deletion**
   - Detect if deleting a project
   - Show special warning
   - Option to delete contents
   - Clean up project_index.json

6. **Project Context Menu**
   - Different menu for project folders
   - Project-specific actions
   - Integration with ProjectManager

### Long-Term (Full Integration)

7. **Project Explorer Panel**
   - Separate from file explorer
   - Shows project hierarchy
   - Quick project switching
   - Recent projects list

8. **Project Properties Dialog**
   - View/edit project.shy
   - Manage project settings
   - View statistics
   - Manage tags

---

## Summary

### Current Capabilities

| Operation | Files | Empty Folders | Non-Empty Folders (Projects) |
|-----------|-------|---------------|------------------------------|
| **Open** | ✅ Yes | ❌ No | ❌ No |
| **Rename** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Delete** | ✅ Yes | ✅ Yes | ❌ No (safety) |
| **Properties** | ✅ Yes | ✅ Yes | ✅ Yes |
| **New File/Folder** | ✅ Yes | ✅ Yes | ✅ Yes |

### What Works Today

✅ **You can do file operations on project folders!**
- Rename projects (folder rename)
- View project properties
- Create files/folders inside projects
- Delete empty project folders

### What's Limited

⚠️ **Projects are treated as regular folders**
- No "Open Project" to activate them
- No project-specific actions
- No automatic structure creation
- Can't delete non-empty projects easily
- No visual distinction

### Bottom Line

**File operations work on both files and directories (projects), but there's no special project-aware functionality yet.** Projects are just folders with a specific structure, and the file explorer treats them as such.

For full project support, you'd want to:
1. Detect project folders (presence of `project.shy`)
2. Provide project-specific context menu
3. Integrate with `ProjectManager`
4. Add visual indicators
5. Implement project lifecycle operations

---

## Code Locations

- **File Explorer Panel**: `src/shypn/helpers/file_explorer_panel.py`
- **File Explorer API**: `src/shypn/file/explorer.py`
- **Project Models**: `src/shypn/data/project_models.py`

## Related Documentation

- **PROJECT_AWARE_FILE_OPERATIONS.md** - How NetObjPersistency integrates with projects
- **PROJECT_AWARE_QUICK_GUIDE.md** - Quick reference for project-aware features
