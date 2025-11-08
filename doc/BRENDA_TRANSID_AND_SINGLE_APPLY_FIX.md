# BRENDA TransID Column & Single Apply Fix

**Date:** 2025-11-06  
**Issue:** TransID column not showing selected transition, single apply not working

---

## Problems Fixed

### 1. TransID Column Empty in Results Table ❌ → ✅ FIXED

**Problem:**
- User right-clicked transition T5 → "Enrich with BRENDA"
- Results table showed all rows with TransID = "N/A"
- User couldn't see which transition the parameters would be applied to

**Root Cause:**
- `_display_results()` was using `param.get('transition_id')` which doesn't exist in single-transition mode
- Only batch queries populate `transition_id` in the param dict

**Solution:**
```python
# Get transition ID from stored context (lines ~1168-1170)
context_transition_id = context.get('transition_id', '')

# Use context transition_id for single queries, param transition_id for batch
trans_id_display = context_transition_id or param.get('transition_name', param.get('transition_id', 'N/A'))

# Display in TreeView column 1
self.results_store.append([
    False,  # Selected
    trans_id_display,  # TransID - now shows "T5" for all rows
    param.get('ec_number', ...),
    ...
])
```

**Result:**
- Single transition query (T5) → All rows show "T5" in TransID column
- Batch query (T5, T6, T7) → Rows show respective transition IDs
- User can clearly see which transition will receive parameters

**Code Location:** `src/shypn/ui/panels/pathway_operations/brenda_category.py`, lines ~1168-1183

---

### 2. Single Apply Not Working ❌ → ✅ FIXED

**Problem:**
- User selected parameters → clicked "Apply Selected to Model"
- For single transition mode, dialog showed hardcoded "T1, T2" options (not real transitions)
- Parameters were never actually applied to the transition
- Rate function remained unchanged

**Root Cause:**
- `_show_apply_dialog()` had TODO comments instead of implementation
- `_apply_parameters_to_transition()` only logged params, didn't apply them
- No integration with `brenda_controller.apply_parameters_to_transition()`

**Solution:**

#### A. Use Enrichment Transition Directly
```python
def _show_apply_dialog(self, selected_params: List[Dict[str, Any]]):
    # Get the enrichment transition (the one user right-clicked to enrich)
    enrichment_transition = getattr(self, '_enrichment_transition', None)
    
    # If we have an enrichment transition, apply directly to it
    if enrichment_transition:
        self._apply_single_transition_parameters(enrichment_transition, selected_params)
        return
    
    # Otherwise, show dialog to select target (fallback for manual queries)
    # ... dialog code with actual transitions from canvas ...
```

**Logic:**
1. If user came from context menu ("Enrich with BRENDA"), we know the target → apply directly
2. If user manually typed EC number, show dialog with real transitions from canvas
3. No more hardcoded "T1, T2" options

#### B. Implement Actual Parameter Application
```python
def _apply_single_transition_parameters(self, transition, params: List[Dict[str, Any]]):
    """Apply selected BRENDA parameters to a single transition."""
    
    # Check override settings (same as batch mode)
    override_kegg = self.override_kegg_checkbox.get_active()
    override_sbml = self.override_sbml_checkbox.get_active()
    
    # Check if we should apply based on data source
    data_source = transition.metadata.get('data_source', 'unknown')
    has_kinetics = transition.metadata.get('has_kinetics', False)
    
    should_apply = False
    if not has_kinetics:
        should_apply = True
    elif data_source == 'kegg_import' and override_kegg:
        should_apply = True
    elif data_source == 'sbml_import' and override_sbml:
        should_apply = True
    
    if not should_apply:
        self._show_status("Enable override to replace existing kinetics", error=True)
        return
    
    # Start enrichment session
    self.brenda_controller.start_enrichment(...)
    
    # Apply parameters using controller (same as batch mode)
    success = self.brenda_controller.apply_parameters_to_transition(
        transition=transition,
        parameters=params,
        override_kegg=override_kegg,
        override_sbml=override_sbml
    )
    
    # Finish enrichment
    self.brenda_controller.finish_enrichment()
    
    # Reset simulation (important!)
    self._reset_simulation_after_parameter_changes()
    
    # Clear highlight
    self._clear_enrichment_highlight()
```

**Features:**
- Uses same logic as batch mode (consistency!)
- Respects override settings (KEGG/SBML checkboxes)
- Checks data_source before applying
- Resets simulation state (critical for correct behavior)
- Clears canvas highlight after applying

**Code Location:** `src/shypn/ui/panels/pathway_operations/brenda_category.py`, lines ~1414-1585

---

## User Workflow Now

### Single Transition Application (Most Common)

```
1. User right-clicks T5 → "Enrich with BRENDA"
2. BRENDA panel opens, T5 highlighted on canvas
3. User searches → Gets 1000 results sorted by relevance
4. Results table shows:
   ┌──────────┬────────┬──────────┬──────┬─────────┬──────┬────────────┬─────────────┬─────────┐
   │ Selected │ TransID│ EC       │ Type │ Value   │ Unit │ Substrate  │ Organism    │ Quality │
   ├──────────┼────────┼──────────┼──────┼─────────┼──────┼────────────┼─────────────┼─────────┤
   │    ☐     │   T5   │ 2.7.1.1  │ Km   │ 0.0520  │ mM   │ D-glucose  │ Homo sapiens│  95%    │
   │    ☐     │   T5   │ 2.7.1.1  │ Km   │ 0.0800  │ mM   │ D-glucose  │ Homo sapiens│  92%    │
   │    ☐     │   T5   │ 2.7.1.1  │ Km   │ 0.1200  │ mM   │ D-glucose  │ Mus musculus│  88%    │
   └──────────┴────────┴──────────┴──────┴─────────┴──────┴────────────┴─────────────┴─────────┘
   
   ↑ All rows show "T5" - user knows these will be applied to T5
   
5. User selects top 2 parameters (best quality)
6. User clicks "Apply Selected to Model"
7. Parameters IMMEDIATELY applied to T5 (no dialog needed!)
8. Simulation state reset (new rate function active)
9. T5 highlight cleared
10. Status shows: "Applied 2 parameters to T5"
```

### Manual Query (No Context Menu)

```
1. User manually types EC "2.7.1.1" in BRENDA panel
2. User clicks "Search" → Gets results
3. Results table shows:
   ┌──────────┬────────┬──────────┬──────┬─────────┐
   │ Selected │ TransID│ EC       │ Type │ Value   │
   ├──────────┼────────┼──────────┼──────┼─────────┤
   │    ☐     │  N/A   │ 2.7.1.1  │ Km   │ 0.0520  │
   └──────────┴────────┴──────────┴──────┴─────────┘
   
   ↑ Shows "N/A" because no specific transition selected
   
4. User selects parameters → Clicks "Apply Selected"
5. Dialog opens with REAL transitions from canvas:
   ┌──────────────────────────────────────┐
   │ Apply BRENDA Parameters              │
   ├──────────────────────────────────────┤
   │ Target Transition: [T5 - Hexokinase▼]│
   │                    [T6 - PGI        ]│
   │                    [T7 - PFK        ]│
   └──────────────────────────────────────┘
   
6. User selects T5 → Clicks "Apply"
7. Parameters applied to T5 (same as context menu mode)
```

---

## Key Improvements

### 1. Visual Clarity ✅
- **Before:** TransID column showed "N/A" → confusion
- **After:** TransID column shows "T5" → crystal clear which transition will be affected

### 2. Workflow Efficiency ✅
- **Before:** Context menu enrichment required extra dialog to select target
- **After:** Direct application when enrichment transition is known (1 less click!)

### 3. Code Consistency ✅
- **Before:** Batch mode worked, single mode was TODO
- **After:** Both modes use same logic (`brenda_controller.apply_parameters_to_transition()`)

### 4. Proper Integration ✅
- **Before:** Parameters "applied" but rate function unchanged
- **After:** Parameters actually written to transition, simulation reset correctly

---

## Technical Details

### Data Flow

```
User: Right-click T5 → "Enrich with BRENDA"
    ↓
context_menu_handler.py:
    transition.selected = True
    brenda_category._enrichment_transition = transition  # Store reference
    brenda_category.set_query_from_transition(transition_id='T5', ...)
    ↓
brenda_category.py set_query_from_transition():
    self._transition_context = {
        'transition_id': 'T5',  # Store for later use
        'organism': 'Homo sapiens',
        'substrates': ['D-glucose'],
        ...
    }
    ↓
User: Searches BRENDA
    ↓
brenda_category.py _display_results():
    context_transition_id = context.get('transition_id', '')  # 'T5'
    for param in results:
        trans_id_display = context_transition_id  # Use 'T5' for all rows
        results_store.append([False, trans_id_display, ...])  # Display 'T5'
    ↓
User: Selects parameters → Clicks "Apply Selected"
    ↓
brenda_category.py _on_apply_selected():
    if has_transition_ids:  # Batch mode
        _apply_batch_parameters()
    else:  # Single mode
        _show_apply_dialog(selected_params)
    ↓
brenda_category.py _show_apply_dialog():
    enrichment_transition = self._enrichment_transition  # T5 object
    if enrichment_transition:
        _apply_single_transition_parameters(enrichment_transition, selected_params)
        return  # No dialog needed!
    ↓
brenda_category.py _apply_single_transition_parameters():
    # Check override settings
    # Check data_source
    # Apply parameters via brenda_controller
    brenda_controller.apply_parameters_to_transition(transition, params)
    # Reset simulation
    _reset_simulation_after_parameter_changes()
    # Clear highlight
    _clear_enrichment_highlight()
```

### Key Variables

```python
# Stored when user right-clicks transition
self._enrichment_transition: Transition  # The actual transition object

# Stored in set_query_from_transition()
self._transition_context: Dict[str, Any] = {
    'transition_id': 'T5',           # Used for TransID column display
    'organism': 'Homo sapiens',      # Used for relevance scoring
    'substrates': ['D-glucose'],     # Used for relevance scoring
    'products': ['G6P']              # Not yet used
}

# Displayed in TreeView column 1
trans_id_display: str = context_transition_id or param.get('transition_id', 'N/A')
```

---

## Testing

### Test Case 1: Single Transition Enrichment
```bash
# Steps:
1. Load model with T5 (Hexokinase)
2. Right-click T5 → "Enrich with BRENDA"
3. Click "Search" (should auto-fill EC 2.7.1.1)
4. Verify: All rows in results show "T5" in TransID column
5. Select top 3 parameters
6. Click "Apply Selected to Model"
7. Verify: No dialog appears (direct application)
8. Verify: Status shows "Applied 3 parameters to T5"
9. Verify: T5 highlight cleared
10. Verify: T5 rate function updated (check kinetics metadata)

# Expected Result: ✅ All steps pass
```

### Test Case 2: Manual Query Then Apply
```bash
# Steps:
1. Load model with T5, T6, T7
2. Open BRENDA panel (don't use context menu)
3. Manually type EC "2.7.1.1" → Click "Search"
4. Verify: All rows show "N/A" in TransID column (no specific target)
5. Select parameters → Click "Apply Selected"
6. Verify: Dialog appears with real transitions: T5, T6, T7
7. Select T6 → Click "Apply"
8. Verify: Parameters applied to T6 (not T5!)
9. Verify: Status shows "Applied X parameters to T6"

# Expected Result: ✅ All steps pass
```

### Test Case 3: Batch Query Mode
```bash
# Steps:
1. Load model with T5, T6, T7
2. Select all 3 transitions
3. Click "Query All" in BRENDA panel
4. Verify: Results show mixed TransID values (T5, T6, T7)
5. Select parameters → Click "Apply Selected"
6. Verify: Batch mode triggered (no dialog, direct application)
7. Verify: Parameters applied to respective transitions

# Expected Result: ✅ All steps pass
```

---

## Files Modified

1. **`src/shypn/ui/panels/pathway_operations/brenda_category.py`**
   - Line ~1168-1183: Fixed TransID column to use context transition_id
   - Line ~1414-1585: Rewrote single apply logic to use enrichment transition
   - Removed TODO comments, implemented actual parameter application

---

## Summary

✅ **TransID Column Fixed**: Shows selected transition ID in all result rows  
✅ **Single Apply Working**: Parameters actually applied to transition  
✅ **Direct Application**: No dialog when enrichment transition is known  
✅ **Code Consistency**: Single and batch modes use same apply logic  
✅ **Proper Integration**: Simulation reset, highlight cleared, status updated  

**Result:** BRENDA single-transition workflow now works correctly! 🎉
