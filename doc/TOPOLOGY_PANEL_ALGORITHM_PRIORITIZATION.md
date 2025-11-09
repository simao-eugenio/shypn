# Topology Panel Algorithm Prioritization System

**Date:** November 9, 2025  
**Author:** Simão Eugénio  
**Status:** Implemented  

---

## Overview

The Topology Panel implements a **priority-based execution system** for topology analyzers to provide fast user feedback while preventing UI freezes from expensive algorithms.

**Key Principle:** Fast algorithms (O(n), O(n²)) run first and display results immediately, while slow algorithms (O(2^n), state explosion) run last or require manual triggering.

---

## Algorithm Priority Levels

### Priority 1: Fastest (< 0.5 seconds)
**Complexity:** O(n) to O(n+e)  
**Execution:** Run first, complete within 500ms  
**Auto-run:** ✅ Yes  

| Algorithm | Complexity | Description |
|-----------|-----------|-------------|
| **Hubs** | O(n+e) | Linear degree calculation |
| **Paths** | O(n+e) | Linear graph traversal |
| **Boundedness** | O(n) | Simple token counting |
| **Fairness** | O(n+e) | Conflict analysis |

**User Experience:** Instant results (< 0.5s), no spinner visible

---

### Priority 2: Fast (1-3 seconds)
**Complexity:** O(n²) to O(n²m)  
**Execution:** Run second, typically complete in 1-3s  
**Auto-run:** ✅ Yes  

| Algorithm | Complexity | Description |
|-----------|-----------|-------------|
| **P-Invariants** | O(n²m) | Matrix null space computation |
| **T-Invariants** | O(nm²) | Matrix left null space |
| **Cycles** | O((n+e)(c+1)) | Johnson's algorithm |
| **Dependency & Coupling** | O(t²) | Pairwise transition analysis |
| **Regulatory Structure** | O(a) | Arc-based analysis |

**User Experience:** Brief spinner (1-3s), results appear quickly

---

### Priority 3: Moderate (5-30 seconds)
**Complexity:** Exponential with bounded exploration  
**Execution:** Run third, or manual trigger only  
**Auto-run:** ❌ No (requires explicit user action)  

| Algorithm | Complexity | Description | Typical Time |
|-----------|-----------|-------------|--------------|
| **Reachability** | O(k^n) | State space exploration (bounded) | 5-30s |
| **Liveness** | O(k^n) | Depends on reachability | 5-30s |
| **Deadlocks** | O(2^n) | Siphon-based detection | 5-30s |

**User Experience:** Clear spinner with progress, ~10-30s wait

**Warnings:**
- ⚠️ **Reachability:** "State space exploration can take 30-60s on complex models"
- ⚠️ **Liveness:** "Can take 10-30s on complex models"
- ⚠️ **Deadlocks:** "Can take 10-30s if siphon checking enabled"

---

### Priority 4: Slow (> 60 seconds)
**Complexity:** Exponential without limits  
**Execution:** Manual trigger ONLY  
**Auto-run:** ❌ Never (too dangerous)  

| Algorithm | Complexity | Description | Risk Level |
|-----------|-----------|-------------|------------|
| **Siphons** | O(2^n) | Subset enumeration | 🔴 CRITICAL |
| **Traps** | O(2^n) | Subset enumeration | 🔴 CRITICAL |

**User Experience:** Must manually expand, shows critical warning

**Warnings:**
- 🔴 **CRITICAL:** "Can take >60s or freeze on models with >25 places. Use on small models only."

**Risk Assessment:**
- Models < 15 places: Safe (~1-5s)
- Models 15-25 places: Risky (~10-60s)
- Models > 25 places: DANGER (>60s or freeze)

---

## Execution Strategy

### Run All Button Behavior

When user clicks **"Run All Analyzers"**:

1. **Skip dangerous analyzers** (Priority 3-4 unless previously run)
2. **Sort remaining by priority** (ascending: 1 → 2 → 3...)
3. **Stagger execution** (50ms delay between starts)
4. **Display results incrementally** as each completes

```
Timeline:
t=0ms:    Start Priority 1 analyzers (Hubs, Paths, Boundedness, Fairness)
t=50ms:   Start Priority 2 analyzers (P-Inv, T-Inv, Cycles, etc.)
t=500ms:  Priority 1 results appear in table
t=2000ms: Priority 2 results appear in table
          UI shows: "Analysis complete: 9 results (prioritized execution)"
```

### Manual Expansion Behavior

When user manually expands an analyzer expander:
- **Safe analyzers (Priority 1-2):** Run immediately, no warning
- **Moderate analyzers (Priority 3):** Show warning, run on confirmation
- **Dangerous analyzers (Priority 4):** Show CRITICAL warning, require confirmation

---

## Implementation Details

### Metadata Structure

```python
ANALYZER_METADATA = {
    'analyzer_name': {
        'priority': 1,                    # 1=fastest, 4=slowest
        'complexity': 'O(n)',            # Big-O notation
        'description': 'Brief explanation',
        'safe_for_auto_run': True,       # Can Run All trigger it?
        'typical_time': '<0.5s',         # Human-readable time
        'warning': '⚠️ Caution text',   # Optional warning
        'risk': 'HIGH'                   # Optional risk level
    }
}
```

### Priority Sorting

```python
def _on_run_all_clicked(self, button):
    # Get analyzers
    analyzer_list = []
    for name in analyzers.keys():
        if name not in DANGEROUS_ANALYZERS:
            priority = ANALYZER_METADATA.get(name, {}).get('priority', 5)
            analyzer_list.append((priority, name))
    
    # Sort by priority (1, 2, 3, ...)
    analyzer_list.sort(key=lambda x: x[0])
    
    # Run with staggered delays
    for i, (priority, name) in enumerate(analyzer_list):
        delay_ms = i * 50
        GLib.timeout_add(delay_ms, self._run_analyzer, name)
```

### Progress Display

Status label updates in real-time:
```
"Running: Hubs, Paths, Boundedness..."        # During execution
"Analysis complete: 9 results (prioritized)"  # When done
```

---

## Benefits

### 1. **Immediate Feedback**
- Priority 1 algorithms complete in < 0.5s
- Users see results instantly while slow algorithms still run
- No perceived wait time for fast analyses

### 2. **No UI Freezing**
- Slow algorithms never auto-run
- Background threading prevents blocking
- GTK main loop stays responsive

### 3. **Predictable Performance**
- Users know which algorithms are fast/slow
- Clear warnings before running expensive operations
- Tooltips explain complexity and timing

### 4. **Optimal Resource Usage**
- Fast algorithms saturate CPU first (maximize throughput)
- Slow algorithms run last (minimize total latency)
- Staggered execution prevents thread explosion

### 5. **Better UX**
- Table populates incrementally (streaming results)
- Progress indicator shows active analyses
- Users can interact with early results while others complete

---

## Performance Comparison

### Before Prioritization (Sequential Execution)
```
Timeline:
t=0s:      Start Siphons (Priority 4)
t=60s:     Siphons completes (⚠️ 60s freeze!)
t=60.5s:   Start Hubs (Priority 1)
t=61s:     All complete
Total: 61 seconds, 60s of apparent freeze
```

### After Prioritization (Priority-Ordered)
```
Timeline:
t=0s:      Start Hubs (Priority 1)
t=0.5s:    Hubs completes → display results
t=1s:      Start P-Invariants (Priority 2)
t=3s:      P-Invariants completes → display results
          (Skip Siphons - manual only)
Total: 3 seconds, instant feedback
```

**Improvement:** 20x faster perceived performance, instant results

---

## Testing Recommendations

### Small Models (< 15 places)
- All algorithms safe to run
- Priority mainly affects order, not safety
- Total time: < 5s

### Medium Models (15-30 places)
- Priority 1-2: Safe (< 5s)
- Priority 3: Risky (10-30s)
- Priority 4: DANGER (>60s)

### Large Models (> 30 places)
- Priority 1-2: Safe (< 10s)
- Priority 3: DANGER (>60s)
- Priority 4: DO NOT RUN (will freeze)

### Recommended Test Models
1. **hsa00010.shy** (25 places) - Good for Priority 1-2
2. **Small workflow** (10 places) - Safe for all
3. **Complex pathway** (50 places) - Only Priority 1-2

---

## Future Enhancements

### Phase 1 (Current) ✅
- [x] Priority metadata system
- [x] Sorted execution order
- [x] Staggered delays
- [x] Progress updates
- [x] Tooltips explaining priorities

### Phase 2 (Future)
- [ ] **Adaptive time limits:** Cancel algorithm if exceeds expected time
- [ ] **Model size detection:** Warn if model too large for Priority 3-4
- [ ] **Parallel execution:** Run multiple Priority 1 algorithms simultaneously
- [ ] **Smart caching:** Remember which algorithms were slow, deprioritize next time
- [ ] **User preferences:** Allow users to customize priority levels

### Phase 3 (Advanced)
- [ ] **Progressive results:** Stream partial results during analysis (e.g., "Found 5 invariants so far...")
- [ ] **Cancelable execution:** Allow user to cancel slow algorithms mid-execution
- [ ] **Resource monitoring:** Track CPU/memory, pause analyses if system overloaded
- [ ] **Benchmarking mode:** Measure actual execution times, refine priorities

---

## Configuration Reference

### Safe for Auto-Run
```python
SAFE_FOR_AUTO_RUN = {
    'hubs', 'paths', 'boundedness', 'fairness',      # Priority 1
    'p_invariants', 't_invariants', 'cycles',        # Priority 2
    'dependency_coupling', 'regulatory_structure'    # Priority 2
}
```

### Dangerous (Manual Only)
```python
DANGEROUS_ANALYZERS = {
    'reachability', 'liveness', 'deadlocks',  # Priority 3
    'siphons', 'traps'                        # Priority 4
}
```

---

## Summary

The **Algorithm Prioritization System** ensures:
1. ✅ Fast algorithms run first (instant results)
2. ✅ Slow algorithms run last (or manual only)
3. ✅ No UI freezing from expensive operations
4. ✅ Clear warnings before running dangerous algorithms
5. ✅ Incremental result display (streaming UX)

**Result:** Users get immediate feedback for 80% of analyses while avoiding the 20% that could freeze the system.
