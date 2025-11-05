# Manual Test Protocol: KEGG/SBML Import with Lifecycle System

**Version:** 1.0  
**Date:** 2025-01-05  
**Purpose:** Verify that KEGG pathway and SBML model imports work correctly with canvas lifecycle system and ID scoping

## Overview

This protocol tests the lifecycle system's handling of file imports across multiple canvases. The key features being tested are:
- **ID Isolation:** Each canvas maintains independent ID sequences
- **No Collisions:** IDs in one canvas don't affect another
- **Clean Import:** Files load correctly into canvases
- **Canvas Switching:** IDs remain consistent when switching between canvases

## Prerequisites

- SHYPN application built and running
- Sample KEGG pathway files (`.xml` format)
- Sample SBML model files (`.xml` format)
- Test data location: `data/biomodels_test/` or similar

## Test Suite

### Test 1: Single Canvas KEGG Import (Baseline)

**Purpose:** Verify basic KEGG import functionality

**Steps:**
1. Launch SHYPN
2. File → Open → Select a KEGG pathway file (e.g., `glycolysis.xml`)
3. Wait for import to complete

**Expected Results:**
- ✅ Canvas loads with pathway visualization
- ✅ Places have IDs: P1, P2, P3, ... (sequential)
- ✅ Transitions have IDs: T1, T2, T3, ... (sequential)
- ✅ Arcs have IDs: A1, A2, A3, ... (sequential)
- ✅ No error messages in console

**Verification:**
```python
# Check console output for:
[GLOBAL-SYNC] ✓ Canvas lifecycle system enabled
[GLOBAL-SYNC] ✓ IDManager lifecycle scoping enabled
```

---

### Test 2: Multi-Canvas Independent IDs

**Purpose:** Verify ID isolation between canvases

**Steps:**
1. Launch SHYPN
2. File → Open → Select first KEGG pathway (e.g., `pathway1.xml`)
   - Note: Tab labeled "pathway1"
3. File → Open → Select second KEGG pathway (e.g., `pathway2.xml`)
   - Note: Tab labeled "pathway2"
4. Switch to Tab 1 (pathway1)
5. Inspect element IDs (hover over places/transitions)
6. Switch to Tab 2 (pathway2)
7. Inspect element IDs

**Expected Results:**
- ✅ **Canvas 1 (pathway1):**
  - First place: P1
  - Second place: P2
  - First transition: T1
  
- ✅ **Canvas 2 (pathway2):**
  - First place: P1 (independent from Canvas 1)
  - Second place: P2
  - First transition: T1

**Key Verification:**
Both canvases start their ID sequences from 1, proving independence.

---

### Test 3: Three Canvases - Full Independence

**Purpose:** Verify system handles 3+ canvases correctly

**Steps:**
1. Launch SHYPN
2. File → Open → KEGG pathway 1 (creates Canvas 1)
3. File → Open → KEGG pathway 2 (creates Canvas 2)
4. File → Open → SBML model 1 (creates Canvas 3)
5. Switch between tabs and verify IDs

**Expected Results:**
- ✅ Canvas 1: P1-Pn, T1-Tn (independent sequence)
- ✅ Canvas 2: P1-Pn, T1-Tn (independent sequence)
- ✅ Canvas 3: P1-Pn, T1-Tn (independent sequence)
- ✅ All canvases accessible without errors
- ✅ No ID conflicts or overlaps

---

### Test 4: Add Elements After Import

**Purpose:** Verify ID sequences continue correctly after import

**Steps:**
1. Launch SHYPN
2. File → Open → KEGG pathway (imports P1-P10, T1-T5)
3. Switch to Edit mode
4. Add new place manually
5. Add new transition manually
6. Check IDs

**Expected Results:**
- ✅ Manually added place gets ID: P11 (continues sequence)
- ✅ Manually added transition gets ID: T6 (continues sequence)
- ✅ IDs don't restart from P1/T1
- ✅ No duplicate IDs

---

### Test 5: Multi-Canvas with Manual Additions

**Purpose:** Verify manual additions maintain independence

**Steps:**
1. Launch SHYPN
2. File → Open → pathway1.xml (Canvas 1, imports P1-P5)
3. File → Open → pathway2.xml (Canvas 2, imports P1-P3)
4. Switch to Canvas 1
5. Add new place (should be P6)
6. Switch to Canvas 2
7. Add new place (should be P4)
8. Verify both canvases

**Expected Results:**
- ✅ Canvas 1: Has P1-P5 (imported) + P6 (manually added)
- ✅ Canvas 2: Has P1-P3 (imported) + P4 (manually added)
- ✅ No ID collisions between canvases
- ✅ Each canvas maintains its own sequence

---

### Test 6: Close Middle Canvas

**Purpose:** Verify closing a canvas doesn't affect others

**Steps:**
1. Launch SHYPN
2. Open three pathways (Canvas 1, 2, 3)
3. Note IDs in each canvas
4. Close Canvas 2 (middle tab)
5. Verify Canvas 1 and Canvas 3 still work

**Expected Results:**
- ✅ Canvas 1: IDs unchanged, can add elements
- ✅ Canvas 3: IDs unchanged, can add elements
- ✅ Canvas 2: Properly destroyed (check console for cleanup message)
- ✅ No errors when adding elements to remaining canvases

**Console Verification:**
```
[LIFECYCLE] ✓ Canvas <id> destroyed
```

---

### Test 7: SBML Model Import

**Purpose:** Verify SBML imports work with lifecycle

**Steps:**
1. Launch SHYPN
2. File → Open → Select SBML model file (`.xml`)
3. Wait for import
4. Check element IDs

**Expected Results:**
- ✅ Model imports successfully
- ✅ Species become places with IDs: P1, P2, P3, ...
- ✅ Reactions become transitions with IDs: T1, T2, T3, ...
- ✅ No ID errors in console

---

### Test 8: Mixed Import Types

**Purpose:** Verify KEGG and SBML can coexist

**Steps:**
1. Launch SHYPN
2. File → Open → KEGG pathway (Canvas 1)
3. File → Open → SBML model (Canvas 2)
4. File → Open → KEGG pathway (Canvas 3)
5. Verify all canvases

**Expected Results:**
- ✅ All three canvases load correctly
- ✅ Each has independent ID sequences
- ✅ KEGG and SBML formats both work
- ✅ No import errors

---

### Test 9: Large File Import

**Purpose:** Verify lifecycle handles large files

**Steps:**
1. Launch SHYPN
2. File → Open → Large KEGG pathway (50+ elements)
3. File → Open → Another large pathway
4. Check performance and IDs

**Expected Results:**
- ✅ Import completes without hanging
- ✅ IDs assigned correctly (P1-P50+)
- ✅ Second canvas also starts at P1
- ✅ No performance degradation

---

### Test 10: Canvas Reset After Import

**Purpose:** Verify reset works on imported canvas

**Steps:**
1. Launch SHYPN
2. File → Open → KEGG pathway (imports elements)
3. Note IDs (e.g., P1-P10, T1-T5)
4. File → Reset Canvas (or call reset_current_canvas())
5. Add new elements

**Expected Results:**
- ✅ Canvas clears (all imported elements removed)
- ✅ IDs restart from P1, T1
- ✅ New elements get P1, P2, T1, ... (fresh sequence)
- ✅ Console shows reset message

**Console Verification:**
```
[RESET] ✓ Canvas reset via lifecycle system
```

---

## Regression Tests

### RT1: Legacy Files Still Load

**Purpose:** Ensure old files work with new system

**Steps:**
1. Load a file saved before lifecycle system
2. Verify it opens correctly

**Expected:** File loads, IDs may be re-assigned but structure preserved

---

### RT2: Save and Reload

**Purpose:** Verify saved files preserve structure

**Steps:**
1. Import KEGG pathway
2. Save as `.shy` file
3. Close application
4. Reopen and load saved file

**Expected:** IDs preserved, structure intact

---

## Error Conditions

### EC1: Import Failure Handling

**Purpose:** Verify graceful failure

**Steps:**
1. Try to import corrupted/invalid file
2. Check for error handling

**Expected:** Error message shown, application doesn't crash

---

### EC2: Concurrent Import

**Purpose:** Test rapid tab creation

**Steps:**
1. Quickly open 5 files in succession
2. Verify all load correctly

**Expected:** All canvases created, no ID conflicts

---

## Verification Checklist

After completing all tests, verify:

- ✅ All tests passed
- ✅ No console errors
- ✅ IDs are independent per canvas
- ✅ Imports work for both KEGG and SBML
- ✅ Canvas switching works smoothly
- ✅ Close tab doesn't break other canvases
- ✅ Reset canvas functionality works
- ✅ Manual additions continue sequences correctly
- ✅ Application remains stable

## Console Output Reference

**Expected lifecycle messages:**
```
[GLOBAL-SYNC] ✓ Canvas lifecycle system enabled
[GLOBAL-SYNC] ✓ IDManager lifecycle scoping enabled
[LIFECYCLE] Creating canvas <id> (file=<path>)
[LIFECYCLE] ✓ Canvas <id> destroyed
[RESET] ✓ Canvas reset via lifecycle system
```

**Error indicators (should NOT appear):**
```
[LIFECYCLE] ⚠️  Failed to ...
[GLOBAL-SYNC] ⚠️  Failed to enable lifecycle system
```

## Bug Report Template

If any test fails, use this template:

```
Test: [Test Name]
Step: [Which step failed]
Expected: [What should happen]
Actual: [What actually happened]
Console Output: [Paste relevant console messages]
Canvas IDs: [List IDs observed]
Reproducible: [Yes/No and frequency]
```

## Test Results Log

| Test | Status | Notes | Tester | Date |
|------|--------|-------|--------|------|
| Test 1 | ⬜ | | | |
| Test 2 | ⬜ | | | |
| Test 3 | ⬜ | | | |
| Test 4 | ⬜ | | | |
| Test 5 | ⬜ | | | |
| Test 6 | ⬜ | | | |
| Test 7 | ⬜ | | | |
| Test 8 | ⬜ | | | |
| Test 9 | ⬜ | | | |
| Test 10 | ⬜ | | | |
| RT1 | ⬜ | | | |
| RT2 | ⬜ | | | |
| EC1 | ⬜ | | | |
| EC2 | ⬜ | | | |

✅ = Pass | ❌ = Fail | ⬜ = Not Tested

## Sign-off

**Tester:** ___________________  
**Date:** ___________________  
**Result:** ⬜ PASS | ⬜ FAIL  
**Comments:** ___________________
