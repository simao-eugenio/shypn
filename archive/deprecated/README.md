# Deprecated Files

This directory contains Python files and UI files that are no longer actively used in the codebase.

## Recently Moved (October 23, 2025)

### File Panel V2 (Replaced by V3)
- `file_panel_v2.py` (33 KB) - File Panel V2 UI component class (replaced by File Panel V3 with XML UI + OOP)
- `file_panel_v2_loader.py` (9.0 KB) - File Panel V2 loader (replaced by file_panel_v3_loader.py)
- **Replacement**: File Panel V3 architecture (XML UI + Base class + Loader + Controller)
- **Migration Date**: October 2025

### Topology Panel Old Controller
- `topology_panel_controller_old.py` (24 KB) - Old topology panel controller (replaced by refactored version)
- **Replacement**: Refactored topology_panel_base.py with skeleton pattern
- **Migration Date**: October 2025

### UI Backup Files
- `main_window_headerbar_backup.ui` (15 KB) - Backup of main window headerbar UI definition
- **Status**: No longer needed, current headerbar working correctly

## Files Moved (October 17, 2025)

### Backup/Old Versions
- `pathway_postprocessor_old.py` - Old version of PathwayPostProcessor (replaced by newer version)
- `tree_layout.py.backup` - Backup of tree layout implementation

### Development/Testing Files
- `example_dev.py` - Development example file (not used in production)
- `palette_integration_example.py` - Example demonstrating palette integration (not used in production)

### Testbed Directories
- `swissknife_testbed/` - Development testbed for SwissKnife palette experimentation
- `settings_sub_palette_testbed/` - Development testbed for settings sub-palette

## Summary

**Total Deprecated Files**: 7 Python files (.py), 1 Python backup (.py.backup), 1 UI file (.ui), 3 directories

All deprecated files are preserved for historical reference but are not imported or used by the active codebase. The application now uses:
- File Panel V3 (XML UI architecture)
- Refactored topology panel controller
- Current main window headerbar UI
- Master Palette system with skeleton pattern

## Note
⚠️ **DO NOT USE** - These files are for reference only and may not work with the current codebase.
