# Topology Analyzer Improvements - Implementation Plan

## 📋 Requirements Summary

Based on user feedback (2025-10-29), the topology analysis system needs:

1. **BLOCK execution on large models** (not just warn)
2. **Offline/background analysis** capability (run overnight, cache results)
3. **Per-element result format** (properties per place/transition, not lists)

---

## 🚫 REQUIREMENT 1: Block Dangerous Analyses on Large Models

### Current Problem
- Warning messages shown but user can still click and freeze system
- No size validation before computation starts
- Curious users will still try and crash the system

### Solution: Pre-Execution Guards

**Implementation in each analyzer's `analyze()` method**:

```python
def analyze(self, **kwargs):
    """Analyze siphons (with size guard)."""
    start_time = self._start_timer()
    
    # ========================================
    # SIZE GUARD: Check model size FIRST
    # ========================================
    n_places = len(self.model.places)
    n_transitions = len(self.model.transitions)
    
    # Siphons: Exponential in number of places
    if n_places > 20:
        return AnalysisResult(
            success=False,
            errors=[
                f"⛔ Model too large for siphon analysis ({n_places} places)",
                f"⚠️ This analysis has O(2^n) complexity and would take hours/days",
                f"Maximum supported: 20 places (current: {n_places})"
            ],
            warnings=[
                "Consider using a smaller model or subnetwork",
                "Siphons can be analyzed offline - see documentation"
            ],
            metadata={
                'blocked': True,
                'reason': 'model_too_large',
                'max_places': 20,
                'actual_places': n_places
            }
        )
    
    # Continue with normal analysis
    try:
        # ... actual analysis code
```

**Size Limits Per Analyzer**:

| Analyzer | Limit | Parameter | Reason |
|----------|-------|-----------|--------|
| **Siphons** | 20 places | `len(places)` | O(2^n) combinations |
| **Traps** | 20 places | `len(places)` | O(2^n) combinations |
| **Reachability** | 50k states | `estimated_states` | State explosion |
| **Liveness** | 30 transitions | `len(transitions)` | Depends on reachability |
| **Deadlocks** | 25 places | `len(places)` | Depends on siphons |
| **Cycles** | 1000 cycles | `max_cycles` | Already has limit ✓ |
| **P-Invariants** | 100 invariants | `max_invariants` | Already has limit ✓ |
| **T-Invariants** | 100 invariants | `max_invariants` | Already has limit ✓ |

**UI Behavior**:
```
When user expands blocked analyzer:

┌─────────────────────────────────────────┐
│ > Siphons                               │
├─────────────────────────────────────────┤
│ ⛔ Analysis Blocked                     │
│                                         │
│ This model is too large for siphon      │
│ analysis (45 places, max: 20).          │
│                                         │
│ Reason: O(2^n) exponential complexity   │
│ would require ~10^13 operations         │
│ (estimated: several hours/days).        │
│                                         │
│ ℹ️ Options:                             │
│ • Analyze a smaller subnetwork          │
│ • Use offline batch analysis (see doc)  │
│ • Export model for HPC cluster          │
└─────────────────────────────────────────┘
```

---

## 🌙 REQUIREMENT 2: Offline/Background Analysis System

### Design: Batch Analysis with Persistent Cache

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                    TOPOLOGY ANALYSIS SYSTEM                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐         ┌─────────────────┐              │
│  │   UI Panel   │         │  Batch Analyzer │              │
│  │ (Interactive)│◄────────┤   (Offline)     │              │
│  └──────────────┘         └─────────────────┘              │
│         │                          │                        │
│         │                          │                        │
│         ▼                          ▼                        │
│  ┌──────────────────────────────────────────┐              │
│  │      PERSISTENT RESULT CACHE             │              │
│  │   ~/.shypn/topology_cache/               │              │
│  │                                           │              │
│  │   model_hash_12345.json:                 │              │
│  │   {                                       │              │
│  │     "model": "glycolysis.xml",           │              │
│  │     "timestamp": "2025-10-29 23:45:12",  │              │
│  │     "results": {                         │              │
│  │       "siphons": [...],                  │              │
│  │       "reachability": {...}              │              │
│  │     }                                     │              │
│  │   }                                       │              │
│  └──────────────────────────────────────────┘              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Implementation**:

**File**: `src/shypn/topology/batch/batch_analyzer.py`
```python
class BatchAnalyzer:
    """Run topology analyses in batch mode (CLI, overnight jobs)."""
    
    def __init__(self, cache_dir="~/.shypn/topology_cache"):
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_model_batch(
        self,
        model_path: str,
        analyzers: List[str] = None,
        force: bool = False
    ) -> Dict[str, AnalysisResult]:
        """Run all requested analyzers on model (can take hours).
        
        Args:
            model_path: Path to SBML/PNT file
            analyzers: List of analyzer names (None = all)
            force: Re-run even if cached
        
        Returns:
            Dict of {analyzer_name: AnalysisResult}
        """
        # Load model
        model = self._load_model(model_path)
        model_hash = self._compute_model_hash(model)
        
        # Check cache
        if not force:
            cached = self._load_from_cache(model_hash)
            if cached:
                print(f"✓ Using cached results from {cached['timestamp']}")
                return cached['results']
        
        # Run all analyzers (can take hours)
        results = {}
        if analyzers is None:
            analyzers = ALL_ANALYZERS
        
        for analyzer_name in analyzers:
            print(f"Running {analyzer_name}...", end='', flush=True)
            start = time.time()
            
            analyzer_class = ANALYZER_MAP[analyzer_name]
            analyzer = analyzer_class(model)
            result = analyzer.analyze()
            
            results[analyzer_name] = result
            elapsed = time.time() - start
            print(f" {elapsed:.1f}s")
        
        # Save to cache
        self._save_to_cache(model_hash, model_path, results)
        
        return results
```

**CLI Tool**: `scripts/batch_topology_analysis.py`
```bash
# Run overnight
$ python scripts/batch_topology_analysis.py \
    --model examples/large_metabolic_network.xml \
    --analyzers siphons,traps,reachability \
    --timeout 3600  # 1 hour per analyzer

# Next day: Results are cached
$ python src/shypn.py examples/large_metabolic_network.xml
# UI instantly shows cached results ✓
```

**Cron Job for Nightly Analysis**:
```bash
# ~/.shypn/crontab
# Run topology analysis on all models at 2 AM
0 2 * * * /usr/bin/python3 /path/to/batch_topology_analysis.py \
    --models-dir ~/models/ \
    --all-analyzers \
    --log ~/.shypn/batch_analysis.log
```

---

## 📊 REQUIREMENT 3: Per-Element Result Format

### Current Problem
Results show **lists of structures**:
```
P-Invariants:
1. {P1, P2, P3} - weights [1, 2, 1]
2. {P4, P5} - weights [1, 1]
...
```

User wants: **Properties per element** (like a database):
```
Place P1 "ATP":
- In P-Invariant #1 (weight: 1)
- In P-Invariant #3 (weight: 2)
- In Siphon #2
- Covered by Trap #1
- Conserved: Yes (sum with P2=const)

Transition T1 "Hexokinase":
- In T-Invariant #1 (weight: 1)
- Hub: Yes (degree: 7)
- In Cycles: [Cycle1, Cycle2]
- Liveness: L3 (Live)
- Can deadlock: No
```

### Solution: Element-Centric Result Transformation

**New Data Structure**:
```python
{
    'places': {
        'P1': {
            'name': 'ATP',
            'id': 1,
            'p_invariants': [
                {'invariant_id': 1, 'weight': 1, 'expression': 'ATP + 2*ADP'},
                {'invariant_id': 3, 'weight': 2, 'expression': '2*ATP + NADH'}
            ],
            'siphons': [2, 5],  # Siphon IDs
            'traps': [1],
            'is_conserved': True,
            'boundedness': 'bounded',
            'can_deadlock': False
        },
        'P2': { ... }
    },
    'transitions': {
        'T1': {
            'name': 'Hexokinase',
            'id': 1,
            't_invariants': [
                {'invariant_id': 1, 'weight': 1, 'sequence': 'T1 → T2 → T3'},
                {'invariant_id': 4, 'weight': 2, 'sequence': '2*T1 → T5'}
            ],
            'is_hub': True,
            'hub_degree': 7,
            'cycles': [
                {'cycle_id': 1, 'length': 5, 'nodes': ['T1','P2','T3','P5','T1']},
                {'cycle_id': 2, 'length': 3, 'nodes': ['T1','P1','T2','P3','T1']}
            ],
            'liveness_level': 'L3',
            'liveness_description': 'Live - can fire infinitely often',
            'can_deadlock': False,
            'fairness': 'fair'
        },
        'T2': { ... }
    }
}
```

**Implementation**: New class `TopologyResultAggregator`

**File**: `src/shypn/topology/aggregator/result_aggregator.py`
```python
class TopologyResultAggregator:
    """Transform analyzer results into per-element properties."""
    
    def aggregate(self, all_results: Dict[str, AnalysisResult]) -> Dict:
        """Aggregate all analysis results into per-element view.
        
        Args:
            all_results: Dict of {analyzer_name: AnalysisResult}
        
        Returns:
            Dict with 'places' and 'transitions' keys containing
            element-centric property dictionaries
        """
        places = defaultdict(lambda: {'name': '', 'id': None, 'properties': {}})
        transitions = defaultdict(lambda: {'name': '', 'id': None, 'properties': {}})
        
        # Process P-Invariants
        if 'p_invariants' in all_results:
            result = all_results['p_invariants']
            if result.success:
                for inv_id, inv in enumerate(result.get('p_invariants', [])):
                    for place_id, weight in zip(inv['places'], inv['weights']):
                        places[place_id]['p_invariants'].append({
                            'invariant_id': inv_id,
                            'weight': weight,
                            'expression': inv['sum_expression']
                        })
        
        # Process T-Invariants
        if 't_invariants' in all_results:
            result = all_results['t_invariants']
            if result.success:
                for inv_id, inv in enumerate(result.get('t_invariants', [])):
                    for trans_id, weight in zip(inv['transition_ids'], inv['weights']):
                        transitions[trans_id]['t_invariants'].append({
                            'invariant_id': inv_id,
                            'weight': weight,
                            'sequence': inv['firing_sequence']
                        })
        
        # Process Hubs
        if 'hubs' in all_results:
            result = all_results['hubs']
            if result.success:
                for hub in result.get('hubs', []):
                    trans_id = hub['id']
                    transitions[trans_id]['is_hub'] = True
                    transitions[trans_id]['hub_degree'] = hub['degree']
        
        # ... process all other analyzers
        
        return {'places': dict(places), 'transitions': dict(transitions)}
```

**UI Display**: Table with properties per element

```
┌──────────────────────────────────────────────────────────────────┐
│ > P-Invariants                                                    │
├──────────────────────────────────────────────────────────────────┤
│ ╔══════════╦══════════════╦═══════════╦══════════════════════╗  │
│ ║ Place    ║ Name         ║ Invariants║ Conservation         ║  │
│ ╠══════════╬══════════════╬═══════════╬══════════════════════╣  │
│ ║ P1       ║ ATP          ║ 2         ║ ATP + 2*ADP = 100    ║  │
│ ║ P2       ║ ADP          ║ 1         ║ ATP + 2*ADP = 100    ║  │
│ ║ P3       ║ Glucose      ║ 3         ║ Multiple             ║  │
│ ║ P4       ║ Pyruvate     ║ 0         ║ Not conserved        ║  │
│ ╚══════════╩══════════════╩═══════════╩══════════════════════╝  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ > Hubs                                                            │
├──────────────────────────────────────────────────────────────────┤
│ ╔══════════╦══════════════╦════════╦═════════════════════════╗  │
│ ║ Trans.   ║ Name         ║ Degree ║ Connected To            ║  │
│ ╠══════════╬══════════════╬════════╬═════════════════════════╣  │
│ ║ T1       ║ Hexokinase   ║ 7      ║ P1,P2,P3,P5,P7,P9,P12  ║  │
│ ║ T5       ║ PFK          ║ 6      ║ P4,P6,P8,P11,P13,P14   ║  │
│ ║ T12      ║ Pyruvate_K   ║ 5      ║ P10,P15,P16,P18,P20    ║  │
│ ╚══════════╩══════════════╩════════╩═════════════════════════╝  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Implementation Priority

### Phase 1: Size Guards (IMMEDIATE) ✅
**Goal**: Prevent system freezes NOW

**Tasks**:
1. ✅ Add size check constants at top of each analyzer
2. ✅ Add guard in `analyze()` method before computation
3. ✅ Return AnalysisResult with blocked=True
4. ✅ Update UI to show block message clearly
5. ✅ Test with models of varying sizes

**Files to Modify**:
- `src/shypn/topology/structural/siphons.py`
- `src/shypn/topology/structural/traps.py`
- `src/shypn/topology/behavioral/reachability.py`
- `src/shypn/topology/behavioral/liveness.py`
- `src/shypn/topology/behavioral/deadlocks.py`

**Time Estimate**: 2-3 hours

---

### Phase 2: Per-Element Results (HIGH PRIORITY)
**Goal**: Better data organization

**Tasks**:
1. Create `TopologyResultAggregator` class
2. Implement transformation logic for all 12 analyzers
3. Update UI to display element-centric tables
4. Add sorting/filtering by element properties
5. Add export to CSV/JSON with per-element format

**Files to Create**:
- `src/shypn/topology/aggregator/result_aggregator.py`
- `src/shypn/topology/aggregator/__init__.py`

**Files to Modify**:
- `src/shypn/ui/panels/topology/base_topology_category.py` (display logic)

**Time Estimate**: 1-2 days

---

### Phase 3: Batch Analysis System (MEDIUM PRIORITY)
**Goal**: Enable overnight analysis

**Tasks**:
1. Create persistent cache directory structure
2. Implement `BatchAnalyzer` class
3. Create CLI tool `batch_topology_analysis.py`
4. Add cache loading in UI panel
5. Document batch analysis workflow
6. Add cache management commands (clear, list, etc.)

**Files to Create**:
- `src/shypn/topology/batch/batch_analyzer.py`
- `src/shypn/topology/batch/cache_manager.py`
- `scripts/batch_topology_analysis.py`
- `doc/BATCH_TOPOLOGY_ANALYSIS.md`

**Time Estimate**: 2-3 days

---

## 📝 Testing Plan

### Test 1: Size Guard Validation
```python
# Small model (10 places) - Should work
model_small = load_model("examples/small_network.xml")
analyzer = SiphonAnalyzer(model_small)
result = analyzer.analyze()
assert result.success == True

# Large model (30 places) - Should block
model_large = load_model("examples/large_network.xml")
analyzer = SiphonAnalyzer(model_large)
result = analyzer.analyze()
assert result.success == False
assert result.metadata['blocked'] == True
```

### Test 2: Per-Element Aggregation
```python
# Run all analyses
results = run_all_analyzers(model)

# Aggregate
aggregator = TopologyResultAggregator()
element_data = aggregator.aggregate(results)

# Verify structure
assert 'places' in element_data
assert 'transitions' in element_data
assert 'P1' in element_data['places']
assert 'p_invariants' in element_data['places']['P1']
```

### Test 3: Batch Analysis & Cache
```bash
# Run batch analysis
$ python scripts/batch_topology_analysis.py --model test.xml

# Check cache created
$ ls ~/.shypn/topology_cache/
# Should show: model_hash_abc123.json

# Load in UI - should use cache
$ python src/shypn.py test.xml
# Check that results appear instantly (from cache)
```

---

## 🎓 Documentation Needs

1. **User Guide**: How to use batch analysis for large models
2. **API Reference**: ResultAggregator class and output format
3. **Size Limits Table**: Clear chart of what model sizes are supported
4. **Performance Guide**: Estimated times for different model sizes
5. **Cache Management**: How to clear/manage cached results

---

## ✅ Success Criteria

1. **No More Freezes**: System never freezes regardless of user actions
2. **Helpful Blocks**: Clear messages explain why analysis blocked + alternatives
3. **Offline Capability**: Large models can be analyzed overnight
4. **Better UX**: Results organized by element, easier to understand
5. **Performance**: Fast interactive use + batch processing for heavy analyses

