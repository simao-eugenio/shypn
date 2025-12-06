# Research Roadmap: Parallel Stochastic Simulation via Weak Independence

**Target Venue**: *Journal of Computational Biology* or *PLOS Computational Biology*  
**Expected Submission**: Q2 2026  
**Dependencies**: Foundation paper (weak independence theory) accepted/published

---

## Research Question

**Can weak independence theory enable parallel τ-leaping with provably correct stochastic semantics and measurable computational speedup?**

### Hypothesis

Convergent and regulatory coupling modes represent spatially distributed molecular events that can be sampled as **independent Poisson processes** during τ-leaping, while competitive coupling requires sequential execution to maintain token conservation.

**Expected Impact**: 2-4× speedup for stochastic simulation of biological models with >65% weakly independent transition pairs.

---

## Paper Structure (Target: 8-10 pages)

### 1. Introduction (1 page)

**Motivation**:
- τ-leaping provides orders-of-magnitude speedup over Gillespie SSA
- Classical τ-leaping is inherently sequential (Gillespie 2001)
- Biological networks have modular pathway structure
- **Gap**: No framework for parallel τ-leaping based on biological semantics

**Contributions**:
1. **Theoretical**: Proof that weakly independent transitions yield independent Poisson processes
2. **Algorithmic**: Dependency-aware parallel τ-leaping scheduler
3. **Experimental**: Speedup validation on 100 BioModels with statistical correctness verification

### 2. Background (1.5 pages)

#### 2.1 τ-Leaping Algorithm
- Gillespie's τ-leaping (2001): $K_j \sim \text{Poisson}(a_j \cdot \tau)$
- Leap condition: bounded relative change in propensities
- Adaptive τ selection (Cao et al. 2006)

#### 2.2 Weak Independence Theory (Brief)
- Reference foundation paper (Section 3.2)
- Three coupling modes: competitive, convergent, regulatory
- 96.93% weakly independent pairs in biological models

#### 2.3 Related Work
- **Parallel SSA**: Exact methods require synchronization barriers
- **GPU τ-leaping**: Assumes all reactions independent (incorrect for biology)
- **Hybrid methods**: Focus on continuous/stochastic partitioning, not parallelism

### 3. Theory: Independent Poisson Processes (2 pages)

#### 3.1 Mathematical Foundation

**Theorem 1 (Convergent Coupling Independence)**:  
If transitions $t_1, t_2$ share only output places ($\bullet t_1 \cap \bullet t_2 = \emptyset \land t_1^\bullet \cap t_2^\bullet \neq \emptyset$), then firing counts during τ-leaping are independent:
$$K_1 \perp K_2 \quad \text{where} \quad K_j \sim \text{Poisson}(a_j \cdot \tau)$$

**Proof Sketch**:
1. Propensities depend only on input place markings: $a_j = \phi_j(M[\bullet t_j])$
2. Input places disjoint: $\bullet t_1 \cap \bullet t_2 = \emptyset$
3. During leap interval $[t, t+\tau)$, propensities evolve independently
4. Poisson processes with independent intensities remain independent
5. QED: $P(K_1=k_1, K_2=k_2) = P(K_1=k_1) \cdot P(K_2=k_2)$

**Theorem 2 (Regulatory Coupling Independence)**:  
Test arcs (catalysts) do not consume tokens. If $t_1, t_2$ share only regulatory places ($\Sigma(t_1) \cap \Sigma(t_2) \neq \emptyset \land \bullet t_1 \cap \bullet t_2 = \emptyset$), then $K_1 \perp K_2$.

**Proof**: Regulatory arcs provide read-only access. Propensities depend on catalyst concentrations which remain constant during leap.

**Corollary 1 (Superposition)**:  
For convergent coupling, output marking evolution is additive:
$$M'(p) = M(p) + K_1 \cdot W(t_1, p) + K_2 \cdot W(t_2, p) \quad \forall p \in t_1^\bullet \cap t_2^\bullet$$

#### 3.2 Statistical Correctness Verification

**Definition (τ-Leaping Equivalence)**:  
Parallel and sequential τ-leaping are equivalent if:
1. Mean trajectory: $\mathbb{E}[M(t)] = \mathbb{E}[M_{\text{seq}}(t)]$ (first moment)
2. Variance: $\text{Var}[M(t)] = \text{Var}[M_{\text{seq}}(t)]$ (second moment)
3. Distribution shape: Kolmogorov-Smirnov test ($p > 0.05$)

**Verification Protocol**:
- Run 1,000 replicate simulations (parallel vs sequential)
- Compare trajectory statistics for each species
- Chi-square test for distribution equivalence

### 4. Algorithm: Parallel τ-Leaping Scheduler (2 pages)

#### 4.1 Dependency Graph Construction

**Input**: Petri net model $(P, T, F, W, \Sigma)$  
**Output**: Dependency groups $G = \{G_1, G_2, \ldots, G_k\}$ where $\forall t_i, t_j \in G_m$: $\Delta(t_i, t_j) \neq \text{Competitive}$

**Algorithm 1: Dependency Partitioning**
```
function PARTITION_TRANSITIONS(T, classifications):
    # Build conflict graph
    G_conflict ← empty graph with vertices T
    for (t1, t2, mode) in classifications:
        if mode == "competitive":
            add edge (t1, t2) to G_conflict
    
    # Find independent sets (graph coloring)
    groups ← COLOR_GRAPH(G_conflict)
    
    return groups  # Each color is a parallel group
```

**Complexity**: $O(|T|^2)$ for pairwise classification (done once), $O(|T| \log |T|)$ for coloring

#### 4.2 Parallel Sampling Protocol

**Algorithm 2: Parallel τ-Leaping Step**
```
function PARALLEL_TAU_LEAP(model, tau):
    # Phase 1: Compute propensities (sequential)
    propensities ← [compute_propensity(t) for t in T]
    
    # Phase 2: Partition transitions
    groups ← PARTITION_TRANSITIONS(T, dependency_classifications)
    
    firings ← {}
    
    # Phase 3: Sample each group in parallel
    for group in groups:
        if len(group) == 1:
            # Single transition - no parallelization
            t ← group[0]
            firings[t] ← Poisson(propensities[t] · tau)
        else:
            # Multiple independent transitions - parallel sampling
            parallel_firings ← SAMPLE_GROUP_PARALLEL(group, propensities, tau)
            firings.update(parallel_firings)
    
    # Phase 4: Apply all firings simultaneously
    new_marking ← UPDATE_MARKING(firings)
    
    return new_marking
```

**Thread Pool Management**:
- Worker count: `min(cpu_count, 8)` (diminishing returns beyond 8)
- Work distribution: `ThreadPoolExecutor` with futures
- Load balancing: Groups sorted by size (largest first)

#### 4.3 Critical Reaction Handling

**Problem**: Transitions with propensity near zero require exact SSA fallback (Cao et al. 2006)

**Solution**: Hybrid approach
- Critical transitions (propensity < threshold): Exact SSA (sequential)
- Non-critical transitions: Parallel τ-leaping
- Synchronize at each step

### 5. Implementation: SHYpn Engine (1 page)

**Architecture**:
```
src/shypn/engine/simulation/tau_leaping/
├── tau_leaping_engine.py       # Main coordinator
├── leap_selector.py            # Adaptive τ selection (Cao 2006)
├── poisson_sampler.py          # Kⱼ ~ Poisson(aⱼ·τ)
└── parallel_scheduler.py       # Parallel execution (THIS WORK)
```

**Key Features**:
- Dependency classification via `DependencyAndCouplingAnalyzer`
- Auto CPU detection: `os.cpu_count()`
- Statistics tracking: parallel vs sequential group counts
- Seamless fallback: `enable_parallel=False` for testing

**Usage Example**:
```python
from shypn.engine.simulation import SimulationController

controller = SimulationController(model)
controller.settings.use_tau_leaping = True
controller.settings.use_parallel = True
controller.run(time_step=0.1)
```

### 6. Experimental Validation (2 pages)

#### 6.1 Dataset

**BioModels Corpus**: Same 93 models from foundation paper
- ID ranges: 1-100, 200-299, 300-399, 400-499
- 1,775 species, 2,234 reactions (mean: 19 species, 24 reactions per model)
- Span metabolism, signaling, gene regulation

**Model Characteristics**:
| ID Range | Complexity | Stochastic Transitions | Weakly Independent % |
|----------|------------|------------------------|----------------------|
| 1-100    | Simple     | 18.3 ± 5.2            | 95.2%               |
| 200-299  | Moderate   | 22.1 ± 7.8            | 96.1%               |
| 300-399  | Complex    | 31.4 ± 11.3           | 97.8%               |
| 400-499  | Mixed      | 25.7 ± 9.5            | 96.4%               |

#### 6.2 Metrics

**Primary: Computational Speedup**
$$\text{Speedup} = \frac{T_{\text{sequential}}}{T_{\text{parallel}}}$$

**Secondary: Statistical Correctness**
1. **Mean Absolute Error (MAE)**: 
   $$\text{MAE} = \frac{1}{|P|} \sum_{p \in P} |\mathbb{E}[M_{\text{par}}(p)] - \mathbb{E}[M_{\text{seq}}(p)]|$$
   
2. **Coefficient of Variation Error**:
   $$\text{CV Error} = \frac{1}{|P|} \sum_{p \in P} \left|\frac{\text{CV}_{\text{par}}(p) - \text{CV}_{\text{seq}}(p)}{\text{CV}_{\text{seq}}(p)}\right|$$

3. **Kolmogorov-Smirnov Distance**: $D_{\text{KS}}$ for trajectory distributions

**Acceptance Criteria**:
- MAE < 1% of mean marking
- CV Error < 5%
- KS test: $p > 0.05$ (distributions indistinguishable)

#### 6.3 Experimental Protocol

**For each model**:
1. Run 1,000 replicate simulations (sequential τ-leaping)
2. Run 1,000 replicate simulations (parallel τ-leaping)
3. Record: execution time, final markings, trajectory statistics
4. Compute speedup and statistical correctness metrics

**Hardware**:
- CPU: AMD Ryzen 9 / Intel Xeon (8+ cores)
- RAM: 32 GB
- OS: Linux (Ubuntu 22.04)

**Configuration**:
- Simulation duration: 100 time units
- τ-leaping ε: 0.03 (Cao et al. default)
- Random seed: Fixed for reproducibility

#### 6.4 Expected Results

**Speedup Prediction**:
- **Best case (>95% weakly independent)**: 3.5-4.0× speedup
- **Average case (~96.5% weakly independent)**: 2.5-3.0× speedup
- **Worst case (high competitive coupling)**: 1.2-1.5× speedup

**Statistical Correctness**: All models expected to pass (MAE < 1%, CV Error < 5%, KS $p > 0.05$)

**Scaling Analysis**:
| CPU Cores | Expected Speedup | Efficiency |
|-----------|------------------|------------|
| 2         | 1.6×            | 80%        |
| 4         | 2.8×            | 70%        |
| 8         | 3.2×            | 40%        |
| 16        | 3.4×            | 21%        |

### 7. Results (Placeholder - to be filled after experiments)

#### 7.1 Speedup Distribution

**Figure 1**: Violin plot of speedup across 93 models
- X-axis: Model complexity (ID ranges)
- Y-axis: Speedup factor
- Median line, quartiles, individual points

**Table 1: Speedup Summary Statistics**
| Metric | Value |
|--------|-------|
| Mean speedup | TBD ± TBD |
| Median speedup | TBD |
| Best case | TBD (Model ID) |
| 75th percentile | TBD |
| Models with speedup > 2.0× | TBD% |
| Models with speedup > 3.0× | TBD% |

#### 7.2 Statistical Correctness Verification

**Figure 2**: Heatmap of statistical errors
- Rows: Models (93)
- Columns: MAE, CV Error, KS Distance
- Color scale: Green (pass) to Red (fail)

**Table 2: Statistical Correctness Results**
| Metric | Pass Rate | Mean Error | Max Error |
|--------|-----------|------------|-----------|
| MAE < 1% | TBD% | TBD | TBD |
| CV Error < 5% | TBD% | TBD | TBD |
| KS test ($p > 0.05$) | TBD% | TBD | TBD |

#### 7.3 Dependency Structure Impact

**Figure 3**: Scatter plot
- X-axis: % Weakly independent pairs
- Y-axis: Speedup
- Color: Model complexity
- Regression line with 95% CI

**Finding**: Linear relationship between weak independence and speedup (Pearson $r$ = TBD, $p$ < 0.001)

#### 7.4 Case Study: Glycolysis Model (BIOMD0000000064)

**Model Characteristics**:
- 19 reactions, 18 species
- 97.2% weakly independent pairs (169/173)
- 5 competitive pairs (glucose-6-phosphate competition)

**Results**:
- Sequential time: TBD seconds
- Parallel time: TBD seconds
- Speedup: TBD×
- Statistical correctness: MAE = TBD%, CV Error = TBD%, KS $p$ = TBD

**Trajectory Comparison**: Plot showing glucose, ATP, pyruvate concentrations (parallel vs sequential - indistinguishable)

### 8. Discussion (1 page)

#### 8.1 Theoretical Significance

**Novel Contribution**: First proof that biological coupling semantics (convergent/regulatory) correspond to independent Poisson processes in τ-leaping.

**Implications**:
- Weak independence is not just a scheduling heuristic - it's mathematically sound
- Biological network topology naturally enables parallelism
- Evolution optimized for computational efficiency (as noted in foundation paper)

#### 8.2 Practical Impact

**When to Use Parallel τ-Leaping**:
- ✅ Models with >90% weakly independent pairs → 2.5-4× speedup
- ✅ Large models (>50 species) → Amortizes thread overhead
- ❌ Small models (<20 species) → Sequential faster (overhead dominates)
- ❌ Models with high competitive coupling → Limited parallelism

**Comparison to GPU Approaches**:
- GPU τ-leaping assumes all reactions independent (biologically incorrect)
- Our method: Dependency-aware (guarantees correctness)
- Trade-off: Lower max speedup but statistically rigorous

#### 8.3 Limitations

**Current Implementation**:
- Thread-based parallelism (GIL limitations in Python)
- Overhead for small models
- Requires dependency analysis preprocessing

**Statistical Assumptions**:
- τ-leaping leap condition must hold (bounded propensity changes)
- Assumes Poisson approximation valid (molecule counts not too low)
- Implicit τ-leaping not yet supported (stiff systems may be slow)

#### 8.4 Future Directions

**Phase 4: GPU Acceleration**
- Port to CUDA/OpenCL for larger models (1000+ reactions)
- Expected speedup: 10-50× over sequential
- Challenge: Dependency graph on GPU

**Phase 5: Hybrid Continuous-Stochastic Parallelism**
- Fast reactions → ODE (continuous)
- Slow reactions → Parallel τ-leaping (stochastic)
- Reference: Haseltine & Rawlings (2002)

**Phase 6: Distributed Simulation**
- MPI-based parallelism across compute nodes
- Whole-cell models (10,000+ species)
- Genome-scale metabolic reconstructions

### 9. Conclusion (0.5 pages)

Weak independence theory, originally developed for continuous Petri nets, extends naturally to stochastic simulation via τ-leaping. We proved that convergent and regulatory coupling modes represent independent Poisson processes, enabling provably correct parallel sampling. Experimental validation on 93 diverse biological models demonstrates **TBD× mean speedup** with statistically indistinguishable trajectories.

**Key Takeaway**: *Biological network modularity is not just a conceptual framework - it's a computational resource for parallel simulation.*

**Impact**: Parallel stochastic simulation enables faster parameter estimation, model exploration, and whole-cell modeling, accelerating computational systems biology research.

---

## Experimental Implementation Plan

### Phase 1: Code Finalization (2 weeks)

**Tasks**:
- [ ] Review `parallel_scheduler.py` for completeness
- [ ] Add detailed logging (per-group statistics)
- [ ] Implement KS test in `statistical_validator.py`
- [ ] Create `trajectory_comparator.py` for MAE/CV calculations

**Deliverable**: Fully functional parallel τ-leaping with statistical validation

### Phase 2: Preliminary Testing (1 week)

**Tasks**:
- [ ] Test on 10 representative models
- [ ] Verify statistical correctness (MAE, CV, KS)
- [ ] Profile performance (identify bottlenecks)
- [ ] Tune thread pool parameters

**Deliverable**: Proof-of-concept results demonstrating correctness

### Phase 3: Full Experimental Run (2 weeks)

**Tasks**:
- [ ] Execute 1,000 replicates × 93 models × 2 modes (186,000 simulations)
- [ ] Collect all metrics (speedup, MAE, CV, KS)
- [ ] Generate plots (violin, heatmap, scatter)
- [ ] Statistical analysis (regression, correlation)

**Deliverable**: Complete results dataset with visualizations

### Phase 4: Paper Writing (4 weeks)

**Tasks**:
- [ ] Write theory section (Theorems 1-2 with proofs)
- [ ] Write algorithm section (pseudocode, complexity analysis)
- [ ] Write results section (tables, figures, case study)
- [ ] Write discussion (interpretation, limitations)
- [ ] Create supplementary materials (model list, code availability)

**Deliverable**: Draft manuscript ready for coauthor review

### Phase 5: Submission (2 weeks)

**Tasks**:
- [ ] Internal review and revisions
- [ ] Format for target journal
- [ ] Prepare cover letter
- [ ] Submit to *Journal of Computational Biology* or *PLOS Computational Biology*

**Deliverable**: Submitted manuscript

---

## Required Theoretical Proofs

### Proof 1: Convergent Coupling Independence (Detailed)

**Theorem**: For transitions $t_1, t_2$ with $\bullet t_1 \cap \bullet t_2 = \emptyset$ and $t_1^\bullet \cap t_2^\bullet \neq \emptyset$, the firing counts $K_1, K_2$ during interval $[t, t+\tau)$ are independent.

**Proof**:

1. **Propensity Independence**:
   - Propensity of $t_j$ at time $s \in [t, t+\tau)$: $a_j(s) = \phi_j(M(s)[\bullet t_j])$
   - Since $\bullet t_1 \cap \bullet t_2 = \emptyset$, propensities depend on disjoint place sets
   - Therefore: $a_1(s) \perp a_2(s)$ for all $s \in [t, t+\tau)$

2. **Poisson Process Construction**:
   - Let $N_j(s)$ be the cumulative firings of $t_j$ up to time $s$
   - $N_j$ is a Poisson process with intensity $\lambda_j(s) = a_j(s)$
   - For small $\Delta t$: $P(N_j(s+\Delta t) - N_j(s) = 1) = a_j(s) \Delta t + o(\Delta t)$

3. **τ-Leaping Approximation**:
   - Assume $a_j(s) \approx a_j(t)$ for $s \in [t, t+\tau)$ (leap condition)
   - Then: $K_j = N_j(t+\tau) - N_j(t) \sim \text{Poisson}(a_j(t) \cdot \tau)$

4. **Independence via Disjoint Inputs**:
   - During $[t, t+\tau)$, firings of $t_1$ only consume tokens from $\bullet t_1$
   - Firings of $t_2$ only consume tokens from $\bullet t_2$
   - Since $\bullet t_1 \cap \bullet t_2 = \emptyset$, consumption events are disjoint
   - Therefore: $P(K_1=k_1, K_2=k_2) = P(K_1=k_1) \cdot P(K_2=k_2)$

5. **QED**: $K_1 \perp K_2$ ∎

**Lemma (Leap Condition Preservation)**:  
If leap condition holds for sequential τ-leaping, it holds for parallel sampling of weakly independent transitions.

**Proof**: Leap condition requires $\max_j |\Delta a_j| < \epsilon \cdot a_j$. Since weakly independent transitions have disjoint input places, firing one does not affect propensity of others. Parallel sampling produces same total marking changes as sequential, preserving leap condition. ∎

### Proof 2: Regulatory Coupling Independence

**Theorem**: For transitions $t_1, t_2$ with $\Sigma(t_1) \cap \Sigma(t_2) \neq \emptyset$ (shared test arcs) and $\bullet t_1 \cap \bullet t_2 = \emptyset$, firing counts are independent: $K_1 \perp K_2$.

**Proof**:

1. **Test Arc Semantics**:
   - Test arc $(p, t)$ enables $t$ if $M(p) \geq \text{threshold}$
   - Firing $t$ does NOT consume tokens from $p$
   - Therefore: $M(p)$ remains constant during leap

2. **Propensity Evolution**:
   - $a_j(s)$ depends on both input places ($\bullet t_j$) and regulatory places ($\Sigma(t_j)$)
   - For regulatory places: $M(p)$ constant → regulatory contribution constant
   - For input places: $\bullet t_1 \cap \bullet t_2 = \emptyset$ → independent

3. **Independence Argument**:
   - Same as Proof 1, with additional constraint that shared regulatory places remain fixed
   - Fixed regulatory markings → propensities still independent
   - Therefore: $K_1 \perp K_2$ ∎

**Corollary (Enzyme Kinetics)**:  
For enzyme-catalyzed reactions with shared catalyst $E$:
$$t_1: S_1 \xrightarrow{E} P_1, \quad t_2: S_2 \xrightarrow{E} P_2$$
If $[E]$ is approximately constant during $\tau$, then $K_1 \perp K_2$. This justifies parallel sampling in metabolic models with enzyme conservation.

---

## Success Criteria

### Minimum Viable Paper (MVP)

**Required for Submission**:
- ✅ Theorems 1-2 with complete proofs
- ✅ Algorithm pseudocode with complexity analysis
- ✅ Experimental results on ≥50 models
- ✅ Statistical correctness validation (all models pass)
- ✅ Mean speedup >1.5× with significance test

### Stretch Goals (High-Impact)

**Bonus Results**:
- 🎯 Mean speedup >2.5× (competitive with GPU methods)
- 🎯 Case study with biological interpretation (e.g., circadian clock)
- 🎯 Scaling analysis up to 64 cores
- 🎯 Open-source release with reproducible benchmarks

---

## Risk Mitigation

### Technical Risks

**Risk 1: Low Speedup (<1.5×)**  
- **Mitigation**: Thread overhead analysis, optimize partition algorithm
- **Fallback**: Focus on theoretical contribution (correctness proof)

**Risk 2: Statistical Correctness Failures**  
- **Mitigation**: Debug using simple models (2-3 transitions)
- **Root Cause**: Likely dependency misclassification → fix analyzer

**Risk 3: Python GIL Bottleneck**  
- **Mitigation**: Profile with `cProfile`, consider Cython/C++ extension
- **Fallback**: Acknowledge limitation, propose GPU/distributed as future work

### Scientific Risks

**Risk 4: Theorem Proofs Incorrect**  
- **Mitigation**: Peer review with mathematicians/statisticians
- **Validation**: Monte Carlo simulation (verify independence empirically)

**Risk 5: Reviewer Concerns about Novelty**  
- **Defense**: "First application of biological dependency semantics to parallel stochastic simulation"
- **Evidence**: No prior work on weak independence for τ-leaping (literature review confirms)

---

## Timeline Summary

| Phase | Duration | Completion Date |
|-------|----------|-----------------|
| Phase 1: Code Finalization | 2 weeks | Dec 19, 2025 |
| Phase 2: Preliminary Testing | 1 week | Dec 26, 2025 |
| Phase 3: Full Experiments | 2 weeks | Jan 9, 2026 |
| Phase 4: Paper Writing | 4 weeks | Feb 6, 2026 |
| Phase 5: Submission | 2 weeks | Feb 20, 2026 |

**Total Time**: ~11 weeks (mid-February 2026 submission target)

---

## References (To be cited in paper)

### Foundational (τ-leaping)
1. Gillespie (2001) - Original τ-leaping
2. Cao et al. (2006) - Adaptive τ selection
3. Cao et al. (2005) - Negative population handling

### Weak Independence
4. Foundation paper (2025) - Weak independence theory
5. Murata (1989) - Classical Petri net independence

### Parallel Stochastic Simulation
6. Cao et al. (2014) - Parallel SSA (for comparison)
7. Dematté & Mazza (2008) - GPU acceleration (for comparison)

### Biological Networks
8. Karr et al. (2012) - Whole-cell model (motivation)
9. Kitano (2002) - Systems biology modularity

**Note**: Full bibliography in `references.bib` (inherit from foundation paper + add new)
