# Deprecated Code Audit Report
**Date**: December 28, 2025  
**Branch**: Signal-Information-Flow  
**Audited by**: GitHub Copilot

---

## Executive Summary

This audit identifies deprecated, obsolete, and legacy code in the SHYpn codebase that should be moved to the `/archive/deprecated/` directory or removed entirely.

**Files to Move**: 3 files  
**Modules with Deprecated Code**: 15+ modules  
**Legacy Compatibility Code**: Multiple locations

---

## 1. CRITICAL - Files with "_old" Suffix (MOVE IMMEDIATELY)

### 1.1 topology_panel_loader_old.py
- **Location**: `src/shypn/helpers/topology_panel_loader_old.py`
- **Status**: ⚠️ DEPRECATED FILE
- **Description**: Old version of topology panel loader (expander design)
- **Action**: MOVE to `archive/deprecated/helpers/`
- **Rationale**: The filename explicitly indicates it's an old version
- **Date Created**: 2025-10-20

### 1.2 viability_panel_old.py
- **Location**: `src/shypn/ui/panels/viability/viability_panel_old.py`
- **Status**: ⚠️ DEPRECATED FILE
- **Description**: Old version of viability panel UI
- **Action**: MOVE to `archive/deprecated/ui/panels/viability/`
- **Rationale**: Replaced by newer viability panel implementation
- **Date Created**: November 9, 2025

---

## 2. HIGH PRIORITY - Explicitly Deprecated Modules

### 2.1 mode_events.py
- **Location**: `src/shypn/events/mode_events.py`
- **Status**: 🚨 DEPRECATED WITH WARNING
- **Deprecation Notice**: Lines 1-21 contain explicit deprecation warning
- **Warning Type**: `DeprecationWarning` (stacklevel=2)
- **Replacement**: Use `shypn.engine.simulation.state.SimulationStateDetector`
- **Documentation**: `doc/modes/MODE_ELIMINATION_PLAN.md`
- **Archive Reference**: `archive/mode/mode_events.py` (already exists)
- **Action**: REMOVE from src/ (already archived)
- **Risk Level**: LOW (deprecation warning active since early 2025)

**Deprecation Message**:
```python
"""⚠️ DEPRECATED: This module is deprecated and will be removed in a future version.
The application no longer uses explicit edit/simulate modes."""
```

---

## 3. MEDIUM PRIORITY - Methods Marked DEPRECATED

### 3.1 SimulationSettings - Tau-Leaping Methods
- **Location**: `src/shypn/engine/simulation/settings.py`
- **Lines**: 180-189
- **Methods**:
  - `enable_tau_leaping()` - Line 180: "DEPRECATED: τ-leaping is always enabled"
  - `disable_tau_leaping()` - Line 189: "DEPRECATED: τ-leaping cannot be disabled"
- **Rationale**: τ-leaping is now the only stochastic engine
- **Action**: Add `@deprecated` decorator, maintain for compatibility
- **Migration Path**: Remove method calls from client code

### 3.2 PathwayConverter - Explicit Places Method
- **Location**: `src/shypn/data/pathway/pathway_converter.py`
- **Line**: 1037
- **Method**: `_create_explicit_places_for_compartments_and_parameters()`
- **Status**: `[DEPRECATED]` marker in docstring
- **Action**: Review usage, consider removal if unused

### 3.3 KEGGImportPanel - Direct Canvas Import
- **Location**: `src/shypn/helpers/kegg_import_panel.py`
- **Line**: 712
- **Method**: Old direct-to-canvas import method
- **Status**: `DEPRECATED: Old direct-to-canvas import`
- **Action**: Remove or isolate behind feature flag

### 3.4 SimulateToolsPaletteLoader - Settings Panel Visibility
- **Location**: `src/shypn/helpers/simulate_tools_palette_loader.py`
- **Line**: 778
- **Note**: `DEPRECATED: Settings panel visibility is now managed by ParameterPanelManager (Phase 3)`
- **Action**: Remove deprecated visibility management code

---

## 4. LEGACY COMPATIBILITY CODE (DOCUMENT & REVIEW)

### 4.1 EditPaletteLoader - Backwards Compatibility Attributes
- **Location**: `src/shypn/helpers/edit_palette_loader.py`
- **Lines**: 52-53, 157-178
- **Code**:
```python
self.tools_palette_loader = None              # OLD: Deprecated - for backwards compatibility
self.editing_operations_palette_loader = None # OLD: Deprecated - for backwards compatibility
```
- **Status**: Maintained for backward compatibility
- **Action**: Identify dependents, create migration plan
- **Risk**: Breaking changes if removed

### 4.2 ModelCanvasLoader - Multiple Deprecated Features
- **Location**: `src/shypn/helpers/model_canvas_loader.py`
- **Deprecated Items**:
  - Line 1049: Auto-close default tabs feature (disabled)
  - Line 1135-1137: `title` and `replace_empty_default` parameters
  - Line 2149: "OLD PALETTE CODE - Keeping temporarily for reference"
  - Line 4344: `OBSOLETE` viability panel management method
- **Action**: Clean up commented code blocks, remove obsolete parameters

### 4.3 CanvasLifecycleAdapter
- **Location**: `src/shypn/canvas/lifecycle/adapter.py`
- **Purpose**: Bridge for migrating from old dictionary pattern to new lifecycle system
- **Status**: Legacy compatibility layer
- **Lines**: 1-378 (entire file is compatibility code)
- **Action**: KEEP but document migration timeline
- **Note**: Critical for gradual migration, not truly deprecated yet

### 4.4 BRENDA Client - Legacy Parsing
- **Location**: `src/shypn/data/brenda_soap_client.py`
- **Lines**: 416, 479, 541
- **Code**: "Legacy string parsing (keep for backward compatibility)"
- **Action**: Document that this maintains compatibility with old BRENDA API responses

---

## 5. OBSOLETE CODE BLOCKS (REMOVE)

### 5.1 CanvasOverlayManager
- **Location**: `src/shypn/canvas/canvas_overlay_manager.py`
- **Line**: 180
- **Code**: `# OLD CODE - REMOVED: Don't create simulate_tools_palette separately anymore`
- **Action**: Verify removed, clean up comment

### 5.2 SimulateToolsPaletteLoader
- **Location**: `src/shypn/helpers/simulate_tools_palette_loader.py`
- **Line**: 1500
- **Code**: `# ... (rest of old toggle code)`
- **Action**: Remove commented placeholder

### 5.3 ViabilityPanel
- **Location**: `src/shypn/ui/panels/viability/viability_panel.py`
- **Lines**: 2073-2092
- **Methods**:
  - `clear_all_results()` - "simplified - removed sections no longer exist"
  - `populate_diagnosis_summary()` - "REMOVED - UI section no longer exists"
  - `populate_suggestions_tree()` - "REMOVED - UI sections no longer exist"
- **Action**: Remove stub methods if truly unused

---

## 6. WAYLAND COMPATIBILITY NOTES (KEEP)

The following are NOT deprecated but noted for context:

- **Location**: Multiple files
- **Pattern**: `# Use popup_at_pointer() instead of deprecated popup() for Wayland compatibility`
- **Files**: 
  - `src/shypn/helpers/file_explorer_panel.py:698`
  - `src/shypn/helpers/model_canvas_loader.py:3585`
- **Status**: ✅ ACTIVE MIGRATION (GTK3 API deprecation, not SHYpn deprecation)
- **Action**: NO ACTION NEEDED (this is proper modernization)

---

## 7. ARCHIVE DIRECTORY AUDIT

### 7.1 Existing Archived Content
```
archive/
├── deprecated/
│   ├── README.md
│   ├── dialogs/
│   ├── file_panel_v2.py
│   ├── file_panel_v2_loader.py
│   ├── pathway_postprocessor_old.py
│   ├── topology_panel.py.old
│   ├── topology_panel_base.py.old
│   ├── topology_panel_controller.py.backup_accordion
│   └── [many more files]
├── mode/
├── refactor_main/
├── ui_removed/
└── [analysis scripts]
```

### 7.2 Legacy Backup
```
legacy/
├── BACKUP_INFO.md
├── shypn_backup_20251219_203422.tar.gz
└── src/
```

---

## 8. RECOMMENDED ACTIONS

### Priority 1: IMMEDIATE (This Week)
1. ✅ **MOVE**: `src/shypn/helpers/topology_panel_loader_old.py` → `archive/deprecated/helpers/`
2. ✅ **MOVE**: `src/shypn/ui/panels/viability/viability_panel_old.py` → `archive/deprecated/ui/panels/viability/`
3. ✅ **REMOVE**: `src/shypn/events/mode_events.py` (already archived, has deprecation warning)

### Priority 2: SHORT TERM (Next Sprint)
4. 📝 **DOCUMENT**: Create `DEPRECATION_TIMELINE.md` with migration paths for:
   - `EditPaletteLoader` backward compatibility attributes
   - `SimulationSettings` tau-leaping methods
   - `ModelCanvasLoader` obsolete parameters

5. 🧹 **CLEAN**: Remove commented "OLD CODE" blocks:
   - `canvas_overlay_manager.py:180`
   - `simulate_tools_palette_loader.py:1500`
   - `model_canvas_loader.py:2149`

### Priority 3: MEDIUM TERM (Next Month)
6. 🔍 **AUDIT**: Identify all dependencies on:
   - `CanvasLifecycleAdapter` (prepare for direct lifecycle API usage)
   - Legacy palette attributes in `EditPaletteLoader`
   - BRENDA legacy string parsing (check if still needed)

7. 🗑️ **REMOVE**: Stub methods in `ViabilityPanel` if confirmed unused:
   - `populate_diagnosis_summary()`
   - `populate_suggestions_tree()`

### Priority 4: LONG TERM (Future Release)
8. 🚀 **MIGRATE**: Remove `CanvasLifecycleAdapter` once all code uses direct lifecycle API
9. 🔄 **REFACTOR**: Consolidate all deprecated code markers with `@deprecated` decorator
10. 📚 **DOCUMENT**: Update all API documentation to remove references to deprecated methods

---

## 9. DEPRECATION DECORATOR RECOMMENDATION

Create a standard deprecation decorator for Python code:

```python
# src/shypn/utils/decorators.py

import warnings
from functools import wraps

def deprecated(reason, version=None, removal_version=None):
    """Mark function/method as deprecated.
    
    Args:
        reason: Why deprecated and what to use instead
        version: Version where deprecation began
        removal_version: Version where it will be removed
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            msg = f"{func.__name__} is deprecated"
            if version:
                msg += f" since v{version}"
            if removal_version:
                msg += f" and will be removed in v{removal_version}"
            msg += f". {reason}"
            
            warnings.warn(msg, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage:
@deprecated("Use SimulationStateDetector instead", 
            version="2.4.0", 
            removal_version="2.6.0")
def get_current_mode():
    pass
```

---

## 10. FILES TO MOVE - DETAILED LIST

### Immediate Moves (Priority 1)

#### File 1: topology_panel_loader_old.py
```bash
SOURCE: src/shypn/helpers/topology_panel_loader_old.py
DEST:   archive/deprecated/helpers/topology_panel_loader_old.py
SIZE:   220 lines
DATE:   2025-10-20
REASON: Filename explicitly indicates old version
CHECK:  grep -r "topology_panel_loader_old" src/  # Verify no imports
```

#### File 2: viability_panel_old.py
```bash
SOURCE: src/shypn/ui/panels/viability/viability_panel_old.py
DEST:   archive/deprecated/ui/panels/viability/viability_panel_old.py
SIZE:   352 lines
DATE:   2025-11-09
REASON: Replaced by newer viability panel
CHECK:  grep -r "viability_panel_old" src/  # Verify no imports
```

#### File 3: mode_events.py
```bash
SOURCE: src/shypn/events/mode_events.py
DEST:   [DELETE - already archived at archive/mode/mode_events.py]
SIZE:   98 lines
STATUS: Has DeprecationWarning active
REASON: Already archived, explicitly deprecated in docstring
CHECK:  grep -r "from.*mode_events import" src/  # Check for imports
ACTION: If no imports found, DELETE (already archived)
```

---

## 11. IMPORT DEPENDENCY CHECK COMMANDS

Before moving files, run these checks:

```bash
# Check for imports of topology_panel_loader_old
cd /home/simao/projetos/shypn
grep -r "topology_panel_loader_old" src/ --include="*.py"
grep -r "from.*topology_panel_loader_old" src/ --include="*.py"

# Check for imports of viability_panel_old
grep -r "viability_panel_old" src/ --include="*.py"
grep -r "from.*viability_panel_old" src/ --include="*.py"

# Check for imports of mode_events
grep -r "mode_events" src/ --include="*.py"
grep -r "from.*events.*import.*Mode" src/ --include="*.py"
```

---

## 12. CONCLUSION

**Total Deprecated Items Found**: 20+  
**Immediate Action Items**: 3 files to move/remove  
**Medium-Term Cleanup**: ~10 code blocks to clean  
**Long-Term Refactoring**: 3 major subsystems (lifecycle adapter, palette compatibility, settings methods)

**Risk Assessment**:
- **LOW RISK**: Moving _old files (no known dependents)
- **MEDIUM RISK**: Removing deprecated methods (may have legacy code dependencies)
- **HIGH RISK**: Removing CanvasLifecycleAdapter (critical for backward compatibility)

**Recommended Timeline**:
- Week 1: Move _old files (this can be done immediately)
- Week 2-4: Document deprecation timeline and add decorators
- Month 2-3: Remove commented OLD CODE blocks
- Quarter 2: Major refactoring (lifecycle adapter, palette system)

---

## 13. NEXT STEPS

1. **IMMEDIATE**: Execute Priority 1 actions (move 3 files)
2. **CREATE**: `docs/DEPRECATION_POLICY.md` with versioning strategy
3. **ADD**: `@deprecated` decorator to all marked methods
4. **TRACK**: Create GitHub issues for each Priority 2-4 item
5. **TEST**: Ensure no regressions after each move/removal

---

**Generated**: 2025-12-28  
**Auditor**: GitHub Copilot  
**Review Status**: Pending human review  
**Branch**: Signal-Information-Flow  
**Version**: SHYpn v2.4.6
