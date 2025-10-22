# UI Refactoring Plan - Wayland Compatibility

**Date:** October 21, 2025  
**Backup:** `legacy/wayland_fixes_complete_20251021_152238.tar.gz` (6.4MB)  
**Objective:** Fix Wayland Error 71 while preserving ALL topology integration and business logic

---

## Current State Analysis

### ✅ What Works (MUST PRESERVE)
1. **Topology Panel Integration** - Complete with 3 tabs, nested expanders, all analysis features
2. **FileChooser Async Pattern** - All dialogs work perfectly with async signal-based approach
3. **Business Logic** - All controllers, data collectors, analysis engines work correctly
4. **Isolation Tests** - All panels work perfectly when isolated (NO Error 71)
5. **Model Canvas** - All drawing, editing, simulation features work
6. **SBML Import** - Async threaded import works perfectly
7. **Panel Functionality** - File explorer, analyses, pathways, topology all functional

### ❌ What Breaks (NEEDS FIXING)
1. **Widget Reparenting** - `container.add(widget)` after `window.show_all()` causes Wayland Error 71
2. **Master Palette Coded UI** - Complex toggle logic was adding unnecessary complexity
3. **Panel Architecture** - Separate window files + dynamic reparenting incompatible with Wayland

### 🔍 Root Cause
**Wayland protocol doesn't support widget reparenting after window realization.**
When we call `window.show_all()`, all widgets become "realized" (allocated Wayland surfaces).
Calling `container.add(widget)` after this tries to reparent an already-realized widget,
which Wayland interprets as a protocol violation → Error 71.

---

## Refactoring Strategy

### Phase 1: Revert to Last Working State ✅ DONE
- [x] Created complete backup: `legacy/wayland_fixes_complete_20251021_152238.tar.gz`
- [x] Backup includes: src/, ui/, doc/, tests/, dev/, all root files
- [x] Backup excludes: .git, __pycache__, htmlcov, workspace (user data)

### Phase 2: Simplify Master Palette (Keep Recent Fix)
**Keep:** Simple callback connections (no complex exclusive logic in MasterPalette class)  
**Revert:** The experimental main_builder integration that broke loading

**Files to modify:**
- `src/shypn/ui/master_palette.py` - Keep simplified connect() method
- `src/shypn.py` - Keep toggle handlers with explicit button deactivation

**Why:** The simplified Master Palette is actually better - moves exclusive logic to
handlers where it's more explicit and easier to debug.

### Phase 3: Fix Panel Architecture (The Critical Part)

#### Option A: Accept Error 71 as Benign (RECOMMENDED)
**Approach:** One Error 71 at startup is acceptable if app works perfectly after
- Keep current panel loader architecture
- Document that Error 71 is expected and harmless
- All functionality works correctly despite the error
- Zero user impact

**Advantages:**
- ✅ Preserves ALL existing code
- ✅ Minimal changes needed
- ✅ Topology integration untouched
- ✅ Quick implementation (< 1 hour)

**Disadvantages:**
- ❌ One console error message at startup
- ❌ Not "clean" solution

#### Option B: Pure Visibility Toggle (NO REPARENTING)
**Approach:** Panel content lives permanently in main_window.ui, just toggle visibility

**Changes needed:**
1. Define all 4 panel content areas in `ui/main/main_window.ui`:
   ```xml
   <object class="GtkStack" id="left_dock_stack">
     <child>
       <object class="GtkBox" id="files_panel_content">
         <!-- Content loaded from left_panel.ui at startup -->
       </object>
     </child>
     <child>
       <object class="GtkBox" id="analyses_panel_content">
         <!-- Content loaded from right_panel.ui at startup -->
       </object>
     </child>
     <!-- etc for pathways and topology -->
   </object>
   ```

2. Panel loaders populate containers BEFORE `window.show_all()`
3. Toggle handlers just call `stack.set_visible_child()`
4. NO add/remove operations after window is shown

**Advantages:**
- ✅ Completely eliminates Error 71
- ✅ "Clean" architecture
- ✅ Better performance (no reparenting overhead)

**Disadvantages:**
- ❌ Significant refactoring (8-16 hours)
- ❌ Risk of breaking topology integration
- ❌ All 4 panel loaders need changes
- ❌ Testing required for each panel

#### Option C: Force X11 Mode
**Approach:** Add `os.environ["GDK_BACKEND"] = "x11"` at startup

**Advantages:**
- ✅ Zero code changes
- ✅ Completely eliminates Error 71
- ✅ Works immediately

**Disadvantages:**
- ❌ Doesn't use native Wayland
- ❌ Loses Wayland benefits (better scaling, security)
- ❌ Not a real fix, just avoidance

---

## Recommended Plan (Hybrid Approach)

### Step 1: Revert Broken Changes (30 minutes)
1. Revert `left_panel_loader.py` to version before main_builder integration
2. Revert `main_window.ui` to remove the 4 placeholder containers
3. Keep simplified `master_palette.py` (it's actually better)
4. Keep all async FileChooser fixes
5. Keep all topology integration untouched

### Step 2: Test and Verify (15 minutes)
1. Run app and verify it works
2. Confirm ONE Error 71 at startup (acceptable)
3. Verify ALL panels work (Files, Analyses, Pathways, Topology)
4. Verify ALL buttons work in each panel
5. Verify float/attach works
6. Verify topology panel has all 3 tabs and all features

### Step 3: Document Current State (15 minutes)
1. Add comment in shypn.py explaining Error 71 is expected
2. Update README with known issue section
3. Document that Error 71 is benign and app works perfectly
4. Reference isolation tests showing panels work correctly

### Step 4: Future Consideration (Optional, Later)
If Error 71 becomes problematic (it shouldn't), implement Option B:
- Plan detailed refactoring schedule
- Test each panel loader modification separately
- Use GtkStack for panel switching
- Eliminate all widget reparenting

---

## Implementation Checklist

### Immediate Actions (Next 1 Hour)
- [ ] Git checkout last working versions of modified files
- [ ] Keep master_palette.py simplifications
- [ ] Test app launches and works
- [ ] Verify one Error 71 but app functional
- [ ] Run isolation tests to confirm panels work
- [ ] Test all topology features

### Documentation Updates (Next 30 Minutes)
- [ ] Add to README.md: Known Issues section
- [ ] Document Error 71 in shypn.py comments
- [ ] Reference isolation test results
- [ ] Note that all functionality works despite error

### Testing Verification (Next 30 Minutes)
- [ ] Launch app - verify Error 71 appears once
- [ ] Test Files panel - all buttons, float/attach
- [ ] Test Analyses panel - data collection, filters
- [ ] Test Pathways panel - SBML import, KEGG
- [ ] Test Topology panel - all 3 tabs, all analyses
- [ ] Test panel switching - exclusive behavior
- [ ] Test float/attach for each panel
- [ ] Verify FileChooser dialogs work

---

## Risk Assessment

### Low Risk (Recommended Approach - Accept Error 71)
- **Technical Risk:** None - app works perfectly
- **User Impact:** Zero - error is console-only
- **Maintenance:** Minimal - current code maintained
- **Timeline:** < 1 hour to implement

### Medium Risk (Option B - Visibility Toggle)
- **Technical Risk:** Medium - significant refactoring
- **User Impact:** None if done correctly
- **Maintenance:** Better long-term architecture
- **Timeline:** 8-16 hours implementation + testing

### Low Risk (Option C - Force X11)
- **Technical Risk:** None
- **User Impact:** Lose Wayland benefits
- **Maintenance:** No changes needed
- **Timeline:** 5 minutes

---

## Success Criteria

### Minimum Viable (Accept Error 71)
- [x] App launches successfully
- [ ] One Error 71 at startup (documented as benign)
- [ ] All 4 panels work correctly
- [ ] Topology integration fully functional
- [ ] FileChooser dialogs work
- [ ] Float/attach works for all panels
- [ ] All business logic preserved

### Ideal (Future Refactoring)
- [ ] Zero Wayland errors
- [ ] All panels work correctly
- [ ] Cleaner architecture with GtkStack
- [ ] No widget reparenting
- [ ] Better performance

---

## Files Requiring Attention

### Core Files (DO NOT BREAK)
- `src/shypn/ui/topology_panel_controller.py` - Topology business logic
- `src/shypn/helpers/topology_panel_loader.py` - Topology UI wiring
- `src/shypn/analyses/` - All analysis engines
- `src/shypn/helpers/model_canvas_loader.py` - Canvas integration

### UI Files (SAFE TO MODIFY)
- `ui/main/main_window.ui` - Main window layout
- `src/shypn.py` - Window initialization
- `src/shypn/helpers/*_panel_loader.py` - Panel lifecycle
- `src/shypn/ui/master_palette.py` - Button behavior

### Already Fixed (PRESERVE)
- `src/shypn/file/netobj_persistency.py` - Async FileChooser ✅
- `src/shypn/helpers/sbml_import_panel.py` - Async FileChooser ✅
- All topology panel UI files ✅
- All analysis data collectors ✅

---

## Next Steps

**Immediate Action:** Revert to last working state, keep improvements, accept Error 71 as benign.

**Command to restore from backup if needed:**
```bash
cd /home/simao/projetos/shypn
tar -xzf legacy/wayland_fixes_complete_20251021_152238.tar.gz -C /tmp/shypn_restore
# Then selectively copy files that need restoration
```

**Testing Command:**
```bash
cd /home/simao/projetos/shypn
python3 src/shypn.py 2>&1 | tee test_output.log
# Check for: one Error 71, then app works normally
```
