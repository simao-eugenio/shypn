#!/bin/bash
# Fix for GTK3 Grid Rendering in Conda Environments
#
# This script helps fix the "grid doesn't appear" issue when running
# SHYpn in a conda environment.

echo "GTK3 Conda Environment Fix"
echo "=========================="
echo ""

# Check if in conda environment
if [[ -z "$CONDA_DEFAULT_ENV" ]]; then
    echo "Warning: Not in a conda environment"
    echo "This fix is only needed when using conda"
    exit 1
fi

echo "Current conda environment: $CONDA_DEFAULT_ENV"
echo ""

# Solution 1: Install complete GTK3 stack in conda
echo "Solution 1: Installing complete GTK3 stack in conda..."
echo ""
read -p "Install GTK3 packages in conda? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    conda install -c conda-forge gtk3 pygobject cairo gdk-pixbuf gobject-introspection -y
    echo ""
    echo "✓ GTK3 packages installed"
    echo ""
fi

# Solution 2: Create environment variables file
echo "Solution 2: Creating environment activation script..."
echo ""

CONDA_ENV_PATH=$(conda info --base)/envs/$CONDA_DEFAULT_ENV

# Create activation script
mkdir -p "$CONDA_ENV_PATH/etc/conda/activate.d"
cat > "$CONDA_ENV_PATH/etc/conda/activate.d/gtk3_fix.sh" << 'EOF'
#!/bin/bash
# GTK3 fix for conda environment
# Forces use of system GTK3 libraries for proper grid rendering

export GI_TYPELIB_PATH=/usr/lib/x86_64-linux-gnu/girepository-1.0:/usr/lib/girepository-1.0:$GI_TYPELIB_PATH
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

echo "GTK3 environment variables set (using system libraries)"
EOF

chmod +x "$CONDA_ENV_PATH/etc/conda/activate.d/gtk3_fix.sh"

echo "✓ Activation script created at:"
echo "  $CONDA_ENV_PATH/etc/conda/activate.d/gtk3_fix.sh"
echo ""

# Create deactivation script
mkdir -p "$CONDA_ENV_PATH/etc/conda/deactivate.d"
cat > "$CONDA_ENV_PATH/etc/conda/deactivate.d/gtk3_fix.sh" << 'EOF'
#!/bin/bash
# Reset GTK3 environment variables
unset GI_TYPELIB_PATH_BACKUP
unset LD_LIBRARY_PATH_BACKUP
EOF

chmod +x "$CONDA_ENV_PATH/etc/conda/deactivate.d/gtk3_fix.sh"

echo "✓ Deactivation script created"
echo ""

echo "=========================="
echo "Setup Complete!"
echo "=========================="
echo ""
echo "The fix will activate automatically when you activate the conda environment."
echo ""
echo "To apply the fix now, run:"
echo "  conda deactivate"
echo "  conda activate $CONDA_DEFAULT_ENV"
echo ""
echo "Then test the app:"
echo "  python src/shypn.py"
echo ""
