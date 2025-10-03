````markdown
# SHYpn - Stochastic Hybrid Petri Net Editor

A GTK-based visual editor for Stochastic Hybrid Petri Nets with advanced modeling capabilities.

## Project Status (October 2, 2025)

**Current State**: Active development and refactoring
- ✅ GTK3 stable implementation
- ✅ Multi-document canvas system with tabbed interface
- ✅ Dockable/undockable left and right panels
- ✅ File explorer with hierarchical tree view
- ✅ Zoom palette with predefined zoom levels
- ✅ Canvas context menus (right-click)
- ✅ Grid system with multiple styles (line/dot/cross)
- ✅ Clean production codebase (debug code removed)
- 🔄 Preparing for transition dialog integration from legacy

**Recent Updates**:
- Repository reorganization (tests consolidated, transition files removed)
- Complete debug code cleanup (8 files cleaned)
- Empty panel visibility fixes
- Grid spacing corrections

## GTK 3 Notice

This project currently uses GTK 3.2+. While there was consideration for GTK 4 migration, the project is stabilizing on GTK 3 for production use. The codebase follows modern Python and OOP practices regardless of the GTK version.
 
## Architectural Guideline: Object-Oriented Design

This project is designed with an object-oriented programming (OOP) approach. Core logic, APIs, and UI components are implemented as classes, utilizing principles such as encapsulation, inheritance, and polymorphism. Contributors are encouraged to structure new modules and features using OOP best practices to ensure maintainability and extensibility.
## Repository Structure Overview

```
shypn/
├── data/           # Data model files (schemas, ORM models, sample data)
├── doc/            # Main documentation in Markdown format
├── legacy/         # Legacy code from previous versions (reference only)
├── models/         # User Petri net model files (.shy format)
├── scripts/        # Utility scripts, demos (non-test)
├── src/
│   └── shypn/
│       ├── api/    # Business logic APIs (file operations, etc.)
│       ├── data/   # Data models and canvas managers
│       ├── dev/    # Experimental or in-development code
│       ├── helpers/# UI loaders and helper functions
│       ├── ui/     # UI component classes
│       └── utils/  # Specific code routines and utilities
├── tests/          # Test suite (consolidated from scripts/)
├── ui/
│   ├── canvas/     # Document canvas interfaces (.ui files)
│   ├── dialogs/    # Modal dialogs (.ui files)
│   ├── main/       # Main window interface (.ui files)
│   ├── palettes/   # Control palettes like zoom (.ui files)
│   └── panels/     # Dockable panels (left/right) (.ui files)
└── venv/           # Python virtual environment (optional)
```

**Key Directories**:
- `src/shypn/`: Main application source code (Python)
- `ui/`: GTK UI definition files (Glade XML format)
- `tests/`: All test files (moved from scripts/)
- `models/`: User workspace for Petri net models
- `legacy/`: Historical code for reference

## Installation

### Prerequisites
- Python 3.8+
- GTK 3.22+
- PyGObject (python3-gi)
- Cairo graphics library

### System Dependencies (Ubuntu/Debian)
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

### Python Environment
```bash
# Option 1: Virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Option 2: System site-packages (for WSL/WSLg)
python3 -m venv venv/shypnenv --system-site-packages
source venv/shypnenv/bin/activate
```

## Usage

### Running the Application
```bash
# From repository root
python3 src/shypn.py

# Or with virtual environment activated
source venv/bin/activate
python3 src/shypn.py
```

### Basic Operations
- **New Document**: Click the "+" button in the left panel toolbar
- **Toggle Panels**: Use the toggle buttons in the main window header
- **Zoom**: Click the zoom button in the canvas to access zoom controls
- **Grid Styles**: Right-click on canvas → Grid Style (line/dot/cross)
- **Pan Canvas**: Right-click and drag on the canvas

### File Organization
- Models are saved in the `models/` directory
- The file explorer panel shows this directory by default
- Supports hierarchical folder navigation within models directory

## Running the GTK4 UI under WSLg / Windows

If you run the project from WSL (WSLg) you may see inconsistencies when using a Conda Python environment because Conda-provided GTK/GLib stacks can be isolated from the system Wayland backend. A reliable workaround is to create a small virtualenv that uses the system site-packages (so it picks up the system GTK/GI installation that works with WSLg).

Steps (one-time):

1. Create the venv (uses system Python and system GTK):

```bash
python3 -m venv venv/shypnenv --system-site-packages
```

2. Activate and run the UI (use system python inside the venv):

```bash
. venv/shypnenv/bin/activate
/usr/bin/python3 src/shypn.py
```

Notes:
- This approach keeps your Conda environment untouched while allowing GTK4 apps to use the system Wayland backend (WSLg). It is the recommended approach when working on Windows+WSL development if the Conda GTK stack misbehaves.
- If you prefer to work with Conda, you can attempt to fix the Conda environment (rebuild PyGObject + GTK packages) but that is more involved and may be fragile.

## Contributing

Please read [CONTRIBUTING.md](doc/CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Documentation

All project documentation is located in the [`doc/`](doc/) directory:

- **[CONTRIBUTING.md](doc/CONTRIBUTING.md)** - Contribution guidelines and code standards
- **[CHANGELOG.md](doc/CHANGELOG.md)** - Version history and changes
- **[REFINEMENTS_LOG.md](doc/REFINEMENTS_LOG.md)** - Detailed technical refinements and fixes
- **[CANVAS_CONTROLS.md](doc/CANVAS_CONTROLS.md)** - Canvas control and interaction documentation
- **[ZOOM_PALETTE.md](doc/ZOOM_PALETTE.md)** - Zoom palette implementation details
- **[FIX_EMPTY_PANEL.md](doc/FIX_EMPTY_PANEL.md)** - Panel visibility fixes documentation
- **[VSCODE_SETUP_VALIDATION.md](doc/VSCODE_SETUP_VALIDATION.md)** - VS Code setup and validation
- **[DOCUMENTATION_UPDATE_SUMMARY.md](doc/DOCUMENTATION_UPDATE_SUMMARY.md)** - Recent documentation updates

See the [`doc/`](doc/) directory for additional technical documentation and implementation notes.

## License

Specify the license here.
