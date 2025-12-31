# SHYpn - Stochastic Hybrid Petri Nets for Systems Biology

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GTK 3.0](https://img.shields.io/badge/GTK-3.0-blue.svg)](https://www.gtk.org/)

**Extended Biological Petri Net Framework with Weak Independence Theory for Pathway Modeling, Simulation, and Analysis**

SHYpn is a comprehensive GTK3-based platform for systems biology that combines stochastic hybrid Petri nets with weak independence theory to enable efficient modeling, simulation, and analysis of biological pathways and regulatory networks.

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

- ✅ **Stochastic Hybrid Petri Nets** - Extended biological Petri net formalism with immediate, timed, stochastic, and continuous transitions
- ✅ **Unified 13-Tuple Formalism** - Complete Extended Bio-PN definition integrating weak independence and signal hierarchy (December 2025)
- ✅ **Signal Hierarchy Theory** - Information-theoretic framework for hierarchical control with signal token consumption semantics
- ✅ **Weak Independence Theory** - Efficient simulation through dependency analysis (convergent, competitive, regulatory coupling)
- ✅ **Two-Phase Execution** - Hierarchical constraint propagation via signal flow arcs (enabling check vs. consumption)
- ✅ **Arc Type Classification** - Normal, test, signal_flow, and inhibitor arcs with distinct consumption semantics
- ✅ **Visual Editor** - Intuitive GTK3-based pathway modeling interface
- ✅ **KEGG/SBML Import** - Direct import from major pathway databases
- ✅ **Real-time Simulation** - Multiple firing policies with live visualization
- ✅ **Topology Analysis** - Structural analysis including P/T-invariants, deadlocks, and liveness properties
- ✅ **Graph Layouts** - Automatic, hierarchical, force-directed, and manual layout algorithms
- ✅ **BRENDA Integration** - Kinetic parameter enrichment from BRENDA enzyme database
- ✅ **Project Management** - Organize models, pathways, and simulation results
- ✅ **Modern UI** - GTK3/Wayland native Linux desktop integration

## Documentation

📚 **[Quick Start Guide](QUICKSTART.md)** - Get started in minutes  
📚 **[Installation Guide](INSTALL.md)** - Detailed installation instructions  
📚 **[User Documentation](doc/README.md)** - Comprehensive guides and tutorials (locally available)

For development documentation, architecture details, and API reference, see the local `doc/` directory after cloning.

## Project Structure

```
shypn/
├── src/shypn/          # Main application source code
│   ├── core/           # Core Petri net engine
│   ├── simulation/     # Simulation algorithms
│   ├── ui/             # GTK user interface
│   └── analysis/       # Topology and structural analysis
├── cli/                # Command-line interface tools
├── ui/                 # GTK UI definitions (XML)
├── workspace/          # User workspace and example projects
│   └── projects/Biochemical-Examples/  # Demo models
├── QUICKSTART.md       # Quick start guide
├── INSTALL.md          # Installation instructions
└── LICENSE             # MIT License
```

**Note:** Development documentation, test suite, and utility scripts are available in the source repository but excluded from the public distribution.

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
@article{simao2025unified,
  title={Unifying Weak Independence and Signal Hierarchy Theory: Extended Biological Petri Net Formalism with Application to Vibrio fischeri Quorum Sensing},
  author={Sim{\~a}o, Eug{\'e}nio},
  journal={arXiv preprint},
  year={2025},
  note={Submitted to arXiv, December 2025}
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
- **Unified Formalism (2025)** - Extended 13-tuple Bio-PN integrating Weak Independence and Signal Hierarchy theories with V. fischeri quorum sensing validation
- **Foundation Paper (2025)** - [arXiv:2512.17106](https://arxiv.org/abs/2512.17106) - Weak Independence and Coupled Parallelism in Biological Petri Nets

**Software:** https://github.com/simao-eugenio/shypn

## Contact

**Eugênio Simão**  
Federal University of Santa Catarina (UFSC)  
Bioinformatics and Computational Systems Biology

## Contributing

Contributions are welcome! Please see the [development documentation](doc/README.md) for guidelines.

## Version

Current version: **v2.5.3** (December 2025)

**Recent Updates:**
- Unified Extended Bio-PN formalism manuscript (13-tuple definition)
- V. fischeri quorum sensing model with 133-fold bistability
- Signal saturation cascade figures (basin of attraction analysis)
- ArXiv submission package prepared
- Comprehensive directory cleanup (1.6GB freed)

See [CHANGELOG](doc/CHANGELOG.md) for complete version history.
