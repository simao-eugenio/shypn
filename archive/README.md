# Archive Directory

This directory contains deprecated and archived code that has been removed from active use but preserved for reference.

## Structure

- **`deprecated/`** - Python files that are no longer used in the current codebase
- **`ui_removed/`** - UI definition files (.ui) that have been deprecated
- **Utility scripts** - Legacy utility scripts moved from the repository root

## Contents

### Deprecated Python Files (6 items)
Files that are no longer invoked from the current codebase:

1. **`analyze_compound_connections.py`** - Legacy compound connection analysis
2. **`analyze_saved_file.py`** - Legacy file analysis tool
3. **`analyze_screenshot_model.py`** - Screenshot model analyzer (obsolete)
4. **`debug_arc_creation.py`** - Old arc creation debugging tool
5. **`debug_arc_rendering.py`** - Old arc rendering debugging tool
6. **`deep_investigate_arcs.py`** - Deep arc investigation utility

### Additional Archived Scripts
Legacy utility and debugging scripts from previous development phases:

- `diagnose_all_spurious_lines.py`
- `diagnose_spurious_lines.py`
- `inspect_gui_arcs.py`
- `inspect_saved_file.py`
- `intercept_arc_rendering.py`
- `lookup_compounds.py`
- `trace_arc_creation.py`
- `visualize_connections.py`

## Purpose

These files are kept for:
- Historical reference
- Understanding past implementation approaches
- Potential recovery of useful code patterns
- Documentation of what didn't work and why

## Status

⚠️ **DO NOT USE** - These files are not maintained and may not work with the current codebase.

## Cleanup Date

- **Archived:** October 17, 2025
- **Reason:** Repository cleanup - removed unused code and deprecated utilities
- **Related Documentation:** See `doc/cleanup/` for cleanup reports

## Notes

If you need to reference or restore any of these files, consult the git history or the cleanup documentation in `doc/cleanup/`.
