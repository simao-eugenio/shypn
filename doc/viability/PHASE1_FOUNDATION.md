# Viability Panel - Phase 1: Foundation

**Timeline:** Weeks 1-2  
**Branch:** `viability`  
**Status:** In Progress

---

## Objectives

Create the basic Viability Panel structure following Shypn's established architecture patterns:

1. ✅ Panel displays in Master Palette (between Topology and Report)
2. ✅ Float/Attach mechanism (Wayland-safe)
3. ✅ OOP with base class and separate modules
4. ✅ Minimal code in loaders
5. ✅ Read topology issues from Topology Panel
6. ✅ Display issues in tree view (diagnosis only, no fixes yet)

---

## Architecture Patterns to Follow

### 1. Panel Structure (from Topology/Report)
```
src/shypn/ui/panels/viability/
├── __init__.py
├── viability_panel.py          # Main panel class (like topology_panel.py)
└── diagnosis_view.py            # Issue display widget
```

### 2. Loader Pattern (Minimal, like topology_panel_loader.py)
```
src/shypn/helpers/viability_panel_loader.py
```
- Instantiates ViabilityPanel
- Provides compatibility with shypn.py infrastructure
- Minimal logic, just wiring

### 3. Base Classes (if needed for categories later)
```
src/shypn/viability/
├── __init__.py
└── diagnosis/
    ├── __init__.py
    └── engine.py               # Diagnosis logic
```

### 4. Master Palette Integration
- Button position: **After Topology, Before Report**
- Icon: ⚡ (lightning bolt = "bring to life")
- Toggle behavior: Mutual exclusivity with other panels
- Careful modification of existing toggle handlers

---

## File Structure

```
doc/viability/
├── PHASE1_FOUNDATION.md        ← This file
└── IMPLEMENTATION_LOG.md       ← Session log

src/shypn/
├── ui/
│   └── panels/
│       └── viability/
│           ├── __init__.py
│           ├── viability_panel.py
│           └── diagnosis_view.py
│
├── helpers/
│   └── viability_panel_loader.py
│
└── viability/                   # Business logic (Phase 2+)
    ├── __init__.py
    └── diagnosis/
        ├── __init__.py
        └── engine.py

tests/
└── viability/
    ├── __init__.py
    └── test_viability_panel.py
```

---

## Implementation Steps

### Step 1: Create Panel Structure ✓
- [x] Create directory structure
- [x] Create `viability_panel.py` (main panel class)
- [x] Create `diagnosis_view.py` (issue tree widget)
- [x] Follow Topology Panel pattern (Gtk.Box with header)

### Step 2: Create Loader ✓
- [x] Create `viability_panel_loader.py`
- [x] Minimal code: instantiate panel, provide compatibility
- [x] Float/attach mechanism (Wayland-safe with GLib.idle_add)

### Step 3: Integrate with Master Palette
- [ ] Modify `src/shypn.py` to add 6th button
- [ ] Position: After 'topology', Before 'report'
- [ ] Wire toggle handlers carefully
- [ ] Test mutual exclusivity

### Step 4: Connect to Topology Panel
- [ ] Add `set_topology_panel()` method to ViabilityPanel
- [ ] Read topology analysis results
- [ ] Parse into issue list

### Step 5: Display Issues
- [ ] Implement DiagnosisView (GtkTreeView)
- [ ] Show issue categories (Critical/Warning/Suggestion)
- [ ] Icons: 🔴/🟡/🟢
- [ ] No action buttons yet (Phase 2)

---

## Code Patterns to Follow

### Panel Class Pattern (from TopologyPanel)
```python
class ViabilityPanel(Gtk.Box):
    """Viability Panel - Intelligent Model Repair Assistant.
    
    Displays model issues and suggests fixes.
    Phase 1: Diagnosis display only.
    """
    
    def __init__(self, model=None, model_canvas=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header (matches REPORT, TOPOLOGY, etc.)
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_size_request(-1, 48)  # Fixed 48px height
        header_label = Gtk.Label()
        header_label.set_markup("<b>VIABILITY</b>")
        # ...
        
        # Float button (top-right)
        self.float_button = Gtk.ToggleButton()
        self.float_button.set_image(...)
        
        # Content (scrollable)
        scrolled = Gtk.ScrolledWindow()
        # ...
```

### Loader Pattern (from TopologyPanelLoader)
```python
class ViabilityPanelLoader:
    """Minimal loader for Viability Panel.
    
    Responsibilities:
    - Instantiate ViabilityPanel class
    - Provide compatibility with shypn.py infrastructure
    - Wire model_canvas_loader reference
    """
    
    def __init__(self, model):
        self.model = model
        self.model_canvas_loader = None
        
        # Create floating window
        self.window = Gtk.Window()
        self.window.set_title('Viability')
        
        # Create the panel
        self.panel = ViabilityPanel(model=self.model)
        
        # Wire float button
        if hasattr(self.panel, 'float_button'):
            self.panel.float_button.connect('toggled', self._on_float_toggled)
        
        # Compatibility
        self.controller = self
        self.widget = self.panel
        self.content = self.panel
```

### Float/Attach Pattern (Wayland-safe)
```python
def hang_on(self, container):
    """Attach panel to container."""
    def _do_hang():
        if self.is_hanged:
            return
        
        # Remove from window if floating
        if self.window.get_child() == self.panel:
            self.window.remove(self.panel)
        
        # Add to container
        container.pack_start(self.panel, True, True, 0)
        self.panel.show_all()
        
        # Hide window
        self.window.hide()
        self.is_hanged = True
        
        # Update button state
        self._updating_button = True
        if hasattr(self.panel, 'float_button'):
            self.panel.float_button.set_active(False)
        self._updating_button = False
    
    GLib.idle_add(_do_hang)
```

---

## Master Palette Integration Details

### Current Button Order (from src/shypn.py)
```python
# Existing buttons:
1. 'files'      - File Explorer
2. 'pathways'   - Pathways Panel  
3. 'analyses'   - Dynamic Analyses
4. 'topology'   - Topology Panel
5. 'report'     - Report Panel
```

### New Button Order
```python
1. 'files'      - File Explorer
2. 'pathways'   - Pathways Panel
3. 'analyses'   - Dynamic Analyses
4. 'topology'   - Topology Panel
5. 'viability'  - Viability Panel  ← NEW! (before report)
6. 'report'     - Report Panel
```

### Master Palette Modification Strategy

**CAREFUL:** Master Palette has complex toggle logic. Need to:

1. **Add button definition** in `create_master_palette()`
2. **Add toggle handler** `on_viability_toggle()`
3. **Update ALL existing toggle handlers** to exclude 'viability'
4. **Wire to panel loader** in main window setup

**Search for existing patterns:**
- Look for `on_topology_toggle` as template
- Check all places where buttons are excluded: `'report'`, `'topology'`, etc.
- Ensure mutual exclusivity works correctly

---

## Testing Strategy

### Manual Testing Checklist
- [ ] Panel appears when viability button clicked
- [ ] Panel hides when other button clicked (mutual exclusivity)
- [ ] Float button works (detaches to separate window)
- [ ] Attach works (returns to left pane)
- [ ] Topology Panel connection works
- [ ] Issues display in tree view
- [ ] No crashes on Wayland

### Unit Tests
```python
# tests/viability/test_viability_panel.py
def test_panel_creation():
    panel = ViabilityPanel()
    assert panel is not None

def test_set_topology_panel():
    panel = ViabilityPanel()
    topology_panel = MockTopologyPanel()
    panel.set_topology_panel(topology_panel)
    assert panel.topology_panel is not None

def test_diagnosis_view():
    view = DiagnosisView()
    issues = [
        {'severity': 'critical', 'type': 'dead_transition', 'id': 'T3'},
        {'severity': 'warning', 'type': 'unbounded_place', 'id': 'P9'}
    ]
    view.display_issues(issues)
    assert view.get_issue_count() == 2
```

---

## Deliverables

### Phase 1 Complete When:
1. ✅ Viability button appears in Master Palette (position 5)
2. ✅ Clicking button shows Viability Panel
3. ✅ Panel has header "VIABILITY" and float button
4. ✅ Panel displays topology issues in tree view
5. ✅ Float/attach works (Wayland-safe)
6. ✅ Mutual exclusivity with other panels works
7. ✅ No crashes, clean logs

### NOT in Phase 1:
- ❌ Suggestion engine (Phase 2)
- ❌ Apply fixes (Phase 2)
- ❌ Canvas preview (Phase 2)
- ❌ Undo/redo (Phase 2)

---

## Notes

### Wayland Safety
- All widget operations use `GLib.idle_add()`
- State guards prevent redundant operations
- Proper hide→remove→add→show sequence

### Code Style
- Follow existing panel patterns exactly
- Minimal logic in loader
- OOP with separate modules
- Comprehensive docstrings

### Integration Points
- TopologyPanel.generate_summary_for_report_panel() ← Read from here
- ModelCanvasLoader.viability_panel_loader ← Store reference here
- Master Palette toggle handlers ← Modify carefully

---

## Progress Log

### Session 1 (November 9, 2025)
- [x] Created design document (VIABILITY_PANEL_DESIGN.md)
- [x] Created viability branch
- [x] Created Phase 1 planning document (this file)
- [ ] Next: Create panel structure files
