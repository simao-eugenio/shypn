# SHYpn - Systems Biology Pathway Modeling Platform

**Hybrid Petri Net Platform for Biological Pathway and Regulatory Network Modeling, Simulation, and Analysis**

A comprehensive GTK3-based platform for systems biology pathway modeling with advanced simulation and analysis capabilities.

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

- ✅ **Petri Net Editor** - Visual modeling of biological pathways
- ✅ **Hybrid Transitions** - Immediate, timed, stochastic, and continuous behaviors
- ✅ **KEGG/SBML Import** - Import pathways from major databases
- ✅ **Simulation Engine** - Real-time pathway simulation with multiple firing policies
- ✅ **Topology Analysis** - Structural analysis (P/T-invariants, deadlocks, liveliness)
- ✅ **Graph Layouts** - Auto, hierarchical, force-directed, and manual layouts
- ✅ **Project Management** - Organize models, pathways, and analyses
- ✅ **GTK3/Wayland** - Modern Linux desktop integration

## Documentation

📚 **[Full Documentation](doc/README.md)** - Comprehensive project documentation including:
- Architecture and design principles
- Feature guides and tutorials
- API reference
- Development guidelines
- Testing and validation

## Project Structure

```
shypn/
├── src/shypn/          # Main application source code
├── tests/              # Test suite and fixtures
├── doc/                # Comprehensive documentation
├── ui/                 # GTK UI definitions
├── scripts/            # Utility scripts
├── examples/           # Example models
└── workspace/          # User workspace (projects, models)
```

## Requirements

- Python 3.10+
- GTK 3.0
- PyGObject
- NetworkX
- libSBML (for SBML import)

## License

See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see the [development documentation](doc/README.md) for guidelines.

## Version

Current version: **2.4.7** (November 2025)

See [doc/README.md](doc/README.md) for full changelog and project status.
