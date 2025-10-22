# Wayland Error 71 - Final Simple Plan

**Date:** October 21, 2025  
**Problem:** Widget reparenting after window.show_all()  
**Solution:** Simplify panel loaders - no reparenting, just state updates  
**Effort:** 4-6 hours

---

## 🎯 THE PROBLEM (Crystal Clear)

You have **4 panels** (Files, Analyses, Pathways, Topology) that can:
- **Attach** - Show in main window (GtkStack)
- **Float** - Show in separate window
- **Hide** - Hide from view

**Current Issue:**
```
Panel tries to move widget after window is shown
    ↓
Wayland sees reparenting of realized widget
    ↓
Error 71: Protocol error
    ↓
Application crashes or becomes unstable
```

**Root Cause:**
Panel loaders have overcomplicated attach/hide logic that moves widgets unnecessarily.

---

## ✅ THE FIX (Three Simple Methods)

### 1. Simplify `attach()` Method
**Purpose:** Show panel in main window stack

**Current Code (Complex):**
```python
def attach_to(self, stack, parent_window=None):
    # 45 lines of complex logic
    # Checks if loaded
    # Checks if attached
    # Schedules idle callbacks
    # Updates parent window
    # BUT DOESN'T ACTUALLY MOVE WIDGET
```

**New Code (Simple):**
```python
def attach(self, parent_window=None):
    """Show panel in main window stack."""
    if self.is_attached:
        return  # Already attached
    
    # Only move if floating
    if self.content.get_parent() == self.window:
        self.window.hide()
        self.window.remove(self.content)
        self.stack_container.add(self.content)
    
    self.is_attached = True
    if parent_window:
        self.parent_window = parent_window
    if self.on_attach_callback:
        self.on_attach_callback()
```

### 2. Simplify `float()` Method
**Purpose:** Show panel in separate window

**New Code:**
```python
def float(self, parent_window=None):
    """Show panel in floating window."""
    if not self.is_attached:
        if not self.window.get_visible():
            self.window.show_all()
        return
    
    # Move from stack to window
    if self.content.get_parent() == self.stack_container:
        self.stack_container.remove(self.content)
        self.window.add(self.content)
    
    self.is_attached = False
    if parent_window:
        self.window.set_transient_for(parent_window)
    self.window.show_all()
```

### 3. Simplify `hide()` Method
**Purpose:** Hide panel without moving it

**New Code:**
```python
def hide(self):
    """Hide panel (stays in current parent)."""
    if not self.is_attached:
        if self.window.get_visible():
            self.window.hide()
```

---

## 📋 IMPLEMENTATION CHECKLIST

### Files to Modify

**Panel Loaders (4 files):**
- [ ] `src/shypn/helpers/left_panel_loader.py`
- [ ] `src/shypn/helpers/right_panel_loader.py`
- [ ] `src/shypn/helpers/pathway_panel_loader.py`
- [ ] `src/shypn/helpers/topology_panel_loader.py`

**Main Integration (1 file):**
- [ ] `src/shypn.py`

### Changes Per File

**Each Panel Loader:**
1. Replace `attach_to(container, parent)` with `attach(parent)`
2. Simplify `float(parent)` method
3. Simplify `hide()` method
4. Remove `_attach_in_progress` flag
5. Remove `_do_attach()` idle callback
6. Remove `unattach()` method

**Main Integration:**
1. Change `loader.attach_to(container, window)` to `loader.attach(window)`
2. Remove idle callback delays
3. Keep stack visibility control in toggle handlers

---

## 🧪 TESTING PLAN

### Test 1: Individual Panels
```bash
# Test each panel in isolation
./dev/test_file_panel_wayland.py
./dev/test_pathway_panel_wayland.py

# Expected: No Error 71, clean attach/float/hide
```

### Test 2: Integration
```bash
# Test full application
python3 src/shypn.py

# Actions:
# 1. Click Files button
# 2. Click Analyses button
# 3. Click Pathways button
# 4. Click Topology button
# 5. Float Files panel
# 6. Attach Files panel
# 7. Rapidly click buttons

# Expected: No errors, smooth transitions
```

### Test 3: Stress Test
```bash
# Rapid panel switching
for i in {1..20}; do
    # Simulate rapid button clicks
    echo "Cycle $i"
done

# Expected: No crashes, stable state
```

---

## 🎯 SUCCESS METRICS

**Zero Tolerance:**
- ❌ No Wayland Error 71
- ❌ No orphaned widgets
- ❌ No application crashes

**Code Quality:**
- ✅ Each method < 30 lines
- ✅ Clear state transitions
- ✅ Consistent API across panels

**User Experience:**
- ✅ Instant panel switching
- ✅ Smooth float/attach
- ✅ No visual glitches

---

## 📚 DOCUMENTATION

**Created:**
- ✅ `doc/SIMPLE_PANEL_FIX_PLAN.md` - Detailed plan
- ✅ `doc/PANEL_STATE_DIAGRAM.md` - Visual diagrams
- ✅ `doc/WAYLAND_FIX_FINAL_PLAN.md` - This file

**Reference:**
- `doc/UI_REFACTORING_PLAN.md` - Original analysis
- `dev/README_WAYLAND_TESTS.md` - Test documentation

---

## 🚀 NEXT STEP

**Ready to implement?**

Say: **"Let's fix the panel loaders"**

I'll start with `left_panel_loader.py` and show you the exact code changes needed.
