# Phase 0 Validation Tests - Instructions

**CRITICAL**: These tests MUST pass before implementing Master Palette in production.

---

## Test 1: GtkStack Principle Validation

### Purpose
Validate that GtkStack works with Wayland WITHOUT Error 71.

### File
`dev/test_gtkstack_principle.py`

### What It Tests
1. ✅ GtkStack with 4 heavy panels (FileChoosers, dialogs, ScrolledWindows)
2. ✅ Rapid switching between stack children (100 cycles)
3. ✅ `set_no_show_all()` with stack children
4. ✅ Master Palette button control of stack visibility
5. ✅ Exclusive panel visibility (only 1 panel at a time)
6. ✅ Panels start hidden on startup

### How to Run

```bash
cd /home/simao/projetos/shypn
./dev/test_gtkstack_principle.py
```

### Interactive Testing
1. Click Master Palette buttons (📁 🗺️ 📊 🔷) to switch panels
2. Test dialogs and FileChoosers in each panel
3. Click "Test Panel Float/Detach" to validate detach/re-attach cycle
4. Watch for Wayland Error 71 in terminal output

### Automated Testing
1. Click "Run Automated Test" button
2. Watch 100 rapid switches between panels
3. Click "Test Panel Float/Detach" button to test detach/re-attach
4. Application auto-exits after 120s = SUCCESS ✅

### Success Criteria
- ✅ NO Wayland Error 71 during any operation
- ✅ Smooth panel switching
- ✅ Panels start hidden
- ✅ Only 1 panel visible at a time
- ✅ Auto-exit after 120s (no crash)

### Failure Scenarios
- ❌ Error 71 appears → **STOP!** GtkStack not safe, use alternative
- ❌ Panels don't hide correctly → Debug `set_no_show_all()` logic
- ❌ Application crashes → Investigate stack child management

---

## Test 2: Error 71 Diagnosis

### Purpose
Identify potential Error 71 root causes in panel code.

### File
`dev/test_error71_diagnosis.py`

### What It Checks

**UI Files** (`ui/panels/*.ui`):
1. ❌ Malformed XML (invalid structure)
2. ❌ Undefined object references
3. ❌ Duplicate IDs
4. ⚠️ Missing required properties
5. ⚠️ Deprecated widgets (GtkHBox, GtkVBox, etc.)
6. ⚠️ Deep widget hierarchies (>10 levels)
7. ✅ Gtk.Builder load test

**Loader Files** (`src/shypn/helpers/*_panel_loader.py`):
1. ⚠️ Dynamic widget creation (outside `__init__`)
2. ⚠️ Fallback mechanisms (creating widgets on error)
3. ⚠️ Widget destruction patterns
4. ⚠️ Dead code (empty except blocks)
5. ⚠️ Improper lifecycle (widget creation in hide/show methods)

### How to Run

```bash
cd /home/simao/projetos/shypn
./dev/test_error71_diagnosis.py
```

### Output
```
============================
PHASE 1: UI FILE ANALYSIS
============================
Analyzing: left_panel.ui
  ✅ Valid XML structure
  ✅ All object references valid
  ✅ No duplicate IDs
  ...

============================
PHASE 2: PANEL LOADER ANALYSIS
============================
Analyzing: left_panel_loader.py
  ✅ No dynamic widget creation outside __init__
  ⚠️ Widget destruction found (12 instances)
  ...

============================
FINAL SUMMARY
============================
  Total critical issues: 0
  Total warnings: 8

🟡 RECOMMENDATION: REVIEW WARNINGS
```

### Interpretation

**🟢 GREEN (0 issues, 0 warnings)**:
- Panels are clean
- Error 71 likely NOT from panel code
- Proceed with GtkStack implementation

**🟡 YELLOW (0 issues, warnings present)**:
- Minor code quality issues
- Review warnings, consider cleanup
- Safe to proceed if Test 1 passes

**🔴 RED (critical issues found)**:
- Panels need refactoring
- **MUST FIX** before production
- See specific issues in analysis output

---

## Decision Tree

```
Run Test 1 (GtkStack Principle)
│
├─ ✅ PASS (no Error 71) ──────────┐
│                                  │
└─ ❌ FAIL (Error 71 detected)     │
   │                               │
   └─ Alternative: Manual show/hide│
      (no GtkStack)                │
                                   │
Run Test 2 (Error 71 Diagnosis)    │
│                                  │
├─ 🟢 CLEAN ──────────────────────┤
│  (no issues)                     │
│                                  │
├─ 🟡 WARNINGS ───────────────────┤
│  (review recommended)            │
│                                  │
└─ 🔴 CRITICAL ISSUES              │
   (refactor required)             │
                                   │
                                   ▼
                          ┌─────────────────┐
                          │ GO/NO-GO DECISION│
                          └─────────────────┘
                                   │
                          ┌────────┴────────┐
                          │                 │
                     ✅ GO            ❌ NO-GO
                          │                 │
                  Proceed with      Fix issues first
                  Master Palette    or use alternative
```

---

## GO Criteria (Proceed with Master Palette)

✅ Test 1 PASSES (no Error 71 with GtkStack)  
✅ Test 2 shows 🟢 or 🟡 (no critical issues)  
✅ User reviews and approves plan

---

## NO-GO Criteria (Alternative approach)

❌ Test 1 FAILS (Error 71 with GtkStack)  
  → **Alternative**: Manual panel show/hide without GtkStack  
  → Use simple GtkBox, manually remove/add panels on toggle

❌ Test 2 shows 🔴 (critical issues)  
  → **Required**: Panel refactoring before production  
  → Fix UI files or loader code

---

## Alternative Approach (if GtkStack fails)

**Manual Panel Management** (like skeleton):

```python
# Instead of GtkStack, use simple GtkBox
self.left_dock_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
self.left_dock_box.set_visible(False)

def _on_panel_toggled(self, palette, panel_name, active):
    """Handle Master Palette button toggle."""
    if active:
        # Remove all panels from box
        for child in self.left_dock_box.get_children():
            self.left_dock_box.remove(child)
        
        # Add selected panel
        panel = self.panels[panel_name]
        self.left_dock_box.pack_start(panel.content, True, True, 0)
        
        # Show box and panel
        self.left_dock_box.set_visible(True)
        panel.show()
    else:
        # Hide box
        self.left_dock_box.set_visible(False)
        panel.hide()
```

**Pros**:
- No GtkStack (avoids potential Error 71)
- Similar to validated skeleton architecture
- Simple widget management

**Cons**:
- Manual widget add/remove
- No built-in transitions
- Slightly more code

---

## Next Steps After Phase 0

### If PASS ✅
1. Review validation results with user
2. User approves GO decision
3. Proceed with Phase 1 (Remove HeaderBar handlers)

### If FAIL ❌
1. Document failure reasons
2. Choose alternative approach
3. Update implementation plan
4. Re-validate alternative approach

---

## Validation Checklist

- [ ] Test 1 executed (GtkStack principle)
- [ ] Test 1 result recorded (PASS/FAIL)
- [ ] Test 2 executed (Error 71 diagnosis)
- [ ] Test 2 result recorded (🟢/🟡/🔴)
- [ ] Decision documented (GO/NO-GO)
- [ ] User approval obtained
- [ ] Phase 1 started OR alternative approach selected

---

## Questions to Answer

1. **Does GtkStack cause Error 71?**  
   → Run Test 1, watch for Wayland errors

2. **Are panel UI files malformed?**  
   → Run Test 2, check for XML errors

3. **Is panel loader code problematic?**  
   → Run Test 2, check for dead code/fallbacks

4. **Should we use GtkStack or manual management?**  
   → Based on Test 1 results

5. **Do panels need refactoring?**  
   → Based on Test 2 results

---

## Timeline

**Phase 0 Duration**: 4 hours
- Test 1 execution: 30 min (interactive + automated)
- Test 2 execution: 30 min (automated analysis)
- Results review: 1 hour
- Decision documentation: 30 min
- Alternative planning (if needed): 1.5 hours

**Critical Path**: Must complete before any production changes

---

## Expected Outcomes

### Most Likely Scenario (70%)
- ✅ Test 1 PASSES (GtkStack works)
- 🟡 Test 2 shows warnings (minor code quality issues)
- → **GO** with GtkStack implementation
- → Review warnings, clean up opportunistically

### Alternative Scenario (20%)
- ❌ Test 1 FAILS (GtkStack causes Error 71)
- 🟢/🟡 Test 2 (panels are clean)
- → **NO-GO** for GtkStack
- → Use manual panel management alternative

### Worst Case Scenario (10%)
- ❌ Test 1 FAILS (GtkStack causes Error 71)
- 🔴 Test 2 shows critical issues
- → **NO-GO** for current approach
- → Requires panel refactoring + alternative architecture
- → Timeline extends by 1-2 days

---

## Support

If tests fail or results are unclear:
1. Document exact error messages
2. Capture terminal output
3. Share Test 1 switch count (if partial success)
4. Share Test 2 specific issues list
5. Discuss alternative approaches

---

**Remember**: These tests protect us from implementing a broken architecture. Better to find issues NOW than after production deployment.
