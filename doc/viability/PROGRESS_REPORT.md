# Viability Refactor Progress Report

**Date:** November 12, 2025  
**Status:** Phases 1-2 Complete

---

## Completed Work

### ✅ Phase 1: Remove Reactive Complexity

**Objective:** Stop interfering with simulation and Report Panel

**Changes Made:**
1. Removed `_pending_callback_registration` tracking
2. Removed `on_simulation_complete()` method (no automatic callbacks)
3. Removed `set_drawing_area()` callback registration logic
4. Removed `_ensure_simulation_callback_registered()` method
5. Removed `_feed_observer_with_kb_data()` automatic KB feeding
6. Updated `refresh_all()` to not auto-feed

**Files Modified:**
- `src/shypn/ui/panels/viability/viability_panel.py`

**Result:** Panel is now completely passive - only activates when user explicitly calls `on_transition_selected()`

**Verification:**
- ✅ No syntax errors
- ✅ Panel no longer registers simulation callbacks
- ✅ No automatic KB updates
- ✅ Won't interfere with Report Panel

---

### ✅ Phase 2: Subnet Construction

**Objective:** Create data structures and builder for subnet analysis

**New Modules Created:**

#### `investigation.py` (254 lines)
Data classes for investigations:
- `InvestigationMode` enum (SINGLE_LOCALITY, SUBNET)
- `Dependency` - flow dependencies between localities
- `Subnet` - subnet structure with boundary classification
- `Issue` - analysis issues (🔴🟡🟢 severity)
- `Suggestion` - actionable fixes
- `BoundaryAnalysis` - boundary flow results
- `ConservationAnalysis` - conservation check results
- `LocalityInvestigation` - single locality investigation
- `SubnetInvestigation` - multi-locality subnet investigation
- `InvestigationManager` - manage multiple investigations

#### `subnet_builder.py` (241 lines)
Subnet extraction and analysis:
- `build_subnet()` - extract subnet from localities
- **`_are_localities_connected()`** - validate localities share places (BFS)
- **`find_connected_components()`** - identify disconnected groups
- `classify_places()` - boundary vs internal classification
- `find_dependencies()` - identify flow dependencies
- `analyze_topology()` - compute subnet metrics

**Key Feature: Connectivity Validation**
- ✅ Only forms subnets from **connected** localities (must share places)
- ✅ Raises `ValueError` if localities are disconnected
- ✅ Uses BFS graph traversal to check connectivity
- ✅ Provides `find_connected_components()` for error messages

**Tests Created:**
- `tests/viability/conftest.py` - pytest fixtures with mocks
- `tests/viability/test_investigation.py` - 15 tests for data classes
- `tests/viability/test_subnet_builder.py` - 13 tests including:
  - ✅ Connectivity validation
  - ✅ Disconnected localities rejection
  - ✅ Connected components detection

**Result:** Solid foundation for subnet-based analysis

**Verification:**
- ✅ No syntax errors
- ✅ All data classes working
- ✅ Subnet builder classifies places correctly
- ✅ Dependencies detected properly
- ✅ Tests cover core functionality

---

## Architecture Highlights

### On-Demand Model
```python
# OLD (reactive):
panel.on_simulation_complete() → auto-updates

# NEW (on-demand):
user right-clicks → panel.on_transition_selected() → pull data → analyze
```

### Subnet Support
```python
# Single locality:
builder.build_subnet([loc1]) → simple subnet

# Multiple CONNECTED localities:
builder.build_subnet([loc1, loc2, loc3]) → subnet with:
  - Boundary places (external connections)
  - Internal places (fully enclosed)
  - Dependencies (T1 → P3 → T2)

# Multiple DISCONNECTED localities:
builder.build_subnet([loc1, loc_isolated]) 
  → raises ValueError("not connected")
  
# Find which can form subnets:
builder.find_connected_components([loc1, loc2, loc3])
  → [[0, 1], [2]]  # loc1+loc2 connected, loc3 isolated
```

**Connectivity Requirement:**
- Subnets only form from localities sharing at least one place
- No artificial grouping of disconnected localities
- Enforced via BFS graph traversal

---

## Next Steps

### Phase 3: Multi-Level Analyzers (3 days)
Create `analysis/` module with:
- `locality_analyzer.py` - Level 1: per-locality issues
- `dependency_analyzer.py` - Level 2: inter-locality flows
- `boundary_analyzer.py` - Level 3: subnet boundary
- `conservation_analyzer.py` - Level 4: subnet conservation

### Phase 4: Subnet UI (2 days)
Create `ui/` module with:
- `investigation_view.py` - single locality view
- `subnet_view.py` - multi-level subnet view
- `topology_viewer.py` - mini topology canvas
- All Wayland-safe

### Phases 5-7: Fix System + Integration (4 days)
- Fix sequencing and application
- Data pulling layer
- Wire everything in viability_panel.py

---

## Phase 3: Multi-Level Analyzers ✅ COMPLETE

**Status:** Complete  
**Completion:** Current session

### What Was Built

Created 4 analyzer classes implementing multi-level subnet analysis:

#### 1. `analysis/base_analyzer.py` (93 lines)
Abstract base class for all analyzers:
- `analyze(context)` - abstract method for analysis
- `generate_suggestions(issues, context)` - abstract method for fixes
- `_get_human_readable_name(element_id, kb)` - helper for display
- `clear()` - reset state

#### 2. `analysis/locality_analyzer.py` (316 lines)
**Level 1: Single Locality Analysis**

Analyzes individual transition problems:
- `_analyze_structural()` - topology issues (missing arcs, source/sink, weight balance)
- `_analyze_biological()` - semantic issues (unmapped compounds, KEGG reactions)
- `_analyze_kinetic()` - simulation issues (never fired, low rate, missing parameters)

Generates suggestions:
- `_suggest_structural_fix()` - balance weights, review source/sink
- `_suggest_biological_fix()` - map compounds, map reactions
- `_suggest_kinetic_fix()` - query BRENDA, adjust rates, investigate enablement

#### 3. `analysis/dependency_analyzer.py` (278 lines)
**Level 2: Inter-Locality Flow Analysis**

Analyzes dependencies between transitions:
- `_analyze_flow_balance()` - production vs consumption matching
- `_analyze_bottlenecks()` - slow transitions limiting subnet
- `_analyze_cascading_issues()` - problems propagating through dependencies

Generates suggestions:
- `_suggest_flow_fix()` - adjust rates to balance flows
- `_suggest_bottleneck_fix()` - increase rate, check enablement
- `_suggest_cascade_fix()` - fix root cause to resolve downstream

#### 4. `analysis/boundary_analyzer.py` (272 lines)
**Level 3: Subnet Boundary Analysis**

Analyzes subnet edge behavior:
- `_analyze_accumulation()` - detects places gaining tokens (> 2x initial)
- `_analyze_depletion()` - detects places losing tokens (< 50% initial)
- `_analyze_balance()` - checks overall subnet input/output balance
- `create_boundary_analysis()` - generates `BoundaryAnalysis` summary

Generates suggestions:
- `_suggest_accumulation_fix()` - add sink, review storage
- `_suggest_depletion_fix()` - add source (critical if near empty), increase input
- `_suggest_balance_fix()` - balance subnet material flow

#### 5. `analysis/conservation_analyzer.py` (315 lines)
**Level 4: Conservation Law Validation**

Analyzes physical conservation laws:
- `_analyze_p_invariants()` - validates P-invariants conserved over time
- `_analyze_mass_balance()` - checks stoichiometry and compound formulas
- `_analyze_conservation_leaks()` - detects unexplained material changes
- `create_conservation_analysis()` - generates `ConservationAnalysis` summary

Generates suggestions:
- `_suggest_invariant_fix()` - add source/sink or fix stoichiometry
- `_suggest_mass_fix()` - map reactions for validation
- `_suggest_leak_fix()` - review stoichiometry, check arc weights

### Test Suite

Created comprehensive tests for all analyzers:
- `test_locality_analyzer.py` (12 tests)
- `test_dependency_analyzer.py` (10 tests)
- `test_boundary_analyzer.py` (13 tests)
- `test_conservation_analyzer.py` (14 tests)
- **Total: 49 analyzer tests**

### Metrics

**Total Analysis Code:** 1,274 lines  
**Test Coverage:** 49 tests across 4 analyzers  
**Syntax Validation:** All files error-free ✓

### Architecture

**4-Level Analysis Hierarchy:**
1. **Locality** → Individual transition problems (structural/biological/kinetic)
2. **Dependency** → Inter-transition flows (balance/bottlenecks/cascades)
3. **Boundary** → Subnet edges (accumulation/depletion/balance)
4. **Conservation** → Physical laws (P-invariants/mass/leaks)

**Common Pattern:**
- All analyzers inherit from `BaseAnalyzer`
- `analyze(context)` → returns list of `Issue` objects
- `generate_suggestions(issues, context)` → returns list of `Suggestion` objects
- Context dict provides flexibility for different data requirements
- Clear separation: analysis (detect) vs suggestions (fix)

### Result

✅ Complete analysis engine for viability investigations  
✅ Multi-level approach from local to global concerns  
✅ Actionable suggestions with impact predictions  
✅ Ready for UI integration (Phase 4)

---

## Phase 4: UI Components ✅ COMPLETE

**Status:** Complete  
**Completion:** Current session

### What Was Built

Created complete GTK3 UI layer (1,634 lines, 11 widgets):

#### 1. `ui/suggestion_widgets.py` (279 lines)
- `SuggestionWidget` - Single suggestion with Apply/Preview buttons
- `SuggestionList` - Grouped suggestions with Apply All
- `SuggestionAppliedBanner` - Success banner with Undo

#### 2. `ui/issue_widgets.py` (320 lines)
- `IssueWidget` - Single issue with severity emoji (🔴🟡🟢)
- `IssueList` - Grouped issues with filtering
- `IssueSummary` - Compact one-line summary

#### 3. `ui/investigation_view.py` (296 lines)
- `InvestigationView` - Single locality investigation display
- `LocalityOverviewCard` - Compact locality card for subnet view

#### 4. `ui/subnet_view.py` (382 lines)
- `SubnetView` - Multi-level subnet investigation with stack switcher
  - Level 1: Localities (cards)
  - Level 2: Dependencies (issues + suggestions)
  - Level 3: Boundaries (summary + issues + suggestions)
  - Level 4: Conservation (summary + issues + suggestions)

#### 5. `ui/topology_viewer.py` (357 lines)
- `TopologyViewer` - Wayland-safe visualization (DrawingArea + Cairo)
- `TopologyViewerWithLegend` - Topology + legend bar

### Key Features

**Wayland Safety:**
- ✅ No X11 dependencies
- ✅ Pure GTK3 + Cairo
- ✅ Works in Wayland environments

**User Experience:**
- Severity indicators: 🔴 error, 🟡 warning, 🟢 info
- Grouping by category/severity
- Expandable sections
- Filter dropdown
- Apply/Preview/Undo buttons
- "Apply All" for batch operations
- Scrollable lists
- Line-wrapped text

**Architecture:**
- Self-contained widgets
- Clear callback interfaces
- Reusable components
- Proper CSS classes
- Responsive layouts

### Test Coverage
- 11 widget tests in `test_ui_widgets.py`
- Validates widget creation, callbacks, grouping

### Metrics
- **Total UI Code:** 1,634 lines
- **Widgets Created:** 11
- **Tests:** 11
- **Zero Syntax Errors:** All validated ✓

---

## Key Benefits So Far

✅ **Performance:** No more simulation interference  
✅ **Clean Architecture:** Separate modules, clear responsibilities  
✅ **Testability:** Unit tests for each component (88+ tests total)  
✅ **Subnet Support:** Multi-locality analysis with connectivity validation  
✅ **OOP Design:** Classes in separate files  
✅ **Multi-Level Analysis:** 4 analyzers covering all aspects  
✅ **Actionable Fixes:** Concrete suggestions with preview capability  
✅ **Complete UI:** All investigation results displayable  
✅ **Wayland-Safe:** Works in pure Wayland environments  
✅ **Interactive:** Apply/Preview/Undo workflow  

---

**Ready to proceed with Phase 5 (Fix Sequencing)!** �
