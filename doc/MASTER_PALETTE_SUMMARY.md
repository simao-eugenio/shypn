# Master Palette Refactoring - Quick Summary

**Date**: October 20, 2025  
**Goal**: Vertical master toolbar on far left with large category buttons  
**Backup**: ✅ legacy/shypn_backup_20251020_131029.tar.gz

---

## 🎯 The Plan in 60 Seconds

### What We're Building

```
┌──┬──────────────────────────────────┐
│📁│ Shypn                    [_][×]  │ ← Clean HeaderBar
├──┼──────────────────────────────────┤
│  │ ┌─────┬──────────┬────────────┐ │
│🗺│ │Left │          │   Right    │ │
│  │ │Dock │ Canvas   │   Dock     │ │
│📊│ └─────┴──────────┴────────────┘ │
│  │                                  │
│🔬│ Status Bar                       │
└──┴──────────────────────────────────┘
 ↑
Master Palette
48px wide, 48px buttons
```

**4 Category Buttons:**
1. 📁 Files - File operations
2. 🗺 Pathways - Pathway import
3. 📊 Analyses - Dynamic analyses
4. 🔬 Topology - Topology analysis (NEW)

---

## 📋 What Gets Created

### New Modules
```
src/shypn/panels/
├── __init__.py
├── master_palette.py      ← Main palette class
└── palette_button.py      ← Button class
```

### New UI Files
```
ui/
├── master_palette.ui       ← Palette UI definition
└── main/main_window.ui     ← MODIFIED (add palette slot)
```

### What Gets Removed
- ❌ HeaderBar toggle buttons (3 buttons)
- ❌ Old toggle logic in shypn.py
- ✅ Cleaner HeaderBar!

---

## 🏗️ Implementation Phases

### Phase 1: Infrastructure (Day 1, 6-8h)
**Create**:
- `MasterPalette` class (manages palette)
- `PaletteButton` class (48x48px buttons)
- UI files
- CSS styling
- Unit tests

### Phase 2: Integration (Day 2, 6-8h)
**Modify**:
- `main_window.ui` (add palette slot)
- `shypn.py` (create palette, add buttons)

**Test**:
- Palette appears
- Buttons visible
- CSS works

### Phase 3: Migration (Day 3, 6-8h)
**Migrate**:
- Files toggle logic
- Pathways toggle logic
- Analyses toggle logic
- Add Topology placeholder

**Implement**:
- Panel float → button sync
- Panel attach → button sync
- Mutual exclusivity

### Phase 4: Cleanup (Day 4, 4-6h)
**Remove**:
- HeaderBar toggle buttons
- Old toggle code
- Orphaned references

**Update**:
- Documentation
- Tests
- Architecture diagrams

---

## 🎨 Design Specs

### Sizing
- Palette Width: **48px**
- Button Size: **48x48px**
- Icon Size: **32x32px**
- Spacing: **6px** between buttons

### Colors (Nord Theme)
```css
Palette Background:  #2e3440  (dark gray)
Border:              #4c566a  (lighter gray)
Button Hover:        rgba(136, 192, 208, 0.1)  (subtle blue)
Button Active:       #5e81ac  (blue)
Icon Default:        #d8dee9  (light gray)
Icon Active:         #eceff4  (white)
```

### Icons (GTK Symbolic)
- Files: `folder-symbolic`
- Pathways: `network-workgroup-symbolic`
- Analyses: `utilities-system-monitor-symbolic`
- Topology: `applications-science-symbolic`

---

## ✅ Success Criteria

**Functional**:
- [ ] Palette at far left
- [ ] 4 category buttons
- [ ] Only one active at a time
- [ ] Panels show/hide on toggle
- [ ] Sync with float/attach
- [ ] No orphaned code

**Quality**:
- [ ] Wayland-safe (no crashes)
- [ ] CSS-styled
- [ ] OOP architecture
- [ ] Fully tested
- [ ] Well documented

**UX**:
- [ ] Intuitive layout
- [ ] Clear visual feedback
- [ ] Touch-friendly (48px)
- [ ] Smooth animations

---

## 🛡️ Safety Features

### Backup
✅ `legacy/shypn_backup_20251020_131029.tar.gz` (6.7 MB)

### Wayland-Safe Practices
✅ Proper widget lifecycle (realize → show → hide → destroy)
✅ CSS for styling (no deprecated modify_* methods)
✅ GTK signals (no direct event manipulation)
✅ Let GTK handle window management

### Testing Strategy
✅ Unit tests (palette, buttons)
✅ Integration tests (palette + panels)
✅ Manual testing (Wayland + X11)
✅ Visual regression testing

---

## ⏱️ Timeline

| Phase | Time | Tasks | Status |
|-------|------|-------|--------|
| 1: Infrastructure | 6-8h | Classes, UI, CSS, tests | 🔴 TODO |
| 2: Integration | 6-8h | Main window, shypn.py | 🔴 TODO |
| 3: Migration | 6-8h | Toggle logic, sync | 🔴 TODO |
| 4: Cleanup | 4-6h | Remove legacy, docs | 🔴 TODO |
| **TOTAL** | **22-30h** | **~4 days** | **0% complete** |

---

## 🚀 Getting Started

### Step 1: Review Plan
Read full plan: `doc/MASTER_PALETTE_REFACTORING_PLAN.md`

### Step 2: Create Infrastructure
```bash
# Create directories
mkdir -p src/shypn/panels
mkdir -p tests/panels

# Create files
touch src/shypn/panels/__init__.py
touch src/shypn/panels/master_palette.py
touch src/shypn/panels/palette_button.py
touch ui/master_palette.ui
touch tests/panels/test_master_palette.py
```

### Step 3: Implement MasterPalette
Copy skeleton from plan → `master_palette.py`

### Step 4: Implement PaletteButton  
Copy skeleton from plan → `palette_button.py`

### Step 5: Create UI
Copy XML from plan → `master_palette.ui`

### Step 6: Write Tests
Copy tests from plan → `test_master_palette.py`

### Step 7: Test
```bash
PYTHONPATH=src:$PYTHONPATH python3 -m pytest tests/panels/ -v
```

---

## 📚 Key Files Reference

### Plan Documents
- **Full Plan**: `doc/MASTER_PALETTE_REFACTORING_PLAN.md` (65 pages)
- **This Summary**: `doc/MASTER_PALETTE_SUMMARY.md` (this file)

### Current Architecture
- **Main Window**: `ui/main/main_window.ui` (HeaderBar with toggles)
- **Main Loader**: `src/shypn.py` (loads everything)
- **Left Panel**: `src/shypn/helpers/left_panel_loader.py`
- **Right Panel**: `src/shypn/helpers/right_panel_loader.py`
- **Pathway Panel**: `src/shypn/helpers/pathway_panel_loader.py`

### Future Files (To Create)
- `src/shypn/panels/master_palette.py`
- `src/shypn/panels/palette_button.py`
- `ui/master_palette.ui`
- `tests/panels/test_master_palette.py`

---

## 💡 Key Insights

### Why This Approach?

**Problem**:
- HeaderBar buttons take valuable space
- Small text buttons not scalable
- Difficult to add more panels (Topology coming)
- Not touch-friendly

**Solution**:
- Vertical palette at far left
- Large icon buttons (48x48px)
- Room for many categories
- Modern IDE pattern (VS Code style)

### Critical Design Decisions

1. **Mutually Exclusive**: Only one panel active at a time
   - Simpler UX
   - Prevents overlap
   - Clearer focus

2. **OOP Classes**: Separate modules for palette and buttons
   - Maintainable
   - Testable
   - Reusable

3. **CSS Styling**: Theme-aware colors
   - Consistent look
   - Wayland-safe
   - Easy to customize

4. **48px Buttons**: Large touch targets
   - Accessibility
   - Modern standard
   - Comfortable use

---

## 🎯 Next Action

**Choose one**:

1. **Start Implementation** → Create infrastructure (Phase 1)
2. **Review Plan First** → Read full plan document
3. **Ask Questions** → Clarify any concerns
4. **Test Current State** → Run app before changes

**Recommended**: Start with Phase 1 (Infrastructure)

---

**Status**: 🟢 Ready - Plan Complete, Backup Done  
**Risk**: 🟡 Medium - Well-planned refactoring  
**Time**: ~4 days (22-30 hours)  
**Priority**: High - Improves scalability for Topology panel

**Last Updated**: October 20, 2025  
**Version**: 1.0 (Summary)
