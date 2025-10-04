# SHYpn - Quick Start Guide

## Running the Application

The simplest way to run SHYpn:

```bash
./run.sh
```

Or directly:

```bash
/usr/bin/python3 src/shypn.py
```

## Why System Python?

SHYpn uses **system Python** (`/usr/bin/python3`) instead of conda because:

1. ✅ Proper GTK3 + Cairo integration
2. ✅ All dependencies already installed via `apt`
3. ✅ No "foreign struct converter" errors
4. ✅ Faster startup (no conda activation)
5. ✅ Simpler dependency management

## System Requirements

### Already Installed ✓

Your system already has all required packages:

```bash
python3              # 3.12.3
python3-gi           # PyGObject 3.48.2
python3-gi-cairo     # Cairo bindings
gir1.2-gtk-3.0       # GTK 3.24
libgtk-3-0           # GTK3 library
```

### Verify Installation

Test that everything works:

```bash
/usr/bin/python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk; print('✓ GTK3 works!')"
```

## Project Structure

```
shypn/
├── src/
│   ├── shypn.py              # Main entry point
│   └── shypn/                # Application modules
│       ├── helpers/          # UI loaders
│       ├── data/             # Data models
│       ├── edit/             # Edit operations
│       └── file/             # Persistency
├── ui/                       # GTK3 UI files (.ui)
├── tests/                    # Unit tests
├── doc/                      # Documentation
├── run.sh                    # Launch script ⭐
└── README.md
```

## Development

### Running Tests

```bash
/usr/bin/python3 tests/test_document_persistence.py
```

### Editing Code

The application uses GTK3 with Python. Main files:

- `src/shypn.py` - Application entry point
- `src/shypn/helpers/model_canvas_loader.py` - Canvas management
- `src/shypn/data/model_canvas_manager.py` - Drawing logic
- `src/shypn/file/net_obj_persistency.py` - Save/load documents

## Common Issues

### "ModuleNotFoundError: No module named 'gi'"

**Solution**: Install system packages:

```bash
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

### "Couldn't find foreign struct converter for 'cairo.Context'"

**Solution**: Use system Python (not conda). The `run.sh` script does this automatically.

### Grid doesn't appear

This was a conda-specific issue. System Python works perfectly.

## Documentation

- **`CAIRO_FIX_FINAL.md`** - Cairo error resolution (completed)
- **`GTK_CONDA_FIX.md`** - GTK3 conda issues (outdated, use system Python instead)
- **`INSTALLATION.md`** - Full installation guide
- **`README.md`** - Project overview

## Quick Commands

```bash
# Run application
./run.sh

# Run application directly
/usr/bin/python3 src/shypn.py

# Run tests
/usr/bin/python3 tests/test_document_persistence.py

# Check Python/GTK version
/usr/bin/python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk; print(f'GTK {Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}')"
```

## Status

✅ **WORKING PERFECTLY**

- Application starts successfully
- Grid renders correctly
- All drawing operations work
- No Cairo Context errors
- Save/Load functionality works

---

**Last Updated**: October 4, 2025  
**Status**: All environment issues resolved - using system Python
