#!/bin/bash
# SHYpn - System Dependencies Installation Script
# 
# This script installs all required system dependencies for the SHYpn application.
# It supports Ubuntu/Debian-based distributions and uses conda for Python packages.
#
# Usage:
#   ./install_dependencies.sh
#
# Or for conda environment installation:
#   ./install_dependencies.sh --conda-env shypn

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default conda environment name
CONDA_ENV_NAME="shypn"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --conda-env)
            CONDA_ENV_NAME="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --conda-env NAME    Specify conda environment name (default: shypn)"
            echo "  -h, --help          Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  SHYpn Dependencies Installation Script${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check if running on Ubuntu/Debian
if ! command -v apt-get &> /dev/null; then
    echo -e "${RED}Error: This script requires apt-get (Ubuntu/Debian).${NC}"
    echo -e "${YELLOW}For other distributions, manually install:${NC}"
    echo "  - Python 3.8+"
    echo "  - GTK3 development files"
    echo "  - PyGObject (python3-gi)"
    echo "  - Cairo development files"
    exit 1
fi

echo -e "${YELLOW}📦 Step 1: Installing system packages...${NC}"
echo ""

# Update package list
echo "Updating package list..."
sudo apt-get update

# Install GTK3 and related dependencies
echo ""
echo "Installing GTK3 and development files..."
sudo apt-get install -y \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    libgtk-3-dev \
    libgirepository1.0-dev \
    gcc \
    libcairo2-dev \
    pkg-config \
    python3-dev

echo -e "${GREEN}✓ System packages installed successfully${NC}"
echo ""

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo -e "${YELLOW}⚠️  Warning: conda not found in PATH${NC}"
    echo -e "${YELLOW}   If you want to use conda, please install it first:${NC}"
    echo -e "${YELLOW}   https://docs.conda.io/en/latest/miniconda.html${NC}"
    echo ""
    echo -e "${YELLOW}   Continuing with system Python...${NC}"
    USE_CONDA=false
else
    USE_CONDA=true
    echo -e "${GREEN}✓ Found conda at: $(which conda)${NC}"
    echo ""
fi

if [ "$USE_CONDA" = true ]; then
    echo -e "${YELLOW}📦 Step 2: Setting up conda environment '${CONDA_ENV_NAME}'...${NC}"
    echo ""
    
    # Check if conda environment exists
    if conda env list | grep -q "^${CONDA_ENV_NAME} "; then
        echo -e "${BLUE}Environment '${CONDA_ENV_NAME}' already exists.${NC}"
        read -p "Do you want to remove and recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Removing existing environment..."
            conda env remove -n "${CONDA_ENV_NAME}" -y
        else
            echo "Using existing environment..."
        fi
    fi
    
    # Create or update conda environment
    if ! conda env list | grep -q "^${CONDA_ENV_NAME} "; then
        echo "Creating conda environment '${CONDA_ENV_NAME}'..."
        conda create -n "${CONDA_ENV_NAME}" python=3.10 -y
    fi
    
    echo ""
    echo -e "${YELLOW}📦 Step 3: Installing Python packages in conda environment...${NC}"
    echo ""
    
    # Activate conda environment and install packages
    eval "$(conda shell.bash hook)"
    conda activate "${CONDA_ENV_NAME}"
    
    # Install PyGObject in conda environment
    echo "Installing PyGObject and dependencies..."
    
    # Try conda-forge first (recommended for PyGObject)
    if conda install -c conda-forge pygobject -y; then
        echo -e "${GREEN}✓ PyGObject installed via conda-forge${NC}"
    else
        echo -e "${YELLOW}⚠️  conda-forge installation failed, trying pip...${NC}"
        pip install PyGObject
    fi
    
    # Install other Python dependencies
    if [ -f "requirements.txt" ]; then
        echo ""
        echo "Installing packages from requirements.txt..."
        pip install -r requirements.txt
    fi
    
    echo ""
    echo -e "${GREEN}✓ Python packages installed successfully${NC}"
    
    # Deactivate conda environment
    conda deactivate
    
else
    echo -e "${YELLOW}📦 Step 2: Installing Python packages with pip (system Python)...${NC}"
    echo ""
    
    # Install PyGObject with pip
    echo "Installing PyGObject..."
    pip3 install --user PyGObject
    
    # Install other dependencies
    if [ -f "requirements.txt" ]; then
        echo ""
        echo "Installing packages from requirements.txt..."
        pip3 install --user -r requirements.txt
    fi
    
    echo ""
    echo -e "${GREEN}✓ Python packages installed successfully${NC}"
fi

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✓ Installation Complete!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Show how to run the application
if [ "$USE_CONDA" = true ]; then
    echo -e "${YELLOW}To run SHYpn:${NC}"
    echo ""
    echo -e "  ${GREEN}conda activate ${CONDA_ENV_NAME}${NC}"
    echo -e "  ${GREEN}python src/shypn.py${NC}"
    echo ""
    echo -e "${YELLOW}To deactivate the environment later:${NC}"
    echo -e "  ${GREEN}conda deactivate${NC}"
else
    echo -e "${YELLOW}To run SHYpn:${NC}"
    echo ""
    echo -e "  ${GREEN}python3 src/shypn.py${NC}"
fi

echo ""
echo -e "${BLUE}============================================${NC}"
echo ""

# Verify installation
echo -e "${YELLOW}🔍 Verifying installation...${NC}"
echo ""

if [ "$USE_CONDA" = true ]; then
    eval "$(conda shell.bash hook)"
    conda activate "${CONDA_ENV_NAME}"
    
    if python -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk" 2>/dev/null; then
        echo -e "${GREEN}✓ GTK3 and PyGObject are working correctly!${NC}"
    else
        echo -e "${RED}✗ Error: GTK3 or PyGObject not working properly${NC}"
        echo -e "${YELLOW}  Try running: conda install -c conda-forge pygobject gtk3${NC}"
    fi
    
    conda deactivate
else
    if python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk" 2>/dev/null; then
        echo -e "${GREEN}✓ GTK3 and PyGObject are working correctly!${NC}"
    else
        echo -e "${RED}✗ Error: GTK3 or PyGObject not working properly${NC}"
        echo -e "${YELLOW}  Try reinstalling: pip3 install --user --force-reinstall PyGObject${NC}"
    fi
fi

echo ""
echo -e "${GREEN}🎉 All done! You can now run SHYpn.${NC}"
echo ""
