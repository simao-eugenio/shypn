# Topology Panel Implementation Plan
**Date**: October 20, 2025  
**Status**: Ready to Implement  
**Branch**: feature/property-dialogs-and-simulation-palette  
**Prerequisites**: Master Palette infrastructure complete ✅

---

## 🎯 Executive Summary

Now that the **Master Palette infrastructure** is complete with bulletproof Wayland safety, we're ready to implement the **Topology Panel** as the 4th panel in the system. This panel will provide global topology analysis tools for the entire Petri net model.

### Panel Position in Architecture

```
┌────────────────────────────────────────────────────────────────┐
│ Shypn                                           [_][□][×]      │ HeaderBar
├──┬──┬──────────────────────────────────────────────────────────┤
│📁│  │                                                          │
│🗺│P │                                                          │
│📊│a │                 Canvas                                   │
│🔬│n │            (Petri Net Display)                           │ ← Master Palette
│  │e │                                                          │   + Left Dock Panel
│  │l │                                                          │   + Canvas
├──┴──┴──────────────────────────────────────────────────────────┤
│ Status: Ready                                                  │ Status Bar
└────────────────────────────────────────────────────────────────┘
 ↑  ↑
 │  └─ Left Dock: Files OR Analyses OR Pathways OR Topology
 └─── Master Palette: 54px wide, 4 buttons (Files/Pathways/Analyses/Topology)
```

**Current Status**:
- ✅ Files panel (left_panel_loader) - Working
- ✅ Analyses panel (right_panel_loader) - Working  
- ✅ Pathways panel (pathway_panel_loader) - Working
- ⏳ **Topology panel** - TO IMPLEMENT

---

## 📋 Implementation Strategy

### Phase 1: Topology Panel Loader (2-3 days)

Create the panel loader following the existing pattern.

#### 1.1 Create Panel Loader File

**File**: `src/shypn/helpers/topology_panel_loader.py`

**Pattern**: Copy from `pathway_panel_loader.py` (simplest, most recent)

**Key Methods**:
```python
class TopologyPanelLoader:
    """Topology Panel Loader/Controller.
    
    Manages global topology analysis panel with attach/detach/float support.
    Shows network-wide topology properties and analysis results.
    
    States:
    - Detached: Standalone floating window
    - Attached: Content embedded in left dock area
    """
    
    def __init__(self, ui_path=None):
        """Initialize loader."""
        
    def load(self):
        """Load UI from XML file."""
        
    def float(self, parent_window=None):
        """Float panel as separate window."""
        
    def attach_to(self, container, parent_window=None):
        """Attach panel to container."""
        
    def hide(self):
        """Hide panel (both attached and detached states)."""
        
    def show(self):
        """Show panel."""
```

**Wayland Safety**: All methods already have deferred operations (GLib.idle_add)

---

#### 1.2 Create UI File

**File**: `ui/panels/topology_panel.ui`

**Structure**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <requires lib="gtk+" version="3.20"/>
  
  <!-- Floating window (for detached state) -->
  <object class="GtkWindow" id="topology_window">
    <property name="title">Topology Analysis</property>
    <property name="default-width">400</property>
    <property name="default-height">600</property>
    <property name="window-position">center</property>
    
    <child>
      <placeholder/>  <!-- Content will be added here -->
    </child>
  </object>
  
  <!-- Main content (shared between window and attached states) -->
  <object class="GtkBox" id="topology_content">
    <property name="orientation">vertical</property>
    <property name="visible">True</property>
    
    <!-- Header with float button -->
    <child>
      <object class="GtkBox" id="topology_header">
        <property name="orientation">horizontal</property>
        <property name="margin">6</property>
        
        <child>
          <object class="GtkLabel">
            <property name="label">&lt;b&gt;Topology Analysis&lt;/b&gt;</property>
            <property name="use-markup">True</property>
            <property name="xalign">0</property>
            <property name="hexpand">True</property>
          </object>
        </child>
        
        <child>
          <object class="GtkToggleButton" id="topology_float_button">
            <property name="image">float_icon</property>
            <property name="tooltip-text">Float/Dock Panel</property>
          </object>
        </child>
      </object>
    </child>
    
    <!-- Notebook with analysis categories -->
    <child>
      <object class="GtkNotebook" id="topology_notebook">
        <property name="visible">True</property>
        <property name="vexpand">True</property>
        
        <!-- Tab 1: Structural Analysis -->
        <child>
          <object class="GtkScrolledWindow">
            <child>
              <object class="GtkBox" id="structural_content">
                <property name="orientation">vertical</property>
                <property name="margin">12</property>
                <property name="spacing">12</property>
                
                <!-- P-Invariants Section -->
                <child>
                  <object class="GtkFrame">
                    <child type="label">
                      <object class="GtkLabel">
                        <property name="label">&lt;b&gt;P-Invariants&lt;/b&gt;</property>
                        <property name="use-markup">True</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkBox">
                        <property name="orientation">vertical</property>
                        <property name="margin">6</property>
                        <property name="spacing">6</property>
                        
                        <child>
                          <object class="GtkLabel" id="p_invariants_label">
                            <property name="label">No analysis results yet</property>
                            <property name="xalign">0</property>
                          </object>
                        </child>
                        
                        <child>
                          <object class="GtkButton" id="p_invariants_analyze_btn">
                            <property name="label">Analyze P-Invariants</property>
                          </object>
                        </child>
                      </object>
                    </child>
                  </object>
                </child>
                
                <!-- T-Invariants Section -->
                <!-- Siphons Section -->
                <!-- Traps Section -->
                
              </object>
            </child>
          </object>
          <child type="tab">
            <object class="GtkLabel">
              <property name="label">Structural</property>
            </object>
          </child>
        </child>
        
        <!-- Tab 2: Graph Analysis -->
        <child>
          <object class="GtkScrolledWindow">
            <child>
              <object class="GtkBox" id="graph_content">
                <!-- Cycles, Paths, Connectivity -->
              </object>
            </child>
          </object>
          <child type="tab">
            <object class="GtkLabel">
              <property name="label">Graph</property>
            </object>
          </child>
        </child>
        
        <!-- Tab 3: Network Analysis -->
        <child>
          <object class="GtkScrolledWindow">
            <child>
              <object class="GtkBox" id="network_content">
                <!-- Hubs, Centrality, Communities, Clustering -->
              </object>
            </child>
          </object>
          <child type="tab">
            <object class="GtkLabel">
              <property name="label">Network</property>
            </object>
          </child>
        </child>
        
      </object>
    </child>
  </object>
</interface>
```

---

#### 1.3 Integrate into Main Window

**File**: `src/shypn.py`

**Changes Needed**:

1. **Import topology panel loader**:
```python
from shypn.helpers.topology_panel_loader import create_topology_panel
```

2. **Create topology panel after other panels**:
```python
# Create topology panel (4th panel)
topology_panel_loader = create_topology_panel(
    ui_path=None,  # Use default
    model=current_model  # Pass model for analysis
)
```

3. **Connect to master palette button**:
```python
def on_topology_toggle(is_active):
    """Handle Topology panel toggle from palette."""
    if is_active:
        # Hide other panels (mutual exclusivity)
        if master_palette.buttons['files'].get_active():
            master_palette.set_active('files', False)
            left_panel_loader.hide()
        if master_palette.buttons['analyses'].get_active():
            master_palette.set_active('analyses', False)
            right_panel_loader.hide()
        if master_palette.buttons['pathways'].get_active():
            master_palette.set_active('pathways', False)
            pathway_panel_loader.hide()
        
        # Attach Topology panel to LEFT dock
        topology_panel_loader.attach_to(left_dock_area, parent_window=window)
        # Adjust paned position (400px for topology panel)
        if left_paned:
            try:
                left_paned.set_position(400)
            except Exception:
                pass
    else:
        # Detach and hide
        topology_panel_loader.hide()
        # Reset paned position
        if left_paned:
            try:
                left_paned.set_position(0)
            except Exception:
                pass

# Connect palette button
master_palette.connect('topology', on_topology_toggle)
```

4. **Enable topology button** (currently disabled):
```python
# Enable topology button (was disabled in Phase 1)
master_palette.set_sensitive('topology', True)
```

5. **Add float/attach callbacks**:
```python
def on_topology_float():
    """Collapse left paned when Topology panel floats."""
    if left_paned:
        try:
            left_paned.set_position(0)
        except Exception:
            pass
    master_palette.set_active('topology', False)

def on_topology_attach():
    """Expand left paned when Topology panel attaches."""
    if left_paned:
        try:
            left_paned.set_position(400)
        except Exception:
            pass
    master_palette.set_active('topology', True)

# Set callbacks on loader
topology_panel_loader.on_float_callback = on_topology_float
topology_panel_loader.on_attach_callback = on_topology_attach
```

---

### Phase 2: Topology Analysis Integration (1-2 weeks)

Connect existing analyzers to the panel.

#### 2.1 Analysis Controller

**File**: `src/shypn/ui/topology_panel_controller.py`

**Purpose**: Coordinate between UI panel and topology analyzers

```python
class TopologyPanelController:
    """Controller for Topology Panel.
    
    Responsibilities:
    - Run topology analyzers on demand
    - Update UI with analysis results
    - Coordinate highlighting on canvas
    - Cache analysis results
    """
    
    def __init__(self, panel_loader, model):
        self.panel_loader = panel_loader
        self.model = model
        self.analyzers = {
            'p_invariants': PInvariantAnalyzer(),
            't_invariants': TInvariantAnalyzer(),  # TODO: implement
            'cycles': CycleAnalyzer(),
            'paths': PathAnalyzer(),
            'hubs': HubAnalyzer(),
            # ... more analyzers
        }
        self.results_cache = {}
    
    def analyze_p_invariants(self):
        """Run P-Invariant analysis and update UI."""
        result = self.analyzers['p_invariants'].analyze(self.model)
        self.results_cache['p_invariants'] = result
        self._update_p_invariants_ui(result)
        return result
    
    def analyze_all_structural(self):
        """Run all structural analyzers."""
        self.analyze_p_invariants()
        self.analyze_t_invariants()
        self.analyze_siphons()
        self.analyze_traps()
    
    def _update_p_invariants_ui(self, result):
        """Update P-Invariants section in UI."""
        label = self.panel_loader.builder.get_object('p_invariants_label')
        if result.success:
            count = len(result.data.get('invariants', []))
            label.set_text(f"Found {count} P-invariants")
        else:
            label.set_text(f"Error: {result.error}")
```

---

#### 2.2 Connect Analyzers to UI

**In**: `src/shypn/helpers/topology_panel_loader.py`

```python
def load(self):
    """Load UI and connect analyzers."""
    # ... load UI ...
    
    # Create controller
    self.controller = TopologyPanelController(self, self.model)
    
    # Connect analyze buttons
    p_inv_btn = self.builder.get_object('p_invariants_analyze_btn')
    p_inv_btn.connect('clicked', lambda b: self.controller.analyze_p_invariants())
    
    t_inv_btn = self.builder.get_object('t_invariants_analyze_btn')
    t_inv_btn.connect('clicked', lambda b: self.controller.analyze_t_invariants())
    
    # ... connect more buttons ...
```

---

### Phase 3: Canvas Highlighting Integration (3-4 days)

Enable visual feedback on canvas.

#### 3.1 Highlighting Manager Integration

**Pattern**: Follow SwissKnife palette highlighting pattern

```python
class TopologyPanelController:
    def __init__(self, panel_loader, model, highlighting_manager):
        self.highlighting_manager = highlighting_manager
        # ...
    
    def highlight_p_invariant(self, invariant_index):
        """Highlight a P-invariant on canvas."""
        result = self.results_cache.get('p_invariants')
        if not result or not result.success:
            return
        
        invariant = result.data['invariants'][invariant_index]
        places = invariant['places']
        
        # Highlight places in the invariant
        self.highlighting_manager.highlight_invariant(
            places,
            color='yellow',
            label=f"P-Inv {invariant_index + 1}"
        )
    
    def highlight_cycle(self, cycle_index):
        """Highlight a cycle on canvas."""
        result = self.results_cache.get('cycles')
        if not result or not result.success:
            return
        
        cycle = result.data['cycles'][cycle_index]
        nodes = cycle['nodes']
        
        # Highlight cycle
        self.highlighting_manager.highlight_cycle(
            nodes,
            color='blue',
            label=f"Cycle {cycle_index + 1}"
        )
```

---

## 📐 UI Layout Design

### Panel Width
- **Recommended**: 400px (wider than other panels due to complex content)
- **Files**: 250px
- **Analyses**: 280px
- **Pathways**: 320px
- **Topology**: 400px ← NEW

### Visual Style
- **Match existing panels**: Same Nord theme, same styling
- **Nord Colors**: #2e3440 (bg), #88c0d0 (accent), #d8dee9 (text)
- **Consistent spacing**: 12px margins, 6px padding
- **GTK Frames**: Use frames to group related content

### Content Organization

```
╔═══════════════════════════════════════════╗
║ Topology Analysis              [Float]   ║
╠═══════════════════════════════════════════╣
║ [Structural] [Graph] [Network]            ║ ← Notebook tabs
╠═══════════════════════════════════════════╣
║                                           ║
║ P-Invariants                              ║
║ ┌───────────────────────────────────────┐ ║
║ │ Found 3 invariants                    │ ║
║ │ - Mass conservation (C6H12O6)         │ ║
║ │ - ATP/ADP balance                     │ ║
║ │ - NAD+/NADH cycle                     │ ║
║ │                                       │ ║
║ │ [Analyze] [Highlight] [Export]        │ ║
║ └───────────────────────────────────────┘ ║
║                                           ║
║ T-Invariants                              ║
║ ┌───────────────────────────────────────┐ ║
║ │ Not analyzed yet                      │ ║
║ │ [Analyze]                             │ ║
║ └───────────────────────────────────────┘ ║
║                                           ║
║ Siphons                                   ║
║ Traps                                     ║
║                                           ║
╚═══════════════════════════════════════════╝
```

---

## 🧪 Testing Strategy

### Unit Tests

**File**: `tests/panels/test_topology_panel_loader.py`

```python
import pytest
from shypn.helpers.topology_panel_loader import TopologyPanelLoader

class TestTopologyPanelLoader:
    def test_panel_creation(self):
        """Test panel can be created."""
        loader = TopologyPanelLoader()
        assert loader is not None
    
    def test_panel_load(self):
        """Test panel UI can be loaded."""
        loader = TopologyPanelLoader()
        loader.load()
        assert loader.window is not None
        assert loader.content is not None
    
    def test_attach_detach_cycle(self):
        """Test attach/detach/float operations."""
        # Similar to other panel tests
        pass
    
    def test_analyzer_integration(self):
        """Test analyzers can be run from panel."""
        pass
```

### Integration Tests

**Manual Testing Checklist**:
- [ ] Panel appears when Topology button clicked
- [ ] Only one panel visible at a time (mutual exclusivity)
- [ ] Float button works (panel becomes floating window)
- [ ] Dock button works (panel re-attaches)
- [ ] Analyze buttons trigger analyzers
- [ ] Results display correctly
- [ ] Highlighting works on canvas
- [ ] No Wayland errors or crashes
- [ ] Performance acceptable (< 1s for most analyses)

---

## 📊 Implementation Timeline

### Week 1: Panel Infrastructure (Days 1-3)
- Day 1: Create topology_panel_loader.py (4-6 hours)
- Day 2: Create topology_panel.ui (4-6 hours)
- Day 3: Integrate into main window, enable button (4-6 hours)

**Milestone**: ✅ Topology panel appears and floats/docks correctly

---

### Week 2: Analysis Integration (Days 4-8)
- Day 4: Create TopologyPanelController (6-8 hours)
- Day 5-6: Connect P-Invariants analyzer (4-6 hours)
- Day 6-7: Connect Cycles analyzer (4-6 hours)
- Day 7-8: Connect Paths analyzer (4-6 hours)
- Day 8: Connect Hubs analyzer (4-6 hours)

**Milestone**: ✅ All 4 existing analyzers working in panel

---

### Week 3: Highlighting & Polish (Days 9-12)
- Day 9-10: Implement highlighting integration (8-10 hours)
- Day 11: Polish UI, add icons, improve layout (6-8 hours)
- Day 12: Testing, bug fixes, documentation (6-8 hours)

**Milestone**: ✅ Topology panel complete and production-ready

---

### Future: Remaining Analyzers (Weeks 4-10)
- Implement remaining 8 static analyzers (T-Invariants, Siphons, etc.)
- Add to topology panel as they're completed
- Continuous integration and testing

---

## 🎯 Success Criteria

### Phase 1 Complete When:
- [ ] topology_panel_loader.py created and working
- [ ] topology_panel.ui created with all tabs
- [ ] Panel appears when Topology button clicked
- [ ] Panel floats/docks correctly
- [ ] No Wayland errors
- [ ] All panel loader tests passing

### Phase 2 Complete When:
- [ ] TopologyPanelController created
- [ ] P-Invariants analyzer connected and working
- [ ] Cycles analyzer connected and working
- [ ] Paths analyzer connected and working
- [ ] Hubs analyzer connected and working
- [ ] Results display correctly in UI

### Phase 3 Complete When:
- [ ] Highlighting manager integrated
- [ ] Can highlight invariants on canvas
- [ ] Can highlight cycles on canvas
- [ ] Can highlight paths on canvas
- [ ] Can highlight hubs on canvas
- [ ] UI polished and professional
- [ ] All tests passing
- [ ] Documentation complete

---

## 📚 Reference Files

### Study These Files (Pattern Examples)
- `src/shypn/helpers/pathway_panel_loader.py` - Most similar panel
- `src/shypn/helpers/left_panel_loader.py` - File operations panel
- `src/shypn/helpers/right_panel_loader.py` - Analyses panel
- `ui/panels/pathway_panel.ui` - UI example
- `src/shypn.py` (lines 378-402) - Pathway panel integration

### Topology Analyzers (Business Logic)
- `src/shypn/topology/structural/p_invariants.py`
- `src/shypn/topology/graph/cycles.py`
- `src/shypn/topology/graph/paths.py`
- `src/shypn/topology/network/hubs.py`

### Infrastructure Files
- `src/shypn/ui/master_palette.py` - Palette that controls panels
- `src/shypn/ui/palette_button.py` - Button in palette
- `doc/WAYLAND_ATTACH_DETACH_FIXES.md` - Wayland safety patterns

---

## 🚀 Quick Start Commands

### Create Panel Loader Skeleton
```bash
cd /home/simao/projetos/shypn
cp src/shypn/helpers/pathway_panel_loader.py src/shypn/helpers/topology_panel_loader.py
# Edit to change class name, imports, etc.
```

### Create UI File
```bash
mkdir -p ui/panels
touch ui/panels/topology_panel.ui
# Edit with template above
```

### Test Panel
```bash
cd /home/simao/projetos/shypn
python3 src/shypn.py
# Click Topology button (should now be enabled)
```

### Run Panel Tests
```bash
PYTHONPATH=/home/simao/projetos/shypn/src:$PYTHONPATH python3 -m pytest tests/panels/test_topology_panel_loader.py -v
```

---

## 💡 Key Implementation Tips

### 1. Start Simple
- Get basic panel showing first
- Add analyzers one at a time
- Test each integration thoroughly

### 2. Follow Wayland Safety Patterns
- All widget reparenting uses `GLib.idle_add()`
- State checks prevent redundant operations
- Exception handling everywhere

### 3. Reuse Existing Code
- Copy from pathway_panel_loader (newest, cleanest)
- Use same Nord CSS theme
- Follow same attach/detach patterns

### 4. Test Incrementally
- Test panel loading
- Test float/dock operations
- Test each analyzer integration
- Test highlighting separately

### 5. Document As You Go
- Add docstrings to all methods
- Comment complex logic
- Update this document with learnings

---

## 🏆 Expected Outcome

After 3 weeks of implementation:

```
✅ Topology Panel Infrastructure Complete
   - Panel appears and hides correctly
   - Floats and docks smoothly
   - No Wayland errors
   - Follows existing patterns

✅ 4 Analyzers Integrated
   - P-Invariants working
   - Cycles working
   - Paths working
   - Hubs working

✅ Canvas Highlighting Working
   - Can highlight invariants
   - Can highlight cycles
   - Can highlight paths
   - Can highlight hubs

✅ Production Ready
   - All tests passing
   - Documentation complete
   - User-friendly UI
   - Performance acceptable
```

---

**Status**: 🟢 Ready to Begin Implementation  
**Next Step**: Create topology_panel_loader.py  
**Estimated Time**: 3 weeks to completion  
**Confidence**: 🟢 High (infrastructure proven, patterns established)

---

**Last Updated**: October 20, 2025  
**Author**: Development Team  
**Version**: 1.0
