# SHYpn — Installation Guide

This guide covers every step needed to run SHYpn on a freshly provisioned machine.
SHYpn is a GTK3 desktop application; it requires both **system-level libraries** (installed
via your OS package manager) and **Python packages** (installed via pip).

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Ubuntu / Debian](#ubuntu--debian)
3. [Fedora / RHEL / CentOS](#fedora--rhel--centos)
4. [macOS](#macos)
5. [Windows (WSL2)](#windows-wsl2)
6. [Python Environment Setup](#python-environment-setup)
7. [Optional Dependencies](#optional-dependencies)
8. [Verifying the Installation](#verifying-the-installation)
9. [Troubleshooting](#troubleshooting)

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.10 | 3.11+ |
| GTK | 3.24 | 3.24+ |
| RAM | 2 GB | 8 GB (large models / sweeps) |
| Disk | 500 MB | 2 GB |
| OS | Linux (primary), macOS, WSL2 | Ubuntu 22.04+ |

> **Note:** SHYpn is developed and tested primarily on Linux.
> macOS and WSL2 are supported but receive less testing.

---

## Ubuntu / Debian

### 1. System packages

```bash
sudo apt update
sudo apt install -y \
    python3 python3-pip python3-venv \
    python3-gi python3-gi-cairo \
    gir1.2-gtk-3.0 gir1.2-glib-2.0 \
    libgtk-3-dev libcairo2-dev \
    libgirepository1.0-dev \
    pkg-config
```

On **Ubuntu 24.04+** or **Debian 13+** the package name changes slightly:

```bash
sudo apt install -y libgirepository-1.0-dev
```

### 2. Clone and install SHYpn

```bash
git clone https://github.com/simao-eugenio/shypn.git
cd shypn
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

### 3. Run

```bash
python src/shypn.py
```

---

## Fedora / RHEL / CentOS

### 1. System packages

```bash
# Fedora
sudo dnf install -y \
    python3 python3-pip \
    python3-gobject python3-cairo \
    gtk3-devel cairo-gobject-devel \
    gobject-introspection-devel \
    pkgconf

# RHEL / CentOS (enable EPEL first)
sudo dnf install -y epel-release
sudo dnf install -y python3 python3-pip gtk3 gobject-introspection
```

### 2. Clone and install SHYpn

```bash
git clone https://github.com/simao-eugenio/shypn.git
cd shypn
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

---

## macOS

### 1. Install Homebrew (if not present)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. System packages via Homebrew

```bash
brew install python@3.11 gtk+3 gobject-introspection cairo pkg-config pygobject3
```

### 3. Clone and install SHYpn

```bash
git clone https://github.com/simao-eugenio/shypn.git
cd shypn
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
# Tell pip where to find gobject-introspection headers
PKG_CONFIG_PATH="$(brew --prefix)/lib/pkgconfig" pip install -e .
```

### 4. Run (XQuartz not needed — macOS uses its own backend)

```bash
python src/shypn.py
```

> **Note:** macOS GTK3 rendering uses a native backend. Some UI scaling differences with
> Linux are expected.

---

## Windows (WSL2)

WSL2 with a graphical display is the recommended path on Windows.

### 1. Install WSL2 and Ubuntu 22.04

In an elevated PowerShell:

```powershell
wsl --install -d Ubuntu-22.04
```

### 2. Install a Wayland/X11 display server

- **Windows 11** ships WSLg (built-in display server) — no extra steps needed.
- **Windows 10** — install [VcXsrv](https://sourceforge.net/projects/vcxsrv/) and set:
  ```bash
  export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
  ```

### 3. Inside the WSL2 Ubuntu shell

Follow the **Ubuntu / Debian** steps above exactly.

---

## Python Environment Setup

All Python dependencies are declared in `pyproject.toml` and installed automatically by
`pip install -e .`.

The key Python packages pulled in are:

| Package | Purpose |
|---------|---------|
| `PyGObject` | GTK3 Python bindings |
| `pycairo` | Cairo drawing (GTK canvas) |
| `numpy` | Numerical arrays / simulation core |
| `scipy` | ODE solvers, statistical analysis |
| `matplotlib` | Embedded plots in the UI |
| `networkx` | Petri net graph algorithms |
| `weasyprint` | Report PDF generation |
| `openpyxl` | Excel export |
| `requests` | KEGG / BRENDA API access |
| `platformdirs` | Cross-platform config directories |

> **PyGObject / pycairo require system GTK headers** to compile.
> If you skip the `apt`/`dnf`/`brew` step above, pip will fail with a build error.

### Development extras

To set up a full development environment (linting, type checking, tests):

```bash
pip install -e ".[dev]"
```

This additionally installs: `pytest`, `mypy`, `ruff`, `pre-commit`.

---

## Optional Dependencies

### Numba acceleration

Speeds up the τ-leaping stochastic engine significantly on large models:

```bash
pip install -e ".[acceleration]"
# or
pip install numba>=0.59.0
```

### libSBML (SBML import)

SHYpn uses its own lightweight SBML parser by default.
For extended SBML compliance you can install the official libSBML Python bindings:

```bash
pip install python-libsbml
```

---

## Verifying the Installation

Run the built-in smoke test (no display required):

```bash
python -c "
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import numpy, scipy, matplotlib, networkx
print('All imports OK')
print('GTK version:', Gtk.get_major_version(), Gtk.get_minor_version())
print('NumPy:', numpy.__version__)
"
```

Expected output:

```
All imports OK
GTK version: 3 24
NumPy: 1.x.x
```

Then launch the application:

```bash
python src/shypn.py
```

---

## Troubleshooting

### `ImportError: No module named 'gi'`

PyGObject is not installed or the virtual environment can't see the system-level GTK.

```bash
# On Ubuntu/Debian — install the apt package then reinstall PyGObject inside venv
sudo apt install python3-gi libgirepository1.0-dev
pip install --force-reinstall PyGObject
```

### `pip install -e .` fails with `gobject-2.0` or `cairo` not found

The GTK development headers are missing:

```bash
sudo apt install libgtk-3-dev libcairo2-dev libgirepository1.0-dev pkg-config
```

### `Gtk-WARNING: cannot open display` (headless server)

SHYpn is a desktop GUI and requires a display server.
For remote machines, use X11 forwarding over SSH:

```bash
ssh -X user@server
python src/shypn.py
```

Or use a virtual framebuffer (for CI / automated testing only):

```bash
sudo apt install xvfb
Xvfb :99 -screen 0 1280x1024x24 &
DISPLAY=:99 python src/shypn.py
```

### `weasyprint` fails to import / PDF export broken

WeasyPrint has its own system dependencies:

```bash
sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0
```

### Slow startup on first run

SHYpn caches dependency graphs and GTK theme data on first launch.
Subsequent starts are significantly faster.
