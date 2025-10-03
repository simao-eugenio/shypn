# Complete Left Panel File Explorer Extraction

## Overview
This document details the complete extraction and conversion of the File Explorer panel from GTK4 to GTK3, including all toolbars, buttons, navigation controls, and window management features.

## Complete Widget Structure

### 1. Panel Header
- **panel_title** (GtkLabel): "File Explorer" heading
- **float_button** (GtkToggleButton): Toggle between floating window and docked mode
  - Icon: ⇱
  - Tooltip: "Float/Dock panel toggle"
  - Controls: Attach/detach panel from main window

### 2. File Operations Toolbar
All buttons are flat-styled with emoji icons for visual clarity:

- **file_new_button**: 📄 New File
  - Creates a new Petri net model file
  - Signal: `_on_file_new_clicked()`
  
- **file_open_button**: 📂 Open File
  - Opens selected file from tree view or shows file chooser
  - Signal: `_on_file_open_clicked()`
  
- **file_save_button**: 💾 Save File
  - Saves current document
  - Signal: `_on_file_save_clicked()`
  
- **file_save_as_button**: 💾+ Save As...
  - Shows save as dialog
  - Signal: `_on_file_save_as_clicked()`
  
- **file_new_folder_button**: 📁+ New Folder
  - Creates new folder in current directory
  - Signal: `_on_file_new_folder_clicked()`
  - Shows dialog to enter folder name

### 3. Navigation Toolbar
Provides directory navigation with history support:

- **nav_back_button**: ◀ Back
  - Navigate to previous directory in history
  - Signal: `_on_back_clicked()`
  - Disabled when no history
  
- **nav_forward_button**: ▶ Forward
  - Navigate to next directory in history
  - Signal: `_on_forward_clicked()`
  - Disabled when no forward history
  
- **nav_up_button**: ▲ Up
  - Navigate to parent directory
  - Signal: `_on_up_clicked()`
  
- **nav_home_button**: 🏠 Home
  - Navigate to models root directory
  - Signal: `_on_home_clicked()`
  
- **nav_refresh_button**: 🔄 Refresh
  - Toggles between hierarchical tree view and flat list view
  - Also refreshes current directory contents
  - Signal: `_on_refresh_clicked()`

### 4. Current File Display
- **Label**: "Current:" (dim-label style)
- **current_file_entry** (GtkEntry): 
  - Read-only entry showing currently opened file
  - Shows relative path from models directory
  - Default: "—" (when no file is open)
  - Flat style with frame

### 5. File Browser TreeView
- **file_browser_scroll** (GtkScrolledWindow):
  - Shadow type: in
  - Automatic scrollbars
  
- **file_browser_tree** (GtkTreeView):
  - Hierarchical tree structure
  - Model: GtkTreeStore (icon, name, path, is_dir)
  - Columns: Icon + Name (combined)
  - Features:
    - Tree lines enabled
    - Expanders visible
    - Single-click to select
    - Double-click to open/navigate
    - Right-click for context menu

### 6. Context Menu (GTK3 Gtk.Menu)
Proper GTK3 menu with automatic dismiss behavior:

**Menu Items:**
- Open
- New Folder
- --- (separator)
- Cut
- Copy
- Paste
- Duplicate
- --- (separator)
- Rename
- Delete
- --- (separator)
- Refresh
- Properties

**Key Features:**
- ✅ **Automatically dismisses on Escape key** (PRIMARY GOAL!)
- ✅ **Automatically dismisses on click outside** (PRIMARY GOAL!)
- Shows at pointer position using `menu.popup()`
- No manual dismiss logic needed

### 7. Status Bar
- **file_browser_status** (GtkLabel):
  - Shows directory statistics: "X folders, Y files"
  - Shows error messages when operations fail
  - Dim-label style
  - Left-aligned

## Event Handling (GTK3)

### Button Press Events
```python
tree_view.connect('button-press-event', handler)
```
- Right-click (button 3): Shows context menu
- Detects click position to select item
- Supports clicking on empty space (uses current directory)

### Row Activation
```python
tree_view.connect('row-activated', handler)
```
- Double-click on directories: Navigate into folder
- Double-click on files: Set as current file

### Navigation History
- Maintains back/forward history stack
- Updates button sensitivity based on history state
- Can navigate up to parent directory
- Can jump to home (models root)

## File Operations

### Supported Operations:
1. **Open**: Opens file in editor (sets as current)
2. **New Folder**: Creates folder with dialog
3. **Cut/Copy/Paste**: Clipboard operations with visual feedback
4. **Duplicate**: Creates copy with "_copy" suffix
5. **Rename**: Shows dialog to rename file/folder
6. **Delete**: Shows confirmation dialog, deletes file/folder
7. **Refresh**: Reloads directory or toggles view mode
8. **Properties**: Shows file/folder properties dialog

### View Modes:
1. **Hierarchical Tree**: Shows all subdirectories expanded
2. **Flat List**: Shows only current directory contents

## Dialog Integration

All dialogs properly use GTK3 API:
- `pack_start()` instead of `append()`
- `show()` / `show_all()` instead of `present()`
- `get_content_area()` for dialog content
- Proper response handlers with lambda callbacks

## Window Management

### Floating Mode:
- Panel becomes separate window
- Transient for main window
- Can be moved/resized independently
- Float button shows active state

### Attached Mode:
- Panel content embedded in main window container
- Window destroyed to prevent phantom windows (WSL/X11)
- Float button shows inactive state
- Container visibility controlled

### State Transitions:
- Float button toggles between states
- Callbacks notify main window of state changes
- Panel content reparented between window and container

## Testing Checklist

✅ All widgets load from UI file
✅ No missing widget warnings
✅ File operations toolbar visible
✅ Navigation toolbar visible
✅ Current file display shows placeholder
✅ TreeView displays with proper columns
✅ Context menu appears on right-click
✅ Context menu dismisses with Escape (**PRIMARY GOAL**)
✅ Context menu dismisses on click-outside (**PRIMARY GOAL**)
✅ Status bar shows directory statistics
✅ Float button controls attach/detach
✅ All buttons have proper tooltips

## Success Metrics

The conversion successfully addresses the original problem:

**Original Issue**: GTK4 context menus/popovers don't dismiss properly on WSL2+WSLg+Wayland when pressing Escape or clicking outside.

**Solution**: GTK3's native `Gtk.Menu` automatically handles:
- ✨ Escape key dismiss
- ✨ Click-outside dismiss
- ✨ Focus management
- ✨ Proper positioning

**Result**: Full-featured File Explorer panel with all expected UI controls, proper event handling, and reliable context menu behavior in GTK3.

## Architecture

```
left_panel_loader.py
  └─ Loads left_panel.ui
  └─ Creates FileExplorerPanel controller
       ├─ Gets widget references from builder
       ├─ Configures TreeView with TreeStore model
       ├─ Sets up GTK3 context menu
       ├─ Connects all signals (GTK3 events)
       └─ Integrates with FileExplorer API (business logic)
```

The controller pattern ensures clean separation:
- **Model**: FileExplorer API (business logic)
- **View**: left_panel.ui (widget definitions)
- **Controller**: FileExplorerPanel (connects model to view)
