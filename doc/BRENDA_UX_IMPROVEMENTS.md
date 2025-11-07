# BRENDA UX Improvements Summary

**Date:** 2025-01-XX  
**Author:** GitHub Copilot  
**Context:** Enhancing BRENDA integration usability and clarity

---

## Overview

This document summarizes the user experience improvements made to the BRENDA integration in Shypn. These changes address confusion points and make the workflow more intuitive when enriching transitions with kinetic parameters.

---

## Problems Addressed

### 1. Successive Queries Accumulated Results ❌ → ✅ FIXED
**Problem:** When user performed multiple BRENDA queries, results accumulated instead of replacing previous ones, causing confusion.

**Solution:** Added `results_store.clear()` at the **start** of both:
- `_on_search_clicked()` (line ~580)
- `_on_query_all_clicked()` (line ~818)

**Code Location:** `src/shypn/ui/panels/pathway_operations/brenda_category.py`

---

### 2. Transition Selection Kept Old Field Values ❌ → ✅ FIXED
**Problem:** When user selected a different transition via context menu, old EC numbers and reaction names remained, leading to incorrect queries.

**Solution:** Modified `set_query_from_transition()` to clear all query fields **before** populating with new data:
```python
# Clear all query fields first (remove previous transition data)
if hasattr(self, 'ec_entry'):
    self.ec_entry.set_text("")
if hasattr(self, 'reaction_name_entry'):
    self.reaction_name_entry.set_text("")
if hasattr(self, 'organism_entry'):
    self.organism_entry.set_text("")
```

**Code Location:** Lines ~1627-1635

---

### 3. KEGG Reaction IDs Not Recognized ❌ → ✅ FIXED
**Problem:** When transitions had KEGG reaction IDs (e.g., `R00299`), the BRENDA "Search" button remained disabled because it wasn't recognized as a valid query.

**Solution:** Added KEGG reaction ID detection and conversion:
```python
# Detect KEGG reaction IDs (R00754 format)
if reaction_name and re.match(r'^R\d{5}$', reaction_name) and not ec_number:
    ec_number = reaction_name  # Use as EC field for automatic conversion
    kegg_reaction_name = self.kegg_ec_fetcher.fetch_reaction_name(reaction_name)
```

**Features:**
- Pattern: `r'^R\d{5}$'` (e.g., R00299, R00756, R01015)
- Automatic EC number lookup via KEGG REST API
- Automatic reaction name fetching (e.g., "ATP:D-glucose 6-phosphotransferase")

**Code Location:** Lines ~1648-1658

---

### 4. No Guidance for 1000+ Results ❌ → ✅ FIXED
**Problem:** BRENDA often returns 500-6928 results for a query, overwhelming the user with no clear way to choose the best parameters.

**Solution:** Implemented **smart filtering and ranking**:

#### Relevance Scoring (`_calculate_relevance_score()`, lines ~1184-1233)
```python
# Organism match (40% weight)
- Exact match: 1.0
- Partial match: 0.7
- Genus match: 0.5

# Substrate match (30% weight)
- Exact match: 1.0
- Partial match: 0.6

# Citation presence (20% weight)
- Has literature: +0.5 bonus

# Value presence (10% weight)
- Has numeric value: +0.2 bonus
```

#### Combined Scoring (`_display_results()`, lines ~1098-1183)
```python
# Quality score (BRENDADataFilter, 0-100%)
quality_score = self.data_filter.calculate_quality_score(param)

# Relevance score (organism + substrate context, 0-1.0)
relevance_score = self._calculate_relevance_score(param, organism, substrates)

# Combined score (60% quality, 40% relevance)
combined_score = (quality_score * 0.6) + (relevance_score * 0.4)
```

#### Results Sorting
- Results automatically sorted by combined score (best-first)
- Best matches (95% quality, perfect organism/substrate match) appear at top
- Poor matches (15% quality, no context match) appear at bottom

**Code Location:** Lines ~1098-1233

---

### 5. User Confused About Which Transition Is Being Queried ❌ → ✅ FIXED
**Problem:** With 1000+ results visible, users forgot which transition they were enriching, leading to:
- Applying parameters to wrong transitions
- Re-querying the same transition multiple times
- General confusion about workflow state

**Solution:** Implemented **transition ID display + canvas highlighting**:

#### A. Results Header Label
Added prominent label showing active transition:
```python
# Header structure:
selected_trans_label = Gtk.Label()
selected_trans_label.set_markup("<b>Target:</b> <i>T5 (Hexokinase)</i>")
```

**Display format:** `Target: T5 (Hexokinase) | 500 results`

**Code Location:** Lines ~372-390

#### B. Canvas Highlighting
Transition remains selected/highlighted while BRENDA panel is active:
```python
# In context_menu_handler.py (_on_enrich_with_brenda):
transition.selected = True  # Keep highlighted
brenda_category._enrichment_transition = transition  # Store reference

# Trigger canvas redraw to show selection
drawing_area.queue_draw()
```

**Visual Effect:** Blue glow around selected transition (consistent with Shypn's selection style)

**Code Location:** `src/shypn/analyses/context_menu_handler.py`, lines ~286-310

#### C. Auto-Clear Highlight
Selection automatically cleared when user finishes:
```python
def _clear_enrichment_highlight(self):
    """Clear highlight after parameters applied."""
    if self._enrichment_transition:
        self._enrichment_transition.selected = False
        self.selected_trans_label.set_markup("<b>Target:</b> <i>None</i>")
        drawing_area.queue_draw()
```

**Trigger points:**
- User clicks "Apply Selected to Model" (batch or single mode)
- User selects a different transition via context menu
- User manually deselects transition on canvas

**Code Location:** Lines ~1787-1814

---

## Workflow Example

### Before Improvements ❌
```
1. User right-clicks T5 → "Enrich with BRENDA"
2. BRENDA panel opens with fields cleared
3. User searches, gets 1500 results
4. User forgets which transition they selected
5. User applies parameters to wrong transition
6. User searches T6, old T5 data still visible (confusion)
```

### After Improvements ✅
```
1. User right-clicks T5 → "Enrich with BRENDA"
2. BRENDA panel shows: "Target: T5 (Hexokinase)"
3. T5 stays highlighted on canvas (blue glow)
4. Previous T4 query results cleared automatically
5. EC number 2.7.1.1 auto-filled from transition
6. Organism "Homo sapiens" auto-filled from model
7. User searches, gets 1500 results sorted by relevance
8. Best matches (95% quality, organism match) at top
9. User selects top 3 parameters
10. User clicks "Apply Selected" → T5 highlight clears
11. User right-clicks T6 → "Enrich with BRENDA"
12. T5 deselected, T6 highlighted, label shows "Target: T6"
```

---

## Technical Implementation

### Key Files Modified

1. **`src/shypn/ui/panels/pathway_operations/brenda_category.py`**
   - Added `selected_trans_label` in results header (lines ~372-390)
   - Modified `set_query_from_transition()` to update label (lines ~1610-1625)
   - Added `_clear_enrichment_highlight()` helper (lines ~1787-1814)
   - Added clearing logic in `_on_search_clicked()` and `_on_query_all_clicked()`
   - Implemented smart filtering/ranking (lines ~1098-1233)

2. **`src/shypn/analyses/context_menu_handler.py`**
   - Modified `_on_enrich_with_brenda()` to keep transition selected (lines ~286-310)
   - Store transition reference for later clearing
   - Trigger canvas redraw to show selection

3. **`src/shypn/data/kegg_ec_fetcher.py`**
   - Added `fetch_reaction_name()` method (lines ~191-230)
   - Fetches reaction names from KEGG REST API
   - Example: R00299 → "ATP:D-glucose 6-phosphotransferase"

### Data Flow

```
User Action: Right-click T5 → "Enrich with BRENDA"
    ↓
context_menu_handler.py: _on_enrich_with_brenda(transition)
    ↓ Extract: EC number, reaction name, organism
    ↓ Call: brenda_category.set_query_from_transition(...)
    ↓ Set: transition.selected = True
    ↓ Store: _enrichment_transition = transition
    ↓
brenda_category.py: set_query_from_transition(...)
    ↓ Clear: Previous enrichment highlight
    ↓ Clear: All query fields (EC, reaction name, organism)
    ↓ Detect: KEGG reaction ID? (regex r'^R\d{5}$')
    ↓ Fetch: EC numbers + reaction name from KEGG API
    ↓ Update: selected_trans_label.set_markup("Target: T5")
    ↓ Store: _transition_context (organism, substrates, products)
    ↓
User Action: Click "Search" or "Query All"
    ↓
brenda_category.py: _on_search_clicked() or _on_query_all_clicked()
    ↓ Clear: results_store.clear() (remove old results)
    ↓ Query: BRENDA SOAP API
    ↓ Filter: Calculate quality score (BRENDADataFilter)
    ↓ Score: Calculate relevance score (organism + substrate match)
    ↓ Combine: (quality × 0.6) + (relevance × 0.4)
    ↓ Sort: Best matches first
    ↓
brenda_category.py: _display_results(results)
    ↓ Populate: TreeView with sorted results
    ↓ Update: results_count_label.set_markup("500 results")
    ↓
User Action: Select parameters → Click "Apply Selected"
    ↓
brenda_category.py: _on_apply_selected()
    ↓ Apply: Parameters to transitions
    ↓ Call: _clear_enrichment_highlight()
    ↓ Deselect: transition.selected = False
    ↓ Update: selected_trans_label → "Target: None"
    ↓ Redraw: Canvas to remove highlight
```

---

## Testing Recommendations

### Manual Testing Workflow

1. **Test Successive Queries:**
   ```
   - Load model with T5, T6
   - Right-click T5 → "Enrich with BRENDA" → Search
   - Verify: 500 results shown
   - Right-click T6 → "Enrich with BRENDA" → Search
   - Verify: Old T5 results cleared, only T6 results shown
   ```

2. **Test Transition Selection Clearing:**
   ```
   - Right-click T5 (EC 2.7.1.1) → "Enrich with BRENDA"
   - Verify: EC entry shows "2.7.1.1"
   - Right-click T6 (EC 2.7.1.11) → "Enrich with BRENDA"
   - Verify: EC entry shows "2.7.1.11" (not 2.7.1.1)
   ```

3. **Test KEGG Reaction ID Support:**
   ```
   - Create transition T7 with label "R00299"
   - Right-click T7 → "Enrich with BRENDA"
   - Verify: EC entry shows "2.7.1.1" (converted)
   - Verify: Reaction name shows "ATP:D-glucose 6-phosphotransferase"
   - Verify: Search button enabled
   ```

4. **Test Smart Filtering:**
   ```
   - Right-click T5 (Hexokinase, Homo sapiens) → "Enrich with BRENDA"
   - Search → Verify: 1000+ results
   - Check top result: Should have organism "Homo sapiens" or close match
   - Check top result: Should have 90%+ quality score
   - Check bottom results: Should have low quality or no organism match
   ```

5. **Test Transition Highlighting:**
   ```
   - Right-click T5 → "Enrich with BRENDA"
   - Verify: Label shows "Target: T5 (Hexokinase)"
   - Verify: T5 has blue glow on canvas
   - Click "Apply Selected to Model"
   - Verify: T5 glow disappears
   - Verify: Label shows "Target: None"
   ```

6. **Test Highlight Clearing:**
   ```
   - Right-click T5 → "Enrich with BRENDA"
   - Verify: T5 highlighted
   - Right-click T6 → "Enrich with BRENDA"
   - Verify: T5 deselected, T6 highlighted
   - Verify: Label shows "Target: T6"
   ```

### Edge Cases to Test

1. **No Transition Context:**
   ```
   - Manually type EC number "2.7.1.1" in field
   - Click "Search"
   - Verify: Results shown, but no transition label
   - Verify: No canvas highlighting
   ```

2. **Invalid KEGG ID:**
   ```
   - Create transition T8 with label "R99999" (invalid)
   - Right-click T8 → "Enrich with BRENDA"
   - Verify: EC entry shows "R99999" (no conversion)
   - Verify: Search button disabled (invalid EC)
   ```

3. **No KEGG Connection:**
   ```
   - Disconnect from internet
   - Create transition T9 with label "R00299"
   - Right-click T9 → "Enrich with BRENDA"
   - Verify: EC entry shows "R00299" (fallback)
   - Verify: Reaction name empty (API failed)
   - Verify: Warning logged in console
   ```

4. **Batch Query Mode:**
   ```
   - Select 5 transitions → Click "Query All"
   - Verify: Previous results cleared
   - Verify: Results show multiple transition IDs in "TransID" column
   - Verify: No specific transition highlighted (batch mode)
   ```

---

## Future Enhancements

### Potential Improvements

1. **Advanced Filtering UI:**
   - Add organism filter dropdown (show available organisms from results)
   - Add substrate filter checkboxes
   - Add quality threshold slider (e.g., "Show only 80%+ quality")

2. **Parameter Comparison:**
   - Side-by-side comparison table for multiple parameters
   - Statistical summary (mean, median, range for Km values)
   - Outlier detection (highlight values 2σ from mean)

3. **Context-Aware Defaults:**
   - Auto-detect organism from model metadata (SBML annotation)
   - Auto-detect substrates from connected places
   - Pre-filter results based on detected context

4. **Enrichment History:**
   - Show previous BRENDA queries for this transition
   - "Undo Apply" button to revert to previous parameters
   - Session log showing all enrichments performed

5. **Visual Feedback:**
   - Color-code transitions by enrichment status:
     - Green: Has BRENDA parameters
     - Orange: Has KEGG parameters (might override)
     - Red: No kinetic data
   - Show parameter source badge on transition (BRENDA icon)

6. **Batch Enrichment Workflow:**
   - Select multiple transitions on canvas
   - Right-click → "Batch Enrich with BRENDA"
   - Single query dialog, apply to all selected
   - Progress bar showing enrichment status per transition

---

## References

### Related Documentation

- **BRENDA Integration:** `doc/BRENDA_DATABASE_INTEGRATION.md`
- **KEGG Integration:** `doc/KEGG_EC_FETCHER.md`
- **Quality Scoring:** `doc/BRENDA_DATA_FILTER.md`
- **Context Menu:** `doc/BRENDA_CONTEXT_MENU.md`

### Code Locations

- **BRENDA Panel:** `src/shypn/ui/panels/pathway_operations/brenda_category.py`
- **Context Handler:** `src/shypn/analyses/context_menu_handler.py`
- **KEGG Fetcher:** `src/shypn/data/kegg_ec_fetcher.py`
- **Data Filter:** `src/shypn/data/brenda_data_filter.py`

### Testing Files

- **Transition Clearing Test:** `dev/test_brenda_transition_clearing.py`
- **Context Menu Test:** `tests/diagnostic/test_brenda_context_menu.py`
- **KEGG Integration Test:** `tests/diagnostic/test_kegg_ec_fetcher.py`

---

## Summary

All UX improvements successfully implemented:

✅ Successive queries clear previous results  
✅ Transition selection clears old field values  
✅ KEGG reaction IDs automatically recognized and converted  
✅ Reaction names automatically fetched from KEGG API  
✅ Smart filtering ranks results by relevance + quality  
✅ Transition ID prominently displayed in results header  
✅ Selected transition highlighted on canvas during enrichment  
✅ Highlight automatically cleared after parameters applied  

**Result:** BRENDA workflow now clear, intuitive, and confusion-free! 🎉
