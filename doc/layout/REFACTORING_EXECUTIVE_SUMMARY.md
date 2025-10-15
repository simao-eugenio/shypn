# Pipeline Refactoring: Executive Summary

**Date**: October 14, 2025  
**Status**: Planning Complete - Ready for Implementation  
**Impact**: Major Simplification (75% code reduction)

---

## The Plan in 3 Minutes

### What We're Doing

**Replacing** the complex OLD SBML import pipeline with a **streamlined NEW flow**:

```
OLD:  Fetch → Parse → [5 layout algorithms] → Import
NEW:  Fetch → Parse → Import → Force-Directed (user-initiated)
```

### Why

The current pipeline has accumulated complexity over time:
- 5+ layout algorithms (hierarchical, grid, force-directed, spiral, tree)
- Multiple coordinate transformations (physics → projection → canvas)
- Auto-selection logic that's hard to debug
- Node ID collisions (recently fixed)
- ~2000 lines of code across 11 files

**Problem**: Hard to maintain, test, and understand

**Solution**: Keep ONLY the proven force-directed layout with user-configurable parameters

### Impact

| Metric | OLD | NEW | Change |
|--------|-----|-----|--------|
| Layout Algorithms | 5+ | 1 | **-80%** |
| Files | 11 | 7 | **-36%** |
| Lines of Code | ~2000 | ~500 | **-75%** |
| User Control | Low (auto) | High (parameters) | ✅ |
| Node ID Bugs | Fixed (v1.0.0) | Fixed | ✅ |

---

## The New Flow

### Step-by-Step

**STEP 1: Fetch** (unchanged)
- User selects local file OR enters BioModels ID
- File downloaded if from BioModels API

**STEP 2: Parse** (simplified)
- Parse SBML → PathwayData
- Validate structure
- Assign **arbitrary positions** (force-directed will recalculate)
- Convert to Petri net (places, transitions, arcs)
- **Load to canvas immediately** (new tab)

**STEP 3: Force-Directed Layout** (user-initiated)
- User clicks **Swiss Palette → Layout → Force-Directed**
- System reads parameters from **SBML tab UI spinners**:
  - Iterations (50-1000)
  - K multiplier (0.5-3.0) - spacing control
  - Scale (500-5000) - canvas size
- Physics simulation runs (NetworkX spring_layout)
- Positions applied **directly** to canvas objects
- Canvas redraws with new layout

### Key Changes

1. **No auto-layout** - User controls when and with what parameters
2. **Single algorithm** - Force-directed only (proven to work)
3. **Direct positions** - No coordinate transformations
4. **Object-based IDs** - No collisions (uses Python object references)

---

## What Gets Removed

### Legacy Files to Delete

1. `src/shypn/data/pathway/hierarchical_layout.py` - Hierarchical algorithm
2. `src/shypn/data/pathway/tree_layout.py` - Tree-based aperture angles  
3. `src/shypn/data/pathway/layout_projector.py` - Spiral/layered projection
4. `src/shypn/data/pathway/sbml_layout_resolver.py` - Cross-reference coords

**Total**: 4 files, ~1500 lines removed

### Legacy Features Removed

- ❌ Hierarchical layout (top-to-bottom flow)
- ❌ Grid layout fallback
- ❌ Spiral projection (entry at center)
- ❌ Layered projection (horizontal layers)
- ❌ Cross-reference coordinates (KEGG/Reactome API)
- ❌ Auto-layout on Import button
- ❌ Curved arc auto-conversion

---

## What Stays

### Core Components (Unchanged)

- ✅ SBML parsing (`sbml_parser.py`)
- ✅ Pathway validation (`pathway_validator.py`)
- ✅ Data structures (`pathway_data.py`)
- ✅ Color assignment (compartment-based)
- ✅ Unit normalization (concentration → tokens)
- ✅ Name resolution (ID → readable name)

### New Components (v1.0.0 - Already Working)

- ✅ Force-directed layout (`force_directed.py`)
- ✅ Layout engine (`engine.py`)
- ✅ Swiss Palette integration (`model_canvas_loader.py`)
- ✅ UI parameter controls (SBML tab spinners)
- ✅ Object-based node IDs (collision-free)
- ✅ Arc weights (stoichiometry-based springs)

---

## Benefits

### For Users

- **Control**: Adjust layout parameters (iterations, spacing, canvas size)
- **Predictability**: Same parameters → same layout (reproducible)
- **Speed**: No trying multiple algorithms, direct to result
- **Clarity**: Visible workflow (Parse → Load → Layout)

### For Developers

- **Simplicity**: 1 algorithm to maintain instead of 5+
- **Testability**: Clear input/output, no branching logic
- **Debuggability**: Single code path, easy to trace
- **Maintainability**: 75% less code, 36% fewer files

### Technical

- **No ID Collisions**: Object references as node IDs (fixed in v1.0.0)
- **No Coordinate Corruption**: Direct position assignment (no transformations)
- **Universal Repulsion**: All nodes repel (Graph instead of DiGraph)
- **Parameter Flow**: UI spinners → Swiss Palette → Layout engine

---

## Migration Path

### For Existing Workflows

**Old way** (current):
```
1. Open SBML file
2. Click Parse
3. Click Import (auto-layout)
4. Edit manually if needed
```

**New way** (after refactoring):
```
1. Open SBML file
2. Click Parse (loads to canvas)
3. Swiss Palette → Force-Directed (apply layout)
4. Adjust parameters in SBML tab if needed, re-apply
```

### Transition Strategy

1. **Create backup branch** (`backup/old-pipeline`) - preserve old code
2. **Provide migration docs** - explain workflow changes
3. **Add release notes** - breaking changes clearly documented
4. **Keep examples** - BIOMD0000000061 tested and documented

---

## Timeline

| Phase | Description | Time | Status |
|-------|-------------|------|--------|
| **Phase 1** | Documentation (this) | 2h | ✅ Complete |
| **Phase 2** | Code refactoring | 6-8h | ⏳ Ready |
| **Phase 3** | Testing | 4-6h | ⏳ Pending |
| **Phase 4** | Docs update | 2-3h | ⏳ Pending |
| **Phase 5** | Release (v2.0.0) | 1h | ⏳ Pending |
| **Total** | | **15-20h** | |

---

## Risk Assessment

### Low Risk ✅
- Force-directed already proven (v1.0.0-force-directed-layout)
- Object-based IDs tested (no collisions)
- Parameter flow verified (SBML tab → Swiss Palette)
- User controls layout (not automatic)

### Medium Risk ⚠️
- Users expect auto-layout on import (need clear docs)
- Breaking changes require migration guide
- Some users may prefer old hierarchical layout (force-directed is better!)

### High Risk 🔴
- None identified (all components already verified)

### Mitigation
- Keep old pipeline in backup branch
- Provide detailed migration guide
- Add examples in documentation
- Tag release with clear breaking changes list

---

## Success Criteria

### Code Quality
- [x] Force-directed layout working (v1.0.0 ✅)
- [ ] <500 lines total (down from ~2000)
- [ ] Single layout algorithm (force-directed only)
- [ ] All tests passing

### Functionality
- [x] Parse SBML to canvas (v1.0.0 ✅)
- [x] Swiss Palette force-directed works (v1.0.0 ✅)
- [x] Parameters flow from UI (v1.0.0 ✅)
- [ ] No auto-layout (user-initiated only)

### Documentation
- [x] Refactoring plan complete ✅
- [x] Comparison document complete ✅
- [ ] Migration guide written
- [ ] API docs updated
- [ ] Release notes published

---

## Approval Required

**Before proceeding to Phase 2 (Code Refactoring), we need approval on**:

1. ✅ Removing 4 legacy layout files (hierarchical, tree, projector, resolver)
2. ✅ Removing Import button (Parse loads directly to canvas)
3. ✅ Breaking change to workflow (no auto-layout)
4. ✅ Single algorithm approach (force-directed only)

**If approved**, we proceed to Phase 2: Code Refactoring

**If concerns**, we discuss alternatives or adjustments

---

## Related Documents

- **Full Plan**: `doc/layout/PIPELINE_REFACTORING_PLAN.md` (detailed technical plan)
- **Comparison**: `doc/layout/PIPELINE_COMPARISON.md` (OLD vs NEW side-by-side)
- **Force-Directed**: `doc/layout/FORCE_DIRECTED_LAYOUT_COMPLETE.md` (v1.0.0 implementation)
- **Swiss Palette**: `doc/layout/SWISS_PALETTE_SBML_PARAMETER_INTEGRATION.md` (integration details)

---

## Next Steps

1. **Review this summary** - Get stakeholder sign-off
2. **Create backup branch** - `git checkout -b backup/old-pipeline`
3. **Start Phase 2** - Rewrite PathwayPostProcessor (minimal version)
4. **Update todo list** - Track refactoring progress
5. **Test continuously** - Verify each change doesn't break existing workflows

---

**Decision Point**: Ready to proceed with refactoring? (Yes/No/Discuss)

---

**Document Status**: Executive Summary - Complete  
**Last Updated**: October 14, 2025  
**Approval Status**: Pending  
**Next Action**: Await stakeholder approval to proceed to Phase 2
