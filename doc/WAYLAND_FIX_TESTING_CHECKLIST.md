# Wayland Fix - Testing Checklist

## Completed ✅

### Code Changes (22 locations across 5 files)

- [x] `netobj_persistency.py` - 6 dialog methods
- [x] `file_explorer_panel.py` - 4 dialogs + 1 context menu
- [x] `model_canvas_loader.py` - 3 context menus + 1 error dialog
- [x] `project_dialog_manager.py` - 3 builder dialog parents
- [x] `shypn.py` - 1 unsaved changes dialog
- [x] All files validated - no syntax errors

### Documentation Created

- [x] `WAYLAND_COMPREHENSIVE_FIX.md` - Technical details and patterns
- [x] `WAYLAND_FIX_SUMMARY.md` - Complete summary for review
- [x] This checklist

---

## Ready For Testing ⏳

### Test 1: Application Startup (PRIMARY TEST)

**Command**:
```bash
cd /home/simao/projetos/shypn
python src/shypn.py
```

**Check**:
- [ ] Application starts without "Error 71 (Protocol error)" message
- [ ] No Wayland errors in terminal output
- [ ] Main window displays properly
- [ ] All panels load correctly

**Expected Output** (should NOT see):
```
Gdk-Message: 15:13:26.924: Error 71 (Protocol error) dispatching to Wayland display
```

---

### Test 2: File Operations

**Actions**:
1. Open a pathway or model file
2. Make some changes
3. Try File → Save (Ctrl+S)
4. Try to close tab without saving

**Check**:
- [ ] Save dialog appears properly
- [ ] Unsaved changes warning shows properly
- [ ] All buttons work
- [ ] No Wayland errors

---

### Test 3: Context Menus

**Actions**:
1. Right-click on canvas (empty area)
2. Right-click on file explorer items
3. Right-click on objects (place, transition, arc)

**Check**:
- [ ] Context menus appear at correct position
- [ ] All menu items work
- [ ] No errors or crashes

---

### Test 4: Project Dialogs

**Actions**:
1. File → New Project
2. File → Open Project
3. (If project open) Project → Properties

**Check**:
- [ ] Dialogs display properly
- [ ] Can create new project
- [ ] Can open existing project
- [ ] Properties dialog shows project info

---

### Test 5: Error Dialogs

**Actions**:
1. Create a model
2. Add two places
3. Try to create an arc from place to place (invalid)

**Check**:
- [ ] Error dialog appears
- [ ] Dialog has proper title and message
- [ ] Can dismiss dialog
- [ ] No crashes

---

## If Errors Persist

### Diagnostic Steps

1. **Capture Full Error Output**:
   ```bash
   python src/shypn.py 2>&1 | tee wayland_test.log
   ```

2. **Check Error Timing**:
   - Note EXACTLY when error appears in log
   - What was the last log message before error?
   - Does error appear during startup or after user action?

3. **Enable GTK Debug** (if needed):
   ```bash
   GTK_DEBUG=interactive python src/shypn.py
   ```

4. **Report Back**:
   - Copy the error message
   - Note what action triggered it
   - Share relevant log lines

---

## Expected Results

### Before Fix ❌
```
[Main] Context menu handler wired for analysis menu items
Gdk-Message: 15:13:26.924: Error 71 (Protocol error) dispatching to Wayland display
```

### After Fix ✅
```
[Main] Context menu handler wired for analysis menu items
[Main] Application initialized successfully
```
(No Error 71 message!)

---

## Quick Test Script

Save this as `test_wayland_fix.sh`:
```bash
#!/bin/bash
echo "=== Wayland Fix Test ==="
echo "Starting application..."
python src/shypn.py 2>&1 | grep -E "(Error 71|Context menu handler wired|Application initialized)"
echo "=== Test Complete ==="
```

Run with:
```bash
chmod +x test_wayland_fix.sh
./test_wayland_fix.sh
```

---

## Success Criteria

- ✅ No "Error 71 (Protocol error)" messages
- ✅ All dialogs show properly
- ✅ All context menus work
- ✅ Application stable on Wayland
- ✅ All functionality preserved

---

**Status**: Ready for Testing  
**Priority**: HIGH - Primary functionality fix  
**Estimated Test Time**: 5-10 minutes for full test suite
