# VS Code Setup Validation Report

**Date:** October 1, 2025  
**Purpose:** Validate that VS Code workspace is correctly configured to run GTK4 applications under WSLg without Conda/environment conflicts.

---

## Test Results Summary

✅ **All configuration files are valid and present**  
✅ **System Python can launch the GTK4 app successfully**  
✅ **Sanitized environment (mimicking VS Code) works correctly**

---

## Configuration Files Status

### ✅ `.vscode/settings.json`
**Status:** Fixed and validated

**Configuration:**
- Python interpreter: `/usr/bin/python3` (system Python)
- Environment file: `.env` loaded
- Terminal activation: Disabled (prevents Conda auto-activation)
- Terminal environment variables forwarded: `DISPLAY`, `WAYLAND_DISPLAY`, `GDK_BACKEND`, `XDG_RUNTIME_DIR`, `DBUS_SESSION_BUS_ADDRESS`

### ✅ `.vscode/launch.json`
**Status:** Valid

**Debug Configuration:** "Run shypn (system python)"
- Type: `debugpy`
- Console: `externalTerminal` (prevents sanitized VS Code environment issues)
- Environment variables:
  - **Cleared:** `CONDA_DEFAULT_ENV`, `CONDA_PREFIX`, `CONDA_PROMPT_MODIFIER`, `LD_LIBRARY_PATH`, `PYTHONPATH`, `GI_TYPELIB_PATH`
  - **Forwarded:** `PATH` (with `/usr/bin` first), `DISPLAY`, `WAYLAND_DISPLAY`, `GDK_BACKEND`, `XDG_RUNTIME_DIR`, `DBUS_SESSION_BUS_ADDRESS`, `HOME`

### ✅ `.vscode/tasks.json`
**Status:** Valid

**Task:** "Run shypn (system python)"
- Command: `/usr/bin/python3 ${workspaceFolder}/src/shypn.py`
- Same environment variable setup as launch config
- Set as default build task

---

## Test Results

### Test 1: System Python from Terminal
**Command:**
```bash
/usr/bin/python3 src/shypn.py
```

**Result:** ✅ **SUCCESS**
- App launched without errors
- No GTK criticals or warnings
- No segmentation faults
- Process ran cleanly

### Test 2: Sanitized Environment (VS Code simulation)
**Command:**
```bash
env -i \
  PATH="/usr/bin:$PATH" \
  DISPLAY="$DISPLAY" \
  WAYLAND_DISPLAY="$WAYLAND_DISPLAY" \
  GDK_BACKEND="$GDK_BACKEND" \
  XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
  DBUS_SESSION_BUS_ADDRESS="$DBUS_SESSION_BUS_ADDRESS" \
  HOME="$HOME" \
  /usr/bin/python3 src/shypn.py
```

**Result:** ✅ **SUCCESS**
- App launched successfully with minimal environment
- Confirms that VS Code's environment forwarding should work
- No errors or crashes

---

## How to Test in VS Code

### Method 1: Using the Debug Configuration (Recommended)

1. **Open VS Code** in the shypn workspace
2. **Press F5** or go to Run → Start Debugging
3. **Select** "Run shypn (system python)" from the dropdown
4. **Expected result:**
   - An external terminal window opens
   - The GTK4 application window appears
   - No errors in the terminal

**Note:** The app uses `externalTerminal` so it launches in a separate terminal window with full session environment access.

### Method 2: Using the Build Task

1. **Open VS Code** in the shypn workspace
2. **Press Ctrl+Shift+B** (or Terminal → Run Build Task)
3. **Select** "Run shypn (system python)"
4. **Expected result:**
   - The integrated terminal shows the command output
   - The GTK4 application window appears
   - No error messages

### Method 3: Direct Terminal Command

1. **Open integrated terminal** in VS Code (Ctrl+`)
2. **Run:**
   ```bash
   /usr/bin/python3 src/shypn.py
   ```
3. **Expected result:**
   - App launches successfully
   - Window appears without errors

---

## Troubleshooting

### If you still see segmentation faults:

**Check 1: Verify Python interpreter**
```bash
which python3
# Should show: /usr/bin/python3
```

**Check 2: Verify gi module is available**
```bash
/usr/bin/python3 -c "import gi; print(gi.__file__)"
# Should show: /usr/lib/python3/dist-packages/gi/__init__.py
```

**Check 3: Check display environment**
```bash
echo $DISPLAY
echo $WAYLAND_DISPLAY
echo $XDG_RUNTIME_DIR
echo $DBUS_SESSION_BUS_ADDRESS
```

**Check 4: Run diagnostic script**
```bash
/usr/bin/python3 scripts/debug_shypn_env.py
```
Expected output should show:
- All environment variables populated
- `gi import: OK`
- `Gdk.Display.get_default()` returns a valid display object (not None)

### If display is None:

Try forcing X11 backend instead of Wayland:
```bash
GDK_BACKEND=x11 /usr/bin/python3 src/shypn.py
```

Or update `.env` file:
```bash
DISPLAY=:0
WAYLAND_DISPLAY=wayland-0
GDK_BACKEND=x11
```

### If VS Code doesn't use system Python:

1. Open Command Palette (Ctrl+Shift+P)
2. Type: "Python: Select Interpreter"
3. Choose: `/usr/bin/python3`
4. Restart VS Code

---

## Environment Variables Reference

### Required for GTK/Wayland:
- `DISPLAY` — X11 display identifier (e.g., `:0`)
- `WAYLAND_DISPLAY` — Wayland socket name (e.g., `wayland-0`)
- `XDG_RUNTIME_DIR` — User runtime directory (e.g., `/run/user/1002/`)
- `DBUS_SESSION_BUS_ADDRESS` — D-Bus session bus socket (e.g., `unix:path=/run/user/1002/bus`)
- `HOME` — User home directory

### Cleared to avoid Conda conflicts:
- `CONDA_DEFAULT_ENV` — Set to empty string
- `CONDA_PREFIX` — Set to empty string
- `CONDA_PROMPT_MODIFIER` — Set to empty string
- `LD_LIBRARY_PATH` — Set to empty string (prevents Conda library mixing)
- `PYTHONPATH` — Set to empty string (prevents mixed site-packages)
- `GI_TYPELIB_PATH` — Set to empty string (prevents GObject typelib conflicts)

---

## Next Steps

Once VS Code setup is validated:

1. ✅ **Environment is working** — proceed with GTK4 migration
2. **Design panel architecture** — implement DockManager following `ui/DOCK_UNDOCK_DESIGN.md`
3. **Create first panel** — start with a simple panel to validate architecture
4. **Build adapters** — expose legacy business logic to new panels
5. **Migrate UI components** — incrementally replace legacy GTK3 UI

---

## Additional Resources

- **Project structure rules:** `doc/PROJECT_STRUCTURE_AND_RULES.md`
- **UI architecture design:** `ui/DOCK_UNDOCK_DESIGN.md`
- **Diagnostic script:** `scripts/debug_shypn_env.py`
- **Environment file:** `.env`

---

## Validation Checklist

- [x] VS Code settings.json configured with system Python
- [x] VS Code launch.json has debug config with external terminal
- [x] VS Code tasks.json has run task with proper environment
- [x] System Python can run the app from terminal
- [x] Sanitized environment test passes
- [ ] **User confirms:** App runs from VS Code without segfaults
- [ ] **User confirms:** Window displays correctly
- [ ] **User confirms:** No GTK critical errors

---

**Status:** Ready for user validation  
**Action Required:** Test running the app from VS Code using F5 or Ctrl+Shift+B
