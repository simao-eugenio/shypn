# SHYpn - Quick Setup Commands

## For Your Conda Environment Named 'shypn'

### Option 1: Quick Setup (Recommended)
```bash
# Run the quick setup script
./setup_conda_env.sh shypn
```

### Option 2: Full Installation Script
```bash
# Run the comprehensive installer
./install_dependencies.sh --conda-env shypn
```

### Option 3: Manual Setup
```bash
# 1. Install system dependencies (only need to do once)
sudo apt-get update
sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
    libgtk-3-dev libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev

# 2. Activate your conda environment
conda activate shypn

# 3. Install PyGObject
conda install -c conda-forge pygobject gtk3 -y

# 4. Done! Run the app
python src/shypn.py
```

---

## Running the Application

### Quick Start:
```bash
# Use the run script (includes GTK3 fix for conda)
chmod +x run.sh
./run.sh
```

### Or manually:
```bash
# Activate conda environment
conda activate shypn

# Fix GTK3 grid rendering (important for conda!)
export GI_TYPELIB_PATH=/usr/lib/x86_64-linux-gnu/girepository-1.0:$GI_TYPELIB_PATH
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Run SHYpn
python src/shypn.py
```

### Alternative (use system Python):
```bash
# Skip conda, use system Python
python3 src/shypn.py
```

---

## Important: GTK3 Grid Rendering Issue

**Problem:** Grid doesn't appear in conda environment?  
**Solution:** Use `./run.sh` or set environment variables (see above)

For detailed fix: See **GTK_CONDA_FIX.md**

---

## Troubleshooting

### If you get "No module named 'gi'":
```bash
conda activate shypn
conda install -c conda-forge pygobject gtk3 -y
```

### If conda environment doesn't exist:
```bash
# Create it
conda create -n shypn python=3.10 -y

# Then run setup
./setup_conda_env.sh shypn
```

### If you get GTK errors:
```bash
# Install system packages first
sudo apt-get install -y python3-gi gir1.2-gtk-3.0 libgtk-3-dev

# Then reinstall in conda
conda activate shypn
conda install -c conda-forge pygobject gtk3 -y
```

---

## Quick Test

```bash
# Activate environment
conda activate shypn

# Test if GTK3 works
python -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk; print('✓ GTK3 working!')"
```

If you see "✓ GTK3 working!" you're all set! 🎉

---

**Note:** For detailed information, see **INSTALLATION.md**
