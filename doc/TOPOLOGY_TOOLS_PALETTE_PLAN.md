# Topology Tools Palette - Comprehensive Plan

**Date**: October 19, 2025  
**Purpose**: Design topology analysis tools for Petri net/graph topological properties  
**Main Button**: "Topology" → reveals topology tools palette

---

## 📋 Executive Summary

Create a new tools palette with topological analysis capabilities for Petri nets, combining:
- **Structural Properties**: P/T-invariants, siphons, traps
- **Graph Topology**: Cycles, paths, connectivity, hubs
- **Behavioral Properties**: Liveness, boundedness, reachability, deadlocks
- **Network Analysis**: Centrality measures, clustering, communities

---

## 🎯 Tool Categories (4 Groups)

### **Category 1: Structural Analysis** (Petri Net Theory)
Traditional Petri net structural properties from formal theory

### **Category 2: Graph Topology** (Network Theory)
Graph-theoretic properties and cycle detection

### **Category 3: Behavioral Analysis** (Dynamic Properties)
Runtime behavior and state space properties

### **Category 4: Network Analysis** (Graph Centrality)
Hub detection, importance measures, community structure

---

## 🔧 Category 1: Structural Analysis Tools

### **Tool 1.1: P-Invariants (Place Invariants)**
**Button**: "P-Invariants" 🔵  
**Icon**: Circle with equals sign

**What It Does**:
- Finds linear combinations of place markings that remain constant
- Identifies conservation laws in the system
- Mathematical: Find vectors `y` where `y^T·C = 0` (C = incidence matrix)

**Why Important**:
- Verifies token conservation (e.g., total tokens = constant)
- Detects resource conservation laws
- Validates system properties

**Implementation Status**: ⚠️ Placeholder in `src/shypn/matrix/dense.py:317`

**Algorithm**:
```python
# Compute null space of C^T
# P-invariants are non-negative integer vectors y where:
# y^T · C = 0
# Use: scipy.linalg.null_space(C.T)
```

**Output Panel**:
```
P-INVARIANTS FOUND: 3

Invariant 1: P1 + P2 = 5 (token conservation)
  Places: P1 (initial=3), P2 (initial=2)
  Type: Conservation law
  
Invariant 2: P3 + P4 + P5 = 10 (resource pool)
  Places: P3, P4, P5
  Type: Resource conservation
  
Invariant 3: P6 = 1 (singleton)
  Places: P6
  Type: Mutex/binary place
```

**Visualization**:
- Highlight places in same invariant with same color
- Show conservation equation on canvas
- Group places visually

---

### **Tool 1.2: T-Invariants (Transition Invariants)**
**Button**: "T-Invariants" 🔶  
**Icon**: Square with circular arrow

**What It Does**:
- Finds firing sequences that return to initial marking
- Identifies reproducible behaviors (cycles)
- Mathematical: Find vectors `x` where `C·x = 0`

**Why Important**:
- Verifies system can repeat behaviors
- Identifies cyclic processes
- Checks for reproducibility

**Implementation Status**: ⚠️ Placeholder in `src/shypn/matrix/dense.py:317`

**Algorithm**:
```python
# Compute null space of C
# T-invariants are non-negative integer vectors x where:
# C · x = 0
# Use: scipy.linalg.null_space(C)
```

**Output Panel**:
```
T-INVARIANTS FOUND: 2

Invariant 1: [T1×2, T2×1, T3×1] → Returns to initial state
  Firing sequence: T1 → T1 → T2 → T3
  Tokens consumed: 10
  Tokens produced: 10
  Type: Production cycle
  
Invariant 2: [T4×1, T5×1] → Simple cycle
  Firing sequence: T4 → T5
  Type: Feedback loop
```

**Visualization**:
- Animate firing sequence on canvas
- Highlight transitions in invariant
- Show cycle as directed path

---

### **Tool 1.3: Siphons**
**Button**: "Siphons" 🕳️  
**Icon**: Downward spiral

**What It Does**:
- Finds sets of places that, once empty, remain empty forever
- Identifies potential deadlock causes
- Critical for liveness analysis

**Why Important**:
- **Deadlock Detection**: Empty siphon → potential deadlock
- **Resource Starvation**: Identifies where resources can get stuck
- **Liveness Verification**: Must ensure siphons never empty

**Mathematical Definition**:
```
A set of places S is a siphon if:
∀p ∈ S: •p ⊆ S• (all input transitions also output to S)

Translation: If all places in S are empty, no transition can add tokens
```

**Algorithm**:
```python
# For each subset S of places:
#   Check if ∀p ∈ S: preset(p) ⊆ postset(S)
#   If yes → S is a siphon
# Return minimal siphons (not contained in others)
```

**Output Panel**:
```
SIPHONS FOUND: 2

Siphon 1: {P1, P3, P5} (CRITICAL)
  Size: 3 places
  Current marking: P1=0, P3=0, P5=0 ⚠️ EMPTY!
  Status: ⚠️ DEADLOCK RISK
  Reason: All input transitions (T1, T2) require tokens from siphon
  
Siphon 2: {P7, P8}
  Size: 2 places
  Current marking: P7=5, P8=3 ✓ Safe
  Status: ✓ Currently marked
```

**Visualization**:
- Highlight siphon places in red (if empty) or yellow (if marked)
- Draw bounding box around siphon
- Show transitions that can't fire due to empty siphon

---

### **Tool 1.4: Traps**
**Button**: "Traps" 🎯  
**Icon**: Target symbol

**What It Does**:
- Finds sets of places that, once marked, stay marked forever
- Identifies resource accumulation points
- Dual concept to siphons

**Why Important**:
- **Safety Analysis**: Tokens can accumulate here
- **Buffer Overflow Detection**: Places that grow unbounded
- **Resource Accumulation**: Where resources get "trapped"

**Mathematical Definition**:
```
A set of places S is a trap if:
∀p ∈ S: S• ⊆ •p (all output transitions also input from S)

Translation: If any place in S has tokens, S will always have tokens
```

**Output Panel**:
```
TRAPS FOUND: 2

Trap 1: {P2, P4, P6}
  Size: 3 places
  Current marking: P2=8, P4=12, P6=5
  Status: ✓ Marked (will stay marked)
  Growth: +3 tokens/step (accumulating!)
  
Trap 2: {P9, P10}
  Size: 2 places
  Current marking: P9=0, P10=0
  Status: Empty (safe)
```

**Visualization**:
- Highlight trap places in green
- Show token accumulation trend (arrow up/down)
- Draw bounding box

---

## 🔧 Category 2: Graph Topology Tools

### **Tool 2.1: Cycles**
**Button**: "Find Cycles" 🔄  
**Icon**: Circular arrow

**What It Does**:
- Finds all cycles in the Petri net graph
- Identifies feedback loops and circular dependencies
- Shows cycle structure (simple cycles, nested cycles)

**Why Important**:
- **Control Flow**: Loops in process
- **Resource Circulation**: Tokens flow in circles
- **Deadlock Analysis**: Cycles can cause circular waits

**Algorithm**:
```python
# Use: networkx.simple_cycles(graph)
# Or: Johnson's algorithm for finding all elementary circuits
# For each cycle:
#   - Length
#   - Node types (places/transitions)
#   - Token flow direction
```

**Output Panel**:
```
CYCLES FOUND: 5

Cycle 1: [P1 → T1 → P2 → T2 → P1] (Length: 4)
  Type: Simple cycle
  Direction: Clockwise
  Token flow: 2 tokens/cycle
  Period: ~3.5 seconds
  
Cycle 2: [P3 → T3 → P4 → T4 → P5 → T5 → P3] (Length: 6)
  Type: Production loop
  Nested in: None
  
Cycle 3: [T6 → P6 → T7 → P7 → T6] (Length: 4)
  Type: Feedback loop
  Contains: 2 transitions, 2 places
```

**Visualization**:
- Highlight each cycle in different color
- Animate token flow around cycle
- Show cycle direction with arrows
- Group overlapping cycles

**Interactive**:
- Click cycle to zoom/focus
- Show only specific cycle
- Compare cycles side-by-side

---

### **Tool 2.2: Paths & Connectivity**
**Button**: "Paths" 🛤️  
**Icon**: Winding path

**What It Does**:
- Finds paths between selected nodes
- Analyzes connectivity (strongly/weakly connected components)
- Identifies shortest/longest paths
- Detects unreachable nodes

**Features**:
1. **Shortest Path**: P1 → ... → P10
2. **All Paths**: Show all possible paths
3. **Longest Path**: Critical path analysis
4. **Reachability**: What's reachable from P1?
5. **Components**: Connected subgraphs

**Output Panel**:
```
PATH ANALYSIS: P1 → P10

Shortest Path (length: 5):
  P1 → T1 → P3 → T5 → P8 → T9 → P10
  Expected time: 4.2 seconds
  
Alternative Paths: 3 found
  Path 2 (length: 7): P1 → T2 → P4 → ...
  Path 3 (length: 6): P1 → T1 → P2 → ...
  
Unreachable Nodes: 2
  - P15 (isolated)
  - T20 (no incoming arcs)
  
Connected Components: 3
  Component 1: 45 nodes (main network)
  Component 2: 5 nodes (isolated subnet)
  Component 3: 1 node (P15 isolated)
```

**Visualization**:
- Highlight path with thick colored line
- Fade non-path nodes
- Show alternative paths in different colors

---

### **Tool 2.3: SCCs (Strongly Connected Components)**
**Button**: "SCCs" 🌀  
**Icon**: Nested circles

**What It Does**:
- Finds strongly connected components (every node reaches every other)
- Identifies tightly coupled subnetworks
- Shows hierarchical structure (SCC tree)

**Why Important**:
- **Modularity**: Natural boundaries in system
- **Cycle Structure**: Where cycles exist
- **Hierarchy**: Dependency structure

**Existing Implementation**: ✅ `src/shypn/layout/sscc/scc_detector.py`

**Algorithm**:
```python
# Already implemented!
# Tarjan's algorithm in scc_detector.py
# Returns: List of SCCs with metadata
```

**Output Panel**:
```
STRONGLY CONNECTED COMPONENTS: 7 found

SCC 1 (Largest): 25 nodes
  Places: 15, Transitions: 10
  Type: Main production cycle
  Internal cycles: 3
  Connections: Inputs from SCC 2, 3
  
SCC 2: 8 nodes
  Places: 5, Transitions: 3
  Type: Input preprocessing
  Connections: Feeds SCC 1
  
SCC 3: 12 nodes
  Places: 7, Transitions: 5
  Type: Output processing
  Connections: Receives from SCC 1
  
Trivial SCCs: 4 (single nodes)
```

**Visualization**:
- Draw boundary around each SCC
- Color code by size/importance
- Show connections between SCCs (condensation graph)
- Hierarchical layout (SCCs as nodes)

---

### **Tool 2.4: DAG Analysis**
**Button**: "DAG Check" 📊  
**Icon**: Hierarchical tree

**What It Does**:
- Checks if graph is a Directed Acyclic Graph (no cycles)
- If not DAG: identifies feedback arcs to remove
- Computes topological ordering
- Finds layers (hierarchical structure)

**Why Important**:
- **Workflow Analysis**: Is process hierarchical?
- **Dependency Analysis**: Can we order operations?
- **Critical Path**: Longest path in DAG

**Algorithm**:
```python
# 1. Check: nx.is_directed_acyclic_graph(graph)
# 2. If not DAG: Find feedback arcs
# 3. Compute topological sort
# 4. Assign layers (longest path from sources)
```

**Output Panel**:
```
DAG ANALYSIS:

Status: ❌ NOT a DAG (contains cycles)

Feedback Arcs (to remove for DAG): 3
  1. T5 → P3 (closes cycle of length 4)
  2. T12 → P8 (closes cycle of length 6)
  3. T15 → P10 (closes cycle of length 3)
  
If removing feedback arcs:
  - Becomes DAG ✓
  - Topological order: P1, T1, P2, T2, ...
  - Layers: 8 levels
  - Critical path: P1 → ... → P25 (length: 15)
  
Original Graph:
  - Cycles: 5
  - Longest cycle: 8 nodes
```

**Visualization**:
- Highlight feedback arcs in red
- Show layers/levels vertically
- Display topological order
- Compare cyclic vs acyclic view

---

## 🔧 Category 3: Behavioral Analysis Tools

### **Tool 3.1: Liveness Analysis**
**Button**: "Liveness" ❤️  
**Icon**: Heart with pulse

**What It Does**:
- Classifies transitions by liveness level (L0-L4)
- Identifies dead transitions (L0) - never fire
- Identifies live transitions (L4) - can always fire

**Liveness Levels** (Murata 1989):
- **L0 (Dead)**: Never fires
- **L1**: Can fire at least once
- **L2**: Can fire arbitrarily often (from some state)
- **L3**: Can fire arbitrarily often (from any reachable state)
- **L4 (Live)**: Can fire immediately from any reachable state

**Output Panel**:
```
LIVENESS ANALYSIS:

L4 (Live): 5 transitions ✓
  - T1: Always enabled
  - T3: Always enabled
  - T5, T7, T9
  
L3 (Potentially live): 8 transitions
  - T2: Can fire often
  - T4, T6, T8, T10, T11, T12, T13
  
L2 (Weakly live): 3 transitions
  - T14: Can fire from initial state
  - T15, T16
  
L1 (Eventually dead): 2 transitions ⚠️
  - T17: Can fire once, then deadlocks
  - T18
  
L0 (Dead): 1 transition ❌
  - T19: Never enabled (missing input place tokens)
```

**Visualization**:
- Color code transitions by liveness:
  - Green: L4 (live)
  - Yellow: L3 (potentially live)
  - Orange: L2 (weakly live)
  - Red: L1 (eventually dead)
  - Dark red: L0 (dead)

---

### **Tool 3.2: Boundedness Check**
**Button**: "Boundedness" 📦  
**Icon**: Box with limit line

**What It Does**:
- Checks if places have bounded token capacity
- Identifies k-bounded places (max k tokens)
- Detects unbounded places (can grow infinitely)
- Verifies safety (1-bounded)

**Why Important**:
- **Resource Limits**: Buffer capacity
- **Memory Safety**: Prevent overflow
- **System Stability**: Bounded behavior

**Algorithm**:
```python
# Reachability analysis:
# 1. Explore all reachable markings
# 2. Track max tokens per place
# 3. Detect unbounded (tokens grow without limit)
# Use: Coverability tree for unbounded nets
```

**Output Panel**:
```
BOUNDEDNESS ANALYSIS:

Safe (1-bounded): 12 places ✓
  P1, P2, P3, P5, P7, P9, P10, P12, P15, P18, P20, P22
  Type: Binary/mutex places
  
k-Bounded: 8 places
  P4: 5-bounded (max 5 tokens)
  P6: 3-bounded (max 3 tokens)
  P8: 10-bounded (max 10 tokens)
  P11, P13, P14, P16, P17
  
Unbounded: 2 places ⚠️
  P19: Unbounded (grows without limit)
    Reason: Production > consumption
  P21: Unbounded
    Reason: Accumulator pattern
```

**Visualization**:
- Show max capacity bar above place
- Color code:
  - Green: Safe (1-bounded)
  - Blue: k-bounded
  - Red: Unbounded
- Show token growth trend (arrow up)

---

### **Tool 3.3: Reachability Analysis**
**Button**: "Reachability" 🌐  
**Icon**: Network of connected dots

**What It Does**:
- Computes reachability set (all reachable markings)
- Generates reachability graph (state space)
- Checks if specific marking is reachable
- Analyzes state space size/complexity

**Why Important**:
- **Verification**: Can we reach desired state?
- **Model Checking**: Verify properties
- **State Space**: Understand system complexity

**Algorithm**:
```python
# BFS/DFS from initial marking:
# 1. Start with M0
# 2. For each enabled transition:
#    a. Fire transition → M'
#    b. If M' new, add to reachable set
#    c. Recurse
# 3. Build graph of M → M' edges
```

**Output Panel**:
```
REACHABILITY ANALYSIS:

Initial Marking: M0 = {P1=1, P2=0, P3=0, ...}

Reachable Markings: 247 states
  Safe states: 230 (93%)
  Deadlocked states: 5 (2%)
  Goal states reached: 12 (5%)
  
State Space Properties:
  Diameter: 15 (max distance between states)
  Average degree: 3.2 (transitions per state)
  Cyclic: Yes (127 cycles found)
  
Specific Query: "Can we reach {P10=5, P15=3}?"
  Answer: ✓ YES (reachable in 8 steps)
  Path: M0 → M5 → M12 → ... → M_goal
```

**Visualization**:
- Reachability graph (nodes = markings, edges = transitions)
- Highlight path to goal marking
- Show clusters of similar states
- Interactive exploration (click state to see details)

---

### **Tool 3.4: Deadlock Detection**
**Button**: "Deadlocks" 🚫  
**Icon**: Stop sign

**What It Does**:
- Finds markings where no transitions are enabled
- Identifies partial deadlocks (some transitions stuck)
- Analyzes deadlock causes (resource conflicts)
- Suggests fixes (add tokens, remove arcs)

**Types of Deadlocks**:
1. **Total Deadlock**: No transitions enabled
2. **Partial Deadlock**: Some transitions never enable
3. **Livelock**: Infinite loop without progress

**Algorithm**:
```python
# From reachability analysis:
# 1. Find states with no enabled transitions
# 2. Analyze why (insufficient tokens, conflicts)
# 3. Trace path to deadlock
# 4. Identify resource dependencies
```

**Output Panel**:
```
DEADLOCK ANALYSIS:

Total Deadlocks: 3 states found ❌

Deadlock 1: M_47 = {P1=0, P3=0, P5=2, ...}
  Enabled transitions: None
  Cause: Circular wait (T1 waits for P1, T3 waits for P3)
  Path to deadlock: M0 → M12 → M31 → M47 (15 steps)
  Fix suggestion: Add token to P1 or P3
  
Deadlock 2: M_103 = {P8=0, P10=0, ...}
  Cause: Resource exhaustion (empty siphon)
  
Partial Deadlocks: 12 states
  - T5 never enables in states M_23, M_56, ...
  - T12 never enables in states M_89, M_102, ...
  
Livelocks: 1 detected
  - Cycle: M_150 → M_151 → M_152 → M_150
    Transitions fire: T8, T9, T10 (infinite loop)
    No progress: Output place P25 never reached
```

**Visualization**:
- Highlight deadlock states in reachability graph
- Show resource dependency chains
- Mark transitions involved in deadlock
- Suggest fixes with green highlights

---

## 🔧 Category 4: Network Analysis Tools

### **Tool 4.1: Hub Detection**
**Button**: "Hubs" ⭐  
**Icon**: Star with connections

**What It Does**:
- Identifies high-degree nodes (hubs)
- Classifies: Super-hubs, Major hubs, Minor hubs
- Shows hub statistics and roles

**Existing Implementation**: ✅ `src/shypn/layout/sscc/hub_mass_assigner.py`

**Hub Classification**:
- **Super-hub**: Degree ≥ 8 (mass = 1000)
- **Major hub**: Degree ≥ 5 (mass = 500)
- **Minor hub**: Degree ≥ 3 (mass = 100)
- **Regular**: Degree < 3 (mass = 10)

**Output Panel**:
```
HUB ANALYSIS:

Super-Hubs (degree ≥ 8): 2 found ⭐⭐⭐
  P5 "Glucose-6-phosphate": degree=12
    Connected to: 12 transitions
    Role: Central metabolite
    Importance: CRITICAL
    
  P18 "ATP": degree=15
    Connected to: 15 transitions
    Role: Energy currency
    Importance: CRITICAL
    
Major Hubs (degree ≥ 5): 5 found ⭐⭐
  P3, P8, P12, P15, P22
  
Minor Hubs (degree ≥ 3): 8 found ⭐
  P1, P4, P7, P9, P11, P13, P16, P19
  
Regular Nodes: 32
  Degree: 1-2 connections
```

**Visualization**:
- Size nodes by degree (bigger = more connections)
- Color code by hub class
- Show connections radiating from hub
- Highlight hub neighborhoods

---

### **Tool 4.2: Centrality Measures**
**Button**: "Centrality" 🎯  
**Icon**: Target with center dot

**What It Does**:
- Computes centrality metrics for nodes
- Identifies most "important" nodes
- Multiple centrality types (degree, betweenness, closeness, eigenvector)

**Centrality Types**:

1. **Degree Centrality**: How many connections?
   ```python
   DC(v) = degree(v) / (n - 1)
   ```

2. **Betweenness Centrality**: How many shortest paths pass through?
   ```python
   BC(v) = Σ(σ_st(v) / σ_st)
   # σ_st = # shortest paths from s to t
   # σ_st(v) = # paths passing through v
   ```

3. **Closeness Centrality**: How close to all others?
   ```python
   CC(v) = (n - 1) / Σ(distance(v, u))
   ```

4. **Eigenvector Centrality**: Importance of neighbors?
   ```python
   # Recursive: Important if connected to important nodes
   ```

**Output Panel**:
```
CENTRALITY ANALYSIS:

Top 10 by Degree Centrality:
  1. P18 "ATP": 0.312 (15 connections)
  2. P5 "G6P": 0.250 (12 connections)
  3. P12 "NADH": 0.187 (9 connections)
  ...
  
Top 10 by Betweenness Centrality:
  1. P5 "G6P": 0.421 (critical pathway junction)
  2. T3 "PFK": 0.389 (rate-limiting step)
  3. P8 "F6P": 0.305
  ...
  
Top 10 by Closeness Centrality:
  1. P5: 0.678 (central location)
  2. P12: 0.623
  3. P15: 0.587
  ...
```

**Visualization**:
- Color nodes by centrality (red = high, blue = low)
- Size nodes by centrality score
- Show heatmap overlay
- Compare multiple centrality measures side-by-side

---

### **Tool 4.3: Community Detection**
**Button**: "Communities" 👥  
**Icon**: Group of connected circles

**What It Does**:
- Finds groups of tightly connected nodes (communities/modules)
- Identifies functional modules in network
- Shows community structure and boundaries

**Why Important**:
- **Modularity**: Natural functional units
- **Hierarchical Organization**: Nested communities
- **Subsystem Identification**: Related components

**Algorithms**:
- Louvain method (fast, hierarchical)
- Girvan-Newman (edge betweenness)
- Label propagation (fast, approximate)

**Output Panel**:
```
COMMUNITY DETECTION (Louvain):

Communities Found: 5

Community 1: "Glycolysis" (18 nodes)
  Places: 12, Transitions: 6
  Modularity: 0.82 (strong internal connections)
  Function: Glucose breakdown pathway
  Key nodes: P1 (Glucose), P5 (G6P), T2 (HK)
  
Community 2: "TCA Cycle" (15 nodes)
  Places: 9, Transitions: 6
  Modularity: 0.75
  Function: Aerobic respiration
  
Community 3: "ATP Synthesis" (8 nodes)
  Places: 5, Transitions: 3
  Modularity: 0.68
  Cross-community links: 12 (connects to all others)
  
Community 4: "NADH Recycling" (6 nodes)
Community 5: "Regulation" (4 nodes)

Modularity Score: 0.73 (good community structure)
```

**Visualization**:
- Color code communities
- Draw boundaries around communities
- Show inter-community connections (dashed lines)
- Hierarchical view (communities as super-nodes)

---

### **Tool 4.4: Clustering Coefficient**
**Button**: "Clustering" 🔗  
**Icon**: Interconnected triangles

**What It Does**:
- Measures how much nodes cluster together
- Identifies tightly knit groups
- Computes local and global clustering coefficients

**Why Important**:
- **Network Density**: How interconnected?
- **Robustness**: Clustered networks more robust
- **Small-World Property**: High clustering + short paths

**Clustering Coefficient**:
```python
# Local clustering (for node v):
C(v) = (# triangles involving v) / (# possible triangles)

# Global clustering:
C_global = average of C(v) for all v
```

**Output Panel**:
```
CLUSTERING ANALYSIS:

Global Clustering Coefficient: 0.42
  Interpretation: Moderately clustered network
  
Local Clustering (Top 10):
  1. P5: 0.87 (highly clustered neighborhood)
  2. P12: 0.79
  3. T5: 0.72
  ...
  
Triangles Found: 47
  Largest clique: {P5, P8, T3, T5} (size 4)
  
Network Type: Small-world
  Clustering: High (0.42 > random network)
  Path length: Short (avg = 4.2)
```

**Visualization**:
- Highlight triangles (3-node cycles)
- Show cliques (fully connected subgraphs)
- Color by local clustering coefficient
- Compare to random network

---

## 🎨 UI Design & Integration

### **Main Button: "Topology"**
Location: Tools palette (next to existing tools)
Icon: Network graph with nodes and edges
Action: Opens topology tools sub-palette (flyout)

---

### **Tools Sub-Palette Layout**

```
┌─────────────────────────────────────────┐
│        TOPOLOGY TOOLS PALETTE           │
├─────────────────────────────────────────┤
│                                         │
│  📊 STRUCTURAL ANALYSIS                 │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │
│  │  🔵  │ │  🔶  │ │ 🕳️   │ │  🎯  │  │
│  │ P-Inv│ │ T-Inv│ │Siphon│ │ Trap │  │
│  └──────┘ └──────┘ └──────┘ └──────┘  │
│                                         │
│  🔄 GRAPH TOPOLOGY                      │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │
│  │  🔄  │ │  🛤️  │ │  🌀  │ │  📊  │  │
│  │Cycles│ │Paths │ │ SCCs │ │ DAG  │  │
│  └──────┘ └──────┘ └──────┘ └──────┘  │
│                                         │
│  ⚡ BEHAVIORAL ANALYSIS                 │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │
│  │  ❤️  │ │  📦  │ │  🌐  │ │  🚫  │  │
│  │ Live │ │Bound │ │Reach │ │Dead  │  │
│  └──────┘ └──────┘ └──────┘ └──────┘  │
│                                         │
│  🌐 NETWORK ANALYSIS                    │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │
│  │  ⭐  │ │  🎯  │ │  👥  │ │  🔗  │  │
│  │ Hubs │ │Center│ │Commun│ │Clust │  │
│  └──────┘ └──────┘ └──────┘ └──────┘  │
│                                         │
└─────────────────────────────────────────┘
```

---

### **Results Panel**

Location: Right sidebar (like existing analysis panels)

Layout:
```
┌─────────────────────────────────────────┐
│   TOPOLOGY ANALYSIS RESULTS             │
├─────────────────────────────────────────┤
│ Tool: P-Invariants                 [×]  │
├─────────────────────────────────────────┤
│                                         │
│  Invariants Found: 3                    │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Invariant 1: P1 + P2 = 5       │   │
│  │   Places: P1, P2                │   │
│  │   [Highlight]  [Details]        │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Invariant 2: P3 + P4 + P5 = 10 │   │
│  │   Places: P3, P4, P5            │   │
│  │   [Highlight]  [Details]        │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Export] [Print] [Close]              │
└─────────────────────────────────────────┘
```

---

### **Canvas Visualization**

Overlay analysis results on canvas:
- **Highlight**: Selected objects in color
- **Annotations**: Show equations, values
- **Paths**: Draw colored paths/cycles
- **Boundaries**: Draw boxes around groups
- **Arrows**: Show flow direction
- **Labels**: Add text annotations

Example: P-Invariant visualization
```
     ┌─────────────────────┐
     │  P1 + P2 = 5        │  ← Annotation
     └─────────────────────┘
            │
     ┌──────▼──────┐
     │   ⭕ P1     │  ← Highlighted in blue
     │  Tokens: 3  │
     └─────────────┘
            │
            │ T1
            ▼
     ┌─────────────┐
     │   ⭕ P2     │  ← Highlighted in blue
     │  Tokens: 2  │
     └─────────────┘
```

---

## 📐 Implementation Architecture

### **Phase 1: Foundation** (2-3 weeks)

**Files to Create**:
```
src/shypn/topology/
    __init__.py
    base_analyzer.py          # Base class for all analyzers
    
    structural/
        __init__.py
        p_invariants.py       # P-invariant computation
        t_invariants.py       # T-invariant computation
        siphons.py            # Siphon detection
        traps.py              # Trap detection
    
    graph/
        __init__.py
        cycles.py             # Cycle detection
        paths.py              # Path finding
        sccs.py               # SCC wrapper (use existing)
        dag_analysis.py       # DAG checking
    
    behavioral/
        __init__.py
        liveness.py           # Liveness analysis
        boundedness.py        # Boundedness checking
        reachability.py       # Reachability analysis
        deadlock.py           # Deadlock detection
    
    network/
        __init__.py
        hubs.py               # Hub detection (use existing)
        centrality.py         # Centrality measures
        community.py          # Community detection
        clustering.py         # Clustering coefficient

ui/palettes/
    topology_palette.ui       # Glade file for palette

src/shypn/helpers/
    topology_palette_loader.py  # Loader for palette

src/shypn/panels/
    topology_results_panel.py   # Results display panel
```

---

### **Phase 2: UI Integration** (1-2 weeks)

1. **Create Topology Button**:
   - Add to tools palette
   - Icon: Network graph
   - Opens flyout sub-palette

2. **Create Sub-Palette**:
   - 4x4 grid of tool buttons
   - Organized by category
   - Tooltips on hover

3. **Results Panel**:
   - Right sidebar panel
   - Tree view for results
   - Interactive highlighting
   - Export functionality

---

### **Phase 3: Analysis Algorithms** (3-4 weeks)

**Priority Order**:

1. **Week 1**: Structural Analysis
   - P/T-invariants (linear algebra)
   - Siphons/traps (subset enumeration)

2. **Week 2**: Graph Topology
   - Cycles (Johnson's algorithm)
   - Paths (Dijkstra, BFS)
   - SCCs (integrate existing)
   - DAG (topological sort)

3. **Week 3**: Behavioral Analysis
   - Liveness (reachability-based)
   - Boundedness (coverability tree)
   - Reachability (BFS/DFS)
   - Deadlock (state space analysis)

4. **Week 4**: Network Analysis
   - Hubs (integrate existing)
   - Centrality (NetworkX wrappers)
   - Community (Louvain)
   - Clustering (triangle counting)

---

### **Phase 4: Visualization** (1-2 weeks)

1. **Canvas Overlays**:
   - Highlight selected objects
   - Draw annotations
   - Show paths/cycles
   - Animate sequences

2. **Results Display**:
   - Tree view for hierarchical results
   - Tables for metrics
   - Charts for distributions
   - Interactive filtering

---

## 📚 Dependencies & Libraries

### **Required**:
- ✅ **NumPy**: Matrix operations (already used)
- ✅ **SciPy**: Linear algebra (null space computation)
- ✅ **NetworkX**: Graph algorithms (already used)

### **Optional**:
- **python-igraph**: Fast community detection
- **scikit-learn**: Clustering algorithms
- **matplotlib**: Result visualization

### **Installation**:
```bash
# Already have:
pip install numpy scipy networkx

# Optional:
pip install python-igraph scikit-learn
```

---

## 🎯 Success Metrics

### **Functionality**:
- ✅ All 16 tools implemented
- ✅ Results displayed correctly
- ✅ Visualization working
- ✅ Export functionality

### **Performance**:
- P/T-invariants: < 5 seconds for 100 places
- Cycles: < 2 seconds for 200 nodes
- Reachability: < 10 seconds for 1000 states
- Centrality: < 3 seconds for 500 nodes

### **Usability**:
- One-click analysis
- Clear result presentation
- Interactive visualization
- Helpful tooltips

---

## 🔬 Testing Strategy

### **Unit Tests**:
```python
tests/topology/
    test_p_invariants.py
    test_t_invariants.py
    test_siphons.py
    test_traps.py
    test_cycles.py
    test_paths.py
    test_liveness.py
    test_boundedness.py
    test_centrality.py
    test_community.py
```

### **Test Models**:
- Simple chain (P1 → T1 → P2 → ...)
- Cycle (P1 → T1 → P2 → T2 → P1)
- Deadlock-prone model
- Unbounded model
- Complex KEGG pathway

---

## 📖 References

### **Petri Net Theory**:
1. **Murata, T. (1989)**: "Petri Nets: Properties, Analysis and Applications"
   - P/T-invariants, siphons, traps, liveness, boundedness

2. **Reisig, W. (2013)**: "Understanding Petri Nets"
   - Reachability, deadlock detection

### **Graph Theory**:
3. **Newman, M. (2010)**: "Networks: An Introduction"
   - Centrality, clustering, community detection

4. **Tarjan, R. (1972)**: "Depth-first search and linear graph algorithms"
   - SCC detection

### **Algorithms**:
5. **Johnson, D. B. (1975)**: "Finding all the elementary circuits of a directed graph"
   - Cycle enumeration

6. **Blondel, V. D. et al. (2008)**: "Fast unfolding of communities in large networks"
   - Louvain method for community detection

---

## ✅ Next Steps

### **Immediate (This Week)**:
1. ✅ Create this plan document
2. ⬜ Review with team
3. ⬜ Prioritize tools (which to implement first?)
4. ⬜ Design UI mockups

### **Short-term (Next 2 Weeks)**:
5. ⬜ Create directory structure
6. ⬜ Implement base_analyzer.py
7. ⬜ Start with P/T-invariants (high priority)
8. ⬜ Create basic UI palette

### **Medium-term (Next Month)**:
9. ⬜ Implement all 16 tools
10. ⬜ Complete UI integration
11. ⬜ Add visualization
12. ⬜ Write tests

### **Long-term (Next 2-3 Months)**:
13. ⬜ Polish UX
14. ⬜ Optimize performance
15. ⬜ Add export features
16. ⬜ User documentation

---

## 🎉 Summary

**Total Tools**: 16 (4 categories × 4 tools each)

**Categories**:
1. **Structural Analysis**: P/T-invariants, Siphons, Traps
2. **Graph Topology**: Cycles, Paths, SCCs, DAG
3. **Behavioral Analysis**: Liveness, Boundedness, Reachability, Deadlock
4. **Network Analysis**: Hubs, Centrality, Communities, Clustering

**Estimated Effort**: 7-11 weeks total
- Foundation: 2-3 weeks
- UI: 1-2 weeks
- Algorithms: 3-4 weeks
- Visualization: 1-2 weeks

**Key Technologies**:
- NumPy/SciPy for linear algebra
- NetworkX for graph algorithms
- GTK for UI
- Matplotlib for visualization

**Status**: ✅ **PLAN COMPLETE** - Ready for implementation!

---

**Document Version**: 1.0  
**Date**: October 19, 2025  
**Author**: AI Assistant (GitHub Copilot)  
**Status**: Planning Phase - Awaiting Approval
