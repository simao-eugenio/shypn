# Phase 0.6: Topology Panel → Knowledge Base Integration Test Plan

**Date:** 2025-01-XX  
**Branch:** viability  
**Commit:** 1c80583 - Phase 0.6: Add Topology Panel → Knowledge Base update hooks

## Overview

Phase 0.6 connects Topology Panel analyses to the Knowledge Base, enabling automatic population of structural and behavioral data. This is the first data pipeline into the unified intelligence system.

## What Was Implemented

### 1. Knowledge Base Access Methods

**TopologyPanel** (`topology_panel.py`):
```python
def get_knowledge_base(self):
    """Get KB for current model from model_canvas."""
    if self.model_canvas and hasattr(self.model_canvas, 'get_current_knowledge_base'):
        return self.model_canvas.get_current_knowledge_base()
    return None
```

**BaseTopologyCategory** (`base_topology_category.py`):
```python
def get_knowledge_base(self):
    """Get KB from parent panel or model_canvas."""
    if self.parent_panel and hasattr(self.parent_panel, 'get_knowledge_base'):
        return self.parent_panel.get_knowledge_base()
    elif self.model_canvas and hasattr(self.model_canvas, 'get_current_knowledge_base'):
        return self.model_canvas.get_current_knowledge_base()
    return None
```

### 2. Update Hook in Analysis Thread

Modified `analyze_thread()` in `BaseTopologyCategory._run_analyzer()`:
```python
# After caching result:
GLib.idle_add(self._update_knowledge_base, analyzer_name, result)
```

KB updates run on GTK main thread for thread safety.

### 3. KB Update Dispatcher

Implemented `_update_knowledge_base()` method that:
1. Retrieves KB instance via `get_knowledge_base()`
2. Parses raw analyzer output dictionaries
3. Converts to KB dataclasses (PInvariant, TInvariant, Siphon)
4. Routes to appropriate KB update method
5. Prints confirmation message

**Supported Analyzers → KB Updates:**

| Analyzer | KB Method | Dataclass | Data Extracted |
|----------|-----------|-----------|----------------|
| `p_invariants` | `kb.update_p_invariants()` | `PInvariant` | vector, place_ids, conserved_value, biological_meaning |
| `t_invariants` | `kb.update_t_invariants()` | `TInvariant` | vector, transition_ids, biological_meaning |
| `liveness` | `kb.update_liveness()` | Dict | transition_id → liveness_level (dead/L1/L2/L3/L4) |
| `siphons` | `kb.update_siphons_traps()` | `Siphon` | place_ids, is_minimal |
| `traps` | `kb.update_siphons_traps()` | `Siphon` | place_ids, is_minimal |
| `deadlocks` | `kb.update_deadlocks()` | List | deadlock_states (markings) |
| `boundedness` | `kb.update_boundedness()` | Dict | place_id → bound_value |

### 4. Error Handling

- Try/except wrapper prevents KB update failures from breaking analysis
- Prints warnings if conversion fails
- Includes traceback for debugging
- Returns False to prevent GLib.idle_add repeats

## Test Plan

### Test 1: P-Invariants Update

**Steps:**
1. Launch Shypn: `python src/shypn.py`
2. Load model: `File → Open` → Select SBML model
3. Open Topology Panel (side panel stack)
4. Expand **Structural** category
5. Wait for auto-run or click "Run All Analyzers"
6. Watch console output

**Expected:**
```
✓ Knowledge Base updated: 3 P-invariants
```

**Verify in Code:**
```python
# In Viability Panel or Python console:
kb = self.model_canvas.get_current_knowledge_base()
print(f"P-invariants: {len(kb.p_invariants)}")
for inv in kb.p_invariants:
    print(f"  - Places: {inv.place_ids}, Vector: {inv.vector}")
```

### Test 2: T-Invariants Update

**Steps:**
1. Continue from Test 1
2. Wait for T-invariants analysis to complete

**Expected Console:**
```
✓ Knowledge Base updated: 2 T-invariants
```

**Verify:**
```python
kb = self.model_canvas.get_current_knowledge_base()
print(f"T-invariants: {len(kb.t_invariants)}")
for inv in kb.t_invariants:
    print(f"  - Transitions: {inv.transition_ids}, Vector: {inv.vector}")
```

### Test 3: Liveness Update

**Steps:**
1. Expand **Behavioral** category
2. Wait for Liveness analysis (may require manual expansion if SAFE_FOR_AUTO_RUN excludes it)

**Expected Console:**
```
✓ Knowledge Base updated: Liveness for 5 transitions
```

**Verify:**
```python
kb = self.model_canvas.get_current_knowledge_base()
print(f"Liveness: {kb.liveness_status}")
# Should show: {'T1': 'L4-live', 'T2': 'dead', ...}

for tid, level in kb.liveness_status.items():
    print(f"  - {tid}: {level}")
```

### Test 4: Siphons Update

**Steps:**
1. In Structural category, expand Siphons analyzer (if not auto-run)
2. Wait for completion

**Expected Console:**
```
✓ Knowledge Base updated: 1 siphons
```

**Verify:**
```python
kb = self.model_canvas.get_current_knowledge_base()
print(f"Siphons: {len(kb.siphons)}")
for siphon in kb.siphons:
    print(f"  - Places: {siphon.place_ids}, Minimal: {siphon.is_minimal}")
```

### Test 5: Boundedness Update

**Steps:**
1. In Behavioral category, wait for Boundedness analysis (auto-run)

**Expected Console:**
```
✓ Knowledge Base updated: Boundedness
```

**Verify:**
```python
kb = self.model_canvas.get_current_knowledge_base()
print(f"Boundedness: {kb.boundedness}")
# Should show: {'P1': 1, 'P2': 1, 'P3': -1} (where -1 means unbounded)
```

### Test 6: Multiple Models (KB Isolation)

**Steps:**
1. Load Model A, wait for topology analyses
2. Open new tab: `File → New` or load Model B
3. Wait for Model B topology analyses
4. Switch between tabs

**Expected:**
- Each tab has separate KB instance
- KB data doesn't leak between models
- Console shows updates for correct model

**Verify:**
```python
# In Model A tab:
kb_a = self.model_canvas.get_current_knowledge_base()
print(f"Model A P-invariants: {len(kb_a.p_invariants)}")

# Switch to Model B tab:
kb_b = self.model_canvas.get_current_knowledge_base()
print(f"Model B P-invariants: {len(kb_b.p_invariants)}")

# Verify they're different instances:
print(f"Same KB? {kb_a is kb_b}")  # Should be False
```

### Test 7: KB Access from Viability Panel

**Steps:**
1. Load model with topology analyses complete
2. Open Viability Panel (float or attach)
3. Add debug code to `viability_panel.py`:

```python
def on_diagnose_button_clicked(self, button):
    kb = self.get_knowledge_base()
    if kb:
        print(f"✓ Viability Panel accessed KB")
        print(f"  - P-invariants: {len(kb.p_invariants)}")
        print(f"  - T-invariants: {len(kb.t_invariants)}")
        print(f"  - Liveness: {len(kb.liveness_status)} transitions")
    else:
        print("✗ KB not accessible")
```

**Expected:**
- Viability Panel can access KB
- KB data matches topology panel results

## Success Criteria

✅ **Phase 0.6 Complete When:**

1. **Console Confirmation:** All 7 analyzer types print "✓ Knowledge Base updated" messages
2. **Data Accuracy:** KB contains correct number of invariants/siphons/etc.
3. **Type Safety:** No TypeErrors when accessing KB dataclasses
4. **Thread Safety:** No GTK warnings about main thread violations
5. **Model Isolation:** Multiple models maintain separate KB instances
6. **Panel Access:** Viability Panel can retrieve and query KB data

## Known Limitations

1. **Analyzer Result Format Assumptions:**
   - Code assumes specific dict keys ('invariants', 'places', 'transitions')
   - If analyzer output format changes, `_update_knowledge_base()` must adapt

2. **Incomplete Biological Meaning:**
   - `biological_meaning` field in invariants is `None` (analyzers don't compute this)
   - Future: Infer from KEGG pathway context

3. **Partial Siphon/Trap Support:**
   - Currently updates siphons OR traps separately
   - TODO: Update both simultaneously if both analyses complete

4. **No Structural Knowledge Update:**
   - KB doesn't receive basic place/transition info (IDs, labels, initial marking)
   - TODO: Add `kb.update_topology_structural()` hook when model loads

## Next Steps (Phase 0.7+)

**Phase 0.7:** Add Pathway Panel → KB hooks
- `kb.update_pathway_metadata()` - Map places to compounds
- `kb.update_compound_info()` - KEGG compound details
- `kb.update_reaction_info()` - KEGG reaction details

**Phase 0.8:** Add BRENDA Panel → KB hooks
- `kb.update_kinetic_parameters()` - Km, Vmax, EC numbers

**Phase 0.9:** Test Complete KB Workflow
- Load model → Topology → Pathway → BRENDA → Viability
- Verify all domains populated
- Test multi-domain queries

**Phase 2:** Implement Inference Engines
- `kb.infer_initial_marking()` - Dead place detection + KEGG basal concentration
- `kb.suggest_source_placement()` - Empty siphon + KEGG source compounds
- `kb.infer_firing_rate()` - Dead transition + BRENDA Km/Vmax

## Test Models

**Recommended Test Models:**

1. **Simple Model (Quick Test):**
   - `data/biomodels_test/BIOMD0000000001.xml` (Edelstein1996)
   - Small (3-5 places, 2-3 transitions)
   - Fast analyses (< 1s)

2. **Medium Model (Stress Test):**
   - Any glycolysis SBML model
   - 10-20 places, 8-15 transitions
   - Moderate analyses (2-5s)

3. **Complex Model (Edge Cases):**
   - Large metabolic network (40+ places)
   - Tests timeout handling, performance

## Debugging Tips

**If KB Not Updated:**

1. **Check KB Exists:**
   ```python
   kb = self.model_canvas.get_current_knowledge_base()
   print(f"KB exists: {kb is not None}")
   ```

2. **Check Analyzer Success:**
   ```python
   # In _update_knowledge_base():
   print(f"Result type: {type(result)}")
   print(f"Result data: {result_data}")
   ```

3. **Check Console for Exceptions:**
   - Look for traceback output from try/except wrapper

4. **Verify Model Canvas Connection:**
   ```python
   # In BaseTopologyCategory:
   print(f"model_canvas: {self.model_canvas}")
   print(f"has get_current_knowledge_base: {hasattr(self.model_canvas, 'get_current_knowledge_base')}")
   ```

## Commit History

```bash
git log --oneline viability
```

Expected (8 commits on viability branch):
```
1c80583 Phase 0.6: Add Topology Panel → Knowledge Base update hooks
053f2f3 Phase 0.5: Integrate Knowledge Base with model lifecycle
8b65ef7 Phase 0: Implement ModelKnowledgeBase foundation
a7f4921 Phase 0: Add Knowledge Base data structures
c5e62ba Phase 0: Create Knowledge Base architecture document
f9e8a1d Fix viability panel loader to match topology pattern
3b4d8e2 Phase 1: Implement Viability Panel UI foundation
... (previous commits)
```

---

**Status:** 🔧 Ready for Testing  
**Next:** Run tests, fix any issues, proceed to Phase 0.7 (Pathway Panel integration)
