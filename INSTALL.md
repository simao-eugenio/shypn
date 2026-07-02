# SHYpn — Installation Guide

**Primary platform: Ubuntu Linux 22.04 and 24.04 LTS.**

SHYpn is a GTK3 desktop application. It requires both system-level libraries
(installed via `apt`) and Python packages (installed via `pip`).

---

## Table of Contents

1. [One-script install (recommended)](#one-script-install-recommended)
2. [Manual install — Ubuntu 22.04 / 24.04](#manual-install--ubuntu-2204--2404)
3. [Display environments — Wayland, X11, WSL2](#display-environments)
4. [Optional dependencies](#optional-dependencies)
5. [Verifying the installation](#verifying-the-installation)
6. [Zip-archive install (no git)](#zip-archive-install-no-git)
7. [Other platforms](#other-platforms)
8. [Troubleshooting](#troubleshooting)

---

## One-script install (recommended)

The installer script handles system packages, venv creation, pip install, and
verification automatically. It detects your Ubuntu version and uses the correct
package names.

```bash
git clone https://github.com/simao-eugenio/shypn.git
cd shypn
bash install_ubuntu.sh
```

When it completes, launch SHYpn with:

```bash
source .venv/bin/activate
shypn
```

Or without activating the venv manually:

```bash
.venv/bin/shypn
```

---

## Manual install — Ubuntu 22.04 / 24.04

Use this if you prefer step-by-step control or need to customise the install.

### System requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| Python | 3.10 | 3.12 |
| GTK | 3.24 | 3.24+ |
| RAM | 2 GB | 8 GB (large models / sweeps) |
| Disk | 500 MB | 2 GB |

### 1. System packages

**Ubuntu 22.04:**

```bash
sudo apt update
sudo apt install -y \
    python3 python3-pip python3-venv \
    python3-gi python3-gi-cairo \
    gir1.2-gtk-3.0 gir1.2-glib-2.0 \
    libgtk-3-dev libcairo2-dev \
    libgirepository1.0-dev \
    pkg-config \
    libpango-1.0-0 libpangocairo-1.0-0 fonts-liberation
```

**Ubuntu 24.04** — one package name changed (dot → hyphen before the version):

```bash
sudo apt update
sudo apt install -y \
    python3 python3-pip python3-venv \
    python3-gi python3-gi-cairo \
    gir1.2-gtk-3.0 gir1.2-glib-2.0 \
    libgtk-3-dev libcairo2-dev \
    libgirepository-1.0-dev \
    pkg-config \
    libpango-1.0-0 libpangocairo-1.0-0 fonts-liberation
```

> **Key difference**: `libgirepository1.0-dev` (22.04) vs `libgirepository-1.0-dev` (24.04).
> Getting this wrong is the most common install failure.

### 2. Clone and create virtual environment

```bash
git clone https://github.com/simao-eugenio/shypn.git
cd shypn
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

### 3. Verify

```bash
python -m shypn --check
```

### 4. Launch

```bash
shypn
# or equivalently:
python src/shypn.py
```

---

## Display environments

SHYpn is a desktop GUI application. It requires a graphical display server.

### Native Ubuntu desktop (Wayland, X11)

On Ubuntu 22.04+ the default GNOME session is Wayland. SHYpn uses GTK3 which
supports Wayland natively — no extra flags needed.

```bash
shypn   # works on both Wayland and X11 GNOME sessions
```

SHYpn automatically detects `$WAYLAND_DISPLAY` (Wayland) or `$DISPLAY` (X11).
If neither is set the application exits with a clear error message.

### WSL2 (Windows 11 with WSLg)

Windows 11 ships WSLg, which provides a built-in Wayland/X11 display server.
Follow the Ubuntu manual steps inside your WSL2 shell — no extra display setup.

**Windows 10 / WSL2 without WSLg**: install
[VcXsrv](https://sourceforge.net/projects/vcxsrv/) on Windows, then:

```bash
export DISPLAY=$(grep nameserver /etc/resolv.conf | awk '{print $2}'):0
shypn
```

### SSH remote session (no display)

SHYpn cannot run headlessly. For remote machines use X11 forwarding:

```bash
ssh -X user@remotehost
shypn
```

You can use the command-line tools (sweep dispatch, model patch) without a
display. The `--check` flag also works without a display:

```bash
python -m shypn --check   # no display required
```

---

## Optional dependencies

### Numba acceleration

Speeds up the τ-leaping stochastic engine on large models:

```bash
pip install -e ".[acceleration]"
```

### GPU acceleration (CuPy + CUDA)

For NVIDIA GPUs. Requires CUDA 12+ and a compatible CuPy wheel:

```bash
pip install cupy-cuda12x   # adjust for your CUDA version
```

GPU support is auto-detected at runtime.

### Development tools

Full linting, type checking, and test setup:

```bash
pip install -e ".[dev]"
```

---

## Verifying the installation

The built-in `--check` command tests all imports and reports the display
environment. No display is required.

```bash
python -m shypn --check
```

Expected output:

```
SHYpn — installation check
  Python                 3.12.3

  numpy                  2.x.x ✓
  scipy                  1.x.x ✓
  matplotlib             3.x.x ✓
  …

  gi (GTK3)              3.24.x ✓

  shypn.engine.simulation.controller  ✓
  shypn.netobjs.place                 ✓
  …

  Display                :0  (GUI can start)

  SHYpn 2.6.1 ✓

  All checks passed.  Run 'shypn' (or 'python src/shypn.py') to launch.
```

---

## Zip-archive install (no git)

Download the zip from GitHub → **Code → Download ZIP**, extract it, then:

```bash
cd shypn-main          # or whatever the extracted directory is named
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .          # note: no -e flag for zip installs
python -m shypn --check
```

After a zip install, `shypn` (the console command) is available in the venv.
`python src/shypn.py` also still works from the extracted directory.

---

## Other platforms

SHYpn is developed and tested on Ubuntu. Other platforms are community-supported.

### Fedora / RHEL

```bash
sudo dnf install -y \
    python3 python3-pip \
    python3-gobject python3-cairo \
    gtk3-devel cairo-gobject-devel \
    gobject-introspection-devel pkgconf

git clone https://github.com/simao-eugenio/shypn.git
cd shypn
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip && pip install -e .
```

### macOS

```bash
brew install python@3.11 gtk+3 gobject-introspection cairo pkg-config pygobject3
git clone https://github.com/simao-eugenio/shypn.git
cd shypn
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
PKG_CONFIG_PATH="$(brew --prefix)/lib/pkgconfig" pip install -e .
```

---

## Troubleshooting

### `ImportError: No module named 'gi'`

PyGObject is not importable inside the venv. Install system headers then
force-reinstall inside the venv:

```bash
# Ubuntu 22.04
sudo apt install libgirepository1.0-dev python3-gi
pip install --force-reinstall PyGObject

# Ubuntu 24.04
sudo apt install libgirepository-1.0-dev python3-gi
pip install --force-reinstall PyGObject
```

### `pip install` fails: `gobject-2.0` or `cairo` not found

Missing GTK development headers:

```bash
# Ubuntu 22.04
sudo apt install libgtk-3-dev libcairo2-dev libgirepository1.0-dev pkg-config

# Ubuntu 24.04
sudo apt install libgtk-3-dev libcairo2-dev libgirepository-1.0-dev pkg-config
```

### Black / invisible window on WSL2

GTK must not initialise GDK before `Gtk.Application.run()`. This is fixed in the
current release. Update with `git pull` and reinstall:

```bash
git pull && pip install -e .
```

### `Gtk-WARNING: cannot open display`

No display server is available. Options:

1. Log into a desktop session and run `shypn` from a terminal there.
2. Enable X11 forwarding: `ssh -X user@host` then `shypn`.
3. Headless CI / testing only — virtual framebuffer:

```bash
sudo apt install xvfb
Xvfb :99 -screen 0 1280x1024x24 &
DISPLAY=:99 shypn
```

### `weasyprint` / PDF export broken

```bash
sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0
```

### `libgirepository` not found (Ubuntu version mismatch)

Run `lsb_release -r` to confirm your Ubuntu version, then use the matching
package name:

| Ubuntu version | Package name |
|---|---|
| 20.04, 22.04 | `libgirepository1.0-dev` |
| 24.04+ | `libgirepository-1.0-dev` |

### Slow startup on first run

SHYpn caches GTK icon themes and dependency graphs on first launch.
Subsequent starts are significantly faster.
