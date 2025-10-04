# SHYpn - Installation and Environment Setup Guide

**Last Updated:** October 4, 2025

---

## Quick Start (Conda Users)

If you have conda and want to get started quickly:

```bash
# Make script executable
chmod +x setup_conda_env.sh

# Run setup (uses 'shypn' as environment name by default)
./setup_conda_env.sh

# Or specify a custom environment name
./setup_conda_env.sh my-shypn-env
```

Then:
```bash
conda activate shypn
python src/shypn.py
```

**Done!** 🎉

---

## Detailed Installation Guide

### Prerequisites

- **Operating System:** Ubuntu/Debian Linux (other distributions require manual dependency installation)
- **Python:** 3.8 or higher
- **Package Manager:** apt-get (for system packages)
- **Optional:** conda/miniconda for environment management

---

## Installation Methods

### Method 1: Automated Installation (Recommended)

**A. With Conda (Recommended for Development)**

```bash
# Make script executable
chmod +x install_dependencies.sh

# Run with conda environment support
./install_dependencies.sh --conda-env shypn
```

**B. Without Conda (System Python)**

```bash
# Make script executable
chmod +x install_dependencies.sh

# Run with system Python
./install_dependencies.sh
```

The script will:
- Install GTK3 system packages
- Install PyGObject
- Set up conda environment (if conda available)
- Verify installation
- Show you how to run the app

---

### Method 2: Manual Installation

#### Step 1: Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    libgtk-3-dev \
    libgirepository1.0-dev \
    gcc \
    libcairo2-dev \
    pkg-config \
    python3-dev
```

**Fedora/RHEL:**
```bash
sudo dnf install -y \
    python3-gobject \
    gtk3-devel \
    gobject-introspection-devel \
    cairo-gobject-devel \
    gcc \
    python3-devel
```

**Arch Linux:**
```bash
sudo pacman -S \
    python-gobject \
    gtk3 \
    gobject-introspection \
    cairo
```

#### Step 2: Set Up Python Environment

**Option A: Using Conda (Recommended)**

```bash
# Create conda environment
conda create -n shypn python=3.10 -y

# Activate environment
conda activate shypn

# Install PyGObject from conda-forge
conda install -c conda-forge pygobject gtk3 -y

# Install other dependencies
pip install -r requirements.txt
```

**Option B: Using venv (System Python)**

```bash
# Create virtual environment
python3 -m venv venv

# Activate environment
source venv/bin/activate

# Install PyGObject
pip install PyGObject

# Install other dependencies
pip install -r requirements.txt
```

**Option C: System Python (Not Recommended)**

```bash
# Install PyGObject
pip3 install --user PyGObject

# Install other dependencies
pip3 install --user -r requirements.txt
```

---

## Verification

After installation, verify that everything is working:

```bash
# Activate your environment first (if using conda or venv)
conda activate shypn  # or: source venv/bin/activate

# Test GTK3 import
python -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk; print('✓ GTK3 working!')"
```

If you see "✓ GTK3 working!" then you're all set!

---

## Running the Application

### With Conda:
```bash
conda activate shypn
python src/shypn.py
```

### With venv:
```bash
source venv/bin/activate
python src/shypn.py
```

### With System Python:
```bash
python3 src/shypn.py
```

---

## Troubleshooting

### Error: "No module named 'gi'"

**Solution 1:** Install PyGObject:
```bash
# For conda
conda install -c conda-forge pygobject

# For pip
pip install PyGObject

# For Ubuntu/Debian system packages
sudo apt-get install python3-gi
```

**Solution 2:** If using venv, you may need to allow system site-packages:
```bash
# Recreate venv with system packages
python3 -m venv --system-site-packages venv
source venv/bin/activate
```

---

### Error: "GTK3 not available"

**Cause:** System GTK3 libraries not installed.

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install gir1.2-gtk-3.0 libgtk-3-dev

# Then reinstall PyGObject
pip install --force-reinstall PyGObject
```

---

### Error: "cannot import name 'Gtk' from 'gi.repository'"

**Cause:** PyGObject not properly compiled against GTK3.

**Solution:**
```bash
# Install build dependencies
sudo apt-get install \
    libgirepository1.0-dev \
    libcairo2-dev \
    python3-dev \
    gcc

# Reinstall PyGObject
pip install --force-reinstall --no-binary :all: PyGObject
```

---

### Conda Environment Issues

**Problem:** Conda environment doesn't activate

**Solution:**
```bash
# Initialize conda for your shell
conda init bash

# Close and reopen terminal, then:
conda activate shypn
```

**Problem:** PyGObject conflicts with conda packages

**Solution:**
```bash
# Remove problematic packages
conda remove pygobject

# Install from conda-forge
conda install -c conda-forge pygobject gtk3
```

---

### Python Version Issues

**Problem:** System Python is too old (< 3.8)

**Solution:** Use conda to get a newer Python:
```bash
conda create -n shypn python=3.10
conda activate shypn
```

---

## Environment Management

### Listing Conda Environments
```bash
conda env list
```

### Activating/Deactivating
```bash
# Activate
conda activate shypn

# Deactivate
conda deactivate
```

### Removing Environment
```bash
conda env remove -n shypn
```

### Exporting Environment
```bash
# Export to file
conda env export > environment.yml

# Recreate from file
conda env create -f environment.yml
```

---

## Development Setup

For development, you might want additional tools:

```bash
conda activate shypn

# Install development tools
pip install pytest pytest-cov black flake8 mypy

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

---

## System Requirements

### Minimum:
- **OS:** Linux (Ubuntu 20.04+, Debian 10+, or equivalent)
- **Python:** 3.8+
- **RAM:** 512 MB
- **Disk:** 100 MB

### Recommended:
- **OS:** Ubuntu 22.04 LTS or later
- **Python:** 3.10+
- **RAM:** 2 GB+
- **Disk:** 500 MB (for dependencies)

---

## Dependencies Overview

### System Libraries (via apt-get):
- **GTK3** - GUI toolkit
- **PyGObject** - Python bindings for GTK3
- **Cairo** - 2D graphics library
- **GObject Introspection** - Runtime type information

### Python Packages (via pip/conda):
- **PyGObject** - Python GTK3 bindings

### Optional Python Packages:
- **pytest** - Testing framework
- **black** - Code formatter
- **flake8** - Linting
- **mypy** - Type checking

---

## Platform Support

### Fully Supported:
- ✅ Ubuntu 20.04+ (LTS)
- ✅ Debian 10+ (Buster)
- ✅ Linux Mint 20+
- ✅ Pop!_OS 20.04+

### Should Work:
- ⚠️ Fedora 34+
- ⚠️ Arch Linux
- ⚠️ openSUSE Leap 15.3+

### Not Supported:
- ❌ Windows (GTK3 support limited)
- ❌ macOS (GTK3 requires Homebrew, not tested)

---

## Uninstallation

### Remove Conda Environment:
```bash
conda env remove -n shypn
```

### Remove System Packages (Ubuntu/Debian):
```bash
# Remove GTK3 development files (be careful, other apps might need these)
sudo apt-get remove \
    libgtk-3-dev \
    libgirepository1.0-dev \
    libcairo2-dev

# Runtime libraries are usually needed by other applications
# so we recommend keeping: python3-gi, gir1.2-gtk-3.0
```

### Remove User Packages:
```bash
pip3 uninstall PyGObject
```

---

## Getting Help

If you encounter issues not covered in this guide:

1. **Check the console output** - Error messages usually indicate what's wrong
2. **Verify Python version:** `python --version` (need 3.8+)
3. **Verify GTK3:** `pkg-config --modversion gtk+-3.0`
4. **Check PyGObject:** `python -c "import gi; print(gi.__version__)"`
5. **Search for error messages** - Many GTK3/PyGObject issues are documented online
6. **Report an issue** - If you think it's a bug in SHYpn

---

## Quick Reference

### Conda Commands:
```bash
# Create environment
conda create -n shypn python=3.10

# Activate
conda activate shypn

# Install packages
conda install -c conda-forge pygobject gtk3

# Deactivate
conda deactivate

# Remove environment
conda env remove -n shypn
```

### Running the App:
```bash
# With conda
conda activate shypn && python src/shypn.py

# With venv
source venv/bin/activate && python src/shypn.py

# With system Python
python3 src/shypn.py
```

---

## Additional Resources

- **PyGObject Documentation:** https://pygobject.readthedocs.io/
- **GTK3 Documentation:** https://docs.gtk.org/gtk3/
- **Conda User Guide:** https://docs.conda.io/projects/conda/en/latest/user-guide/
- **Python venv:** https://docs.python.org/3/library/venv.html

---

**Installation Guide Version:** 1.0  
**Date:** October 4, 2025  
**Status:** Complete
