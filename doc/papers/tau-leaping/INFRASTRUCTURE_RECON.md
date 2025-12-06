# SHYpn Infrastructure Reconnaissance Report
**Date**: December 5, 2025  
**Branch**: `feature/papers-concurrent-transition-types`  
**Purpose**: Assess readiness for parallel τ-leaping paper experiments

---

## Executive Summary

**Status**: 🟡 **PARTIALLY READY** - Core simulation works, but missing experimental automation infrastructure

**Good News**: 
- ✅ Core τ-leaping engine implemented (480 lines)
- ✅ Parallel scheduler with dependency classification (360 lines)
- ✅ Data export infrastructure EXISTS (CSV/JSON exporters)
- ✅ SBML import pipeline works
- ✅ Foundation paper scripts show the pattern to follow

**Bad News**:
- ❌ No replicate runner (must implement)
- ❌ No batch processing for multiple models (must implement)
- ❌ No statistical validation scripts (must implement)
- ❌ Existing exporters are GUI-triggered, not programmatic API

---

## Detailed Component Analysis

### 1. ✅ **Simulation Engine** (READY)

#### Location: `src/shypn/engine/simulation/`

**τ-Leaping Implementation**:
```
tau_leaping/
├── tau_leaping_engine.py (480 lines) ✅
├── leap_selector.py (346 lines) ✅
├── poisson_sampler.py (158 lines) ✅
└── parallel_scheduler.py (360 lines) ✅
```

**Controller Integration**:
```python
# Line 925-966 in controller.py
if self.settings.use_tau_leaping:
    self._tau_leaping_engine.execute_step(self)
```

**Settings**:
```python
# Line 41-46 in settings.py
DEFAULT_USE_TAU_LEAPING = True
DEFAULT_USE_PARALLEL_STOCHASTIC = True
```

**Verdict**: ✅ **Core engine ready** - Can run single τ-leaping simulations

---

### 2. 🟡 **Data Collection** (EXISTS BUT LIMITED)

#### Location: `src/shypn/engine/simulation/data_collector.py`

**What Exists** (155 lines):
```python
class DataCollector:
    def start_collection(self)
    def record_state(self, current_time: float)
    def record_firing(self, time, transition, ...)
    
    # Storage
    self.time_points: List[float]
    self.place_data: Dict[str, List[int]]
    self.transition_data: Dict[str, List[int]]
```

**Capabilities**:
- ✅ Records time-series (time points, place tokens, firing counts)
- ✅ Tracks events during simulation
- ✅ Integrated with SimulationController

**Limitations**:
- ❌ No built-in statistics computation (mean, variance, CV)
- ❌ No trajectory comparison methods
- ❌ No export API (data stays in memory)

**Verdict**: 🟡 **Works but needs extension** - Add `get_statistics()` and `export_trajectories()` methods

---

### 3. ✅ **Export Infrastructure** (EXISTS)

#### Location: `src/shypn/reporting/exporters/`

**Available Exporters**:
```
exporters/
├── csv_simulation_exporter.py (297 lines) ✅
├── json_simulation_exporter.py (207 lines) ✅
└── plot_exporter.py (290 lines) ✅
```

**CSV Exporter Capabilities**:
```python
class CSVSimulationExporter:
    def export_timeseries_wide(self, filepath)  # Species as columns
    def export_timeseries_long(self, filepath)  # Tidy format
    def export_summary_statistics(self, filepath)  # Mean/std/min/max
```

**JSON Exporter Capabilities**:
```python
class JSONSimulationExporter:
    def export_full(self, filepath)  # Complete data + metadata
    def export_trajectories(self, filepath)  # Time-series only
```

**Current Limitation**:
- ⚠️ GUI-triggered only (via Export toolbar button)
- ⚠️ Requires `simulation_data` dict structure
- ⚠️ Not directly callable from scripts

**Fix Needed** (1 day):
```python
# Add programmatic API to DataCollector
def export_csv(self, filepath, format='wide'):
    exporter = CSVSimulationExporter(self.get_data(), metadata={})
    exporter.export_timeseries_wide(filepath)
```

**Verdict**: ✅ **Exists, needs API wrapper** - 80% done, just need programmatic interface

---

### 4. ❌ **Replicate Runner** (MISSING)

**What's Needed**:
```python
class ReplicateRunner:
    """Run multiple stochastic simulation replicates."""
    
    def run_replicates(self, n=1000, seed_base=42):
        """Run n independent simulations with different seeds."""
        results = []
        for i in range(n):
            # Reset model to initial state
            controller = SimulationController(self.model)
            controller.settings.random_seed = seed_base + i
            
            # Run simulation
            controller.run()
            
            # Collect trajectory
            results.append(controller.data_collector.get_data())
        
        return results
    
    def compute_statistics(self, results):
        """Compute mean, variance, CV across replicates."""
        # Stack trajectories
        # Compute statistics per timepoint per species
        return statistics
```

**Location**: `src/shypn/engine/simulation/replicate_runner.py` (NEW FILE)

**Effort**: 2-3 days
- Day 1: Basic replicate loop
- Day 2: Statistics computation (mean, variance, CV)
- Day 3: Integration tests

**Verdict**: ❌ **Critical missing piece** - Must implement for paper

---

### 5. ❌ **Batch Model Processing** (MISSING)

**What's Needed**:
```python
class BatchModelProcessor:
    """Process multiple models in batch."""
    
    def load_models_from_list(self, csv_path):
        """Load models from CSV (BioModels IDs)."""
        # Parse CSV with columns: model_id, sbml_path
        # Return list of (id, model) tuples
    
    def process_batch(self, models, experiment_func):
        """Run experiment_func on each model."""
        results = {}
        for model_id, model in models:
            try:
                result = experiment_func(model)
                results[model_id] = result
            except Exception as e:
                results[model_id] = {'error': str(e)}
        
        return results
    
    def export_batch_results(self, results, output_dir):
        """Export results to output_dir/model_id/..."""
```

**Location**: `src/shypn/data/batch/batch_processor.py` (NEW MODULE)

**Effort**: 2-3 days
- Day 1: Model loading from CSV
- Day 2: Batch processing loop with error handling
- Day 3: Result aggregation and export

**Verdict**: ❌ **Critical missing piece** - Must implement for 93-model experiments

---

### 6. ✅ **SBML Import** (READY)

#### Location: `src/shypn/data/pathway/sbml_parser.py`

**Capabilities** (666 lines):
```python
class SBMLParser:
    def parse_file(self, filepath) -> PathwayData
    # Extracts species, reactions, kinetics, compartments
```

**Works With**:
- BioModels database files
- Tested on 93 models (foundation paper)
- Handles kinetic laws, compartments, units

**Integration**:
```python
from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_converter import PathwayConverter

parser = SBMLParser()
pathway = parser.parse_file("BIOMD0000000064.xml")

converter = PathwayConverter()
doc_model = converter.convert(pathway)
# Now doc_model ready for simulation
```

**Verdict**: ✅ **Fully functional** - Used successfully in foundation paper

---

### 7. 🟡 **Dependency Analysis** (READY)

#### Location: `src/shypn/topology/biological/dependency_coupling.py`

**Capabilities** (441 lines):
```python
class DependencyAndCouplingAnalyzer(TopologyAnalyzer):
    def analyze(self) -> AnalysisResult
        # Returns:
        # - strongly_independent: List[(t1, t2)]
        # - competitive: List[(t1, t2)]
        # - convergent: List[(t1, t2)]
        # - regulatory: List[(t1, t2)]
        # - statistics: Counts and percentages
```

**Used By**: `parallel_scheduler.py` (line 97-124)

**Verdict**: ✅ **Production ready** - Already used in foundation paper

---

### 8. ❌ **Statistical Validation** (MISSING)

**What's Needed**:
```python
class StatisticalValidator:
    """Validate parallel vs sequential equivalence."""
    
    def compute_mae(self, traj1, traj2):
        """Mean Absolute Error."""
        # |E[M_par] - E[M_seq]|
    
    def compute_cv_error(self, traj1, traj2):
        """Coefficient of Variation error."""
        # |CV_par - CV_seq| / CV_seq
    
    def ks_test(self, dist1, dist2):
        """Kolmogorov-Smirnov test."""
        from scipy.stats import ks_2samp
        return ks_2samp(dist1, dist2)
    
    def validate_equivalence(self, par_results, seq_results):
        """Full validation report."""
        return {
            'mae': ...,
            'cv_error': ...,
            'ks_statistic': ...,
            'ks_pvalue': ...,
            'passes': mae < 0.01 and cv_error < 0.05 and ks_pvalue > 0.05
        }
```

**Location**: `scripts/validation/statistical_validator.py` (EXTERNAL SCRIPT)

**Dependencies**: `scipy`, `numpy`, `pandas`

**Effort**: 2 days
- Day 1: Implement MAE, CV, KS tests
- Day 2: Generate validation reports (markdown + JSON)

**Verdict**: ❌ **Must implement** - Core paper validation

---

### 9. 📚 **Foundation Paper Scripts** (REFERENCE AVAILABLE)

#### Location: `doc/papers/foundation/scripts/`

**Available Scripts**:
```
scripts/
├── fetch_biomodels_dataset.py ✅ (Download BioModels)
├── benchmark_parallel_simulation.py ✅ (Speedup measurement)
├── classify_all_dependencies.py ✅ (Dependency analysis)
├── validate_topology.py ✅ (Correctness checks)
├── validate_sbml_conversion.py ✅ (Import validation)
└── run_all_experiments.sh ✅ (Orchestration)
```

**Key Insight**: These scripts show the **pattern to follow** for τ-leaping paper

**Example Pattern** (from `benchmark_parallel_simulation.py`):
```python
# 1. Load model from SBML
parser = SBMLParser()
pathway = parser.parse_file(sbml_path)
converter = PathwayConverter()
doc_model = converter.convert(pathway)

# 2. Analyze dependencies
analyzer = DependencyAndCouplingAnalyzer(doc_model)
result = analyzer.analyze()

# 3. Run simulation (sequential)
controller = SimulationController(doc_model)
controller.settings.use_parallel = False
start = time.time()
controller.run(time_step=0.1, duration=100.0)
time_seq = time.time() - start

# 4. Run simulation (parallel)
controller2 = SimulationController(doc_model)
controller2.settings.use_parallel = True
start = time.time()
controller2.run(time_step=0.1, duration=100.0)
time_par = time.time() - start

# 5. Compute speedup
speedup = time_seq / time_par
```

**Verdict**: ✅ **Excellent reference** - Copy this pattern for τ-leaping scripts

---

## Missing Features Summary

### Critical (Must Have)
| Feature | Status | Effort | Priority |
|---------|--------|--------|----------|
| Replicate Runner | ❌ Missing | 2-3 days | 🔥 P0 |
| Batch Processor | ❌ Missing | 2-3 days | 🔥 P0 |
| Statistical Validator | ❌ Missing | 2 days | 🔥 P0 |
| Export API Wrapper | 🟡 80% done | 1 day | ⚠️ P1 |

### Nice to Have
| Feature | Status | Effort | Priority |
|---------|--------|--------|----------|
| Trajectory Plots | ✅ Exists (plot_exporter.py) | 0 days | ✅ Done |
| Basic Statistics | 🟡 Partial | 1 day | 💡 P2 |
| CI/CD Pipeline | ❌ Missing | 3 days | 💡 P3 |

---

## Revised Implementation Roadmap

### **Phase 0: Foundation Setup** (Week 1: Dec 5-12)

#### Day 1-2: Replicate Runner
**File**: `src/shypn/engine/simulation/replicate_runner.py`
```python
class ReplicateRunner:
    def run_replicates(self, model, n=1000, **kwargs) -> List[Dict]
    def compute_statistics(self, results) -> Dict
    def compare_distributions(self, results1, results2) -> Dict
```

**Tests**: `tests/engine/simulation/test_replicate_runner.py`
- Test: 10 replicates produce different results (stochastic)
- Test: Statistics match analytical solution (simple model)

---

#### Day 3: Export API Wrapper
**File**: Add methods to `src/shypn/engine/simulation/data_collector.py`
```python
def get_data(self) -> Dict:
    """Return data in format expected by exporters."""
    return {
        'time_points': self.time_points,
        'place_data': self.place_data,
        'transition_data': self.transition_data,
        'model': self.model
    }

def export_csv(self, filepath, format='wide'):
    """Programmatic CSV export."""
    from shypn.reporting.exporters import CSVSimulationExporter
    exporter = CSVSimulationExporter(self.get_data(), {})
    if format == 'wide':
        exporter.export_timeseries_wide(filepath)
    else:
        exporter.export_timeseries_long(filepath)
```

**Tests**: `tests/engine/simulation/test_data_export.py`
- Test: Export CSV and verify format
- Test: Reload CSV and verify data integrity

---

#### Day 4-5: Batch Model Processor
**File**: `src/shypn/data/batch/batch_processor.py`
```python
class BatchModelProcessor:
    def load_from_csv(self, csv_path: str) -> List[Tuple[str, Any]]
    def process_batch(self, models, func) -> Dict[str, Any]
    def export_results(self, results, output_dir: str)
```

**Integration**: 
```python
# Load 93 models from foundation paper CSV
processor = BatchModelProcessor()
models = processor.load_from_csv("model_list.csv")

# Run experiment on each
def experiment(model):
    # Run τ-leaping validation
    return validate_tau_leaping(model)

results = processor.process_batch(models, experiment)
processor.export_results(results, "batch_results/")
```

**Tests**: `tests/data/batch/test_batch_processor.py`
- Test: Load 10 models from CSV
- Test: Process batch with mock function
- Test: Handle errors gracefully (skip failed models)

---

### **Phase 1: Experimental Scripts** (Week 2: Dec 12-19)

#### Day 6-7: Statistical Validator Script
**File**: `scripts/tau_leaping/statistical_validator.py`
```python
#!/usr/bin/env python3
import numpy as np
from scipy.stats import ks_2samp

def compute_mae(traj_par, traj_seq):
    """Mean Absolute Error across all species."""
    
def compute_cv_error(traj_par, traj_seq):
    """Coefficient of Variation error."""
    
def validate_equivalence(par_csv, seq_csv):
    """Load CSVs and perform full validation."""
    # Load data
    # Compute MAE, CV, KS
    # Generate report
    
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--parallel', required=True)
    parser.add_argument('--sequential', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    report = validate_equivalence(args.parallel, args.sequential)
    with open(args.output, 'w') as f:
        f.write(report)
```

---

#### Day 8-9: Single Model Validation Script
**File**: `scripts/tau_leaping/validate_single_model.py`
```python
#!/usr/bin/env python3
"""
Validate τ-leaping parallel vs sequential equivalence for one model.

Usage:
    python validate_single_model.py \
        --model BIOMD0000000064.xml \
        --replicates 1000 \
        --duration 100.0 \
        --output results/glycolysis/
"""
import argparse
import sys
from pathlib import Path

# Add SHYpn to path
sys.path.insert(0, str(Path(__file__).parents[2] / 'src'))

from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_converter import PathwayConverter
from shypn.engine.simulation.replicate_runner import ReplicateRunner
from shypn.engine.simulation.controller import SimulationController

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True, help='SBML file path')
    parser.add_argument('--replicates', type=int, default=1000)
    parser.add_argument('--duration', type=float, default=100.0)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    # Load model
    print(f"Loading model: {args.model}")
    sbml_parser = SBMLParser()
    pathway = sbml_parser.parse_file(args.model)
    converter = PathwayConverter()
    model = converter.convert(pathway)
    
    # Run parallel replicates
    print(f"Running {args.replicates} parallel replicates...")
    runner_par = ReplicateRunner(model)
    results_par = runner_par.run_replicates(
        n=args.replicates,
        use_parallel=True,
        use_tau_leaping=True,
        duration=args.duration
    )
    
    # Run sequential replicates
    print(f"Running {args.replicates} sequential replicates...")
    runner_seq = ReplicateRunner(model)
    results_seq = runner_seq.run_replicates(
        n=args.replicates,
        use_parallel=False,
        use_tau_leaping=True,
        duration=args.duration
    )
    
    # Export trajectories
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    runner_par.export_trajectories(results_par, output_dir / "parallel.csv")
    runner_seq.export_trajectories(results_seq, output_dir / "sequential.csv")
    
    # Compute statistics
    stats_par = runner_par.compute_statistics(results_par)
    stats_seq = runner_seq.compute_statistics(results_seq)
    
    # Export statistics
    import json
    with open(output_dir / "stats_parallel.json", 'w') as f:
        json.dump(stats_par, f, indent=2)
    with open(output_dir / "stats_sequential.json", 'w') as f:
        json.dump(stats_seq, f, indent=2)
    
    # Validate equivalence
    from scripts.tau_leaping.statistical_validator import validate_equivalence
    report = validate_equivalence(
        output_dir / "parallel.csv",
        output_dir / "sequential.csv"
    )
    
    with open(output_dir / "validation_report.md", 'w') as f:
        f.write(report)
    
    print(f"✅ Validation complete! Results in {output_dir}")
    
    # Print summary
    print("\n" + "="*60)
    print(report)
    print("="*60)

if __name__ == '__main__':
    main()
```

---

#### Day 10: Batch Validation Script
**File**: `scripts/tau_leaping/validate_batch.py`
```python
#!/usr/bin/env python3
"""
Validate τ-leaping on all 93 BioModels.

Usage:
    python validate_batch.py \
        --models ../../doc/papers/foundation/experimental_data/model_list.csv \
        --replicates 1000 \
        --output results/batch_validation/
"""
# Similar structure to validate_single_model.py
# But uses BatchModelProcessor to loop over all models
```

---

### **Phase 2: Preliminary Testing** (Week 3: Dec 19-26)

#### Tasks:
1. Test replicate runner on 3 simple models
2. Test batch processor on 10 models
3. Verify statistical validation passes
4. Tune parameters (epsilon, tau_max)
5. Fix any bugs discovered

---

### **Phase 3: Full Experiments** (Week 4-5: Dec 26 - Jan 9)

#### Tasks:
1. Run validation on all 93 models (1,000 replicates each)
2. Collect speedup data
3. Collect statistical correctness data
4. Generate plots (violin, heatmap, scatter)
5. Statistical analysis (regression, correlation)

---

## Effort Estimation

| Phase | Duration | Components | Lines of Code |
|-------|----------|------------|---------------|
| Phase 0: Foundation | 5 days | Replicate runner, Export API, Batch processor | ~800 lines |
| Phase 1: Scripts | 5 days | Validation scripts, Statistical validator | ~600 lines |
| Phase 2: Testing | 7 days | Manual validation, tuning | Testing only |
| Phase 3: Experiments | 14 days | Full 93-model run, analysis | Scripts usage |
| **Total** | **31 days (~4.5 weeks)** | | **~1,400 new lines** |

---

## Comparison to Original Roadmap

### Original Plan (Ambitious):
- Week 1-2: Build everything from scratch (1,500 lines)
- Week 3-4: Run experiments
- **Total**: 4 weeks

### Revised Plan (Realistic):
- Week 1: Core infrastructure (replicate, batch, export)
- Week 2: Experimental scripts
- Week 3: Preliminary testing (10 models)
- Week 4-5: Full experiments (93 models)
- **Total**: 4-5 weeks

### Key Difference:
Original plan assumed **ZERO** infrastructure exists. Reality: **~60% exists**, need to:
1. ✅ Use existing exporters (just add API)
2. ✅ Copy pattern from foundation scripts
3. ✅ Leverage existing SBML import and dependency analysis
4. 🆕 Build only: replicate runner, batch processor, validation scripts

---

## Risk Assessment

### Low Risk (High Confidence)
- ✅ Replicate runner (straightforward loop + statistics)
- ✅ Export API wrapper (80% done)
- ✅ Statistical validator (SciPy does the heavy lifting)

### Medium Risk (Moderate Confidence)
- ⚠️ Batch processor error handling (models may fail to import)
- ⚠️ Memory usage for 1,000 replicates (need streaming)

### High Risk (Needs Monitoring)
- 🔥 Computational time: 93 models × 1,000 replicates × 2 modes = 186,000 simulations
  - **Mitigation**: Run on cluster, parallelize across models
- 🔥 Statistical equivalence failures
  - **Mitigation**: Test on simple models first, debug if failures occur

---

## Recommendations

### Week 1 Priorities (CRITICAL PATH)
1. **Day 1-2**: Replicate runner (MUST HAVE)
2. **Day 3**: Export API (NICE TO HAVE, but easy)
3. **Day 4-5**: Batch processor (MUST HAVE)

### Week 2 Priorities
4. **Day 6-7**: Statistical validator script
5. **Day 8-9**: Single model validation script
6. **Day 10**: Test on 3 models, fix bugs

### Success Criteria (End of Week 2)
- ✅ Can run 1,000 replicates on 1 model
- ✅ Can export trajectories to CSV
- ✅ Can compute MAE, CV, KS statistics
- ✅ Validation passes on 3 test models

---

## Conclusion

**Original Assessment**: Roadmap was ambitious, assumed infrastructure missing

**Reality Check**: Infrastructure is **60% complete**
- ✅ Core simulation engine works
- ✅ Export infrastructure exists
- ✅ Foundation scripts show the pattern
- ❌ Missing: Replicate runner, batch processor, validation scripts

**Revised Timeline**: **4-5 weeks** (not 2 weeks)
- Week 1: Build infrastructure
- Week 2: Build scripts + preliminary testing
- Week 3-4: Full experiments

**Confidence Level**: 🟢 **HIGH** - The revised plan is achievable and realistic

**Next Action**: Start Phase 0, Day 1 - Implement `ReplicateRunner` class
