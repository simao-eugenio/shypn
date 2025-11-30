# SHYpn Quick Start Guide

**Version 2.4.7** - November 2025

Get up and running with SHYpn in minutes! This guide covers installation, basic usage, and troubleshooting.

## System Requirements

- **Operating System**: Linux (Ubuntu/Debian recommended), Windows (via WSL), macOS
- **Python**: 3.10 or higher
- **GTK**: 3.22 or higher
- **Display**: X11 or Wayland

## Installation

### Option 1: Standard Installation (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/simao-eugenio/shypn.git
cd shypn

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 3. Install SHYpn
pip install -e .
```

### Option 2: System Python (No Virtual Environment)

```bash
# Install system dependencies
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Run directly
python3 src/shypn.py
```

### Option 3: Conda Environment

```bash
# Create conda environment
conda create -n shypn python=3.10 -y
conda activate shypn

# Install PyGObject and GTK
conda install -c conda-forge pygobject gtk3 -y

# Fix GTK3 grid rendering (important for conda!)
export GI_TYPELIB_PATH=/usr/lib/x86_64-linux-gnu/girepository-1.0:$GI_TYPELIB_PATH
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Run SHYpn
python src/shypn.py
```

## Running SHYpn

### Quick Launch

```bash
# If installed with pip
python src/shypn.py

# Or if in virtual environment
source .venv/bin/activate
python src/shypn.py
```

### Convenience Script (Conda users)

Create a `run.sh` script:

```bash
#!/bin/bash
export GI_TYPELIB_PATH=/usr/lib/x86_64-linux-gnu/girepository-1.0:$GI_TYPELIB_PATH
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
python src/shypn.py
```

Then run:

```bash
chmod +x run.sh
./run.sh
```

## Basic Usage

### Creating Your First Model

1. **Launch SHYpn**: `python src/shypn.py`
2. **New Document**: `File → New` or `Ctrl+N`
3. **Add Places**: Click the circle tool in the Edit palette, then click on canvas
4. **Add Transitions**: Click the rectangle tool, then click on canvas
5. **Connect with Arcs**: Click the arc tool, click source, then click target
6. **Set Initial Marking**: Double-click a place, set tokens in the dialog
7. **Simulate**: Use the Simulate palette (`Run`, `Step`, `Reset`)

### Import from KEGG/SBML

1. `File → Import → KEGG Pathway` or `File → Import → SBML Model`
2. Enter pathway ID (e.g., `hsa00010` for glycolysis) or browse SBML file
3. Apply heuristic parameters and layout options
4. SHYpn will create a Petri net model automatically

### Key Shortcuts

- **Ctrl+N**: New document
- **Ctrl+O**: Open document
- **Ctrl+S**: Save document
- **Ctrl+Z**: Undo
- **Ctrl+Y**: Redo
- **Middle-click drag**: Pan canvas
- **Mouse wheel**: Zoom in/out
- **Double-click object**: Open properties dialog
- **Right-click**: Context menu

### Panel Controls

- **Master Palette**: Toggle between Files, Analyses, Pathways, Topology, Settings
- **Left Panel**: File explorer with project tree
- **Right Panel**: Analysis tools, data collection, topology reports
- **SwissKnife Palette**: Edit, Simulate, and Layout tools
- **Float/Attach**: Minimize/maximize buttons to detach panels to floating windows

## Features Overview

### Transition Types
- **Immediate**: Fire instantly when enabled (priority-based)
- **Timed**: Fire after fixed delay
- **Stochastic**: Fire with exponential distribution (Gillespie algorithm)
- **Continuous**: Fire continuously with rate functions (ODE simulation)

### Arc Types
- **Normal**: Standard input/output arcs with weights
- **Inhibitor**: Block transition when place has ≥ threshold tokens
- **Test Arc** (catalyst): Non-consuming read arcs

### Advanced Features
- **Source/Sink Places**: Infinite supply/capacity for boundary conditions
- **Parallel Arcs**: Multiple arcs between objects (automatic curving)
- **Graph Layouts**: Auto, hierarchical, horizontal tree, force-directed
- **Locality Analysis**: Automatic P-T-P pattern detection and plotting
- **Firing Policies**: Random, earliest, latest, priority, race, age, preemptive-priority
- **Real-Time Plotting**: Optimized analysis panel with 95% performance improvement

## Troubleshooting

### "No module named 'gi'" Error

**Problem**: PyGObject not installed

**Solution**:
```bash
# Virtual environment
pip install pygobject

# System packages
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Conda
conda install -c conda-forge pygobject gtk3
```

### Grid Not Appearing (Conda)

**Problem**: Conda GTK isolation from system Wayland backend

**Solution**: Set environment variables before running:
```bash
export GI_TYPELIB_PATH=/usr/lib/x86_64-linux-gnu/girepository-1.0:$GI_TYPELIB_PATH
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
python src/shypn.py
```

Or use the system Python approach:
```bash
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
/usr/bin/python3 src/shypn.py
```

### Windows (WSL/WSLg) Issues

**Problem**: GTK/Wayland inconsistencies under WSL

**Solution**: Use system site-packages virtual environment:
```bash
# One-time setup
python3 -m venv .venv --system-site-packages

# Always use system Python
source .venv/bin/activate
/usr/bin/python3 src/shypn.py
```

### Dialog Windows Not Appearing (Wayland)

**Problem**: Dialog parent window issues on Wayland

**Solution**: Already fixed in v2.4.7 (all dialogs set `transient_for` properly)

### Model Won't Simulate

**Common Issues**:
1. **No enabled transitions**: Check if transitions have sufficient input tokens
2. **Inhibitor arcs active**: Verify threshold values in arc properties
3. **Missing rate functions**: Continuous transitions need valid rate formulas
4. **Incorrect transition type**: Check transition properties (immediate/timed/stochastic/continuous)

**Debug Steps**:
1. Open Topology panel: Check "Why Transitions Don't Fire" report
2. Check transition properties: Double-click transition, verify type and parameters
3. Review console output: Run from terminal to see error messages

### SBML Import Failures

**Problem**: SBML file not loading or missing species

**Solution**:
- Install libSBML: `pip install python-libsbml`
- Check SBML validity: Use online validators (e.g., http://sbml.org/validator/)
- Enable "Filter isolated species": In import dialog, check the filter option

## Learning Resources

- **Full Documentation**: [`doc/README.md`](doc/README.md)
- **Examples**: Browse `workspace/examples/` for sample models
- **Tutorial Models**: `workspace/projects/Biochemical-Examples/`
- **Keyboard Shortcuts**: [`doc/KEYBOARD_SHORTCUTS_GUIDE.md`](doc/KEYBOARD_SHORTCUTS_GUIDE.md)
- **Coordinate System**: [`doc/COORDINATE_SYSTEM.md`](doc/COORDINATE_SYSTEM.md)

## Quick Reference

### File Operations
```
New             Ctrl+N
Open            Ctrl+O
Save            Ctrl+S
Save As         Ctrl+Shift+S
Close           Ctrl+W
```

### Editing
```
Undo            Ctrl+Z
Redo            Ctrl+Y
Delete          Delete
Select All      Ctrl+A
Deselect        Escape
```

### Canvas Navigation
```
Pan             Middle-click drag / Right-click drag
Zoom In         Mouse wheel up / Ctrl++
Zoom Out        Mouse wheel down / Ctrl+-
Zoom Reset      Ctrl+0
```

### Simulation
```
Step            (Simulate palette)
Run             (Simulate palette)
Pause           (Simulate palette)
Reset           (Simulate palette)
```

## Next Steps

1. **Explore Examples**: Open `workspace/examples/` and try the sample models
2. **Read Full Docs**: See [`doc/README.md`](doc/README.md) for architecture and advanced features
3. **Import Pathways**: Try importing a KEGG pathway (e.g., `hsa00010` for glycolysis)
4. **Create Projects**: Use File Panel to create organized project structures
5. **Join Community**: Report issues and contribute at [GitHub](https://github.com/simao-eugenio/shypn)

---

**Need More Help?**
- 📖 [Full Documentation](doc/README.md)
- 🐛 [Report Issues](https://github.com/simao-eugenio/shypn/issues)
- 💡 [Feature Requests](https://github.com/simao-eugenio/shypn/issues)

**Version**: 2.4.7 (November 2025)  
**License**: See [LICENSE](LICENSE) file
