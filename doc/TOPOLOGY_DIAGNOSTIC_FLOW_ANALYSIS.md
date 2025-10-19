# Topology Tools: Diagnostic Flow Analysis & Implementation Plan

**Date**: October 19, 2025  
**Purpose**: Analyze existing diagnostic flow, compare with topology plan, and create practical implementation strategy

---

## 📋 Executive Summary

This document analyzes:
1. **Existing diagnostic flow path** - What we already have
2. **Coverage of Petri net topology properties** - Gap analysis
3. **Real-time panel grouping** - Similar to diagnostic flow
4. **Static properties for dialogs** - What to add to property dialogs
5. **Essential tools for biochemists** - Priority palette tools

---

## 1️⃣ Diagnostic Flow Path Analysis

### **Current Diagnostic Flow Architecture**

```
User Interaction
      ↓
[Right-click Transition] → Context Menu
      ↓
"Add to Analysis" → DiagnosticsPanel
      ↓
┌─────────────────────────────────────────────┐
│         DiagnosticsPanel                    │
│  (src/shypn/analyses/diagnostics_panel.py)  │
├─────────────────────────────────────────────┤
│  • Real-time updates (500ms)                │
│  • Auto-tracking (follows active trans.)    │
│  • Locality detection                       │
│  • Static + Runtime analysis                │
└─────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────┐
│         Analysis Components                 │
├─────────────────────────────────────────────┤
│  LocalityDetector                           │
│    └─ Detects locality structure            │
│                                             │
│  LocalityAnalyzer (STATIC)                  │
│    ├─ Token counts (in/out/balance)         │
│    ├─ Arc weights                           │
│    ├─ Place counts                          │
│    └─ Can fire (static check)               │
│                                             │
│  LocalityRuntimeAnalyzer (DYNAMIC)          │
│    ├─ Recent firing events                  │
│    ├─ Throughput calculation                │
│    ├─ Enablement state                      │
│    ├─ Time since last fire                  │
│    └─ Logical time tracking                 │
└─────────────────────────────────────────────┘
      ↓
Display in Right Panel
  • Locality Structure
  • Static Analysis
  • Runtime Diagnostics
  • Recent Events (last 5)
```

---

### **What Diagnostic Flow Currently Shows**

#### **A. Locality Structure** ✅
```
Input Places:  2 (P1, P2)
Output Places: 2 (P3, P4)
Input Arcs:    2
Output Arcs:   2
Valid Locality: Yes
```

#### **B. Static Analysis** ✅
```
Places:           4 (2 in, 2 out)
Arcs:             4
Arc Weight:       4.0
Input Tokens:     5
Output Tokens:    0
Token Balance:    +5
Can Fire (static): ✓ Yes
```

#### **C. Runtime Diagnostics** ✅
```
Simulation Time:  12.5s
Enabled Now:      ✓ Yes
Reason:           Sufficient input tokens
Last Fired:       10.2s
Time Since:       2.3s ago
Recent Events:    8
Throughput:       0.392 fires/sec
```

#### **D. Recent Events** ✅
```
1. t= 10.20s  fire
2. t=  8.15s  fire
3. t=  6.30s  fire
4. t=  4.50s  fire
5. t=  2.10s  fire
```

---

## 2️⃣ Gap Analysis: What We're Missing

### **Comparison: Diagnostic Flow vs. Topology Plan**

| **Property** | **Diagnostic Flow** | **Topology Plan** | **Status** |
|--------------|---------------------|-------------------|------------|
| **Locality Structure** | ✅ Yes | Not in plan | ✅ **Already have** |
| **Token Flow** | ✅ Yes (in/out/balance) | Not in plan | ✅ **Already have** |
| **Recent Events** | ✅ Yes (last 5-10) | Not in plan | ✅ **Already have** |
| **Throughput** | ✅ Yes (fires/sec) | Not in plan | ✅ **Already have** |
| **Enablement** | ✅ Yes (can fire now) | ⚠️ Part of liveness | ⚠️ **Partial** |
| | | | |
| **P-Invariants** | ❌ No | ✅ Yes | ❌ **MISSING** |
| **T-Invariants** | ❌ No | ✅ Yes | ❌ **MISSING** |
| **Siphons** | ❌ No | ✅ Yes | ❌ **MISSING** |
| **Traps** | ❌ No | ✅ Yes | ❌ **MISSING** |
| **Cycles** | ❌ No | ✅ Yes | ❌ **MISSING** |
| **Paths** | ❌ No | ✅ Yes | ❌ **MISSING** |
| **SCCs** | ❌ No | ✅ Yes (impl. exists) | ⚠️ **Not exposed** |
| **DAG Analysis** | ❌ No | ✅ Yes | ❌ **MISSING** |
| **Liveness** | ⚠️ Partial (can fire now) | ✅ Yes (L0-L4) | ⚠️ **Partial** |
| **Boundedness** | ❌ No | ✅ Yes (k-bounded) | ❌ **MISSING** |
| **Reachability** | ❌ No | ✅ Yes | ❌ **MISSING** |
| **Deadlocks** | ❌ No | ✅ Yes | ❌ **MISSING** |
| **Hubs** | ❌ No | ✅ Yes (impl. exists) | ⚠️ **Not exposed** |
| **Centrality** | ❌ No | ✅ Yes | ❌ **MISSING** |
| **Communities** | ❌ No | ✅ Yes | ❌ **MISSING** |
| **Clustering** | ❌ No | ✅ Yes | ❌ **MISSING** |

---

### **Summary: Coverage Status**

✅ **Already Covered by Diagnostic Flow**: 4 properties
- Locality structure
- Token flow analysis
- Recent events tracking
- Throughput calculation

⚠️ **Partially Covered**: 3 properties
- Enablement (dynamic only, not full liveness L0-L4)
- SCCs (implemented but not exposed in UI)
- Hubs (implemented but not exposed in UI)

❌ **Missing from Current Implementation**: 13 properties
- P/T-invariants (critical for conservation laws)
- Siphons/Traps (critical for deadlock analysis)
- Cycles (important for biochemical pathways)
- Paths (reachability, critical path)
- DAG analysis (workflow structure)
- Full liveness analysis (L0-L4 classification)
- Boundedness (capacity limits)
- Reachability (state space)
- Deadlock detection (stuck states)
- Centrality measures (importance ranking)
- Community detection (functional modules)
- Clustering coefficient (network density)

---

## 3️⃣ Real-Time Panel Grouping (Like Diagnostic Flow)

### **Proposed: "Topology Analysis" Right Panel**

Similar to how DiagnosticsPanel shows real-time metrics, we can create a **TopologyPanel** that groups related topology properties.

```
┌──────────────────────────────────────────────┐
│      TOPOLOGY ANALYSIS PANEL                 │
│  (Right Panel - Updates in Real-Time)        │
├──────────────────────────────────────────────┤
│                                              │
│  📊 STRUCTURAL PROPERTIES                    │
│  ─────────────────────────────────────       │
│  P-Invariants:      3 found                  │
│    • Inv1: P1+P2 = 5 (conservation)          │
│    • Inv2: P3+P4+P5 = 10                     │
│    • Inv3: P6 = 1 (mutex)                    │
│                                              │
│  T-Invariants:      2 found                  │
│    • Inv1: [T1×2, T2×1] → cycle              │
│    • Inv2: [T3×1, T4×1] → loop               │
│                                              │
│  Siphons:           1 found ⚠️               │
│    • {P1, P3} - Currently EMPTY!             │
│                                              │
│  Traps:             2 found                  │
│    • {P2, P4} - Marked (safe)                │
│    • {P5, P6} - Accumulating                 │
│                                              │
│  ─────────────────────────────────────       │
│                                              │
│  🔄 GRAPH TOPOLOGY                           │
│  ─────────────────────────────────────       │
│  Cycles:            5 found                  │
│    • Main cycle: [P1→T1→P2→T2→P1] (len=4)   │
│    • Feedback: [T3→P5→T4→P6→T3] (len=4)     │
│    [View All] [Highlight]                    │
│                                              │
│  SCCs:              3 components             │
│    • SCC1: 25 nodes (main production)        │
│    • SCC2: 8 nodes (preprocessing)           │
│    • SCC3: 12 nodes (postprocessing)         │
│    [Visualize]                               │
│                                              │
│  Paths:             Selected: P1 → P10       │
│    • Shortest: 5 hops (4.2s estimated)       │
│    • Alternative: 3 paths found              │
│    [Show on Canvas]                          │
│                                              │
│  ─────────────────────────────────────       │
│                                              │
│  ⚡ BEHAVIORAL PROPERTIES                    │
│  ─────────────────────────────────────       │
│  Liveness:          L3 (potentially live)    │
│    • L4 (Live): 5 transitions                │
│    • L3: 8 transitions                       │
│    • L0 (Dead): 1 transition ⚠️              │
│    [Details]                                 │
│                                              │
│  Boundedness:       Safe (1-bounded)         │
│    • Safe places: 12                         │
│    • k-bounded: 8 (max k=10)                 │
│    • Unbounded: 0 ✓                          │
│                                              │
│  Deadlocks:         None detected ✓          │
│    • Reachable states: 247                   │
│    • Deadlock states: 0                      │
│                                              │
│  ─────────────────────────────────────       │
│                                              │
│  🌐 NETWORK STRUCTURE                        │
│  ─────────────────────────────────────       │
│  Hubs:              2 super-hubs found       │
│    • P5 "G6P": degree=12 (central)           │
│    • P18 "ATP": degree=15 (energy)           │
│    [Show Hub Map]                            │
│                                              │
│  Communities:       5 modules detected       │
│    • Glycolysis: 18 nodes                    │
│    • TCA Cycle: 15 nodes                     │
│    • ATP Synthesis: 8 nodes                  │
│    [Visualize Communities]                   │
│                                              │
│  Clustering:        0.42 (moderate)          │
│    • Network type: Small-world               │
│    • Triangles: 47 found                     │
│                                              │
└──────────────────────────────────────────────┘
```

---

### **Panel Design Features**

1. **Collapsible Sections** (like Diagnostics)
   - User can collapse/expand each category
   - Remember collapsed state in preferences

2. **Real-Time Updates** (500ms like Diagnostics)
   - Update counts and states during simulation
   - Highlight changes (e.g., siphon becomes empty)

3. **Interactive Buttons**
   - [View All] - Open detailed view
   - [Highlight] - Highlight on canvas
   - [Visualize] - Show graph visualization

4. **Color Coding** (like Diagnostics)
   - ✓ Green: Good/safe
   - ⚠️ Yellow: Warning
   - ❌ Red: Error/problem

5. **Context-Sensitive** (like Diagnostics)
   - When transition/place selected → show related properties
   - When nothing selected → show global properties

---

### **Implementation Strategy**

```python
# Similar to DiagnosticsPanel structure

class TopologyPanel:
    """Real-time topology analysis panel (right panel)."""
    
    def __init__(self, model, data_collector):
        self.model = model
        self.data_collector = data_collector
        
        # Analysis components
        self.structural_analyzer = StructuralAnalyzer(model)  # NEW
        self.graph_analyzer = GraphAnalyzer(model)           # NEW
        self.behavioral_analyzer = BehavioralAnalyzer(model) # NEW
        self.network_analyzer = NetworkAnalyzer(model)       # NEW
        
        # Existing components (reuse!)
        self.locality_detector = LocalityDetector(model)
        self.locality_analyzer = LocalityAnalyzer(model)
        self.runtime_analyzer = LocalityRuntimeAnalyzer(model, data_collector)
    
    def setup(self, container):
        """Setup panel with GTK container."""
        # Create collapsible sections
        self._create_structural_section()
        self._create_graph_section()
        self._create_behavioral_section()
        self._create_network_section()
        
        # Start real-time updates (500ms like DiagnosticsPanel)
        GLib.timeout_add(500, self._update_all_sections)
    
    def _update_all_sections(self):
        """Update all sections (called every 500ms)."""
        self._update_structural_properties()
        self._update_graph_topology()
        self._update_behavioral_properties()
        self._update_network_structure()
        return True  # Continue timer
```

---

## 4️⃣ Static Properties for Property Dialogs

### **What to Add to Property Dialogs**

Property dialogs show **static, editable properties** for selected objects.  
Topology properties that are **static and informative** should be added here.

---

### **A. Place Properties Dialog**

**Current Properties** (PlacePropDialogLoader):
```
✅ Name (read-only)
✅ Tokens (editable)
✅ Radius (editable)
✅ Capacity (editable)
✅ Border Width (editable)
✅ Border Color (editable)
✅ Description (editable)
```

**Proposed: Add "Topology" Tab**:
```
┌──────────────────────────────────────────────┐
│  Place Properties Dialog                     │
├──────────────────────────────────────────────┤
│  [General] [Appearance] [Topology] [Docs]    │  ← NEW TAB
├──────────────────────────────────────────────┤
│                                              │
│  📊 Topology Information                     │
│  ─────────────────────────────────────       │
│                                              │
│  Structural Properties:                      │
│    • In P-Invariants: 2 invariants           │
│      - P1 + P2 = 5                           │
│      - P3 + P4 + P5 = 10                     │
│                                              │
│    • In Siphons: 1 siphon                    │
│      - {P1, P3, P5} ⚠️ Currently empty!      │
│                                              │
│    • In Traps: 1 trap                        │
│      - {P2, P4, P6} ✓ Marked                 │
│                                              │
│  ─────────────────────────────────────       │
│                                              │
│  Graph Topology:                             │
│    • Degree: 5 (3 in, 2 out)                 │
│    • In SCCs: SCC #1 (25 nodes)              │
│    • In Cycles: 2 cycles                     │
│      - Cycle 1: [P1→T1→P2→T2→P1]             │
│      - Cycle 2: [P1→T3→P5→T4→P1]             │
│                                              │
│  ─────────────────────────────────────       │
│                                              │
│  Behavioral Properties:                      │
│    • Boundedness: 5-bounded (max 5 tokens)   │
│    • Current tokens: 3 / 5                   │
│    • Reachable range: [0, 5]                 │
│                                              │
│  ─────────────────────────────────────       │
│                                              │
│  Network Properties:                         │
│    • Hub status: Minor hub (degree ≥ 3)      │
│    • Centrality (degree): 0.125              │
│    • Centrality (betweenness): 0.342         │
│    • In community: "Glycolysis" (18 nodes)   │
│                                              │
│  ─────────────────────────────────────       │
│                                              │
│  [Refresh] [Export Report]                   │
│                                              │
└──────────────────────────────────────────────┘
```

**Implementation**:
```python
# src/shypn/helpers/place_prop_dialog_loader.py

def _populate_topology_tab(self):
    """Populate topology tab with static analysis."""
    
    # Get analysis
    structural = self.structural_analyzer.analyze_place(self.place_obj)
    graph = self.graph_analyzer.analyze_place(self.place_obj)
    behavioral = self.behavioral_analyzer.analyze_place(self.place_obj)
    network = self.network_analyzer.analyze_place(self.place_obj)
    
    # Populate fields
    self._set_text('p_invariants_label', structural['p_invariants_text'])
    self._set_text('siphons_label', structural['siphons_text'])
    self._set_text('traps_label', structural['traps_text'])
    self._set_text('degree_label', f"{graph['degree']} ({graph['in_degree']} in, {graph['out_degree']} out)")
    # ... etc
```

---

### **B. Transition Properties Dialog**

**Current Properties** (TransitionPropDialogLoader):
```
✅ Name (read-only)
✅ Type (immediate/timed/stochastic/continuous)
✅ Rate function (type-specific)
✅ Guard (optional)
✅ Priority (optional)
✅ Description (editable)
```

**Proposed: Add "Topology" Tab**:
```
┌──────────────────────────────────────────────┐
│  Transition Properties Dialog                │
├──────────────────────────────────────────────┤
│  [General] [Behavior] [Topology] [Docs]      │  ← NEW TAB
├──────────────────────────────────────────────┤
│                                              │
│  📊 Topology Information                     │
│  ─────────────────────────────────────────   │
│                                              │
│  Structural Properties:                      │
│    • In T-Invariants: 2 invariants           │
│      - [T1×2, T2×1, T3×1] → Production cycle │
│      - [T4×1, T5×1] → Feedback loop          │
│                                              │
│    • Locality:                               │
│      - Input places: 2 (P1, P2)              │
│      - Output places: 2 (P3, P4)             │
│      - Token balance: +2 (producer)          │
│                                              │
│  ─────────────────────────────────────────   │
│                                              │
│  Graph Topology:                             │
│    • Degree: 4 (2 in, 2 out)                 │
│    • In SCCs: SCC #1 (25 nodes)              │
│    • In Cycles: 3 cycles                     │
│      - Main: [T1→P2→T2→P3→T1]                │
│      - Feedback: [T1→P5→T4→P6→T1]            │
│      - Nested: [T1→P8→T5→P9→T1]              │
│                                              │
│  ─────────────────────────────────────────   │
│                                              │
│  Behavioral Properties:                      │
│    • Liveness: L3 (potentially live)         │
│    • Can fire now: ✓ Yes                     │
│    • Enablement: 85% of the time             │
│    • Conflicts with: T5, T7 (shared input)   │
│                                              │
│  ─────────────────────────────────────────   │
│                                              │
│  Network Properties:                         │
│    • Centrality (betweenness): 0.421         │
│      → Critical pathway junction!            │
│    • In community: "Glycolysis" (18 nodes)   │
│                                              │
│  ─────────────────────────────────────────   │
│                                              │
│  Runtime Statistics (if simulation active):  │
│    • Total fires: 127                        │
│    • Throughput: 0.42 fires/sec              │
│    • Last fired: 2.3s ago                    │
│                                              │
│  [Refresh] [Export Report]                   │
│                                              │
└──────────────────────────────────────────────┘
```

---

### **C. Arc Properties Dialog**

**Current Properties**:
```
✅ Weight (editable)
✅ Arc type (normal/inhibitor/reset)
✅ Description
```

**Proposed: Add Topology Info** (simpler):
```
┌──────────────────────────────────────────────┐
│  Arc Properties Dialog                       │
├──────────────────────────────────────────────┤
│  [General] [Topology]                        │  ← NEW TAB
├──────────────────────────────────────────────┤
│                                              │
│  📊 Topology Information                     │
│  ─────────────────────────────────────────   │
│                                              │
│  Connection:                                 │
│    • From: P1 "Glucose"                      │
│    • To: T2 "Hexokinase"                     │
│    • Direction: Place → Transition (input)   │
│                                              │
│  Flow Analysis:                              │
│    • Weight: 2 (stoichiometry)               │
│    • Part of cycles: 2 cycles                │
│    • Critical path: Yes (on shortest path)   │
│                                              │
│  Token Flow (if simulation active):          │
│    • Total tokens: 245 tokens passed         │
│    • Flow rate: 0.84 tokens/sec              │
│                                              │
└──────────────────────────────────────────────┘
```

---

### **Summary: What Goes in Dialogs**

**Include in Property Dialogs**:
- ✅ **Static topology properties** (invariants, cycles, SCCs)
- ✅ **Structural relationships** (part of which cycles/invariants)
- ✅ **Network metrics** (degree, centrality, community)
- ✅ **Boundedness limits** (max tokens observed)
- ✅ **Conflict information** (which transitions conflict)

**Do NOT Include in Property Dialogs**:
- ❌ **Global properties** (total P-invariants, all cycles) → Goes in TopologyPanel
- ❌ **Real-time changing data** (current enablement, throughput) → Goes in DiagnosticsPanel
- ❌ **Computation-heavy analysis** (full reachability graph) → Separate tool window

---

## 5️⃣ Most Useful Tools for Biochemists

### **Priority Ranking for Biochemist Users**

Based on biochemical pathway analysis needs:

---

### **🥇 TIER 1: CRITICAL (Must Have)**

#### **1. Cycles Detection** 🔄 **[HIGHEST PRIORITY]**
**Why Critical**:
- Biochemical pathways are FULL of cycles (TCA cycle, Calvin cycle, Krebs cycle)
- Feedback loops are fundamental to metabolism
- Regulatory circuits depend on cycles
- Substrate recycling requires cycle identification

**Use Cases**:
- Identify metabolic cycles (glycolysis → pyruvate → lactate → glucose)
- Find feedback loops (product inhibition, allosteric regulation)
- Detect futile cycles (energy waste)
- Trace substrate recycling paths

**Biochemist Workflow**:
```
1. Import KEGG pathway
2. Click "Find Cycles" → Shows all cycles
3. Select cycle → Highlights on canvas
4. Analyze cycle stoichiometry
5. Check if cycle is balanced (ATP/NADH)
```

---

#### **2. Conservation Laws (P-Invariants)** 🔵 **[CRITICAL]**
**Why Critical**:
- **Mass balance** is fundamental in biochemistry
- **Cofactor conservation** (NAD+/NADH, ATP/ADP must be conserved)
- **Substrate conservation** (total metabolites must balance)
- Verify model correctness (no token creation/destruction)

**Use Cases**:
- Verify NAD+/NADH conservation (P_NAD+ + P_NADH = constant)
- Check ATP/ADP balance (P_ATP + P_ADP + P_AMP = constant)
- Validate substrate pools (total glucose derivatives = constant)
- Detect modeling errors (unexpected token creation)

**Biochemist Workflow**:
```
1. Import pathway
2. Click "P-Invariants" → Find conservation laws
3. Check: NAD+/NADH conserved? ✓
4. Check: ATP/ADP conserved? ✓
5. If not conserved → Model has error!
```

---

#### **3. Hubs (High-Degree Metabolites)** ⭐ **[CRITICAL]**
**Why Critical**:
- Central metabolites (G6P, Pyruvate, ATP) are hubs
- Understanding pathway organization
- Identify key regulatory points
- Find pathway "currency" molecules (ATP, NAD+, CoA)

**Use Cases**:
- Find central metabolites (G6P connects 5+ pathways)
- Identify cofactor hubs (ATP involved in 20+ reactions)
- Locate regulatory nodes (allosteric effectors)
- Prioritize experimental measurements (hubs have most impact)

**Biochemist Workflow**:
```
1. Import pathway
2. Click "Find Hubs" → Shows high-degree metabolites
3. ATP: degree=15 (super-hub) ← Energy currency
4. G6P: degree=12 (super-hub) ← Central branch point
5. Focus experiments on these critical metabolites
```

---

#### **4. Paths (Metabolic Routes)** 🛤️ **[CRITICAL]**
**Why Critical**:
- Find metabolic routes (glucose → pyruvate)
- Identify alternative pathways (glycolysis vs. pentose phosphate)
- Trace substrate fate (where does glucose go?)
- Critical path analysis (rate-limiting steps)

**Use Cases**:
- Shortest path: Glucose → Pyruvate (glycolysis)
- Alternative paths: Glucose → Ribose-5-P (pentose phosphate)
- Substrate tracing: Follow 14C-labeled glucose
- Bottleneck identification: Where is the slowest step?

**Biochemist Workflow**:
```
1. Select source metabolite (e.g., Glucose)
2. Select target metabolite (e.g., Pyruvate)
3. Click "Find Paths"
4. See:
   - Shortest path: Glycolysis (10 steps)
   - Alternative: Pentose phosphate → Glycolysis (15 steps)
5. Compare pathway efficiency
```

---

### **🥈 TIER 2: IMPORTANT (Should Have)**

#### **5. Boundedness Check** 📦
**Why Important**:
- Prevent metabolite accumulation to toxic levels
- Check buffer capacity (how many metabolites can accumulate)
- Validate physiological ranges (e.g., ATP: 1-10 mM)

**Use Cases**:
- Verify [ATP] doesn't exceed capacity
- Check metabolite pools are bounded
- Detect potential overflow (lactate accumulation)

---

#### **6. Communities (Functional Modules)** 👥
**Why Important**:
- Pathways are modular (glycolysis, TCA, ETC)
- Identify functional subsystems
- Understand pathway organization
- Plan experiments by module

**Use Cases**:
- Detect glycolysis module (10 enzymes)
- Find TCA cycle module (8 enzymes)
- Identify ATP synthesis module
- Analyze module interactions

---

#### **7. T-Invariants (Reproducible Cycles)** 🔶
**Why Important**:
- Verify cycle reproducibility
- Check if pathways return to initial state
- Identify minimal firing sequences

**Use Cases**:
- TCA cycle: [T1×1, T2×1, ..., T8×1] → Returns to start
- Verify cycle can repeat indefinitely
- Find minimal enzyme firings for one cycle turn

---

### **🥉 TIER 3: USEFUL (Nice to Have)**

#### **8. Centrality Measures** 🎯
**Why Useful**:
- Rank metabolite/enzyme importance
- Betweenness centrality → Which metabolites are "bridges"?
- Guide experimental design (measure critical nodes first)

---

#### **9. Deadlock Detection** 🚫
**Why Useful**:
- Find stuck states (pathway can't proceed)
- Identify substrate exhaustion points
- Prevent simulation freezes

---

#### **10. Liveness Analysis** ❤️
**Why Useful**:
- Which enzymes can fire?
- Identify dead enzymes (never fire → useless in model)
- Check pathway completeness

---

### **🔵 TIER 4: ADVANCED (For Experts)**

#### **11. SCCs (Strongly Connected Components)** 🌀
**Why Advanced**:
- Mathematical abstraction
- Not directly biochemically meaningful
- Useful for modelers, not bench scientists

---

#### **12. Siphons/Traps** 🕳️🎯
**Why Advanced**:
- Mathematical constructs
- Useful for model verification
- Not intuitive for biochemists

---

#### **13. Reachability Analysis** 🌐
**Why Advanced**:
- State space explosion
- Computationally expensive
- More useful for model checking than biochemistry

---

#### **14. DAG Analysis** 📊
**Why Advanced**:
- Most pathways are cyclic (not DAGs)
- Limited use in biochemistry
- Mainly for workflow analysis

---

#### **15. Clustering Coefficient** 🔗
**Why Advanced**:
- Abstract network metric
- Not directly actionable for biochemists

---

### **16. Network Centrality** (Already in Tier 3)

---

## 📋 Final Recommendations

### **Phase 1: Essential Biochemist Tools (4-6 weeks)**

Implement Tier 1 tools first - highest impact for biochemists:

1. **Cycles** 🔄
   - Algorithm: Johnson's (simple cycles)
   - UI: Highlight cycle on canvas
   - Export: Cycle list with stoichiometry

2. **P-Invariants** 🔵
   - Algorithm: Null space of C^T
   - UI: Show conservation laws
   - Validation: Check NAD+/NADH, ATP/ADP

3. **Hubs** ⭐
   - Algorithm: Degree centrality (already implemented!)
   - UI: Size nodes by degree
   - Highlight: Super-hubs, major hubs

4. **Paths** 🛤️
   - Algorithm: Dijkstra (shortest), BFS (all paths)
   - UI: Select source/target, show paths
   - Highlight: Shortest path on canvas

---

### **Phase 2: Important Analysis Tools (3-4 weeks)**

5. **Boundedness** 📦
6. **Communities** 👥
7. **T-Invariants** 🔶

---

### **Phase 3: Advanced Tools (2-3 weeks)**

8-15. Remaining tools as needed

---

### **Implementation Priority for Each Question**

#### **1) Diagnostic Flow Coverage**
**Answer**: Diagnostic flow covers **4/16** topology properties (25%)
- ✅ Locality, token flow, events, throughput
- ❌ Missing: Invariants, cycles, paths, hubs, etc.

**Action**: Extend diagnostic flow with topology analysis

---

#### **2) Real-Time Panel Grouping**
**Answer**: YES - Create **TopologyPanel** similar to DiagnosticsPanel
- Same structure (real-time updates, collapsible sections)
- Group by: Structural, Graph, Behavioral, Network
- Update every 500ms during simulation

**Action**: Create `src/shypn/panels/topology_panel.py`

---

#### **3) Static Properties for Dialogs**
**Answer**: Add **"Topology" tab** to property dialogs
- Place dialog: P-invariants, siphons, traps, degree, centrality
- Transition dialog: T-invariants, locality, liveness, cycles
- Arc dialog: Flow analysis, critical path status

**Action**: Extend property dialog loaders with topology tab

---

#### **4) Most Useful for Biochemists**
**Answer**: **TIER 1 (Critical)** = Top 4 tools:
1. 🥇 **Cycles** - Fundamental to metabolism
2. 🥇 **P-Invariants** - Mass balance verification
3. 🥇 **Hubs** - Central metabolites identification
4. 🥇 **Paths** - Metabolic route finding

**Action**: Implement these 4 tools first

---

## 🎯 Next Steps

### **Immediate (This Week)**:
1. ✅ Create this analysis document
2. ⬜ Review with user
3. ⬜ Prioritize: Property dialogs vs. Panel vs. Palette?
4. ⬜ Choose: Start with Cycles or P-Invariants?

### **Short-Term (Next 2 Weeks)**:
5. ⬜ Implement Tier 1 Tool #1 (user choice)
6. ⬜ Add to property dialog OR create panel
7. ⬜ Test with real KEGG pathway

### **Medium-Term (Next Month)**:
8. ⬜ Complete all Tier 1 tools
9. ⬜ Integrate with UI (palette + panel + dialogs)
10. ⬜ User testing with biochemists

---

## ✅ Summary

**Diagnostic Flow Analysis**:
- ✅ Already covers: Locality, token flow, throughput, events
- ❌ Missing: All topology properties (invariants, cycles, hubs, etc.)

**Real-Time Panel**:
- ✅ Create TopologyPanel similar to DiagnosticsPanel
- Group properties by category (Structural/Graph/Behavioral/Network)
- Update every 500ms during simulation

**Property Dialogs**:
- ✅ Add "Topology" tab to Place/Transition/Arc dialogs
- Show static topology info (invariants, cycles, centrality)
- Keep dialogs simple, move complex analysis to panel

**Biochemist Priorities**:
- 🥇 **Tier 1**: Cycles, P-Invariants, Hubs, Paths (MUST HAVE)
- 🥈 **Tier 2**: Boundedness, Communities, T-Invariants (SHOULD HAVE)
- 🥉 **Tier 3**: Centrality, Deadlocks, Liveness (NICE TO HAVE)
- 🔵 **Tier 4**: Advanced math tools (FOR EXPERTS)

**Recommended Start**: Implement **Cycles** first (highest biochemical value)

---

**Document Status**: ✅ **COMPLETE** - Ready for review and implementation  
**Date**: October 19, 2025  
**Next**: Get user feedback and start implementation
