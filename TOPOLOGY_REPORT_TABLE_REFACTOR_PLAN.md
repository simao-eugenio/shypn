# Topology Report Table-Based Refactor Plan

## Overview
Refactor the Topology Analyses category in the Report Panel from text-based expanders to professional table-based layouts, following the same approach successfully implemented for Thermodynamic Validation.

## Current Structure Analysis

### Current Display Format
**File**: `src/shypn/ui/panels/report/topology_analyses_category.py` (712 lines)

**Current Layout**:
1. **Status Bar**: Text label with icon (✓/⚠️/❌/ℹ️)
2. **Key Findings**: Text frame with bullet points
3. **Four Expanders** (text-based):
   - Structural Analysis (P/T-Invariants, Siphons, Traps)
   - Graph & Network Analysis (Cycles, Paths, Hubs)
   - Behavioral Analysis (Boundedness, Liveness, Deadlocks, etc.)
   - Biological Analysis (Dependency, Regulatory patterns)

### Current Problems
- Text-based display with many expanders (like old thermodynamic report)
- Information scattered across multiple collapsible sections
- No sorting, searching, or filtering capabilities
- Poor data density - lots of scrolling needed
- Inconsistent with refactored thermodynamic validation UI

## Refactoring Goals

### Primary Objectives
1. **Consolidate data** into unified, scannable tables
2. **Match UI patterns** from thermodynamic validation refactor
3. **Improve data density** - show more information at once
4. **Add interactivity** - sortable columns, searchable content
5. **Maintain all existing functionality** while improving presentation

### Design Principles
- Use `Gtk.TreeView` + `Gtk.ListStore` for tabular data
- Keep Status Bar and Key Findings (these work well)
- Replace 4 text expanders with 4 table expanders
- Add column sorting, text wrapping, search capabilities
- Use status icons (✓/✗/⏱️/○) in table cells

## Detailed Refactoring Plan

### Phase 1: Structural Analysis Table

**Current Format** (text):
```
✓ 5 P-invariants (80% coverage)
✓ 3 T-invariants (60% coverage)
✓ 2 siphon(s)
✓ 1 trap(s)
```

**New Table Format**:
| Analysis Type | Count | Coverage | Status |
|--------------|-------|----------|--------|
| P-Invariants | 5 | 80% | ✓ |
| T-Invariants | 3 | 60% | ✓ |
| Siphons | 2 | N/A | ✓ |
| Traps | 1 | N/A | ✓ |

**Implementation**:
- `Gtk.ListStore(str, int, str, str)` - Type, Count, Coverage, Status
- 4 columns: Analysis Type, Count, Coverage, Status Icon
- Sortable by Count
- Show "N/A" for analyses without coverage metrics
- Show "○ Not computed" row if analysis not performed

---

### Phase 2: Graph & Network Analysis Table

**Current Format** (text):
```
✓ 12 feedback cycle(s)
✓ 5 hub node(s)
✓ 8 critical path(s)
```

**New Table Format**:
| Feature | Count | Details | Status |
|---------|-------|---------|--------|
| Feedback Cycles | 12 | Detected | ✓ |
| Hub Nodes | 5 | High connectivity | ✓ |
| Critical Paths | 8 | Identified | ✓ |

**Implementation**:
- `Gtk.ListStore(str, int, str, str)` - Feature, Count, Details, Status
- 4 columns: Feature, Count, Details, Status Icon
- Sortable by Count
- Details column can show additional context
- Expandable in future for showing individual cycles/hubs/paths

---

### Phase 3: Behavioral Analysis Table

**Current Format** (text):
```
✓ Bounded
✗ Not live
✓ Deadlock-free
⏱️ Fairness (timeout)
✓ Reachable
```

**New Table Format**:
| Property | Result | Status | Details |
|----------|--------|--------|---------|
| Boundedness | Bounded | ✓ | System tokens limited |
| Liveness | Not Live | ✗ | Some transitions cannot fire |
| Deadlock-Free | Yes | ✓ | No deadlock states |
| Fairness | Timeout | ⏱️ | Analysis exceeded time limit |
| Reachability | Reachable | ✓ | All states accessible |

**Implementation**:
- `Gtk.ListStore(str, str, str, str)` - Property, Result, Status, Details
- 4 columns: Property, Result, Status Icon, Details
- Status icons: ✓ (pass), ✗ (fail), ⏱️ (timeout), ℹ️ (info), ○ (not computed)
- Sortable by Property name
- Details column provides interpretation
- Color-code rows: green (✓), red (✗), yellow (⏱️), gray (○)

---

### Phase 4: Biological Analysis Table

**Current Format** (text):
```
✓ Mass Balance: Passed (all reactions balanced)
✗ Stoichiometry: Invalid
✓ Flux Balance: Feasible
✓ Dependency score: 0.65 (moderate coupling)
✓ Regulatory patterns: 7
⚠️ Thermodynamics: 3 warning(s)
```

**New Table Format**:
| Analysis | Result | Status | Interpretation |
|----------|--------|--------|----------------|
| Mass Balance | Passed | ✓ | All reactions balanced |
| Stoichiometry | Invalid | ✗ | Some reactions have issues |
| Flux Balance | Feasible | ✓ | Solution exists |
| Dependency Score | 0.65 | ✓ | Moderate coupling |
| Regulatory Patterns | 7 found | ✓ | Patterns identified |
| Thermodynamics | 3 warnings | ⚠️ | Check warnings panel |

**Implementation**:
- `Gtk.ListStore(str, str, str, str)` - Analysis, Result, Status, Interpretation
- 4 columns: Analysis, Result, Status Icon, Interpretation
- Sortable by Analysis name
- Status icons match severity
- Interpretation column provides context
- Link to thermodynamic validation category for details

---

## Implementation Details

### Code Structure Changes

#### 1. Update `_build_content()` Method
**Location**: Lines 45-142

**Changes**:
- Keep Status Bar (line 51-55) ✓
- Keep Key Findings frame (line 57-76) ✓
- **Replace** 4 text expanders (lines 78-142) with 4 table expanders:
  - Create `Gtk.ListStore` for each category
  - Create `Gtk.TreeView` with configured columns
  - Add scrolled windows with min/max heights
  - Set up column sorting and search

#### 2. Update Refresh Methods
**Current**: Lines 150-168 (`refresh()`)

**Changes**:
- Keep main `refresh()` logic ✓
- Replace `_update_*_preview()` methods with `_update_*_table()` methods:
  - `_update_structural_preview()` → `_update_structural_table()`
  - `_update_graph_preview()` → `_update_graph_table()`
  - `_update_behavioral_preview()` → `_update_behavioral_table()`
  - `_update_biological_preview()` → `_update_biological_table()`

#### 3. New Table Update Methods

**Add 4 new methods**:
```python
def _update_structural_table(self, stats):
    """Populate structural analysis table."""
    self.structural_store.clear()
    
    # Add rows for P-invariants, T-invariants, Siphons, Traps
    p_inv = stats.get('p_invariants', 0) or 0
    if p_inv > 0:
        coverage = f"{stats.get('p_invariant_coverage', 0):.0%}"
        self.structural_store.append(["P-Invariants", p_inv, coverage, "✓"])
    else:
        self.structural_store.append(["P-Invariants", 0, "N/A", "○"])
    
    # Similar for T-invariants, Siphons, Traps...
```

#### 4. Data Flow
**Keep existing data flow**:
1. Topology Panel → `generate_summary_for_report_panel()`
2. Returns dict with `statistics`, `status`, `warnings`
3. Report Category → `_update_display(summary)`
4. Calls `_update_*_table()` methods to populate tables

### UI Component Specifications

#### Common Table Configuration
```python
# Create store (columns vary by table)
store = Gtk.ListStore(str, int/str, str, str)

# Create tree view
tree = Gtk.TreeView(model=store)
tree.set_enable_search(True)
tree.set_search_column(0)  # Search by first column

# Configure columns with sorting
for i, (title, col_id) in enumerate(columns):
    renderer = Gtk.CellRendererText()
    if title == "Status":
        # Center-align status icons
        renderer.set_property("xalign", 0.5)
    column = Gtk.TreeViewColumn(title, renderer, text=col_id)
    column.set_sort_column_id(col_id)
    column.set_resizable(True)
    if i == len(columns) - 2:  # Details/Interpretation column
        column.set_expand(True)
    tree.append_column(column)

# Add to scrolled window
scroll = Gtk.ScrolledWindow()
scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
scroll.set_min_content_height(150)
scroll.set_max_content_height(300)
scroll.add(tree)
```

#### Status Icon Colors
- ✓ Green (success): Analysis passed/completed
- ✗ Red (error): Analysis failed
- ⚠️ Yellow (warning): Issues detected
- ⏱️ Blue (timeout): Analysis exceeded time limit
- ℹ️ Gray (info): Additional information
- ○ Gray (not computed): Analysis not performed

### Benefits of Table-Based Approach

#### User Experience
1. **Better Overview**: See all results at once without expanding multiple sections
2. **Quick Scanning**: Tabular format easier to scan than text lists
3. **Sorting**: Click column headers to sort by property/count/status
4. **Searching**: Find specific analyses quickly with built-in search
5. **Consistency**: Matches thermodynamic validation UI patterns

#### Maintainability
1. **Cleaner Code**: Replace multiple text manipulation methods with table population
2. **Easier Updates**: Add new analyses as table rows, not new expanders
3. **Scalability**: Tables handle varying data sizes better than text
4. **Testability**: Easier to verify table contents than text parsing

#### Future Enhancements
1. **Row Selection**: Click row to see detailed analysis results
2. **Context Menus**: Right-click for options (re-run, export, etc.)
3. **Drill-Down**: Expand rows to show sub-analyses or details
4. **Export**: Easy to export table data to CSV/Excel
5. **Filtering**: Add filter row to show/hide specific analyses

---

## Migration Strategy

### Step 1: Preserve Existing Functionality
- Keep all data retrieval logic unchanged
- Keep `generate_summary_for_report_panel()` interface
- Maintain backward compatibility with topology panel

### Step 2: Incremental Refactoring
**Option A - All at once** (Recommended):
- Replace all 4 expanders in single commit
- Test thoroughly before committing
- Consistent user experience

**Option B - One category at a time**:
- Start with Structural Analysis table
- Test and verify
- Move to Graph, then Behavioral, then Biological
- Allows gradual testing but inconsistent UI during transition

### Step 3: Testing Checklist
- [ ] All 4 tables display correctly
- [ ] Column sorting works for each table
- [ ] Search functionality works
- [ ] Data updates when topology analyses run
- [ ] Status icons display correctly
- [ ] Tables handle empty data (show "Not computed" rows)
- [ ] Tables handle timeout states
- [ ] Scrolling works for large datasets
- [ ] Layout responsive to window resizing
- [ ] No performance degradation

### Step 4: Polish
- [ ] Adjust column widths for optimal display
- [ ] Fine-tune min/max heights for scrolled windows
- [ ] Add tooltips for status icons
- [ ] Ensure consistent styling across all tables
- [ ] Update documentation/comments

---

## Implementation Checklist

### Phase 1: Structural Analysis Table
- [ ] Create `self.structural_store = Gtk.ListStore(str, int, str, str)`
- [ ] Build TreeView with 4 columns: Type, Count, Coverage, Status
- [ ] Add to scrolled window in expander
- [ ] Implement `_update_structural_table(stats)`
- [ ] Test with real topology analysis data

### Phase 2: Graph & Network Analysis Table
- [ ] Create `self.graph_store = Gtk.ListStore(str, int, str, str)`
- [ ] Build TreeView with 4 columns: Feature, Count, Details, Status
- [ ] Add to scrolled window in expander
- [ ] Implement `_update_graph_table(stats)`
- [ ] Test with real topology analysis data

### Phase 3: Behavioral Analysis Table
- [ ] Create `self.behavioral_store = Gtk.ListStore(str, str, str, str)`
- [ ] Build TreeView with 4 columns: Property, Result, Status, Details
- [ ] Add to scrolled window in expander
- [ ] Implement `_update_behavioral_table(stats)`
- [ ] Test with real topology analysis data

### Phase 4: Biological Analysis Table
- [ ] Create `self.biological_store = Gtk.ListStore(str, str, str, str)`
- [ ] Build TreeView with 4 columns: Analysis, Result, Status, Interpretation
- [ ] Add to scrolled window in expander
- [ ] Implement `_update_biological_table(stats)`
- [ ] Test with real topology analysis data

### Phase 5: Cleanup
- [ ] Remove old `_update_*_preview()` methods
- [ ] Update docstrings to reflect table-based approach
- [ ] Remove unused text manipulation code
- [ ] Test complete workflow: analyze → report refresh
- [ ] Verify export functions still work
- [ ] Update file header comments

---

## Code Size Estimate

### Current File
- Total: 712 lines
- `_build_content()`: ~100 lines (text expanders)
- Preview methods: ~200 lines (4 methods × 50 lines avg)
- Other methods: ~412 lines (unchanged)

### After Refactoring
- Total: ~650 lines (reduced by ~60 lines)
- `_build_content()`: ~200 lines (4 tables with configuration)
- Table update methods: ~120 lines (4 methods × 30 lines avg)
- Other methods: ~330 lines (unchanged/simplified)

**Net Result**: More code in `_build_content()` (tables require setup), but much less in update methods (simpler logic).

---

## Risk Assessment

### Low Risk
- ✓ Data flow unchanged (same input from topology panel)
- ✓ Similar patterns already working in thermodynamic validation
- ✓ No changes to topology panel or analysis logic
- ✓ Easy to revert if needed (single file change)

### Medium Risk
- ⚠️ Need to test all topology analysis types thoroughly
- ⚠️ Some analyses may have edge cases (None, timeout, error states)
- ⚠️ Must handle varying data sizes gracefully

### Mitigation
- Test with multiple models (simple, complex, edge cases)
- Add defensive checks for None/missing data
- Use same patterns that worked for thermodynamic validation
- Keep debug logging during initial rollout

---

## Success Criteria

### Functional Requirements
1. ✓ All topology analysis data displays correctly in tables
2. ✓ Tables are sortable by clicking column headers
3. ✓ Search functionality works for each table
4. ✓ Status icons correctly reflect analysis results
5. ✓ Tables update when topology analyses re-run
6. ✓ Handles edge cases (no data, timeouts, errors)

### Non-Functional Requirements
1. ✓ UI matches thermodynamic validation style
2. ✓ Performance: No lag when loading/refreshing tables
3. ✓ Accessibility: Keyboard navigation works
4. ✓ Responsiveness: Layout adapts to window size
5. ✓ Maintainability: Code is cleaner and more maintainable

### User Experience
1. ✓ Users can quickly scan all topology results
2. ✓ Expanders allow focusing on specific analysis categories
3. ✓ Sorting helps identify important findings
4. ✓ Searching helps locate specific analyses
5. ✓ Overall improvement over text-based display

---

## Timeline Estimate

### Development
- Phase 1 (Structural): 1-2 hours
- Phase 2 (Graph): 1-2 hours
- Phase 3 (Behavioral): 1-2 hours
- Phase 4 (Biological): 1-2 hours
- **Total Development**: 4-8 hours

### Testing
- Unit testing: 2 hours
- Integration testing: 2 hours
- User acceptance testing: 1 hour
- **Total Testing**: 5 hours

### Polish & Documentation
- Code cleanup: 1 hour
- Documentation updates: 1 hour
- **Total Polish**: 2 hours

**Grand Total**: 11-15 hours

---

## Next Steps

1. **Review this plan** with user for approval
2. **Start with Phase 1** (Structural Analysis table)
3. **Test thoroughly** before proceeding
4. **Continue phases 2-4** once pattern is validated
5. **Final testing** across all topology analyses
6. **Deploy** and gather user feedback

---

## Related Files

### Primary File to Modify
- `src/shypn/ui/panels/report/topology_analyses_category.py`

### Reference Files (No Changes Needed)
- `src/shypn/ui/panels/topology/topology_panel.py` (data source)
- `src/shypn/topology/reporting.py` (summary generator)
- `src/shypn/ui/panels/report/thermodynamic_validation_category.py` (reference implementation)

### Testing Files
- Models in `workspace/` directory
- Example SBML files for topology analysis

---

## Conclusion

This refactoring will significantly improve the Topology Analyses report by:
1. Making data more scannable and accessible
2. Adding interactive features (sort, search)
3. Matching the improved thermodynamic validation UI
4. Improving code maintainability and extensibility

The approach is low-risk, follows proven patterns, and delivers substantial UX improvements.
