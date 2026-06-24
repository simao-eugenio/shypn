## SHYpn 2.7.0 — Ubuntu Installer & Console Entry Point

**Release date:** 2026-06-24

---

### Highlights

This release makes getting SHYpn running on Ubuntu as simple as two commands:

```bash
git clone https://github.com/simao-eugenio/shypn.git
cd shypn && bash install_ubuntu.sh
```

Then launch with:

```bash
source .venv/bin/activate
shypn
```

---

### What's new

#### Installation infrastructure
- **`install_ubuntu.sh`** — one-script setup for Ubuntu 22.04 and 24.04 LTS. Detects the Ubuntu version, installs the correct `libgirepository` package (`libgirepository1.0-dev` on 22.04, `libgirepository-1.0-dev` on 24.04), creates the virtual environment, pip-installs SHYpn, and runs the headless verification.
- **`shypn` console command** — after `pip install`, typing `shypn` launches the application from any directory. No need to know the repo path.
- **`python -m shypn --check`** — headless installation verification. Reports Python version, all dependencies, GTK3 binding version, core SHYpn modules, and display environment. Returns exit code 0 on success; usable in CI without a display.

#### CI
- New workflow **`.github/workflows/ubuntu-install.yml`** — 4-cell matrix (Ubuntu 22.04 × 24.04 × Python 3.10 × 3.12). Tests full `apt install` → `pip install` → `--check` path on clean runners. Also simulates a zip-download install (no `.git` directory).

#### Documentation
- **`INSTALL.md`** rewritten — Ubuntu primary path leads; explicit Wayland / X11 / WSL2 section; zip-archive install path; Ubuntu 22.04 vs 24.04 package name differences prominently documented.
- **`QUICKSTART.md`** and **`README.md`** updated to reflect the new one-script path.

---

### Engine & UI fixes (since v2.6.1)

- **fix(ui):** WSLg/Wayland window init — remove premature `Gdk.init()`, add re-activation guard for D-Bus single-instance, deferred `present()` for correct Wayland compositor handshake.
- **fix(engine):** curved arc audit — apply inhibitor non-consumption constraints generically across all τ-leaping sampling paths (`_calculate_max_firings` and `_apply_flow_to_arcs`).
- **ui:** GPU policy dropdown added to remote sweep dispatch dialog.
- **fix:** remote sweep decoupled from SSH channel — survives client disconnect.
- **fix:** `_write_covariance` crash on numpy `place_data` arrays in `finalize_buf` path.
- **fix:** local `_on_queue_run` now reads `output_tier` and `trajectory_thin_seconds` from UI state.
- **fix:** full precision (`:.6g`) in factorial range display column.

---

### Upgrading from v2.6.x

If you have an existing clone:

```bash
git pull
pip install -e .          # picks up the new shypn console script
python -m shypn --check   # verify
```

---

### Supported platforms

| Platform | Status |
|---|---|
| Ubuntu 22.04 LTS (Wayland / X11) | ✅ primary — CI tested |
| Ubuntu 24.04 LTS (Wayland / X11) | ✅ primary — CI tested |
| WSL2 Ubuntu (Windows 11 + WSLg) | ✅ supported |
| Fedora / macOS | community-supported |

---

### Cite this software

```
Eugênio, S. (2026). SHYpn: Signal Hierarchical Petri Nets for Systems Biology (v2.7.0).
Zenodo. https://doi.org/10.5281/zenodo.20835073
```

---

**Full changelog:** [`CITATION.cff`](CITATION.cff) · [`src/shypn/version.py`](src/shypn/version.py)
