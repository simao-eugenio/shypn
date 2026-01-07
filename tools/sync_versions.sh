#!/usr/bin/env bash

# sync_versions.sh - Synchronize version information across all project files
# 
# This script ensures version consistency by updating all version-related files
# from the single source of truth (src/shypn/version.py)
#
# Usage: ./scripts/sync_versions.sh [--check]
#   --check: Verify versions are in sync without making changes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
CHECK_ONLY=false
if [[ "$1" == "--check" ]]; then
    CHECK_ONLY=true
fi

echo "🔍 Extracting version from source of truth (src/shypn/version.py)..."

# Extract version from version.py
VERSION_FILE="$PROJECT_ROOT/src/shypn/version.py"
if [[ ! -f "$VERSION_FILE" ]]; then
    echo -e "${RED}❌ Error: $VERSION_FILE not found${NC}"
    exit 1
fi

VERSION=$(grep -E '^__version__\s*=\s*"[^"]*"' "$VERSION_FILE" | sed -E 's/^__version__\s*=\s*"([^"]*)".*/\1/')
if [[ -z "$VERSION" ]]; then
    echo -e "${RED}❌ Error: Could not extract version from $VERSION_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found version: $VERSION${NC}"

# Function to check/update file
check_or_update() {
    local file="$1"
    local pattern="$2"
    local replacement="$3"
    local description="$4"
    
    if [[ ! -f "$file" ]]; then
        echo -e "${YELLOW}⚠ Warning: $file not found, skipping${NC}"
        return
    fi
    
    if grep -qE "$pattern" "$file"; then
        current=$(grep -E "$pattern" "$file" | head -1)
        
        if echo "$current" | grep -q "$VERSION"; then
            echo -e "${GREEN}✓ $description: Already synchronized ($VERSION)${NC}"
        else
            if [[ "$CHECK_ONLY" == true ]]; then
                echo -e "${RED}✗ $description: Out of sync${NC}"
                echo "  Current: $current"
                echo "  Expected: $replacement"
                return 1
            else
                sed -i -E "s|$pattern|$replacement|" "$file"
                echo -e "${GREEN}✓ $description: Updated to $VERSION${NC}"
            fi
        fi
    else
        echo -e "${YELLOW}⚠ Warning: Pattern not found in $file${NC}"
    fi
}

# Track if any file was out of sync
SYNC_STATUS=0

# Update pyproject.toml
check_or_update \
    "$PROJECT_ROOT/pyproject.toml" \
    '^version\s*=\s*"[^"]*"' \
    "version = \"$VERSION\"" \
    "pyproject.toml" || SYNC_STATUS=1

# Update CITATION.cff
check_or_update \
    "$PROJECT_ROOT/CITATION.cff" \
    '^version:\s*[0-9]+\.[0-9]+\.[0-9]+' \
    "version: $VERSION" \
    "CITATION.cff" || SYNC_STATUS=1

# Update __init__.py (check that it imports from version.py)
INIT_FILE="$PROJECT_ROOT/src/shypn/__init__.py"
if grep -q "from .version import" "$INIT_FILE"; then
    echo -e "${GREEN}✓ __init__.py: Correctly imports from version.py${NC}"
else
    echo -e "${YELLOW}⚠ Warning: __init__.py doesn't import from version.py${NC}"
    SYNC_STATUS=1
fi

echo ""
if [[ "$CHECK_ONLY" == true ]]; then
    if [[ $SYNC_STATUS -eq 0 ]]; then
        echo -e "${GREEN}✅ All versions are synchronized!${NC}"
        exit 0
    else
        echo -e "${RED}❌ Version files are out of sync. Run without --check to fix.${NC}"
        exit 1
    fi
else
    if [[ $SYNC_STATUS -eq 0 ]]; then
        echo -e "${GREEN}✅ All versions are synchronized to $VERSION${NC}"
    else
        echo -e "${YELLOW}⚠ Version synchronization complete with warnings${NC}"
    fi
fi
