# SHYpn - Extended Biological Petri Nets with Weak Independence

**Systems Biology Platform for Parallel Simulation of Metabolic and Regulatory Networks**

SHYpn implements Extended Biological Petri Nets (12-tuple formalism) with weak independence analysis, enabling parallel simulation of biochemical pathways while preserving biological correctness. The platform supports hybrid stochastic/continuous dynamics, regulatory control, and atomic mass balance validation.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux-lightgrey.svg)](https://www.linux.org/)

## Key Innovations

- **Weak Independence Theory**: Two-tier independence classification (strong vs weak) enabling parallelization of reactions sharing species under specific biological constraints
- **12-Tuple Formalism**: Extended Bio-PN definition including transition types (τ), formula tracking (ρ), regulatory arcs (Σ), and dependency taxonomy (Δ)
- **Biological Topology Validation**: Atomic mass balance checking, flux feasibility analysis, and thermodynamic consistency
- **Hybrid Simulation**: Seamless integration of stochastic (Gillespie) and continuous (ODE) transitions
- **Parallel Execution**: Multi-core simulation leveraging weak independence (2-4× speedup on realistic models)

## Research Context

This software implements the theory described in:

**Paper**: Eugênio Simão (2025). *"Weak Independence and Coupled Parallelism in Biological Petri Nets"*. [Submitted to Bioinformatics]

**Key Results** (validated on 100 BioModels):
- 65% of transition pairs are weakly independent (parallelizable)
- 2-4× speedup on multi-core systems with 67% reduction in false positives vs classical independence
- First tool to combine Petri net topology with biochemical validation (atomic formulas, regulatory arcs)

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/simao-eugenio/shypn.git
cd shypn

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# OR: .venv\Scripts\activate  # Windows

# Install SHYpn
pip install -e .

# Run GUI
python src/shypn.py
```

See [INSTALL.md](INSTALL.md) for detailed platform-specific instructions.

### Quick Example

```python
from shypn.core.biological_petri_net import BiologicalPetriNet
from shypn.simulation.hybrid_simulator import HybridSimulator

# Create enzyme-catalyzed reaction: Substrate + Enzyme → Product
net = BiologicalPetriNet()
substrate = net.add_place("Substrate", marking=100.0, formula="C6H12O6")
enzyme = net.add_place("Enzyme", marking=10.0, formula="ENZYME")
product = net.add_place("Product", marking=0.0, formula="C6H12O6")

reaction = net.add_continuous_transition(
    "Catalysis", 
    rate_function="michaelis_menten",
    vmax=5.0,
    km_substrates={"Substrate": 0.5}
)

net.add_arc(substrate, reaction, weight=1)
net.add_arc(enzyme, reaction, weight=0, arc_type="test")  # Catalyst not consumed
net.add_arc(reaction, product, weight=1)

# Simulate
simulator = HybridSimulator(net)
results = simulator.simulate(t_end=10.0, dt=0.1)
results.plot()
```

See `examples/` directory for comprehensive demonstrations including glycolysis, gene regulation, and allosteric control.

## Features

### Extended Biological Petri Net Formalism (12-tuple)

```
BioPN = (P, T, F, W, M₀, K, Φ, Σ, Θ, Δ, τ, ρ)
```

- **P, T, F**: Places (species), transitions (reactions), flow relation
- **W, M₀, K**: Arc weights, initial marking, place capacity
- **Φ**: Rate functions (mass action, Michaelis-Menten, Hill equations)
- **Σ**: Regulatory arcs (test, inhibitor with dynamic thresholds)
- **Θ**: Environmental exchange (source/sink classification)
- **Δ**: Dependency taxonomy (INDEPENDENT, COMPETITIVE, CONVERGENT, REGULATORY)
- **τ**: Transition types (IMMEDIATE, TIMED, STOCHASTIC, CONTINUOUS)
- **ρ**: Biochemical formulas for atomic mass tracking (C, H, O, N, P, S)

### Simulation and Analysis

- **Weak Independence Analyzer**: Classify transition pairs for parallel execution
- **Hybrid Simulator**: Gillespie (stochastic) + ODE (continuous) with event synchronization
- **Parallel Execution**: Multi-core simulation respecting weak independence constraints
- **Topology Analysis**: P/T-invariants, deadlock detection, liveness checking
- **Mass Balance Validation**: Atomic composition tracking ensuring conservation laws

### Integration

- **SBML Import**: Load models from BioModels, JWS Online, COPASI
- **KEGG Pathways**: Fetch and enrich metabolic pathways with EC numbers
- **BRENDA Database**: Query kinetic parameters (Km, Vmax, Ki, kcat)
- **Visual Editor**: GTK3-based GUI for interactive model construction

### Supported Kinetics

- Mass action (elementary reactions)
- Michaelis-Menten (enzyme catalysis)
- Hill equation (cooperative binding, allosteric regulation)
- Custom rate laws (user-defined Python functions)

## Examples

Comprehensive examples demonstrating key features:

1. **Hexokinase** (`examples/01_hexokinase_simple.py`) - Basic enzyme catalysis
2. **Glycolysis** (`examples/02_glycolysis_pathway.py`) - Multi-step pathway with weak independence
3. **Lac Operon** (`examples/03_lac_operon_regulation.py`) - Gene regulation with hybrid dynamics
4. **PFK Allosteric** (`examples/04_pfk_allosteric_inhibition.py`) - Dynamic threshold regulation

Run all examples:
```bash
cd examples/
bash run_all_examples.sh
```

See [examples/README.md](examples/README.md) for detailed descriptions.

## Documentation

- 📄 **Research Paper**: [Weak Independence in Biological Petri Nets](doc/papers/weak_independence_biopn.pdf)
- 📘 **Examples**: [examples/README.md](examples/README.md) - Comprehensive tutorial examples
- 🔧 **Installation**: [INSTALL.md](INSTALL.md) - Platform-specific setup instructions
- 📚 **Full Documentation**: [doc/README.md](doc/README.md) - Architecture, API, development guides

## Citation

If you use SHYpn in your research, please cite:

```bibtex
@article{simao2025weak,
  title={Weak Independence and Coupled Parallelism in Biological Petri Nets},
  author={Sim\~{a}o, Eug\^{e}nio},
  journal={[Submitted to Bioinformatics]},
  year={2025},
  note={Software available at \url{https://github.com/simao-eugenio/shypn}}
}
```

## Performance

Validated on 100 BioModels repository models:

| Metric | Value |
|--------|-------|
| Weak Independent Pairs | 65% |
| Speedup (8 cores) | 3.9× |
| Efficiency (8 cores) | 49% |
| False Positives | 5% (vs 72% classical) |
| Mass Balance Violations | 0% |

See paper Section 6 (Validation) and Section 7 (Performance Evaluation) for detailed benchmarks.

## Requirements

- **Python**: 3.10 or higher
- **GTK**: 3.0 (for GUI, optional for headless simulation)
- **Libraries**: PyGObject, NetworkX, NumPy, SciPy, Matplotlib

### Optional Dependencies

- `python-libsbml` - SBML import (`pip install python-libsbml`)
- `brenda_credentials.txt` - BRENDA database access (register at brenda-enzymes.org)

See [INSTALL.md](INSTALL.md) for platform-specific installation instructions (Linux/macOS/Windows WSL2).

## Project Structure

```
shypn/
├── src/shypn/              # Core implementation
│   ├── core/               # Petri net engine (places, transitions, arcs)
│   ├── simulation/         # Hybrid simulator (Gillespie + ODE)
│   ├── analysis/           # Weak independence analyzer, topology checker
│   ├── integration/        # KEGG, BRENDA, SBML importers
│   └── gui/                # GTK3 visual editor
├── tests/                  # Unit and integration tests (pytest)
├── examples/               # Tutorial examples (hexokinase, glycolysis, lac operon, PFK)
├── ui/                     # GTK UI definitions (.ui files)
├── doc/                    # Documentation and research paper
│   ├── papers/             # weak_independence_biopn.pdf
│   └── release/            # Release planning documentation
├── data/                   # Sample models and test datasets
├── workspace/              # User workspace (projects, cached data)
├── pyproject.toml          # Python package configuration
├── README.md               # This file
├── INSTALL.md              # Installation guide
└── LICENSE                 # MIT License
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! Areas of interest:
- Additional kinetic rate laws
- New example models (SBML import from BioModels)
- Performance optimizations (GPU acceleration, distributed simulation)
- Extended topology analysis (CTL model checking, reachability graphs)

Please open issues or pull requests on GitHub.

## Acknowledgments

- **BioModels**: Model validation dataset (https://www.ebi.ac.uk/biomodels/)
- **KEGG**: Pathway data (https://www.genome.jp/kegg/)
- **BRENDA**: Enzyme kinetic parameters (https://www.brenda-enzymes.org/)
- **Petri Net Community**: Foundation theory (Wolfgang Reisig, Monika Heiner, et al.)

## Version

**v1.0.0** (November 2025) - Initial public release

Major features:
- Extended 12-tuple formalism with weak independence
- Hybrid stochastic/continuous simulation
- Parallel execution (multi-core)
- SBML/KEGG/BRENDA integration
- 100 BioModels validation

See [doc/release/RELEASE_PLAN.md](doc/release/RELEASE_PLAN.md) for release history and roadmap.

## Contact

**Author**: Eugênio Simão  
**Institution**: Universidade Federal de Santa Catarina (UFSC), Computer Engineering  
**Location**: Araranguá, Brazil  
**Email**: eugenio.simao@ufsc.br  
**GitHub**: https://github.com/simao-eugenio/shypn

For research collaboration or technical questions, please open a GitHub issue or contact via email.
