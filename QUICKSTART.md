# SHYpn — Quick Start Guide

Get from zero to a running simulation in under 5 minutes.

---

## Prerequisites

Before cloning, install the GTK3 system libraries for your OS.

**Fastest path on Ubuntu 22.04 / 24.04** — the installer script handles everything:

```bash
git clone https://github.com/simao-eugenio/shypn.git
cd shypn
bash install_ubuntu.sh
```

Skip to [Step 2](#step-2--launch-shypn) after the script completes.

**Manual prerequisites (Ubuntu):**

```bash
# Ubuntu 22.04
sudo apt install -y python3 python3-venv python3-gi python3-gi-cairo \
    gir1.2-gtk-3.0 libgtk-3-dev libcairo2-dev libgirepository1.0-dev pkg-config

# Ubuntu 24.04 (package name differs)
sudo apt install -y python3 python3-venv python3-gi python3-gi-cairo \
    gir1.2-gtk-3.0 libgtk-3-dev libcairo2-dev libgirepository-1.0-dev pkg-config
```

Full details in [INSTALL.md](INSTALL.md).

---

## Step 1 — Clone and install

If you didn't use `install_ubuntu.sh`, run these steps manually:

```bash
git clone https://github.com/simao-eugenio/shypn.git
cd shypn
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

---

## Step 2 — Launch SHYpn

```bash
source .venv/bin/activate   # if not already active
shypn
# or: python src/shypn.py
```

The main window opens with three panels:
- **File Explorer** (left) — project tree and model files
- **Canvas** (centre) — visual Petri net editor
- **Panels** (right) — simulation, analysis, reports

---

## Step 3 — Open a built-in example

1. In the **File Explorer**, expand `workspace/projects/Biochemical-Examples/`
2. Double-click any example folder (e.g. `03_Hexokinase_MM`)
3. The model loads on the canvas

Recommended first examples:

| Folder | What it demonstrates |
|--------|----------------------|
| `01_ATP_Hydrolysis` | Simplest model — basic place/transition |
| `03_Hexokinase_MM` | Michaelis-Menten kinetics |
| `07_Upper_Glycolysis_Pathway` | Multi-step pathway |
| `19_Bacterial_Quorum_Sensing` | Signal Hierarchy (13-tuple formalism) |
| `21_Hybrid_Glucose_Insulin` | Hybrid stochastic/continuous mode |

---

## Step 4 — Run a simulation

1. Click **Analyses** in the right panel tabs
2. Under **Simulation Settings**, choose a mode:
   - `Stochastic (τ-leaping)` — fast approximate SSA
   - `Continuous (ODE)` — deterministic integration
   - `Hybrid` — mixed mode
3. Set `t_end` (e.g. `100` seconds) and `n_replicates` (e.g. `10`)
4. Click **Run Simulation**
5. Results appear in the **Plots** sub-tab

---

## Step 5 — Import a KEGG or SBML pathway (optional)

1. **File → Import → KEGG Pathway** — paste a KEGG pathway ID (e.g. `hsa00010`)
2. **File → Import → SBML** — select an `.xml` file from BioModels Database

SHYpn auto-detects assignment rules and prompts for the import mode (ODE, Hybrid, Stochastic).

---

## Next steps

| Resource | Contents |
|----------|---------|
| [INSTALL.md](INSTALL.md) | Full installation details, troubleshooting, optional deps |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Architecture overview, development workflow |
| `workspace/projects/Biochemical-Examples/README.md` | Full catalogue of the 22 built-in models |
| `doc/` | Architecture documentation, API reference (local only) |
| [arXiv:2512.17106](https://arxiv.org/abs/2512.17106) | Theory paper: Weak Independence |
| [arXiv:2501.03850](https://arxiv.org/abs/2501.03850) | Thermodynamic Hierarchy paper |
