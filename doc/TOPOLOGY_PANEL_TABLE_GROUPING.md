# Topology Panel Table Grouping Plan

**Date**: November 9, 2025  
**Branch**: topology-analyses  
**Purpose**: Group related analyzers into unified tables with type columns

## Overview

Currently, each analyzer in the Topology Panel has its own expander with separate results display. This creates visual clutter and makes comparison difficult. 

**Proposed Solution**: Group related analyzers into **unified tables** where each analyzer's results become rows with a **Type** column to distinguish them.

## Benefits

1. **Better Data Density**: See all related results in one table
2. **Easy Comparison**: Sort by Type, Size, Properties across different analysis types
3. **Consistent UI**: Single table per category instead of 4-5 separate expanders
4. **Reduced Clicking**: No need to expand multiple expanders to see results
5. **Export-Friendly**: Single CSV/JSON export per category captures all analyses

## Category Groupings

### 1. STRUCTURAL ANALYSIS → Unified Invariants & Traps Table

**Current**: 4 separate expanders (P-Invariants, T-Invariants, Siphons, Traps)  
**Proposed**: Single table with Type column

#### Table: Structural Properties

| Type | Name | Size | Elements | Support | Properties |
|------|------|------|----------|---------|------------|
| P-Invariant | P_Inv_1 | 5 | p1,p2,p3,p4,p5 | [1,1,1,2,1] | Conservative |
| P-Invariant | P_Inv_2 | 3 | p6,p7,p8 | [1,1,1] | Minimal |
| T-Invariant | T_Inv_1 | 4 | t1,t2,t3,t4 | [1,2,1,1] | Reproducible |
| Siphon | Siphon_1 | 3 | p1,p5,p9 | - | Minimal, Not Trap |
| Trap | Trap_1 | 2 | p2,p3 | - | Minimal, Not Siphon |

**Column Definitions**:
- **Type**: Invariant/structural property type (P-Invariant, T-Invariant, Siphon, Trap)
- **Name**: Auto-generated identifier (P_Inv_1, T_Inv_1, etc.)
- **Size**: Number of elements in the structure
- **Elements**: Comma-separated list of places/transitions involved
- **Support**: Support vector (for invariants) or "-" for siphons/traps
- **Properties**: Key characteristics (Minimal, Conservative, Reproducible, etc.)

**Implementation**:
- Run all 4 analyzers in parallel (if safe - P/T-Inv are safe, Siphons/Traps are dangerous)
- Merge results into single ListStore
- Add Type column for filtering/sorting
- Color-code by type: Green=P-Inv, Blue=T-Inv, Orange=Siphon, Red=Trap

**Auto-run Policy**:
- ✅ P-Invariants: Auto-run (safe, polynomial)
- ✅ T-Invariants: Auto-run (safe, polynomial)
- ❌ Siphons: Manual only (dangerous, exponential)
- ❌ Traps: Manual only (dangerous, exponential)

---

### 2. GRAPH & NETWORK ANALYSIS → Unified Graph Properties Table

**Current**: 3 separate expanders (Cycles, Paths, Hubs)  
**Proposed**: Single table with Type column

#### Table: Graph Properties

| Type | ID | Length/Degree | Nodes | Properties | Significance |
|------|-----|---------------|-------|------------|--------------|
| Cycle | Cycle_1 | 6 | p1→t1→p2→t2→p3→t3→p1 | Simple, Directed | Medium |
| Cycle | Cycle_2 | 4 | p5→t5→p6→t6→p5 | Elementary | High |
| Path | Path_1 | 8 | p1→t1→...→p10 | Longest | Critical |
| Hub | Hub_p5 | 12 | p5 | Place, In/Out=6/6 | High Connectivity |
| Hub | Hub_t3 | 8 | t3 | Transition, In/Out=4/4 | Medium Connectivity |

**Column Definitions**:
- **Type**: Graph structure type (Cycle, Path, Hub)
- **ID**: Unique identifier (Cycle_1, Path_1, Hub_p5)
- **Length/Degree**: 
  - Cycles/Paths: Number of nodes in the path
  - Hubs: Total degree (in + out connections)
- **Nodes**: 
  - Cycles/Paths: Sequence of nodes (p1→t1→p2)
  - Hubs: Node name
- **Properties**: 
  - Cycles: Simple/Elementary, Directed/Undirected
  - Paths: Shortest/Longest, Critical
  - Hubs: Place/Transition, In/Out degree breakdown
- **Significance**: High/Medium/Low (based on size/complexity)

**Implementation**:
- Run all 3 analyzers in parallel (all safe)
- Merge results with Type discriminator
- Color-code: Blue=Cycle, Green=Path, Orange=Hub
- Add context menu: "Highlight in Model" to show cycle/path/hub on canvas

**Auto-run Policy**:
- ✅ Cycles: Auto-run (safe, efficient algorithm)
- ✅ Paths: Auto-run (safe, linear traversal)
- ✅ Hubs: Auto-run (safe, degree calculation)

---

### 3. BEHAVIORAL ANALYSIS → 2 Tables (Different Structures)

**Current**: 5 separate expanders  
**Proposed**: 2 tables (Properties Matrix + Deadlock Details)

#### Table 1: Behavioral Properties Matrix

**Single-row table** showing Yes/No for each property:

| Reachability | Boundedness | Liveness | Deadlocks | Fairness |
|--------------|-------------|----------|-----------|----------|
| Yes (245 states) | Yes (k=5) | Quasi-Live (80%) | Yes (3 found) | Yes |

**Column Definitions**:
- **Reachability**: Yes/No + state count if computed
- **Boundedness**: Yes/No + bound value (k) if bounded
- **Liveness**: Yes/No or Quasi-Live + percentage
- **Deadlocks**: Yes/No + count if detected
- **Fairness**: Yes/No

**Visual Format**:
- Green cell background = Yes (good property)
- Red cell background = No or detected problem
- Orange cell background = Partial/Warning (e.g., Quasi-Live)
- Cell text shows qualifier (state count, bound, percentage)

**Example Visual**:
```
┌─────────────────┬──────────────┬───────────────┬──────────────┬──────────┐
│ Reachability    │ Boundedness  │ Liveness      │ Deadlocks    │ Fairness │
├─────────────────┼──────────────┼───────────────┼──────────────┼──────────┤
│ 🟢 Yes          │ 🟢 Yes       │ 🟠 Quasi-Live │ 🔴 Yes       │ 🟢 Yes   │
│ 245 states      │ k=5          │ 80%           │ 3 found      │          │
└─────────────────┴──────────────┴───────────────┴──────────────┴──────────┘
```

#### Table 2: Deadlock States (shown only if deadlocks detected)

| Has Deadlock | Deadlock Type | Disabled Transitions | Deadlock Places |
|--------------|---------------|----------------------|-----------------|
| Yes | Total Deadlock | t1, t2, t5 | p1 (0 tokens), p3 (0 tokens) |
| Yes | Partial Deadlock | t3, t7 | p5 (0 tokens), p9 (1 token) |
| Yes | Siphon-Based | t2, t4, t6 | p2 (0 tokens), p8 (0 tokens), p10 (0 tokens) |

**Column Definitions**:
- **Has Deadlock**: Always "Yes" in this table (since table only shows deadlocks)
- **Deadlock Type**: 
  - Total Deadlock (no transitions can fire)
  - Partial Deadlock (some transitions blocked)
  - Siphon-Based (caused by empty minimal siphon)
  - Trap-Based (caused by marked minimal trap preventing progress)
- **Disabled Transitions**: Comma-separated list of transitions that cannot fire in this state
- **Deadlock Places**: Places involved in the deadlock with their token counts

**Implementation**:
- Table 1 (Properties Matrix) always visible - compact single-row overview
- Table 2 (Deadlock States) conditionally shown if "Deadlocks" column = Yes
- Color-code cells: Green=Yes/Good, Red=No/Problem, Orange=Warning
- Tooltips on hover show detailed metrics (e.g., hover Liveness → "8/10 transitions can eventually fire")
- Click on "Deadlocks: Yes (3 found)" to scroll to Deadlock States table

**Auto-run Policy**:
- ❌ Reachability: Manual only (state explosion, can take 60s+)
- ✅ Boundedness: Auto-run (safe, simple token counting)
- ❌ Liveness: Manual only (depends on reachability)
- ❌ Deadlocks: Manual only (can be expensive with siphon analysis)
- ✅ Fairness: Auto-run (safe, graph analysis)

---

### 4. BIOLOGICAL ANALYSIS → Unified Dependencies Table

**Current**: 2 separate expanders (Dependency & Coupling, Regulatory Structure)  
**Proposed**: Single table combining both

#### Table: Biological Dependencies & Regulation

| Transition Pair | Type | Shared Elements | Conflict Score | Classification | Notes |
|-----------------|------|-----------------|----------------|----------------|-------|
| (t1, t2) | Competitive | p1 (input) | 0.95 | True Conflict | Mutually exclusive firing |
| (t3, t4) | Convergent | p5 (output) | 0.00 | Valid Coupling | Both produce same metabolite |
| (t5, t6) | Regulatory | p8 (catalyst) | 0.00 | Valid Coupling | Share enzyme, no conflict |
| (t7, t8) | Independent | - | 0.00 | No Coupling | No shared places |
| t9 | Catalyst | p12 (test arc) | - | Enzymatic | Enzyme for reaction |

**Column Definitions**:
- **Transition Pair**: Transitions being analyzed (or single transition for catalysts)
- **Type**: Dependency type (Competitive, Convergent, Regulatory, Independent, Catalyst)
- **Shared Elements**: Places that cause the relationship
- **Conflict Score**: 0.0-1.0 (0=no conflict, 1=true conflict)
- **Classification**: High-level verdict (True Conflict, Valid Coupling, No Coupling, Enzymatic)
- **Notes**: Biological interpretation

**Implementation**:
- Run DependencyAndCouplingAnalyzer for transition pairs
- Run RegulatoryStructureAnalyzer for test arcs/catalysts
- Merge results with Type column
- Color-code by classification:
  - Red: True Conflict (competitive with high score)
  - Green: Valid Coupling (convergent/regulatory)
  - Gray: Independent
  - Blue: Enzymatic (catalysts)

**Auto-run Policy**:
- Auto-run both analyzers (both are graph-based, safe complexity)

---

## Implementation Strategy

### Phase 1: Refactor BaseTopologyCategory (1 day)

**Goal**: Support grouped table mode alongside existing expander mode

**Changes**:
1. Add `use_grouped_table` parameter to `__init__()`
2. Add `_build_grouped_table()` method
3. Add `_merge_analyzer_results()` method to combine results with Type column
4. Keep existing `_build_analyzer_expanders()` for backward compatibility

**New Methods**:
```python
def _build_grouped_table(self):
    """Build single table combining all analyzers in category.
    
    Returns:
        Gtk.Box: Box with table + "Run All" button
    """
    pass

def _merge_analyzer_results(self, results_dict):
    """Merge analyzer results into single table data.
    
    Args:
        results_dict: {analyzer_name: result}
    
    Returns:
        list: Rows for TreeView (with Type column)
    """
    pass
```

### Phase 2: Update Category Classes (2 days)

**For each category** (structural, graph_network, behavioral, biological):

1. **Override `_build_content()`** to use grouped table:
   ```python
   def _build_content(self):
       if self.use_grouped_table:
           return self._build_grouped_table()
       else:
           return super()._build_content()  # Old expander mode
   ```

2. **Implement `_define_table_columns()`**:
   ```python
   def _define_table_columns(self):
       """Define columns for this category's grouped table."""
       return [
           ('Type', str),
           ('Name', str),
           ('Size', int),
           # ... category-specific columns
       ]
   ```

3. **Implement `_format_analyzer_row()`**:
   ```python
   def _format_analyzer_row(self, analyzer_name, result):
       """Format single analyzer result as table row(s).
       
       Args:
           analyzer_name: Name of analyzer
           result: Analyzer result
       
       Returns:
           list: List of row tuples
       """
       pass
   ```

**Specific Implementations**:

- **StructuralCategory**: 
  - 6 columns: Type, Name, Size, Elements, Support, Properties
  - P/T-Invariants show support vectors
  - Siphons/Traps show "-" for support

- **GraphNetworkCategory**:
  - 6 columns: Type, ID, Length/Degree, Nodes, Properties, Significance
  - Cycles show path sequence
  - Hubs show single node with degree

- **BehavioralCategory**:
  - 2 tables: Properties Matrix (5 cols) + Deadlock States (4 cols)
  - Properties Matrix: Single-row with Yes/No for each property (Reachability, Boundedness, Liveness, Deadlocks, Fairness)
  - Deadlock States: Has Deadlock, Deadlock Type, Disabled Transitions, Deadlock Places

- **BiologicalCategory**:
  - 6 columns: Transition Pair, Type, Shared Elements, Conflict Score, Classification, Notes
  - Merge dependency_coupling + regulatory_structure results

### Phase 3: Enable Grouped Mode (1 day)

**Update TopologyPanel** to enable grouped tables:

```python
self.structural_category = StructuralCategory(
    model_canvas=model_canvas,
    expanded=False,
    use_grouped_table=True  # NEW: Enable grouped table
)
```

**Test each category**:
- Verify table populates correctly
- Test sorting by Type, Size, Properties
- Test color-coding
- Test context menu (if applicable)
- Test auto-run behavior

### Phase 4: Add Export & Actions (1 day)

**Add toolbar above each grouped table**:
- 📊 **Export to CSV**: Export full table
- 🎨 **Color Legend**: Show what each color means
- 🔄 **Refresh All**: Re-run all analyzers
- ⚙️ **Column Toggles**: Show/hide columns

**Add context menu** (right-click on row):
- 📍 **Highlight in Model**: Show cycle/path/invariant on canvas
- 📋 **Copy**: Copy row data to clipboard
- 🔍 **Details**: Show full details in dialog

### Phase 5: Documentation & Testing (1 day)

1. Update user documentation
2. Add screenshots showing grouped tables
3. Test performance with large models
4. Test auto-run with safe/dangerous analyzers
5. Verify backward compatibility (old expander mode still works)

---

## Migration Plan

### Step 1: Keep Old Mode Available
- Add `use_grouped_table` flag (default: False)
- Old expander mode remains default initially
- Test grouped mode in parallel

### Step 2: Gradual Rollout
1. Enable for **Graph & Network** category first (all safe analyzers)
2. Enable for **Biological** category (small result sets)
3. Enable for **Structural** category (test with P/T-Inv only)
4. Enable for **Behavioral** category last (complex logic)

### Step 3: Make Default
- After 1 week of testing, switch default to `use_grouped_table=True`
- Keep flag for users who prefer old style

### Step 4: Cleanup (Optional)
- After 1 month, if no issues, remove expander mode code
- Simplify BaseTopologyCategory

---

## Risk Assessment

### Low Risk
- ✅ Graph & Network grouping (homogeneous data, all safe)
- ✅ Biological grouping (small result sets, both safe)
- ✅ Adding Type column (simple schema change)

### Medium Risk
- ⚠️ Structural grouping (mixing safe + dangerous analyzers)
  - Mitigation: Only auto-run P/T-Inv, require manual trigger for Siphons/Traps
- ⚠️ Behavioral grouping (heterogeneous data structures)
  - Mitigation: Use 2 tables (summary + details) instead of forcing into 1

### High Risk
- ❌ Breaking existing analyzer output format
  - Mitigation: Keep analyzer classes unchanged, only change display layer

---

## Testing Plan

### Unit Tests
- [ ] Test `_merge_analyzer_results()` with various result types
- [ ] Test `_format_analyzer_row()` for each analyzer
- [ ] Test Type column filtering/sorting
- [ ] Test color-coding logic

### Integration Tests
- [ ] Test with empty model (no results)
- [ ] Test with small model (5 places, 5 transitions)
- [ ] Test with large model (50+ places, 100+ transitions)
- [ ] Test switching between documents (cache behavior)
- [ ] Test dangerous analyzer warnings in grouped table

### UI Tests
- [ ] Verify table renders correctly
- [ ] Test sorting by each column
- [ ] Test export to CSV
- [ ] Test context menu actions
- [ ] Test toolbar buttons
- [ ] Test column toggles

### Performance Tests
- [ ] Measure table render time with 100+ rows
- [ ] Measure auto-run time for safe analyzers
- [ ] Verify no UI blocking during analysis
- [ ] Test memory usage with multiple documents

---

## Timeline

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| Phase 1: Refactor Base | 1 day | Day 1 | Day 1 |
| Phase 2: Update Categories | 2 days | Day 2 | Day 3 |
| Phase 3: Enable Grouped Mode | 1 day | Day 4 | Day 4 |
| Phase 4: Export & Actions | 1 day | Day 5 | Day 5 |
| Phase 5: Documentation | 1 day | Day 6 | Day 6 |
| **Total** | **6 days** | | |

**Target Completion**: 1 week (including buffer for testing)

---

## Success Criteria

✅ All 4 categories use grouped tables  
✅ Results sorted/filtered by Type column  
✅ Color-coding clearly distinguishes analyzer types  
✅ Auto-run works for safe analyzers only  
✅ Export to CSV captures all results  
✅ No UI blocking during analysis  
✅ Context menu provides useful actions  
✅ Performance acceptable on large models (50+ places)  

---

## Next Steps

1. **Review this plan** with team/user
2. **Create branch**: `topology-grouped-tables`
3. **Start Phase 1**: Refactor BaseTopologyCategory
4. **Iterate**: Get feedback after each category implementation

---

**Document Status**: Draft for Review  
**Author**: GitHub Copilot  
**Reviewer**: Simão Eugénio
