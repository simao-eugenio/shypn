# SHyPN — workspace instructions for AI agents

These rules apply to **every** Copilot/agent session in this workspace
(local dev box and the remote GPU server). Both sides share the same
git repo, so any agent that follows these instructions will produce
filesystem layouts that match across machines.

## Project filesystem layout (STRICT)

For any project under `workspace/projects/<project_name>/` the
following per-project subdirectories are canonical:

| Path                                          | Purpose                                                                   |
|-----------------------------------------------|---------------------------------------------------------------------------|
| `workspace/projects/<name>/models/`           | `.shy` model files (versioned)                                            |
| `workspace/projects/<name>/results/`          | **All** sweep / simulation outputs (run_YYYYMMDD_HHMMSS/ directories)     |
| `workspace/projects/<name>/scripts/`          | **All** analysis & auxiliary scripts (server-side or client-side)         |
| `workspace/projects/<name>/figures/`          | Generated plots, manuscript figures                                       |
| `workspace/projects/<name>/manuscript/`       | LaTeX / markdown for the write-up                                         |
| `workspace/projects/<name>/metadata/`         | Curated reference data, experimental constants, citations                 |
| `workspace/projects/<name>/docs/`             | Project-specific notes, design docs                                       |
| `workspace/projects/<name>/sweep_config.json` | Sweep dispatch configuration                                              |

### Rules

1. **Sweep results MUST go to `<project>/results/`.**
   - Local default (CLI): `python -m shypn.cli.sweep --project <p> --sweep …`
     resolves the output dir to `<project>/results/` automatically.
   - On the remote GPU server, `<project>/results/` is a **symlink** to
     the dedicated HDD (e.g. `/home/simao/data/results/<project>/`) so
     trajectory data does not consume the SSD. The path the agent uses
     is still `<project>/results/`; the symlink is the operator's job
     to set up once per project, not the agent's.
   - Do **not** write sweep output to `~/data/...`, `/tmp/...`,
     `experiments/results/`, or any path outside `<project>/results/`.
   - The legacy `<project>/experiments/` tree is deprecated; do not
     create new content there. Existing run dirs may be left in place
     but new dispatches go to `<project>/results/`.

2. **Analysis & auxiliary scripts MUST go to `<project>/scripts/`.**
   - This includes server-side analysis (e.g. dose-response summarisers,
     trajectory inspectors), client-side helpers, model-patching scripts,
     and one-off CLI utilities **that are specific to a project**.
   - Do **not** drop project scripts into `/tmp/`, the workspace root,
     `dev/`, `archive/`, or `tools/`.
   - If a script is genuinely *cross-project* (a generic tool), it
     belongs in `tools/` or `scripts/` at the repo root and must accept
     the target project path as an argument.

3. **Symlink convention (server side, optional but recommended).**
   When a project starts producing >1 GiB of trajectory data, the
   operator creates the per-project HDD store and symlinks it:
   ```bash
   mkdir -p /home/simao/data/results/<project>
   ln -s /home/simao/data/results/<project> ~/shypn/workspace/projects/<project>/results
   ```
   The agent does not need to create this symlink — it just writes to
   `<project>/results/` and the kernel resolves it.

4. **Never inline-overwrite the canonical model file from a script.**
   Patching scripts in `<project>/scripts/` either save a new versioned
   file (`model_v2.shy`) or perform an in-memory dispatch only.

## Git workflow (recap)

- `private` remote → `git@github.com:simao-eugenio/shypn-dev.git`
- `public`  remote → `git@github.com:simao-eugenio/shypn.git`
- Branch in active use: `Usability-and-enhancements`
- Deploy to server: commit → `git push private` → SSH `git pull private --ff-only`
- Server alias: `remote-gpu` → `simao@150.162.232.36`, repo at `~/shypn/`
- Server venv: `~/shypn/.venv/` (CuPy 14.0.1, CUDA 12.9, RTX 5060 Ti)

## CLI cheatsheet

```bash
# Dispatch sweep (writes to <project>/results/run_<timestamp>/)
python -m shypn.cli.sweep \
    --project workspace/projects/<name> \
    --sweep   workspace/projects/<name>/sweep_config.json \
    --workers 4 --verbose

# Override output explicitly (rarely needed)
python -m shypn.cli.sweep --project … --sweep … --output <abs-or-rel-path>
```

## Engine facts

- τ-leaping is the only stochastic engine (`use_tau_leaping=True` is
  baked in; the setter is a no-op).
- GPU path: `cupy` backend → `GPUHybridEngine` for ODE+stochastic models.
  Decline reasons logged at `WARNING` level by `replicate_runner.py`.
- Per-condition resource metrics land in `summary.csv` and
  `resource_usage.json` inside each run dir.
