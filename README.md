````markdown
# SHYpn - Systems Biology Pathway Modeling Platform

**Hybrid Petri Net Platform for Biological Pathway and Regulatory Network Modeling, Simulation, and Analysis**

A comprehensive GTK-based platform for systems biology pathway modeling with advanced simulation and analysis capabilities.

## Project Status (October 2025)

**Current State**: Active development - Feature-rich Petri net editor
- ✅ GTK3 stable implementation with Wayland support
- ✅ Multi-document canvas system with tabbed interface
- ✅ Master Palette unified panel control system
- ✅ Dockable/undockable panels with float/attach functionality
- ✅ File Panel V3 with normalized XML UI architecture
- ✅ File explorer with hierarchical tree view and file operations
- ✅ SwissKnife unified palette (Edit/Simulate/Layout tools)
- ✅ Property dialogs for all Petri net objects with topology integration
- ✅ Arc transformations (straight/curved, normal/inhibitor, parallel arcs)
- ✅ Simulation system with stochastic transitions and real-time analysis
- ✅ Graph layout algorithms (auto, hierarchical, force-directed)
- ✅ KEGG pathway import with enhancement pipeline
- ✅ Project management system
- ✅ Canvas context menus with rich functionality
- ✅ **Production-ready codebase** (all debug output removed, zero syntax errors)
- ✅ **Clean repository structure** (test files organized, shell scripts archived)

**Recent Updates** (November 2025):
- ✅ **Catalyst/TestArc Implementation** - Complete fix for KEGG model catalysts
  - Removed all silent fallbacks in simulation engine (explicit error handling)
  - Added proper TestArc handling in enablement checks (non-consuming arcs)
  - Fixed dict/list compatibility in behavior code
  - All KEGG models now load and simulate correctly with catalysts
- ✅ **Hybrid Petri Net Validation** - Equilibrium and deadlock analysis
  - Documented continuous chain equilibrium behavior
  - Created test suite for hybrid transition type combinations
  - Mathematical validation of Michaelis-Menten equilibrium
  - Design guidelines for biological pathway modeling
- ✅ **Repository Organization** - Major cleanup (Nov 5, 2025)
  - Moved 673 documentation files from root to `doc/`
  - Moved 90 test/diagnostic files to `tests/diagnostic/`
  - Moved 54 utility scripts to `scripts/`
  - Clean root directory with proper project structure
- ✅ **Canvas Health fixing series** - Complete feature parity across all canvas creation flows (5 branches merged)
  - Color matching (transitions: border+fill, places: border) across Default/File New/File Open/KEGG/SBML
  - Locality detection and automatic addition
  - Data collector wiring for plot panels
  - Pan/Zoom NavigationToolbar integration
  - Wayland compatibility fixes
- ✅ **SBML workflow enhancements** - Production-ready biological modeling
  - 7 firing policies (random, earliest, latest, priority, race, age, preemptive-priority)
  - Fixed duplicate ID bugs (DocumentModel.from_dict + ID parsing "10" vs "P10")
  - Fixed stochastic transition scheduling
  - Can load SBML models and add source/sink transitions without conflicts
  - Scientific corrections (mass action → stochastic terminology)
- ✅ **Master Palette system** - Unified panel control with exclusive button logic
- ✅ **Panel architecture refactoring** - All 5 panels use skeleton pattern (synchronous float/attach)
- ✅ **File Panel V3** - Normalized XML UI + OOP architecture (Base → Loader → Controller)
- ✅ **CategoryFrame structure** - Programmatic collapsible categories with exclusive expansion
- ✅ **Float/attach functionality** - All panels support detach to floating window
- ✅ **Analysis panel performance optimization** - 95% faster updates (156ms → 7ms)
- ✅ **Locality integration fix** - Complete P-T-P pattern plotting in analyses
- ✅ **Canvas management** - Proper reset/clear with immediate visual feedback
- ✅ **UI improvements** - Hierarchical display of locality objects with color-coded indicators
- ✅ **Comprehensive testing** - 34/34 property dialog and analysis tests passing (100%)
- ✅ **Documentation** - 24+ new comprehensive documentation files
- ✅ **Complete repository cleanup** - Legacy code removed, deprecated files archived
- ✅ **Debug print removal** - 107 debug prints removed from 26 files
- ✅ **Syntax error fixes** - 27 empty code blocks fixed in 15 files
- ✅ **Code quality** - Zero syntax errors, production-ready state
- ✅ Arc boundary precision fixes (proper border width accounting)
- ✅ Inhibitor arc hollow circle positioning on curved arcs
- ✅ Context menu enhancements (arc transformation options)
- ✅ Source/sink place types implementation
- ✅ Workspace state persistence
- ✅ Unsaved changes protection

## GTK 3 Notice

This project currently uses GTK 3.2+. While there was consideration for GTK 4 migration, the project is stabilizing on GTK 3 for production use. The codebase follows modern Python and OOP practices regardless of the GTK version.
 
## Architectural Guideline: Object-Oriented Design

This project is designed with an object-oriented programming (OOP) approach. Core logic, APIs, and UI components are implemented as classes, utilizing principles such as encapsulation, inheritance, and polymorphism. Contributors are encouraged to structure new modules and features using OOP best practices to ensure maintainability and extensibility.
## Repository Structure Overview

```
shypn/
├── archive/        # Archived and deprecated code (no longer in active use)
│   ├── deprecated/ # Deprecated Python files (6 items)
│   ├── ui_removed/ # Deprecated UI files (none yet)
│   └── *.py        # Legacy analysis and debug scripts
├── data/           # Data model files (schemas, ORM models, sample data)
├── doc/            # Comprehensive documentation (673 markdown files)
│   ├── cleanup/    # Cleanup documentation (October 2025)
│   ├── topology/   # Topology and network analysis documentation
│   ├── independency/ # Petri net independency analysis
│   ├── crossfetch/ # Cross-model fetching documentation
│   ├── heuristic/  # Heuristic algorithms documentation
│   ├── atomicity/  # Atomic operations documentation
│   ├── concurrency/ # Concurrency and parallelism documentation
│   ├── time/       # Time-related documentation
│   ├── project/    # Project management documentation
│   └── validation/ # Validation and testing documentation
├── models/         # User Petri net model files (.shy format - primary extension)
├── scripts/        # Utility scripts and diagnostic tools (54 files)
│   ├── add_source_transitions.py
│   ├── analyze_biomd61_parameters.py
│   ├── check_arc_types.py
│   ├── check_stochastic_sources.py
│   ├── compare_topology.py
│   ├── diagnose_firing_issue.py
│   ├── diagnosis_sigmoid_issue.py
│   ├── fix_stochastic_to_continuous.py
│   ├── inspect_kegg_ec_numbers.py
│   └── verify_biomd61_fix.py
├── src/
│   └── shypn/
│       ├── analyses/      # Analysis tools and real-time plotting (optimized)
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
├── tests/          # Complete test suite (130+ test files)
│   ├── diagnostic/        # Diagnostic and test scripts (90 files)
│   │   ├── test_*.py      # Unit and integration tests
│   │   ├── diagnose_*.py  # Diagnostic scripts
│   │   ├── debug_*.py     # Debug scripts
│   │   ├── check_*.py     # Validation scripts
│   │   └── analyze_*.py   # Analysis scripts
│   ├── validation/        # Validation test suites
│   │   ├── continuous/    # Continuous transition tests (including chain equilibrium)
│   │   ├── stochastic/    # Stochastic transition tests
│   │   ├── immediate/     # Immediate transition tests
│   │   └── timed/         # Timed transition tests
│   ├── prop_dialogs/      # Property dialog integration tests (34 tests)
│   └── ...
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
- `src/shypn/`: Main application source code (Python) - Production ready
  - `analyses/`: Real-time plotting with 95% performance improvement
  - `engine/`: Simulation engine with hybrid Petri net support (continuous, stochastic, immediate, timed)
  - `helpers/`: Panel loaders (Files V3, Analyses, Pathways, Topology) with skeleton pattern
  - `ui/`: UI component classes (FilePanelBase, CategoryFrame, dialogs, controllers)
- `ui/`: GTK UI definition files (Glade XML format) - All files actively used
  - `panels/`: Panel UI definitions including file_panel_v3.ui
- `tests/`: Complete test suite (130+ files, all tests passing)
  - `diagnostic/`: Test and diagnostic scripts (90 files) - organized Nov 5, 2025
  - `validation/`: Validation test suites for all transition types
  - `prop_dialogs/`: Integration tests for Place, Arc, and Transition dialogs (100% passing)
- `scripts/`: Utility scripts (54 files) - KEGG inspection, topology comparison, diagnostic tools
- `workspace/`: User workspace with examples and projects
- `doc/`: Comprehensive technical documentation (673 files) - organized Nov 5, 2025
  - `validation/`: Validation documentation including continuous chain equilibrium analysis
  - Recent additions: Catalyst fix, hybrid Petri net analysis, canvas health series
  - Panel architecture, File Panel V3, Master Palette system
- `archive/`: Archived and deprecated code (not for active use)
  - `deprecated/`: 6 unused Python files
  - `sh/`: Historical test shell scripts (4 files, moved Oct 2025)
  - Legacy analysis and debug scripts

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
- **Real-Time Analysis**: Optimized plotting with 95% performance improvement (7ms updates)
- **Locality Plotting**: Automatic selection of Place-Transition-Place patterns for analysis
- **Property Dialogs**: Complete topology integration showing network connections
- **Analysis Tools**: Use right panel for model analysis and data collection with hierarchical display

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

All project documentation is located in the [`doc/`](doc/) directory (440+ files):

### Core Documentation
- **[COORDINATE_SYSTEM.md](doc/COORDINATE_SYSTEM.md)** - Coordinate system conventions (Cartesian vs Graphics)
- **[CONTRIBUTING.md](doc/CONTRIBUTING.md)** - Contribution guidelines and code standards
- **[CHANGELOG.md](doc/CHANGELOG.md)** - Version history and changes

### Canvas Health Series (October 2025)
- **[FIRING_POLICIES.md](doc/FIRING_POLICIES.md)** - 7 firing policies implementation
- **[FIX_STOCHASTIC_SCHEDULING_INITIALIZATION.md](doc/FIX_STOCHASTIC_SCHEDULING_INITIALIZATION.md)** - Stochastic transition scheduling fixes
- **[DUPLICATE_ID_BUG_FIX.md](doc/DUPLICATE_ID_BUG_FIX.md)** - Duplicate ID bug analysis and fix
- **[SBML_COMPLETE_FLOW_ANALYSIS.md](doc/SBML_COMPLETE_FLOW_ANALYSIS.md)** - Complete SBML import pipeline documentation
- **[DUPLICATE_ID_BUG_ALL_FLOWS_ANALYSIS.md](doc/DUPLICATE_ID_BUG_ALL_FLOWS_ANALYSIS.md)** - Cross-flow duplicate ID analysis

### Recent Features (December 2024)
- **[ANALYSES_PANEL_PERFORMANCE_COMPLETE.md](doc/ANALYSES_PANEL_PERFORMANCE_COMPLETE.md)** - Performance optimization (95% improvement)
- **[ANALYSES_COMPLETE_FIX_SUMMARY.md](doc/ANALYSES_COMPLETE_FIX_SUMMARY.md)** - Complete analysis panel fix summary
- **[ANALYSES_LOCALITY_AND_RESET_FIXES.md](doc/ANALYSES_LOCALITY_AND_RESET_FIXES.md)** - Locality integration and reset fixes
- **[ANALYSES_LOCALITY_UI_LIST_FIX.md](doc/ANALYSES_LOCALITY_UI_LIST_FIX.md)** - UI list display improvements
- **[DIALOG_PROPERTIES_SIMULATION_INTEGRATION_ANALYSIS.md](doc/DIALOG_PROPERTIES_SIMULATION_INTEGRATION_ANALYSIS.md)** - Complete integration analysis
- **[PROPERTY_DIALOG_TESTS_100_PERCENT.md](doc/PROPERTY_DIALOG_TESTS_100_PERCENT.md)** - Test coverage results (34/34 passing)
- **[PLACE_DIALOG_TOPOLOGY_INTEGRATION.md](doc/PLACE_DIALOG_TOPOLOGY_INTEGRATION.md)** - Place dialog topology integration
- **[ARC_DIALOG_TOPOLOGY_INTEGRATION.md](doc/ARC_DIALOG_TOPOLOGY_INTEGRATION.md)** - Arc dialog topology integration
- **[TRANSITION_DIALOG_TOPOLOGY_INTEGRATION.md](doc/TRANSITION_DIALOG_TOPOLOGY_INTEGRATION.md)** - Transition dialog topology integration

### Technical Documentation
- **[REFINEMENTS_LOG.md](doc/REFINEMENTS_LOG.md)** - Detailed technical refinements and fixes
- **[CANVAS_CONTROLS.md](doc/CANVAS_CONTROLS.md)** - Canvas control and interaction documentation
- **[ZOOM_PALETTE.md](doc/ZOOM_PALETTE.md)** - Zoom palette implementation details
- **[FIX_EMPTY_PANEL.md](doc/FIX_EMPTY_PANEL.md)** - Panel visibility fixes documentation
- **[VSCODE_SETUP_VALIDATION.md](doc/VSCODE_SETUP_VALIDATION.md)** - VS Code setup and validation
- **[DOCUMENTATION_UPDATE_SUMMARY.md](doc/DOCUMENTATION_UPDATE_SUMMARY.md)** - Recent documentation updates

### Architecture Documentation
- **[doc/topology/](doc/topology/)** - Topology and network analysis
- **[doc/independency/](doc/independency/)** - Petri net independency analysis
- **[doc/crossfetch/](doc/crossfetch/)** - Cross-model fetching
- **[doc/heuristic/](doc/heuristic/)** - Heuristic algorithms
- **[doc/atomicity/](doc/atomicity/)** - Atomic operations
- **[doc/concurrency/](doc/concurrency/)** - Concurrency and parallelism
- **[doc/time/](doc/time/)** - Time-related documentation
- **[doc/project/](doc/project/)** - Project management
- **[doc/validation/](doc/validation/)** - Validation and testing

### Cleanup Documentation (October 2025)
- **[INDENTATION_FIXES_COMPLETE.md](doc/INDENTATION_FIXES_COMPLETE.md)** - Indentation error fixes (27 blocks in 15 files)
- **[cleanup/](doc/cleanup/)** - Complete cleanup documentation
  - Repository cleanup summary
  - UI analysis report
  - Debug print removal report
  - Final verification results

See the [`doc/`](doc/) directory for additional technical documentation and implementation notes.

**Note on Coordinate Systems**: This project uses Cartesian coordinates conceptually (origin at lower-left, Y grows upward) for all documentation and mathematical reasoning, but implements using standard graphics coordinates (origin at top-left, Y grows downward) for Cairo/GTK rendering. See [COORDINATE_SYSTEM.md](doc/COORDINATE_SYSTEM.md) for details.

## License

Specify the license here.
