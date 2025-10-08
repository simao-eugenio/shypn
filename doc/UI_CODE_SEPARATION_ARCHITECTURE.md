# UI and Code Separation Architecture

## Principle

**Physical Separation**: UI definition files (`.ui`, `.glade`) are kept completely separate from code (`.py`) in the directory structure.

```
ui/                    ← Pure UI definitions (GTK XML, resources)
src/shypn/             ← All code (business logic, controllers, helpers)
```

## Directory Structure

### UI Layer (`ui/`)

Pure UI definitions only - no Python code:

```
ui/
├── canvas/
│   └── model_canvas.ui              # Canvas UI definition
├── dialogs/
│   ├── arc_prop_dialog.ui           # Arc properties dialog
│   ├── place_prop_dialog.ui         # Place properties dialog
│   └── transition_prop_dialog.ui    # Transition properties dialog
├── main/
│   └── main_window.ui               # Main window layout
├── palettes/
│   ├── combined_tools_palette.ui
│   ├── edit_palette.ui
│   ├── edit_tools_palette.ui
│   ├── zoom.ui
│   └── mode/
│       └── mode_palette.ui
├── panels/
│   ├── left_panel.ui                # File explorer panel UI
│   ├── right_panel.ui               # Analyses panel UI
│   └── pathway_panel.ui             # Pathway operations panel UI (NEW)
└── simulate/
    ├── simulate_palette.ui
    └── simulate_tools_palette.ui
```

### Code Layer (`src/shypn/`)

All Python code - controllers, loaders, business logic:

```
src/shypn/
├── api/                    # Business logic (OOP)
├── importer/              # Import modules (KEGG, etc.)
│   └── kegg/              # KEGG pathway importer
│       ├── api_client.py
│       ├── kgml_parser.py
│       ├── models.py
│       └── pathway_converter.py
├── helpers/               # Controllers and loaders
│   ├── left_panel_loader.py          # Loads ui/panels/left_panel.ui
│   ├── right_panel_loader.py         # Loads ui/panels/right_panel.ui
│   ├── pathway_panel_loader.py       # Loads ui/panels/pathway_panel.ui (NEW)
│   ├── file_explorer_panel.py        # Controller for file explorer
│   ├── kegg_import_panel.py          # Controller for KEGG import (NEW)
│   ├── model_canvas_loader.py        # Loads ui/canvas/model_canvas.ui
│   ├── place_prop_dialog_loader.py   # Loads ui/dialogs/place_prop_dialog.ui
│   ├── arc_prop_dialog_loader.py     # Loads ui/dialogs/arc_prop_dialog.ui
│   └── ...
└── ui/
    └── README.md          # Documentation only
```

## Pattern: Loader + Controller

### Architecture

```
UI Definition (XML)  ←─loads─  Loader (Python)  ←─uses─  Controller (Python)
  ui/*.ui                      helpers/*_loader.py       helpers/*_panel.py
```

### Example: Pathway Panel

**1. UI Definition** (`ui/panels/pathway_panel.ui`):
```xml
<object class="GtkWindow" id="pathway_panel_window">
  <object class="GtkNotebook" id="pathway_notebook">
    <object class="GtkEntry" id="pathway_id_entry"/>
    <object class="GtkButton" id="fetch_button"/>
  </object>
</object>
```

**2. Loader** (`src/shypn/helpers/pathway_panel_loader.py`):
- Loads UI file
- Manages window lifecycle (attach/detach)
- Creates controllers
- No business logic

```python
class PathwayPanelLoader:
    def load(self):
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        self.window = self.builder.get_object('pathway_panel_window')
        self._setup_import_tab()  # Creates controller
```

**3. Controller** (`src/shypn/helpers/kegg_import_panel.py`):
- Gets widget references from builder
- Connects signals to handlers
- Implements business logic
- Talks to backend APIs

```python
class KEGGImportPanel:
    def __init__(self, builder, model_canvas):
        self.builder = builder
        self._get_widgets()           # Get references
        self._connect_signals()       # Wire up handlers
    
    def _on_fetch_clicked(self, button):
        # Business logic here
```

## Benefits

### ✅ Clean Separation
- UI designers can work on `.ui` files without touching code
- Developers can work on controllers without touching UI
- Easy to swap UI frameworks (GTK3 → GTK4, Qt, etc.)

### ✅ Maintainability
- Find all UI in `ui/`
- Find all code in `src/shypn/`
- No mixed concerns

### ✅ Version Control
- UI changes don't pollute code diffs
- Code changes don't pollute UI diffs
- Binary resources isolated

### ✅ Testing
- Controllers can be unit tested without UI
- UI can be visually tested without running full app
- Mock builders for testing

## MVC Pattern

```
┌─────────────────┐
│  Model (API)    │  ← Business logic (src/shypn/api/, src/shypn/importer/)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Controller     │  ← Helpers/Loaders (src/shypn/helpers/)
│  (Helper)       │     - Gets widget references
└────────┬────────┘     - Connects signals
         │              - Updates view
         ↓              - Calls model
┌─────────────────┐
│  View (UI)      │  ← GTK XML files (ui/*.ui)
└─────────────────┘     - Widget definitions
                        - Layout
                        - Static properties
```

## KEGG Import Example

### File Organization

```
# UI Definition (pure GTK XML)
ui/panels/pathway_panel.ui                    ← Notebook with Import tab

# Loaders (window management)
src/shypn/helpers/pathway_panel_loader.py     ← Loads window, manages attach/detach

# Controllers (business logic)
src/shypn/helpers/kegg_import_panel.py        ← Handles import workflow

# Backend (data processing)
src/shypn/importer/kegg/api_client.py         ← Fetches from KEGG
src/shypn/importer/kegg/kgml_parser.py        ← Parses XML
src/shypn/importer/kegg/pathway_converter.py  ← Converts to Petri net
```

### Data Flow

```
User clicks "Fetch"
    ↓
kegg_import_panel.py (_on_fetch_clicked)
    ↓
api_client.py (fetch_kgml)
    ↓
kgml_parser.py (parse)
    ↓
kegg_import_panel.py (_update_preview)
    ↓
pathway_panel.ui (preview_text updated)
```

## Guidelines

### DO ✅
- Keep all `.ui` files in `ui/`
- Keep all `.py` files in `src/shypn/`
- Use loaders to bridge UI and code
- Controllers get widget references from builder
- Document UI structure in `ui/*/README.md`

### DON'T ❌
- Don't put Python files in `ui/`
- Don't create widgets programmatically if they can be in `.ui`
- Don't put UI logic in business logic modules
- Don't mix UI and backend concerns

## Migration Checklist

When adding new UI:

1. ✅ Create `.ui` file in `ui/` subdirectory
2. ✅ Create loader in `src/shypn/helpers/`
3. ✅ Create controller in `src/shypn/helpers/` (if needed)
4. ✅ Loader loads UI, creates controller
5. ✅ Controller gets widgets from builder
6. ✅ Controller connects to backend APIs
7. ✅ Update README in respective `ui/` subdirectory

## Current Status

✅ **Cleaned up**:
- Moved `file_explorer_panel.py` → `src/shypn/helpers/`
- Moved `kegg_import_panel.py` → `src/shypn/helpers/`
- Removed `src/shypn/ui/panels/` (no code in ui tree)
- Removed `ui/kegg/` (unused)

✅ **Proper structure**:
- All UI: `ui/`
- All code: `src/shypn/`
- Clean separation maintained
