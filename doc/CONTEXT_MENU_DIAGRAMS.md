# Context Menu Structure

## Visual Layout

```
╔═══════════════════════════════════════╗
║     RIGHT-CLICK CONTEXT MENU          ║
╠═══════════════════════════════════════╣
║                                       ║
║  📄 Open                              ║
║                                       ║
╟───────────────────────────────────────╢
║                                       ║
║  📁 New Folder                        ║
║                                       ║
╟───────────────────────────────────────╢
║                                       ║
║  ✂️  Cut                              ║
║  📋 Copy                              ║
║  📌 Paste                             ║
║  📑 Duplicate                         ║
║                                       ║
╟───────────────────────────────────────╢
║                                       ║
║  ✏️  Rename                           ║
║  🗑️  Delete                           ║
║                                       ║
╟───────────────────────────────────────╢
║                                       ║
║  🔄 Refresh                           ║
║  ℹ️  Properties                       ║
║                                       ║
╚═══════════════════════════════════════╝
```

## Operation Flow Diagrams

### Copy & Paste Flow
```
┌─────────────┐
│  Right-Click│
│   on File   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Select "Copy"│
│     📋      │
└──────┬──────┘
       │
       ▼
┌─────────────┐    ┌─────────────────────┐
│ Clipboard:  │───▶│ clipboard_path = X  │
│ File stored │    │ clipboard_op = copy │
└──────┬──────┘    └─────────────────────┘
       │
       ▼
┌─────────────┐
│Right-Click  │
│Destination  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Select Paste │
│     📌      │
└──────┬──────┘
       │
       ▼
┌─────────────┐    ┌──────────────────┐
│Check if name│───▶│Name exists?      │
│  exists     │    │Yes: Add suffix   │
└──────┬──────┘    │No: Use original  │
       │           └──────────────────┘
       ▼
┌─────────────┐
│ Copy file   │
│  Original   │
│  preserved  │
└─────────────┘
```

### Cut & Paste Flow
```
┌─────────────┐
│  Right-Click│
│   on File   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Select "Cut"│
│     ✂️      │
└──────┬──────┘
       │
       ▼
┌─────────────┐    ┌─────────────────────┐
│ Clipboard:  │───▶│ clipboard_path = X  │
│ File marked │    │ clipboard_op = cut  │
└──────┬──────┘    └─────────────────────┘
       │
       ▼
┌─────────────┐
│Right-Click  │
│Destination  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Select Paste │
│     📌      │
└──────┬──────┘
       │
       ▼
┌─────────────┐    ┌──────────────────┐
│Check if name│───▶│Name exists?      │
│  exists     │    │Yes: Add suffix   │
└──────┬──────┘    │No: Use original  │
       │           └──────────────────┘
       ▼
┌─────────────┐    ┌─────────────────┐
│  Move file  │───▶│ Clear clipboard │
│  Original   │    │ (cut complete)  │
│  removed    │    └─────────────────┘
└─────────────┘
```

### Duplicate Flow
```
┌─────────────┐
│  Right-Click│
│   on File   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Duplicate  │
│     📑      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Generate    │
│ unique name │
│ file_copy.x │
└──────┬──────┘
       │
       ▼         ┌─────────────────────┐
┌─────────────┐  │ file_copy2.txt      │
│Name exists? │─▶│ file_copy3.txt      │
│Auto-number  │  │ ...                 │
└──────┬──────┘  └─────────────────────┘
       │
       ▼
┌─────────────┐
│  Copy file  │
│    to new   │
│    name     │
└─────────────┘
```

## State Management

```
FileExplorerPanel State:
├── Selected Item (for context menu)
│   ├── selected_item_path: str
│   ├── selected_item_name: str
│   └── selected_item_is_dir: bool
│
└── Clipboard (for cut/copy/paste)
    ├── clipboard_path: Optional[str]
    └── clipboard_operation: 'cut' | 'copy' | None
```

## Action Registration

```python
Action Group: "file"
├── file.open         → _on_open_action()
├── file.new_folder   → _on_new_folder_action()
├── file.cut          → _on_cut_action()
├── file.copy         → _on_copy_action()
├── file.paste        → _on_paste_action()
├── file.duplicate    → _on_duplicate_action()
├── file.rename       → _on_rename_action()
├── file.delete       → _on_delete_action()
├── file.refresh      → _on_refresh_action()
└── file.properties   → _on_properties_action()
```

## Menu Activation

```
User Input: Right-Click on TreeView
         │
         ▼
    GestureClick (button=3)
         │
         ▼
  _on_tree_view_right_click()
         │
         ├──▶ Get click coordinates (x, y)
         ├──▶ Find row at position
         ├──▶ Store selected item info
         │    ├── selected_item_path
         │    ├── selected_item_name
         │    └── selected_item_is_dir
         │
         ▼
    Show PopoverMenu at click position
         │
         ▼
    User selects menu item
         │
         ▼
    Action activated (e.g., file.copy)
         │
         ▼
    Handler called (_on_copy_action)
         │
         ▼
    Operation performed
```

## Naming Strategy

### Copy/Paste
```
Original: document.txt
Exists? → document_1.txt
Exists? → document_2.txt
Exists? → document_3.txt
...
```

### Duplicate
```
Original: report.pdf
Duplicate: report_copy.pdf
Exists? → report_copy2.pdf
Exists? → report_copy3.pdf
...
```

## Integration Points

### Current Integration
- File Explorer Panel (fully integrated)
- TreeView right-click gesture (working)
- File operations API (connected)

### Future Integration Points
- Document Management System
  - Open action should load file into editor
  - Track document-file associations
  - Enable auto-save functionality
  
- System Clipboard
  - Copy Path to system clipboard
  - Paste from system clipboard
  
- Drag & Drop
  - Visual drag and drop support
  - Multi-file operations
