# Feature Request: SBML XML Viewer

## Overview
Implement ability to open and view raw SBML XML files within SHYpn for inspection and debugging purposes.

## Use Case
While most users work with the visual Petri net representation, some advanced users (researchers, developers, debuggers) may need to:
- Inspect the original SBML XML structure
- Debug import issues by examining raw data
- Verify specific SBML annotations or metadata
- Compare raw SBML with the converted model
- Educational purposes - understanding SBML format

**Frequency:** Very rare, but important for power users and debugging

## Current State
- ✅ SBML files are saved to `project/pathways/*.xml`
- ✅ Petri net models saved to `project/models/*.shy`
- ❌ No way to open/view the raw XML files within SHYpn
- Workaround: Users must use external text editor

## Proposed Implementation

### Option 1: Integrated XML Viewer (Recommended)
Add a viewer panel specifically for XML/text files:

**Location:** Right-click context menu in File Explorer
```
Right-click on .xml file in file tree
  ↓
"Open" → Opens in Petri net view (if already converted)
"View Raw XML" → Opens in XML viewer panel
"Open with External Editor" → Opens in system text editor
```

**UI Components:**
- New tab type in canvas notebook for XML viewing
- Syntax highlighting for XML
- Read-only view (or editable with warning about breaking imports)
- Search/Find functionality
- Line numbers
- Collapsible XML tree structure (optional)

**Implementation:**
- Use GtkSourceView for syntax highlighting
- Add XML mime type detection in file_explorer_panel.py
- Create XMLViewerPanel class in `src/shypn/helpers/xml_viewer_panel.py`
- Register .xml files to open in viewer when double-clicked

### Option 2: External Editor Integration
Simpler approach - just open in system default text editor:

**Implementation:**
- Add "Open in Text Editor" context menu item
- Use `xdg-open` or `subprocess` to launch external editor
- Faster to implement, less maintenance

### Option 3: Hybrid Approach
- Double-click .xml → Opens converted Petri net (if exists)
- Right-click → "View Raw XML" → Opens in integrated viewer
- Right-click → "Edit Externally" → Opens in system editor

## Technical Requirements

### File Type Detection
```python
# In file_explorer_panel.py
def _on_row_activated(self, tree_view, path, column):
    filepath = self.get_selected_filepath()
    
    if filepath.endswith('.xml') or filepath.endswith('.sbml'):
        # Check if converted model exists
        model_path = self._get_corresponding_model_path(filepath)
        if model_path and os.path.exists(model_path):
            # Open converted Petri net
            self._open_petri_net(model_path)
        else:
            # No conversion yet - open XML viewer
            self._open_xml_viewer(filepath)
    elif filepath.endswith('.shy'):
        self._open_petri_net(filepath)
```

### XML Viewer Component
```python
# src/shypn/helpers/xml_viewer_panel.py

class XMLViewerPanel:
    """Viewer for raw XML/SBML files with syntax highlighting."""
    
    def __init__(self, filepath):
        self.filepath = filepath
        
        # Use GtkSourceView for syntax highlighting
        self.source_view = GtkSource.View()
        self.buffer = GtkSource.Buffer()
        
        # Set XML language for highlighting
        language_manager = GtkSource.LanguageManager.get_default()
        xml_language = language_manager.get_language('xml')
        self.buffer.set_language(xml_language)
        
        # Load file content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        self.buffer.set_text(content)
        
        # Configure view
        self.source_view.set_buffer(self.buffer)
        self.source_view.set_show_line_numbers(True)
        self.source_view.set_editable(False)  # Read-only by default
        self.source_view.set_monospace(True)
```

### Context Menu Integration
```python
# In file_explorer_panel.py
menu_items = [
    ('Open', self._on_context_open_clicked),
    ('View Raw XML', self._on_view_xml_clicked),  # NEW
    ('Open in External Editor', self._on_open_external_clicked),  # NEW
    ('---', None),
    # ... rest of menu
]

def _on_view_xml_clicked(self, menu_item):
    """Open XML file in integrated viewer."""
    filepath = self.get_selected_filepath()
    if filepath.endswith('.xml') or filepath.endswith('.sbml'):
        # Create XML viewer tab
        self.canvas_loader.add_xml_viewer(filepath)

def _on_open_external_clicked(self, menu_item):
    """Open file in external editor."""
    filepath = self.get_selected_filepath()
    subprocess.Popen(['xdg-open', filepath])
```

## Dependencies

### Option 1 (Integrated Viewer)
- **GtkSourceView**: For syntax highlighting
  - Package: `python3-gi-gtksourceview` or `gir1.2-gtksource-3.0`
  - Already available in most GTK3 environments
  - Provides XML, JSON, Python, etc. syntax highlighting

### Option 2 (External Editor)
- No dependencies - uses system default editor

## Benefits

### For Users
- **Debugging:** Inspect raw SBML when imports fail or produce unexpected results
- **Learning:** Understand SBML structure by comparing raw XML with visual model
- **Verification:** Confirm specific SBML annotations or metadata are preserved
- **Research:** Extract specific XML elements for analysis

### For Developers
- **Testing:** Easier to debug SBML parser issues
- **Validation:** Verify import correctness against original XML
- **Documentation:** Show SBML examples in tutorials

## Implementation Priority

**Priority:** Low to Medium
- Not critical for normal workflow
- Important for debugging and advanced users
- Relatively simple to implement (Option 2 or 3)

**Estimated Effort:**
- Option 1 (Integrated Viewer): 4-6 hours
- Option 2 (External Editor): 1-2 hours
- Option 3 (Hybrid): 2-3 hours

## Related Files

**To Modify:**
- `src/shypn/helpers/file_explorer_panel.py` - Add context menu items
- `src/shypn/helpers/model_canvas_loader.py` - Support XML viewer tabs (Option 1)

**To Create:**
- `src/shypn/helpers/xml_viewer_panel.py` - XML viewer component (Option 1)

## Testing Checklist

When implementing:
- [ ] Double-click .xml file opens appropriate view
- [ ] Context menu shows "View Raw XML" for .xml files
- [ ] XML viewer displays content with syntax highlighting
- [ ] Large XML files (>1MB) load without freezing UI
- [ ] Read-only mode prevents accidental edits
- [ ] Search/find works in XML viewer
- [ ] External editor opens correctly on all platforms
- [ ] Works with both .xml and .sbml extensions
- [ ] Handles UTF-8 encoding correctly
- [ ] Handles malformed XML gracefully

## Future Enhancements

Once basic viewer is implemented:
- **Edit Mode:** Allow editing with re-import confirmation
- **XML Validation:** Show validation errors inline
- **Diff View:** Compare raw XML before/after processing
- **Export:** Save modified XML back to project
- **Pretty Print:** Auto-format XML for readability
- **XPath Query:** Advanced users can query XML structure
- **Side-by-Side:** Show XML and Petri net simultaneously

## Notes

- This is a **"power user"** feature - most users will never need it
- Keep implementation simple - external editor integration (Option 2) might be sufficient
- Consider adding keyboard shortcut: `Ctrl+Shift+X` to view XML of current model
- Document this feature in user manual for researchers/developers

## Status

**Current:** Not implemented
**Requested:** October 25, 2025
**Target Version:** Future release (after core features stable)
**Assigned:** To be determined
