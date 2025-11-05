# ID Generation Issues - Investigation Summary

**Date:** November 5, 2025  
**Status:** CRITICAL - Needs comprehensive fix tomorrow

## Issues Discovered Today

### 1. ✅ FIXED: DocumentController Interactive Creation
**Problem:** `DocumentController.add_place/transition/arc()` was creating objects with numeric IDs instead of prefixed strings.
- Created place with ID `151` instead of `"P151"`
- **Fix:** Changed to use `id_manager.generate_*_id()` methods
- **Commit:** 85c92bc, 961fcaa

### 2. ✅ FIXED: DocumentModel Programmatic Creation  
**Problem:** `DocumentModel.create_place/transition/arc()` was also using numeric IDs.
- **Fix:** Changed to generate string IDs with prefix `f"P{self._next_place_id}"`
- **Commit:** bf999b4 (previous session)

### 3. ⚠️ PARTIALLY FIXED: Simulation Engine Lookup
**Problem:** `_get_place()` method had multiple issues:
- Originally assumed dict storage, but model uses list storage
- Then assumed dict storage from ModelAdapter (which IS correct)
- Added fallback logic for inconsistent ID formats
- **Current State:** Has workarounds but underlying issue remains
- **Commits:** 9581cee, 368ce8d, fc247ed

### 4. 🔴 SEVERE ISSUE IDENTIFIED - NOT FULLY RESOLVED

User reports: "there are a severe issue on IDs generation"

## Suspected Root Causes

### A. Multiple ID Generation Paths
Even after centralization, there may be paths that bypass IDManager:
1. **DocumentController** → Now uses IDManager ✅
2. **DocumentModel** → Has its own separate IDManager instance ⚠️
3. **KEGG Import** → May have direct ID creation ❓
4. **SBML Import** → May have direct ID creation ❓
5. **Copy/Paste** → Unknown ❓
6. **Undo/Redo** → Unknown ❓

### B. ID Counter Synchronization
**Problem:** DocumentController has ONE IDManager, but DocumentModel might have ANOTHER.
- When loading a model, counters need to be synchronized
- When importing, who owns the IDManager?
- Counter registration from existing objects may be incomplete

### C. ID Format Inconsistencies Still Present
Despite fixes, user reports issues with:
- T3, T4 working in simulation
- P101 working  
- Place '151' exists without prefix in live model

**This suggests:**
- Old objects with wrong IDs still in model files
- OR new objects still being created with wrong format through some path
- OR counter sync issues causing ID collisions

## Architecture Issues

### Current Architecture (Problematic)
```
DocumentController (has IDManager #1)
    ├─ add_place() → IDManager #1
    └─ add_transition() → IDManager #1

DocumentModel (has IDManager #2?)
    ├─ create_place() → Direct string formatting
    └─ create_transition() → Direct string formatting

ModelCanvasManager
    ├─ Delegates to DocumentController
    └─ Has properties that access counters
```

### Potential Issues
1. **Two sources of truth:** DocumentController.id_manager vs DocumentModel counters
2. **Counter sync:** When loading model, both need same counter values
3. **Import workflows:** Which IDManager do they use?
4. **Interactive vs Programmatic:** Different code paths might diverge

## What Needs Investigation Tomorrow

### 1. Audit ALL ID Creation Sites
Search for:
- `Place(` - where Place objects are constructed
- `Transition(` - where Transition objects are constructed  
- `Arc(` - where Arc objects are constructed
- Check if ID parameter is always prefixed string

### 2. Check DocumentModel ID Generation
- Does it have its own IDManager?
- Is it synchronized with DocumentController's IDManager?
- When loading a model, are both updated?

### 3. Verify Import Workflows
- KEGG import: Where do IDs come from?
- SBML import: Where do IDs come from?
- Do they use DocumentModel.create_*() or DocumentController.add_*()?

### 4. Check Counter Registration Logic
File: `model_canvas_manager.py` lines 605-650
- Extracts numeric IDs from existing objects
- Updates counters to avoid collisions
- Does this work correctly with prefixed string IDs?
- Is it called at the right time?

### 5. Test ID Normalization
- Are all existing model files using correct format?
- Do we need a migration script?
- Should `_get_place()` fallbacks be permanent or temporary?

## Questions for Tomorrow

1. **Should there be ONE global IDManager?**
   - Shared between DocumentController and DocumentModel?
   - Or should DocumentModel not generate IDs at all?

2. **Who is responsible for ID generation during import?**
   - Should imports use DocumentController.add_*() (interactive path)?
   - Or DocumentModel.create_*() (programmatic path)?
   - Or call IDManager directly?

3. **Should we enforce ID validation?**
   - Reject objects with non-prefixed IDs?
   - Auto-normalize on construction?
   - Validate in Place/Transition/Arc constructors?

4. **Migration strategy?**
   - Script to fix existing .shy files?
   - Runtime normalization on load?
   - Backward compatibility layer?

## Current Workarounds in Place

1. **_get_place() fallbacks** - Handles mixed ID formats during simulation
2. **IDManager.normalize_*_id()** - Can convert any format to standard
3. **IDManager.extract_numeric_id()** - Extracts number from any format
4. **Counter registration** - Updates counters from existing IDs

These are safety nets but don't fix the root cause.

## Success Criteria for Tomorrow

- [ ] All new objects created with correct format ("P1", "T1", "A1")
- [ ] No numeric-only IDs (151, 35, etc.) created anywhere
- [ ] Single source of truth for ID generation
- [ ] Counter synchronization verified and working
- [ ] All import workflows use correct IDs
- [ ] User can create interactive place and verify correct ID
- [ ] Simulation works without needing fallback logic
- [ ] Documentation of ID generation architecture

## Files to Review Tomorrow

1. `src/shypn/core/controllers/document_controller.py` - Interactive creation ✅ Fixed
2. `src/shypn/data/canvas/document_model.py` - Programmatic creation ⚠️ Check
3. `src/shypn/data/model_canvas_manager.py` - Counter sync logic ⚠️ Check
4. `src/shypn/data/canvas/id_manager.py` - Central manager ✅ Good
5. `src/shypn/importer/kegg/*.py` - KEGG import paths ❓ Unknown
6. `src/shypn/importer/sbml/*.py` - SBML import paths ❓ Unknown
7. `src/shypn/netobjs/*.py` - Object constructors ❓ Check
8. `src/shypn/engine/transition_behavior.py` - Lookup fallbacks ⚠️ Workaround

## Test Plan for Tomorrow

1. Start fresh app
2. Create Interactive project
3. Add place interactively → Check ID format
4. Import KEGG model → Check all IDs in resulting objects
5. Run simulation → Verify no fallback needed
6. Save and reload → Verify IDs persist correctly
7. Check all places, transitions, arcs have prefixed IDs

---

**Note:** This is a critical architectural issue affecting model integrity and simulation correctness. Needs thorough investigation and comprehensive fix, not just patches.
