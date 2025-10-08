# KEGG Import End-to-End Testing Checklist

**Date**: October 7, 2025  
**Status**: 🔄 In Progress

## Test Environment

- **Application**: shypn
- **Branch**: feature/property-dialogs-and-simulation-palette
- **Test Pathway**: hsa00010 (Glycolysis / Gluconeogenesis)

## Testing Checklist

### 1. Application Launch ⬜

```bash
cd /home/simao/projetos/shypn
python3 src/shypn.py
```

**Expected**:
- ✅ Application launches without errors
- ✅ Main window appears
- ✅ Canvas is visible
- ✅ Header bar shows: "File Ops", "Pathways", "Analyses" buttons

**Result**: [ PENDING ]

---

### 2. Panel Toggle - Show Pathways ⬜

**Action**: Click "Pathways" button in header bar

**Expected**:
- ✅ Pathways panel docks on right side
- ✅ Analyses panel hidden (if was visible)
- ✅ Panel shows 3 tabs: Import, Browse, History
- ✅ Import tab is active by default
- ✅ Panel width ~320px

**Result**: [ PENDING ]

---

### 3. Panel UI - Import Tab Widgets ⬜

**Expected widgets visible**:
- ✅ Pathway ID entry field (empty)
- ✅ Organism dropdown (default: "Homo sapiens (hsa)")
- ✅ "Fetch Pathway" button (enabled)
- ✅ Import options section (collapsed or visible)
- ✅ "Import to Canvas" button (disabled initially)
- ✅ Preview text area (empty)

**Result**: [ PENDING ]

---

### 4. Fetch Pathway ⬜

**Action**: 
1. Enter "hsa00010" in Pathway ID field
2. Click "Fetch Pathway" button

**Expected**:
- ✅ Status message: "Fetching pathway..."
- ✅ Button temporarily disabled during fetch
- ✅ Progress indication (if implemented)
- ✅ After ~2-3 seconds: Success message
- ✅ Preview area shows pathway info:
  - Name: "Glycolysis / Gluconeogenesis"
  - Organism: Homo sapiens (hsa)
  - Statistics: ~31 places, ~34 transitions, ~73 arcs
- ✅ "Import to Canvas" button now enabled

**Result**: [ PENDING ]

---

### 5. Preview Content Validation ⬜

**Check preview shows**:
- ✅ Pathway name
- ✅ Organism
- ✅ Number of compounds (places)
- ✅ Number of reactions (transitions)
- ✅ Number of connections (arcs)
- ✅ Optional: List of key compounds
- ✅ Optional: Import options summary

**Result**: [ PENDING ]

---

### 6. Import Options (Optional) ⬜

**If options visible, check**:
- ✅ Filter cofactors checkbox (default: checked)
- ✅ Coordinate scaling factor (default: 1.0)
- ✅ Options can be toggled/changed
- ✅ Preview updates if options changed

**Result**: [ PENDING / N/A ]

---

### 7. Import to Canvas ⬜

**Action**: Click "Import to Canvas" button

**Expected**:
- ✅ Status message: "Importing pathway..."
- ✅ Progress indication
- ✅ After ~1-2 seconds: Success message
- ✅ Canvas shows imported pathway:
  - Places appear as circles
  - Transitions appear as rectangles
  - Arcs connect them
  - Layout roughly matches KEGG coordinates
- ✅ Canvas is zoomable/pannable
- ✅ Objects are selectable

**Result**: [ PENDING ]

---

### 8. Verify Imported Objects ⬜

**On Canvas**:
- ✅ Count places (should be ~31)
- ✅ Count transitions (should be ~34)
- ✅ Places have labels (compound names)
- ✅ Transitions have labels (reaction/enzyme names)
- ✅ Arcs connect places to transitions
- ✅ No disconnected objects (unless expected)

**Result**: [ PENDING ]

---

### 9. Panel Toggle - Hide Pathways ⬜

**Action**: Click "Pathways" button again

**Expected**:
- ✅ Pathways panel hides
- ✅ Canvas expands to full width
- ✅ Imported pathway remains on canvas
- ✅ Button toggle state: inactive

**Result**: [ PENDING ]

---

### 10. Panel Toggle - Show Analyses (Mutual Exclusivity) ⬜

**Action**: Click "Analyses" button

**Expected**:
- ✅ Analyses panel docks on right
- ✅ Pathways panel remains hidden
- ✅ Only one panel visible at a time

**Action**: Click "Pathways" button again

**Expected**:
- ✅ Pathways panel docks on right
- ✅ Analyses panel hides
- ✅ Mutual exclusivity works correctly

**Result**: [ PENDING ]

---

### 11. Float Panel ⬜

**With Pathways panel visible**:

**Action**: Click float button (⇲) in panel header

**Expected**:
- ✅ Panel becomes floating window
- ✅ Window can be moved independently
- ✅ Window has title: "Pathway Operations"
- ✅ Float button state: active
- ✅ Panel content still functional

**Result**: [ PENDING ]

---

### 12. Close Floating Window (Critical Test) ⬜

**Action**: Click X button on floating window

**Expected**:
- ✅ Window closes smoothly
- ✅ **NO segmentation fault** (Exit Code 139)
- ✅ **NO crash**
- ✅ Panel hides
- ✅ Panel docks back to main window
- ✅ Float button updates to inactive
- ✅ Application remains running

**Result**: [ PENDING ]

---

### 13. Reopen Panel After Close ⬜

**Action**: Click "Pathways" button

**Expected**:
- ✅ Panel reappears docked on right
- ✅ Previous state preserved (pathway info may be cleared)
- ✅ No errors or crashes

**Result**: [ PENDING ]

---

### 14. Import Another Pathway ⬜

**Action**:
1. Enter "hsa00020" (TCA Cycle)
2. Click "Fetch Pathway"
3. Wait for preview
4. Click "Import to Canvas"

**Expected**:
- ✅ Second pathway imports successfully
- ✅ Appears on canvas (may overlap first pathway)
- ✅ Both pathways visible
- ✅ No errors

**Result**: [ PENDING ]

---

### 15. Error Handling - Invalid Pathway ID ⬜

**Action**:
1. Enter "invalid123"
2. Click "Fetch Pathway"

**Expected**:
- ✅ Error message displayed
- ✅ "Could not fetch pathway" or similar
- ✅ Import button remains disabled
- ✅ Application doesn't crash
- ✅ User can try again

**Result**: [ PENDING ]

---

### 16. Error Handling - Empty Pathway ID ⬜

**Action**: Click "Fetch Pathway" with empty field

**Expected**:
- ✅ Validation message: "Please enter pathway ID"
- ✅ Or fetch button disabled when field empty
- ✅ No crash

**Result**: [ PENDING ]

---

### 17. Canvas Interaction with Imported Objects ⬜

**Test**:
- ✅ Click place → selectable
- ✅ Click transition → selectable
- ✅ Drag object → movable (if enabled)
- ✅ Zoom in/out → objects scale correctly
- ✅ Pan canvas → objects move with canvas

**Result**: [ PENDING ]

---

### 18. File Operations - Save Imported Pathway ⬜

**Action**: 
1. File → Save As (or use File Ops panel)
2. Save as "test_glycolysis.shy"

**Expected**:
- ✅ File saves successfully
- ✅ No errors
- ✅ File exists in expected location

**Result**: [ PENDING ]

---

### 19. File Operations - Load Saved Pathway ⬜

**Action**:
1. File → New (clear canvas)
2. File → Open "test_glycolysis.shy"

**Expected**:
- ✅ Pathway loads from file
- ✅ All objects restored correctly
- ✅ Layout preserved
- ✅ Objects functional

**Result**: [ PENDING ]

---

### 20. Clean Application Exit ⬜

**Action**: Close main window (X button or File → Quit)

**Expected**:
- ✅ Application exits cleanly
- ✅ No segmentation fault
- ✅ No error messages
- ✅ Exit code: 0

**Result**: [ PENDING ]

---

## Test Results Summary

**Total Tests**: 20  
**Passed**: 0  
**Failed**: 0  
**Pending**: 20  

**Overall Status**: 🔄 Testing in progress

---

## Issues Found

### Issue #1
**Description**: [ None yet ]  
**Severity**: [ ]  
**Workaround**: [ ]

---

## Notes

- Test with pathway hsa00010 (Glycolysis) first - well-tested pathway
- Verify mutual exclusivity between Pathways and Analyses panels
- **Critical**: Confirm X button close doesn't cause segfault (fix applied)
- Test both docked and floating states
- Check error handling for invalid inputs

---

## Next Steps After Testing

1. ✅ If all tests pass → Mark todo as complete
2. ⚠️ If issues found → Document and fix
3. 📝 Update documentation with test results
4. 🎯 Proceed to next todo: Metadata preservation

