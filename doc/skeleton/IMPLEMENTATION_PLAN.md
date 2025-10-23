# Skeleton to Production Implementation Plan

**Date**: October 22, 2025  
**Objective**: Apply validated skeleton principles to Shypn production code

---

## What We Validated in Skeleton

✅ **Main Window = Hanger** (empty container)  
✅ **Master Palette = Native widget** (48px toolbar)  
✅ **Panels = Independent windows** (can be hanged/hidden)  
✅ **Show/Hide with `set_no_show_all()`** (prevents accidental reveal)  
✅ **No Wayland Error 71** (all operations stable)

---

## Current Shypn Architecture

### Existing Panel System

```python
# Location: src/shypn.py
self.left_panel = create_left_panel()      # Files panel
self.right_panel = create_right_panel()    # Analyses panel  
self.pathway_panel = create_pathway_panel()  # Pathways panel
self.topology_panel = create_topology_panel()  # Topology panel
```

**Current Behavior**:
- Panels are independent GtkWindow instances ✅ (already correct!)
- Panels have `attach_to()` and `detach_from()` methods ✅ (working!)
- HeaderBar toggle buttons control panel visibility
- Panels can float as independent windows ✅ (working!)

### What's Missing

❌ Master Palette widget (no central toolbar)  
❌ Panel `hide()` and `show()` methods (only attach/detach)  
❌ Panels start visible (should start hidden)  
❌ `set_no_show_all()` logic (panels appear on startup)

---

## Implementation Plan

### Phase 1: Create Master Palette Widget (2 hours)

**Goal**: Add 48px vertical toolbar on left side of main window

**Tasks**:
1. Create `src/shypn/ui/master_palette.py`
   ```python
   class MasterPalette(GObject.GObject):
       """Master Palette - vertical toolbar for panel control."""
       
       __gsignals__ = {
           'files': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
           'pathways': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
           'analyses': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
           'topology': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
       }
       
       def __init__(self):
           super().__init__()
           self.widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
           self.buttons = {}
           self._create_buttons()
       
       def _create_buttons(self):
           """Create toggle buttons for each panel."""
           for name in ['files', 'pathways', 'analyses', 'topology']:
               btn = Gtk.ToggleButton()
               btn.set_size_request(48, 48)
               # Load icon from ui/images/
               self.buttons[name] = btn
               self.widget.pack_start(btn, False, False, 0)
       
       def get_widget(self):
           return self.widget
   ```

2. Modify `ui/main/main_window.ui`
   - Add 48px box on left for Master Palette
   - Keep existing `left_dock_stack` for panel content

3. Wire Master Palette in `src/shypn.py`
   ```python
   from shypn.ui.master_palette import MasterPalette
   
   self.master_palette = MasterPalette()
   # Insert into main_window's left slot
   ```

**Validation**: Master Palette appears as vertical toolbar with 4 buttons

---

### Phase 2: Add Panel Show/Hide Methods (1 hour)

**Goal**: Extend existing panel classes with hide/show capability

**Tasks**:

1. Update `src/shypn/helpers/left_panel_loader.py` (Files panel)
   ```python
   class LeftPanel:
       def hide(self):
           """Hide panel content (keep attached)."""
           if hasattr(self, 'content') and self.content:
               self.content.set_no_show_all(True)
               self.content.hide()
       
       def show(self):
           """Show panel content (reveal)."""
           if hasattr(self, 'content') and self.content:
               self.content.set_no_show_all(False)
               self.content.show_all()
   ```

2. Update `src/shypn/helpers/right_panel_loader.py` (Analyses panel)
   - Add same `hide()` and `show()` methods

3. Update `src/shypn/helpers/pathway_panel_loader.py` (Pathways panel)
   - Add same `hide()` and `show()` methods

4. Update `src/shypn/helpers/topology_panel_loader.py` (Topology panel)
   - Add same `hide()` and `show()` methods

**Validation**: Panels can be hidden/shown without detaching

---

### Phase 3: Wire Master Palette to Panels (2 hours)

**Goal**: Master Palette buttons control panel visibility

**Tasks**:

1. Connect signals in `src/shypn.py`
   ```python
   def setup_master_palette(self):
       """Wire Master Palette buttons to panel show/hide."""
       
       # Files button → Files panel (left)
       self.master_palette.connect('files', self._on_files_toggled)
       
       # Pathways button → Pathways panel
       self.master_palette.connect('pathways', self._on_pathways_toggled)
       
       # Analyses button → Analyses panel (right)
       self.master_palette.connect('analyses', self._on_analyses_toggled)
       
       # Topology button → Topology panel
       self.master_palette.connect('topology', self._on_topology_toggled)
   
   def _on_files_toggled(self, palette, active):
       """Handle Files button toggle."""
       if active:
           # Ensure panel is attached
           if not hasattr(self.left_panel, 'is_attached') or not self.left_panel.is_attached:
               self.left_panel.attach_to(self.left_dock_stack, parent_window=self.window)
           # Show panel
           self.left_panel.show()
       else:
           # Hide panel (keep attached)
           self.left_panel.hide()
   
   # Similar handlers for pathways, analyses, topology
   ```

2. Initialize panels as hidden
   ```python
   # In on_activate() after creating panels:
   
   # Attach all panels but hide them
   self.left_panel.attach_to(self.left_dock_stack, parent_window=self.window)
   self.left_panel.content.set_no_show_all(True)
   self.left_panel.hide()
   
   self.right_panel.attach_to(self.right_dock_stack, parent_window=self.window)
   self.right_panel.content.set_no_show_all(True)
   self.right_panel.hide()
   
   # Similar for pathways and topology
   ```

**Validation**: Clicking Master Palette buttons shows/hides panels

---

### Phase 4: Handle HeaderBar Buttons (1 hour)

**Goal**: Keep existing HeaderBar toggle buttons in sync with Master Palette

**Decision Point**:
- **Option A**: Remove HeaderBar toggle buttons (Master Palette is primary control)
- **Option B**: Keep HeaderBar buttons, sync with Master Palette state

**Recommended**: Option A (cleaner, follows skeleton design)

**If Option B** (backward compatibility):
```python
# Wire HeaderBar buttons to Master Palette
self.header_files_button.connect('toggled', 
    lambda btn: self.master_palette.buttons['files'].set_active(btn.get_active()))

# Wire Master Palette back to HeaderBar
def _on_files_toggled(self, palette, active):
    # Update HeaderBar button state
    self.header_files_button.set_active(active)
    # ... rest of handler
```

**Validation**: Both HeaderBar and Master Palette buttons stay in sync (if keeping both)

---

### Phase 5: Panel Positioning (1 hour)

**Goal**: Panels appear in correct slots

**Current Layout**:
```
┌─────────────────────────────────────────┐
│ HeaderBar                               │
├────┬──────────────┬────────────┬────────┤
│ MP │ left_dock    │   Canvas   │ right  │
│    │  (Files)     │            │ (Analy)│
│ 📁 │              │            │        │
│ 🗺️ │              │            │        │
│ 📊 │              │            │        │
│ 🔷 │              │            │        │
└────┴──────────────┴────────────┴────────┘
```

**Panel Assignments**:
- Files panel → `left_dock_stack` (already correct)
- Analyses panel → `right_dock_stack` (already correct)
- Pathways panel → ??? (currently separate window)
- Topology panel → ??? (currently separate window)

**Options for Pathways/Topology**:
1. Add them to left_dock_stack (stack multiple panels)
2. Add them to right_dock_stack (stack multiple panels)
3. Keep as floating only (Master Palette just shows/hides floating window)

**Recommended**: Option 1 - Add to left_dock_stack with GtkStack

```python
# Modify left_dock_stack to be a GtkStack
# Panels: Files (default), Pathways, Topology
# Master Palette button switches active stack child
```

**Validation**: All 4 panels can be shown via Master Palette

---

### Phase 6: State Persistence (1 hour)

**Goal**: Remember which panels were visible on shutdown

**Tasks**:

1. Save panel state on shutdown
   ```python
   # In application shutdown
   settings = Gio.Settings.new('org.shypn.app')
   settings.set_boolean('panel-files-visible', 
                       self.master_palette.buttons['files'].get_active())
   settings.set_boolean('panel-pathways-visible', 
                       self.master_palette.buttons['pathways'].get_active())
   # ... etc
   ```

2. Restore panel state on startup
   ```python
   # In on_activate() after setup
   settings = Gio.Settings.new('org.shypn.app')
   if settings.get_boolean('panel-files-visible'):
       self.master_palette.buttons['files'].set_active(True)
   # ... etc
   ```

**Validation**: Panel visibility persists across restarts

---

### Phase 7: Testing & Polish (2 hours)

**Testing Checklist**:
- [ ] All Master Palette buttons show/hide panels
- [ ] Panels start hidden on first launch
- [ ] Panel state persists across restarts
- [ ] No Wayland Error 71 during rapid toggling
- [ ] Dialogs work correctly from panels
- [ ] File operations work (Open/Save)
- [ ] Panel content is preserved when hidden
- [ ] HeaderBar buttons sync with Master Palette (if keeping)

**Polish**:
- Add keyboard shortcuts (F1=Files, F2=Pathways, etc.)
- Add tooltips to Master Palette buttons
- Add smooth transitions (fade in/out)
- Add visual feedback (button highlights)

**Validation**: Full smoke test of all features

---

## Risk Assessment

### Low Risk (Already Working)
✅ Panel attach/detach mechanism (validated in skeleton)  
✅ Independent panel windows (already implemented)  
✅ Wayland compatibility (skeleton tests pass)

### Medium Risk (Needs Testing)
⚠️ Multiple panels in same stack (Files + Pathways in left_dock)  
⚠️ State synchronization (HeaderBar ↔ Master Palette)  
⚠️ Panel content preservation during hide/show

### High Risk (Requires Careful Testing)
⚠️ Migration from HeaderBar-only to Master Palette  
⚠️ Backward compatibility with existing workflows  
⚠️ State persistence (new settings schema)

---

## Rollout Strategy

### Phase 1: Feature Flag (Week 1)
```python
USE_MASTER_PALETTE = os.getenv('SHYPN_MASTER_PALETTE', 'false') == 'true'

if USE_MASTER_PALETTE:
    # New Master Palette code path
else:
    # Existing HeaderBar-only code path
```

**Testing**: Internal testing with master palette enabled

### Phase 2: Beta (Week 2)
- Master Palette enabled by default
- HeaderBar buttons still available (both work)
- User feedback collection

### Phase 3: Production (Week 3)
- Master Palette as primary control
- Optional: Remove HeaderBar toggle buttons
- Full documentation update

---

## Timeline

| Phase | Task | Time | Status |
|-------|------|------|--------|
| 1 | Create Master Palette Widget | 2h | ⏳ Not Started |
| 2 | Add Panel Show/Hide Methods | 1h | ⏳ Not Started |
| 3 | Wire Master Palette to Panels | 2h | ⏳ Not Started |
| 4 | Handle HeaderBar Buttons | 1h | ⏳ Not Started |
| 5 | Panel Positioning | 1h | ⏳ Not Started |
| 6 | State Persistence | 1h | ⏳ Not Started |
| 7 | Testing & Polish | 2h | ⏳ Not Started |
| **TOTAL** | | **10h** | |

**Estimated Completion**: 2 working days

---

## Success Criteria

✅ Master Palette appears as 48px vertical toolbar  
✅ All 4 panel buttons work (Files, Pathways, Analyses, Topology)  
✅ Panels start hidden on application startup  
✅ Clicking button shows panel (reveals to the right)  
✅ Clicking button again hides panel  
✅ No Wayland Error 71 during any operation  
✅ Panel state persists across restarts  
✅ All existing features continue to work  

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Create feature branch**: `feature/master-palette`
3. **Start Phase 1**: Create Master Palette widget
4. **Test incrementally**: After each phase
5. **Document as you go**: Update user documentation

---

## Files to Modify

```
src/shypn.py                           # Main application logic
ui/main/main_window.ui                 # Add Master Palette slot
src/shypn/ui/master_palette.py        # NEW - Master Palette widget
src/shypn/helpers/left_panel_loader.py    # Add hide/show methods
src/shypn/helpers/right_panel_loader.py   # Add hide/show methods
src/shypn/helpers/pathway_panel_loader.py # Add hide/show methods
src/shypn/helpers/topology_panel_loader.py # Add hide/show methods
```

---

## Reference

**Skeleton Test**: `dev/test_architecture_principle.py`  
**Documentation**: `doc/skeleton/`  
**Validated Principles**: See `doc/skeleton/README.md`
