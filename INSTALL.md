# SHYpn Installation Guide

Complete installation instructions for Extended Biological Petri Nets with Weak Independence platform.

## System Requirements

- **Operating System**: Linux (GTK 3.0 native), macOS (via XQuartz), Windows (WSL2)
- **Python**: 3.10 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended for large models (100+ species)
- **Disk Space**: 200MB for software + 500MB for workspace/cache
- **Display**: X11 or Wayland compositor (for GUI; headless simulation supported)

## Dependencies

### Core Dependencies (Installed Automatically)

- **PyGObject** - GTK 3.0 Python bindings for GUI
- **NetworkX** - Graph algorithms and topology analysis
- **NumPy** - Numerical computing and array operations
- **SciPy** - ODE solvers for continuous transitions
- **Matplotlib** - Plotting simulation results

### Optional Dependencies

- **python-libsbml** - SBML import from BioModels (`pip install python-libsbml`)
- **requests** - KEGG pathway fetching
- **pytest** - Running unit tests (`pip install pytest pytest-cov`)

---

## Quick Installation (Linux)

```bash
# 1. Clone repository
git clone https://github.com/simao-eugenio/shypn.git
cd shypn

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install SHYpn
pip install -e .

# 4. Run GUI
python src/shypn.py
```

---

## Detailed Platform-Specific Instructions

### Linux (Ubuntu/Debian)

#### Prerequisites

GTK 3.0 should be pre-installed. If missing:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
sudo apt install libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-3.0
```

#### Installation

```bash
# Clone repository
git clone https://github.com/simao-eugenio/shypn.git
cd shypn

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install SHYpn in editable mode
pip install -e .

# Verify installation
python -c "import shypn; print(f'SHYpn v{shypn.__version__} installed successfully')"
```

#### Running SHYpn

```bash
# Activate virtual environment (if not already activated)
source .venv/bin/activate

# Launch GUI
python src/shypn.py
```

---

### Linux (Fedora/RHEL)

#### Prerequisites

```bash
sudo dnf install python3 python3-pip
sudo dnf install python3-gobject gtk3
sudo dnf install cairo-devel cairo-gobject-devel gobject-introspection-devel
```

#### Installation

Follow same steps as Ubuntu (clone, venv, pip install -e .).

---

### macOS

#### Prerequisites

Requires Homebrew and XQuartz:

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install GTK and Python dependencies
brew install python@3.10 gtk+3 pygobject3 adwaita-icon-theme

# Install XQuartz for X11 support
brew install --cask xquartz
```

**Important**: After installing XQuartz, log out and log back in to activate X11 server.

#### Installation

```bash
# Clone repository
git clone https://github.com/simao-eugenio/shypn.git
cd shypn

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install SHYpn
pip install -e .
```

#### Running SHYpn on macOS

```bash
# Start XQuartz first
open -a XQuartz

# In terminal, activate venv
source .venv/bin/activate

# Set DISPLAY variable
export DISPLAY=:0

# Run SHYpn
python src/shypn.py
```

---

### Windows (WSL2)

SHYpn runs on Windows via Windows Subsystem for Linux 2 (WSL2) with Ubuntu.

#### Prerequisites

1. **Enable WSL2**:
   ```powershell
   # In PowerShell (Administrator)
   wsl --install
   wsl --set-default-version 2
   ```

2. **Install Ubuntu 22.04** from Microsoft Store

3. **Install X Server** (for GUI):
   - Download VcXsrv: https://sourceforge.net/projects/vcxsrv/
   - Or Xming: https://sourceforge.net/projects/xming/
   - Launch with: "Multiple windows", "Start no client", **Disable access control**

#### Installation in WSL2

```bash
# Inside WSL2 Ubuntu terminal
sudo apt update
sudo apt install python3 python3-pip python3-venv
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Clone repository
git clone https://github.com/simao-eugenio/shypn.git
cd shypn

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install SHYpn
pip install -e .
```

#### Running SHYpn on WSL2

```bash
# Set DISPLAY to Windows host
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0

# Or if above doesn't work
export DISPLAY=:0

# Run SHYpn
python src/shypn.py
```

**Tip**: Add `export DISPLAY=...` to `~/.bashrc` to avoid setting every time.

---

## Optional: SBML Import Support

To enable SBML import from BioModels:

```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# OR: .venv\Scripts\activate  # Windows

# Install libSBML
pip install python-libsbml

# Test SBML import
python -c "import libsbml; print(f'libSBML {libsbml.getLibSBMLDottedVersion()} installed')"
```

---

## Optional: BRENDA Database Integration

To enable kinetic parameter enrichment from BRENDA:

### 1. Register at BRENDA

Visit https://www.brenda-enzymes.org/ and create free account.

### 2. Create Credentials File

In repository root, create `brenda_credentials.txt`:

```
your_email@example.com
your_password
```

**Security**: This file is in `.gitignore` and will never be committed.

### 3. Verify Integration

```bash
python -c "from shypn.integration.brenda_enricher import BRENDAEnricher; enricher = BRENDAEnricher(); print('BRENDA connection successful')"
```

---

## Verification and Testing

### Verify Installation

```bash
# Check Python version
python --version  # Should be 3.10+

# Check SHYpn import
python -c "import shypn; print(shypn.__version__)"

# Check GTK availability
python -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk; print('GTK 3.0 available')"

# Check core dependencies
python -c "import networkx, numpy, scipy, matplotlib; print('All dependencies OK')"
```

### Run Unit Tests

```bash
# Install pytest
pip install pytest pytest-cov

# Run test suite
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/shypn --cov-report=html
```

### Run Examples

```bash
cd examples/

# Run individual example
python 01_hexokinase_simple.py

# Run all examples
bash run_all_examples.sh
```

Expected output: Console logs + PDF/PNG plots in `examples/` directory.

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'shypn'"

**Solution**: Install in editable mode:
```bash
cd /path/to/shypn
pip install -e .
```

### "ImportError: cannot import name 'Gtk' from 'gi.repository'"

**Solution**: Install GTK development packages:
```bash
# Ubuntu/Debian
sudo apt install libgirepository1.0-dev python3-gi

# macOS
brew install pygobject3 gtk+3
```

### "Failed to initialize Wayland display"

**Solution**: Force X11 backend:
```bash
export GDK_BACKEND=x11
python src/shypn.py
```

### "GTK Warning: cannot open display"

**Solution**:
- **Linux**: Ensure X server running (`echo $DISPLAY` should show `:0` or similar)
- **macOS**: Start XQuartz first (`open -a XQuartz`)
- **WSL2**: Set DISPLAY correctly (`export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0`)

### Slow Simulation on Large Models

**Solutions**:
1. Reduce time resolution: `simulator.simulate(t_end=100, dt=1.0)` instead of `dt=0.01`
2. Use approximate stochastic: `stochastic_method="tau_leaping"`
3. Enable parallel execution: `simulator.enable_parallel(num_cores=4)`

### BRENDA Connection Fails

**Solutions**:
1. Verify credentials in `brenda_credentials.txt`
2. Check internet connection
3. Ensure BRENDA account is active (verify by logging in on website)

---

## Headless Mode (No GUI)

SHYpn core simulation does not require GTK. For headless servers:

```bash
# Install without GUI dependencies
pip install -e . --no-deps
pip install networkx numpy scipy matplotlib

# Use Matplotlib non-interactive backend for batch processing
export MPLBACKEND=Agg

# Launch GUI application
python src/shypn.py
```

---

## Docker Installation (Experimental)

For containerized deployment:

```dockerfile
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
    libgirepository1.0-dev gcc libcairo2-dev pkg-config

WORKDIR /app
COPY . /app

RUN python3 -m venv .venv && \
    .venv/bin/pip install -e .

CMD [".venv/bin/python", "src/shypn.py"]
```

**Note**: GUI requires X11 forwarding (`docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix`).

---

## Uninstallation

```bash
# Remove virtual environment
rm -rf .venv

# Remove SHYpn repository
cd ..
rm -rf shypn

# Remove cached data (optional)
rm -rf ~/.cache/shypn
```

---

## Next Steps

After successful installation:

1. **Run Examples**: `cd examples/ && bash run_all_examples.sh`
2. **Read Documentation**: See [README.md](README.md) for feature overview
3. **Explore Paper**: Read [doc/papers/weak_independence_biopn.pdf](doc/papers/weak_independence_biopn.pdf)
4. **Import Models**: Try loading SBML from BioModels (if libsbml installed)

---

## Getting Help

- **Issues**: https://github.com/simao-eugenio/shypn/issues
- **Email**: eugenio.simao@ufsc.br
- **Documentation**: [doc/README.md](doc/README.md)

For installation problems, include:
- OS and version (`uname -a` on Linux/Mac)
- Python version (`python --version`)
- Error messages (full traceback)
- Installation method used
