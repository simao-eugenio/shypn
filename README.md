````markdown
# SHYpn - Stochastic Hybrid Petri Net Editor

A GTK-based visual editor for Stochastic Hybrid Petri Nets with advanced modeling capabilities.

## Project Status (October 11, 2025)

**Current State**: Active development - Feature-rich Petri net editor
- ✅ GTK3 stable implementation with Wayland support
- ✅ Multi-document canvas system with tabbed interface
- ✅ Dockable/undockable left and right panels
- ✅ File explorer with hierarchical tree view and file operations
- ✅ SwissKnife unified palette (Edit/Simulate/Layout tools)
- ✅ Property dialogs for all Petri net objects
- ✅ Arc transformations (straight/curved, normal/inhibitor, parallel arcs)
- ✅ Simulation system with stochastic transitions
- ✅ Graph layout algorithms (auto, hierarchical, force-directed)
- ✅ KEGG pathway import with enhancement pipeline
- ✅ Project management system
- ✅ Canvas context menus with rich functionality
- ✅ Clean production codebase (all debug output removed)

**Recent Updates** (October 2025):
- Complete debug and print statement cleanup (12 files)
- Repository reorganization (64 files moved to proper directories)
- Arc boundary precision fixes (proper border width accounting)
- Inhibitor arc hollow circle positioning on curved arcs
- Context menu enhancements (arc transformation options)
- Source/sink place types implementation
- Workspace state persistence
- Unsaved changes protection

## GTK 3 Notice

This project currently uses GTK 3.2+. While there was consideration for GTK 4 migration, the project is stabilizing on GTK 3 for production use. The codebase follows modern Python and OOP practices regardless of the GTK version.
 
## Architectural Guideline: Object-Oriented Design

This project is designed with an object-oriented programming (OOP) approach. Core logic, APIs, and UI components are implemented as classes, utilizing principles such as encapsulation, inheritance, and polymorphism. Contributors are encouraged to structure new modules and features using OOP best practices to ensure maintainability and extensibility.
## Repository Structure Overview

```
shypn/
├── archive/        # Archived utility scripts (moved from root)
├── data/           # Data model files (schemas, ORM models, sample data)
├── doc/            # Comprehensive documentation (414+ markdown files)
├── legacy/         # Legacy code from previous versions (reference only)
├── models/         # User Petri net model files (.shy format)
├── scripts/        # Utility scripts, demos (non-test)
├── src/
│   └── shypn/
│       ├── analyses/      # Analysis tools and algorithms
│       ├── canvas/        # Canvas management and overlay system
│       ├── data/          # Data models and project management
│       ├── dev/           # Development and testing utilities
│       ├── diagnostic/    # Diagnostic tools
│       ├── edit/          # Editing tools and graph layout
│       ├── engine/        # Simulation engine and behaviors
│       ├── file/          # File operations and persistence
│       ├── helpers/       # UI loaders (panels, palettes, dialogs)
│       ├── importer/      # KEGG pathway import system
│       ├── matrix/        # Petri net matrix representations
│       ├── netobjs/       # Petri net objects (Place, Transition, Arc)
│       ├── pathway/       # Pathway enhancement pipeline
│       ├── ui/            # UI component classes
│       └── utils/         # Utility functions
├── tests/          # Complete test suite (104+ test files)
├── ui/
│   ├── canvas/     # Document canvas interfaces (.ui files)
│   ├── dialogs/    # Modal dialogs (.ui files)
│   ├── main/       # Main window interface (.ui files)
│   ├── palettes/   # Control palettes (.ui files)
│   └── panels/     # Dockable panels (left/right) (.ui files)
├── workspace/      # User workspace directory
│   ├── examples/   # Example Petri net models
│   └── projects/   # User projects
└── venv/           # Python virtual environment (optional)
```

**Key Directories**:
- `src/shypn/`: Main application source code (Python)
- `ui/`: GTK UI definition files (Glade XML format)
- `tests/`: All test files (104+ files)
- `workspace/`: User workspace with examples and projects
- `doc/`: Comprehensive technical documentation (414+ files)
- `archive/`: Archived utility scripts

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
- **New Document**: File → New or Ctrl+N
- **Open Document**: File → Open or Ctrl+O or double-click in file explorer
- **Save Document**: File → Save or Ctrl+S
- **Toggle Panels**: Use the minimize/maximize buttons in panel headers
- **SwissKnife Palette**: Access Edit, Simulate, and Layout tools from unified palette
- **Property Dialogs**: Double-click objects or right-click → Properties
- **Arc Transformations**: Right-click arcs → Transform to Straight/Curved, Convert to Normal/Inhibitor
- **Simulation**: Use Simulate tools (Step, Run, Reset, Settings)
- **Graph Layout**: Apply Auto, Hierarchical, or Force-Directed layouts
- **Pan Canvas**: Middle-mouse drag or right-click and drag
- **Zoom**: Mouse wheel or zoom controls in status bar

### Advanced Features
- **Source/Sink Places**: Create places with infinite token supply/capacity
- **Parallel Arcs**: Multiple arcs between same objects curve automatically
- **Inhibitor Arcs**: Convert normal arcs to inhibitor arcs with hollow circle markers
- **KEGG Import**: Import biological pathways from KEGG database
- **Project Management**: Create and manage projects with multiple models
- **Analysis Tools**: Use right panel for model analysis and data collection

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

### Core Documentation
- **[COORDINATE_SYSTEM.md](doc/COORDINATE_SYSTEM.md)** - Coordinate system conventions (Cartesian vs Graphics)
- **[CONTRIBUTING.md](doc/CONTRIBUTING.md)** - Contribution guidelines and code standards
- **[CHANGELOG.md](doc/CHANGELOG.md)** - Version history and changes

### Technical Documentation
- **[REFINEMENTS_LOG.md](doc/REFINEMENTS_LOG.md)** - Detailed technical refinements and fixes
- **[CANVAS_CONTROLS.md](doc/CANVAS_CONTROLS.md)** - Canvas control and interaction documentation
- **[ZOOM_PALETTE.md](doc/ZOOM_PALETTE.md)** - Zoom palette implementation details
- **[FIX_EMPTY_PANEL.md](doc/FIX_EMPTY_PANEL.md)** - Panel visibility fixes documentation
- **[VSCODE_SETUP_VALIDATION.md](doc/VSCODE_SETUP_VALIDATION.md)** - VS Code setup and validation
- **[DOCUMENTATION_UPDATE_SUMMARY.md](doc/DOCUMENTATION_UPDATE_SUMMARY.md)** - Recent documentation updates

See the [`doc/`](doc/) directory for additional technical documentation and implementation notes.

**Note on Coordinate Systems**: This project uses Cartesian coordinates conceptually (origin at lower-left, Y grows upward) for all documentation and mathematical reasoning, but implements using standard graphics coordinates (origin at top-left, Y grows downward) for Cairo/GTK rendering. See [COORDINATE_SYSTEM.md](doc/COORDINATE_SYSTEM.md) for details.

## License

Specify the license here.
