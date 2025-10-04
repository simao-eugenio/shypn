#!/bin/bash
# Cairo Foreign Struct Converter Fix
#
# This fixes the "Couldn't find foreign struct converter for 'cairo.Context'" error
# which is caused by missing python3-cairo package

echo "Fixing Cairo Context Error..."
echo ""

# Check if python3-cairo is installed
if dpkg -l | grep -q python3-cairo; then
    echo "✓ python3-cairo is already installed"
else
    echo "Installing python3-cairo..."
    sudo apt-get update
    sudo apt-get install -y python3-cairo
fi

# For conda users, also install via conda
if [[ ! -z "$CONDA_DEFAULT_ENV" ]]; then
    echo ""
    echo "Conda environment detected: $CONDA_DEFAULT_ENV"
    echo "Installing pycairo via conda..."
    conda install -c conda-forge pycairo -y
fi

echo ""
echo "✓ Cairo fix applied!"
echo ""
echo "Now run the app with:"
echo "  python3 src/shypn.py"
echo ""
