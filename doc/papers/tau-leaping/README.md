# Parallel Stochastic Simulation Paper

**Working Title**: "Parallel τ-Leaping via Weak Independence Theory"  
**Status**: Planning Phase  
**Target Submission**: Q2 2026

---

## Overview

This paper demonstrates that **weak independence theory** (from the foundation paper) enables **provably correct parallel stochastic simulation** using τ-leaping. The key insight: convergent and regulatory coupling modes represent spatially distributed molecular events that can be sampled as **independent Poisson processes**.

**Expected Impact**: 2-4× speedup for biological models with ~96% weakly independent transition pairs.

---

## Key Innovation

### Problem
Classical τ-leaping (Gillespie 2001) is inherently sequential:
```
for each timestep τ:
    for each reaction j:
        Kⱼ ~ Poisson(aⱼ·τ)  # Sequential sampling
```

### Solution
Dependency-aware parallel sampling:
```
for each timestep τ:
    groups ← partition_by_weak_independence(transitions)
    
    parallel_for each group in groups:
        for each transition t in group:
            Kₜ ~ Poisson(aₜ·τ)  # Parallel sampling
```

### Theoretical Foundation
**Theorem**: If transitions $t_1, t_2$ are weakly independent (convergent or regulatory coupling), then their firing counts are independent Poisson random variables:
$$K_1 \perp K_2 \quad \text{where} \quad K_j \sim \text{Poisson}(a_j \cdot \tau)$$

This guarantees **statistical correctness** - parallel and sequential simulations produce identical distributions.

---

## Contributions

1. **Theoretical**: Proof that weak independence → independent Poisson processes
2. **Algorithmic**: Parallel τ-leaping scheduler with dependency classification
3. **Experimental**: Speedup validation on 93 BioModels with statistical correctness tests

---

## Directory Structure

```
doc/papers/tau-leaping/
├── README.md                    # This file
├── RESEARCH_ROADMAP.md          # Detailed roadmap (proofs, experiments, timeline)
├── paper.tex                    # LaTeX manuscript (from bioinformatics)
├── references.bib               # Bibliography
├── figures/                     # Plots and diagrams
│   ├── speedup_plot.pdf
│   └── dependency_graph.pdf
└── experimental_data/           # Results (to be created)
    ├── speedup_results.csv
    ├── statistical_correctness.csv
    └── trajectory_comparisons/
```

---

## Implementation Status

### ✅ Already Implemented
- `src/shypn/engine/simulation/tau_leaping/tau_leaping_engine.py`: Main τ-leaping loop
- `src/shypn/engine/simulation/tau_leaping/parallel_scheduler.py`: Parallel execution
- `src/shypn/engine/simulation/tau_leaping/leap_selector.py`: Adaptive τ selection
- `src/shypn/engine/simulation/tau_leaping/poisson_sampler.py`: Kⱼ ~ Poisson(aⱼ·τ)
- `src/shypn/topology/biological/dependency_coupling.py`: Dependency classifier

### 🚧 To Be Completed
- [ ] Statistical validator (KS test, MAE, CV error)
- [ ] Trajectory comparator (parallel vs sequential)
- [ ] Experimental scripts (batch runner for 93 models)
- [ ] Visualization scripts (violin plots, heatmaps)

---

## Experimental Protocol

### Dataset
- **Source**: BioModels database (same 93 models as foundation paper)
- **Characteristics**: 1,775 species, 2,234 reactions, 96.93% weakly independent pairs

### Metrics

**Primary**: Computational speedup
$$\text{Speedup} = \frac{T_{\text{sequential}}}{T_{\text{parallel}}}$$

**Secondary**: Statistical correctness
- **MAE** (Mean Absolute Error): $|\mathbb{E}[M_{\text{par}}] - \mathbb{E}[M_{\text{seq}}]|$
- **CV Error**: Coefficient of variation difference
- **KS Test**: Kolmogorov-Smirnov distance ($p > 0.05$ required)

### Acceptance Criteria
- ✅ All models: MAE < 1%, CV Error < 5%, KS $p > 0.05$
- ✅ Mean speedup > 1.5× (statistically significant)
- 🎯 Stretch goal: Mean speedup > 2.5×

---

## Theoretical Results

### Theorem 1: Convergent Coupling Independence
**Statement**: If $t_1, t_2$ share only output places ($\bullet t_1 \cap \bullet t_2 = \emptyset$), then $K_1 \perp K_2$.

**Proof Sketch**:
1. Propensities depend only on input places (disjoint)
2. Poisson processes with independent intensities remain independent
3. QED

### Theorem 2: Regulatory Coupling Independence
**Statement**: If $t_1, t_2$ share only test arcs (catalysts), then $K_1 \perp K_2$.

**Proof**: Test arcs don't consume tokens → catalyst markings constant → propensities independent.

**Corollary**: Enzyme-catalyzed reactions with shared catalyst can be sampled in parallel (common in metabolism).

---

## Timeline

| Milestone | Target Date |
|-----------|-------------|
| Code finalization | Dec 19, 2025 |
| Preliminary testing (10 models) | Dec 26, 2025 |
| Full experiments (93 models) | Jan 9, 2026 |
| Draft manuscript | Feb 6, 2026 |
| **Submission** | **Feb 20, 2026** |

---

## Related Work

### Parallel Stochastic Simulation
- **Cao et al. (2014)**: Parallel exact SSA (requires synchronization barriers)
- **Dematté & Mazza (2008)**: GPU τ-leaping (assumes all reactions independent - incorrect for biology)
- **Our Work**: Dependency-aware parallelism with biological correctness guarantees

### Weak Independence
- **Foundation Paper (2025)**: Introduced weak independence for continuous Petri nets
- **This Work**: Extends to stochastic simulation via τ-leaping

---

## Key References

1. **Gillespie (2001)** - "Approximate Accelerated Stochastic Simulation"  
   *Original τ-leaping algorithm*

2. **Cao et al. (2006)** - "Efficient Step Size Selection for Tau-Leaping"  
   *Adaptive τ selection (implemented in SHYpn)*

3. **Foundation Paper (2025)** - "Weak Independence in Biological Petri Nets"  
   *Theoretical foundation for this work*

Full bibliography: See `doc/REFERENCES_TAU_LEAPING_AND_HYBRID.md` (510 lines of references)

---

## How to Run Experiments

### Prerequisites
```bash
# Install SHYpn with tau-leaping support
cd /home/simao/projetos/shypn
pip install -e .

# Verify installation
python -c "from shypn.engine.simulation.tau_leaping import TauLeapingEngine; print('OK')"
```

### Single Model Test
```python
from shypn.data.sbml import SBMLImporter
from shypn.engine.simulation import SimulationController

# Load model
importer = SBMLImporter()
model = importer.import_from_file("BIOMD0000000064.xml")

# Configure simulation
controller = SimulationController(model)
controller.settings.use_tau_leaping = True
controller.settings.use_parallel = True
controller.settings.duration = 100.0

# Run and time
import time
start = time.time()
controller.run()
elapsed = time.time() - start

print(f"Simulation time: {elapsed:.2f}s")
```

### Batch Experiments (93 models)
```bash
# To be created: scripts/run_parallel_tau_leaping_experiments.py
python scripts/run_parallel_tau_leaping_experiments.py \
    --models experimental_data/model_list.csv \
    --replicates 1000 \
    --output experimental_data/results/
```

---

## Questions for Discussion

1. **Thread Count**: Currently auto-detected (`os.cpu_count()`). Should we expose as parameter?

2. **Critical Reactions**: How to handle very low propensity transitions (exact SSA fallback)?

3. **Hybrid Continuous-Stochastic**: Should this paper include hybrid methods or save for Phase 5?

4. **Genome-Scale Models**: Should we test on large metabolic reconstructions (1000+ reactions)?

---

## Contact

**Author**: Simão Eugénio  
**Affiliation**: TBD  
**Branch**: `feature/parallel-stochastic`  
**Code**: `src/shypn/engine/simulation/tau_leaping/`

For detailed roadmap, see `RESEARCH_ROADMAP.md`.
