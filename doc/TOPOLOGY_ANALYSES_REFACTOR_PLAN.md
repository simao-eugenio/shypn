# Topology Analyses Refactor Plan

**Date**: November 9, 2025  
**Branch**: `topology-analyses`  
**Context**: Refactoring Topology Analyses category to match the design pattern of Models and Dynamic Analyses

---

## Executive Summary

The current Topology Analyses category uses **text-based displays** with TextViews, while Models and Dynamic Analyses categories use **structured tables** (Gtk.TreeView with sortable columns). This creates UI inconsistency and limits data usability.

**Goal**: Refactor Topology Analyses to use **tables with grouped results**, matching the successful patterns from Models and Dynamic Analyses.

---

## Current State Analysis

### 1. Models Category (REFERENCE - Good Pattern) ✅

**Structure**:
```
MODELS
├── Model Overview (Frame - always visible)
│   └── Text summary (name, date, file, description)
├── Petri Net Structure (Frame - always visible)
│   └── Text summary (counts, model type)
├── Import Provenance (Frame - conditional)
│   └── Text summary (source, organism, date)
├── Show Species/Places Table (Expander - collapsed)
│   ├── Toolbar (column toggles, legend)
│   └── Sortable Table (ID, Name, Type, Formula, Tokens, Biological Role, Data Source)
├── Show Reactions/Transitions Table (Expander - collapsed)
│   └── Sortable Table (ID, Name, Type, Rate Function, EC Number, Pathway, Data Source)
└── Show Selected Locality (Expander - conditional)
    └── Sortable Table (unified view: transition + input places + output places)
```

**Key Features**:
- ✅ **Summary frames** at top (always visible)
- ✅ **Tables in expanders** (collapsed by default)
- ✅ **Sortable columns** for all data
- ✅ **Color-coded cells** (database source: green=KEGG, blue=BRENDA, orange=User)
- ✅ **Conditional visibility** (locality only shown when selected)
- ✅ **Search/filter** capability
- ✅ **Export-friendly** structured data

---

### 2. Dynamic Analyses Category (REFERENCE - Good Pattern) ✅

**Structure**:
```
DYNAMIC ANALYSES
├── Summary (Frame - always visible)
│   └── Text summary (simulation status, data availability)
├── 📊 Simulation Data (Expander - collapsed)
│   ├── Status label
│   ├── Species Concentration Table
│   │   └── Sortable columns (Species, Initial, Final, Min, Max, Average)
│   ├── Reaction Activity Table
│   │   └── Sortable columns (Reaction, Firings, Total Rate, Avg Rate)
│   └── Reaction Selected Table (NEW - v2.4.1)
│       └── Summary statistics for selected locality
│           └── Columns: Component, ID, Name, Initial, Final, Min, Max, Avg, Info
```

**Key Features**:
- ✅ **Summary frame** at top
- ✅ **Multiple tables** in single expander (logical grouping)
- ✅ **Summary statistics** instead of time-series data
- ✅ **Reaction Selected** shows locality pattern (P→T→P) in 3-5 rows
- ✅ **Per-document data** isolation
- ✅ **Auto-refresh** on simulation complete

---

### 3. Topology Analyses Category (CURRENT - Needs Refactor) ❌

**Current Structure**:
```
TOPOLOGY ANALYSES
├── Analysis Summary (Frame - always visible)
│   └── Text with checkmarks/status for 4 analyses
├── Topology Analysis (Expander - collapsed)
│   ├── Summary label (text)
│   └── Detailed Metrics (Expander - nested)
│       └── TextView (unstructured text)
├── Locality Analysis (Expander - collapsed)
│   ├── Summary label (text)
│   └── Region Details (Expander - nested)
│       └── TextView (unstructured text)
├── Source-Sink Analysis (Expander - collapsed)
│   ├── Summary label (text)
│   └── Flow Details (Expander - nested)
│       └── TextView (unstructured text)
└── Structural Invariants (Expander - collapsed)
    ├── Summary label (text)
    └── Invariant Vectors (Expander - nested)
        └── TextView (unstructured text)
```

**Problems** ❌:
1. **Text-based data** - No sorting, filtering, or structured access
2. **Nested expanders** - Poor UX (expander within expander)
3. **Inconsistent with other categories** - Doesn't match Models/Dynamic Analyses patterns
4. **Not export-friendly** - Unstructured text is hard to parse
5. **No color coding** - Can't distinguish data quality/source
6. **Limited search** - Can't search/filter specific nodes or values
7. **Poor data density** - Text takes more space than tables
8. **Placeholder implementation** - Not integrated with real analyses

---

## Comparative Analysis

| Feature | Models ✅ | Dynamic Analyses ✅ | Topology Analyses ❌ |
|---------|----------|---------------------|----------------------|
| Summary Frame | ✅ Yes | ✅ Yes | ✅ Yes |
| Sortable Tables | ✅ Yes (2 tables) | ✅ Yes (3 tables) | ❌ No (TextViews) |
| Color Coding | ✅ Source colors | ⚪ N/A | ❌ No |
| Search/Filter | ✅ Yes | ✅ Yes | ❌ No |
| Grouped Results | ✅ By type | ✅ By analysis | ⚪ By analysis (text) |
| Export-Friendly | ✅ Structured | ✅ Structured | ⚪ Text-based |
| Nested Expanders | ❌ No (flat) | ❌ No (flat) | ❌ Yes (bad UX) |
| Data Integration | ✅ Real-time | ✅ Real-time | ❌ Placeholder |

---

## Design Problems to Fix

### Problem 1: Text-Based Data Display ❌
**Current**: TextView with unstructured text
```
Detailed topology metrics will appear here:
- Node degree distribution
- Connected components list
- Detected cycles
- Hub nodes identification
```

**Issue**: Can't sort, filter, or export structured data.

---

### Problem 2: Nested Expanders ❌
**Current**: Expander → Expander → TextView
```
Topology Analysis (Expander)
└── Detailed Metrics (Expander)
    └── TextView
```

**Issue**: Double-click required, poor UX, inconsistent with other categories.

---

### Problem 3: No Structured Results ❌
**Current**: Results mixed in text blob
```
"Degree distribution:
  Node P1: degree 3
  Node P2: degree 5
  ...
Connected components: 2
Cycles detected: 4"
```

**Issue**: Can't sort by degree, filter by component, or export to CSV.

---

### Problem 4: Data Source Not Tracked ❌
**Current**: No indication of analysis quality/confidence
**Issue**: Can't distinguish computed vs heuristic vs incomplete results.

---

## Proposed Refactor

### New Structure

```
TOPOLOGY ANALYSES
├── Analysis Summary (Frame - always visible)
│   └── Status: X of Y analyses complete, warnings
│
├── 📊 Graph Structure (Expander - collapsed)
│   ├── Summary label (quick stats)
│   └── Node Degrees Table (sortable)
│       └── Columns: Node, ID, Type, In-Degree, Out-Degree, Total Degree, Is Hub
│
├── 🔗 Network Components (Expander - collapsed)
│   ├── Summary label (component count, largest size)
│   ├── Components Table (sortable)
│   │   └── Columns: Component ID, Size, Nodes List, Type (strong/weak)
│   └── Isolated Nodes Table (if any)
│       └── Columns: Node, ID, Type, Reason
│
├── 🔄 Cycles & Paths (Expander - collapsed)
│   ├── Summary label (cycle count, feedback loops)
│   ├── Cycles Table (sortable)
│   │   └── Columns: Cycle ID, Length, Nodes, Type (P-cycle/T-cycle), Significance
│   └── Critical Paths Table (if computed)
│       └── Columns: Path ID, Length, Start→End, Bottleneck Nodes
│
├── 📍 Localities (Expander - collapsed)
│   ├── Summary label (locality count, coverage)
│   └── Localities Table (sortable)
│       └── Columns: Transition, Inputs, Outputs, Is Valid, Is Source, Is Sink, Complexity
│
├── 🔁 Source-Sink Analysis (Expander - collapsed)
│   ├── Summary label (source/sink counts)
│   ├── Sources Table (sortable)
│   │   └── Columns: Transition, ID, Output Places, Flow Capacity
│   └── Sinks Table (sortable)
│       └── Columns: Transition, ID, Input Places, Consumption Rate
│
└── 🔢 Structural Invariants (Expander - collapsed)
    ├── Summary label (P-inv/T-inv counts, coverage)
    ├── P-Invariants Table (sortable)
    │   └── Columns: ID, Size, Places, Coverage %, Is Minimal
    └── T-Invariants Table (sortable)
        └── Columns: ID, Size, Transitions, Coverage %, Is Minimal
```

---

## Detailed Table Specifications

### 1. Node Degrees Table

**Purpose**: Show connectivity of each node (place/transition)

**Columns**:
| Column | Type | Description | Sortable | Width |
|--------|------|-------------|----------|-------|
| Node | Text | Place/Transition name | ✅ | 120px |
| ID | Text | Internal ID | ✅ | 80px |
| Type | Text | "Place" or "Transition" | ✅ | 100px |
| In-Degree | Int | Number of incoming arcs | ✅ | 80px |
| Out-Degree | Int | Number of outgoing arcs | ✅ | 80px |
| Total Degree | Int | In + Out | ✅ | 100px |
| Is Hub | Bool | Total > threshold | ✅ | 80px |

**Sample Data**:
```
Node          | ID   | Type       | In | Out | Total | Hub
-----------------------------------------------------------
ATP           | P001 | Place      | 12 | 8   | 20    | ✅
Glycolysis_T1 | T004 | Transition | 2  | 3   | 5     | ❌
Glucose       | P002 | Place      | 0  | 15  | 15    | ✅
```

**Features**:
- Click column header to sort
- Search by name or ID
- Color code hubs (orange background)
- Export to CSV

---

### 2. Components Table

**Purpose**: Show connected components in the network

**Columns**:
| Column | Type | Description | Sortable | Width |
|--------|------|-------------|----------|-------|
| Component | Text | Component identifier | ✅ | 100px |
| Size | Int | Number of nodes | ✅ | 80px |
| Nodes | Text | Comma-separated list (truncated) | ❌ | 200px |
| Type | Text | Strong/Weak connected | ✅ | 120px |
| Is Isolated | Bool | Single-node component | ✅ | 100px |

**Sample Data**:
```
Component | Size | Nodes                        | Type   | Isolated
------------------------------------------------------------------
C1        | 234  | P001, P002, T001, ...       | Strong | ❌
C2        | 12   | P055, T012, P056, ...       | Weak   | ❌
C3        | 1    | P099                        | Weak   | ✅
```

---

### 3. Cycles Table

**Purpose**: Show detected cycles (feedback loops)

**Columns**:
| Column | Type | Description | Sortable | Width |
|--------|------|-------------|----------|-------|
| Cycle | Text | Cycle identifier | ✅ | 80px |
| Length | Int | Number of nodes in cycle | ✅ | 80px |
| Nodes | Text | Cycle path | ❌ | 250px |
| Type | Text | P-cycle, T-cycle, Mixed | ✅ | 100px |
| Significance | Text | Regulatory, Metabolic, etc. | ✅ | 120px |

**Sample Data**:
```
Cycle | Length | Nodes                    | Type    | Significance
--------------------------------------------------------------------
C1    | 4      | P1→T1→P2→T2→P1          | Mixed   | Regulatory
C2    | 6      | T1→T2→T3→T4→T5→T6→T1    | T-cycle | Metabolic
C3    | 3      | P5→P6→P7→P5             | P-cycle | Feedback
```

**Color Coding**:
- Regulatory cycles: Blue background
- Metabolic cycles: Green background
- Short cycles (≤3): Yellow background (potential oscillation)

---

### 4. Localities Table

**Purpose**: Show all detected localities (input places → transition → output places)

**Columns**:
| Column | Type | Description | Sortable | Width |
|--------|------|-------------|----------|-------|
| Transition | Text | Transition name | ✅ | 120px |
| ID | Text | Transition ID | ✅ | 80px |
| Inputs | Int | Number of input places | ✅ | 80px |
| Outputs | Int | Number of output places | ✅ | 80px |
| Is Valid | Bool | Has both inputs and outputs | ✅ | 80px |
| Is Source | Bool | No inputs (token generator) | ✅ | 80px |
| Is Sink | Bool | No outputs (token consumer) | ✅ | 80px |
| Complexity | Text | Simple/Medium/Complex | ✅ | 100px |

**Sample Data**:
```
Transition | ID   | Inputs | Outputs | Valid | Source | Sink | Complexity
---------------------------------------------------------------------------
Reaction_1 | T001 | 2      | 3       | ✅    | ❌     | ❌   | Simple
Synthesis  | T005 | 0      | 5       | ✅    | ✅     | ❌   | Medium
Degradation| T012 | 8      | 0       | ✅    | ❌     | ✅   | Complex
Orphan_T   | T099 | 0      | 0       | ❌    | ❌     | ❌   | Invalid
```

**Color Coding**:
- Sources: Light green background
- Sinks: Light blue background
- Invalid: Light red background

**Actions**:
- Double-click row → Select transition in Analyses panel
- Right-click → "Highlight locality on canvas"

---

### 5. P-Invariants Table

**Purpose**: Show place invariants (conservation laws)

**Columns**:
| Column | Type | Description | Sortable | Width |
|--------|------|-------------|----------|-------|
| ID | Text | Invariant identifier | ✅ | 60px |
| Size | Int | Number of places | ✅ | 60px |
| Places | Text | Place names (truncated) | ❌ | 200px |
| Coverage | Float | % of places covered | ✅ | 100px |
| Is Minimal | Bool | Not subset of another | ✅ | 100px |
| Biological | Text | Interpretation (if known) | ❌ | 150px |

**Sample Data**:
```
ID   | Size | Places                  | Coverage | Minimal | Biological
-------------------------------------------------------------------------
P-I1 | 5    | ATP, ADP, AMP, ...     | 15.2%    | ✅      | Adenylate pool
P-I2 | 12   | NAD+, NADH, ...        | 38.5%    | ✅      | Redox balance
P-I3 | 3    | Glucose, G6P, F6P      | 9.1%     | ❌      | Glycolysis
```

---

### 6. T-Invariants Table

**Purpose**: Show transition invariants (elementary flux modes)

**Columns**:
| Column | Type | Description | Sortable | Width |
|--------|------|-------------|----------|-------|
| ID | Text | Invariant identifier | ✅ | 60px |
| Size | Int | Number of transitions | ✅ | 60px |
| Transitions | Text | Transition names (truncated) | ❌ | 200px |
| Coverage | Float | % of transitions covered | ✅ | 100px |
| Is Minimal | Bool | Not subset of another | ✅ | 100px |
| Pathway | Text | Pathway annotation | ❌ | 150px |

**Sample Data**:
```
ID   | Size | Transitions            | Coverage | Minimal | Pathway
----------------------------------------------------------------------
T-I1 | 8    | Glycolysis_T1, T2, ... | 22.4%    | ✅      | Glycolysis
T-I2 | 15   | TCA_T1, T2, T3, ...    | 42.1%    | ✅      | TCA cycle
T-I3 | 4    | T15, T16, T17, T18     | 11.2%    | ❌      | Branch
```

---

## Implementation Plan

### Phase 1: Table Infrastructure (Week 1)

**Goal**: Create reusable table components

**Tasks**:
1. Create `TopologyTableBase` class (extends Gtk.TreeView)
   - Standard column creation
   - Sortable columns by default
   - Search/filter support
   - Color coding support
   - Export to CSV

2. Create specific table classes:
   - `NodeDegreesTable`
   - `ComponentsTable`
   - `CyclesTable`
   - `LocalitiesTable`
   - `InvariantsTable`

**Files to Create**:
- `src/shypn/ui/panels/report/widgets/topology_tables.py`

---

### Phase 2: Data Model (Week 1)

**Goal**: Define data structures for topology results

**Tasks**:
1. Create `TopologyAnalysisResult` data class
   ```python
   @dataclass
   class TopologyAnalysisResult:
       timestamp: datetime
       node_degrees: List[NodeDegree]
       components: List[Component]
       cycles: List[Cycle]
       localities: List[Locality]
       p_invariants: List[PInvariant]
       t_invariants: List[TInvariant]
       warnings: List[str]
       status: str  # 'complete', 'partial', 'error'
   ```

2. Create storage in DocumentReportData
   ```python
   class DocumentReportData:
       # ... existing ...
       topology_result: Optional[TopologyAnalysisResult] = None
   ```

**Files to Modify**:
- `src/shypn/ui/panels/report/document_report_data.py`

**Files to Create**:
- `src/shypn/data/topology_analysis_result.py`

---

### Phase 3: UI Refactor (Week 2)

**Goal**: Replace TextViews with tables

**Tasks**:
1. Refactor `_build_content()` in `topology_analyses_category.py`
   - Remove nested expanders
   - Remove TextViews and TextBuffers
   - Add table widgets
   - Add summary labels

2. Update expander structure:
   ```python
   # Old (nested):
   Topology Analysis (Expander)
   └── Detailed Metrics (Expander)
       └── TextView
   
   # New (flat):
   📊 Graph Structure (Expander)
   ├── Summary label
   └── NodeDegreesTable
   ```

3. Implement `_populate_XXX_table()` methods
   - `_populate_degrees_table()`
   - `_populate_components_table()`
   - `_populate_cycles_table()`
   - `_populate_localities_table()`
   - `_populate_invariants_table()`

**Files to Modify**:
- `src/shypn/ui/panels/report/topology_analyses_category.py`

---

### Phase 4: Integration (Week 2-3)

**Goal**: Wire up real data from analysis algorithms

**Tasks**:
1. Connect to LocalityDetector
   - Fetch locality results
   - Populate localities table
   - Mark sources/sinks

2. Connect to graph algorithms (if implemented)
   - Degree calculation
   - Component detection
   - Cycle detection

3. Connect to invariant computation (if implemented)
   - P-invariant calculation
   - T-invariant calculation

4. Implement auto-refresh
   - On model load
   - On model modification
   - On demand (refresh button)

**Files to Modify**:
- `src/shypn/ui/panels/report/topology_analyses_category.py`
- `src/shypn/diagnostic/locality_detector.py` (if needed)

---

### Phase 5: Actions & Export (Week 3)

**Goal**: Add interactivity and export

**Tasks**:
1. Add table actions:
   - Double-click → Select object on canvas
   - Right-click → Context menu
   - "Highlight on canvas"
   - "Copy to clipboard"

2. Implement export:
   - Export table → CSV
   - Export all → Multi-sheet Excel
   - Export summary → PDF

3. Add toolbar:
   - Refresh button
   - Export button
   - Filter controls

**Files to Modify**:
- `src/shypn/ui/panels/report/topology_analyses_category.py`

---

## Success Criteria

### UI Consistency ✅
- [ ] All data in sortable tables (like Models/Dynamic Analyses)
- [ ] No nested expanders (flat structure)
- [ ] Color-coded cells for data quality
- [ ] Summary frame at top

### Data Usability ✅
- [ ] Can sort by any column
- [ ] Can search/filter results
- [ ] Can export to CSV/Excel
- [ ] Can copy individual cells

### Integration ✅
- [ ] Real data from LocalityDetector
- [ ] Auto-refresh on model changes
- [ ] Per-document isolation (like Dynamic Analyses)
- [ ] Proper callback registration

### User Experience ✅
- [ ] Single-click expand shows table
- [ ] Double-click row selects object
- [ ] Right-click context menu
- [ ] Keyboard navigation works

---

## Migration Path

### Step 1: Keep Old Code (Parallel Development)
- Don't delete TextViews immediately
- Create new table components alongside
- Test both versions

### Step 2: Feature Flag (Testing)
```python
USE_NEW_TOPOLOGY_TABLES = True  # Set to False to revert

if USE_NEW_TOPOLOGY_TABLES:
    content = self._build_table_content()
else:
    content = self._build_textview_content()
```

### Step 3: Remove Old Code (Cleanup)
- After testing confirms new version works
- Delete TextViews and buffers
- Delete nested expanders
- Clean up unused methods

---

## Risk Assessment

### Low Risk ⚠️
- **UI refactor only** - No changes to analysis algorithms
- **Isolated to one category** - Doesn't affect Models or Dynamic Analyses
- **Reuses existing patterns** - Following proven Models/Dynamic Analyses design

### Medium Risk ⚠️⚠️
- **Data integration** - May need to modify LocalityDetector API
- **Performance** - Large tables (1000+ rows) need optimization
- **Testing** - Needs thorough testing with real models

### Mitigation
- Develop on `topology-analyses` branch (isolated)
- Feature flag for easy rollback
- Incremental deployment (Phase 1 → 2 → 3 → ...)
- Extensive testing with large models

---

## Open Questions

1. **LocalityDetector API**: Does it already return structured data or just text?
   - Need to check `src/shypn/diagnostic/locality_detector.py`
   - May need to enhance API to return List[LocalityData]

2. **Invariant Computation**: Is this implemented?
   - Check if P-invariants/T-invariants are computed
   - May need to implement or integrate external library

3. **Performance**: How many rows in typical models?
   - Test with 100-place, 1000-place models
   - May need pagination or virtual scrolling

4. **Color Scheme**: What colors for data sources?
   - Reuse Models colors (green=database, blue=BRENDA, etc.)?
   - Or new scheme (green=complete, yellow=partial, red=missing)?

---

## Summary

**Current State**: Text-based displays with nested expanders (inconsistent, not user-friendly)

**Proposed State**: Table-based displays with flat expanders (consistent with Models/Dynamic Analyses)

**Benefits**:
- ✅ Sortable, searchable, filterable data
- ✅ Export-friendly (CSV/Excel)
- ✅ Consistent UI across all Report Panel categories
- ✅ Better data density and readability
- ✅ Interactive (double-click to select, right-click menu)

**Effort**: ~3 weeks (5 phases)

**Risk**: Low (isolated refactor, reuses proven patterns)

**Next Steps**:
1. Review and approve this plan
2. Start Phase 1 (Table Infrastructure)
3. Incremental development with testing at each phase

---

**Document Version**: 1.0  
**Author**: GitHub Copilot (Analysis Agent)  
**Status**: Proposal - Awaiting Approval
