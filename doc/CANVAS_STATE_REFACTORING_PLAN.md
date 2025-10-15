# Canvas State Refactoring - Implementation Plan

**Project**: Centralized State Management Architecture  
**Status**: Planning Phase  
**Priority**: High (Critical Architecture Issue)  
**Estimated Duration**: 8-10 weeks  
**Start Date**: TBD  
**Owner**: TBD

---

## Executive Summary

### Problem Statement

The Shypn canvas state is **critically fragmented** across 4+ independent managers with massive duplication and no synchronization. This leads to:
- Data inconsistency bugs
- Incomplete file persistence
- UI components showing stale data
- Mode changes not propagating properly

### Solution

Implement a **centralized state management architecture** with:
1. Single `CanvasStateManager` as source of truth
2. Observer pattern for automatic UI updates
3. Complete state persistence (document + application + simulation)
4. Proper mode coordination (Edit ↔ Simulate)

### Benefits

- ✅ Eliminate synchronization bugs
- ✅ Complete file save/load (preserves all context)
- ✅ Automatic UI updates across all components
- ✅ Consistent mode transitions
- ✅ Easier testing and maintenance
- ✅ Foundation for undo/redo system

---

## Current State vs Target State

### Current Architecture (❌ Broken)

```
┌─────────────────────┐
│  DocumentModel      │  ← Places, Transitions, Arcs
│  view_state         │  ← Zoom, Pan (copy 1)
└─────────────────────┘

┌─────────────────────┐
│  ViewportState      │  ← Zoom, Pan (copy 2)
│  Grid settings      │
└─────────────────────┘

┌─────────────────────┐
│  DocumentState      │  ← Filename, Modified
└─────────────────────┘

┌─────────────────────┐
│ ModelCanvasManager  │  ← Places, Transitions, Arcs (DUPLICATE!)
│  zoom, pan_x, pan_y │  ← Zoom, Pan (copy 3!)
│  filename, modified │  ← Metadata (DUPLICATE!)
│  Selection, Tools   │
└─────────────────────┘

❌ NO SYNCHRONIZATION between them!
❌ THREE copies of zoom/pan state!
❌ TWO copies of object collections!
```

### Target Architecture (✅ Fixed)

```
┌──────────────────────────────────────────────────┐
│         CanvasStateManager (Single Source)       │
│  ┌────────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Document   │ │ Viewport │ │ Application  │  │
│  │ Model      │ │ State    │ │ State        │  │
│  │ (objects)  │ │ (view)   │ │ (mode, tool) │  │
│  └────────────┘ └──────────┘ └──────────────┘  │
│                                                  │
│  Observer Pattern → Notify all listeners        │
└──────────────────────────────────────────────────┘
        ↓            ↓            ↓
   ┌────────┐  ┌──────────┐  ┌──────────┐
   │ Canvas │  │  Right   │  │ Status   │
   │ Widget │  │  Panel   │  │   Bar    │
   └────────┘  └──────────┘  └──────────┘
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Goal**: Create core state infrastructure

**Tasks**:
1. **Create Base Classes** (3 days)
   - [ ] `CanvasStateManager` - Central coordinator
   - [ ] `StateChangeEvent` - Base event class
   - [ ] `StateObserver` - Observer interface
   - [ ] Event types: `ObjectAddedEvent`, `ObjectRemovedEvent`, `SelectionChangedEvent`, etc.

2. **State Consolidation Design** (2 days)
   - [ ] Define clean separation: Document / Viewport / Metadata / Application
   - [ ] Design state schema (JSON format)
   - [ ] Plan migration from current managers

3. **Testing Infrastructure** (2 days)
   - [ ] Unit test framework for state manager
   - [ ] Mock observers for testing
   - [ ] State serialization tests

4. **Documentation** (1 day)
   - [ ] API documentation for new classes
   - [ ] Migration guide for developers

**Deliverables**:
- ✅ `src/shypn/state/canvas_state_manager.py` (new)
- ✅ `src/shypn/state/events.py` (new)
- ✅ `src/shypn/state/observers.py` (new)
- ✅ `tests/test_canvas_state_manager.py` (new)
- ✅ `doc/STATE_MANAGER_API.md` (new)

**Success Criteria**:
- [ ] `CanvasStateManager` can store and retrieve all state
- [ ] Observer notifications work correctly
- [ ] All tests pass (>90% coverage)

---

### Phase 2: Migrate Document Model (Week 3-4)

**Goal**: Move object management to centralized state

**Tasks**:
1. **Remove Duplication** (3 days)
   - [ ] Keep `DocumentModel` as storage
   - [ ] Remove duplicate collections from `ModelCanvasManager`
   - [ ] Route all object operations through `CanvasStateManager`

2. **Update Object Operations** (3 days)
   - [ ] `add_place()` → triggers `ObjectAddedEvent`
   - [ ] `remove_place()` → triggers `ObjectRemovedEvent`
   - [ ] `add_transition()` → triggers event
   - [ ] `remove_transition()` → triggers event
   - [ ] `add_arc()` → triggers event
   - [ ] `remove_arc()` → triggers event

3. **Wire Canvas Loader** (2 days)
   - [ ] Update `model_canvas_loader.py` to use `CanvasStateManager`
   - [ ] Replace direct `manager.places.append()` with `state.add_place()`
   - [ ] Test object creation workflow

4. **Testing** (2 days)
   - [ ] Test object lifecycle (add, remove)
   - [ ] Test event notifications
   - [ ] Test object queries (at point, in rectangle)

**Deliverables**:
- ✅ Objects managed by single source
- ✅ No duplicate collections
- ✅ Events fired for all operations
- ✅ Canvas loader updated

**Success Criteria**:
- [ ] Only one copy of places/transitions/arcs
- [ ] All object operations fire events
- [ ] Canvas still renders correctly

---

### Phase 3: Migrate Viewport State (Week 5)

**Goal**: Consolidate zoom/pan state

**Tasks**:
1. **Eliminate Duplication** (2 days)
   - [ ] Keep `ViewportState` as storage
   - [ ] Remove `zoom/pan_x/pan_y` from `ModelCanvasManager`
   - [ ] Remove `view_state` from `DocumentModel`

2. **Update Zoom/Pan Operations** (2 days)
   - [ ] `set_zoom()` → triggers `ViewportChangedEvent`
   - [ ] `pan()` → triggers event
   - [ ] Coordinate transformations via `CanvasStateManager`

3. **Testing** (1 day)
   - [ ] Test zoom/pan operations
   - [ ] Test coordinate transformations
   - [ ] Test pointer-centered zoom

**Deliverables**:
- ✅ Single zoom/pan state
- ✅ Events for viewport changes
- ✅ Coordinate transforms work

**Success Criteria**:
- [ ] Only one copy of zoom/pan state
- [ ] Viewport operations fire events
- [ ] Zoom/pan work correctly in UI

---

### Phase 4: Observer Integration (Week 6)

**Goal**: Wire UI components as observers

**Tasks**:
1. **Status Bar Observer** (1 day)
   - [ ] Create `StatusBarObserver`
   - [ ] Show object count, zoom level, mode
   - [ ] Update on state changes

2. **Title Bar Observer** (1 day)
   - [ ] Create `TitleBarObserver`
   - [ ] Show filename with "*" for modified
   - [ ] Update on document changes

3. **Right Panel Observer** (2 days)
   - [ ] Create `RightPanelObserver`
   - [ ] Update diagnostics on object changes
   - [ ] Update plots on simulation data changes

4. **Canvas Redraw Observer** (1 day)
   - [ ] Create `CanvasRedrawObserver`
   - [ ] Trigger `queue_draw()` on any visual change
   - [ ] Optimize redraw frequency

5. **Testing** (1 day)
   - [ ] Test observer registration
   - [ ] Test notification delivery
   - [ ] Test multiple observers

**Deliverables**:
- ✅ 4+ observer implementations
- ✅ Automatic UI updates
- ✅ No manual refresh needed

**Success Criteria**:
- [ ] UI updates automatically on state changes
- [ ] Status bar shows current info
- [ ] Title bar shows modified state
- [ ] Right panel stays in sync

---

### Phase 5: Complete Persistence (Week 7)

**Goal**: Save/load complete application state

**Tasks**:
1. **Extend State Schema** (2 days)
   - [ ] Add `app_state` (mode, tool, selection)
   - [ ] Add `simulation_state` (if active)
   - [ ] Add `ui_state` (right panel config)
   - [ ] Add versioning and migration logic

2. **Update Serialization** (2 days)
   - [ ] Implement `ApplicationState.to_dict()`
   - [ ] Implement `SimulationState.to_dict()`
   - [ ] Implement `UIState.to_dict()`
   - [ ] Update `CanvasStateManager.save_to_file()`

3. **Update Deserialization** (2 days)
   - [ ] Implement `ApplicationState.from_dict()`
   - [ ] Implement version migration logic
   - [ ] Update `CanvasStateManager.load_from_file()`
   - [ ] Handle missing fields (backwards compatibility)

4. **Testing** (1 day)
   - [ ] Test save/load cycle
   - [ ] Test version migration
   - [ ] Test backwards compatibility

**Deliverables**:
- ✅ Complete state schema (v2.0)
- ✅ Full save/load support
- ✅ Version migration logic

**Success Criteria**:
- [ ] File save captures ALL state
- [ ] File load restores complete context
- [ ] Old files can still be opened

---

### Phase 6: Mode Coordination (Week 8)

**Goal**: Proper Edit ↔ Simulate mode management

**Tasks**:
1. **Create ModeCoordinator** (2 days)
   - [ ] `ModeCoordinator` class
   - [ ] Track current mode (edit/simulate)
   - [ ] Coordinate mode transitions
   - [ ] Fire `ModeChangedEvent`

2. **Wire Mode Listeners** (2 days)
   - [ ] Swiss Palette mode change → `ModeCoordinator`
   - [ ] Right panel switches tabs on mode change
   - [ ] Edit tools disabled in simulate mode
   - [ ] Visual feedback (cursor, colors)

3. **Update State Persistence** (1 day)
   - [ ] Save current mode to file
   - [ ] Restore mode on file load
   - [ ] Handle mode-specific state

4. **Testing** (2 days)
   - [ ] Test Edit → Simulate transition
   - [ ] Test Simulate → Edit transition
   - [ ] Test mode persistence
   - [ ] Test mode-specific operations

**Deliverables**:
- ✅ `ModeCoordinator` class
- ✅ Complete mode propagation
- ✅ Mode persisted in files

**Success Criteria**:
- [ ] Mode changes propagate to all components
- [ ] UI consistent across modes
- [ ] Invalid operations prevented
- [ ] Mode restored on file load

---

### Phase 7: Cleanup (Week 9)

**Goal**: Remove old code, optimize performance

**Tasks**:
1. **Remove Deprecated Code** (2 days)
   - [ ] Remove duplicate state from `ModelCanvasManager`
   - [ ] Remove `view_state` from `DocumentModel`
   - [ ] Clean up unused methods

2. **Refactor ModelCanvasManager** (2 days)
   - [ ] Focus on rendering only
   - [ ] Remove state management responsibilities
   - [ ] Use `CanvasStateManager` for all state access

3. **Performance Optimization** (2 days)
   - [ ] Batch observer notifications
   - [ ] Optimize redraw frequency
   - [ ] Profile state operations

4. **Documentation Update** (1 day)
   - [ ] Update architecture docs
   - [ ] Update code comments
   - [ ] Create migration guide for users

**Deliverables**:
- ✅ Clean codebase
- ✅ Optimized performance
- ✅ Updated documentation

**Success Criteria**:
- [ ] No duplicate state remains
- [ ] Performance equal or better
- [ ] All docs updated

---

### Phase 8: Testing & Validation (Week 10)

**Goal**: Comprehensive testing and bug fixes

**Tasks**:
1. **Integration Testing** (3 days)
   - [ ] Test complete workflows (create → edit → save → load)
   - [ ] Test mode transitions
   - [ ] Test file compatibility
   - [ ] Test observer system under load

2. **Regression Testing** (2 days)
   - [ ] Test all existing features still work
   - [ ] Test SBML import workflow
   - [ ] Test simulation workflow
   - [ ] Test force-directed layout

3. **Performance Testing** (1 day)
   - [ ] Profile state operations
   - [ ] Test with large models (1000+ objects)
   - [ ] Optimize bottlenecks

4. **Bug Fixes** (1 day)
   - [ ] Fix any issues found
   - [ ] Verify all test pass
   - [ ] Final review

**Deliverables**:
- ✅ All tests passing
- ✅ No regressions
- ✅ Performance validated

**Success Criteria**:
- [ ] >95% test coverage
- [ ] Zero critical bugs
- [ ] Performance acceptable
- [ ] Ready for merge

---

## Risk Management

### High Risk Items

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Breaking existing features | Critical | Comprehensive regression testing |
| Performance degradation | High | Profiling and optimization |
| Incomplete migration | Critical | Phased approach with validation |
| Synchronization bugs | High | Single source of truth enforced |

### Medium Risk Items

| Risk | Impact | Mitigation |
|------|--------|-----------|
| File format incompatibility | Medium | Version migration logic |
| Observer memory leaks | Medium | Proper unregistration |
| Event storm (too many notifications) | Medium | Batch notifications |

---

## Success Metrics

### Code Quality
- [ ] **Test Coverage**: >90% for new code
- [ ] **Code Review**: All code reviewed by 2+ developers
- [ ] **Documentation**: All public APIs documented

### Functionality
- [ ] **State Sync**: Zero synchronization bugs
- [ ] **Persistence**: Complete state save/load
- [ ] **Mode Management**: Proper Edit/Simulate transitions
- [ ] **UI Updates**: Automatic observer notifications

### Performance
- [ ] **State Operations**: <1ms for typical operations
- [ ] **Observer Notifications**: <5ms to notify all observers
- [ ] **File Load**: <2s for typical model
- [ ] **Memory**: No leaks, stable memory usage

---

## Dependencies & Prerequisites

### Technical Dependencies
- ✅ Python 3.x
- ✅ GTK3/PyGObject
- ✅ Existing codebase

### Team Dependencies
- [ ] 1-2 developers (full-time or part-time)
- [ ] Code reviewer
- [ ] QA tester

### Knowledge Requirements
- [ ] Understanding of observer pattern
- [ ] Familiarity with Shypn codebase
- [ ] GTK event system knowledge

---

## Rollback Plan

If critical issues arise:

### Phase 1-3 Rollback (Low Risk)
- New code can be disabled via feature flag
- Old code paths still functional
- Minimal disruption

### Phase 4-6 Rollback (Medium Risk)
- May need to revert commits
- Test data migration backwards
- Document rollback procedure

### Phase 7-8 Rollback (High Risk)
- Old code removed - harder to rollback
- Keep backup branch until validated
- Thorough testing before Phase 7

---

## Communication Plan

### Weekly Updates
- **Monday**: Sprint planning, task assignment
- **Wednesday**: Progress check-in
- **Friday**: Weekly summary, demo

### Deliverables
- **End of Phase**: Demo to stakeholders
- **Milestone Complete**: Architecture review
- **Project Complete**: Final presentation

---

## Post-Implementation

### After Refactoring Complete

**New Capabilities Unlocked**:
1. **Undo/Redo System** - Observer events provide operation log
2. **Real-time Collaboration** - State sync via websockets
3. **Plugins/Extensions** - Observers allow third-party extensions
4. **State Inspection Tools** - Debug and profile state changes
5. **Automated Testing** - Mock observers for testing

**Technical Debt Eliminated**:
- ✅ State duplication removed
- ✅ Synchronization bugs fixed
- ✅ Complete persistence implemented
- ✅ Clean architecture established

---

## Quick Reference

### Key Files to Create
```
src/shypn/state/
├── __init__.py
├── canvas_state_manager.py      # Central state manager
├── events.py                      # Event classes
├── observers.py                   # Observer interfaces
└── mode_coordinator.py            # Mode management

tests/state/
├── test_canvas_state_manager.py
├── test_observers.py
└── test_mode_coordinator.py

doc/
├── STATE_MANAGER_API.md           # API documentation
└── STATE_MIGRATION_GUIDE.md       # Developer guide
```

### Key Classes to Modify
```
src/shypn/data/model_canvas_manager.py   # Simplify to render-only
src/shypn/helpers/model_canvas_loader.py # Use CanvasStateManager
src/shypn/file/persistency_manager.py    # Extend save/load
src/shypn/helpers/right_panel_loader.py  # Add observer
```

### Key Concepts
- **Single Source of Truth**: `CanvasStateManager` owns all state
- **Observer Pattern**: Components listen for state changes
- **Event-Driven**: All state changes fire events
- **Complete Persistence**: Save ALL state, not just objects
- **Mode Coordination**: Centralized mode management

---

**Document Status**: Implementation Plan Complete  
**Next Steps**: Review plan with team, assign tasks, begin Phase 1  
**Owner**: TBD  
**Date**: October 14, 2025
