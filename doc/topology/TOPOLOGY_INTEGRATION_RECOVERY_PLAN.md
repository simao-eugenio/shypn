# Topology Integration Recovery Plan

**Date**: December 2024  
**Status**: Recovery Mode  
**Goal**: Resume Topology Analysis Integration into Property Dialogs

---

## 📖 Context

We were working on integrating Petri net topology analysis and graph properties into property dialogs. This resulted in **FOUR CATEGORIES** of analysis tools that would be displayed in a "Topology" tab in each property dialog.

### The Four Categories

1. **Structural Analysis** (Petri Net Theory)
   - P-Invariants (place invariants)
   - T-Invariants (transition invariants)
   - Siphons (places that stay empty)
   - Traps (places that stay marked)

2. **Graph Topology** (Network Theory)
   - Cycles (feedback loops)
   - Paths & Connectivity
   - SCCs (Strongly Connected Components)
   - DAG Analysis

3. **Behavioral Analysis** (Dynamic Properties)
   - Liveness (can transitions fire?)
   - Boundedness (token limits)
   - Reachability (state space)
   - Deadlock Detection

4. **Network Analysis** (Graph Centrality)
   - Hub Detection
   - Centrality Measures
   - Community Detection
   - Clustering Coefficient

---

## 🏗️ Architecture

### Directory Structure (Planned)

```
src/shypn/topology/
    base/
        topology_analyzer.py        # Abstract base class ✅
        analysis_result.py          # Result data structure ✅
        exceptions.py               # Custom exceptions
    
    structural/
        p_invariants.py             # P-invariant analysis
        t_invariants.py             # T-invariant analysis
        siphons.py                  # Siphon detection
        traps.py                    # Trap detection
    
    graph/
        cycles.py                   # Cycle detection ✅ IMPLEMENTED
        paths.py                    # Path finding
        sccs.py                     # SCC analysis
        dag.py                      # DAG analysis
    
    behavioral/
        liveness.py                 # Liveness analysis
        boundedness.py              # Boundedness checking
        reachability.py             # Reachability analysis
        deadlock.py                 # Deadlock detection
    
    network/
        hubs.py                     # Hub detection
        centrality.py               # Centrality measures
        communities.py              # Community detection
        clustering.py               # Clustering coefficient
```

### Design Principles

1. **OOP Base Classes**: All analyzers inherit from `TopologyAnalyzer`
2. **Separate Modules**: Each analyzer in its own file
3. **Thin Loaders**: UI loaders delegate to analyzers
4. **No Orphaned Widgets**: Proper GTK widget lifecycle
5. **Wayland Compatible**: No X11-specific code

---

## ✅ What's Already Implemented

### 1. Base Infrastructure ✅

**Files Created**:
- `src/shypn/topology/base/topology_analyzer.py` - Abstract base class
- `src/shypn/topology/base/analysis_result.py` - Result data structure

**What It Provides**:
```python
# Base class for all analyzers
class TopologyAnalyzer(ABC):
    @abstractmethod
    def analyze(self, **kwargs) -> AnalysisResult:
        pass

# Standard result format
@dataclass
class AnalysisResult:
    success: bool
    data: Dict[str, Any]
    summary: str
    warnings: List[str]
    errors: List[str]
    metadata: Dict[str, Any]
```

### 2. Cycle Analyzer ✅

**File**: `src/shypn/topology/graph/cycles.py`

**Status**: ✅ Fully Implemented

**Features**:
- Detects all elementary cycles (simple cycles)
- Uses Johnson's algorithm via NetworkX
- Classifies cycle types (self-loop, balanced, place-heavy, transition-heavy)
- Finds cycles containing specific nodes

**Usage**:
```python
from shypn.topology.graph.cycles import CycleAnalyzer

analyzer = CycleAnalyzer(model)
result = analyzer.analyze(max_cycles=100)

for cycle in result.get('cycles', []):
    print(f"Cycle: {' → '.join(cycle['names'])}")
    print(f"  Length: {cycle['length']}")
    print(f"  Type: {cycle['type']}")
```

---

## 🔄 What Needs to Be Recovered/Continued

### Phase 1: Verify Existing Implementation ✅

**Action Items**:
1. ✅ Verify `topology/base/` classes exist and work
2. ✅ Verify `topology/graph/cycles.py` is implemented
3. ✅ Check if property dialog integration started
4. ✅ Review test coverage

### Phase 2: Property Dialog Integration 🔄

**Goal**: Add "Topology" tab to all three property dialogs

**Files to Modify**:
1. `ui/dialogs/place_prop_dialog.ui` - Add Topology tab
2. `ui/dialogs/transition_prop_dialog.ui` - Add Topology tab  
3. `ui/dialogs/arc_prop_dialog.ui` - Add Topology tab

**Python Loaders to Update**:
1. `src/shypn/helpers/place_prop_dialog_loader.py`
2. `src/shypn/helpers/transition_prop_dialog_loader.py`
3. `src/shypn/helpers/arc_prop_dialog_loader.py`

**What to Add**:
```python
def _setup_topology_tab(self):
    """Setup topology tab with analysis results."""
    from shypn.topology.graph.cycles import CycleAnalyzer
    
    # Create analyzer
    cycle_analyzer = CycleAnalyzer(self.model)
    result = cycle_analyzer.analyze()
    
    # Find cycles containing this object
    obj_cycles = [c for c in result.get('cycles', []) 
                  if self.place_obj.id in c['nodes']]
    
    # Update UI
    cycles_label = self.builder.get_object('topology_cycles_label')
    if cycles_label:
        if obj_cycles:
            text = f"In {len(obj_cycles)} cycle(s):\n"
            for i, cycle in enumerate(obj_cycles[:5], 1):
                names = ' → '.join(cycle['names'][:10])
                text += f"  {i}. {names}\n"
            cycles_label.set_text(text)
        else:
            cycles_label.set_text("Not in any cycles")
```

### Phase 3: Implement Priority Analyzers 🔜

**Next Analyzers (in priority order)**:

1. **P-Invariants** (Week 2)
   - File: `topology/structural/p_invariants.py`
   - Uses: Integer linear algebra (null space of C^T)
   - Output: Conservation laws

2. **Hubs** (Week 2)
   - File: `topology/network/hubs.py`
   - Wrap existing: `layout/sscc/hub_mass_assigner.py`
   - Output: Super-hubs, major hubs, minor hubs

3. **Paths** (Week 3)
   - File: `topology/graph/paths.py`
   - Uses: NetworkX shortest/longest paths
   - Output: Connectivity analysis

4. **T-Invariants** (Week 3)
   - File: `topology/structural/t_invariants.py`
   - Uses: Null space of C
   - Output: Reproducible firing sequences

---

## 🎯 Recovery Steps

### Step 1: Verify Foundation ✅

```bash
# Check if files exist
ls -la src/shypn/topology/base/
ls -la src/shypn/topology/graph/cycles.py

# Run existing tests
python3 -m pytest tests/topology/ -v
```

### Step 2: Check Current Property Dialog State

```bash
# Check if Topology tab exists in UI files
grep -n "Topology" ui/dialogs/*_prop_dialog.ui

# Check if loaders have topology methods
grep -n "topology" src/shypn/helpers/*_prop_dialog_loader.py
```

### Step 3: Add Topology Tab to UI Files

**Example for Place Dialog** (`ui/dialogs/place_prop_dialog.ui`):

```xml
<!-- Add after existing tabs -->
<child>
  <object class="GtkBox" id="topology_tab">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="orientation">vertical</property>
    <property name="spacing">10</property>
    <property name="margin">10</property>
    
    <!-- Cycles Section -->
    <child>
      <object class="GtkFrame">
        <property name="visible">True</property>
        <property name="label">Cycles</property>
        <child>
          <object class="GtkLabel" id="topology_cycles_label">
            <property name="visible">True</property>
            <property name="xalign">0</property>
            <property name="yalign">0</property>
            <property name="wrap">True</property>
            <property name="selectable">True</property>
            <property name="label">Analyzing...</property>
          </object>
        </child>
      </object>
    </child>
    
    <!-- P-Invariants Section -->
    <child>
      <object class="GtkFrame">
        <property name="visible">True</property>
        <property name="label">P-Invariants</property>
        <child>
          <object class="GtkLabel" id="topology_p_invariants_label">
            <property name="visible">True</property>
            <property name="xalign">0</property>
            <property name="yalign">0</property>
            <property name="wrap">True</property>
            <property name="selectable">True</property>
            <property name="label">Not yet analyzed</property>
          </object>
        </child>
      </object>
    </child>
    
    <!-- Connectivity Section -->
    <child>
      <object class="GtkFrame">
        <property name="visible">True</property>
        <property name="label">Connectivity</property>
        <child>
          <object class="GtkLabel" id="topology_connectivity_label">
            <property name="visible">True</property>
            <property name="xalign">0</property>
            <property name="yalign">0</property>
            <property name="wrap">True</property>
            <property name="selectable">True</property>
            <property name="label">Not yet analyzed</property>
          </object>
        </child>
      </object>
    </child>
  </object>
</child>
<child type="tab">
  <object class="GtkLabel">
    <property name="visible">True</property>
    <property name="label">Topology</property>
  </object>
</child>
```

### Step 4: Add Topology Methods to Loaders

**In each dialog loader** (place/transition/arc):

```python
def _setup_topology_tab(self):
    """Setup topology analysis tab.
    
    Displays structural and graph properties of the Petri net
    relevant to this object.
    """
    try:
        # Import analyzers
        from shypn.topology.graph.cycles import CycleAnalyzer
        
        # Get object ID for filtering
        obj_id = self.place_obj.id  # or transition_obj.id, or arc_obj.id
        
        # --- Cycles Analysis ---
        cycle_analyzer = CycleAnalyzer(self.model)
        cycle_result = cycle_analyzer.analyze(max_cycles=100)
        
        if cycle_result.success:
            # Filter cycles containing this object
            obj_cycles = [c for c in cycle_result.get('cycles', [])
                         if obj_id in c['nodes']]
            
            # Update UI
            cycles_label = self.builder.get_object('topology_cycles_label')
            if cycles_label:
                if obj_cycles:
                    text = f"In {len(obj_cycles)} cycle(s):\n\n"
                    for i, cycle in enumerate(obj_cycles[:5], 1):
                        # Truncate long cycles
                        names = cycle['names'][:10]
                        if len(cycle['names']) > 10:
                            names.append('...')
                        cycle_str = ' → '.join(names)
                        text += f"{i}. {cycle_str}\n"
                        text += f"   Length: {cycle['length']}, Type: {cycle['type']}\n\n"
                    
                    if len(obj_cycles) > 5:
                        text += f"... and {len(obj_cycles) - 5} more cycles\n"
                    
                    cycles_label.set_text(text)
                else:
                    cycles_label.set_text("✓ Not in any cycles")
        else:
            cycles_label = self.builder.get_object('topology_cycles_label')
            if cycles_label:
                error_text = "❌ Cycle analysis failed:\n"
                error_text += '\n'.join(cycle_result.errors)
                cycles_label.set_text(error_text)
        
        # --- P-Invariants Analysis (when implemented) ---
        # p_inv_label = self.builder.get_object('topology_p_invariants_label')
        # if p_inv_label:
        #     p_inv_label.set_text("Analysis coming soon...")
        
        # --- Connectivity Analysis (when implemented) ---
        # conn_label = self.builder.get_object('topology_connectivity_label')
        # if conn_label:
        #     conn_label.set_text("Analysis coming soon...")
        
    except Exception as e:
        print(f"⚠️  Topology tab setup failed: {e}")
        import traceback
        traceback.print_exc()
```

**Call from `show()` method**:
```python
def show(self):
    """Show the dialog."""
    # ... existing code ...
    
    # Setup all tabs
    self._setup_basic_tab()
    self._setup_visual_tab()
    self._setup_topology_tab()  # ← Add this!
    
    self.dialog.show_all()
```

---

## 📋 Implementation Checklist

### Week 1: Recovery & Integration
- [ ] Verify topology base classes exist and work
- [ ] Verify cycles analyzer is implemented
- [ ] Add Topology tab to place_prop_dialog.ui
- [ ] Add Topology tab to transition_prop_dialog.ui
- [ ] Add Topology tab to arc_prop_dialog.ui
- [ ] Add `_setup_topology_tab()` to place loader
- [ ] Add `_setup_topology_tab()` to transition loader
- [ ] Add `_setup_topology_tab()` to arc loader
- [ ] Test cycle analysis in property dialogs
- [ ] Write/update tests

### Week 2: P-Invariants & Hubs
- [ ] Implement P-Invariants analyzer
- [ ] Wrap existing Hub analyzer
- [ ] Integrate P-Invariants into dialogs
- [ ] Integrate Hubs into dialogs
- [ ] Write tests

### Week 3: Paths & T-Invariants
- [ ] Implement Paths analyzer
- [ ] Implement T-Invariants analyzer
- [ ] Integrate into dialogs
- [ ] Write tests

### Week 4: Polish & Documentation
- [ ] Complete all four categories
- [ ] Update documentation
- [ ] Performance optimization
- [ ] User testing

---

## 🎨 UI Design Guidelines

### Topology Tab Layout

```
┌─────────────────────────────────────┐
│  Topology                           │
├─────────────────────────────────────┤
│                                     │
│  ┌─ Cycles ─────────────────────┐  │
│  │ In 3 cycle(s):                │  │
│  │   1. P1 → T1 → P2 → T2 → P1   │  │
│  │      Length: 4, Type: balanced│  │
│  │   2. P1 → T3 → P5 → T4 → P1   │  │
│  │      Length: 4, Type: balanced│  │
│  │   ... and 1 more cycle        │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌─ P-Invariants ────────────────┐  │
│  │ In 1 invariant:               │  │
│  │   P1 + P2 = 10 (conservation) │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌─ Connectivity ────────────────┐  │
│  │ Degree: 4 (2 in, 2 out)      │  │
│  │ In SCC: Main Component (23)   │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌─ Network Properties ──────────┐  │
│  │ Hub Type: Minor hub           │  │
│  │ Centrality: 0.342             │  │
│  └───────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```

### Wayland Safety Rules

1. ✅ **Use GtkLabel** for display (not TextView)
2. ✅ **Proper hierarchy**: All widgets have parents
3. ✅ **No orphans**: Clean up in destructors
4. ✅ **No X11 calls**: Use GTK3 standard widgets only
5. ✅ **Visible property**: Set on all widgets

---

## 📚 Documentation

### Key Documents

1. **Main Plan**: `doc/TOPOLOGY_TOOLS_PALETTE_PLAN.md` - Full specification
2. **Implementation**: `doc/topology/IMPLEMENTATION_PLAN_OPTION_A.md` - Detailed plan
3. **README**: `doc/topology/README.md` - Overview and quick start
4. **Phases**: `doc/topology/PHASE*.md` - Completed phases

### Reference Materials

- Cycle detection: Johnson's algorithm (1975)
- P-Invariants: Integer linear algebra
- Petri net theory: Murata (1989)
- Network analysis: NetworkX documentation

---

## 🚀 Next Actions

1. **Immediate**: Check what exists in `src/shypn/topology/`
2. **Then**: Add Topology tab to UI files
3. **Then**: Integrate cycles analyzer into property dialogs
4. **Finally**: Test and iterate

---

**Status**: 🔄 Ready to Resume  
**Priority**: High (Property dialog enhancement)  
**Estimated Time**: 2-3 weeks for complete four-category integration

