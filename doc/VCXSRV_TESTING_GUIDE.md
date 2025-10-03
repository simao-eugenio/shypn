# VcXsrv Display Backend Testing

## Overview

This document explains how to test SHYpn with VcXsrv (X11) instead of WSLg (Wayland) to compare popover behavior between the two display backends.

## Why Test VcXsrv?

While your current WSLg setup is optimal, testing with VcXsrv can help:
- **Compare popover rendering** between X11 and Wayland
- **Diagnose backend-specific issues** if any arise
- **Provide alternative** if WSLg has problems

## Current Setup (Default)

```
Display Backend: WSLg (Wayland)
GTK4 Version: 4.14.5
Display Type: GdkWaylandDisplay
Status: ✅ OPTIMAL
```

## VcXsrv Setup Instructions

### Step 1: Install VcXsrv on Windows

1. Download VcXsrv from: https://sourceforge.net/projects/vcxsrv/
2. Install to default location
3. Do NOT run it yet (we'll configure it first)

### Step 2: Launch VcXsrv with Display :99

**Option A: Using XLaunch (GUI)**

1. Start XLaunch (should be in Start Menu)
2. **Display settings:**
   - Select: "Multiple windows"
   - Display number: `99`
   - Click Next
3. **Client startup:**
   - Select: "Start no client"
   - Click Next
4. **Extra settings:**
   - ☑️ Clipboard
   - ☑️ Primary Selection
   - ☑️ Native opengl
   - ☑️ **Disable access control** (important!)
   - Click Next
5. **Finish:**
   - Optionally save configuration
   - Click Finish

**Option B: Using Command Line (PowerShell/CMD)**

```powershell
# Navigate to VcXsrv installation directory (usually):
cd "C:\Program Files\VcXsrv"

# Start VcXsrv on display 99
.\vcxsrv.exe :99 -multiwindow -clipboard -wgl -ac
```

**Option C: Create Windows Shortcut**

Create a shortcut with target:
```
"C:\Program Files\VcXsrv\vcxsrv.exe" :99 -multiwindow -clipboard -wgl -ac
```

### Step 3: Verify VcXsrv is Running

In WSL terminal:
```bash
cd /home/simao/projetos/shypn
bash scripts/test_vcxsrv_display.sh
```

You should see:
```
✅ VcXsrv on :99 is ACCESSIBLE
```

## Running SHYpn with VcXsrv

### Method 1: Using the Launcher Script

```bash
cd /home/simao/projetos/shypn
bash scripts/run_with_vcxsrv.sh
```

### Method 2: Manual Environment Variables

```bash
cd /home/simao/projetos/shypn
DISPLAY=:99 GDK_BACKEND=x11 python3 src/shypn.py
```

### Method 3: Export for Session

```bash
export DISPLAY=:99
export GDK_BACKEND=x11
unset WAYLAND_DISPLAY

cd /home/simao/projetos/shypn
python3 src/shypn.py
```

## Expected Behavior Differences

### WSLg (Wayland) - Current Default
- **Pros:**
  - Native Wayland protocol
  - Better integration with Windows 11
  - Modern compositor features
  - Lower latency
  - Better HiDPI support
- **Cons:**
  - Newer technology (may have edge cases)

### VcXsrv (X11) - Alternative
- **Pros:**
  - Mature, well-tested protocol
  - Wider compatibility with older apps
  - Known behavior patterns
- **Cons:**
  - Extra process on Windows
  - Slightly higher latency
  - Manual configuration needed
  - Some rendering differences

## Popover Testing Checklist

When testing with VcXsrv, verify:

### Canvas Context Menu
- [ ] Right-click and release shows menu
- [ ] Menu appears at correct position
- [ ] Menu items are visible and readable
- [ ] Menu items are clickable
- [ ] Menu closes when clicking outside
- [ ] Right-click drag still pans canvas

### File Browser Context Menu
- [ ] Right-click on file shows menu
- [ ] Right-click on folder shows menu
- [ ] Right-click on empty space shows menu
- [ ] All 10 menu items visible
- [ ] Menu closes after selection
- [ ] Operations work correctly

### General Behavior
- [ ] No frozen/leftover popovers
- [ ] Multiple menu opens work correctly
- [ ] No graphical glitches
- [ ] Responsive performance

## Troubleshooting

### Issue: "VcXsrv on :99 is NOT accessible"

**Solutions:**
1. Check if VcXsrv is running:
   - Look for VcXsrv icon in Windows system tray
   - Check Windows Task Manager for `vcxsrv.exe`

2. Check Windows Firewall:
   - VcXsrv may be blocked by firewall
   - Allow VcXsrv through Windows Defender Firewall

3. Try different display number:
   ```bash
   # Try :0 instead of :99
   DISPLAY=:0 xset q
   ```

4. Restart VcXsrv with verbose logging:
   ```powershell
   vcxsrv.exe :99 -multiwindow -clipboard -wgl -ac -logverbose 3
   ```

### Issue: "Cannot open display :99"

**Solutions:**
1. Set DISPLAY in WSL:
   ```bash
   export DISPLAY=:99
   ```

2. Check WSL can reach Windows:
   ```bash
   # Should show your Windows IP
   cat /etc/resolv.conf | grep nameserver
   ```

3. Set display with Windows IP:
   ```bash
   export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):99
   ```

### Issue: "Authentication required"

**Solution:**
Restart VcXsrv with `-ac` flag (disable access control):
```powershell
vcxsrv.exe :99 -multiwindow -clipboard -wgl -ac
```

### Issue: Popover appears but looks different

This is **expected** - X11 and Wayland render differently. Specifically:
- Font rendering may differ
- Window decorations may differ
- Animations may differ
- Colors may have slight differences

As long as functionality works, these are normal.

## Comparison Results Template

After testing both backends, document your findings:

```
=== Backend Comparison ===

WSLg (Wayland):
- Canvas menu: ✅/❌
- File browser menu: ✅/❌
- Autohide behavior: ✅/❌
- Performance: Excellent/Good/Fair/Poor
- Notes: ___________

VcXsrv (X11):
- Canvas menu: ✅/❌
- File browser menu: ✅/❌
- Autohide behavior: ✅/❌
- Performance: Excellent/Good/Fair/Poor
- Notes: ___________

Recommendation: WSLg / VcXsrv / Either
```

## Switching Back to WSLg

To return to default WSLg/Wayland:

```bash
unset DISPLAY
unset GDK_BACKEND
export WAYLAND_DISPLAY=wayland-0
export DISPLAY=:0

# Or simply restart your terminal
```

## Performance Monitoring

Compare performance between backends:

```bash
# With WSLg
time python3 src/shypn.py

# With VcXsrv
DISPLAY=:99 GDK_BACKEND=x11 time python3 src/shypn.py
```

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `scripts/test_vcxsrv_display.sh` | Test VcXsrv connectivity and functionality |
| `scripts/run_with_vcxsrv.sh` | Launch SHYpn with VcXsrv backend |

## Recommendations

1. **Keep using WSLg by default** - It's optimal for your system
2. **Test VcXsrv only if:**
   - Experiencing popover issues with WSLg
   - Need to compare behavior
   - Debugging specific problems
3. **Document any differences** you find between backends
4. **Report issues** to appropriate projects:
   - WSLg issues: https://github.com/microsoft/wslg/issues
   - GTK4 issues: https://gitlab.gnome.org/GNOME/gtk/-/issues
   - SHYpn issues: This repository

## References

- VcXsrv Project: https://sourceforge.net/projects/vcxsrv/
- WSLg Documentation: https://github.com/microsoft/wslg
- GTK4 Display Backends: https://docs.gtk.org/gdk4/class.Display.html
- X11 Protocol: https://www.x.org/releases/current/doc/

## Support

If you encounter issues with either backend:

1. Run the test script and save output:
   ```bash
   bash scripts/test_vcxsrv_display.sh > vcxsrv_test.log 2>&1
   ```

2. Check GTK4 debug output:
   ```bash
   GTK_DEBUG=interactive DISPLAY=:99 GDK_BACKEND=x11 python3 src/shypn.py
   ```

3. Include both logs when reporting issues

---

**Note:** Your current WSLg setup (GTK 4.14.5 + WSL2 + WSLg 2.6.1) is excellent and should not require VcXsrv. This testing is purely optional for comparison and troubleshooting purposes.
