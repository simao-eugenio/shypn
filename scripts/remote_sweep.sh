#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# remote_sweep.sh — Run a parametric sweep on the remote server
#
# Workflow:
#   1. Local:  push latest code to shypn-dev
#   2. Remote: git pull + run sweep
#   3. Local:  pull results back into the project folder
#
# Project-aware usage (recommended):
#   ./scripts/remote_sweep.sh --project workspace/projects/thesis \
#                              --sweep biological/sweep_config.json \
#                              [--model biological/hexokinase.shy] \
#                              [--workers 24] [--dry-run]
#
# Legacy usage (paths relative to repo root):
#   ./scripts/remote_sweep.sh --model workspace/path/model.shy \
#                              --sweep workspace/path/config.json
#
# Both local and remote share the same project-relative paths.
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────
REMOTE_HOST="remote-gpu"          # SSH config alias (ControlMaster)
REMOTE_REPO="/home/simao/shypn"

SSH_CMD="ssh ${REMOTE_HOST}"

# ── Parse arguments ──────────────────────────────────────────────────
PROJECT=""
MODEL=""
SWEEP=""
WORKERS=""
DRY_RUN=""
VERBOSE="-v"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project|-p) PROJECT="$2"; shift 2 ;;
        --model|-m)   MODEL="$2"; shift 2 ;;
        --sweep|-s)   SWEEP="$2"; shift 2 ;;
        --workers|-w) WORKERS="--workers $2"; shift 2 ;;
        --dry-run)    DRY_RUN="--dry-run"; shift ;;
        --quiet|-q)   VERBOSE=""; shift ;;
        -h|--help)
            cat << 'USAGE'
Usage: remote_sweep.sh [OPTIONS]

  --project, -p <path>   Project folder (relative to repo root)
  --sweep,   -s <path>   Sweep config JSON (relative to project or repo)
  --model,   -m <path>   Model .shy file (overrides config; relative to project or repo)
  --workers, -w <N>      Parallel workers (default: auto)
  --dry-run              Preview without running
  --quiet,   -q          Suppress progress output

Project-aware (model_path in sweep config):
  ./scripts/remote_sweep.sh -p workspace/projects/thesis -s biological/sweep.json

Legacy (explicit model):
  ./scripts/remote_sweep.sh -m workspace/path/model.shy -s workspace/path/sweep.json
USAGE
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

if [[ -z "$SWEEP" ]]; then
    echo "Error: --sweep is required."
    echo "Run $0 --help for usage."
    exit 1
fi

# ── Step 1: Push local changes ──────────────────────────────────────
echo "═══ Step 1: Pushing local changes to shypn-dev ═══"
if git diff --quiet && git diff --cached --quiet; then
    echo "  Working tree clean, pushing..."
else
    echo "  Warning: uncommitted changes detected."
    echo "  Commit and push manually first, or press Enter to continue anyway."
    read -r
fi
git push origin "$(git branch --show-current)" 2>&1 | sed 's/^/  /'
echo ""

# ── Step 2: Remote git pull ─────────────────────────────────────────
echo "═══ Step 2: Pulling latest code on remote ═══"
$SSH_CMD "cd ${REMOTE_REPO} && git pull" 2>&1 | sed 's/^/  /'
echo ""

# ── Step 3: Run sweep on remote ─────────────────────────────────────
echo "═══ Step 3: Running sweep on remote ($(echo ${REMOTE_HOST})) ═══"

# Build the CLI command based on project vs legacy mode
CLI_ARGS="--sweep ${SWEEP}"
if [[ -n "$PROJECT" ]]; then
    CLI_ARGS="--project ${PROJECT} ${CLI_ARGS}"
    echo "  Project: ${PROJECT}"
fi
if [[ -n "$MODEL" ]]; then
    CLI_ARGS="${CLI_ARGS} --model ${MODEL}"
    echo "  Model:   ${MODEL}"
else
    echo "  Model:   (from sweep config)"
fi
echo "  Sweep:   ${SWEEP}"
echo "  Workers: ${WORKERS:-auto}"
echo "  Dry-run: ${DRY_RUN:-no}"
echo ""

REMOTE_CMD="cd ${REMOTE_REPO} && \
    export PYTHONPATH=\${PWD}/src && \
    .venv/bin/python -m shypn.cli.sweep \
        ${CLI_ARGS} \
        ${WORKERS} \
        ${VERBOSE} \
        ${DRY_RUN}"

# Run and capture the last line (Results: /path/to/run_dir)
REMOTE_OUTPUT=$($SSH_CMD "${REMOTE_CMD}" 2>&1)
echo "$REMOTE_OUTPUT" | sed 's/^/  /'
echo ""

# If dry-run, stop here
if [[ -n "$DRY_RUN" ]]; then
    echo "Dry-run complete. No results to fetch."
    exit 0
fi

# ── Step 4: Fetch results ───────────────────────────────────────────
# Extract the run directory from the last "Results: ..." line
RUN_DIR=$(echo "$REMOTE_OUTPUT" | grep "^Results:" | tail -1 | awk '{print $2}')

if [[ -z "$RUN_DIR" ]]; then
    echo "Error: could not determine remote results directory."
    echo "Check remote output above."
    exit 1
fi

echo "═══ Step 4: Fetching results from remote ═══"
echo "  Remote: ${RUN_DIR}"

# Determine local results directory:
# Project mode: <project>/experiments/results/<run_name>
# Legacy mode:  ./results/<run_name>
RUN_NAME=$(basename "$RUN_DIR")

if [[ -n "$PROJECT" ]]; then
    LOCAL_RESULTS_DIR="${PROJECT}/experiments/results"
else
    LOCAL_RESULTS_DIR="./results"
fi

mkdir -p "${LOCAL_RESULTS_DIR}"
LOCAL_RUN_DIR="${LOCAL_RESULTS_DIR}/${RUN_NAME}"

scp -r "${REMOTE_HOST}:${RUN_DIR}" "${LOCAL_RUN_DIR}" 2>&1 | sed 's/^/  /'
echo ""

echo "═══ Done ═══"
echo "Results saved to: ${LOCAL_RUN_DIR}"
echo ""
echo "Files:"
find "${LOCAL_RUN_DIR}" -type f | sort | sed 's/^/  /'
