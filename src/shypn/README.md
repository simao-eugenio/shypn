# shypn/

This is the main Python package for the Shypn project - a GTK4-based Petri Net modeling application. All code modules, subpackages, and application logic reside here.

## Package Structure

### `analyses/`
**Static and Dynamic Analysis Modules**
- Structural analysis (P-invariants, T-invariants, siphons, traps)
- Behavioral properties (liveness, boundedness, reachability)
- Analysis algorithms and solvers

### `data/`
**Data models and state management** for the application:
- `model_canvas_manager.py` - Canvas state management (zoom, pan, grid, document metadata)
- `canvas/` - Document model and canvas data structures
- `user_model.py` - User data models

This directory contains the business logic layer, separated from UI components.

### `dev/`
Development utilities and experimental code for testing and prototyping.

### `diagnostic/`
**System Diagnostics and Debug Tools**
- System configuration diagnostics
- Debug utilities and logging
- Performance profiling tools

### `edit/`
**Editing Operations and Controllers**
- `selection_manager.py` - Object selection and multi-select
- `drag_controller.py` - Drag and drop operations
- `object_editing_transforms.py` - Object transformations (move, resize)
- `rectangle_selection.py` - Rectangle selection tool
- `transient_arc.py` - Temporary arc drawing during creation

### `engine/`
**Simulation Engine and Transition Behaviors**
- `transition_behavior.py` - Base transition behavior interface
- `immediate_behavior.py` - Immediate transitions (priority-based)
- `timed_behavior.py` - Timed transitions (deterministic delays)
- `stochastic_behavior.py` - Stochastic transitions (exponential distributions)
- `continuous_behavior.py` - Continuous transitions (rate functions)
- `behavior_factory.py` - Factory for creating behavior instances
- `function_catalog.py` - Rate function catalog and parsing
- `simulation/` - Simulation controller and execution engine

### `file/`
**File Operations and Persistence**
- `netobj_persistency.py` - Save/Load operations for Petri Net models
- `explorer.py` - File explorer integration and file management
- JSON serialization/deserialization
- File format versioning and migration

### `helpers/`
**UI component loaders and controllers** for the GTK4 interface:
- `left_panel_loader.py` - File Operations panel loader (attachable/detachable)
- `right_panel_loader.py` - Dynamic Analyses panel loader (attachable/detachable)
- `model_canvas_loader.py` - Multi-document canvas loader with tab management
- `predefined_zoom.py` - Zoom control palette with revealer
- `edit_palette_loader.py` - Edit tools palette loader
- `edit_tools_loader.py` - Edit toolbar loader
- `simulate_palette_loader.py` - Simulation palette loader
- `simulate_tools_palette_loader.py` - Simulation tools palette loader
- `place_prop_dialog_loader.py` - Place properties dialog
- `transition_prop_dialog_loader.py` - Transition properties dialog
- `arc_prop_dialog_loader.py` - Arc properties dialog
- `color_picker.py` - Color picker widget
- `example_helper.py` - Example helper utilities

These modules bridge the UI layer (GTK4 widgets) with the data layer.

### `netobjs/`
**Petri Net Object Models**
- `petri_net_object.py` - Base class for all Petri Net objects
- `place.py` - Place nodes (tokens, initial marking, capacity)
- `transition.py` - Transition nodes (type, priority, delay, rate function)
- `arc.py` - Normal arcs (weight, multiplicity)
- `inhibitor_arc.py` - Inhibitor arcs (test without consuming)
- `curved_arc.py` - Curved normal arcs (Bézier curves)
- `curved_inhibitor_arc.py` - Curved inhibitor arcs

All objects support:
- Serialization (to_dict/from_dict)
- Rendering (draw method with Cairo)
- Selection and highlighting
- Properties editing

### `ui/`
**UI State Management**
- UI state persistence
- View state management (pan, zoom)
- Window state tracking

### `utils/`
**General utility modules** for common operations:
- `arc_transform.py` - Arc geometry transformations and coordinate conversions

## Architecture Overview

```
shypn/
├── netobjs/       → Petri Net object models (Place, Transition, Arc)
├── engine/        → Simulation engine & transition behaviors
├── data/          → Business logic & state management
├── file/          → File operations & persistence
├── edit/          → Editing operations & selection management
├── helpers/       → UI loaders & controllers (GTK4)
├── analyses/      → Static & dynamic analysis modules
├── ui/            → UI state management
├── utils/         → Shared utilities
├── diagnostic/    → System diagnostics & debugging
└── dev/           → Development tools & experiments
```

## Import Patterns

- **Petri Net objects**: `from shypn.netobjs.place import Place`
- **Data models**: `from shypn.data.model_canvas_manager import ModelCanvasManager`
- **UI helpers**: `from shypn.helpers.model_canvas_loader import create_model_canvas`
- **Simulation engine**: `from shypn.engine.simulation.controller import SimulationController`
- **File operations**: `from shypn.file.netobj_persistency import save_document, load_document`
- **Editing**: `from shypn.edit.selection_manager import SelectionManager`
- **Utils**: `from shypn.utils.arc_transform import transform_arc_coordinates`

## Recent Reorganization (October 2025)

The package structure was reorganized to improve clarity:
1. Moved `model_canvas_manager.py` from orphaned `src/data/` to `src/shypn/data/`
2. Moved UI loaders from `src/shypn/` root to `src/shypn/helpers/`:
   - `left_panel_loader.py`
   - `right_panel_loader.py`
   - `model_canvas_loader.py`
   - `predefined_zoom.py`

This separation clarifies the distinction between:
- **Data layer** (`data/`) - State and business logic
- **UI layer** (`helpers/`) - GTK4 components and controllers