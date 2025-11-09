# Behavioral Category Algorithm Prioritization

**Date:** November 9, 2025  
**Author:** Simão Eugénio  
**Status:** Implemented  

---

## Overview

The **Behavioral Analysis** category implements **internal algorithm prioritization** to provide fast feedback by running lightweight analyses first and expensive analyses last.

Unlike other topology categories that display individual result rows, Behavioral uses a **single-row Properties Matrix** with 5 columns (one per algorithm). This makes prioritization particularly effective because results populate **left-to-right** as each algorithm completes.

---

## Algorithm Priority Order

### Execution Sequence (Fast → Slow)

```
┌─────────────────────────────────────────────────────────────────┐
│  Properties Matrix (Results populate left-to-right)            │
├──────────┬──────────┬──────────┬──────────┬────────────────────┤
│ Bounded- │ Fairness │ Deadlocks│ Liveness │ Reachability       │
│ ness     │          │          │          │                    │
│ ⚡ 0.5s  │ ⚡ 1s    │ ⚠️ 10s   │ ⚠️ 20s   │ ⚠️ 30s            │
│ Priority │ Priority │ Priority │ Priority │ Priority 3         │
│ 1        │ 1        │ 3        │ 3        │                    │
└──────────┴──────────┴──────────┴──────────┴────────────────────┘
```

### 1. **Boundedness** (Priority 1) ⚡
- **Complexity:** O(n) - Linear in number of places
- **Algorithm:** Simple token counting + P-invariant sum check
- **Typical Time:** < 0.5 seconds
- **Output:** 
  - `✓ Yes, k=5` (bounded with max k tokens)
  - `✗ Unbounded` (places can grow infinitely)

**Why Fast:** Only counts current marking and checks conservation laws. No reachability exploration needed.

---

### 2. **Fairness** (Priority 1) ⚡
- **Complexity:** O(n+e) - Linear in nodes + edges
- **Algorithm:** Conflict detection via shared input places
- **Typical Time:** 0.5 - 1 second
- **Output:**
  - `✓ Yes` (all transitions get fair chances)
  - `⚠ Quasi-Fair, 80%` (some conflicts exist)
  - `✗ No` (starvation possible)

**Why Fast:** Graph traversal to find transitions sharing input places. No state space exploration.

---

### 3. **Deadlocks** (Priority 3) ⚠️
- **Complexity:** O(2^n) - Exponential in places (siphon detection)
- **Algorithm:** Siphon enumeration + enablement checking
- **Typical Time:** 5 - 30 seconds
- **Output:**
  - `✓ No` (no deadlock states)
  - `✗ Yes, Structural` (empty siphons found)
  - `✗ Yes, Behavioral` (no enabled transitions)

**Why Slow:** Requires siphon detection (exponential) or reachability checking. Can be expensive on large nets.

---

### 4. **Liveness** (Priority 3) ⚠️
- **Complexity:** O(k^n) - State explosion (depends on reachability)
- **Algorithm:** Check if transitions can fire infinitely often
- **Typical Time:** 10 - 30 seconds
- **Output:**
  - `✓ Yes, 100%` (all transitions live)
  - `⚠ Quasi-Live, 60%` (some transitions live)
  - `✗ No` (dead transitions exist)

**Why Slow:** Requires reachability analysis to determine if transitions can fire from all reachable states. State space explosion possible.

---

### 5. **Reachability** (Priority 3) ⚠️
- **Complexity:** O(k^n) - State explosion (k tokens, n places)
- **Algorithm:** Breadth-first marking space exploration (bounded)
- **Typical Time:** 5 - 60 seconds (depends on model size)
- **Output:**
  - `✓ Yes, 127 states` (reachable marking count)
  - `⚠ Partial, 10000+ states` (exploration limit reached)

**Why Slowest:** Full state space exploration. Even with bounds (10,000 states max), can take 30-60s on complex models.

---

## Implementation Strategy

### 1. Ordered Dictionary

```python
def _get_analyzers(self):
    """Return analyzers in PRIORITY ORDER using OrderedDict."""
    return OrderedDict([
        # FAST - Priority 1 (< 1s)
        ('boundedness', BoundednessAnalyzer),  # O(n)
        ('fairness', FairnessAnalyzer),        # O(n+e)
        
        # SLOW - Priority 3 (5-30s)
        ('deadlocks', DeadlockAnalyzer),       # O(2^n)
        ('liveness', LivenessAnalyzer),        # O(k^n)
        ('reachability', ReachabilityAnalyzer), # O(k^n)
    ])
```

**Result:** Base class iterates in this order, ensuring fast algorithms run first.

---

### 2. Properties Matrix Layout

Columns match execution order so results populate **left-to-right**:

```python
column_names = [
    'Boundedness',   # Column 0 - Results appear first (⚡ 0.5s)
    'Fairness',      # Column 1 - Results appear second (⚡ 1s)
    'Deadlocks',     # Column 2 - Results appear third (⚠️ 10s)
    'Liveness',      # Column 3 - Results appear fourth (⚠️ 20s)
    'Reachability'   # Column 4 - Results appear last (⚠️ 30s)
]
```

**Visual Effect:** Users see cells populate progressively left-to-right, providing immediate feedback.

---

### 3. Real-Time Status Updates

```python
def _update_properties_matrix(self):
    """Update matrix showing current status for each analyzer."""
    for analyzer_name in ['boundedness', 'fairness', 'deadlocks', 'liveness', 'reachability']:
        if analyzer_name in self.analyzing:
            texts.append('⏳ Analyzing...')  # Currently running
        elif analyzer_name in results:
            texts.append(format_result())     # Completed
        else:
            texts.append('Not analyzed')      # Pending
```

**User Experience:**
```
Initial:  [Not analyzed] [Not analyzed] [Not analyzed] [Not analyzed] [Not analyzed]
t=0.3s:   [⏳ Analyzing...] [Not analyzed] [Not analyzed] [Not analyzed] [Not analyzed]
t=0.5s:   [✓ Yes, k=10] [⏳ Analyzing...] [Not analyzed] [Not analyzed] [Not analyzed]
t=1.0s:   [✓ Yes, k=10] [✓ Yes] [⏳ Analyzing...] [Not analyzed] [Not analyzed]
t=10s:    [✓ Yes, k=10] [✓ Yes] [✗ Yes, Structural] [⏳ Analyzing...] [Not analyzed]
t=20s:    [✓ Yes, k=10] [✓ Yes] [✗ Yes, Structural] [⚠ Quasi-Live, 80%] [⏳ Analyzing...]
t=30s:    [✓ Yes, k=10] [✓ Yes] [✗ Yes, Structural] [⚠ Quasi-Live, 80%] [✓ Yes, 127 states]
```

---

### 4. Analyzer Start Hook

```python
# Base class notifies subclass when analyzer starts
if hasattr(self, '_on_analyzer_start'):
    GLib.idle_add(self._on_analyzer_start, analyzer_name)

# Behavioral category updates UI immediately
def _on_analyzer_start(self, analyzer_name):
    """Called when analyzer starts - shows '⏳ Analyzing...' status."""
    self._update_properties_matrix()
```

**Benefit:** UI updates twice per algorithm (start + complete), providing better progress visibility.

---

## Performance Comparison

### Before Prioritization

**Order:** Reachability → Boundedness → Liveness → Deadlocks → Fairness

```
Timeline:
t=0s:     Start Reachability (Priority 3)
t=30s:    Reachability completes
t=30.5s:  Start Boundedness (Priority 1)
t=31s:    Boundedness completes
t=31.5s:  Start Liveness (Priority 3)
t=51s:    Liveness completes
t=52s:    Start Deadlocks (Priority 3)
t=62s:    Deadlocks completes
t=62.5s:  Start Fairness (Priority 1)
t=63s:    Fairness completes

Total: 63 seconds
First result visible: 30 seconds (⏰ long wait!)
```

---

### After Prioritization

**Order:** Boundedness → Fairness → Deadlocks → Liveness → Reachability

```
Timeline:
t=0s:     Start Boundedness (Priority 1)
t=0.5s:   Boundedness completes ✅ First result visible!
t=0.5s:   Start Fairness (Priority 1)
t=1s:     Fairness completes ✅ Second result visible!
t=1s:     Start Deadlocks (Priority 3)
t=11s:    Deadlocks completes ✅
t=11s:    Start Liveness (Priority 3)
t=31s:    Liveness completes ✅
t=31s:    Start Reachability (Priority 3)
t=61s:    Reachability completes ✅

Total: 61 seconds (similar)
First result visible: 0.5 seconds (⚡ 60x faster!)
40% of results visible: 1 second
```

---

## Benefits Summary

### 1. **Instant Feedback** ⚡
- Boundedness result appears in < 0.5s
- Fairness result appears in < 1s
- Users see 40% (2/5) of results immediately

### 2. **Progressive Display** 📊
- Results populate left-to-right across matrix
- "⏳ Analyzing..." indicators show active algorithms
- No "black box" waiting period

### 3. **Psychological Advantage** 🧠
- 0.5s feels instant (vs 30s feels frozen)
- Progressive results feel faster than batch results
- Users can make decisions while slow algorithms run

### 4. **Efficient Resource Use** 🔧
- Fast algorithms complete quickly, freeing resources
- Slow algorithms don't block fast ones
- Staggered execution (50ms delays) prevents thread explosion

---

## Testing Recommendations

### Small Models (< 15 places)
- All algorithms safe and fast
- Prioritization mainly improves perceived performance
- Total time: 2-5 seconds

**Example:** Simple workflow with 10 places
```
Boundedness: 0.2s
Fairness: 0.5s
Deadlocks: 1s
Liveness: 2s
Reachability: 3s
Total: 6.7s (Priority 1 results in 0.7s)
```

---

### Medium Models (15-30 places)
- Priority 1 still fast (< 1s)
- Priority 3 becomes expensive (10-60s)
- Prioritization critical for UX

**Example:** Biological pathway with 25 places
```
Boundedness: 0.5s ✅
Fairness: 1s ✅
Deadlocks: 15s ⚠️
Liveness: 30s ⚠️
Reachability: 45s ⚠️
Total: 91.5s (Priority 1 results in 1.5s)
```

---

### Large Models (> 30 places)
- Priority 1 safe (< 2s)
- Priority 3 DANGEROUS (>60s or timeout)
- Manual triggering recommended for Priority 3

**Example:** Complex network with 50 places
```
Boundedness: 1s ✅
Fairness: 2s ✅
Deadlocks: 60s+ ⚠️ (May timeout)
Liveness: 60s+ ⚠️ (May timeout)
Reachability: 60s+ ⚠️ (May timeout)
Recommendation: Only run Boundedness + Fairness automatically
```

---

## Algorithm Details

### Boundedness Algorithm

**Steps:**
1. Check P-invariants (conservation laws)
2. Count tokens in current marking
3. Determine bound level k

**Why Fast:** No exploration, pure arithmetic.

**Code:**
```python
def analyze(self):
    # Check if total tokens conserved (O(n))
    is_conservative = sum(p_inv) == constant
    
    # Find max tokens per place (O(n))
    max_tokens = max(marking.values())
    
    return {'bounded': True, 'k': max_tokens}
```

---

### Fairness Algorithm

**Steps:**
1. Build transition conflict graph
2. Find strongly connected components
3. Check for potential starvation

**Why Fast:** Graph traversal only, no state space.

**Code:**
```python
def analyze(self):
    # Find transitions with shared input places (O(t*p))
    conflicts = find_conflicting_transitions()
    
    # Check for starvation risk (O(t+e))
    starvation_risk = detect_starvation_patterns()
    
    return {'is_fair': len(starvation_risk) == 0}
```

---

### Deadlocks Algorithm

**Steps:**
1. Enumerate minimal siphons (exponential!)
2. Check if siphons are empty
3. Check current enablement

**Why Slow:** Siphon enumeration is O(2^n).

**Code:**
```python
def analyze(self):
    # Find all minimal siphons (EXPENSIVE!)
    siphons = enumerate_minimal_siphons()  # O(2^n)
    
    # Check emptiness
    empty_siphons = [s for s in siphons if is_empty(s)]
    
    return {'has_deadlock': len(empty_siphons) > 0}
```

---

### Liveness Algorithm

**Steps:**
1. Explore reachable states (expensive!)
2. Check if transitions can fire infinitely
3. Classify liveness levels (L0-L4)

**Why Slow:** Requires reachability analysis.

**Code:**
```python
def analyze(self):
    # Build reachability graph (EXPENSIVE!)
    states = explore_state_space()  # O(k^n)
    
    # Check firing potential for each transition
    liveness_levels = classify_transitions(states)
    
    return {'live': all_transitions_L3_or_higher}
```

---

### Reachability Algorithm

**Steps:**
1. Start from initial marking
2. Breadth-first exploration
3. Build coverability graph
4. Limit to prevent explosion

**Why Slowest:** Full state space exploration.

**Code:**
```python
def analyze(self):
    # Explore marking space (VERY EXPENSIVE!)
    queue = [initial_marking]
    states = set()
    
    while queue and len(states) < MAX_STATES:
        marking = queue.pop(0)
        states.add(marking)
        
        # Find enabled transitions, fire, explore new markings
        for new_marking in fire_enabled_transitions(marking):
            if new_marking not in states:
                queue.append(new_marking)
    
    return {'state_count': len(states)}
```

---

## Future Enhancements

### Phase 1 (Current) ✅
- [x] OrderedDict execution order
- [x] Left-to-right result population
- [x] Real-time "Analyzing..." indicators
- [x] Analyzer start hook

### Phase 2 (Planned)
- [ ] **Progress bars** for slow algorithms (show % explored)
- [ ] **Partial results** from Reachability (show state count incrementally)
- [ ] **Time estimates** based on model size
- [ ] **Cancel button** for long-running analyses

### Phase 3 (Advanced)
- [ ] **Adaptive limits:** Reduce exploration depth on large models
- [ ] **Smart skipping:** Auto-skip Reachability if model > 30 places
- [ ] **Parallel execution:** Run Boundedness + Fairness simultaneously
- [ ] **Incremental display:** Update Reachability count every 1000 states

---

## Summary

**Key Achievement:** Behavioral category now displays **40% of results in 1 second** instead of waiting **30+ seconds** for all results. This is achieved by:

1. ✅ Prioritizing fast algorithms (Boundedness, Fairness)
2. ✅ Running slow algorithms last (Reachability, Liveness, Deadlocks)
3. ✅ Progressive left-to-right result display
4. ✅ Real-time status indicators

**Result:** Users get instant behavioral property feedback while expensive state space analyses run in the background!
