#!/bin/bash
# Quick Fix for Cairo Context Error (System Python)
#
# Error: "Couldn't find foreign struct converter for 'cairo.Context'"
# Solution: Install python3-cairo package

set -e

echo "=================================="
echo "Cairo Context Error - Quick Fix"
echo "=================================="
echo ""

# Check if running as system Python (not conda)
if [[ ! -z "$CONDA_DEFAULT_ENV" ]]; then
    echo "⚠️  You're in a conda environment: $CONDA_DEFAULT_ENV"
    echo ""
    echo "For conda, run:"
    echo "  conda install -c conda-forge pycairo -y"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to cancel..."
fi

echo "Installing python3-cairo system package..."
echo ""

sudo apt-get update
sudo apt-get install -y python3-cairo

echo ""
echo "✅ Cairo fix installed!"
echo ""
echo "Now test the app:"
echo "  python3 src/shypn.py"
echo ""

# Quick verification
python3 -c "import cairo; print('✓ Cairo version:', cairo.version)" 2>/dev/null || echo "⚠️  Import test failed, but may still work"

echo ""
