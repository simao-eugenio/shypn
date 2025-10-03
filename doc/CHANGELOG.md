# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed
- Updated main README.md with current project status and accurate structure
- Enhanced CONTRIBUTING.md with strict code quality standards
- Expanded REFINEMENTS_LOG.md with October 2, 2025 updates

## [2025-10-02] - Repository Cleanup Sprint

### Added
- Comprehensive documentation updates across all main .md files
- Clear contribution guidelines prohibiting debug prints
- Usage instructions and basic operations guide in README

### Changed
- **Repository Organization**
  - Consolidated all test files from `scripts/` to `tests/` (8 files moved)
  - Removed all transition-related files preparing for fresh import (5 files)
  - Cleaned up repository structure for better organization

- **Codebase Quality Improvements**
  - Removed all debug print statements from 8 core files
  - Preserved only ERROR messages to stderr for critical failures
  - Fixed empty code blocks across multiple files
  - Ensured all Python files compile without errors

### Removed
- ✓, →, 🖱️, ✗, ⚠, 📋, ✂, 🔄 debug symbols from entire codebase
- WARNING print statements (reserved for proper logging)
- Test print statements from development code
- Example print statements from API documentation

### Fixed
- IndentationError in left_panel_loader.py (empty except block)
- IndentationError in model_canvas_loader.py (empty else blocks)
- IndentationError in file_explorer_panel.py (empty if blocks)
- Empty control flow blocks across all files

### Technical Details
**Files Modified for Debug Cleanup**:
1. `src/shypn.py` - Main application entry point
2. `src/shypn/helpers/model_canvas_loader.py` - Canvas management (~20+ prints removed)
3. `src/shypn/helpers/left_panel_loader.py` - Left panel loading
4. `src/shypn/helpers/right_panel_loader.py` - Right panel loading (~15 prints removed)
5. `src/shypn/ui/panels/file_explorer_panel.py` - File explorer UI (~40+ prints removed)
6. `src/shypn/helpers/predefined_zoom.py` - Zoom palette
7. `src/shypn/dev/example_dev.py` - Development examples
8. `src/shypn/api/file/explorer.py` - File explorer API

**Verification**:
- Zero console output on normal application startup
- All error handling preserved for critical failures
- All Python modules pass py_compile validation
- Application runs cleanly without warnings

## [2025-10-01] - Right Panel Refinements

### Fixed
- Empty right panel visible on startup (position issue in right_paned)
- Grid cells too large on startup (reversed iteration in grid subdivision)

### Changed
- Right panel position defaults to 10000 (fully collapsed)
- Grid subdivision iterates in ascending order for correct spacing
- Grid displays at correct ~5mm cells at 100% zoom

### Added
- Detailed technical documentation in REFINEMENTS_LOG.md
- Grid behavior analysis at different zoom levels

## Earlier Changes

See legacy documentation in the `legacy/` directory for historical changes and previous versions.

---

## Version Numbering

This project follows [Semantic Versioning](https://semver.org/):
- MAJOR version for incompatible API changes
- MINOR version for backwards-compatible functionality additions
- PATCH version for backwards-compatible bug fixes

## Release Process

1. Update this CHANGELOG.md with all changes
2. Update version in relevant files
3. Create git tag with version number
4. Build and test release candidate
5. Publish release with compiled documentation
