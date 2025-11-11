# Viability Panel - Comprehensive Analysis & Refactor Plan

**Date:** November 10, 2025  
**Status:** WRONG PARADIGM - Needs Major Refactor  
**Priority:** HIGH - Core concept misaligned with purpose

---

## Executive Summary

**CRITICAL REALIZATION:** The Viability Panel was being built as an **issue reporter** (like Report Panel) instead of an **intelligent assistant** that suggests improvements.

### Original Intent (CORRECT):
- **Intelligent Assistant** that learns from KB and suggests model improvements
- **Interactive Mode**: User selects transition → get locality-specific suggestions
- **Batch Mode**: Analyze entire model → get comprehensive suggestions
- **Actionable**: Apply/Preview/Undo suggestions with one click

### What Was Being Built (WRONG):
- Issue detector reporting dead transitions, inactive places
- Statistics dashboard showing problem counts
- Read-only problem list (like Report Panel duplication)

**REFOCUS NEEDED:** Transform from "problem reporter" to "solution suggester"

---

## Architecture Overview

```
ViabilityPanel
├── Statistics Bar (NEW - shows summary)
├── Diagnosis Category (expanded by default)
├── Structural Category (collapsible)
├── Biological Category (collapsible)
└── Kinetic Category (collapsible)

Each category:
- Subscribes to ViabilityObserver for updates
- Receives Issue objects when rules trigger
- Displays issues in ListBox with apply/preview buttons
- Supports locality filtering
```

---

## Critical Issues Found

### 🔴 ISSUE 1: Observer Condition/Action Mismatch

**Location:** `viability_observer.py` lines 106-169

**Problem:** Rule conditions check for keys that don't exist in the knowledge dict.

**Example:**
```python
# Condition checks for 'simulation_data' key
condition=lambda data: 'simulation_data' in data and data['simulation_data'].get('has_data', False)

# But knowledge dict has 'simulation_state' key instead:
self.knowledge = {
    'topology_state': {},
    'simulation_state': {},  # <-- actual key
    'biological_state': {},
    'kinetic_state': {}
}
```

**Evidence from logs:**
```
[OBSERVER] knowledge keys: ['topology_state', 'simulation_state', 'biological_state', 'kinetic_state']
[OBSERVER] simulation_state keys: ['has_data', 'dead_transitions', 'inactive_places', 'zero_firing_transitions', 'total_firings']
[OBSERVER] simulation_state dead_transitions: [39 transitions including T6]
[OBSERVER] Rule 'dead_transitions_from_simulation' (category=structural): condition=False  <-- FAILS!
```

**Fix Applied:** Changed conditions to check `'simulation_state'` instead of `'simulation_data'`.

---

### 🔴 ISSUE 2: Dead Transitions Data Structure Problem

**Location:** `viability_panel.py` lines 355-362

**Problem:** The log shows `dead_transitions` contains string representations of dictionaries instead of simple transition IDs:

```python
# Expected format:
dead_transitions = ['T1', 'T2', 'T6', ...]

# Actual format in logs:
dead_transitions = ["{'transition_id': 'T1', 'label': 'R00710'}", ...]
```

**Impact:** The `_analyze_dead_transitions_simulation()` function expects simple string IDs but receives complex dict-as-string objects.

**Root Cause:** Unknown - need to trace where this transformation happens. Code shows:
```python
if firings == 0:
    simulation_data['dead_transitions'].append(trans_id)  # Should append 'T6'
```

**Status:** NEEDS INVESTIGATION

---

### 🔴 ISSUE 3: Observer Never Triggers Rules

**Location:** `viability_observer.py` lines 310-355

**Problem:** Even after fixing condition keys, observer shows:
```
[OBSERVER] Evaluated 9 rules, 0 triggered
```

**Reasons:**
1. Conditions checking wrong keys (FIXED)
2. Conditions not checking if lists are non-empty (PARTIALLY FIXED)
3. Possible data type mismatch in dead_transitions list (NEEDS FIX)

**Current State:**
- Rules evaluate: ✅
- Conditions pass: ❌ (still failing after key fix)
- Actions execute: ❌ (never reached)
- UI updates: ❌ (no issues to display)

---

### 🟡 ISSUE 4: Statistics Bar Not Updating

**Location:** `viability_panel.py` lines 376-397

**Problem:** Statistics labels added but never show meaningful data during simulation.

**Expected Behavior:**
```
✅ Model Healthy (or ⚠️ 39 Issues Detected)
Transitions: 0/39 active
Total Firings: 0
Issues: 39
```

**Actual Behavior:**
```
No simulation data available
[empty]
[empty]
[empty]
```

**Root Cause:** Statistics update code runs but observer has 0 issues, so displays zeros/empty.

**Fix Needed:** Verify statistics update happens AFTER observer processes simulation_complete event.

---

### 🟡 ISSUE 5: Category Refresh Not Triggering UI Updates

**Location:** `base_category.py` lines 756-782

**Problem:** Observer calls `_on_observer_update(issues)` but categories might not be expanded.

**Code Analysis:**
```python
def _on_observer_update(self, issues):
    self.current_issues = issues
    
    if self.category_frame and self.category_frame.is_expanded():
        GLib.idle_add(self._display_issues, issues)
    else:
        print(f"[VIABILITY_CATEGORY] Not expanded - UI update skipped")
```

**Issue:** If categories are collapsed, issues are stored but never displayed.

**Expected:** Categories should show badge/count even when collapsed (like Report panel does).

**Status:** BY DESIGN - but could be improved with issue count badges.

---

### 🟢 ISSUE 6: Locality Support Not Implemented

**Location:** Multiple category files

**Problem:** Categories inherit locality support from `BaseViabilityCategory` but don't use it.

**Impact:** LOW - Feature not advertised, not blocking core functionality.

**Example:**
```python
def set_selected_locality(self, locality_id):
    """Set selected locality for filtering."""
    self.selected_locality_id = locality_id
    # Refresh if category is expanded
    if self.category_frame and self.category_frame.is_expanded():
        GLib.idle_add(self._refresh)
```

**Status:** FUTURE ENHANCEMENT - needs integration with Analyses panel locality system.

---

## Data Flow Analysis

### Current Flow (BROKEN)

```
1. Simulation Complete
   ↓
2. viability_panel.on_simulation_complete()
   - Extracts simulation data
   - Builds simulation_data dict with dead_transitions
   - ❌ Creates wrong data structure (dict-as-strings)
   ↓
3. observer.record_event('simulation_complete', data)
   ↓
4. observer._update_knowledge(event)
   - Updates self.knowledge['simulation_state']
   - ❌ Stores malformed dead_transitions list
   ↓
5. observer._evaluate_rules()
   - Checks rule conditions
   - ❌ Conditions check wrong keys ('simulation_data' vs 'simulation_state')
   - ❌ Conditions return False even with 39 dead transitions
   ↓
6. observer._notify_subscribers(category, issues)
   - ❌ NEVER REACHED - no issues generated
   ↓
7. category._on_observer_update(issues)
   - ❌ NEVER CALLED - no notification sent
   ↓
8. category._display_issues(issues)
   - ❌ NEVER CALLED - no UI update
```

### Expected Flow (FIXED)

```
1. Simulation Complete
   ↓
2. viability_panel.on_simulation_complete()
   - Extracts simulation data correctly
   - simulation_data['dead_transitions'] = ['T1', 'T2', ..., 'T6', ...]
   ↓
3. observer.record_event('simulation_complete', data)
   ↓
4. observer._update_knowledge(event)
   - self.knowledge['simulation_state'] updated correctly
   ↓
5. observer._evaluate_rules()
   - Checks 'simulation_state' in self.knowledge ✅
   - Finds len(dead_transitions) = 39 ✅
   - Condition passes ✅
   - Calls action function ✅
   ↓
6. observer._analyze_dead_transitions_simulation(knowledge)
   - Reads knowledge['simulation_state']['dead_transitions']
   - Creates Issue objects for each dead transition
   - Returns list of 39 Issue objects
   ↓
7. observer._notify_subscribers('structural', issues)
   - Calls all subscribed callbacks
   ↓
8. structural_category._on_observer_update(issues)
   - Stores issues in self.current_issues
   - Schedules UI update
   ↓
9. structural_category._display_issues(issues)
   - Clears ListBox
   - Creates ListBoxRow for each issue
   - Shows issue title, description, suggestions
   ↓
10. UI Shows 39 issues in Structural Category ✅
```

---

## Root Cause: Dead Transitions String Format

### Investigation Needed

The logs show this bizarre format:
```python
"{'transition_id': 'T1', 'label': 'R00710'}"
```

This suggests somewhere in the code, dictionaries are being converted to strings via `str()` or similar.

### Possible Sources:

1. **KB Transitions Dict Format**
   - Maybe `kb.transitions` doesn't contain simple IDs
   - Need to check what `kb.transitions.keys()` actually returns

2. **Data Collector Issue**
   - Maybe `data_collector.get_transition_series()` modifies trans_id

3. **Observer Update Logic**
   - Maybe `_update_knowledge()` transforms the data

### Debug Steps:

```python
# Add to viability_panel.py line 355:
for trans_id in kb.transitions.keys():
    print(f"[DEBUG] trans_id type: {type(trans_id)}, value: {repr(trans_id)}")
    time_points, firing_counts = data_collector.get_transition_series(trans_id)
    firings = firing_counts[-1] if firing_counts else 0
    print(f"[DEBUG] firings: {firings}, type: {type(firings)}")
    if firings == 0:
        print(f"[DEBUG] Appending to dead_transitions: {repr(trans_id)}")
        simulation_data['dead_transitions'].append(trans_id)
```

---

## Fixes Applied (This Session)

### Fix 1: Observer Condition Keys ✅
Changed rule conditions from `'simulation_data'` to `'simulation_state'`:
- `dead_transitions_from_simulation` rule
- `zero_firing_transitions` rule  
- `inactive_compounds` rule

### Fix 2: Added Non-Empty Checks ✅
Conditions now verify lists are not empty:
```python
condition=lambda data: 'simulation_state' in data 
    and data['simulation_state'].get('has_data', False) 
    and len(data['simulation_state'].get('dead_transitions', [])) > 0
```

### Fix 3: Statistics Bar Added ✅
Created UI elements to display:
- Model health status
- Active/total transitions
- Total firings count
- Total issues count

---

## Fixes Still Needed

### Priority 1: Critical

1. **Fix Dead Transitions Data Format** 🔴
   - Debug why dict-as-strings appear in logs
   - Ensure `simulation_data['dead_transitions']` contains simple strings
   - Verify `kb.transitions.keys()` returns correct format

2. **Verify Observer Triggers** 🔴
   - Test with corrected condition keys
   - Confirm actions generate Issue objects
   - Confirm subscribers receive notifications

3. **Test UI Display** 🔴
   - Expand Structural category
   - Verify issues appear in ListBox
   - Check issue formatting and buttons

### Priority 2: Important

4. **Statistics Bar Values** 🟡
   - Ensure labels update after simulation
   - Show correct counts from observer
   - Handle zero-issues case gracefully

5. **Category Badges** 🟡
   - Add issue count badges when collapsed
   - Make categories visually indicate problems
   - Follow Report panel design pattern

### Priority 3: Enhancements

6. **Locality Integration** 🟢
   - Connect to Analyses panel locality system
   - Filter issues by selected locality
   - Highlight locality-specific problems

7. **Apply/Preview Buttons** 🟢
   - Implement suggestion application
   - Add preview before applying changes
   - Track undo history

---

## Testing Checklist

Once fixes are applied, test this workflow:

1. ✅ Load model with dead transitions (e.g., T6)
2. ✅ Run simulation to completion
3. ✅ Observer processes simulation_complete event
4. ✅ Observer evaluates rules
5. ✅ Observer finds dead transitions (condition passes)
6. ✅ Observer creates Issue objects
7. ✅ Observer notifies subscribers
8. ✅ Categories receive issues
9. ✅ Expand Structural category
10. ✅ See "Dead Transition: T6" in issues list
11. ✅ Statistics bar shows "⚠️ 39 Issues Detected"
12. ✅ Click on issue to see details
13. ✅ Verify suggestions/actions if available

---

## Technical Debt

1. **Observer Event Queue**
   - Currently processes events immediately
   - Could batch for performance
   - No event deduplication

2. **Issue Dataclass Usage**
   - Well-designed but underutilized
   - Suggestion/Change classes not fully leveraged
   - No persistence layer

3. **Category Scan Buttons**
   - Redundant with automatic observer
   - Should be removed or repurposed
   - Confusing UX with observer system

4. **Debug Logging**
   - Excessive print statements
   - Should use proper logging framework
   - Need log levels (DEBUG, INFO, WARNING, ERROR)

---

## Recommendations

### Short Term (This Week)
1. Debug and fix dead_transitions string format issue
2. Test observer with corrected conditions
3. Verify UI updates when categories expanded
4. Add basic error handling to prevent silent failures

### Medium Term (This Month)
1. Implement locality filtering
2. Add issue count badges to categories
3. Clean up debug logging
4. Write unit tests for observer rules

### Long Term (Next Quarter)
1. Implement suggestion application system
2. Add undo/redo for viability changes
3. Integrate with BRENDA for kinetic suggestions
4. Create persistent issue tracking database

---

## Conclusion

**The Viability Panel is architecturally sound but has critical implementation bugs that prevent it from working.** The observer pattern design is good, the category structure makes sense, and the UI layout is clean. The main issues are:

1. **Data key mismatch** (simulation_data vs simulation_state) - FIXED
2. **Dead transitions format corruption** - NEEDS INVESTIGATION  
3. **Lack of integration testing** - NEEDS ADDITION

Once these are resolved, the panel should work as designed. The codebase shows good design patterns and is maintainable with proper documentation.

**Next Steps:** 
1. Add debug logging to find dead_transitions corruption source
2. Run end-to-end test with fixed conditions
3. Document working flow for future developers
