# SHYpn - Signal Hierarchical Petri Nets

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GTK 3.0](https://img.shields.io/badge/GTK-3.0-blue.svg)](https://www.gtk.org/)

**Extended Biological Petri Net Framework with Signal Hierarchy Theory and Weak Independence for Systems Biology**

SHYpn (Signal Hierarchical Petri Nets) is a comprehensive GTK3-based platform for systems biology that integrates signal hierarchy theory, weak independence, and thermodynamic constraints to enable rigorous modeling, simulation, and analysis of biological pathways, regulatory networks, and cellular decision-making.

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/simao-eugenio/shypn.git
cd shypn
```

2. Create and activate virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Linux/Mac
```

3. Install dependencies:
```bash
pip install -e .
```

### Running SHYpn

```bash
python src/shypn.py
```

See [QUICKSTART.md](QUICKSTART.md) for detailed getting started guide.

## Model Examples

SHYpn includes **22 ready-to-use biochemical model examples** in the workspace:

**Location:** `workspace/projects/Biochemical-Examples/`

**Examples include:**
- 01_ATP_Hydrolysis - Basic energy metabolism
- 03_Hexokinase_MM - Michaelis-Menten kinetics
- 07_Upper_Glycolysis_Pathway - Multi-step pathways
- 09_Complete_Glycolysis - Full glycolytic pathway
- 17_Lac_Operon_Regulation - Gene regulation
- 19_Bacterial_Quorum_Sensing - Signal hierarchy (13-tuple formalism)
- 21_Hybrid_Glucose_Insulin - Hybrid simulation

**To use examples:**
1. Launch SHYpn: `python src/shypn.py`
2. Open File Explorer panel (left sidebar)
3. Navigate to `workspace/projects/Biochemical-Examples/`
4. Double-click any example folder to load the model

Each example includes complete documentation, simulation parameters, and expected results.

See `workspace/projects/Biochemical-Examples/README.md` for the complete catalog.

## Features

### Core Simulation & Theory
- ✅ **Signal Hierarchical Petri Nets (SHYpn)** - Extended biological Petri net formalism with immediate, timed, stochastic, and continuous transitions for hierarchical biological systems
- ✅ **Unified 13-Tuple Formalism** - Complete Extended Bio-PN definition integrating weak independence and signal hierarchy theory (December 2025)
- ✅ **Signal Hierarchy Theory** - Mathematical framework for hierarchical preemption and information-driven pathway selection with signal token consumption semantics
- ✅ **Weak Independence Theory** - Efficient simulation through dependency analysis (convergent, competitive, regulatory coupling)
- ✅ **Two-Phase Execution** - Hierarchical constraint propagation via signal flow arcs (enabling check vs. consumption)
- ✅ **Thermodynamic Constraints** - ATP-dependent rate modulation and Gibbs free energy validation ensure biophysical realism
- ✅ **τ-Leaping Engine** - Approximate stochastic simulation with Skellam distribution for reversible reactions (v0.3.0)

### SBML Import & Assignment Rules
- ✅ **Intelligent SBML Import** - Automatic detection of assignment rules and reversible reactions
- ✅ **Option 1: Continuous Mode** - Full ODE integration for maximum accuracy
- ✅ **Option 2: Enhanced Hybrid Mode** - Smart dependency tracking converts only affected transitions (v0.5.0)
- ✅ **Option 3: Stochastic with Re-evaluation** - Runtime formula evaluation maintains constraints (~7% overhead) (v0.5.0)
- ✅ **Skellam Distribution** - Net flux sampling for reversible reactions (forward - reverse)

### Thermodynamic Validation
- ✅ **Gibbs Free Energy Integration** - Validates rate constants against thermodynamic equilibrium (v0.4.0)
- ✅ **KEGG/ChEBI Database** - Automatic ΔG° lookup for compounds
- ✅ **K_eq vs k_ratio Validation** - Flags thermodynamically inconsistent reactions
- ✅ **Automated Warnings** - Clear categorization (valid, warning, violation, insufficient data)

### User Interface & Import
- ✅ **Arc Type Classification** - Normal, test, signal_flow, and inhibitor arcs with distinct consumption semantics
- ✅ **Visual Editor** - Intuitive GTK3-based pathway modeling interface
- ✅ **KEGG/SBML Import** - Direct import from major pathway databases with smart mode detection
- ✅ **Real-time Simulation** - Multiple firing policies with live visualization
- ✅ **Topology Analysis** - Structural analysis including P/T-invariants, deadlocks, and liveness properties
- ✅ **Graph Layouts** - Automatic, hierarchical, force-directed, and manual layout algorithms
- ✅ **BRENDA Integration** - Kinetic parameter enrichment from BRENDA enzyme database
- ✅ **Project Management** - Organize models, pathways, and simulation results
- ✅ **Modern UI** - GTK3/Wayland native Linux desktop integration

## Documentation

📚 **[Quick Start Guide](QUICKSTART.md)** - Get started in minutes  
📚 **[Installation Guide](INSTALL.md)** - Detailed installation instructions

**Core Features Documentation:**
- **Signal Hierarchy Theory** - Mathematical framework for hierarchical preemption (see papers below)
- **Weak Independence** - Efficient simulation through dependency analysis (arXiv:2512.17106)
- **Thermodynamic Validation** - Gibbs free energy integration (v0.4.0)
- **SBML Import Options** - Enhanced hybrid mode and stochastic assignment rules (v0.5.0)
- **τ-Leaping Engine** - Skellam distribution for reversible reactions (v0.3.0)

**Development Documentation:**  
Comprehensive development guides, architecture documentation, API reference, test suite, and utility scripts are available in the local source repository (`doc/`, `tests/`, `scripts/` directories) but excluded from public GitHub.

## Project Structure

```
shypn/
├── src/shypn/          # Main application source code
│   ├── engine/         # Simulation engines (stochastic, continuous, τ-leaping)
│   ├── data/           # Data models and pathway structures
│   ├── ui/             # GTK user interface components
│   ├── thermodynamics/ # Gibbs free energy validation (v0.4.0)
│   ├── repositories/   # Repository pattern with caching (v0.5.0)
│   ├── analyses/       # Topology, viability, and pathway analysis
│   └── export/         # Model export (SBML, SNOOPY, reports)
├── ui/                 # GTK UI definitions (XML)
├── workspace/          # User workspace and example projects
│   └── Biochemical-Examples/  # Demo models (22 examples)
├── QUICKSTART.md       # Quick start guide
├── INSTALL.md          # Installation instructions
├── CONTRIBUTING.md     # Contribution guidelines
├── CITATION.cff        # Citation metadata
└── LICENSE             # MIT License
```

**Development Resources (Local Only):**
- `doc/` - Architecture documentation, implementation guides, API reference (350+ documents)
- `tests/` - Test suite with 292+ tests (pytest)
- `scripts/` - Analysis and debugging scripts
- `tools/` - Model editing utilities (DTO-based)
- `dev/` - Development testbed and experiments
- `archive/` - Historical code and documentation

These development directories are git-ignored for public distribution but available when cloning the repository.

## Requirements

- **Python 3.10+**
- **GTK 3.0** - GNOME Toolkit for GUI
- **PyGObject** - Python bindings for GTK
- **NetworkX** - Graph algorithms and analysis
- **NumPy/SciPy** - Numerical computations
- **libSBML** - SBML format support (optional)
- **Requests** - KEGG/BRENDA API access (optional)

Full dependency list in [INSTALL.md](INSTALL.md).

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Citation

If you use SHYpn in your research, please cite:

```bibtex
@article{simao2026thermodynamic,
  title={Thermodynamic Constraints Drive Hierarchical Preemption in Bacillus subtilis Sporulation: A Signal Hierarchical Petri Net Analysis},
  author={Sim{\~a}o, Eug{\'e}nio},
  journal={arXiv preprint arXiv:2501.03850},
  year={2026},
  url={https://arxiv.org/abs/2501.03850}
}

@article{simao2026adaptation,
  title={Adaptation Dynamics Emerge from Signal Hierarchy Theory: Formal Semantics for Biological Petri Nets with Application to MAPK Cascades},
  author={Sim{\~a}o, Eug{\'é}nio},
  journal={bioRxiv preprint},
  year={2026},
  note={Submitted to bioRxiv, January 2026}
}

@article{simao2025weak,
  title={Weak Independence and Coupled Parallelism in Biological Petri Nets},
  author={Sim{\~a}o, Eug{\'e}nio},
  journal={arXiv preprint arXiv:2512.17106},
  year={2025},
  url={https://arxiv.org/abs/2512.17106}
}
```

**Latest Publications:**
- **Thermodynamic Hierarchy (2026)** - [arXiv:2501.03850](https://arxiv.org/abs/2501.03850) - Demonstrates 16× ATP reduction in stress-induced B. subtilis sporulation through hierarchical preemption
- **Signal Hierarchy Theory (2026)** - Formal semantics for Signal Hierarchical Petri Nets with MAPK adaptation analysis (bioRxiv submission)
- **Foundation Paper (2025)** - [arXiv:2512.17106](https://arxiv.org/abs/2512.17106) - Weak Independence and Coupled Parallelism in Biological Petri Nets

**Software:** https://github.com/simao-eugenio/shypn

## Contact

**Eugênio Simão**  
Federal University of Santa Catarina (UFSC)  
Bioinformatics and Computational Systems Biology

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Version

Current version: **v2.6.0** (February 2026)

**Recent Updates (v2.6.0 - February 2026):**
- ✅ **Option 2: Enhanced Hybrid Mode** - Smart dependency tracking for assignment rules
- ✅ **Option 3: Stochastic with Runtime Re-evaluation** - Full stochastic mode support for SBML assignment rules
- ✅ **Assignment Rule Infrastructure** - Formula compilation, caching, and temporal evaluation
- ✅ **Enhanced SBML Import Dialog** - Clear options for handling assignment rules and reversible reactions
- ✅ **Comprehensive Testing** - 11/11 tests passing for Options 2 & 3
- ✅ **Documentation** - Complete implementation guides in doc/ directory

**Previous Updates (v0.3.0 - v0.4.0):**
- Skellam distribution for reversible reactions in τ-leaping
- Thermodynamic validation with Gibbs free energy
- KEGG/ChEBI database integration for ΔG° values
- Unified Extended Bio-PN formalism manuscript (13-tuple definition)
- V. fischeri quorum sensing model with 133-fold bistability
- Signal saturation cascade analysis
- Comprehensive directory cleanup (1.6GB freed)
