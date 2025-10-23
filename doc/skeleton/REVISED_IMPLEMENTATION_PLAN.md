# REVISED Implementation Plan - Addressing Critical Concerns

**Date**: October 22, 2025  
**Status**: REVISED based on user feedback

---

## Critical User Concerns Addressed

### 1. ❌ Remove ALL HeaderBar Handlers (Phase 4)
**User Request**: "remove all Handlers from headerbar"

**Action**: Complete removal of HeaderBar toggle buttons
- Remove ALL signal handlers from src/shypn.py
- Remove ALL toggle button logic
- Keep HeaderBar ONLY for window title and window controls (minimize/maximize/close)
- Master Palette becomes the ONLY control mechanism

**Risk**: NONE - This simplifies the code significantly

---

### 2. ✅ All Panels Dock to LEFT (Phase 5)
**User Request**: "all panels dock int left, no panels to the right"

**New Layout**:
```
┌─────────────────────────────────────────┐
│ HeaderBar (title + window controls)    │
├────┬────────────────────────────────────┤
│ MP │ LEFT DOCK AREA  │   Canvas         │
│    │ (ALL 4 PANELS)  │                  │
│ 📁 │  - Files        │                  │
│ 🗺️ │  - Pathways     │                  │
│ 📊 │  - Analyses     │                  │
│ 🔷 │  - Topology     │                  │
│    │                 │                  │
└────┴─────────────────┴──────────────────┘
```

**Architecture**:
- Master Palette (MP): 48px vertical toolbar on far left
- Left Dock Area: GtkStack containing all 4 panels (switch between them)
- Canvas: Main drawing area (no right panel!)
- NO right_dock_area

**Implementation**:
- Convert `left_dock_stack` to GtkStack
- All panels pack into the same stack
- Master Palette buttons switch active stack child
- Remove `right_dock_stack` entirely

---

### 3. ⚠️ GtkStack NOT TESTED in Skeleton - Test FIRST
**User Request**: "WE have not tryed GTKStack in skeleton, be carefull, perhaps we must do first"

**CRITICAL**: GtkStack might cause Wayland Error 71!

**Action Required BEFORE Production**:
1. Create `dev/test_gtkstack_principle.py` 
2. Test GtkStack with multiple heavy panels
3. Validate NO Error 71 when:
   - Switching between stack children rapidly
   - Hiding/showing stack
   - Panels contain complex widgets (FileChoosers, dialogs, ScrolledWindows)
4. Test `set_no_show_all()` with GtkStack children
5. Test panel show/hide with stack switching

**BLOCKER**: Do NOT proceed with production until GtkStack validated

---

### 4. ⚠️ Error 71 Root Cause Hypothesis
**User Request**: "My suspicius on erroe 71 is malformed UI files, dead code, fallbacks, widgets creatio/desctrotion on contents panel"

**Hypothesis**: Error 71 caused by:
- ❌ Malformed UI files (invalid XML, undefined widgets)
- ❌ Dead code (unused widget creation/destruction)
- ❌ Fallback mechanisms (creating widgets when UI load fails)
- ❌ Dynamic widget creation/destruction in panel content
- ❌ Improper widget lifecycle (create → destroy → recreate cycles)

**Investigation Plan**:
```python
# dev/test_error71_diagnosis.py
# Test each hypothesis individually:

# TEST 1: Load UI files without creating widgets
# TEST 2: Create panels WITHOUT loading UI (pure Python construction)
# TEST 3: Test panels WITH dead code removal
# TEST 4: Test panels WITHOUT fallback mechanisms
# TEST 5: Test panels WITHOUT dynamic widget creation
```

**Risk**: If hypothesis is correct, panels need COMPLETE refactoring

---

### 5. ⚠️ Panel Refactoring May Be Required
**User Request**: "if it is the case then wem must refactor the panels entirely"

**Refactoring Scope** (if Error 71 is confirmed from panels):

#### Option A: Minimal Refactor (UI files are clean)
- Remove dead code from panel loaders
- Remove fallback mechanisms
- Remove dynamic widget creation/destruction
- Simplify panel lifecycle

#### Option B: Complete Refactor (UI files are malformed)
- Rewrite ALL UI files from scratch
- Pure declarative XML (no dynamic creation)
- All widgets defined statically
- No fallback logic
- Clean separation: UI (XML) ↔ Logic (Python)

**Decision Tree**:
```
Is GtkStack causing Error 71?
├─ YES → Find alternative to GtkStack
│         (e.g., manual show/hide without stack)
│
└─ NO → Are UI files malformed?
        ├─ YES → Option B (Complete Refactor)
        └─ NO → Are panels creating/destroying widgets?
                ├─ YES → Option A (Minimal Refactor)
                └─ NO → Root cause is elsewhere
```

---

## REVISED Implementation Phases

### Phase 0: VALIDATION (DO THIS FIRST!) - 4 hours

**BLOCKER**: Must complete BEFORE any production changes

#### Test 1: GtkStack Principle (2 hours)
**File**: `dev/test_gtkstack_principle.py`

**Test Scenarios**:
1. Create GtkStack with 4 dummy panels
2. Rapidly switch between stack children (100 cycles)
3. Hide/show stack while switching
4. Stack children with heavy widgets (FileChoosers, dialogs, ScrolledWindows)
5. Stack children with `set_no_show_all(True)`
6. Master Palette buttons switching stack children

**Success Criteria**:
- ✅ NO Error 71 in any scenario
- ✅ Smooth switching between panels
- ✅ `set_no_show_all()` works with stack children
- ✅ Hidden panels don't auto-reveal on stack show

**Failure Scenario**:
- ❌ Error 71 appears → STOP! Find alternative to GtkStack
- Alternative: Manual panel show/hide without GtkStack (like skeleton)

#### Test 2: Error 71 Diagnosis (2 hours)
**File**: `dev/test_error71_diagnosis.py`

**Test Scenarios**:
1. Load each panel UI file individually
2. Inspect for malformed XML
3. Check for undefined widget references
4. Identify dead code in panel loaders
5. Identify fallback widget creation
6. Identify dynamic widget creation/destruction

**Deliverable**: Report listing all issues found in each panel

**Decision Point**:
- If issues found → Refactor panels (Option A or B)
- If no issues → Error 71 is NOT from panels

---

### Phase 1: Remove HeaderBar Handlers - 30 minutes

**Goal**: Clean removal of ALL HeaderBar toggle logic

**Tasks**:

1. Remove signal handlers from `src/shypn.py`:
   ```python
   # DELETE ALL:
   # - headerbar_files_toggle signal connections
   # - headerbar_pathways_toggle signal connections
   # - headerbar_analyses_toggle signal connections
   # - headerbar_topology_toggle signal connections
   # - All on_headerbar_*_toggled() callback functions
   ```

2. Modify `ui/main/main_window.ui`:
   ```xml
   <!-- REMOVE ALL toggle buttons: -->
   <!-- DELETE: headerbar_files_toggle -->
   <!-- DELETE: headerbar_pathways_toggle -->
   <!-- DELETE: headerbar_analyses_toggle -->
   <!-- DELETE: headerbar_topology_toggle -->
   
   <!-- KEEP ONLY: -->
   <!-- - Window title -->
   <!-- - Minimize/Maximize/Close buttons -->
   ```

3. Clean up panel loader integration:
   ```python
   # DELETE callbacks:
   # - on_float_callback
   # - on_attach_callback
   # These were used to sync HeaderBar buttons, no longer needed
   ```

**Validation**: Application runs with clean HeaderBar (no toggles)

---

### Phase 2: Restructure Main Window Layout - 1 hour

**Goal**: All panels dock to LEFT using GtkStack

**Tasks**:

1. Modify `ui/main/main_window.ui`:
   ```xml
   <object class="GtkBox" id="main_content">
     <property name="orientation">horizontal</property>
     
     <!-- Master Palette Slot (48px) -->
     <child>
       <object class="GtkBox" id="master_palette_slot">
         <property name="width-request">48</property>
       </object>
     </child>
     
     <!-- Left Dock Area (GtkStack for ALL panels) -->
     <child>
       <object class="GtkStack" id="left_dock_stack">
         <property name="visible">False</property>
         <property name="transition-type">none</property>
         <!-- Panels will be added here programmatically -->
       </object>
     </child>
     
     <!-- Canvas (main drawing area) -->
     <child>
       <object class="GtkBox" id="canvas_container">
         <property name="hexpand">True</property>
         <property name="vexpand">True</property>
       </object>
     </child>
     
     <!-- NO right_dock_area! -->
   </object>
   ```

2. Update `src/shypn.py`:
   ```python
   # Get left dock stack
   self.left_dock_stack = main_builder.get_object('left_dock_stack')
   
   # Remove right dock stack references
   # DELETE: self.right_dock_stack
   ```

**Validation**: Main window has correct 3-column layout

---

### Phase 3: Create Master Palette Widget - 2 hours

**Goal**: Vertical toolbar with 4 toggle buttons

**File**: `src/shypn/ui/master_palette.py`

```python
"""Master Palette - Vertical toolbar for panel control."""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

class MasterPalette(GObject.GObject):
    """Master Palette widget for panel visibility control.
    
    Signals:
        panel-toggled(panel_name: str, active: bool): Emitted when button toggled
    """
    
    __gsignals__ = {
        'panel-toggled': (GObject.SignalFlags.RUN_FIRST, None, (str, bool)),
    }
    
    def __init__(self):
        super().__init__()
        
        # Create vertical box
        self.widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.widget.set_size_request(48, -1)
        
        # Panel definitions (order matters - top to bottom)
        self.panels = [
            ('files', 'Files', 'folder-symbolic'),
            ('pathways', 'Pathways', 'network-workgroup-symbolic'),
            ('analyses', 'Analyses', 'utilities-system-monitor-symbolic'),
            ('topology', 'Topology', 'preferences-system-symbolic'),
        ]
        
        # Create buttons
        self.buttons = {}
        for panel_name, label, icon_name in self.panels:
            btn = Gtk.ToggleButton()
            btn.set_size_request(48, 48)
            btn.set_tooltip_text(label)
            
            # Add icon
            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
            btn.set_image(icon)
            
            # Connect signal
            btn.connect('toggled', self._on_button_toggled, panel_name)
            
            # Store reference
            self.buttons[panel_name] = btn
            
            # Add to widget
            self.widget.pack_start(btn, False, False, 0)
    
    def _on_button_toggled(self, button, panel_name):
        """Internal handler for button toggle."""
        active = button.get_active()
        self.emit('panel-toggled', panel_name, active)
    
    def get_widget(self):
        """Get the widget to pack into UI."""
        return self.widget
    
    def set_active(self, panel_name, active):
        """Programmatically set button state."""
        if panel_name in self.buttons:
            self.buttons[panel_name].set_active(active)
```

**Integration** in `src/shypn.py`:
```python
from shypn.ui.master_palette import MasterPalette

# Create Master Palette
self.master_palette = MasterPalette()

# Pack into slot
master_palette_slot = main_builder.get_object('master_palette_slot')
master_palette_slot.pack_start(self.master_palette.get_widget(), True, True, 0)

# Connect signal
self.master_palette.connect('panel-toggled', self._on_panel_toggled)
```

**Validation**: Master Palette appears with 4 buttons

---

### Phase 4: Refactor Panel Loaders for GtkStack - 3 hours

**Goal**: Panels add themselves to GtkStack, not separate containers

**Changes to ALL panel loaders**:

1. **Remove** `attach_to(container)` method
2. **Add** `add_to_stack(stack, panel_name)` method
3. **Update** `hide()` and `show()` methods for stack children

**Example** (`left_panel_loader.py`):
```python
class LeftPanelLoader:
    def add_to_stack(self, stack, panel_name):
        """Add panel content to GtkStack.
        
        Args:
            stack: GtkStack widget
            panel_name: String identifier for stack child
        """
        if self.window is None:
            self.load()
        
        # Extract content from window
        if self.content.get_parent() == self.window:
            self.window.remove(self.content)
        
        # Add to stack as named child
        stack.add_named(self.content, panel_name)
        
        # Hide stack initially
        self.content.set_no_show_all(True)
        stack.set_visible(False)
        
        self.is_in_stack = True
        self.stack = stack
        self.panel_name = panel_name
    
    def show(self):
        """Show panel by setting as active stack child."""
        if self.is_in_stack:
            # Make stack visible
            self.stack.set_visible(True)
            
            # Set as active child
            self.stack.set_visible_child_name(self.panel_name)
            
            # Allow visibility
            self.content.set_no_show_all(False)
            self.content.show_all()
    
    def hide(self):
        """Hide panel (but keep in stack)."""
        if self.is_in_stack:
            # Don't hide stack - other panels might be visible
            # Just hide content
            self.content.set_no_show_all(True)
            self.content.hide()
            
            # If no other panels visible, hide stack
            # (this logic handled by Master Palette callback)
```

**Apply to**:
- `left_panel_loader.py` (Files)
- `pathway_panel_loader.py` (Pathways)
- `right_panel_loader.py` → **RENAME** to `analyses_panel_loader.py` (Analyses)
- `topology_panel_loader.py` (Topology)

**Validation**: All panels can be added to GtkStack

---

### Phase 5: Wire Master Palette to GtkStack - 2 hours

**Goal**: Master Palette buttons control which panel is visible in stack

**Implementation** in `src/shypn.py`:

```python
def setup_panels(self):
    """Initialize all panels and add to GtkStack."""
    
    # Create panels
    self.left_panel = create_left_panel()
    self.pathway_panel = create_pathway_panel()
    self.analyses_panel = create_analyses_panel()  # renamed from right_panel
    self.topology_panel = create_topology_panel()
    
    # Add all panels to stack
    self.left_panel.add_to_stack(self.left_dock_stack, 'files')
    self.pathway_panel.add_to_stack(self.left_dock_stack, 'pathways')
    self.analyses_panel.add_to_stack(self.left_dock_stack, 'analyses')
    self.topology_panel.add_to_stack(self.left_dock_stack, 'topology')
    
    # Initially all hidden
    self.left_panel.hide()
    self.pathway_panel.hide()
    self.analyses_panel.hide()
    self.topology_panel.hide()

def _on_panel_toggled(self, palette, panel_name, active):
    """Handle Master Palette button toggle.
    
    Args:
        palette: MasterPalette instance
        panel_name: 'files', 'pathways', 'analyses', or 'topology'
        active: True if button activated, False if deactivated
    """
    # Get panel instance
    panel_map = {
        'files': self.left_panel,
        'pathways': self.pathway_panel,
        'analyses': self.analyses_panel,
        'topology': self.topology_panel,
    }
    
    panel = panel_map.get(panel_name)
    if not panel:
        return
    
    if active:
        # EXCLUSIVE BEHAVIOR: Hide all other panels first
        for name, p in panel_map.items():
            if name != panel_name:
                p.hide()
                # Deactivate other buttons
                self.master_palette.buttons[name].set_active(False)
        
        # Show selected panel
        panel.show()
    else:
        # Hide panel
        panel.hide()
        
        # Hide stack if no panels visible
        self.left_dock_stack.set_visible(False)
```

**Validation**: Clicking Master Palette button shows ONLY that panel

---

### Phase 6: Testing & Error 71 Validation - 2 hours

**Test Scenarios**:
1. ✅ Rapid button clicking (10x Files → Pathways → Analyses → Topology)
2. ✅ Show panel → Close panel → Show again (10 cycles)
3. ✅ Open dialogs from panels (FileChoosers, MessageDialogs)
4. ✅ All panels start hidden on startup
5. ✅ NO Error 71 during any operation
6. ✅ Panel content preserved when hidden
7. ✅ GtkStack transitions smooth

**Failure Scenarios**:
- ❌ Error 71 appears → ROLLBACK to Phase 0, investigate root cause
- ❌ Panels don't hide correctly → Debug `set_no_show_all()` with GtkStack
- ❌ Stack transitions janky → Change `transition-type` property

**Deliverable**: Clean test run with NO errors

---

## Risk Assessment & Mitigation

### HIGH RISK: GtkStack Causes Error 71
**Probability**: 40%  
**Impact**: CRITICAL (blocks entire implementation)

**Mitigation**:
- Phase 0 validation catches this EARLY
- Alternative: Use manual show/hide without GtkStack (like skeleton)
  ```python
  # Instead of GtkStack, use simple GtkBox
  # Manually remove/add panels on button toggle
  def _on_panel_toggled(self, palette, panel_name, active):
      if active:
          # Remove all panels from left_dock_box
          for child in self.left_dock_box.get_children():
              self.left_dock_box.remove(child)
          
          # Add selected panel
          panel = panel_map[panel_name]
          self.left_dock_box.pack_start(panel.content, True, True, 0)
          panel.show()
  ```

### MEDIUM RISK: UI Files Malformed
**Probability**: 30%  
**Impact**: HIGH (requires panel refactoring)

**Mitigation**:
- Phase 0 diagnosis identifies issues
- Option A (minimal refactor) if issues are minor
- Option B (complete refactor) if issues are severe

### LOW RISK: Dead Code in Panel Loaders
**Probability**: 60%  
**Impact**: LOW (easy to clean)

**Mitigation**:
- Remove during Phase 4 refactoring
- Comment out first, test, then delete

---

## Timeline (REVISED)

| Phase | Task | Time | Blocker? |
|-------|------|------|----------|
| **0** | **Validation (GtkStack + Error 71)** | **4h** | **YES** |
| 1 | Remove HeaderBar Handlers | 0.5h | NO |
| 2 | Restructure Main Window Layout | 1h | NO |
| 3 | Create Master Palette Widget | 2h | NO |
| 4 | Refactor Panel Loaders for GtkStack | 3h | NO |
| 5 | Wire Master Palette to GtkStack | 2h | NO |
| 6 | Testing & Error 71 Validation | 2h | NO |
| **TOTAL** | | **14.5h** | |

**Critical Path**: Phase 0 → If fails → Alternative approach (manual show/hide)

---

## Success Criteria (REVISED)

✅ NO HeaderBar toggle buttons (removed completely)  
✅ Master Palette is ONLY control mechanism  
✅ ALL 4 panels dock to LEFT (in GtkStack)  
✅ NO right dock area  
✅ GtkStack validated in skeleton (Phase 0)  
✅ NO Error 71 in any scenario  
✅ Panels start hidden on startup  
✅ Exclusive panel visibility (only 1 visible at a time)  
✅ Panel content preserved when hidden  

---

## Phase 0 Deliverables (MUST DO FIRST!)

### Test 1: GtkStack Principle
**File**: `dev/test_gtkstack_principle.py`  
**Deliverable**: Test report with Error 71 status

### Test 2: Error 71 Diagnosis
**File**: `dev/test_error71_diagnosis.py`  
**Deliverable**: Issue report for each panel UI file

### Decision Document
**File**: `doc/skeleton/GTKSTACK_VALIDATION.md`  
**Content**:
- GtkStack test results
- Error 71 diagnosis results
- GO/NO-GO decision for GtkStack
- Alternative approach if needed

---

## Next Steps

1. **User Review**: Review this REVISED plan
2. **Phase 0 Start**: Create GtkStack skeleton test
3. **Decision Point**: After Phase 0, decide GO/NO-GO
4. **Implementation**: Only if Phase 0 passes

---

## Questions for User

1. **GtkStack Exclusive Behavior**: Should only 1 panel be visible at a time? (recommended)
2. **Panel Persistence**: Should we remember which panel was last visible? (optional)
3. **Keyboard Shortcuts**: F1-F4 for panel switching? (optional)
4. **Alternative if GtkStack Fails**: Use manual show/hide like skeleton? (fallback)

---

## Comparison: OLD vs NEW Plan

| Aspect | OLD Plan | NEW Plan |
|--------|----------|----------|
| HeaderBar | Keep buttons, sync with Master Palette | ❌ REMOVE completely |
| Right Dock | Keep for Analyses panel | ❌ REMOVE completely |
| Panel Layout | Left=Files, Right=Analyses, Float=Pathways/Topology | All 4 panels in LEFT stack |
| GtkStack | Assumed safe | ⚠️ MUST TEST FIRST |
| Error 71 | Assumed fixed | ⚠️ Investigate root cause |
| Panel Refactor | Not planned | ⚠️ May be required |
| Timeline | 10 hours | 14.5 hours (with validation) |

**Key Difference**: NEW plan is **RISK-AWARE** and **TEST-FIRST**

