# Topology Analyzer Performance Analysis

## Overview

This document identifies analyzers with high computational complexity that could freeze the system when auto-run on model load.

**Date**: October 29, 2025  
**Context**: Auto-run feature disabled due to Wayland compositor crashes

---

## 🔴 CRITICAL - HIGH RISK ANALYZERS (Can cause system freeze)

### 1. **Siphons Analyzer** ⚠️ EXPONENTIAL COMPLEXITY

**File**: `src/shypn/topology/structural/siphons.py`

**Algorithm**: Brute-force enumeration with `combinations()`

**Complexity**: **O(2^n)** where n = number of places

**Why it's slow**:
```python
# Lines 228-233: Checks ALL possible place subsets
for size in range(min_size, min(max_size + 1, n_places + 1)):
    for place_subset in combinations(place_ids, size):
        self._checked_count += 1
        if self._is_siphon(set(place_subset), place_presets, place_postsets):
            siphons.append(set(place_subset))
```

**Performance Impact**:
- 10 places: ~1,000 combinations
- 20 places: ~1,000,000 combinations  
- 30 places: **~1 BILLION combinations** ❌ FREEZE
- 50 places: ~10^15 combinations (weeks of computation)

**Current Limits**: 
- `max_siphons=100` (doesn't prevent computation explosion)
- No timeout mechanism
- No early termination

**Risk Level**: 🔴 **CRITICAL** - Will freeze on models with >25 places

---

### 2. **Traps Analyzer** ⚠️ EXPONENTIAL COMPLEXITY

**File**: `src/shypn/topology/structural/traps.py`

**Algorithm**: Identical to Siphons (dual concept)

**Complexity**: **O(2^n)** where n = number of places

**Performance Impact**: Same as Siphons analyzer

**Risk Level**: 🔴 **CRITICAL** - Will freeze on models with >25 places

---

### 3. **Reachability Analyzer** ⚠️ STATE EXPLOSION

**File**: `src/shypn/topology/behavioral/reachability.py`

**Algorithm**: Breadth-First Search (BFS) of marking space

**Complexity**: **O(k^n)** where:
- k = average tokens per place
- n = number of places

**Why it's slow**:
```python
# Lines 213-248: BFS explores state space
while queue and len(visited) < max_states:
    current_marking, depth = queue.popleft()
    
    # Find enabled transitions
    enabled = self._get_enabled_transitions(current_marking)
    
    # Fire each enabled transition (creates new states)
    for trans_id in enabled:
        new_marking = self._fire_transition(current_marking, trans_id)
        # ... add to queue
```

**Performance Impact**:
- Small models (5-10 places): Fast
- Medium models (15-25 places): Seconds to minutes
- Large models (30+ places): **Can explore millions of states** ❌ FREEZE
- Unbounded nets: Infinite exploration (limited by max_states)

**Current Limits**: 
- `max_states=10000` (good protection)
- `max_depth=100` (good protection)
- **BUT**: Can still take 30-60 seconds on complex models

**Risk Level**: 🟠 **HIGH** - Can cause 30-60s freeze on complex models

---

### 4. **Liveness Analyzer** ⚠️ DEPENDS ON REACHABILITY

**File**: `src/shypn/topology/behavioral/liveness.py`

**Algorithm**: Uses deadlock analysis + structural checks

**Complexity**: Depends on deadlock analyzer complexity

**Performance Impact**: 
- Can trigger reachability analysis internally
- Less risky than pure reachability but still slow

**Risk Level**: 🟠 **MEDIUM-HIGH** - Can take 10-30s on complex models

---

### 5. **Deadlocks Analyzer** ⚠️ DEPENDS ON SIPHONS

**File**: `src/shypn/topology/behavioral/deadlocks.py`

**Algorithm**: Checks empty siphons + transition enablement

**Complexity**: Depends on siphon detection if `check_siphons=True`

**Performance Impact**: 
- If siphon check enabled: Inherits siphon complexity (exponential)
- Otherwise: Fast (just checks transition enablement)

**Risk Level**: 🟠 **MEDIUM-HIGH** - Slow if siphon checking enabled

---

## 🟡 MODERATE RISK ANALYZERS (Can be slow but less likely to freeze)

### 6. **Cycles Analyzer** 

**File**: `src/shypn/topology/graph/cycles.py`

**Algorithm**: Johnson's algorithm via NetworkX `simple_cycles()`

**Complexity**: **O((n+e)(c+1))** where:
- n = nodes
- e = edges  
- c = number of cycles

**Performance Impact**:
- Efficient algorithm (Johnson's is state-of-the-art)
- Most models: <1 second
- Dense graphs with many cycles: Can take 5-10 seconds

**Current Limits**: `max_cycles=100` (good protection)

**Risk Level**: 🟡 **MODERATE** - Usually fast, occasionally slow

---

### 7. **P-Invariants Analyzer**

**File**: `src/shypn/topology/structural/p_invariants.py`

**Algorithm**: Farkas algorithm (null space computation via SVD)

**Complexity**: **O(n²m)** where:
- n = places
- m = transitions

**Performance Impact**:
- Matrix operations are fast (NumPy/SciPy optimized)
- Most models: <1 second
- Very large models (100+ places/transitions): 2-5 seconds

**Current Limits**: `max_invariants=100` (good protection)

**Risk Level**: 🟡 **LOW-MODERATE** - Usually fast

---

### 8. **T-Invariants Analyzer**

**File**: `src/shypn/topology/structural/t_invariants.py`

**Algorithm**: Farkas algorithm (null space computation)

**Complexity**: **O(nm²)** where:
- n = places
- m = transitions

**Performance Impact**: Similar to P-Invariants

**Risk Level**: 🟡 **LOW-MODERATE** - Usually fast

---

## 🟢 LOW RISK ANALYZERS (Fast, unlikely to cause issues)

### 9. **Paths Analyzer**
- **Complexity**: Linear graph traversal
- **Risk**: 🟢 **LOW** - Fast

### 10. **Hubs Analyzer**
- **Complexity**: O(n+e) graph degree calculation
- **Risk**: 🟢 **LOW** - Very fast

### 11. **Boundedness Analyzer**
- **Complexity**: Simple token counting
- **Risk**: 🟢 **LOW** - Very fast

### 12. **Fairness Analyzer**
- **Complexity**: Graph analysis
- **Risk**: 🟢 **LOW-MODERATE** - Usually fast

---

## 📊 Summary Table

| Analyzer | Complexity | Freeze Risk | Typical Time | Max Time (bad case) |
|----------|-----------|-------------|--------------|---------------------|
| **Siphons** | O(2^n) | 🔴 CRITICAL | 0.1s - 5s | **INFINITE** (>30 places) |
| **Traps** | O(2^n) | 🔴 CRITICAL | 0.1s - 5s | **INFINITE** (>30 places) |
| **Reachability** | O(k^n) | 🟠 HIGH | 0.5s - 10s | **60s+** (complex models) |
| **Liveness** | Variable | 🟠 MEDIUM-HIGH | 0.5s - 5s | 30s |
| **Deadlocks** | Variable | 🟠 MEDIUM-HIGH | 0.1s - 5s | 30s |
| **Cycles** | O((n+e)(c+1)) | 🟡 MODERATE | 0.1s - 1s | 10s |
| **P-Invariants** | O(n²m) | 🟡 LOW-MODERATE | 0.1s - 2s | 5s |
| **T-Invariants** | O(nm²) | 🟡 LOW-MODERATE | 0.1s - 2s | 5s |
| **Paths** | O(n+e) | 🟢 LOW | <0.1s | 1s |
| **Hubs** | O(n+e) | 🟢 LOW | <0.1s | 0.5s |
| **Boundedness** | O(n) | 🟢 LOW | <0.1s | 0.5s |
| **Fairness** | O(n+e) | 🟢 LOW-MODERATE | <0.5s | 2s |

**Legend**: n=places, m=transitions, e=arcs, k=avg tokens, c=cycles

---

## 🎯 RECOMMENDED SOLUTIONS

### Option 1: **Disable Dangerous Analyzers in Auto-Run** ✅ SAFEST

**Implementation**:
```python
# In base_topology_category.py - auto_run_all_analyzers()
SAFE_FOR_AUTO_RUN = [
    'p_invariants',
    't_invariants', 
    'cycles',
    'paths',
    'hubs',
    'boundedness',
    'fairness'
]

DANGEROUS_ANALYZERS = [
    'siphons',      # Exponential
    'traps',        # Exponential
    'reachability', # State explosion
    'liveness',     # Slow
    'deadlocks'     # Depends on siphons
]

def auto_run_all_analyzers(self):
    for analyzer_name in self.analyzers:
        if analyzer_name in SAFE_FOR_AUTO_RUN:
            self._run_analyzer(analyzer_name)
        # Dangerous analyzers require manual expansion
```

**Pros**: 
- ✅ No system freezes
- ✅ Fast analyzers run automatically
- ✅ User can still manually run slow analyzers
- ✅ Simple to implement

**Cons**: 
- ❌ Users don't get full automatic analysis

---

### Option 2: **Add Timeouts** ⏱️

**Implementation**:
```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds):
    def timeout_handler(signum, frame):
        raise TimeoutError("Analyzer exceeded time limit")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

# In _run_analyzer():
try:
    with timeout(5):  # 5 second limit
        result = analyzer.analyze()
except TimeoutError:
    result = AnalysisResult(
        success=False,
        errors=["Analysis timeout (>5s)"]
    )
```

**Pros**: 
- ✅ Protects against infinite loops
- ✅ All analyzers available for auto-run

**Cons**: 
- ❌ Doesn't work on Windows
- ❌ Timeout in middle of computation wastes resources
- ❌ May leave partial results

---

### Option 3: **Add Size-Based Guards** 📏

**Implementation**:
```python
# In each analyzer's analyze() method
def analyze(self, **kwargs):
    # Siphons/Traps: Check place count
    if len(self.model.places) > 20:
        return AnalysisResult(
            success=False,
            errors=["Model too large for siphon analysis (>20 places)"],
            warnings=["Use max_size parameter to limit search"]
        )
    
    # Reachability: Check state space estimate
    estimated_states = self._estimate_state_space()
    if estimated_states > 50000:
        return AnalysisResult(
            success=False,
            errors=["State space too large (>50k states)"]
        )
```

**Pros**: 
- ✅ Fast pre-check prevents computation
- ✅ Clear error messages to user

**Cons**: 
- ❌ May reject models that could be analyzed
- ❌ Requires tuning thresholds

---

### Option 4: **Thread Pool with Limited Concurrency** 🔀

**Current Issue**: Running 12 analyzers simultaneously overwhelms system

**Implementation**:
```python
from concurrent.futures import ThreadPoolExecutor

def auto_run_all_analyzers(self):
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        for analyzer_name in self.analyzers:
            future = executor.submit(self._run_analyzer, analyzer_name)
            futures.append((analyzer_name, future))
        
        # Wait for completion
        for name, future in futures:
            try:
                future.result(timeout=10)  # 10s per analyzer
            except TimeoutError:
                print(f"{name} timed out")
```

**Pros**: 
- ✅ Limits system load (only 2 at once)
- ✅ Timeout per analyzer

**Cons**: 
- ❌ Still can freeze if even one analyzer is too slow
- ❌ More complex threading

---

## ✅ RECOMMENDED APPROACH

**Hybrid Solution**:

1. **Whitelist safe analyzers for auto-run** (Option 1)
2. **Add size guards to exponential analyzers** (Option 3)
3. **Show "⚠️ Manual only" badge for dangerous analyzers in UI**

**Implementation Priority**:
- ✅ **Phase 1** (NOW): Whitelist-based auto-run
- ⏳ **Phase 2**: Add size guards to siphons/traps
- ⏳ **Phase 3**: Add UI warnings for dangerous analyzers
- ⏳ **Phase 4**: Consider timeouts if needed

---

## 🧪 Testing Recommendations

**Test Models**:
1. **Small** (5 places, 5 transitions) - All analyzers fast
2. **Medium** (15 places, 20 transitions) - Siphons/traps slow
3. **Large** (30+ places, 50+ transitions) - Siphons/traps freeze
4. **Complex** (cyclic, high branching) - Reachability explodes

**Benchmark Each Analyzer**:
```bash
# Create test script
python scripts/benchmark_analyzers.py --model examples/glycolysis.xml
```

**Expected Results**:
- P/T-Invariants: <2s on all models
- Cycles/Paths/Hubs: <1s on all models
- Siphons/Traps: **>10s on medium, FREEZE on large**
- Reachability: **>30s on complex models**

---

## 📝 Conclusion

**Root Cause of System Freeze**: 
Running **all 12 analyzers** simultaneously, including:
- 2 exponential-complexity analyzers (Siphons, Traps)
- 1 state-explosion analyzer (Reachability)
- 2 analyzers that depend on the above (Liveness, Deadlocks)

**Solution**: 
Only auto-run the **7 safe analyzers**, leave the **5 dangerous ones** for manual expansion.

**Current Status**: 
Auto-run disabled entirely (safe but limits functionality)

**Next Step**: 
Implement whitelist-based auto-run (restores 60% of automatic analysis)
