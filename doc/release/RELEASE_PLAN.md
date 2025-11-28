# SHYpn GitHub Release Plan v1.0.0

## Overview

Prepare a clean public release of SHYpn for citation in research paper and PhD thesis. The repository contains valuable systems biology software implementing Extended Biological Petri Nets (12-tuple formalism) with weak independence analysis and parallel simulation capabilities.

**Target Audience**: Systems biologists, Petri net researchers, computational modelers  
**Release Goal**: Professional open-source repository suitable for academic citation  
**Timeline**: Before paper submission (paper references GitHub URL at line 433)

---

## Current Repository Structure Analysis

### ✅ **KEEP - Core Implementation**
- `src/shypn/` - Main application source (Petri net engine, GUI, simulation)
- `tests/` - Unit test suite (pytest)
- `ui/` - GTK3 UI definitions
- `pyproject.toml` - Python package configuration
- `README.md` - Project documentation (needs enhancement)
- `LICENSE` - License file
- `.gitignore` - Git ignore patterns (needs updates)

### ⚠️ **REVIEW - May Keep or Remove**
- `examples/` - Currently only `matrix_integration_example.py` (minimal)
  - **Decision needed**: Add more examples from workspace/projects/ or create new demos?
- `workspace/` - User workspace with projects
  - **Decision needed**: Include sample projects as examples or remove entirely?
- `doc/` - Documentation directory
  - `doc/papers/` - ✅ Keep (research paper with figures)
  - `doc/thesis/` - ❓ **CRITICAL DECISION**: Keep or remove thesis source?
    - **Option A**: Remove until post-defense (keep research private)
    - **Option B**: Keep if already publicly accessible
  - Other doc/ subdirectories - TBD based on content

### ❌ **REMOVE - Development Artifacts**
- `archive/` - Old debugging scripts (19 files)
  - `analyze_compound_connections.py`
  - `debug_arc_creation.py`, `debug_arc_rendering.py`
  - `diagnose_spurious_lines.py`
  - `deprecated/`, `mode/`, `refactor_main/`, `ui_removed/`
  - **Purpose**: Historical debugging, no longer needed
  
- `dev/` - Experimental test files (38 files)
  - `test_brenda_*.py` (10+ BRENDA database test scripts)
  - `test_file_panel_*.py` (GUI development tests)
  - `test_pathway_panel_wayland.py` (Wayland-specific debugging)
  - `validate_heuristic_fixes.py`, `diagnose_*.py`
  - **Purpose**: Development experiments, not production code

- `scripts/` - Mixed utility/development scripts (67 files)
  - Many `debug_*.py`, `diagnose_*.py`, `test_*.py` scripts
  - `generate_galaxy_model.py`, `generate_blackhole_galaxy.py` (test model generators)
  - `run_with_vcxsrv.sh`, `run_with_debug.sh` (WSL/debugging helpers)
  - **Analysis**: Some may be useful (e.g., `export_thesis_figures.py`), most are development tools
  - **Recommendation**: Keep essential utilities, remove development scripts

- `.pre-commit-config.yaml` - Development-only pre-commit hooks
- `.pytest_cache/` - Already gitignored, but verify

### 🔒 **ALREADY IGNORED (No Action Needed)**
- `legacy/` - Pre-UI backup (already in .gitignore)
- `workspace/cache/` - Cached data (already in .gitignore)
- `__pycache__/`, `*.pyc` - Python bytecode (already in .gitignore)
- `.venv/` - Virtual environment (already in .gitignore)
- Credentials: `brenda_credentials.txt`, `Token.txt` (already in .gitignore)

---

## Critical Decisions Needed

### Decision 1: Thesis Source Code Visibility
**Question**: Should `doc/thesis/` be included in public GitHub release?

**Option A: Remove Thesis Source (Recommended)**
- **Rationale**: PhD work not yet defended; keep research private until official publication
- **Impact**: Cleaner repo focused on software; thesis available post-defense
- **Action**: `git rm -r doc/thesis/` and add to .gitignore
- **Paper update**: Reference SHYpn software, not thesis source

**Option B: Keep Thesis Source**
- **Rationale**: Already publicly accessible; demonstrates research context
- **Impact**: Larger repo; full transparency on research process
- **Action**: No changes needed
- **Consideration**: Thesis is 243 pages (991KB) + LaTeX source

**Recommendation**: **Option A** - Remove thesis source until post-defense, then publish separately or in archive

---

### Decision 2: Release Strategy

**Option A: Clean Main Branch (Simpler)**
```bash
# Remove development artifacts from main branch
git rm -r archive/ dev/ scripts/
git rm -r doc/thesis/  # If Decision 1 = Remove
git rm .pre-commit-config.yaml
git add .gitignore  # After updates
git commit -m "chore: prepare v1.0.0 public release - remove development artifacts"
git tag -a v1.0.0 -m "Initial public release: Extended Biological Petri Nets with weak independence"
git push origin main
git push origin v1.0.0
```
**Pros**: Simple, clean history  
**Cons**: Loses development history (but can recover from backup)

**Option B: Create Release Branch (Preserves History)**
```bash
# Create separate release branch
git checkout -b public-release
git rm -r archive/ dev/ scripts/
git rm -r doc/thesis/  # If Decision 1 = Remove
git rm .pre-commit-config.yaml
git add .gitignore
git commit -m "chore: clean repository for public release v1.0.0"
git tag -a v1.0.0 -m "Initial public release"
git push origin public-release
git push origin v1.0.0

# Main branch keeps full development history
# Public release branch is clean for users
```
**Pros**: Preserves development history on main; clean public branch  
**Cons**: More complex to maintain two branches

**Recommendation**: **Option A** - Clean main branch (simpler for single-researcher project)

---

### Decision 3: Examples Directory Content

**Current State**: Only 1 file (`matrix_integration_example.py`)

**Option A: Add Comprehensive Examples**
Create polished examples from thesis/paper demonstrations:
- `examples/01_hexokinase/` - Simple enzyme catalysis (Example 1 from thesis)
- `examples/02_glycolysis/` - Multi-step pathway (Chapter 5)
- `examples/03_lac_operon/` - Gene regulation (Example 4)
- `examples/04_pfk_inhibition/` - Dynamic threshold (Example 16, Figure 7.4 in paper)
- `examples/README.md` - Explanation of each example

**Option B: Minimal Examples**
Keep current minimal state; point users to SBML import for real models

**Recommendation**: **Option A** - Add 3-5 well-documented examples (increases usability)

---

### Decision 4: Scripts Directory - Keep or Remove?

**Current Analysis**: 67 files, mostly development/debugging scripts

**Option A: Remove Entirely**
- Most scripts are development tools (`debug_*.py`, `diagnose_*.py`, `test_*.py`)
- Users can create their own utility scripts
- Keeps repo focused on core software

**Option B: Curate and Keep Essential Utilities**
- Keep: `export_thesis_figures.py` (reproducing research figures)
- Keep: `demo_sbml_enrichment.py`, `demo_pathway_import.py` (usage examples)
- Keep: `fetch_kegg_pathway.py` (KEGG integration demo)
- Remove: All debug/diagnose/test scripts (move to dev/ before deletion)

**Recommendation**: **Option A** - Remove scripts/ entirely (simplifies release, reduces maintenance)

---

## Action Plan

### Phase 1: Update .gitignore (Before Cleanup)

Add to `.gitignore`:
```gitignore
# Development artifacts (not for public release)
archive/
dev/
scripts/
test_output/

# Thesis source (private until post-defense)
doc/thesis/

# Development configuration
.pre-commit-config.yaml

# Additional Python artifacts
*.egg-info/
dist/
build/
```

**Command**:
```bash
# Append to .gitignore
cat >> .gitignore << 'EOF'

# === Public Release Exclusions (v1.0.0) ===
# Development and debugging scripts
archive/
dev/
scripts/

# Thesis source (available post-defense)
doc/thesis/

# Development configuration
.pre-commit-config.yaml

# Build artifacts
*.egg-info/
dist/
build/
EOF
```

---

### Phase 2: Remove Development Artifacts

```bash
# Remove from Git tracking (keeps files locally in .git history)
git rm -r archive/
git rm -r dev/
git rm -r scripts/
git rm -r doc/thesis/  # If Decision 1 = Remove
git rm .pre-commit-config.yaml

# Commit removal
git commit -m "chore: remove development artifacts for v1.0.0 public release

Removed directories:
- archive/ (19 old debugging scripts)
- dev/ (38 experimental test files)
- scripts/ (67 utility/development scripts)
- doc/thesis/ (PhD thesis source - available post-defense)
- .pre-commit-config.yaml (development-only configuration)

These artifacts are preserved in Git history and can be recovered if needed.
Public release focuses on core SHYpn implementation, tests, and documentation."
```

---

### Phase 3: Enhance README.md

**Update `/home/simao/projetos/shypn/README.md`** with:

#### 3.1 Add Citation Information
```markdown
## Citation

If you use SHYpn in your research, please cite:

```bibtex
@inproceedings{eugenio2025weak,
  title={Weak Independence and Coupled Parallelism in Biological Petri Nets},
  author={Eugénio, Simão and others},
  booktitle={Proceedings of [Conference Name]},
  year={2025},
  note={Software available at \url{https://github.com/simao-eugenio/shypn}}
}
```

**Paper**: Eugénio et al. (2025). *Weak Independence and Coupled Parallelism in Biological Petri Nets*. [Conference/Journal].
```

#### 3.2 Expand Features Section
```markdown
## Key Features

### Extended Biological Petri Nets (12-tuple Formalism)
- **Places (P)**: Chemical species with discrete/continuous marking
- **Transitions (T)**: Biochemical reactions with heterogeneous dynamics
- **Flow Relation (F)**: Normal arcs with stoichiometric weights
- **Regulatory Arcs (Σ)**: Test and inhibitor arcs for regulation
- **Rate Functions (Φ)**: Kinetic laws (mass action, Michaelis-Menten, Hill equations)
- **Transition Types (τ)**: Immediate, timed, stochastic, continuous
- **Formula Tracking (ρ)**: Atomic mass balance validation
- **Environmental Exchange (Θ)**: Source/sink classification
- **Dependency Taxonomy (Δ)**: INDEPENDENT, COMPETITIVE, CONVERGENT, REGULATORY

### Simulation and Analysis
- **Weak Independence Analysis**: Detect parallelizable reactions
- **Hybrid Simulation**: Mix discrete (stochastic) and continuous (ODE) transitions
- **Parallel Execution**: Multi-core simulation with coupled parallelism
- **Topology Analysis**: P/T-invariants, deadlock detection, liveness checking
- **Mass Balance Validation**: Atomic composition tracking (C, H, O, N, P, S)

### Integration
- **SBML Import**: Load models from BioModels, JWS Online, etc.
- **KEGG Pathways**: Fetch and enrich metabolic pathways
- **BRENDA Database**: Query kinetic parameters (Km, Vmax, Ki)
```

#### 3.3 Add Quick Example
```markdown
## Quick Example

```python
from shypn.core import BiologicalPetriNet
from shypn.simulation import HybridSimulator

# Create simple enzyme-catalyzed reaction: S + E → E + P
net = BiologicalPetriNet()
s = net.add_place("Substrate", marking=100.0)
e = net.add_place("Enzyme", marking=10.0)
p = net.add_place("Product", marking=0.0)

t = net.add_continuous_transition("Catalysis", rate_function="michaelis_menten")
net.add_arc(s, t, weight=1)
net.add_arc(e, t, weight=0)  # Test arc (catalyst not consumed)
net.add_arc(t, e, weight=0)  # Return enzyme
net.add_arc(t, p, weight=1)

# Simulate
sim = HybridSimulator(net)
results = sim.run(t_end=10.0, dt=0.1)
results.plot()
```

See `examples/` for more demonstrations.
```

#### 3.4 Update Installation Instructions
```markdown
### Installation

**Requirements**: Python 3.10+, GTK 3.0

```bash
# Clone repository
git clone https://github.com/simao-eugenio/shypn.git
cd shypn

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# OR: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -e .

# Run GUI
python src/shypn.py
```

**Optional Dependencies**:
- `libsbml` - SBML import (install via `pip install python-libsbml`)
- `brenda_credentials.txt` - BRENDA database access (register at brenda-enzymes.org)
```

#### 3.5 Add Links to Paper/Documentation
```markdown
## Documentation

- 📄 **Research Paper**: [Weak Independence in Biological Petri Nets](doc/papers/weak_independence_biopn.pdf)
- 📘 **API Documentation**: [Coming soon - Sphinx docs]
- 🎓 **PhD Thesis**: [Available post-defense]
- 🧪 **Examples**: See `examples/` directory
```

---

### Phase 4: Create Essential Documentation Files

#### 4.1 - `INSTALL.md`
```markdown
# SHYpn Installation Guide

## System Requirements

- **Operating System**: Linux (GTK 3.0 native), macOS (via XQuartz), Windows (WSL2)
- **Python**: 3.10 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended for large models
- **Display**: X11 or Wayland compositor

## Dependencies

### Core Dependencies (Automatic)
- `PyGObject` - GTK 3.0 Python bindings
- `NetworkX` - Graph algorithms
- `NumPy` - Numerical computing
- `SciPy` - ODE solvers
- `Matplotlib` - Plotting

### Optional Dependencies
- `python-libsbml` - SBML import (`pip install python-libsbml`)
- `requests` - KEGG pathway fetching

## Installation Steps

### 1. Clone Repository
```bash
git clone https://github.com/simao-eugenio/shypn.git
cd shypn
```

### 2. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# OR: .venv\Scripts\activate  # Windows
```

### 3. Install SHYpn
```bash
pip install -e .
```

### 4. Verify Installation
```bash
python -c "import shypn; print(shypn.__version__)"
# Expected output: 2.4.7

# Run GUI
python src/shypn.py
```

## Platform-Specific Notes

### Linux
GTK 3.0 should be pre-installed on most distributions. If not:
```bash
# Ubuntu/Debian
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Fedora
sudo dnf install python3-gobject gtk3
```

### macOS
Requires XQuartz for X11 display:
```bash
brew install gtk+3 pygobject3 adwaita-icon-theme
# Install XQuartz from xquartz.org
```

### Windows (WSL2)
Install WSL2 with Ubuntu, then follow Linux instructions. Requires X server (VcXsrv, Xming) for GUI.

## BRENDA Database Integration (Optional)

1. Register at https://www.brenda-enzymes.org/
2. Create `brenda_credentials.txt` in repository root:
```
username@example.com
your_password_here
```
3. Restart SHYpn to enable kinetic parameter queries

## Troubleshooting

**ImportError: No module named 'gi'**
→ Install PyGObject: `pip install PyGObject`

**GTK Warning: cannot open display**
→ Set DISPLAY: `export DISPLAY=:0` (Linux) or configure X server (WSL/macOS)

**SBML import fails**
→ Install libsbml: `pip install python-libsbml`

## Next Steps

- Read [TUTORIAL.md](TUTORIAL.md) for usage guide
- Explore `examples/` directory
- See [README.md](README.md) for feature overview
```

#### 4.2 - `examples/README.md`
```markdown
# SHYpn Examples

Demonstration models showcasing Extended Biological Petri Net features.

## Available Examples

### 1. Simple Enzyme Catalysis (`matrix_integration_example.py`)
**Concept**: Basic enzyme-substrate reaction  
**Features**: Continuous transitions, mass action kinetics  
**Complexity**: Beginner  
**Runtime**: < 1 second

```bash
python examples/matrix_integration_example.py
```

## Coming Soon

- **Hexokinase Reaction**: Glucose phosphorylation with ATP
- **Glycolysis Pathway**: Multi-step glucose metabolism
- **Lac Operon**: Gene regulation with allosteric inhibition
- **PFK Regulation**: Dynamic threshold inhibition (paper Figure 2)

## Creating Your Own Models

See [TUTORIAL.md](../TUTORIAL.md) for step-by-step guide.

## Model Format

SHYpn uses custom XML format (`.shypn`). SBML import also supported:
```python
from shypn.io import import_sbml
net = import_sbml("model.xml")
```

## Data Sources

- **BioModels**: https://www.ebi.ac.uk/biomodels/
- **KEGG Pathways**: https://www.genome.jp/kegg/pathway.html
- **Reactome**: https://reactome.org/
```

---

### Phase 5: Update Paper with GitHub URL

**File**: `doc/papers/weak_independence_biopn.tex`  
**Line 433** (or appropriate location in Implementation/Availability section):

```latex
\section{Implementation: The SHYpn Tool}

SHYpn (Systems Hybrid Pathway Networks) is an open-source implementation 
of the Extended Biological Petri Net formalism with weak independence analysis 
and parallel simulation capabilities. The platform provides a GTK3-based 
graphical interface for visual modeling, simulation, and analysis of 
biochemical pathways.

\textbf{Key Features}:
\begin{itemize}
    \item 12-tuple Extended Biological Petri Net formalism (Definition~\ref{def:extended-biopn})
    \item Weak independence analysis for reaction decoupling
    \item Hybrid simulation engine (discrete stochastic + continuous ODE)
    \item Parallel execution with coupled parallelism (up to 3.9× speedup on 8 cores)
    \item SBML import and KEGG/BRENDA integration
    \item Topology analysis (P/T-invariants, deadlocks, liveness)
\end{itemize}

\textbf{Availability}: Open-source software available under MIT License at 
\url{https://github.com/simao-eugenio/shypn}. Release v1.0.0 includes 
full source code, test suite, documentation, and example models. 
Tested on 100 BioModels SBML files with 100\% import success.

\textbf{Implementation}: Python 3.10+ with PyGObject (GTK 3.0), NetworkX, 
NumPy, SciPy. Cross-platform (Linux native, macOS via XQuartz, Windows via WSL2).
```

---

### Phase 6: Tag Release

```bash
# Ensure all changes committed
git add .gitignore README.md doc/papers/weak_independence_biopn.tex
git commit -m "docs: enhance README and paper for v1.0.0 public release"

# Create annotated tag
git tag -a v1.0.0 -m "SHYpn v1.0.0 - Initial Public Release

Extended Biological Petri Nets with weak independence analysis.

Features:
- 12-tuple Bio-PN formalism with heterogeneous dynamics
- Weak independence analysis for parallel simulation
- Hybrid simulation (stochastic + continuous)
- SBML/KEGG/BRENDA integration
- GTK3 visual modeling interface

Citation: Eugénio et al. (2025). Weak Independence and Coupled 
Parallelism in Biological Petri Nets. [Conference/Journal]."

# Push to GitHub
git push origin main
git push origin v1.0.0
```

---

### Phase 7: Create GitHub Release (via Web Interface)

1. Go to: `https://github.com/simao-eugenio/shypn/releases/new`
2. **Tag**: Select `v1.0.0`
3. **Title**: `SHYpn v1.0.0 - Initial Public Release`
4. **Description**:

```markdown
# SHYpn v1.0.0 - Initial Public Release

**Extended Biological Petri Nets for Systems Biology**

First public release of SHYpn, implementing the 12-tuple Extended Biological Petri Net formalism with weak independence analysis and parallel simulation capabilities.

## 🎯 Key Features

- **Extended Bio-PN Formalism**: 12-tuple definition with heterogeneous transition types (immediate, timed, stochastic, continuous)
- **Weak Independence Analysis**: Automated detection of parallelizable reactions
- **Parallel Simulation**: Multi-core execution with coupled parallelism (up to 3.9× speedup on 8 cores)
- **Mass Balance Validation**: Atomic composition tracking (C, H, O, N, P, S)
- **Database Integration**: SBML import, KEGG pathways, BRENDA kinetic parameters
- **Visual Modeling**: GTK3-based graphical interface with auto-layout algorithms
- **Topology Analysis**: P/T-invariants, deadlock detection, liveness checking

## 📦 Installation

```bash
git clone https://github.com/simao-eugenio/shypn.git
cd shypn
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python src/shypn.py
```

See [INSTALL.md](INSTALL.md) for detailed instructions.

## 📚 Documentation

- **Research Paper**: [doc/papers/weak_independence_biopn.pdf](doc/papers/weak_independence_biopn.pdf)
- **Installation Guide**: [INSTALL.md](INSTALL.md)
- **Examples**: [examples/README.md](examples/README.md)

## 🧪 Validation

- ✅ Tested on 100 BioModels SBML files (100% import success)
- ✅ Mass balance validation on 16 curated models
- ✅ Parallel speedup verified on 8-core system

## 📖 Citation

```bibtex
@inproceedings{eugenio2025weak,
  title={Weak Independence and Coupled Parallelism in Biological Petri Nets},
  author={Eugénio, Simão and others},
  booktitle={[Conference/Journal]},
  year={2025}
}
```

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

This work is part of a PhD thesis at [University Name]. Special thanks to advisors and collaborators.
```

5. **Attach Assets**: Upload `weak_independence_biopn.pdf` from `doc/papers/`
6. Click **Publish release**

---

## Testing Before Release

### Test 1: Clean Install
```bash
# Test in isolated environment
cd /tmp
git clone https://github.com/simao-eugenio/shypn.git shypn-test
cd shypn-test
python3 -m venv test_venv
source test_venv/bin/activate
pip install -e .

# Verify no development artifacts
ls -la | grep -E "(archive|dev|scripts|test_output)"
# Should return nothing

# Run test suite
pytest tests/ -v

# Run GUI
python src/shypn.py
```

### Test 2: SBML Import
```bash
# Test SBML import functionality
python -c "
from shypn.io import import_sbml
import urllib.request
urllib.request.urlretrieve(
    'https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000061.2',
    'test_model.xml'
)
net = import_sbml('test_model.xml')
print(f'✅ Imported: {len(net.places)} places, {len(net.transitions)} transitions')
"
```

### Test 3: Example Execution
```bash
python examples/matrix_integration_example.py
# Should run without errors
```

---

## Post-Release Checklist

- [ ] GitHub release created (v1.0.0)
- [ ] Paper updated with GitHub URL
- [ ] Thesis references SHYpn availability (update before defense)
- [ ] README.md enhanced with citation, features, examples
- [ ] INSTALL.md created
- [ ] examples/README.md created
- [ ] All development artifacts removed (archive/, dev/, scripts/)
- [ ] .gitignore updated
- [ ] Clean install tested successfully
- [ ] Test suite passes
- [ ] SBML import verified
- [ ] GitHub repository set to public (if private)
- [ ] Add topics on GitHub: `systems-biology`, `petri-nets`, `modeling`, `simulation`, `python`, `gtk`
- [ ] Enable GitHub Issues (for community feedback)
- [ ] Add repository description: "Extended Biological Petri Nets with weak independence analysis for systems biology modeling and simulation"

---

## Optional: PyPI Publication

If you want users to `pip install shypn`:

1. Update `pyproject.toml` with metadata:
```toml
[project]
name = "shypn"
version = "1.0.0"
description = "Extended Biological Petri Nets for systems biology"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [{name = "Simão Eugénio", email = "your.email@example.com"}]
keywords = ["petri-nets", "systems-biology", "simulation", "modeling"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Science/Research",
    "Topic :: Scientific/Engineering :: Bio-Informatics",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.10",
]
```

2. Build and upload:
```bash
pip install build twine
python -m build
twine upload dist/*
```

3. Users can then install: `pip install shypn`

---

## Timeline Recommendation

**Week 1**: Clean repository, update documentation  
**Week 2**: Create examples, test clean install  
**Week 3**: Tag release, update paper/thesis  
**Week 4**: Submit paper with GitHub URL confirmed  

**Post-Defense**: Publish thesis source, create thesis citation release (v1.1.0)

---

## Contact for Decisions

**Next Steps**: Please review and make decisions on:
1. ❓ Remove `doc/thesis/` or keep in release?
2. ❓ Release strategy: Clean main branch (A) or separate release branch (B)?
3. ❓ Add comprehensive examples or keep minimal?
4. ❓ Remove `scripts/` entirely or curate essential utilities?

After decisions, proceed with Phase 1 (.gitignore update).
