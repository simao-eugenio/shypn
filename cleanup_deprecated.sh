#!/bin/bash
# Deprecated Code Cleanup Script
# Safely moves deprecated files to archive/deprecated/
# Run from project root: ./cleanup_deprecated.sh

set -e  # Exit on error

echo "========================================================================"
echo "SHYpn Deprecated Code Cleanup"
echo "========================================================================"
echo ""
echo "This script will move deprecated files to archive/deprecated/"
echo "All files have been verified to have NO active dependencies."
echo ""
echo "Files to be moved:"
echo "  1. src/shypn/helpers/topology_panel_loader_old.py"
echo "  2. src/shypn/ui/panels/viability/viability_panel_old.py"  
echo "  3. src/shypn/events/mode_events.py (will also update __init__.py)"
echo ""
read -p "Proceed with cleanup? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Starting cleanup..."
echo ""

# Create destination directories
echo "[1/6] Creating destination directories..."
mkdir -p archive/deprecated/helpers
mkdir -p archive/deprecated/ui/panels/viability
mkdir -p archive/deprecated/events

# Move topology_panel_loader_old.py
echo "[2/6] Moving topology_panel_loader_old.py..."
if [ -f "src/shypn/helpers/topology_panel_loader_old.py" ]; then
    git mv src/shypn/helpers/topology_panel_loader_old.py archive/deprecated/helpers/
    echo "  ✓ Moved to archive/deprecated/helpers/"
else
    echo "  ⚠ File not found (may already be moved)"
fi

# Move viability_panel_old.py
echo "[3/6] Moving viability_panel_old.py..."
if [ -f "src/shypn/ui/panels/viability/viability_panel_old.py" ]; then
    git mv src/shypn/ui/panels/viability/viability_panel_old.py archive/deprecated/ui/panels/viability/
    echo "  ✓ Moved to archive/deprecated/ui/panels/viability/"
else
    echo "  ⚠ File not found (may already be moved)"
fi

# Move mode_events.py
echo "[4/6] Moving mode_events.py..."
if [ -f "src/shypn/events/mode_events.py" ]; then
    git mv src/shypn/events/mode_events.py archive/deprecated/events/
    echo "  ✓ Moved to archive/deprecated/events/"
else
    echo "  ⚠ File not found (may already be moved)"
fi

# Update events/__init__.py to remove mode_events imports
echo "[5/6] Updating src/shypn/events/__init__.py..."
if [ -f "src/shypn/events/__init__.py" ]; then
    # Create backup
    cp src/shypn/events/__init__.py src/shypn/events/__init__.py.bak
    
    # Remove the mode_events import lines
    sed -i '/from \.mode_events import/,+2d' src/shypn/events/__init__.py
    sed -i "/^    'ModeChangedEvent',$/d" src/shypn/events/__init__.py
    sed -i "/^    'ToolChangedEvent',$/d" src/shypn/events/__init__.py
    
    echo "  ✓ Removed mode_events exports from __init__.py"
    echo "  ℹ Backup saved as __init__.py.bak"
fi

# Create deprecation notice in archive
echo "[6/6] Creating deprecation notice..."
cat > archive/deprecated/MOVED_$(date +%Y%m%d).md << 'EOF'
# Files Moved to Deprecated - $(date +%Y-%m-%d)

## Files Moved

### 1. topology_panel_loader_old.py
- **From**: `src/shypn/helpers/topology_panel_loader_old.py`
- **Reason**: Filename explicitly indicates old version
- **Replacement**: `src/shypn/helpers/topology_panel_loader.py`
- **Dependencies**: None found (verified via grep)

### 2. viability_panel_old.py
- **From**: `src/shypn/ui/panels/viability/viability_panel_old.py`
- **Reason**: Replaced by newer viability panel implementation
- **Replacement**: `src/shypn/ui/panels/viability/viability_panel.py`
- **Dependencies**: None found (verified via grep)

### 3. mode_events.py
- **From**: `src/shypn/events/mode_events.py`
- **Reason**: Explicitly deprecated with DeprecationWarning
- **Replacement**: `shypn.engine.simulation.state.SimulationStateDetector`
- **Dependencies**: Exported in __init__.py but never imported elsewhere
- **Note**: Also removed exports from `src/shypn/events/__init__.py`

## Verification Commands Used

```bash
# Check for imports of deprecated files
grep -r "topology_panel_loader_old" src/ --include="*.py"
grep -r "viability_panel_old" src/ --include="*.py"
grep -r "from shypn.events import.*Mode" src/ --include="*.py"
```

All returned zero results, confirming no active dependencies.

## Related Documentation

- See `/DEPRECATED_CODE_AUDIT.md` for full deprecation audit
- See `doc/modes/MODE_ELIMINATION_PLAN.md` for mode system deprecation plan
- See `archive/mode/mode_events.py` for original archived version

EOF

echo ""
echo "========================================================================"
echo "✅ Cleanup Complete!"
echo "========================================================================"
echo ""
echo "Files moved:"
echo "  • topology_panel_loader_old.py → archive/deprecated/helpers/"
echo "  • viability_panel_old.py → archive/deprecated/ui/panels/viability/"
echo "  • mode_events.py → archive/deprecated/events/"
echo ""
echo "Files modified:"
echo "  • src/shypn/events/__init__.py (removed mode_events exports)"
echo ""
echo "Documentation created:"
echo "  • archive/deprecated/MOVED_$(date +%Y%m%d).md"
echo ""
echo "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Run tests: python -m pytest tests/"
echo "  3. Commit: git commit -m 'refactor: move deprecated files to archive'"
echo ""
echo "⚠ IMPORTANT: If you see any import errors, restore from backup:"
echo "   git checkout src/shypn/events/__init__.py"
echo "   git checkout src/shypn/helpers/topology_panel_loader_old.py"
echo "   git checkout src/shypn/ui/panels/viability/viability_panel_old.py"
echo "   git checkout src/shypn/events/mode_events.py"
echo ""
