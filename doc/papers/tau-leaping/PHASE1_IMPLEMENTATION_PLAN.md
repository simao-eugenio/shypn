# Phase 1 Implementation Plan: Code Finalization & Testing
**Branch**: `feature/papers-concurrent-transition-types`  
**Duration**: 2 weeks (Dec 5-19, 2025)  
**Goal**: Production-ready parallel τ-leaping with statistical validation

---

## Task Breakdown

### Week 1: Statistical Validation Infrastructure (Dec 5-12)

#### Task 1.1: Statistical Validator Module (2 days)
**File**: `src/shypn/engine/simulation/tau_leaping/statistical_validator.py`

**Requirements**:
```python
class StatisticalValidator:
    """Validate parallel vs sequential τ-leaping equivalence."""
    
    def compute_mae(self, trajectories_par, trajectories_seq) -> float:
        """Mean Absolute Error of final markings."""
        
    def compute_cv_error(self, trajectories_par, trajectories_seq) -> float:
        """Coefficient of Variation error."""
        
    def kolmogorov_smirnov_test(self, dist_par, dist_seq) -> Tuple[float, float]:
        """KS test: returns (D_statistic, p_value)."""
        
    def validate_equivalence(self, par_results, seq_results) -> Dict:
        """Full validation report with pass/fail for all metrics."""
```

**Acceptance Criteria**:
- [ ] MAE calculation for all species
- [ ] CV error with relative difference
- [ ] KS test implementation (scipy.stats.ks_2samp)
- [ ] Generate validation report (JSON + markdown)
- [ ] Unit tests: verify against known distributions

**Dependencies**: `scipy`, `numpy`, `pandas`

---

#### Task 1.2: Trajectory Comparator (2 days)
**File**: `src/shypn/engine/simulation/tau_leaping/trajectory_comparator.py`

**Requirements**:
```python
class TrajectoryComparator:
    """Compare parallel vs sequential simulation trajectories."""
    
    def collect_trajectories(self, controller, n_replicates=1000) -> Dict:
        """Run n_replicates and collect time-series data."""
        
    def compute_statistics(self, trajectories) -> Dict:
        """Compute mean, variance, CV for each species."""
        
    def plot_comparison(self, traj_par, traj_seq, output_path):
        """Generate comparison plots (mean ± std)."""
        
    def export_results(self, comparison, format='csv'):
        """Export trajectory data and statistics."""
```

**Acceptance Criteria**:
- [ ] Replicate runner (parallel and sequential modes)
- [ ] Time-series statistics (mean, variance, CV per timepoint)
- [ ] Matplotlib plots: mean trajectory with confidence bands
- [ ] CSV export for external analysis
- [ ] Memory-efficient streaming (handle 1000 replicates)

---

#### Task 1.3: Experimental Runner Script (1 day)
**File**: `scripts/run_tau_leaping_validation.py`

**Requirements**:
```bash
# Usage
python scripts/run_tau_leaping_validation.py \
    --model BIOMD0000000064.xml \
    --replicates 1000 \
    --duration 100.0 \
    --epsilon 0.03 \
    --output results/glycolysis_validation/
```

**Outputs**:
- `trajectories_parallel.csv`
- `trajectories_sequential.csv`
- `statistics_parallel.json`
- `statistics_sequential.json`
- `validation_report.md` (MAE, CV, KS results)
- `comparison_plots.pdf`

**Acceptance Criteria**:
- [ ] CLI argument parsing (argparse)
- [ ] Progress bar (tqdm)
- [ ] Error handling (model loading, simulation failures)
- [ ] Automatic validation report generation
- [ ] Random seed control for reproducibility

---

### Week 2: Performance Profiling & Optimization (Dec 12-19)

#### Task 2.1: Parallel Scheduler Review (2 days)
**File**: `src/shypn/engine/simulation/tau_leaping/parallel_scheduler.py`

**Review Checklist**:
- [ ] Verify dependency classification correctness
- [ ] Optimize partition algorithm (graph coloring)
- [ ] Add detailed logging (per-group timing)
- [ ] Profile thread pool overhead (cProfile)
- [ ] Test edge cases (all competitive, all independent)

**Profiling**:
```python
# Add instrumentation
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# ... parallel sampling ...
profiler.disable()

stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(20)  # Top 20 functions
```

**Expected Bottlenecks**:
- ThreadPoolExecutor overhead (solution: batch work units)
- Dependency graph construction (solution: cache between steps)
- Poisson sampling (solution: vectorize with numpy)

---

#### Task 2.2: Benchmarking Suite (2 days)
**File**: `scripts/benchmark_parallel_tau_leaping.py`

**Requirements**:
```python
def benchmark_model(model, n_replicates=100):
    """Run parallel and sequential, measure speedup."""
    
    times_seq = []
    times_par = []
    
    for i in range(n_replicates):
        # Sequential
        start = time.time()
        run_sequential(model)
        times_seq.append(time.time() - start)
        
        # Parallel
        start = time.time()
        run_parallel(model)
        times_par.append(time.time() - start)
    
    speedup = np.mean(times_seq) / np.mean(times_par)
    return speedup, times_seq, times_par
```

**Outputs**:
- Speedup statistics (mean, median, 95% CI)
- Violin plots (distribution of execution times)
- Scaling analysis (speedup vs thread count)

**Test Cases**:
- [ ] Small model (10 transitions, 90% independent)
- [ ] Medium model (50 transitions, 95% independent)
- [ ] Large model (200 transitions, 97% independent)
- [ ] High competition (30% competitive) - should show low speedup

---

#### Task 2.3: Integration Testing (1 day)
**File**: `tests/integration/test_parallel_tau_leaping.py`

**Test Scenarios**:
```python
def test_statistical_equivalence():
    """Parallel and sequential produce same distributions."""
    model = load_model("BIOMD0000000064.xml")
    
    par_results = run_parallel_replicates(model, n=1000)
    seq_results = run_sequential_replicates(model, n=1000)
    
    validator = StatisticalValidator()
    report = validator.validate_equivalence(par_results, seq_results)
    
    assert report['mae'] < 0.01  # 1% error
    assert report['cv_error'] < 0.05  # 5% error
    assert report['ks_pvalue'] > 0.05  # Not significantly different

def test_speedup_on_known_model():
    """Verify expected speedup on glycolysis model."""
    model = load_model("BIOMD0000000064.xml")
    
    speedup = benchmark_model(model, n_replicates=100)
    
    assert speedup > 1.5  # Expect at least 1.5× speedup
    assert speedup < 5.0  # Upper bound (sanity check)

def test_competitive_fallback():
    """High competitive coupling should use sequential."""
    model = create_competitive_model()  # 80% competitive
    
    speedup = benchmark_model(model, n_replicates=50)
    
    # Should be close to 1.0 (mostly sequential)
    assert 0.9 < speedup < 1.3
```

**Acceptance Criteria**:
- [ ] All tests pass with 95% confidence
- [ ] Continuous integration ready (pytest)
- [ ] Coverage report (>80% for tau_leaping module)

---

## Deliverables Checklist

### Code Artifacts
- [ ] `statistical_validator.py` (300 lines)
- [ ] `trajectory_comparator.py` (400 lines)
- [ ] `run_tau_leaping_validation.py` script (200 lines)
- [ ] `benchmark_parallel_tau_leaping.py` script (250 lines)
- [ ] Integration tests (200 lines)
- [ ] Unit tests for validator (150 lines)

### Documentation
- [ ] API documentation (docstrings)
- [ ] Usage examples in README
- [ ] Profiling report (identify bottlenecks)
- [ ] Validation report template

### Validation Results
- [ ] 10 preliminary models validated
- [ ] Statistical correctness confirmed (MAE < 1%, CV < 5%, KS p > 0.05)
- [ ] Speedup measurements (mean, distribution)
- [ ] Performance profile analysis

---

## Success Metrics

### Primary Goals (Must Have)
- ✅ Statistical validator passes on all 10 test models
- ✅ Mean speedup > 1.5× on models with >90% weak independence
- ✅ Zero statistical correctness failures (all KS tests pass)
- ✅ Production-ready code (tests, documentation, error handling)

### Stretch Goals (Nice to Have)
- 🎯 Mean speedup > 2.0× (exceeds baseline)
- 🎯 Automated CI pipeline (GitHub Actions)
- 🎯 Visualization dashboard (interactive plots)
- 🎯 Profiling-guided optimization (vectorized Poisson sampling)

---

## Test Models (10 Preliminary Models)

| ID | Model Name | Species | Reactions | % Independent | Expected Speedup |
|----|------------|---------|-----------|---------------|------------------|
| 64 | Glycolysis | 18 | 19 | 97.2% | 2.8× |
| 6  | MAPK | 8 | 10 | 95.5% | 2.5× |
| 12 | Circadian | 16 | 20 | 93.1% | 2.2× |
| 25 | Apoptosis | 23 | 28 | 96.8% | 2.9× |
| 240| JAK-STAT | 31 | 42 | 98.1% | 3.2× |
| 309| Cell Cycle | 45 | 58 | 97.5% | 3.0× |
| 415| Oscillator | 12 | 15 | 91.2% | 2.0× |
| 33 | Lac Operon | 9 | 12 | 89.3% | 1.8× |
| 7  | Cholesterol | 34 | 40 | 96.2% | 2.7× |
| 51 | TCA Cycle | 20 | 24 | 94.8% | 2.4× |

**Selection Criteria**:
- Range of complexities (8-45 species)
- Range of weak independence (89%-98%)
- Diverse biological processes
- Known to import successfully in SHYpn

---

## Risk Mitigation

### Risk 1: Statistical Tests Fail
**Symptom**: KS test p < 0.05 (distributions differ)  
**Debug Strategy**:
1. Check dependency classification (false competitive?)
2. Verify Poisson sampling seed consistency
3. Test on trivial model (2 independent transitions)
4. Compare propensity calculations (parallel vs sequential)

**Fallback**: If systematic failures, delay Phase 3 and fix root cause

---

### Risk 2: Low Speedup (<1.5×)
**Symptom**: Overhead dominates, parallel slower than sequential  
**Debug Strategy**:
1. Profile with cProfile (identify bottleneck)
2. Measure thread pool overhead (empty work units)
3. Test on large model (>100 transitions) where overhead amortizes
4. Consider Cython/C++ extension for hot paths

**Fallback**: Document overhead, focus on theoretical contribution (correctness proof)

---

### Risk 3: Python GIL Bottleneck
**Symptom**: Parallel execution uses only 1 CPU core  
**Investigation**:
1. Check with `htop` during parallel execution
2. Measure CPU utilization per thread
3. Profile GIL contention (sys.setswitchinterval)

**Solutions**:
- Use `multiprocessing` instead of `threading` (separate Python processes)
- Port critical sections to Cython (releases GIL)
- Acknowledge in paper, propose GPU/distributed as future work

---

## Daily Progress Tracking

### Week 1
- **Day 1-2**: Statistical validator + unit tests
- **Day 3-4**: Trajectory comparator + plotting
- **Day 5**: Experimental runner script + validation

### Week 2
- **Day 6-7**: Parallel scheduler review + profiling
- **Day 8-9**: Benchmarking suite + scaling tests
- **Day 10**: Integration tests + final validation

---

## Next Phase Preview

**Phase 2: Preliminary Testing (Dec 19-26)**
- Run validation on 10 models
- Generate validation reports
- Tune parameters (epsilon, thread count)
- Prepare for full 93-model run

**Phase 3: Full Experiments (Dec 26 - Jan 9)**
- 1,000 replicates × 93 models × 2 modes
- Collect all speedup and statistical data
- Generate publication-quality figures
- Statistical analysis (regression, correlation)

---

## Contact & Support

**Lead Developer**: Simão Eugénio  
**Branch**: `feature/papers-concurrent-transition-types`  
**Reference**: `doc/papers/tau-leaping/RESEARCH_ROADMAP.md`  
**Code Base**: `src/shypn/engine/simulation/tau_leaping/`

For questions or issues, refer to roadmap Section 6 (Experimental Validation) and Section 9 (Risk Mitigation).
