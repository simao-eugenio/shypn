# Topology Analysis Panel - Design Document

**Date**: December 18, 2024  
**Status**: Planning Phase  
**Pattern**: Float/Dock/Attach/Detach (like Analyses & Pathway Panels)  

---

## 🎯 Overview

Create a **Topology Panel** following the same architectural pattern as the existing **Analyses Panel** (right panel) and **Pathway Panel**. This panel will provide comprehensive topology analysis capabilities with the float/dock/attach/detach behavior users expect.

### Existing Panel Pattern in Shypn

The application already has two successful panel implementations:

1. **Right Panel (Analyses)** - `RightPanelLoader`
   - Location: `src/shypn/helpers/right_panel_loader.py` (443 lines)
   - UI: `ui/panels/right_panel.ui`
   - Contains: Place/Transition rate plots, Diagnostics
   - Features: Float/dock, attach/detach, dynamic plots during simulation

2. **Pathway Panel** - `PathwayPanelLoader`
   - Location: `src/shypn/helpers/pathway_panel_loader.py` (357 lines)
   - UI: `ui/panels/pathway_panel.ui`
   - Contains: KEGG import, SBML import, pathway browser
   - Features: Float/dock, attach/detach, notebook with multiple tabs

### New Panel: Topology Panel

Following the same pattern, we'll create:

3. **Topology Panel** - `TopologyPanelLoader` (NEW)
   - Location: `src/shypn/helpers/topology_panel_loader.py` (to be created)
   - UI: `ui/panels/topology_panel.ui` (to be created)
   - Contains: All 20 topology analyzers (static + dynamic)
   - Features: Float/dock, attach/detach, notebook with analysis tabs

---

## 🏗️ Architecture Pattern

### Core Components

Every panel in Shypn follows this structure:

```
┌────────────────────────────────────────────────────────┐
│                    Panel Window                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Toolbar (with Float/Dock button)                │  │
│  ├──────────────────────────────────────────────────┤  │
│  │                                                  │  │
│  │          Panel Content (reparentable)            │  │
│  │                                                  │  │
│  │   - Can be in window (floating)                  │  │
│  │   - Can be in main window container (docked)     │  │
│  │                                                  │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

### Panel States

1. **Floating** - Standalone window, can be moved anywhere
2. **Docked** - Content embedded in main window container
3. **Hidden** - Window not visible (but still exists)

### Key Features

- **Reparenting**: Content box can move between window and main container
- **State Persistence**: Remembers user's preference (float/dock)
- **Clean Destruction**: Properly handles window close events
- **Callback System**: Notifies main window of state changes

---

## 📋 Topology Panel Design

### Panel Structure

```
┌───────────────────────────────────────────────────────────┐
│  Topology Analysis Panel                       [Float] [×] │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Static Analysis | Dynamic Analysis | Settings      │  │
│  ├─────────────────────────────────────────────────────┤  │
│  │                                                     │  │
│  │  [Active Tab Content]                               │  │
│  │                                                     │  │
│  │  • Cycles                                           │  │
│  │  • P-Invariants                                     │  │
│  │  • Paths                                            │  │
│  │  • Hubs                                             │  │
│  │  • T-Invariants                                     │  │
│  │  • Siphons/Traps                                    │  │
│  │  • Centrality                                       │  │
│  │  • Communities                                      │  │
│  │  • Clustering                                       │  │
│  │                                                     │  │
│  │  [Analyze] [Highlight] [Export] [Clear]            │  │
│  │                                                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### Three Main Tabs

#### Tab 1: Static Analysis
**Properties computed from network structure alone**

**Categories:**
- **Structural** (4 tools)
  - P-Invariants ✅
  - T-Invariants ⏳
  - Siphons ⏳
  - Traps ⏳

- **Graph** (4 tools)
  - Cycles ✅
  - Paths ✅
  - DAG Analysis ⏳
  - Connectivity ⏳

- **Network** (4 tools)
  - Hubs ✅
  - Centrality ⏳
  - Communities ⏳
  - Clustering ⏳

**Total: 12 static tools (4/12 complete)**

**UI Layout:**
```
┌────────────────────────────────────────────────┐
│ Static Analysis                                │
├────────────────────────────────────────────────┤
│                                                │
│  Select Analysis Type:                         │
│  [Cycles ▼]                                    │
│                                                │
│  ┌──────────────────────────────────────────┐  │
│  │ Results:                                 │  │
│  │                                          │  │
│  │ Found 3 cycles:                          │  │
│  │  • Cycle 1: P1 → T1 → P2 → T2 → P1      │  │
│  │  • Cycle 2: P3 → T3 → P4 → T4 → P3      │  │
│  │  • Cycle 3: P1 → T5 → P3 → T2 → P1      │  │
│  │                                          │  │
│  └──────────────────────────────────────────┘  │
│                                                │
│  [Analyze Now] [Highlight] [Export CSV]       │
│                                                │
│  Options:                                      │
│  ☑ Auto-analyze on model load                 │
│  ☑ Cache results                               │
│  ☐ Show progress during analysis               │
│                                                │
└────────────────────────────────────────────────┘
```

#### Tab 2: Dynamic Analysis
**Properties requiring simulation or state space exploration**

**Categories:**
- **State Space** (3 tools)
  - Reachability ⏳
  - Boundedness ⏳
  - Coverability ⏳

- **Liveness** (2 tools)
  - Liveness Analysis ⏳
  - Deadlock Detection ⏳

- **Performance** (3 tools)
  - Throughput ⏳
  - Response Time ⏳
  - Bottlenecks ⏳

**Total: 8 dynamic tools (0/8 complete)**

**UI Layout:**
```
┌────────────────────────────────────────────────┐
│ Dynamic Analysis                               │
├────────────────────────────────────────────────┤
│                                                │
│  Simulation Status: Running...                 │
│  Progress: [████████░░] 80%                    │
│                                                │
│  ┌──────────────────────────────────────────┐  │
│  │ Live Results:                            │  │
│  │                                          │  │
│  │ Reachability:                            │  │
│  │  • States explored: 1,247                │  │
│  │  • State space size: 2.4 MB              │  │
│  │                                          │  │
│  │ Boundedness:                             │  │
│  │  • All places bounded: YES               │  │
│  │  • Max tokens (P1): 15                   │  │
│  │                                          │  │
│  │ Deadlocks:                               │  │
│  │  • Deadlock-free: NO                     │  │
│  │  • Deadlock states found: 3              │  │
│  │                                          │  │
│  └──────────────────────────────────────────┘  │
│                                                │
│  [Pause] [Resume] [Highlight Issues]          │
│                                                │
└────────────────────────────────────────────────┘
```

#### Tab 3: Settings
**Configuration and preferences**

```
┌────────────────────────────────────────────────┐
│ Settings                                       │
├────────────────────────────────────────────────┤
│                                                │
│  Analysis Behavior:                            │
│  ┌──────────────────────────────────────────┐  │
│  │ ☑ Cache static analysis results         │  │
│  │ ☑ Auto-clear cache on model change      │  │
│  │ ☐ Run static analysis on model load     │  │
│  │ ☑ Show warnings for large networks      │  │
│  └──────────────────────────────────────────┘  │
│                                                │
│  Performance:                                  │
│  ┌──────────────────────────────────────────┐  │
│  │ Max cycles to find: [1000      ]         │  │
│  │ Timeout (seconds): [30         ]         │  │
│  │ Use threading: ☑ Yes ☐ No               │  │
│  └──────────────────────────────────────────┘  │
│                                                │
│  Highlighting:                                 │
│  ┌──────────────────────────────────────────┐  │
│  │ Cycle color: [🔵 Blue]                   │  │
│  │ Path color: [🟢 Green]                   │  │
│  │ Hub color: [🔴 Red]                      │  │
│  │ Invariant color: [🟡 Yellow]             │  │
│  │ Line width: [2          ]                │  │
│  └──────────────────────────────────────────┘  │
│                                                │
│  [Restore Defaults] [Apply]                   │
│                                                │
└────────────────────────────────────────────────┘
```

---

## 💻 Implementation Plan

### Phase 1: Panel Infrastructure (Week 1)

**Goal**: Create panel skeleton following existing pattern

**Tasks:**

1. **Create UI File** (`ui/panels/topology_panel.ui`)
   - Copy `pathway_panel.ui` as template
   - Modify window title to "Topology Analysis"
   - Add notebook with 3 tabs (Static, Dynamic, Settings)
   - Include float/dock button in toolbar

2. **Create Loader Class** (`src/shypn/helpers/topology_panel_loader.py`)
   - Copy `pathway_panel_loader.py` as template
   - Adapt constructor for topology-specific dependencies
   - Implement float/dock/attach/detach behavior
   - Add callback system for state changes

3. **Integrate with Main Window** (modify `src/shypn.py`)
   - Add topology panel to main window
   - Add menu item: View → Topology Analysis
   - Add keyboard shortcut: Ctrl+T
   - Wire float/dock callbacks

**Deliverable**: Empty topology panel that floats/docks correctly

**Time Estimate**: 4-6 hours

---

### Phase 2: Static Analysis Tab (Weeks 2-3)

**Goal**: Integrate existing 4 analyzers + implement 8 new ones

**2.1 Integrate Existing Analyzers (Week 2)**

Connect the 4 complete analyzers:
- ✅ CycleAnalyzer
- ✅ PInvariantAnalyzer
- ✅ PathAnalyzer
- ✅ HubAnalyzer

Tasks:
1. Create dropdown selector for analysis type
2. Create results display area (scrollable text view)
3. Wire "Analyze Now" button to analyzer
4. Display results in formatted text
5. Add "Highlight" button (connects to canvas)
6. Add "Export" button (save to CSV/JSON)

**Time**: 8-10 hours

**2.2 Implement New Static Analyzers (Week 3)**

Implement 8 remaining analyzers:
- T-Invariants (4-6h)
- Siphons (6-8h)
- Traps (4-6h)
- DAG Analysis (3-4h)
- Centrality (6-8h)
- Communities (6-8h)
- Clustering (3-4h)

**Time**: 35-44 hours (full week)

**Deliverable**: Complete static analysis tab with all 12 tools

---

### Phase 3: Dynamic Analysis Tab (Weeks 4-5)

**Goal**: Implement all 8 dynamic analyzers

**3.1 State Space Analyzers (Week 4)**
- Reachability (10-12h)
- Boundedness (8-10h)
- Coverability (6-8h)

**3.2 Liveness & Performance (Week 5)**
- Liveness (8-10h)
- Deadlock Detection (6-8h)
- Throughput (6-8h)
- Response Time (4-6h)
- Bottlenecks (6-8h)

**Deliverable**: Complete dynamic analysis tab with all 8 tools

**Time**: ~60 hours (2 weeks)

---

### Phase 4: Settings & Polish (Week 6)

**Goal**: Add settings tab and polish UX

Tasks:
1. Settings tab UI (4h)
2. Preferences persistence (4h)
3. Canvas highlighting integration (8h)
4. Performance optimization (8h)
5. Error handling (4h)
6. User documentation (4h)

**Deliverable**: Production-ready topology panel

**Time**: 32 hours (1 week)

---

## 🔧 Technical Details

### Panel Loader Structure

```python
# src/shypn/helpers/topology_panel_loader.py

class TopologyPanelLoader:
    """Loader and controller for Topology Analysis panel (attachable window)."""
    
    def __init__(self, ui_path=None, model_canvas=None, workspace_settings=None):
        """Initialize the topology panel loader.
        
        Args:
            ui_path: Path to topology_panel.ui. If None, uses default.
            model_canvas: ModelCanvasManager for highlighting
            workspace_settings: WorkspaceSettings for preferences
        """
        # Standard panel attributes
        self.ui_path = ui_path or self._get_default_ui_path()
        self.model_canvas = model_canvas
        self.workspace_settings = workspace_settings
        self.builder = None
        self.window = None
        self.content = None
        self.is_attached = False
        self.parent_container = None
        self.parent_window = None
        self._updating_button = False
        self.on_float_callback = None
        self.on_attach_callback = None
        
        # Topology-specific attributes
        self.static_analyzers = {}  # {name: analyzer_instance}
        self.dynamic_analyzers = {}
        self.analysis_cache = {}  # Cache for expensive computations
        self.current_model = None
        self.highlighting_manager = None
    
    def load(self):
        """Load the panel UI and return the window."""
        # Load UI file
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        
        # Extract window and content
        self.window = self.builder.get_object('topology_panel_window')
        self.content = self.builder.get_object('topology_panel_content')
        
        # Setup float/dock button
        float_button = self.builder.get_object('float_button')
        if float_button:
            float_button.connect('toggled', self._on_float_toggled)
        
        # Initialize tabs
        self._setup_static_tab()
        self._setup_dynamic_tab()
        self._setup_settings_tab()
        
        # Initialize analyzers
        self._initialize_analyzers()
        
        # Connect window close event
        self.window.connect('delete-event', self._on_delete_event)
        
        return self.window
    
    def _setup_static_tab(self):
        """Setup static analysis tab."""
        # Get widgets
        self.static_combo = self.builder.get_object('static_analysis_combo')
        self.static_results = self.builder.get_object('static_results_view')
        self.analyze_button = self.builder.get_object('analyze_button')
        self.highlight_button = self.builder.get_object('highlight_button')
        self.export_button = self.builder.get_object('export_button')
        
        # Connect signals
        self.analyze_button.connect('clicked', self._on_analyze_clicked)
        self.highlight_button.connect('clicked', self._on_highlight_clicked)
        self.export_button.connect('clicked', self._on_export_clicked)
        
        # Populate combo box
        self._populate_static_combo()
    
    def _initialize_analyzers(self):
        """Initialize all analyzer instances."""
        from shypn.topology.graph.cycles import CycleAnalyzer
        from shypn.topology.structural.p_invariants import PInvariantAnalyzer
        from shypn.topology.graph.paths import PathAnalyzer
        from shypn.topology.network.hubs import HubAnalyzer
        
        self.static_analyzers = {
            'cycles': CycleAnalyzer(),
            'p_invariants': PInvariantAnalyzer(),
            'paths': PathAnalyzer(),
            'hubs': HubAnalyzer(),
            # More to be added...
        }
    
    def _on_analyze_clicked(self, button):
        """Handle analyze button click."""
        # Get selected analysis type
        selected = self.static_combo.get_active_text()
        
        # Check if model is available
        if not self.current_model:
            self._show_error("No model loaded")
            return
        
        # Get analyzer
        analyzer = self.static_analyzers.get(selected.lower())
        if not analyzer:
            self._show_error(f"Analyzer not found: {selected}")
            return
        
        # Run analysis (in thread to avoid blocking)
        GLib.idle_add(self._run_analysis, analyzer, selected)
    
    def _run_analysis(self, analyzer, name):
        """Run analysis and display results."""
        try:
            # Show progress
            self._show_progress(f"Analyzing {name}...")
            
            # Run analyzer
            result = analyzer.analyze(self.current_model)
            
            # Cache result
            self.analysis_cache[name] = result
            
            # Display result
            self._display_result(name, result)
            
            # Hide progress
            self._hide_progress()
            
        except Exception as e:
            self._show_error(f"Analysis failed: {str(e)}")
            self._hide_progress()
    
    # Float/dock behavior (copy from pathway_panel_loader.py)
    def _on_float_toggled(self, button):
        """Handle float button toggle."""
        # Same implementation as PathwayPanelLoader
        pass
    
    def float(self):
        """Float the panel (detach from main window)."""
        # Same implementation as PathwayPanelLoader
        pass
    
    def dock(self, container):
        """Dock the panel (attach to main window)."""
        # Same implementation as PathwayPanelLoader
        pass
```

---

## 🎨 UI File Structure

```xml
<!-- ui/panels/topology_panel.ui -->
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <requires lib="gtk+" version="3.20"/>
  
  <!-- Main Window -->
  <object class="GtkWindow" id="topology_panel_window">
    <property name="title">Topology Analysis</property>
    <property name="default-width">500</property>
    <property name="default-height">600</property>
    <property name="icon-name">applications-science</property>
    
    <child>
      <object class="GtkBox" orientation="vertical">
        <!-- Toolbar -->
        <child>
          <object class="GtkToolbar">
            <child>
              <object class="GtkToolButton">
                <property name="label">Refresh</property>
                <property name="icon-name">view-refresh</property>
              </object>
            </child>
            <child>
              <object class="GtkSeparatorToolItem"/>
            </child>
            <child>
              <object class="GtkToggleToolButton" id="float_button">
                <property name="label">Float</property>
                <property name="icon-name">window-new</property>
              </object>
            </child>
          </object>
        </child>
        
        <!-- Content (reparentable) -->
        <child>
          <object class="GtkBox" id="topology_panel_content" orientation="vertical">
            <property name="expand">True</property>
            
            <child>
              <object class="GtkNotebook">
                <!-- Static Analysis Tab -->
                <child>
                  <object class="GtkBox" orientation="vertical">
                    <property name="margin">12</property>
                    <property name="spacing">12</property>
                    
                    <!-- Analysis selector -->
                    <child>
                      <object class="GtkComboBoxText" id="static_analysis_combo">
                        <items>
                          <item>Cycles</item>
                          <item>P-Invariants</item>
                          <item>Paths</item>
                          <item>Hubs</item>
                        </items>
                      </object>
                    </child>
                    
                    <!-- Results area -->
                    <child>
                      <object class="GtkScrolledWindow">
                        <property name="expand">True</property>
                        <child>
                          <object class="GtkTextView" id="static_results_view">
                            <property name="editable">False</property>
                          </object>
                        </child>
                      </object>
                    </child>
                    
                    <!-- Action buttons -->
                    <child>
                      <object class="GtkButtonBox">
                        <child>
                          <object class="GtkButton" id="analyze_button">
                            <property name="label">Analyze Now</property>
                          </object>
                        </child>
                        <child>
                          <object class="GtkButton" id="highlight_button">
                            <property name="label">Highlight</property>
                          </object>
                        </child>
                        <child>
                          <object class="GtkButton" id="export_button">
                            <property name="label">Export</property>
                          </object>
                        </child>
                      </object>
                    </child>
                  </object>
                  <packing>
                    <property name="tab_label">Static Analysis</property>
                  </packing>
                </child>
                
                <!-- Dynamic Analysis Tab -->
                <child>
                  <object class="GtkLabel">
                    <property name="label">Dynamic analysis tab (to be implemented)</property>
                  </object>
                  <packing>
                    <property name="tab_label">Dynamic Analysis</property>
                  </packing>
                </child>
                
                <!-- Settings Tab -->
                <child>
                  <object class="GtkLabel">
                    <property name="label">Settings tab (to be implemented)</property>
                  </object>
                  <packing>
                    <property name="tab_label">Settings</property>
                  </packing>
                </child>
              </object>
            </child>
          </object>
        </child>
      </object>
    </child>
  </object>
</interface>
```

---

## 📊 Integration Points

### Main Window Integration

Add topology panel to main window:

```python
# In src/shypn.py (MainWindow class)

def _setup_panels(self):
    """Setup all floating/dockable panels."""
    # Existing panels
    self._setup_left_panel()
    self._setup_right_panel()
    self._setup_pathway_panel()
    
    # NEW: Topology panel
    self._setup_topology_panel()

def _setup_topology_panel(self):
    """Setup topology analysis panel."""
    from shypn.helpers.topology_panel_loader import TopologyPanelLoader
    
    self.topology_panel_loader = TopologyPanelLoader(
        model_canvas=self.model_canvas,
        workspace_settings=self.workspace_settings
    )
    
    self.topology_panel_window = self.topology_panel_loader.load()
    
    # Set callbacks
    self.topology_panel_loader.on_float_callback = self._on_topology_panel_floated
    self.topology_panel_loader.on_attach_callback = self._on_topology_panel_attached
    
    # Connect to model changes
    self.model_canvas.connect('model-changed', self._on_model_changed_topology)

def _on_topology_panel_floated(self):
    """Handle topology panel float."""
    # Update menu checkboxes
    pass

def _on_topology_panel_attached(self):
    """Handle topology panel dock."""
    # Update menu checkboxes
    pass

def _on_model_changed_topology(self, canvas, model):
    """Update topology panel when model changes."""
    if self.topology_panel_loader:
        self.topology_panel_loader.set_model(model)
```

### Menu Integration

Add menu items:

```xml
<!-- In ui/main_window.ui -->
<menu>
  <item>
    <attribute name="label">Topology Analysis</attribute>
    <attribute name="action">win.toggle-topology-panel</attribute>
    <attribute name="accel">&lt;Primary&gt;t</attribute>
  </item>
</menu>
```

---

## ✅ Success Criteria

### Phase 1 Complete When:
- [ ] Topology panel window floats/docks correctly
- [ ] Panel follows same pattern as Analyses/Pathway panels
- [ ] Menu item and keyboard shortcut work
- [ ] Panel state persists across sessions

### Phase 2 Complete When:
- [ ] All 12 static analyzers implemented
- [ ] Static tab shows analysis results
- [ ] Highlight button works (highlights on canvas)
- [ ] Export button saves results to file
- [ ] Analysis cache works correctly

### Phase 3 Complete When:
- [ ] All 8 dynamic analyzers implemented
- [ ] Dynamic tab updates during simulation
- [ ] Live analysis works without freezing UI
- [ ] Canvas highlights dynamic issues

### Phase 4 Complete When:
- [ ] Settings tab allows configuration
- [ ] Preferences persist correctly
- [ ] Performance is acceptable (<1s for most analyses)
- [ ] User documentation complete
- [ ] All tests passing

---

## 📚 References

### Existing Code to Study

**Panel Patterns:**
- `src/shypn/helpers/right_panel_loader.py` - Right panel (analyses)
- `src/shypn/helpers/pathway_panel_loader.py` - Pathway panel
- `ui/panels/right_panel.ui` - Right panel UI
- `ui/panels/pathway_panel.ui` - Pathway panel UI

**Topology Infrastructure:**
- `src/shypn/topology/base/topology_analyzer.py` - Base analyzer
- `src/shypn/topology/graph/cycles.py` - Cycle analyzer (complete)
- `src/shypn/topology/structural/p_invariants.py` - P-invariants (complete)
- `src/shypn/topology/graph/paths.py` - Path analyzer (complete)
- `src/shypn/topology/network/hubs.py` - Hub analyzer (complete)

**Related Documentation:**
- `doc/topology/PHASES_1_TO_4_COMPLETE.md` - Current status
- `doc/topology/REVISED_PLAN_OCT2025.md` - Detailed plan
- `doc/topology/EXECUTIVE_SUMMARY_OCT2025.md` - Executive summary

---

## 🎯 Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 1: Panel Infrastructure | 4-6 hours | Empty panel that floats/docks |
| 2: Static Analysis Tab | 2-3 weeks | 12 static analyzers complete |
| 3: Dynamic Analysis Tab | 2 weeks | 8 dynamic analyzers complete |
| 4: Settings & Polish | 1 week | Production-ready panel |
| **TOTAL** | **6 weeks** | **Complete topology panel** |

---

## 🚀 Next Steps

### Immediate Actions

1. **Review and Approve Design** (30 min)
   - Review this document
   - Confirm panel pattern is correct
   - Approve architecture

2. **Create Panel Infrastructure** (Week 1)
   - Create `ui/panels/topology_panel.ui`
   - Create `src/shypn/helpers/topology_panel_loader.py`
   - Integrate with main window
   - Test float/dock behavior

3. **Integrate Existing Analyzers** (Week 2)
   - Connect 4 complete analyzers
   - Create results display
   - Test with real models

4. **Implement Remaining Analyzers** (Weeks 3-5)
   - 8 static analyzers (Week 3)
   - 8 dynamic analyzers (Weeks 4-5)

5. **Polish and Document** (Week 6)
   - Settings tab
   - Performance optimization
   - User documentation

---

**Status**: 🟢 Design Complete, Ready to Implement  
**Next Step**: Create panel infrastructure (Week 1)  
**Pattern**: Float/Dock/Attach/Detach (proven architecture)  
**Priority**: Follows established Shypn panel pattern  

**Last Updated**: December 18, 2024  
**Version**: 1.0 (Initial Design)
