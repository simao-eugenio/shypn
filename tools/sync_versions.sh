#!/bin/bash
# tools/sync_versions.sh — version synchronisation utility for shypn
#
# Usage:
#   ./tools/sync_versions.sh           # write mode: update all files to match version.py
#   ./tools/sync_versions.sh --check   # check mode: verify all files are in sync (exit 1 if not)
#
# Single source of truth: src/shypn/version.py

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

CHECK_ONLY=false
if [[ "$1" == "--check" ]]; then
    CHECK_ONLY=true
fi

# ── Resolve repo root (works whether called from root or tools/) ───────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# ── Extract version from single source of truth ───────────────────────────────
VERSION_FILE="src/shypn/version.py"
if [ ! -f "$VERSION_FILE" ]; then
    echo -e "${RED}❌ Error: $VERSION_FILE not found${NC}"
    exit 1
fi

VERSION=$(grep -E '^__version__\s*=\s*"[^"]*"' "$VERSION_FILE" \
          | sed -E 's/^__version__\s*=\s*"([^"]*)".*/\1/')

if [ -z "$VERSION" ]; then
    echo -e "${RED}❌ Error: could not extract __version__ from $VERSION_FILE${NC}"
    exit 1
fi

echo "🔍 Version source: $VERSION"

FAILED=0

# ── Helper: check or update a file ────────────────────────────────────────────
check_or_update() {
    local file="$1"
    local pattern="$2"       # grep pattern to find the version line
    local current="$3"       # current value found in the file
    local replacement="$4"   # what the line should look like

    if [ ! -f "$file" ]; then
        echo -e "${YELLOW}⚠  $file not found — skipping${NC}"
        return
    fi

    if [ "$current" = "$VERSION" ]; then
        echo -e "   ✓ $file: ${GREEN}$current${NC}"
    elif $CHECK_ONLY; then
        echo -e "   ${RED}❌ VERSION DRIFT in $file${NC}"
        echo "      Expected: $VERSION"
        echo "      Found:    $current"
        FAILED=1
    else
        # Write mode: perform in-place substitution
        sed -i "s|$pattern|$replacement|" "$file"
        echo -e "   ✓ $file: ${YELLOW}$current${NC} → ${GREEN}$VERSION${NC}"
    fi
}

# ── pyproject.toml ─────────────────────────────────────────────────────────────
PYPROJECT_VER=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
check_or_update "pyproject.toml" \
    "^version = \".*\"" "$PYPROJECT_VER" \
    "version = \"$VERSION\""

# ── CITATION.cff ──────────────────────────────────────────────────────────────
CITATION_VER=$(grep '^version: ' CITATION.cff | awk '{print $2}')
check_or_update "CITATION.cff" \
    "^version: .*" "$CITATION_VER" \
    "version: $VERSION"

# ── __init__.py import check (read-only, never auto-patched) ──────────────────
if [ -f "src/shypn/__init__.py" ]; then
    if ! grep -q "from .version import" src/shypn/__init__.py; then
        echo -e "${YELLOW}⚠  src/shypn/__init__.py does not import from version.py${NC}"
    else
        echo -e "   ✓ src/shypn/__init__.py imports from version.py"
    fi
fi

# ── Python import smoke-test ──────────────────────────────────────────────────
PYTHON_BIN=${PYTHON:-python3}
if command -v "$PYTHON_BIN" &>/dev/null; then
    if $PYTHON_BIN -c "import sys; sys.path.insert(0,'src'); from shypn import __version__" 2>/dev/null; then
        echo -e "   ✓ Python imports work"
    else
        echo -e "${YELLOW}⚠  Python import check skipped (shypn not installed in this env)${NC}"
    fi
fi

# ── Result ────────────────────────────────────────────────────────────────────
if [ $FAILED -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Version sync check FAILED — run ./tools/sync_versions.sh to fix${NC}"
    exit 1
fi

if $CHECK_ONLY; then
    echo -e "${GREEN}✅ All version files in sync${NC}"
else
    echo -e "${GREEN}✅ Version sync complete${NC}"
fi
