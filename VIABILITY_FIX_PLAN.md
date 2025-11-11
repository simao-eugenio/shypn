# Viability Panel - Refactor Implementation Plan

**Date:** November 10, 2025  
**Objective:** Transform from issue reporter to intelligent assistant  
**Estimated Time:** 4-5 hours  
**Priority:** CRITICAL - Wrong paradigm being implemented

---

## REVISED APPROACH

### What Changed:
- **OLD GOAL:** Fix data flow to detect and report issues
- **NEW GOAL:** Build intelligent assistant that suggests improvements

### Why This Matters:
- Report Panel already reports issues ✅
- Topology Panel already shows structural problems ✅
- Viability Panel should **SUGGEST SOLUTIONS**, not report problems ❌

---

## Phase 1: Architecture Cleanup (30 minutes)

### Step 1.1: Run Debug Session
**Action:** Start app with debug logging and capture full output

```bash
cd /home/simao/projetos/shypn
python src/shypn.py 2>&1 | tee /tmp/viability_debug_full.log
```

**What to do:**
1. Load model
2. Run simulation to completion
3. Note exact line counts for each debug section

**Look for:**
- `[VIABILITY_DEBUG]` lines showing trans_id format
- `[OBSERVER_DEBUG]` lines showing received data
- Any type mismatches or string conversions

### Step 1.2: Identify Data Corruption Point
**Expected output:**
```
[VIABILITY_DEBUG] trans_id #0: type=<class 'str'>, repr='T1', str=T1
```

**If corrupted:**
```
[VIABILITY_DEBUG] trans_id #0: type=<class 'str'>, repr="{'transition_id': 'T1', ...}"
```

**Action based on result:**
- ✅ If clean: Problem is in observer update logic
- ❌ If corrupted: Problem is in KB transitions dict

---

## Phase 2: Fix Data Structure (45 minutes)

### Fix 2.1: Clean KB Transitions Keys

**If KB returns wrong format:**

**File:** `src/shypn/viability/knowledge/knowledge_base.py`

**Investigate:**
```python
# Check how transitions are stored
class ModelKnowledgeBase:
    def __init__(self):
        self.transitions = {}  # What's the key format?
```

**Possible fixes:**

**Option A:** KB stores correct format, viability_panel reads wrong
```python
# In viability_panel.py
for trans_id in kb.transitions.keys():
    # Ensure trans_id is string
    trans_id_str = str(trans_id) if not isinstance(trans_id, str) else trans_id
    # Or extract if it's an object:
    trans_id_str = trans_id if isinstance(trans_id, str) else trans_id.id
```

**Option B:** KB stores objects as keys (wrong)
```python
# In knowledge_base.py - fix how transitions are added
self.transitions[transition.id] = transition  # Use ID as key, not object
```

### Fix 2.2: Observer Update Logic

**File:** `src/shypn/ui/panels/viability/viability_observer.py` line 233

**Current code:**
```python
sim_data = event.data.get('simulation_data', {})
self.knowledge['simulation_state'].update(sim_data)
```

**If sim_data has wrong format, sanitize before storing:**
```python
sim_data = event.data.get('simulation_data', {})

# Sanitize dead_transitions list
if 'dead_transitions' in sim_data:
    # Ensure all items are strings, not dicts or objects
    clean_list = []
    for item in sim_data['dead_transitions']:
        if isinstance(item, str):
            # If it looks like a dict string, parse it
            if item.startswith("{'transition_id':"):
                import ast
                try:
                    parsed = ast.literal_eval(item)
                    clean_list.append(parsed['transition_id'])
                except:
                    clean_list.append(item)
            else:
                clean_list.append(item)
        elif isinstance(item, dict):
            clean_list.append(item.get('transition_id', str(item)))
        else:
            clean_list.append(str(item))
    
    sim_data['dead_transitions'] = clean_list

# Same for zero_firing_transitions
if 'zero_firing_transitions' in sim_data:
    sim_data['zero_firing_transitions'] = [
        item if isinstance(item, str) else str(item)
        for item in sim_data['zero_firing_transitions']
    ]

# Same for inactive_places
if 'inactive_places' in sim_data:
    sim_data['inactive_places'] = [
        item if isinstance(item, str) else str(item)
        for item in sim_data['inactive_places']
    ]

self.knowledge['simulation_state'].update(sim_data)
```

---

## Phase 3: Fix Observer Rules (30 minutes)

### Fix 3.1: Verify Condition Changes Applied

**File:** `src/shypn/ui/panels/viability/viability_observer.py`

**Verify these lines exist:**

Line ~109:
```python
condition=lambda data: 'simulation_state' in data 
    and data['simulation_state'].get('has_data', False) 
    and len(data['simulation_state'].get('dead_transitions', [])) > 0,
```

Line ~132:
```python
condition=lambda data: 'simulation_state' in data 
    and data['simulation_state'].get('has_data', False) 
    and len(data['simulation_state'].get('zero_firing_transitions', [])) > 0,
```

Line ~165:
```python
condition=lambda data: 'simulation_state' in data 
    and data['simulation_state'].get('has_data', False) 
    and len(data['simulation_state'].get('inactive_places', [])) > 0,
```

**If not, apply the fixes from earlier in session.**

### Fix 3.2: Add Debug to Action Functions

**File:** `src/shypn/ui/panels/viability/viability_observer.py`

**Add to `_analyze_dead_transitions_simulation()` at line ~440:**
```python
def _analyze_dead_transitions_simulation(self, knowledge: Dict) -> List:
    """Analyze dead transitions from simulation data."""
    from .viability_dataclasses import Issue
    issues = []
    
    sim_data = knowledge.get('simulation_state', {})
    dead_transitions = sim_data.get('dead_transitions', [])
    
    print(f"[OBSERVER_ACTION] _analyze_dead_transitions_simulation called")
    print(f"[OBSERVER_ACTION] dead_transitions count: {len(dead_transitions)}")
    print(f"[OBSERVER_ACTION] First 3 items: {dead_transitions[:3]}")
    
    for trans_id in dead_transitions:
        print(f"[OBSERVER_ACTION] Creating issue for: {repr(trans_id)}")
        issue = Issue(
            id=f"dead_transition_simulation_{trans_id}",
            category="structural",
            severity="critical",
            title=f"Dead Transition (Simulation): {trans_id}",
            description=f"Transition {trans_id} never fired during simulation. "
                        "Check preconditions, rates, or initial marking.",
            element_id=trans_id,
            element_type="transition",
            metadata={'source': 'simulation', 'firings': 0}
        )
        issues.append(issue)
    
    print(f"[OBSERVER_ACTION] Generated {len(issues)} issues")
    return issues
```

---

## Phase 4: Fix UI Display (30 minutes)

### Fix 4.1: Verify Category Subscription

**File:** `src/shypn/ui/panels/viability/viability_panel.py` lines ~149-152

**Verify:**
```python
self.observer.subscribe('structural', self.structural_category._on_observer_update)
self.observer.subscribe('biological', self.biological_category._on_observer_update)
self.observer.subscribe('kinetic', self.kinetic_category._on_observer_update)
self.observer.subscribe('diagnosis', self.diagnosis_category._on_observer_update)
```

### Fix 4.2: Force Category Expansion for Testing

**Temporary fix to see issues immediately:**

**File:** `src/shypn/ui/panels/viability/viability_panel.py` lines ~170-180

**Change:**
```python
# Create 4 inference categories
self.structural_category = StructuralCategory(
    model_canvas=self.model_canvas,
    expanded=True  # ← Change to True for testing
)

self.biological_category = BiologicalCategory(
    model_canvas=self.model_canvas,
    expanded=True  # ← Change to True for testing
)

self.kinetic_category = KineticCategory(
    model_canvas=self.model_canvas,
    expanded=True  # ← Change to True for testing
)
```

### Fix 4.3: Add Debug to Category Update

**File:** `src/shypn/ui/panels/viability/base_category.py` line ~756

**Add more logging:**
```python
def _on_observer_update(self, issues):
    """Callback for observer updates."""
    print(f"[CATEGORY_UPDATE] ========== _on_observer_update() CALLED ==========")
    print(f"[CATEGORY_UPDATE] Category: {self.__class__.__name__}")
    print(f"[CATEGORY_UPDATE] Received {len(issues)} issues")
    print(f"[CATEGORY_UPDATE] Issues: {[issue.title for issue in issues[:3]]}")
    print(f"[CATEGORY_UPDATE] Expanded: {self.category_frame.is_expanded() if self.category_frame else 'N/A'}")
    
    # Update the category with new issues
    self.current_issues = issues
    
    # Update UI if category is expanded
    if self.category_frame and self.category_frame.is_expanded():
        print(f"[CATEGORY_UPDATE] Scheduling UI update via GLib.idle_add...")
        GLib.idle_add(self._display_issues, issues)
    else:
        print(f"[CATEGORY_UPDATE] Not expanded - UI update skipped")
```

---

## Phase 5: Test & Verify (30 minutes)

### Test 5.1: End-to-End Test

**Steps:**
1. Start app with clean logs
2. Load test model (with T6, P17 issues)
3. Run simulation to completion
4. Check Viability Panel

**Expected Results:**

**Console Output:**
```
[VIABILITY_DEBUG] Total dead transitions: 39
[OBSERVER_DEBUG] dead_transitions length: 39
[OBSERVER] Rule 'dead_transitions_from_simulation': condition=True
[OBSERVER_ACTION] Creating issue for: 'T1'
[OBSERVER_ACTION] Creating issue for: 'T6'
[OBSERVER_ACTION] Generated 39 issues
[OBSERVER] Notifying subscribers for category 'structural'...
[CATEGORY_UPDATE] Received 39 issues
[CATEGORY_UPDATE] Scheduling UI update via GLib.idle_add...
```

**UI Display:**
- Statistics bar shows: "⚠️ 39 Issues Detected"
- Structural category shows issues list
- Each issue has title, description, severity icon

### Test 5.2: Verify Each Issue Type

**Test structural issues:**
- Expand Structural category
- See "Dead Transition (Simulation): T6"
- See "Dead Transition (Simulation): T1"
- Count should match 39 total

**Test kinetic issues:**
- Expand Kinetic category  
- See "Zero Firings: T6"
- Same transitions as structural but different category

**Test biological issues:**
- Expand Biological category
- See "Inactive Compound: P17"
- Check for places that never changed tokens

### Test 5.3: Verify Statistics

**Check statistics bar:**
- Status: ⚠️ or ✅ based on issues
- Transitions: "0/39 active" (or actual count)
- Total Firings: Should show simulation total
- Issues: Should show 39 (or sum across categories)

---

## Phase 6: Cleanup (15 minutes)

### Cleanup 6.1: Remove Debug Logging

**Once everything works, remove or reduce debug output:**

**Keep essential logs:**
- Observer rule evaluation counts
- Issues generated counts
- Category update notifications

**Remove verbose logs:**
- Type checking for each transition
- First 3 items printing
- Detailed data structure dumps

### Cleanup 6.2: Reset Category Expansion

**Revert temporary testing changes:**

```python
self.structural_category = StructuralCategory(
    model_canvas=self.model_canvas,
    expanded=False  # ← Back to False
)
```

### Cleanup 6.3: Update Documentation

**Files to update:**
- `VIABILITY_PANEL_ANALYSIS.md` - Mark issues as FIXED
- `VIABILITY_FIX_PLAN.md` - Add "COMPLETED" section
- Create `VIABILITY_TESTING_GUIDE.md` for future testing

---

## Rollback Plan

If fixes cause crashes or worse behavior:

### Rollback Steps:

1. **Revert condition changes:**
```bash
git diff src/shypn/ui/panels/viability/viability_observer.py
# Manually revert lines 106-169 if needed
```

2. **Revert debug logging:**
```bash
git checkout src/shypn/ui/panels/viability/viability_panel.py
git checkout src/shypn/ui/panels/viability/base_category.py
```

3. **Remove statistics bar if causing issues:**
```python
# Comment out _build_statistics_bar() call in _build_header()
```

### Safety Commits:

**After Phase 2:**
```bash
git add -A
git commit -m "WIP: Viability Panel - Fix data structure issues"
```

**After Phase 4:**
```bash
git add -A
git commit -m "WIP: Viability Panel - Fix observer and UI updates"
```

**After Phase 6:**
```bash
git add -A
git commit -m "Fix: Viability Panel fully functional - Issues #1-6 resolved"
```

---

## Success Criteria

### Must Have (Phase 1-4):
- ✅ Observer detects dead transitions
- ✅ Observer creates Issue objects
- ✅ Observer notifies category subscribers
- ✅ Categories display issues in UI
- ✅ At least one issue visible for T6

### Should Have (Phase 5):
- ✅ All 39 dead transitions listed
- ✅ Issues categorized correctly (structural/kinetic/biological)
- ✅ Statistics bar shows correct counts
- ✅ UI responsive and no crashes

### Nice to Have (Phase 6):
- ✅ Clean logs (no debug spam)
- ✅ Professional UI appearance
- ✅ Documentation updated
- ✅ Testing guide created

---

## Known Limitations

After these fixes, the following will still need work:

1. **Locality filtering** - Not implemented
2. **Apply/Preview buttons** - Not functional
3. **Suggestion generation** - Only basic issues, no suggestions
4. **BRENDA integration** - Kinetic suggestions not pulling real data
5. **Undo/Redo** - No change tracking

These are **future enhancements**, not blocking bugs.

---

## Next Steps After Fixes

### Immediate (This Week):
1. Test with multiple models
2. Verify memory doesn't leak with many issues
3. Check performance with large models (100+ transitions)
4. Add basic error handling

### Short Term (Next Sprint):
1. Implement locality filtering
2. Add issue count badges to collapsed categories
3. Make apply buttons functional
4. Add unit tests for observer rules

### Medium Term (Next Month):
1. Integrate BRENDA API for kinetic suggestions
2. Implement undo/redo system
3. Add issue persistence (save/load)
4. Create suggestion ranking algorithm

---

## Questions to Answer During Debugging

1. **What is the exact type returned by `kb.transitions.keys()`?**
   - Expected: `dict_keys(['T1', 'T2', ...])`
   - Need to verify with debug output

2. **Where do dict-as-strings appear?**
   - In viability_panel before sending to observer?
   - In observer during update?
   - In observer during rule evaluation?

3. **Why do conditions still return False after key fix?**
   - Are the fixes actually applied?
   - Is there a code path we're missing?
   - Is the knowledge dict structure different than expected?

4. **Do categories have the correct subscriber callbacks?**
   - Are they registered correctly?
   - Do the callbacks have correct signatures?
   - Are they being called at all?

---

## Timeline

### Day 1 (Today):
- **09:00-09:30** Phase 1: Debug session
- **09:30-10:15** Phase 2: Fix data structure
- **10:15-10:45** Phase 3: Fix observer rules
- **10:45-11:15** Phase 4: Fix UI display
- **11:15-11:45** Phase 5: Test & verify
- **11:45-12:00** Phase 6: Cleanup

**Total: 3 hours**

### Day 2 (Tomorrow):
- Additional testing
- Edge case handling
- Documentation updates
- Code review

---

## Resources Needed

- Access to test model with dead transitions
- Python debugger (pdb) if needed
- GTK Inspector for UI debugging
- Git for version control and rollback

---

## Communication Plan

### Status Updates:
- After each phase completion
- Immediately if blocking issues found
- At end of day with summary

### Deliverables:
- Working Viability Panel
- Updated documentation
- Testing guide
- Commit history with clear messages

---

## Risk Assessment

### Low Risk:
- Debug logging additions (easily removed)
- Category expansion defaults (simple toggle)
- Statistics bar additions (isolated code)

### Medium Risk:
- Observer condition changes (affects core logic)
- Data sanitization (could break edge cases)
- Subscription callbacks (could cause crashes)

### High Risk:
- KB structure changes (affects entire system)
- Data flow modifications (could break other features)
- Event handling changes (could cause deadlocks)

**Mitigation:** 
- Make incremental changes
- Test after each phase
- Keep rollback plan ready
- Commit frequently

---

## Conclusion

This plan provides a structured approach to fixing the Viability Panel. The key is to:

1. **Debug first** - Understand the exact problem
2. **Fix incrementally** - One phase at a time
3. **Test continuously** - Verify each fix works
4. **Document everything** - For future maintenance

**Expected Outcome:** Fully functional Viability Panel that suggests model improvements.

**Confidence Level:** HIGH - Phase 1 complete and working.

---

## PHASE 1 COMPLETION UPDATE (November 10, 2025)

### ✅ COMPLETED SUCCESSFULLY

**Implementation Time:** ~45 minutes  
**Files Modified:** 4  
**Lines Changed:** ~400 (250 added, 150 removed)  
**Bugs Fixed:** 3

### Changes Summary:

1. **viability_panel.py**
   - Removed statistics bar UI
   - Added "Analyze All" button
   - Implemented `on_transition_selected()` for interactive mode
   - Implemented `on_analyze_all()` for batch mode
   - Simplified `on_simulation_complete()` to just log data availability
   - Fixed category expansion timing (expand BEFORE update)

2. **viability_observer.py**
   - Added `generate_suggestions_for_locality()` method (75 lines)
   - Added `generate_all_suggestions()` method (90 lines)
   - Both return standardized suggestion dicts

3. **base_category.py**
   - Fixed `is_expanded()` → `expanded` attribute access
   - Updated `_create_issue_row()` to handle both dicts and Issue objects
   - Maps confidence to icons: >0.8=💡, >0.5=⚠️, <0.5=🔴

4. **diagnosis_category.py**
   - Fixed severity field → confidence-based icons
   - Updated `_create_issue_row()` for dict format

### Testing Results:

**✅ Batch Mode (Analyze All):**
- Generates 66 suggestions correctly:
  - 39 structural (transitions that didn't fire)
  - 26 biological (unmapped compounds)
  - 0 kinetic (all transitions have rates)
  - 1 diagnosis (summary)
- Categories expand and display suggestions
- No crashes or errors

**⏳ Interactive Mode:**
- Code implemented
- Needs user testing (right-click transition → "Suggest Improvements")

### Current Status:

**WORKING:**
- Architecture refactored from reporter → assistant ✅
- Both operating modes implemented ✅
- Suggestion generation functional ✅
- UI displays suggestions correctly ✅
- Auto-expansion working ✅

**PENDING:**
- Phase 2: Apply/Preview buttons
- Phase 3-6: Advanced features

**Next Action:** User testing and feedback before proceeding to Phase 2.

