#!/bin/bash
# Quick conda environment setup for SHYpn
#
# Usage: ./setup_conda_env.sh [environment_name]
#
# If no environment name is provided, uses 'shypn' as default

set -e

CONDA_ENV_NAME="${1:-shypn}"

echo "Setting up conda environment: $CONDA_ENV_NAME"
echo ""

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "Error: conda not found. Please install Miniconda or Anaconda first."
    echo "Download from: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Check if environment exists
if conda env list | grep -q "^${CONDA_ENV_NAME} "; then
    echo "Environment '$CONDA_ENV_NAME' already exists."
    read -p "Remove and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        conda env remove -n "$CONDA_ENV_NAME" -y
    else
        echo "Using existing environment."
        conda activate "$CONDA_ENV_NAME"
        exit 0
    fi
fi

echo "Creating conda environment..."
conda create -n "$CONDA_ENV_NAME" python=3.10 -y

echo ""
echo "Activating environment..."
eval "$(conda shell.bash hook)"
conda activate "$CONDA_ENV_NAME"

echo ""
echo "Installing PyGObject from conda-forge..."
conda install -c conda-forge pygobject gtk3 pycairo -y

echo ""
echo "Installing additional packages via pip..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

echo ""
echo "✓ Setup complete!"
echo ""
echo "To activate: conda activate $CONDA_ENV_NAME"
echo "To run app:  python src/shypn.py"
echo ""
