# shypn/

This is the main Python package for the Shypn project - a GTK3-based Stochastic Hybrid Petri Net modeling application. All code modules, subpackages, and application logic reside here.

## Package Structure

### `analyses/`
**Static and Dynamic Analysis Modules**
- Structural analysis (P-invariants, T-invariants, siphons, traps)
- Behavioral properties (liveness, boundedness, reachability)
- Analysis algorithms and solvers
- Integration with right panel analysis tools

### `canvas/`
**Canvas Management and Overlay System**
- `canvas_overlay_manager.py` - Canvas overlay management
- `model_canvas_manager.py` - Core canvas state and object management
- Zoom, pan, grid rendering
- Multi-document support with tabs

### `data/`
**Data Models and Project Management**
- `document_model.py` - Petri net document model
- `project_models.py` - Project management system
- `workspace_state.py` - Workspace persistence
- User preferences and settings

### `dev/`
**Development Utilities and Testing**
- SwissKnife palette testbed
- Experimental features
- Prototyping utilities

### `diagnostic/`
**System Diagnostics and Debug Tools**
- System configuration diagnostics
- Debug utilities and logging
- Performance profiling tools

### `edit/`
**Editing Operations and Graph Layout**
- `editing_operations.py` - Core editing operations
- `graph_layout/` - Layout algorithms (auto, hierarchical, force-directed)
- `operations_palette.py` - Operations palette widget
- `tools_palette.py` - Edit tools palette
- Selection and transformation tools

### `engine/`
**Simulation Engine and Transition Behaviors**
- `transition_behavior.py` - Base transition behavior interface
- `immediate_behavior.py` - Immediate transitions (priority-based)
- `timed_behavior.py` - Timed transitions (deterministic delays)
- `stochastic_behavior.py` - Stochastic transitions (exponential distributions)
- `behavior_factory.py` - Factory for creating behavior instances
- Simulation controller and execution

### `file/`
**File Operations and Persistence**
- `netobj_persistency.py` - Save/Load operations for Petri Net models
- JSON serialization/deserialization
- File format versioning
- Document state management

### `helpers/`
**UI Component Loaders and Controllers**
- `model_canvas_loader.py` - Multi-document canvas with tabs
- `left_panel_loader.py` - File explorer panel (dockable)
- `right_panel_loader.py` - Analysis panel (dockable)
- `swissknife_palette.py` - Unified Edit/Simulate/Layout palette
- `simulate_tools_palette_loader.py` - Simulation controls
- Property dialog loaders (place, transition, arc)
- File explorer, project management interfaces
- Color pickers and widget utilities

### `importer/`
**External Format Import**
- `kegg/` - KEGG pathway import system
  - API client for KEGG database
  - Pathway parser and converter
  - Petri net transformation

### `matrix/`
**Petri Net Matrix Representations**
- Incidence matrix construction
- Pre/Post matrices
- Matrix-based analysis support

### `netobjs/`
**Petri Net Object Models**
- `petri_net_object.py` - Base class for all Petri Net objects
- `place.py` - Place nodes (tokens, marking, capacity, source/sink types)
- `transition.py` - Transition nodes (immediate, timed, stochastic, continuous)
- `arc.py` - Normal arcs (straight and curved with Bézier curves)
- `inhibitor_arc.py` - Inhibitor arcs (test without consuming)
- Rendering with Cairo, serialization, properties

### `pathway/`
**Pathway Enhancement Pipeline**
- `pipeline.py` - Post-processing pipeline orchestration
- `metadata_enhancer.py` - Extract and enrich metadata
- `arc_router.py` - Smart arc routing (parallel arcs, obstacles)
- `layout_optimizer.py` - Overlap resolution and spacing
- `visual_validator.py` - Visual validation against pathway images

### `ui/`
**UI Component Classes**
- `document_canvas.py` - Canvas widget implementation
- UI state management
- View state persistence

### `utils/`
**General Utility Modules**
- Common operations and helper functions
- Geometric calculations
- Color utilities

## Architecture Overview

```
shypn/
├── netobjs/       → Petri Net object models (Place, Transition, Arc)
├── engine/        → Simulation engine & transition behaviors
├── canvas/        → Canvas management & overlay system
├── data/          → Data models & project management
├── file/          → File operations & persistence
├── edit/          → Editing operations & graph layout
├── helpers/       → UI loaders & controllers (GTK3)
├── importer/      → External format import (KEGG)
├── pathway/       → Pathway enhancement pipeline
├── analyses/      → Static & dynamic analysis modules
├── matrix/        → Matrix representations
├── ui/            → UI components & state
├── utils/         → Shared utilities
├── diagnostic/    → System diagnostics & debugging
└── dev/           → Development tools & experiments
```

## Import Patterns

- **Petri Net objects**: `from shypn.netobjs.place import Place`
- **Canvas management**: `from shypn.canvas.model_canvas_manager import ModelCanvasManager`
- **UI helpers**: `from shypn.helpers.model_canvas_loader import create_model_canvas`
- **Simulation engine**: `from shypn.engine.behavior_factory import create_behavior`
- **File operations**: `from shypn.file.netobj_persistency import NetobjPersistencyManager`
- **Editing**: `from shypn.edit.editing_operations import EditingOperations`
- **KEGG Import**: `from shypn.importer.kegg.pathway_converter import PathwayConverter`
- **Pathway enhancement**: `from shypn.pathway.pipeline import EnhancementPipeline`

## Key Features

### Multi-Document Canvas
- Tabbed interface with multiple documents
- Per-document zoom and pan state
- Document switching with unsaved changes protection

### SwissKnife Unified Palette
- **Edit Tools**: Place (P), Transition (T), Arc (A), Select (S), Label (L)
- **Simulate Tools**: Step, Run, Pause, Reset, Settings
- **Layout Tools**: Auto, Hierarchical, Force-Directed

### Property Dialogs
- Place properties: Name, label, tokens, capacity, source/sink types
- Transition properties: Name, label, type (immediate/timed/stochastic)
- Arc properties: Weight, inhibitor conversion, curve transformation

### Arc System
- Straight and curved arcs (Bézier curves)
- Normal and inhibitor arcs
- Parallel arc detection with automatic curving
- Context menu transformations (straight↔curved, normal↔inhibitor)

### KEGG Import
- Import biological pathways from KEGG database
- Automatic conversion to Petri nets
- Enhancement pipeline with metadata, routing, and layout optimization

### Project Management
- Create and manage projects
- Hierarchical file organization
- Recent projects tracking
- Workspace state persistence

## Recent Reorganization (October 2025)

Major package restructuring completed:
1. **Repository cleanup**: 64 files reorganized
   - 31 markdown files moved to `doc/`
   - 19 test files moved to `tests/`
   - 14 utility scripts moved to `archive/`

2. **Debug output cleanup**: 12 files cleaned
   - All debug print statements removed
   - Logger.debug/info statements removed
   - Only critical errors remain

3. **Feature additions**:
   - Source/sink place types
   - Arc boundary precision fixes
   - Inhibitor arc positioning on curved arcs
   - Enhanced context menus

4. **Code quality**:
   - Clean production codebase
   - Consistent error handling
   - Improved documentation