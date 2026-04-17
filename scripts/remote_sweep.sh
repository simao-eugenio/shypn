#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# remote_sweep.sh — Run a parametric sweep on the remote server
#
# Workflow:
#   1. Local:  push latest code to shypn-dev
#   2. Remote: git pull + run sweep
#   3. Local:  pull results back via scp
#
# Usage:
#   ./scripts/remote_sweep.sh --model workspace/path/model.shy \
#                              --sweep workspace/path/config.json \
#                              [--workers 24] [--dry-run]
#
# The --model and --sweep paths are relative to the shypn repo root
# (same on both local and remote).
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────
REMOTE_HOST="remote-gpu"          # SSH config alias (ControlMaster)
REMOTE_USER="simao"
REMOTE_REPO="/home/simao/shypn"
REMOTE_RESULTS_DIR="/home/simao/shypn/results"
LOCAL_RESULTS_DIR="./results"

SSH_CMD="ssh ${REMOTE_HOST}"

# ── Parse arguments ──────────────────────────────────────────────────
MODEL=""
SWEEP=""
WORKERS=""
DRY_RUN=""
VERBOSE="-v"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --model|-m)   MODEL="$2"; shift 2 ;;
        --sweep|-s)   SWEEP="$2"; shift 2 ;;
        --workers|-w) WORKERS="--workers $2"; shift 2 ;;
        --dry-run)    DRY_RUN="--dry-run"; shift ;;
        --quiet|-q)   VERBOSE=""; shift ;;
        -h|--help)
            echo "Usage: $0 --model <path> --sweep <config.json> [--workers N] [--dry-run]"
            echo ""
            echo "Paths are relative to the shypn repo root."
            echo "Results are fetched to ./results/ after completion."
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

if [[ -z "$MODEL" || -z "$SWEEP" ]]; then
    echo "Error: --model and --sweep are required."
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
echo "  Model:   ${MODEL}"
echo "  Sweep:   ${SWEEP}"
echo "  Workers: ${WORKERS:-auto}"
echo "  Dry-run: ${DRY_RUN:-no}"
echo ""

REMOTE_CMD="cd ${REMOTE_REPO} && \
    export PYTHONPATH=\${PWD}/src && \
    .venv/bin/python -m shypn.cli.sweep \
        --model ${MODEL} \
        --sweep ${SWEEP} \
        --output results \
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
mkdir -p "${LOCAL_RESULTS_DIR}"

# Use the basename of the run dir (e.g. run_20260417_154624)
RUN_NAME=$(basename "$RUN_DIR")
LOCAL_RUN_DIR="${LOCAL_RESULTS_DIR}/${RUN_NAME}"

scp -r "${REMOTE_HOST}:${RUN_DIR}" "${LOCAL_RUN_DIR}" 2>&1 | sed 's/^/  /'
echo ""

echo "═══ Done ═══"
echo "Results saved to: ${LOCAL_RUN_DIR}"
echo ""
echo "Files:"
find "${LOCAL_RUN_DIR}" -type f | sort | sed 's/^/  /'
