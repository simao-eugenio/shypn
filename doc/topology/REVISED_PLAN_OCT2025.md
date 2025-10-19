# Topology System - Revised Plan (October 2025)

**Date**: October 19, 2025  
**Status**: Phases 1-4 Complete, Ready for Next Phase  
**Branch**: feature/property-dialogs-and-simulation-palette  

---

## 🔄 Key Revisions

### 1. Layout/SSCC Removal ❌
**Decision**: Remove Layout/SSCC from topology plan - it's incomplete and unfinished.

**Rationale**:
- `src/shypn/layout/sscc/` module is under development
- Not stable enough for integration
- Focus on pure topology analyzers instead

**Action**: Remove all references to wrapping SCC detector from plan.

---

### 2. Property Categories Reorganization 🔀

**OLD Structure** (4 categories):
1. Structural Analysis
2. Graph Topology  
3. Behavioral Analysis
4. Network Analysis

**NEW Structure** (2 main categories):

#### **Category A: Static Topology Properties** 📊
Properties that can be computed from network structure alone (no simulation needed).

**Subcategories**:
- **A1: Structural** - P-Invariants, T-Invariants, Siphons, Traps
- **A2: Graph** - Cycles, Paths, DAG Analysis, Connectivity
- **A3: Network** - Hubs, Centrality, Communities, Clustering

#### **Category B: Dynamic Behavior Properties** ⚡
Properties that require simulation or state space exploration.

**Subcategories**:
- **B1: State Space** - Reachability, Boundedness, Coverability
- **B2: Liveness** - Liveness analysis, Deadlock detection
- **B3: Performance** - Throughput, Response time, Bottlenecks

**Key Distinction**:
- **Static** → Computed once from structure → Display in **Property Dialogs**
- **Dynamic** → Require simulation data → Display in **Runtime Analysis Panel**

---

### 3. Property Dialogs Status 🏗️

**Current State**: Under Development (NOT complete)

**What's Done** ✅:
- UI architecture (clean XML/Python separation)
- Topology tab infrastructure in all 3 dialogs
- 4 static analyzers (Cycles, P-Invariants, Paths, Hubs)

**What's NOT Done** ⚠️:
- Remaining static analyzers (T-Invariants, Siphons, Traps, etc.)
- Final UI polish and layout
- Integration testing with real biochemical models
- User documentation

**Action Items**:
1. Complete all static analyzers (Category A)
2. Populate topology tabs with all static properties
3. Test with biochemical models (glycolysis, TCA, etc.)
4. Polish UI and user experience
5. Write user documentation

**Estimated Time**: 2-3 weeks

---

### 4. Runtime Analysis Panel (New Component) 🆕

**Purpose**: Display dynamic properties during/after simulation

**Pattern**: Attach/Detach/Float (like existing panels in system)

**Existing Examples in Shypn**:
- `RightPanelLoader` - Right analysis panel (attach/detach)
- `AnalysisPlotPanel` - Base class for plot panels
- `PlaceRatePanel`, `TransitionRatePanel` - Rate analysis panels

**Architecture**:
```
Main Window
├── Left Panel (Model Tree)         [existing]
├── Canvas (Petri Net)               [existing]
├── Right Panel                      [existing]
│   ├── Place Analysis Tab           [existing]
│   ├── Transition Analysis Tab      [existing]
│   └── Runtime Dynamics Tab         [NEW - Category B properties]
└── Floating Palettes
    ├── Simulate Palette             [existing]
    ├── SwissKnife Palette           [existing]
    └── Topology Tools Palette       [planned - Phase 6]
```

**New Runtime Dynamics Tab**:
```
╔═══════════════════════════════════════════════╗
║  Runtime Dynamics                             ║
╠═══════════════════════════════════════════════╣
║                                               ║
║  State Space                                  ║
║  ├─ Reachable markings: 1,247                ║
║  ├─ State space size: 2.4 MB                 ║
║  └─ [Visualize State Graph]                  ║
║                                               ║
║  Boundedness                                  ║
║  ├─ All places bounded: YES                  ║
║  ├─ Max tokens (P1): 15                      ║
║  └─ Unbounded places: None                   ║
║                                               ║
║  Liveness                                     ║
║  ├─ Live transitions: 8/10                   ║
║  ├─ Dead transitions: T5, T7                 ║
║  └─ [Show Details]                           ║
║                                               ║
║  Deadlocks                                    ║
║  ├─ Deadlock-free: NO                        ║
║  ├─ Deadlock states found: 3                 ║
║  └─ [Highlight Deadlocks]                    ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

**Implementation**:
- Create `src/shypn/analyses/runtime_dynamics_panel.py`
- Integrate into `RightPanelLoader`
- Add new tab to right panel notebook
- Connect to simulation data collector

**Estimated Time**: 1-2 weeks

---

### 5. Topology Tools Palette - Biochemist Requirements 🔬

**Question**: What tools do biochemists need during **creation/simulation**?

**Use Cases**:

#### A. During Model Creation 🏗️
**Goal**: Validate network structure before simulation

**Tools Needed**:
1. **P-Invariants** - Check mass conservation (C6H12O6 balance)
2. **T-Invariants** - Verify reproducible pathways
3. **Cycles** - Detect feedback loops (product inhibition)
4. **Siphons/Traps** - Find potential deadlocks in resource pools
5. **Connectivity** - Ensure pathways are connected
6. **Hub Detection** - Identify central metabolites (ATP, NAD+)

**Workflow**:
```
Create Network → Run Static Analysis → Fix Issues → Save Model
```

**UI Integration**:
- Show in **Property Dialogs** (per-element view)
- Show in **Topology Tools Palette** (global view)

#### B. During Simulation ⚡
**Goal**: Understand system behavior in real-time

**Tools Needed**:
1. **Liveness** - Check if reactions are active
2. **Deadlock Detection** - Find stuck states
3. **Boundedness** - Monitor metabolite accumulation
4. **Bottleneck Analysis** - Find rate-limiting steps
5. **Reachability** - Explore state space

**Workflow**:
```
Run Simulation → Monitor Dynamics → Identify Issues → Adjust Parameters
```

**UI Integration**:
- Show in **Runtime Dynamics Panel** (right panel)
- Highlight issues on **Canvas**
- Pause simulation to inspect

#### C. Post-Simulation Analysis 📊
**Goal**: Analyze simulation results

**Tools Needed**:
1. **State Space Graph** - Visualize reachable states
2. **Transition Statistics** - Firing frequencies
3. **Place Statistics** - Token distributions
4. **Critical Path Analysis** - Main metabolic routes
5. **Sensitivity Analysis** - Parameter effects

**Workflow**:
```
Simulation Complete → Analyze Results → Export Data → Report
```

**UI Integration**:
- Show in **Runtime Dynamics Panel**
- Export to CSV/JSON
- Generate plots

---

### 6. Highlighting Infrastructure 🎨

**Current State**: Infrastructure exists but not implemented

**What Exists** ✅:
- `HighlightingManager` class skeleton
- Canvas overlay system
- Color palette definitions

**What's Needed** ⚠️:
- Implement highlighting methods:
  - `highlight_cycle(nodes, color='blue')`
  - `highlight_path(nodes, color='green')`
  - `highlight_hubs(nodes, color='red')`
  - `highlight_invariant(places, color='yellow')`
  - `clear_highlights()`

**Where to Plug Highlighting**:

#### Option 1: Property Dialogs (Per-Element)
```python
# In topology tab loader
def _on_highlight_cycle_clicked(self, button):
    """User clicked "Highlight" button in dialog."""
    cycle_nodes = self.current_cycle['nodes']
    self.highlighting_manager.highlight_cycle(cycle_nodes)
```

**Use Case**: Highlight this specific place's cycles

#### Option 2: Topology Tools Palette (Global)
```python
# In palette button handler
def _on_show_all_cycles_clicked(self, button):
    """User clicked "Show All Cycles" in palette."""
    all_cycles = self.cycle_analyzer.analyze()
    for cycle in all_cycles:
        self.highlighting_manager.highlight_cycle(
            cycle['nodes'], 
            color=self._get_cycle_color(cycle)
        )
```

**Use Case**: Highlight all cycles in the network

#### Option 3: Runtime Panel (Dynamic)
```python
# During simulation
def _on_deadlock_detected(self, marking):
    """Simulation detected a deadlock."""
    # Highlight the stuck places
    stuck_places = self._find_stuck_places(marking)
    self.highlighting_manager.highlight_deadlock(stuck_places)
```

**Use Case**: Highlight problematic states during simulation

**Implementation Strategy**:
1. Implement `HighlightingManager` methods (Phase 5)
2. Integrate into Property Dialogs (Phase 5)
3. Add to Topology Tools Palette (Phase 6)
4. Add to Runtime Panel (Phase 7)

**Estimated Time**: 1 week for basic implementation

---

## 📋 Revised Implementation Roadmap

### Phase 5: Complete Static Analyzers ⏳ (Current Priority)

**Duration**: 2-3 weeks

**Tasks**:
1. Implement remaining Category A analyzers:
   - T-Invariants (4-6h)
   - Siphons (6-8h)
   - Traps (4-6h)
   - DAG Analysis (3-4h)
   - Centrality (6-8h)
   - Communities (6-8h)
   - Clustering (3-4h)

2. Complete Property Dialogs:
   - Populate all topology tabs
   - Polish UI layout
   - Add "Highlight" buttons
   - Test with real models

3. Documentation:
   - User guide for each analyzer
   - Biochemical examples
   - API documentation

**Deliverable**: ✅ Property Dialogs Complete with All Static Properties

---

### Phase 6: Canvas Highlighting 🎨

**Duration**: 1 week

**Tasks**:
1. Implement `HighlightingManager`:
   - `highlight_cycle()` - Blue outline
   - `highlight_path()` - Green arrows
   - `highlight_invariant()` - Yellow fill
   - `highlight_hubs()` - Red star
   - `clear_highlights()` - Remove all

2. Integrate into Property Dialogs:
   - Add "Highlight" button to each section
   - Click → highlight on canvas
   - Auto-clear on dialog close

3. Test highlighting:
   - Multiple cycles simultaneously
   - Overlapping paths
   - Performance with large networks

**Deliverable**: ✅ Visual Highlighting from Property Dialogs

---

### Phase 7: Runtime Dynamics Panel 🆕

**Duration**: 2 weeks

**Tasks**:
1. Create `RuntimeDynamicsPanel`:
   - New tab in right panel
   - Attach/detach/float support
   - Live updates during simulation

2. Implement Category B analyzers:
   - Reachability (10-12h)
   - Boundedness (8-10h)
   - Liveness (8-10h)
   - Deadlock Detection (6-8h)

3. Connect to simulation:
   - Listen to simulation events
   - Update panel in real-time
   - Highlight issues on canvas

4. Add controls:
   - Pause/resume analysis
   - Export results
   - Configure thresholds

**Deliverable**: ✅ Runtime Analysis Panel with Dynamic Properties

---

### Phase 8: Topology Tools Palette 🎨

**Duration**: 2-3 weeks

**Tasks**:
1. Design palette UI:
   - Button layout
   - Grouping (Static vs Dynamic)
   - Icons and labels

2. Implement palette:
   - Create `TopologyToolsPalette` class
   - Add buttons for all tools
   - Connect to analyzers

3. Global analysis:
   - Run analyzer on whole network
   - Display results in floating window
   - Highlight on canvas

4. Integration:
   - Add to main window
   - Coordinate with other palettes
   - Keyboard shortcuts

**Deliverable**: ✅ Topology Tools Palette (like SwissKnife)

---

## 📊 Property Distribution

### Category A: Static Topology (Property Dialogs)

| Subcategory | Tools | Status | Display Location |
|-------------|-------|--------|------------------|
| **A1: Structural** | P-Invariants, T-Invariants, Siphons, Traps | 1/4 done | Property Dialogs → Topology Tab |
| **A2: Graph** | Cycles, Paths, DAG, Connectivity | 2/4 done | Property Dialogs → Topology Tab |
| **A3: Network** | Hubs, Centrality, Communities, Clustering | 1/4 done | Property Dialogs → Topology Tab |
| **TOTAL** | **12 tools** | **4/12 (33%)** | **Property Dialogs** |

### Category B: Dynamic Behavior (Runtime Panel)

| Subcategory | Tools | Status | Display Location |
|-------------|-------|--------|------------------|
| **B1: State Space** | Reachability, Boundedness, Coverability | 0/3 done | Right Panel → Runtime Dynamics Tab |
| **B2: Liveness** | Liveness, Deadlock Detection | 0/2 done | Right Panel → Runtime Dynamics Tab |
| **B3: Performance** | Throughput, Response Time, Bottlenecks | 0/3 done | Right Panel → Runtime Dynamics Tab |
| **TOTAL** | **8 tools** | **0/8 (0%)** | **Runtime Panel** |

### Overall Progress

- **Static Tools**: 4/12 complete (33%)
- **Dynamic Tools**: 0/8 complete (0%)
- **Total**: 4/20 complete (20%)

---

## 🏗️ Architecture Summary

### Component Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                      Main Window                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Left Panel │  │     Canvas      │  │  Right Panel    │  │
│  │            │  │                 │  │                 │  │
│  │ Model Tree │  │  Petri Net      │  │  ┌─────────────┤  │
│  │            │  │  Display        │  │  │ Place Tab   │  │
│  │            │  │                 │  │  ├─────────────┤  │
│  │            │  │  [Highlighting] │  │  │ Trans Tab   │  │
│  │            │  │                 │  │  ├─────────────┤  │
│  │            │  │                 │  │  │ Runtime Tab │  │ ← NEW
│  │            │  │                 │  │  │ [Dynamic]   │  │
│  └────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘

        Property Dialogs                  Floating Palettes
┌───────────────────────────┐    ┌──────────────────────────┐
│ Place Properties          │    │ Simulate Palette         │
├───────────────────────────┤    ├──────────────────────────┤
│ ┌─────────────────────┐   │    │ Play/Pause/Step/Reset    │
│ │ Basic    │ Topology │   │    └──────────────────────────┘
│ ├──────────┴──────────┤   │
│ │ [Static Properties] │   │    ┌──────────────────────────┐
│ │ Cycles: 3           │   │    │ SwissKnife Palette       │
│ │ P-Inv: 2            │   │    ├──────────────────────────┤
│ │ Hubs: Yes           │   │    │ Layout/Edit/Debug Tools  │
│ │ [Highlight] buttons │   │    └──────────────────────────┘
│ └─────────────────────┘   │
└───────────────────────────┘    ┌──────────────────────────┐
                                 │ Topology Tools Palette   │ ← NEW
                                 ├──────────────────────────┤
                                 │ Global Analysis Tools    │
                                 │ Static + Dynamic         │
                                 └──────────────────────────┘
```

### Data Flow

```
Model (Petri Net)
      │
      ├──→ Static Analyzers (Category A)
      │         │
      │         ├──→ Property Dialogs (Topology Tab)
      │         └──→ Topology Tools Palette (Global View)
      │
      └──→ Simulation Engine
                │
                └──→ Dynamic Analyzers (Category B)
                          │
                          ├──→ Runtime Dynamics Panel (Right Panel)
                          ├──→ Topology Tools Palette (Live Updates)
                          └──→ Canvas Highlighting
```

---

## 🎯 Success Criteria

### Phase 5 Complete When:
- [ ] All 12 static analyzers implemented
- [ ] Property dialogs show all static properties
- [ ] Tests passing (80%+ coverage)
- [ ] Documentation complete
- [ ] Tested with real biochemical models

### Phase 6 Complete When:
- [ ] `HighlightingManager` fully implemented
- [ ] Highlighting works from property dialogs
- [ ] Multiple highlights can coexist
- [ ] Performance is acceptable (<100ms to highlight)
- [ ] Clear visual distinction between types

### Phase 7 Complete When:
- [ ] Runtime Dynamics Panel exists in right panel
- [ ] All 8 dynamic analyzers implemented
- [ ] Real-time updates during simulation
- [ ] Canvas highlighting for dynamic issues
- [ ] Export functionality working

### Phase 8 Complete When:
- [ ] Topology Tools Palette implemented
- [ ] Global analysis for all 20 tools
- [ ] Palette integrates with existing UI
- [ ] Keyboard shortcuts working
- [ ] User documentation complete

---

## 📚 Key Documents

### Planning Documents
- `doc/topology/REVISED_PLAN_OCT2025.md` ← **This document**
- `doc/topology/PHASES_1_TO_4_COMPLETE.md` - What's done
- `doc/TOPOLOGY_TOOLS_PALETTE_PLAN.md` - Original full spec

### Implementation Guides
- `doc/topology/QUICK_RESUME_GUIDE.md` - How to implement new analyzer
- `doc/topology/IMPLEMENTATION_PLAN_OPTION_A.md` - Detailed technical plan

### Status Documents
- `doc/topology/CURRENT_STATUS.md` - Current progress
- `doc/topology/PHASE*_COMPLETE.md` - Phase completion docs

---

## 🚀 Next Actions (This Week)

### Immediate Priorities

1. **Review and Approve Plan** (1 hour)
   - Review this revised plan
   - Confirm scope and priorities
   - Approve next steps

2. **Implement T-Invariants** (4-6 hours)
   - Copy `p_invariants.py` template
   - Change algorithm (null space of C, not C^T)
   - Add tests
   - Integrate into topology tabs

3. **Implement Siphons** (6-8 hours)
   - Graph search algorithm
   - Find minimal siphons
   - Add tests
   - Integrate into topology tabs

4. **Test with Real Models** (2-3 hours)
   - Load glycolysis model
   - Load TCA cycle model
   - Verify all analyzers work
   - Document any issues

### Weekly Goals

- **Week 1**: T-Invariants, Siphons, Traps
- **Week 2**: DAG, Centrality, Communities, Clustering
- **Week 3**: Complete property dialogs, polish UI

---

## 📊 Metrics

### Current Status
- **Analyzers**: 4/20 (20%)
- **Property Dialogs**: 70% (UI done, need all analyzers)
- **Runtime Panel**: 0% (not started)
- **Highlighting**: 20% (infrastructure only)
- **Palette**: 0% (not started)

### Estimated Completion
- **Phase 5** (Static Analyzers): End of Week 3
- **Phase 6** (Highlighting): End of Week 4
- **Phase 7** (Runtime Panel): End of Week 6
- **Phase 8** (Palette): End of Week 9

**Total Estimated Time**: ~9 weeks to full completion

---

**Status**: 🟢 Plan Revised and Ready to Execute  
**Next Step**: Approve plan → Implement T-Invariants  
**Priority**: Complete all static analyzers first (Category A)

**Last Updated**: October 19, 2025  
**Version**: 2.0 (Revised)
