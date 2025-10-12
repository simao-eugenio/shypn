# Pathway Import - System-Wide Installation Guide

**Date**: October 12, 2025  
**Issue**: Conda conflicts with GTK/GI (pygobject)  
**Solution**: Use system-wide packages only (no conda) ✅

---

## THE PROBLEM: Conda vs GI

### Why Conda Doesn't Work Well

```
❌ PROBLEMATIC SETUP:
Conda Environment
├── python-libsbml (conda)
├── python packages (conda)
└── ❌ pygobject/GTK (SYSTEM)  ← Can't install in conda!

Result: Import conflicts, segfaults, version mismatches
```

### Why GTK Must Be System-Wide

**GTK/GI Dependencies**:
- GTK+ 3.0 libraries (system C libraries)
- GObject Introspection (system)
- Pygobject (Python bindings to system)

**These CANNOT be installed in conda** without major issues.

---

## THE SOLUTION: All System-Wide ✅

```
✅ WORKING SETUP:
System Python 3
├── python3-gi (system package)
├── python3-cairo (system package)
├── python3-libsbml (system package) ← ADD THIS
└── Other Python packages (pip --user or system)

Result: Everything compatible!
```

---

## INSTALLATION METHODS

### Method 1: System Package Manager ⭐ RECOMMENDED

**Ubuntu/Debian**:
```bash
# Install libsbml via apt
sudo apt update
sudo apt install python3-libsbml

# Verify
python3 -c "import libsbml; print('libSBML version:', libsbml.getLibSBMLVersion())"
```

**Fedora/RHEL**:
```bash
# Install libsbml via dnf
sudo dnf install python3-libsbml

# Verify
python3 -c "import libsbml; print('libSBML version:', libsbml.getLibSBMLVersion())"
```

**Arch Linux**:
```bash
# Install from AUR
yay -S python-libsbml

# Verify
python3 -c "import libsbml; print('libSBML version:', libsbml.getLibSBMLVersion())"
```

---

### Method 2: Pip User Install (Fallback)

If system package not available:

```bash
# Install to user directory (no sudo needed)
pip3 install --user python-libsbml

# Verify
python3 -c "import libsbml; print('libSBML version:', libsbml.getLibSBMLVersion())"
```

**Benefits**:
- No sudo required
- No conda conflicts
- Works with system GTK
- User-specific installation

---

### Method 3: Build from Source (Advanced)

Only if methods 1-2 fail:

```bash
# Install dependencies
sudo apt install libxml2-dev zlib1g-dev

# Download and build
wget https://github.com/sbmlteam/python-libsbml/archive/refs/tags/v5.20.2.tar.gz
tar -xzf v5.20.2.tar.gz
cd python-libsbml-5.20.2
python3 setup.py install --user

# Verify
python3 -c "import libsbml; print('libSBML version:', libsbml.getLibSBMLVersion())"
```

---

## VERIFICATION CHECKLIST

### 1. Check System Python
```bash
which python3
# Should be: /usr/bin/python3 (system Python)
```

### 2. Check GTK/GI (Already Working)
```bash
python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk; print('GTK OK')"
# Should print: GTK OK
```

### 3. Check libSBML (New)
```bash
python3 -c "import libsbml; print('libSBML version:', libsbml.getLibSBMLVersion())"
# Should print: libSBML version: 52002 (or similar)
```

### 4. Check networkx (For layout)
```bash
python3 -c "import networkx; print('networkx OK')"
# If missing: pip3 install --user networkx
```

### 5. Full Integration Test
```bash
python3 -c "
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import libsbml
import networkx
print('✅ All dependencies OK!')
print('  GTK:', Gtk.get_major_version(), Gtk.get_minor_version())
print('  libSBML:', libsbml.getLibSBMLVersion())
print('  networkx:', networkx.__version__)
"
```

---

## DEPENDENCY SUMMARY

### Required for Pathway Import

| Package | Installation | Purpose |
|---------|--------------|---------|
| python3-libsbml | `sudo apt install python3-libsbml` | SBML parsing |
| python3-networkx | `pip3 install --user networkx` | Layout algorithms |

### Already Installed (GTK/GI)

| Package | Status | Purpose |
|---------|--------|---------|
| python3-gi | ✅ Installed | GTK bindings |
| python3-cairo | ✅ Installed | Drawing |
| GTK+ 3.0 | ✅ Installed | UI framework |

---

## INSTALLATION SCRIPT

### One-Command Installation (Ubuntu/Debian)

```bash
# Copy-paste this entire block:

# Install python3-libsbml (system package)
sudo apt update && sudo apt install -y python3-libsbml

# Install networkx (user package)
pip3 install --user networkx

# Verify everything
echo ""
echo "═══════════════════════════════════════"
echo "Verification:"
echo "═══════════════════════════════════════"

# Check libSBML
python3 -c "import libsbml; print('✅ libSBML:', libsbml.getLibSBMLVersion())" 2>&1 | grep -q "✅" && echo "✅ libSBML installed" || echo "❌ libSBML failed"

# Check networkx
python3 -c "import networkx; print('✅ networkx:', networkx.__version__)" 2>&1 | grep -q "✅" && echo "✅ networkx installed" || echo "❌ networkx failed"

# Check GTK (should already work)
python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk; print('✅ GTK OK')" 2>&1 | grep -q "✅" && echo "✅ GTK OK" || echo "❌ GTK failed"

echo "═══════════════════════════════════════"
echo ""
echo "If all ✅ above, you're ready to proceed!"
```

---

## ALTERNATIVE: If System Package Not Available

```bash
# Fallback to pip user install
pip3 install --user python-libsbml networkx

# Verify
python3 << 'EOF'
try:
    import libsbml
    import networkx
    print("✅ Dependencies installed via pip --user")
    print(f"  libSBML version: {libsbml.getLibSBMLVersion()}")
    print(f"  networkx version: {networkx.__version__}")
except ImportError as e:
    print(f"❌ Import failed: {e}")
EOF
```

---

## UPDATE requirements.txt

Add to `requirements.txt` (with note about system packages):

```txt
# requirements.txt

# Core dependencies (can be pip installed)
networkx>=2.6

# System dependencies (install via apt/dnf):
# - python3-libsbml (apt: python3-libsbml)
# - python3-gi (apt: python3-gi)
# - python3-cairo (apt: python3-cairo)
#
# If system package not available, install via pip:
#   pip3 install --user python-libsbml
```

---

## CONDA ALTERNATIVE (If You Must Use Conda)

⚠️ **Not recommended** due to GTK conflicts, but possible with workarounds:

```bash
# Create conda environment
conda create -n shypn python=3.10

# Install conda packages
conda activate shypn
conda install -c conda-forge python-libsbml networkx

# Use system GTK (symlink approach)
# This is fragile and not recommended!
ln -s /usr/lib/python3/dist-packages/gi ~/.conda/envs/shypn/lib/python3.10/site-packages/
ln -s /usr/lib/python3/dist-packages/cairo ~/.conda/envs/shypn/lib/python3.10/site-packages/

# Run shypn
python src/shypn.py
```

**Problems with this approach**:
- ❌ Symlinks are fragile
- ❌ Version mismatches possible
- ❌ Segfaults common
- ❌ Hard to debug

**Recommendation**: DON'T use conda for GTK apps! ✋

---

## WHY SYSTEM-WIDE IS BETTER

### ✅ Advantages

1. **No conflicts**: GTK and libsbml both from same source
2. **Stable**: System package manager handles dependencies
3. **Fast**: No environment switching
4. **Simple**: Just run `python3 src/shypn.py`
5. **Maintainable**: System updates handle everything

### ❌ Conda Disadvantages (for GTK apps)

1. **GTK conflicts**: Can't install pygobject properly
2. **Segfaults**: Mixed system/conda libraries
3. **Complex**: Need workarounds and symlinks
4. **Fragile**: Breaks on updates
5. **Slow**: Environment activation overhead

---

## YOUR CURRENT SETUP (Keep It!)

```
✅ Current Working Setup:
System Python 3.x
├── python3-gi (system) ← Working
├── python3-cairo (system) ← Working
├── GTK+ 3.0 (system) ← Working
└── Your shypn code ← Working

Just add:
└── python3-libsbml (system) ← Need to add
└── python3-networkx (pip --user) ← Need to add
```

**This is the BEST setup for GTK applications!** ✅

---

## INSTALLATION COMMAND (Ubuntu/Debian)

```bash
# Install libsbml system-wide
sudo apt install python3-libsbml

# Install networkx for current user
pip3 install --user networkx

# Done! ✅
```

---

## TROUBLESHOOTING

### Issue: `python3-libsbml` package not found

**Solution**: Use pip instead
```bash
pip3 install --user python-libsbml
```

### Issue: Import error after pip install

**Solution**: Check Python user packages path
```bash
python3 -m site --user-site
# Add to ~/.bashrc if needed:
export PYTHONPATH="$HOME/.local/lib/python3.x/site-packages:$PYTHONPATH"
```

### Issue: Multiple Python versions

**Solution**: Use specific version
```bash
python3.10 -m pip install --user python-libsbml networkx
# Then run: python3.10 src/shypn.py
```

---

## FINAL VERIFICATION

Run this complete test:

```bash
python3 << 'EOF'
import sys
print(f"Python: {sys.version}")
print(f"Executable: {sys.executable}")
print()

# Test GTK (should already work)
try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    print(f"✅ GTK {Gtk.get_major_version()}.{Gtk.get_minor_version()}")
except Exception as e:
    print(f"❌ GTK failed: {e}")

# Test libSBML (new)
try:
    import libsbml
    version = libsbml.getLibSBMLVersion()
    major = version // 10000
    minor = (version % 10000) // 100
    patch = version % 100
    print(f"✅ libSBML {major}.{minor}.{patch}")
except Exception as e:
    print(f"❌ libSBML failed: {e}")
    print("   Install: sudo apt install python3-libsbml")

# Test networkx (new)
try:
    import networkx as nx
    print(f"✅ networkx {nx.__version__}")
except Exception as e:
    print(f"❌ networkx failed: {e}")
    print("   Install: pip3 install --user networkx")

print()
print("If all ✅ above, you're ready to implement pathway import!")
EOF
```

---

## SUMMARY

### ❌ DON'T Use Conda
- Conflicts with GTK/GI
- Segfaults and crashes
- Complex workarounds needed

### ✅ DO Use System-Wide
- Install via apt/dnf
- Or pip3 --user as fallback
- Works perfectly with GTK
- Simple and stable

### Installation Command
```bash
sudo apt install python3-libsbml  # or pip3 install --user python-libsbml
pip3 install --user networkx
```

**That's it!** No conda needed. ✅

