# Documentation Directory

This directory contains comprehensive technical documentation for the SHYpn project (440+ markdown files).

## Latest Documentation (October 2025)

### Canvas Health Series
Major feature series providing complete parity across all canvas creation flows:

- **[FIRING_POLICIES.md](FIRING_POLICIES.md)** - 7 firing policies for biological realism
  - Random, Earliest, Latest, Priority, Race, Age, Preemptive-Priority
  - Default policy: 'random' for biological systems
  
- **[FIX_STOCHASTIC_SCHEDULING_INITIALIZATION.md](FIX_STOCHASTIC_SCHEDULING_INITIALIZATION.md)** - Stochastic transition scheduling
  - Fixed initialization timing issues
  - Proper enablement state tracking
  
- **[DUPLICATE_ID_BUG_FIX.md](DUPLICATE_ID_BUG_FIX.md)** - Critical duplicate ID bug fixes
  - Bug #1: DocumentModel.from_dict() counter update
  - Bug #2: ID parsing ("10" vs "P10" format)
  
- **[SBML_COMPLETE_FLOW_ANALYSIS.md](SBML_COMPLETE_FLOW_ANALYSIS.md)** - Complete SBML import pipeline
  - Parse → Post-process → Convert → Save → Load
  - ID generation flow documentation
  
- **[DUPLICATE_ID_BUG_ALL_FLOWS_ANALYSIS.md](DUPLICATE_ID_BUG_ALL_FLOWS_ANALYSIS.md)** - Cross-flow analysis
  - SBML, KEGG, Interactive drawing, File operations
  - Impact assessment across all workflows

### Analysis Panel Series (December 2024)
Performance optimization and feature enhancements:

- **[ANALYSES_PANEL_PERFORMANCE_COMPLETE.md](ANALYSES_PANEL_PERFORMANCE_COMPLETE.md)** - 95% performance improvement
- **[ANALYSES_COMPLETE_FIX_SUMMARY.md](ANALYSES_COMPLETE_FIX_SUMMARY.md)** - Complete fix summary
- **[ANALYSES_LOCALITY_AND_RESET_FIXES.md](ANALYSES_LOCALITY_AND_RESET_FIXES.md)** - Locality integration
- **[ANALYSES_LOCALITY_UI_LIST_FIX.md](ANALYSES_LOCALITY_UI_LIST_FIX.md)** - UI improvements

### Property Dialog Integration
Complete topology integration for all dialogs:

- **[PLACE_DIALOG_TOPOLOGY_INTEGRATION.md](PLACE_DIALOG_TOPOLOGY_INTEGRATION.md)** - Place dialog
- **[ARC_DIALOG_TOPOLOGY_INTEGRATION.md](ARC_DIALOG_TOPOLOGY_INTEGRATION.md)** - Arc dialog  
- **[TRANSITION_DIALOG_TOPOLOGY_INTEGRATION.md](TRANSITION_DIALOG_TOPOLOGY_INTEGRATION.md)** - Transition dialog
- **[DIALOG_PROPERTIES_SIMULATION_INTEGRATION_ANALYSIS.md](DIALOG_PROPERTIES_SIMULATION_INTEGRATION_ANALYSIS.md)** - Complete integration
- **[PROPERTY_DIALOG_TESTS_100_PERCENT.md](PROPERTY_DIALOG_TESTS_100_PERCENT.md)** - Test results (34/34 passing)

## Core Documentation

### Project Fundamentals
- **[COORDINATE_SYSTEM.md](COORDINATE_SYSTEM.md)** - Coordinate system conventions
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[CHANGELOG.md](CHANGELOG.md)** - Version history

### Technical Documentation
- **[REFINEMENTS_LOG.md](REFINEMENTS_LOG.md)** - Detailed technical refinements
- **[CANVAS_CONTROLS.md](CANVAS_CONTROLS.md)** - Canvas control documentation
- **[ZOOM_PALETTE.md](ZOOM_PALETTE.md)** - Zoom palette implementation
- **[FIX_EMPTY_PANEL.md](FIX_EMPTY_PANEL.md)** - Panel visibility fixes
- **[VSCODE_SETUP_VALIDATION.md](VSCODE_SETUP_VALIDATION.md)** - VS Code setup
- **[DOCUMENTATION_UPDATE_SUMMARY.md](DOCUMENTATION_UPDATE_SUMMARY.md)** - Recent updates

### Arc Features
- **[ALL_ARC_TYPES_TRANSFORMATION_VERIFIED.md](ALL_ARC_TYPES_TRANSFORMATION_VERIFIED.md)** - Arc transformations
- **[ARC_BORDER_FIX_SUMMARY.md](ARC_BORDER_FIX_SUMMARY.md)** - Border rendering fixes
- **[ARC_BOUNDARY_PRECISION_FIX.md](ARC_BOUNDARY_PRECISION_FIX.md)** - Boundary precision
- **[ARC_CONTEXT_MENU_FIX.md](ARC_CONTEXT_MENU_FIX.md)** - Context menu enhancements
- **[ARC_DIALOG_COMPACTNESS_REFINEMENT.md](ARC_DIALOG_COMPACTNESS_REFINEMENT.md)** - Dialog UI improvements
- **[ARC_DIALOG_LOADING_FIX.md](ARC_DIALOG_LOADING_FIX.md)** - Dialog loading fixes
- **[ARC_EDITING_CURRENT_STATE.md](ARC_EDITING_CURRENT_STATE.md)** - Current implementation state

## Documentation by Category

### `/topology/`
Network topology and connection analysis documentation

### `/independency/`
Petri net independency and conflict analysis

### `/crossfetch/`
Cross-model data fetching strategies

### `/heuristic/`
Heuristic algorithms for layout and optimization

### `/atomicity/`
Atomic operations and transaction handling

### `/concurrency/`
Concurrency patterns and parallelism

### `/time/`
Time-based operations and temporal logic

### `/project/`
Project management system documentation

### `/validation/`
Testing and validation procedures

### `/cleanup/` (October 2025)
Repository cleanup documentation:
- **[INDENTATION_FIXES_COMPLETE.md](INDENTATION_FIXES_COMPLETE.md)** - Fixed 27 blocks in 15 files
- Repository cleanup summary
- UI analysis report
- Debug print removal (107 prints from 26 files)
- Final verification results

## Documentation Statistics

- **Total Files**: 440+ markdown documents
- **Recent Additions**: Canvas Health series (5 docs), Cleanup documentation (4 docs)
- **Coverage**: All major features documented
- **Test Documentation**: 100% property dialog tests documented
- **API Documentation**: Complete engine and behavior documentation

## How to Use This Documentation

1. **For New Developers**: Start with CONTRIBUTING.md and COORDINATE_SYSTEM.md
2. **For Feature Work**: Check the relevant category directory (e.g., /topology/ for network features)
3. **For Bug Fixes**: Review recent fix documentation (ANALYSES_*, ARC_*, DUPLICATE_ID_*)
4. **For Testing**: See PROPERTY_DIALOG_TESTS_100_PERCENT.md and /validation/
5. **For Architecture**: Review technical documentation and refinements logs

## Maintenance

Documentation is actively maintained and updated with each major feature or fix. When adding new features:

1. Document the feature in the relevant category directory
2. Update this README if it's a major feature
3. Add test documentation if tests are included
4. Update CHANGELOG.md with user-facing changes

## Related Directories

- `tests/`: Test files referenced in documentation (organized November 2025)
- `scripts/`: Utility and diagnostic scripts (organized November 2025)
- `src/shypn/`: Source code documented here
- `ui/`: UI files and dialog specifications
