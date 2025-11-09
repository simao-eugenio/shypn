# Report Panel - Topology Analyses Refactor Plan

**Date:** November 9, 2025  
**Branch:** report-topology  
**Purpose:** Align Report Panel's TopologyAnalysesCategory with new grouped tables architecture

---

## Current State Analysis

### Topology Panel (Source of Truth)
✅ **Status:** Fully implemented with grouped tables

**Architecture:**
- 4 categories with 12 analyzers total:
  - **StructuralCategory:** P/T-Invariants, Siphons, Traps (3 analyzers)
  - **GraphNetworkCategory:** Cycles, Paths, Hubs (3 analyzers)
  - **BehavioralCategory:** Boundedness, Fairness, Deadlocks, Liveness, Reachability (5 analyzers)
  - **BiologicalCategory:** Dependency & Coupling, Regulatory Structure (1 analyzer combined)

**Data Flow:**
```python
TopologyPanel.get_all_results() → Dict[analyzer_name, AnalysisResult]
TopologyPanel.generate_summary_for_report_panel() → Summary dict
```

**Summary Format:**
```python
{
    'category': 'Topology',
    'status': 'complete'/'partial'/'error'/'not_analyzed',
    'summary_lines': ['Short summary strings'],
    'statistics': {
        'p_invariants': int,
        't_invariants': int,
        'cycles': int,
        'hubs': int,
        'is_live': bool,
        'is_bounded': bool,
        'is_deadlock_free': bool,
        # ... etc
    },
    'formatted_text': 'Pre-formatted display text',
    'warnings': ['Warning messages']
}
```

---

### Report Panel TopologyAnalysesCategory (Legacy)
❌ **Status:** Outdated architecture

**Current Structure:**
- 4 sub-expanders with old naming:
  1. **Topology Analysis** → Should be "Structural Analysis"
  2. **Locality Analysis** → Should be "Graph & Network Analysis"
  3. **Source-Sink Analysis** → Should be "Behavioral Analysis"
  4. **Structural Invariants** → Duplicate of #1 (confusion)

**Problems:**
1. ❌ **Naming Mismatch:** Sub-expanders don't match Topology Panel's 4 categories
2. ❌ **Incorrect Mapping:** Logic tries to map old names to new data incorrectly
3. ❌ **Duplicate Content:** "Topology Analysis" and "Structural Invariants" overlap
4. ❌ **Missing Category:** No "Biological Analysis" section
5. ❌ **Hardcoded Placeholders:** Uses TODO comments instead of real data flow
6. ❌ **Confusion:** "Locality" and "Source-Sink" don't match any Topology category

---

## Refactor Goals

### 1. Architectural Alignment
**Match Report Panel structure to Topology Panel's 4 categories:**
- Structural Analysis (P/T-Invariants, Siphons, Traps)
- Graph & Network Analysis (Cycles, Paths, Hubs)
- Behavioral Analysis (Boundedness, Fairness, Deadlocks, Liveness, Reachability)
- Biological Analysis (Dependency & Coupling, Regulatory Structure)

### 2. Data Flow Integration
**Establish clean connection between panels:**
```
Topology Panel (12 analyzers)
    ↓ generate_summary_for_report_panel()
    ↓ returns summary dict
Report Panel (4 sub-expanders)
    ↓ display categorized summaries
User sees organized results
```

### 3. Summary Display Design
**Each sub-expander shows:**
- **Summary Label:** Quick overview (✓/✗/⏱️/○ status indicators)
- **Detailed Expander:** Full metrics and results
- **Export Support:** Include in text export

---

## Detailed Refactor Plan

### Phase 1: Rename Sub-Expanders (CRITICAL)
**File:** `topology_analyses_category.py`

**Changes:**
```python
# OLD NAME → NEW NAME
self.topology_expander      → self.structural_expander
self.locality_expander      → self.graph_network_expander
self.sourcesink_expander    → self.behavioral_expander
self.invariants_expander    → self.biological_expander
```

**Impact:** Aligns UI labels with actual Topology Panel categories

---

### Phase 2: Update Content Creation Methods
**Replace old logic with category-aligned methods:**

#### 2.1 Structural Analysis (P/T-Invariants, Siphons, Traps)
```python
def _create_structural_content(self):
    """Display P/T-Invariants, Siphons, Traps results."""
    # Summary: "✓ 5 P-invariants, 3 T-invariants, 2 siphons, 1 trap"
    # Details: Expandable table/list of each
```

**Data Source:** `statistics['p_invariants']`, `statistics['t_invariants']`, etc.

---

#### 2.2 Graph & Network Analysis (Cycles, Paths, Hubs)
```python
def _create_graph_network_content(self):
    """Display Cycles, Paths, Hubs results."""
    # Summary: "✓ 3 cycles detected, 5 hubs, 12 critical paths"
    # Details: Expandable cycle/path/hub lists
```

**Data Source:** `statistics['cycles']`, `statistics['hubs']`, `statistics['paths']`

---

#### 2.3 Behavioral Analysis (All 5 Properties)
```python
def _create_behavioral_content(self):
    """Display Boundedness, Fairness, Deadlocks, Liveness, Reachability."""
    # Summary: "✓ Bounded | ✗ Not Live | ⏱️ Reachability timeout"
    # Details: Matrix table with property results
```

**Data Source:** `statistics['is_bounded']`, `statistics['is_live']`, etc.

**Special:** Show timeout indicators (⏱️) for algorithms that didn't complete

---

#### 2.4 Biological Analysis (Dependency & Regulatory)
```python
def _create_biological_content(self):
    """Display Dependency & Coupling, Regulatory Structure."""
    # Summary: "✓ Dependency score: 0.45 | Regulatory patterns: 3"
    # Details: Dependency matrix, regulatory network info
```

**Data Source:** `statistics['dependency_score']`, `statistics['regulatory_patterns']`

---

### Phase 3: Update Data Fetching Logic

#### 3.1 Update `_update_with_summary()` Method
**Replace old mapping logic:**

```python
def _update_with_summary(self, summary):
    """Update UI with real topology summary data."""
    status = summary.get('status', 'unknown')
    statistics = summary.get('statistics', {})
    warnings = summary.get('warnings', [])
    
    # Update overall summary (status emoji + summary lines)
    self._update_overall_summary(summary)
    
    # Update each category with correct data
    self._update_structural_section(statistics)      # P/T-Inv, Siphons, Traps
    self._update_graph_network_section(statistics)   # Cycles, Paths, Hubs
    self._update_behavioral_section(statistics)      # 5 behavioral properties
    self._update_biological_section(statistics)      # Dependency, Regulatory
```

---

#### 3.2 Implement New Update Methods
**Each method maps statistics to correct UI elements:**

```python
def _update_structural_section(self, statistics):
    """Update structural analysis with P/T-Inv, Siphons, Traps."""
    p_inv = statistics.get('p_invariants', 0)
    t_inv = statistics.get('t_invariants', 0)
    siphons = statistics.get('siphons', 0)
    traps = statistics.get('traps', 0)
    
    summary = f"Structural: ✓ {p_inv} P-inv, {t_inv} T-inv, {siphons} siphons, {traps} traps"
    self.structural_summary_label.set_text(summary)
    
    details = f"P-Invariants: {p_inv}\nT-Invariants: {t_inv}\nSiphons: {siphons}\nTraps: {traps}"
    self.structural_buffer.set_text(details)
```

**Repeat for graph_network, behavioral, biological sections.**

---

### Phase 4: Handle Timeouts and Errors

#### 4.1 Timeout Indicators
**Show ⏱️ for timed-out analyses:**

```python
def _format_property_status(self, property_name, value):
    """Format property with status indicator.
    
    Returns:
        - "✓ Property" if True
        - "✗ Property" if False
        - "⏱️ Property (timeout)" if None/timeout
        - "○ Property (not run)" if missing
    """
    if value is True:
        return f"✓ {property_name}"
    elif value is False:
        return f"✗ {property_name}"
    elif value == "timeout":
        return f"⏱️ {property_name} (timeout)"
    else:
        return f"○ {property_name} (not run)"
```

---

#### 4.2 Partial Results Display
**Handle incomplete analysis runs:**

```python
if status == 'partial':
    # Show what completed + what didn't
    summary_text += "\n⚠️  Some analyses incomplete or timed out"
```

---

### Phase 5: Export Update

#### 5.1 Update `export_to_text()` Method
**Align export with new 4-category structure:**

```python
def export_to_text(self):
    """Export as plain text with correct category names."""
    text = ["# TOPOLOGY ANALYSES\n"]
    
    # Add overall status
    text.append("## Overall Status")
    text.append(self.overall_summary_label.get_text())
    text.append("")
    
    # Export each expanded category
    if self.structural_expander.get_expanded():
        text.append("## Structural Analysis")
        text.append(self.structural_summary_label.get_text())
        text.append(self.structural_buffer.get_text(...))
        text.append("")
    
    # ... repeat for graph_network, behavioral, biological
    
    return "\n".join(text)
```

---

## Implementation Checklist

### Step 1: Rename Variables and UI Labels ✅
- [ ] Rename `topology_expander` → `structural_expander`
- [ ] Rename `locality_expander` → `graph_network_expander`
- [ ] Rename `sourcesink_expander` → `behavioral_expander`
- [ ] Rename `invariants_expander` → `biological_expander`
- [ ] Update expander labels to match
- [ ] Update all associated variables (summary_label, buffer, textview)

### Step 2: Rewrite Content Creation Methods ✅
- [ ] `_create_structural_content()` - P/T-Inv, Siphons, Traps
- [ ] `_create_graph_network_content()` - Cycles, Paths, Hubs
- [ ] `_create_behavioral_content()` - 5 behavioral properties
- [ ] `_create_biological_content()` - Dependency, Regulatory

### Step 3: Update Data Mapping Logic ✅
- [ ] `_update_with_summary()` - Route to correct update methods
- [ ] `_update_structural_section()` - Map structural statistics
- [ ] `_update_graph_network_section()` - Map graph statistics
- [ ] `_update_behavioral_section()` - Map behavioral statistics
- [ ] `_update_biological_section()` - Map biological statistics

### Step 4: Handle Special Cases ✅
- [ ] Add timeout detection (⏱️ indicator)
- [ ] Add partial results handling (⚠️ indicator)
- [ ] Add error handling (❌ indicator)
- [ ] Update placeholder logic

### Step 5: Update Export ✅
- [ ] Rewrite `export_to_text()` with new category names
- [ ] Ensure all 4 categories are exported correctly

### Step 6: Testing ✅
- [ ] Test with no analyses (placeholder display)
- [ ] Test with partial analyses (some complete, some not)
- [ ] Test with timeouts (show ⏱️ correctly)
- [ ] Test with all analyses complete (show ✓)
- [ ] Test export functionality

---

## Expected Benefits

### 1. **Consistency**
✅ Report Panel matches Topology Panel's category structure  
✅ User sees same 4 categories in both places  
✅ No confusion about "Locality" vs "Graph Analysis"

### 2. **Accuracy**
✅ Data correctly mapped from Topology Panel to Report Panel  
✅ No duplicate sections (old "Topology" + "Invariants" both showing P/T-Inv)  
✅ All 12 analyzers represented in correct categories

### 3. **Completeness**
✅ Biological Analysis section added (was missing)  
✅ All 5 behavioral properties displayed (not just 3)  
✅ Timeout indicators show which analyses didn't complete

### 4. **Usability**
✅ Clear status at top (Overall Summary)  
✅ Expandable sub-sections for details  
✅ Export includes all categories  
✅ Status indicators (✓/✗/⏱️/○) provide quick visual feedback

---

## Risk Assessment

### Low Risk ✅
- Renaming variables (internal only, no API changes)
- UI label updates (improves clarity)
- Export method rewrite (backward compatible)

### Medium Risk ⚠️
- Data mapping changes (need to test all statistics keys)
- Placeholder logic update (ensure no regression)

### Mitigation ✅
- Test with real Topology Panel data
- Verify all 12 analyzers map correctly
- Keep backward compatibility for missing statistics keys

---

## Timeline Estimate

**Total Effort:** ~2-3 hours

- **Phase 1:** 30 minutes (renaming)
- **Phase 2:** 45 minutes (content creation rewrite)
- **Phase 3:** 45 minutes (data mapping logic)
- **Phase 4:** 30 minutes (special cases)
- **Phase 5:** 15 minutes (export update)
- **Phase 6:** 30 minutes (testing)

---

## Success Criteria

✅ **Report Panel shows 4 categories matching Topology Panel:**
1. Structural Analysis
2. Graph & Network Analysis
3. Behavioral Analysis
4. Biological Analysis

✅ **All 12 analyzers correctly displayed in their categories**

✅ **Status indicators work:**
- ✓ for completed
- ✗ for failed
- ⏱️ for timeout
- ○ for not run

✅ **Export includes all 4 categories with correct names**

✅ **No regressions in existing functionality**

---

## Next Steps

1. **Implement Phase 1-5** on report-topology branch
2. **Test thoroughly** with real Topology Panel data
3. **Document changes** in commit messages
4. **Merge to main** when verified working
5. **Update user documentation** to reflect new category names

---

## Notes

- This refactor is **non-breaking** - only changes internal mapping and UI labels
- **No API changes** to `generate_summary_for_report_panel()` - it already returns correct data
- **Backward compatible** - handles missing statistics keys gracefully
- **Aligns with completed topology-analyses work** from earlier today

---

**Author:** GitHub Copilot  
**Review Status:** Ready for implementation  
**Approval Required:** User confirmation before proceeding
