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

## Features

- ✅ **Stochastic Hybrid Petri Nets** - Extended biological Petri net formalism with immediate, timed, stochastic, and continuous transitions
- ✅ **Weak Independence Theory** - Efficient simulation through dependency analysis and partial order reduction
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
@article{shypn2025,
  title={SHYpn: Stochastic Hybrid Petri Nets with Weak Independence for Efficient Biological Pathway Simulation},
  author={Simão, Eugênio},
  journal={arXiv preprint},
  year={2025},
  note={Available at: https://github.com/simao-eugenio/shypn}
}
```

## Contact

**Eugênio Simão**  
Federal University of Santa Catarina (UFSC)  
Bioinformatics and Computational Systems Biology

## Contributing

Contributions are welcome! Please see the [development documentation](doc/README.md) for guidelines.

## Version

Current version: **v2.5.2** (December 2025)

See [CHANGELOG](doc/README.md) for version history and project status.
