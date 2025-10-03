# File Explorer Implementation Roadmap

**Project**: SHYpn Left Panel Refactoring  
**Target**: Full file browser functionality  
**Status**: Planning Complete

---

## Overview

Transform the current minimal left panel (`ui/panels/left_panel.ui`) into a comprehensive file explorer for managing Petri net project files.

---

## Implementation Phases

### ✅ Phase 0: Research (COMPLETED)
- [x] Analyze legacy implementation
- [x] Research GTK4 patterns
- [x] Document best practices
- [x] Create reference examples
- [x] Decision matrix completed

**Output**: `doc/FILE_EXPLORER_RESEARCH.md`

---

### 📋 Phase 1: Basic File Browser (2-3 days)

**Goal**: Display and navigate file system

#### Tasks:
1. **UI Structure**
   - [ ] Create `ui/panels/file_explorer_panel.ui`
   - [ ] Design toolbar with navigation buttons (back, forward, up, refresh)
   - [ ] Add GtkTreeView for file display
   - [ ] Create breadcrumb/path bar component
   - [ ] Add status bar for file count

2. **Python Class**
   - [ ] Create `ui/panels/file_explorer.py`
   - [ ] Implement `FileExplorerPanel` class
   - [ ] Add directory loading logic
   - [ ] Implement navigation (back/forward/up)
   - [ ] Add history management

3. **Features**
   - [ ] Display folders and files with icons
   - [ ] Show file size and modification date
   - [ ] Double-click to navigate folders
   - [ ] Sort by name, size, date
   - [ ] Parent directory navigation

4. **Integration**
   - [ ] Replace current `left_panel.ui`
   - [ ] Connect to main window
   - [ ] Test dock/undock functionality

**Acceptance Criteria**:
- ✅ Can browse file system
- ✅ Navigation buttons work
- ✅ File information displayed correctly
- ✅ Sorts by different columns

**Estimated Time**: 2-3 days

---

### 🔧 Phase 2: File Operations (2-3 days)

**Goal**: Create, rename, delete files/folders

#### Tasks:
1. **Context Menu**
   - [ ] Create right-click context menu
   - [ ] Add "Open" action
   - [ ] Add "New Folder" action
   - [ ] Add "New File" action
   - [ ] Add "Rename" action
   - [ ] Add "Delete" action
   - [ ] Add "Properties" action

2. **Dialogs**
   - [ ] Create new folder dialog
   - [ ] Create new file dialog (with templates)
   - [ ] Inline rename functionality
   - [ ] Delete confirmation dialog

3. **File Operations**
   - [ ] Implement create folder
   - [ ] Implement create file
   - [ ] Implement rename (inline editing)
   - [ ] Implement delete with confirmation
   - [ ] Add error handling

4. **File System Monitoring**
   - [ ] Watch current directory for changes
   - [ ] Auto-refresh on external changes
   - [ ] Update view when files added/removed

**Acceptance Criteria**:
- ✅ Can create new folders
- ✅ Can create new files
- ✅ Can rename files/folders
- ✅ Can delete with confirmation
- ✅ View updates automatically

**Estimated Time**: 2-3 days

---

### 🎨 Phase 3: Enhanced Features (3-4 days)

**Goal**: Advanced functionality and polish

#### Tasks:
1. **Recent Files**
   - [ ] Add "Recent" tab/section
   - [ ] Track opened files
   - [ ] Store in config file
   - [ ] Display with icons and paths
   - [ ] Double-click to open

2. **Search & Filter**
   - [ ] Add search entry in toolbar
   - [ ] Filter by filename
   - [ ] Filter by file type
   - [ ] Highlight matches
   - [ ] Clear search functionality

3. **File Type Support**
   - [ ] Create file type registry
   - [ ] Petri net files (.pn, .json)
   - [ ] Python files (.py)
   - [ ] Documentation (.md, .txt)
   - [ ] Custom icons per type
   - [ ] Open with default handler

4. **User Experience**
   - [ ] Bookmarks/favorites
   - [ ] Multiple selection (Ctrl+click)
   - [ ] Drag and drop support
   - [ ] Keyboard shortcuts (F2=rename, Del=delete)
   - [ ] Tooltips with full paths
   - [ ] Loading indicators

5. **Polish**
   - [ ] Custom CSS styling
   - [ ] Smooth animations
   - [ ] Consistent icons
   - [ ] Accessibility labels
   - [ ] Error messages

**Acceptance Criteria**:
- ✅ Recent files easily accessible
- ✅ Search finds files quickly
- ✅ Petri net files have custom icons
- ✅ Keyboard shortcuts work
- ✅ Professional appearance

**Estimated Time**: 3-4 days

---

### 🔌 Phase 4: Application Integration (1-2 days)

**Goal**: Connect with main application features

#### Tasks:
1. **Project Management**
   - [ ] Create "New Project" action
   - [ ] "Open Project" integration
   - [ ] "Save Project" updates view
   - [ ] Project folder recognition

2. **Canvas Integration**
   - [ ] Double-click .pn file opens in canvas
   - [ ] Show preview in properties
   - [ ] Drag file to canvas
   - [ ] Current file indicator

3. **Settings**
   - [ ] Remember last opened directory
   - [ ] Show hidden files toggle
   - [ ] File type associations
   - [ ] Default new file templates

4. **Testing**
   - [ ] Unit tests for file operations
   - [ ] Integration tests with main app
   - [ ] Edge case testing
   - [ ] Performance testing (large dirs)

**Acceptance Criteria**:
- ✅ Opens Petri net files in application
- ✅ New project workflow smooth
- ✅ Settings persist across sessions
- ✅ All tests passing

**Estimated Time**: 1-2 days

---

## Technical Specifications

### File Structure

```
ui/panels/
├── file_explorer_panel.ui          # UI definition (GTK4)
├── file_explorer.py                # Main class
├── file_operations.py              # Create/delete/rename
├── file_system_monitor.py          # Directory watching
├── recent_files_manager.py         # Recent files tracking
└── file_type_registry.py           # File type handlers
```

### Class Architecture

```python
# ui/panels/file_explorer.py
class FileExplorerPanel:
    - __init__(builder, base_path)
    - navigate_to(path)
    - go_back()
    - go_forward()
    - go_up()
    - refresh()
    - create_folder(name)
    - create_file(name, template)
    - rename_item(old_name, new_name)
    - delete_item(path)
    - search(query)
    - open_file(path)

# ui/panels/file_operations.py
class FileOperations:
    - create_directory(path, name)
    - create_file(path, name, content)
    - rename(old_path, new_path)
    - delete(path, confirm=True)
    - copy(src, dest)
    - move(src, dest)

# ui/panels/file_system_monitor.py
class FileSystemMonitor:
    - watch_directory(path, callback)
    - stop_watching()
    - _on_file_created(path)
    - _on_file_deleted(path)
    - _on_file_modified(path)

# ui/panels/recent_files_manager.py
class RecentFilesManager:
    - add_recent(path)
    - get_recent(count=10)
    - clear_recent()
    - save_to_disk()
    - load_from_disk()

# ui/panels/file_type_registry.py
class FileTypeRegistry:
    - register_type(extension, icon, handler)
    - get_icon(filename)
    - get_handler(filename)
    - open_with(path)
```

---

## Configuration

### Settings File (`~/.config/shypn/file_explorer.json`)

```json
{
  "last_directory": "/home/user/projects",
  "show_hidden_files": false,
  "sort_column": "name",
  "sort_order": "ascending",
  "recent_files": [
    "/home/user/projects/model1.pn",
    "/home/user/projects/model2.pn"
  ],
  "bookmarks": [
    "/home/user/projects",
    "/home/user/documents"
  ],
  "file_associations": {
    ".pn": "shypn.open_petri_net",
    ".json": "shypn.open_json_model"
  }
}
```

---

## UI/UX Guidelines

### Visual Design
- **Icons**: Use symbolic icons from GTK icon theme
- **Colors**: Respect system theme
- **Spacing**: 6px standard padding
- **Fonts**: System default, monospace for paths

### Interaction Patterns
- **Single-click**: Select item
- **Double-click**: Open/navigate
- **Right-click**: Context menu
- **Drag**: Move/copy files (future)
- **F2**: Rename selected
- **Delete**: Delete selected (with confirmation)

### Error Handling
- **Permission denied**: Show clear message
- **File exists**: Ask to overwrite/rename
- **Delete folder**: Confirm if contains files
- **Network paths**: Show loading indicator

---

## Testing Strategy

### Unit Tests
```python
# tests/test_file_explorer.py
- test_navigate_to_directory()
- test_go_back_forward()
- test_create_folder()
- test_rename_file()
- test_delete_file()
- test_search_files()

# tests/test_file_operations.py
- test_create_directory_success()
- test_create_directory_permission_denied()
- test_rename_file_exists()
- test_delete_non_empty_folder()
```

### Integration Tests
```python
# tests/test_file_explorer_integration.py
- test_open_file_in_application()
- test_new_project_workflow()
- test_recent_files_persistence()
- test_drag_drop_to_canvas()
```

### Manual Testing Checklist
- [ ] Browse through nested folders
- [ ] Create/rename/delete files and folders
- [ ] Search for files
- [ ] Open Petri net files
- [ ] Test with large directories (1000+ files)
- [ ] Test with permission-restricted folders
- [ ] Test dock/undock panel
- [ ] Test keyboard shortcuts
- [ ] Test context menus

---

## Dependencies

### Python Modules
```python
# Standard library
import os
import json
from datetime import datetime
from pathlib import Path

# GTK4
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Gio, GLib

# Optional (for file watching)
# pip install watchdog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
```

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| GTK4 API changes | Medium | Use stable APIs, avoid experimental features |
| Performance with large dirs | High | Lazy loading, pagination, virtual scrolling |
| File permissions | Medium | Proper error handling, user feedback |
| Cross-platform compatibility | Low | Use platform-agnostic APIs, test on multiple OS |
| File system monitoring overhead | Medium | Use native OS notifications, debounce updates |

---

## Success Metrics

### Phase 1
- ✅ Can browse any directory
- ✅ Navigation smooth and responsive
- ✅ File info accurate

### Phase 2
- ✅ All file operations work
- ✅ No data loss
- ✅ Proper error messages

### Phase 3
- ✅ Search is fast (<500ms)
- ✅ Recent files load instantly
- ✅ UI feels polished

### Phase 4
- ✅ Integrates seamlessly with app
- ✅ User workflow improved
- ✅ Zero critical bugs

---

## Timeline

```
Week 1:
├── Days 1-3: Phase 1 (Basic File Browser)
└── Days 4-5: Phase 2 Start (File Operations)

Week 2:
├── Days 1-2: Phase 2 Complete
├── Days 3-5: Phase 3 (Enhanced Features)

Week 3:
├── Days 1-2: Phase 4 (Integration)
└── Days 3-5: Testing & Polish
```

**Total Estimated Time**: 2-3 weeks (part-time)

---

## Next Session Action Items

When ready to start implementation:

1. **Review** `doc/FILE_EXPLORER_RESEARCH.md`
2. **Choose** implementation pattern (recommend: GtkTreeView)
3. **Create** `ui/panels/file_explorer_panel.ui` base structure
4. **Implement** `FileExplorerPanel` class skeleton
5. **Test** basic directory loading
6. **Iterate** based on feedback

---

## References

- 📘 Research Document: `doc/FILE_EXPLORER_RESEARCH.md`
- 📘 Legacy Implementation: `legacy/shypnpy/interface/shypn.ui` (lines 260-310)
- 📘 Current Panel: `ui/panels/left_panel.ui`
- 📘 GTK4 Docs: https://docs.gtk.org/gtk4/

---

**Status**: Ready to Begin Implementation 🚀  
**Next Phase**: Phase 1 - Basic File Browser  
**Estimated Start**: When you're ready today/tomorrow
