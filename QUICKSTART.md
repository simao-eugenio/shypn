# SHYpn Quick Start Guide

Get started with SHYpn in just a few minutes!

## Installation

### 1. Prerequisites

Ensure you have Python 3.10+ and GTK 3.0 installed:

```bash
# On Ubuntu/Debian
sudo apt install python3 python3-pip python3-venv python3-gi python3-gi-cairo gir1.2-gtk-3.0

# On Fedora
sudo dnf install python3 python3-pip python3-gobject gtk3

# On Arch Linux
sudo pacman -S python python-pip python-gobject gtk3
```

### 2. Clone and Install

```bash
# Clone the repository
git clone https://github.com/simao-eugenio/shypn.git
cd shypn

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# .venv\Scripts\activate   # On Windows

# Install SHYpn
pip install -e .
```

### 3. Run SHYpn

```bash
python src/shypn.py
```

## First Steps

### Creating Your First Model

1. **Launch SHYpn** and you'll see the main window with:
   - **Pathway Panel** (left): Organize your models
   - **Canvas** (center): Design your Petri net
   - **Properties Panel** (right): Configure elements

2. **Add Places** (biological compounds/states):
   - Click "Add Place" button in toolbar
   - Click on canvas to place
   - Double-click to edit name and initial marking

3. **Add Transitions** (reactions/events):
   - Click "Add Transition" button
   - Click on canvas to place
   - Choose transition type: Immediate, Timed, Stochastic, or Continuous

4. **Connect with Arcs**:
   - Click "Add Arc" button
   - Click source, then destination
   - Set arc weights in properties panel

### Loading Example Models

1. Click **File → Open Project**
2. Navigate to `workspace/projects/Biochemical-Examples/`
3. Try these examples:
   - **Lambda Phage Switch** - Genetic regulatory network
   - **Circadian Clock** - Oscillatory behavior
   - **MAPK Cascade** - Signal transduction pathway

### Running Simulations

1. **Select Simulation Mode**:
   - Go to **Simulation → Configure**
   - Choose firing policy: Random, Priority, or Weak Independence

2. **Start Simulation**:
   - Click **Simulation → Start** (or press F5)
   - Watch tokens flow through the network in real-time
   - Use **Step** button for step-by-step execution

3. **View Results**:
   - **Marking History** shows token evolution
   - **Transition Firings** logs all events
   - Export data for further analysis

### Importing Pathways

#### From KEGG Database

1. **File → Import → KEGG Pathway**
2. Enter pathway ID (e.g., `hsa04010` for MAPK signaling)
3. Select compounds/reactions to include
4. SHYpn automatically creates the Petri net model

#### From SBML Files

1. **File → Import → SBML**
2. Select your `.xml` SBML file
3. Choose import options (species as places, reactions as transitions)
4. Model is ready for simulation

### BRENDA Kinetic Parameters

Enrich your model with real kinetic data:

1. Select a transition (reaction)
2. Click **Tools → Query BRENDA**
3. Search by enzyme name or EC number
4. Select Km, Kcat, or other parameters
5. Parameters are automatically assigned

## Key Concepts

### Petri Net Elements

- **Places** (circles): Represent biological compounds, proteins, or states
- **Transitions** (rectangles): Represent reactions, events, or processes
- **Arcs** (arrows): Define input/output relationships and stoichiometry
- **Tokens** (dots): Represent molecular counts or concentrations

### Transition Types

- **Immediate**: Fire instantly when enabled (regulatory switches)
- **Timed**: Fire after fixed delay (transcription, translation)
- **Stochastic**: Fire with exponential distribution (random processes)
- **Continuous**: Fire continuously based on ODEs (mass action kinetics)

### Weak Independence

SHYpn's key innovation for efficient simulation:

- Automatically detects independent transitions
- Enables parallel execution of non-conflicting events
- Reduces simulation time without affecting results
- Activated by selecting "Weak Independence" firing policy

## Analysis Tools

### Topology Analysis

**Analyze → Topology** provides:
- **P-invariants**: Conservation laws (mass conservation)
- **T-invariants**: Cyclic behaviors (metabolic cycles)
- **Deadlocks**: States where no transitions can fire
- **Liveness**: Which transitions can always eventually fire

### Layout Algorithms

Organize your network automatically:
- **Auto Layout**: Quick automatic positioning
- **Hierarchical**: Layered structure (good for signaling cascades)
- **Force-Directed**: Physics-based layout (good for complex networks)
- **Manual**: Full control over positioning

## Common Workflows

### Workflow 1: KEGG Pathway Analysis

1. Import pathway from KEGG
2. Enrich with BRENDA kinetic parameters
3. Run weak independence simulation
4. Analyze topology and invariants
5. Export results

### Workflow 2: Custom Model Design

1. Create places for compounds
2. Add transitions for reactions
3. Connect with arcs
4. Set initial markings and parameters
5. Simulate and analyze

### Workflow 3: SBML Model Simulation

1. Import SBML file
2. Review and adjust model
3. Run continuous or stochastic simulation
4. Compare with ODE results
5. Export trajectory data

## Tips and Tricks

- **Undo/Redo**: Ctrl+Z / Ctrl+Shift+Z
- **Save Often**: Ctrl+S (auto-save every 5 minutes)
- **Zoom**: Ctrl+Scroll or View menu
- **Batch Simulations**: Use CLI tools in `cli/` directory
- **Custom Scripts**: Python API for advanced automation

## Troubleshooting

### GTK Import Errors

```bash
# Install missing GTK dependencies
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

### SBML Import Fails

```bash
# Install libSBML
pip install python-libsbml
```

### Simulation Runs Slow

- Enable "Weak Independence" firing policy
- Reduce simulation time span
- Increase time step for continuous transitions
- Close other applications

## Modular Architecture (Advanced)

### Signal Places and Modules

SHYpn supports **modular Bio-PN** with signal places (Ψ) for information flow:

#### When to Use Modules
- Multi-compartment models (nucleus, cytoplasm, mitochondria)
- Large pathway networks (glycolysis + TCA cycle)
- Multi-cellular systems (quorum sensing)

#### Quick Example: Energy Sensing

```python
# Signal place for ATP/ADP ratio (read-only)
atp_ratio = create_place("ATP_Ratio")
atp_ratio.is_signal_place = True
atp_ratio.signal_type = SignalType.ENERGY
atp_ratio.tokens = 0.8  # High energy state

# Transition reads signal without consuming
pfk = create_transition("Phosphofructokinase")
pfk.rate_function = "Vmax * Glucose * (1 - ATP_Ratio)"
```

#### SBML Auto-Import with Modules

When importing SBML with compartments:
1. **File → Import → SBML**
2. Compartments become modules automatically
3. Cross-compartment modifiers become signal places
4. Analyze with: `python -m cli.analysis.module_analysis model.json`

#### Manual Module Creation

1. **Create module**: Right-click → "Create Module"
2. **Assign places/transitions**: Select → Set "Module ID" in properties
3. **Designate signals**: Check "Is Signal Place" in place properties
4. **Validate**: Use CLI analysis tool to check architecture quality

**Learn more**: See [doc/MODULAR_BIOPN_GUIDE.md](doc/MODULAR_BIOPN_GUIDE.md) for comprehensive guide

## Next Steps

- **Full Documentation**: See `doc/` directory for in-depth guides
- **Modular Architecture**: [doc/MODULAR_BIOPN_GUIDE.md](doc/MODULAR_BIOPN_GUIDE.md) for modules and signals
- **Installation Guide**: [INSTALL.md](INSTALL.md) for advanced setup
- **API Reference**: Explore `src/shypn/` for programmatic access
- **Examples**: Study models in `workspace/projects/Biochemical-Examples/`

## Publication

SHYpn is based on the weak independence theory published on arXiv:

**[arXiv:2512.17106](https://arxiv.org/abs/2512.17106)** - *Weak Independence and Coupled Parallelism in Biological Petri Nets*

If you use SHYpn in your research, please cite this paper.

## Getting Help

- **GitHub Issues**: Report bugs or request features
- **Contact**: See README.md for author contact information
- **Community**: Share models and scripts in Discussions

---

**Ready to explore?** Launch SHYpn and start with the Lambda Phage Switch example!
