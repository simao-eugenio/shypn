# Manual Testing Guide - Canvas Lifecycle System

**Date:** 2025-01-05  
**Feature:** Canvas Lifecycle Management (Global Sync)  
**Status:** Merged to main, ready for manual testing

---

## Quick Test (5 minutes)

### Test 1: Basic Multi-Canvas ID Isolation

1. **Launch shypn**
   ```bash
   cd ~/projetos/shypn
   python3 src/shypn.py
   ```

2. **Create Canvas 1 - Enzymatic Reaction**
   - You should see: `[GLOBAL-SYNC] ✓ Canvas XXX registered with lifecycle system`
   - Add 2 places → Should be named **P1**, **P2**
   - Add 1 transition → Should be named **T1**
   - Note the IDs

3. **Create Canvas 2 - New Document**
   - File → New (or Ctrl+N)
   - You should see: `[GLOBAL-SYNC] ✓ Canvas YYY registered`
   - Add 1 place → Should be named **P1** (not P3!)
   - Add 1 transition → Should be named **T1** (not T2!)
   
4. **Switch Back to Canvas 1**
   - Click first tab
   - You should see: `[GLOBAL-SYNC] ✓ Switched to canvas XXX`
   - Add another place → Should be named **P3** (continues from P2!)
   
5. **Create Canvas 3**
   - File → New again
   - Add 1 place → Should be **P1** (independent!)

**Expected Result:** ✅ Each canvas has independent ID sequences

---

## Comprehensive Test (15 minutes)

### Test 2: Canvas Switching

1. Create 4-5 canvases with different content
2. Switch between tabs randomly
3. Add elements to each
4. Verify IDs continue correctly when returning to a canvas

**Look for:**
- `[GLOBAL-SYNC] ✓ Switched to canvas` messages in terminal
- No ID collisions
- IDs continue from where they left off

### Test 3: File Operations

1. **Save a canvas**
   - Create some places/transitions
   - File → Save As → test1.shy
   - Verify file saves correctly

2. **Open the file**
   - File → Open → test1.shy
   - Verify: `[GLOBAL-SYNC] ✓ Canvas registered`
   - Add more elements
   - IDs should continue from highest in file + 1

3. **Load multiple files**
   - Open 2-3 different .shy files
   - Each should have independent ID scopes
   - Switching between them should maintain scope

### Test 4: KEGG/SBML Import

1. **Import KEGG pathway**
   - KEGG → Import pathway
   - Verify canvas registration message
   - Add new elements
   - IDs should continue from import

2. **Import SBML model**
   - File → Import SBML
   - Same verification as KEGG

### Test 5: Tab Closing

1. Create 5 canvases
2. Close tabs in random order
3. Add elements to remaining canvases
4. Verify no ID conflicts
5. Check terminal for any errors

---

## What to Look For

### ✅ Success Indicators

1. **Terminal messages:**
   ```
   [GLOBAL-SYNC] ✓ Canvas lifecycle system enabled
   [GLOBAL-SYNC] ✓ Canvas XXXXXX registered with lifecycle system
   [GLOBAL-SYNC] ✓ Switched to canvas XXXXXX, tab N
   ```

2. **ID behavior:**
   - New canvas starts at P1, T1, A1
   - IDs continue correctly when returning to canvas
   - No collisions across canvases

3. **No crashes:**
   - Switching tabs doesn't crash
   - Closing tabs doesn't crash
   - Opening files doesn't crash

### ⚠️ Warning Signs

1. **Missing messages:**
   - If you don't see `[GLOBAL-SYNC]` messages, lifecycle might not be active

2. **ID collisions:**
   - If Canvas 2 continues IDs from Canvas 1 (e.g., P3 instead of P1)
   - This would indicate scope switching isn't working

3. **Errors in terminal:**
   - Python tracebacks
   - `AttributeError`, `KeyError`, etc.
   - Memory warnings

---

## Stress Test (Optional - 30 minutes)

### Test 6: Heavy Load

1. Open 10+ canvases
2. Add 20+ places to each
3. Switch between them frequently
4. Monitor memory usage: `htop` or `top`
5. Look for memory leaks

### Test 7: Concurrent Operations

1. Open multiple canvases
2. While simulation running in one canvas
3. Edit another canvas
4. Switch tabs during simulation
5. Verify no interference

---

## Reporting Issues

If you encounter problems:

1. **Check terminal output** for error messages
2. **Note the exact steps** to reproduce
3. **Look for patterns:**
   - Does it happen with specific file types?
   - Only after N canvases?
   - Only with KEGG/SBML imports?

4. **Capture info:**
   ```bash
   # Terminal output
   python3 src/shypn.py 2>&1 | tee test_output.log
   
   # Git info
   git log -1
   git status
   ```

---

## Rollback if Needed

If major issues arise:

```bash
cd ~/projetos/shypn
git log --oneline -5  # Find commit hash before merge
git revert HEAD  # Or git reset --hard <commit-hash>
```

The backup is also available: `backup_20251105_185353_ui_src.tar.gz`

---

## Expected Behavior Summary

| Action | Expected Lifecycle Behavior |
|--------|----------------------------|
| Launch app | "✓ Canvas lifecycle system enabled" |
| Create new canvas | "✓ Canvas XXX registered" |
| Switch tabs | "✓ Switched to canvas XXX, tab N" |
| Add place to new canvas | ID starts at P1 |
| Return to old canvas | ID continues from last used |
| Open file | Canvas registered, IDs continue from file |
| Close tab | No errors, other canvases unaffected |

---

## Next Development (Phase 4)

After manual testing confirms everything works:

- [ ] Integrate lifecycle with File→New (create via lifecycle manager)
- [ ] Integrate lifecycle with File→Close (proper destruction)
- [ ] Update global IDManager to use scoping
- [ ] Add canvas reset functionality
- [ ] Remove legacy dictionaries (final cleanup)

---

**Happy Testing!** 🧪

Report any issues or unexpected behavior. The system is designed to fail gracefully with informative messages.
