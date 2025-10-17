# Force-Directed Layout with SCC Post-Processing - Executive Summary

## The Vision: Solar System Layout

Transform chaotic Petri net models into structured, hierarchical layouts using **strongly-connected components (SCCs)** as gravitational centers.

```
   BEFORE: Random/Manual              AFTER: Solar System
   
   T1  P1  P2  T2                         Satellites
                                              ↓
   P3  T3  P4  T4              Moon → Planet → ⭐ Star ← Planet ← Moon
                                              ↑
   P5  T5  P6  T6                         Satellites
   
   (Chaotic)                          (Structured Hierarchy)
```

## Core Concept

**Strongly Connected Component (SCC):**
- Maximal subgraph where every node can reach every other node
- In Petri nets: Feedback loops, resource cycles, core functional units
- Represents **structural importance**

**Solar System Metaphor:**
- **Star** = Largest/most connected SCC (center)
- **Planets** = Medium SCCs (orbit star)
- **Moons** = Small SCCs (orbit planets)
- **Satellites** = Single nodes (orbit nearest SCC)

## Algorithm Pipeline

```
┌──────────────────────────────────────────────────┐
│ 1. BUILD GRAPH                                    │
│    Input: Places, Transitions, Arcs              │
│    Output: Directed graph (adjacency list)       │
└────────────────────┬─────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────┐
│ 2. DETECT SCCs (Tarjan's Algorithm)              │
│    Find strongly connected components            │
│    Complexity: O(V + E)                          │
└────────────────────┬─────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────┐
│ 3. RANK SCCs                                      │
│    Criteria: size + connectivity + centrality    │
│    Output: Hierarchical levels (0=star, 1,2,3...)│
└────────────────────┬─────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────┐
│ 4. FORCE-DIRECTED LAYOUT (Fruchterman-Reingold) │
│    Classic spring-electrical model               │
│    Output: Aesthetic initial positions           │
└────────────────────┬─────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────┐
│ 5. ORBITAL POST-PROCESSING ✨                     │
│    Constrain SCCs to orbital rings               │
│    Preserve internal SCC structure               │
│    Output: Structured solar system layout        │
└────────────────────┬─────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────┐
│ 6. APPLY TO CANVAS                                │
│    Update node coordinates, trigger redraw       │
└──────────────────────────────────────────────────┘
```

## Key Innovation

**Traditional Force-Directed:**
- ✅ Aesthetically pleasing
- ✅ Minimizes edge crossings
- ❌ No semantic structure
- ❌ Important nodes scattered
- ❌ Hard to understand large models

**Our SCC-Based Approach:**
- ✅ Aesthetically pleasing (keeps force-directed beauty)
- ✅ Minimizes edge crossings
- ✅ **Semantic hierarchy** (structure reflects importance)
- ✅ **Important SCCs at center** (visual focus)
- ✅ **Scalable** (large models decompose into regions)

## Technical Architecture

### Components

```
AutoLayoutManager (Orchestrator)
    ├── GraphAnalyzer
    │   ├── build_adjacency_list()
    │   ├── find_sccs() → SCCDetector (Tarjan)
    │   └── rank_components() → ComponentRanker
    │
    └── LayoutEngine
        ├── ForceSimulator (Fruchterman-Reingold)
        └── OrbitPostProcessor (Solar System)
```

### Integration Points

1. **Context Menu**: Right-click → Auto Layout → Solar System (SCC)
2. **Dialog**: Configure force parameters + orbital spacing
3. **Canvas**: Apply computed positions to nodes
4. **Undo/Redo**: Command pattern for reversibility

## Example: Biological Pathway

```
Before (Manual):                After (Solar System):

  ATP                              NADH
   ↓                                ↓
  P1 → T1 → P2                   [Enzyme]
            ↓                        ↓
           T2                    [Cycle] ⭐ ← [Substrate]
            ↓                        ↑
  P3 ← T3 ← P4                   [Product]
   ↑                                ↑
  ADP                              NAD+

(Linear, unclear)           (Circular feedback visible)
```

## Benefits

**For Users:**
- 🎯 **One-click layout**: No manual positioning
- 🧭 **Visual clarity**: Structure reflects semantics
- 📊 **Scalability**: Works on 10-1000 node models
- 🎨 **Professional**: Publication-ready diagrams

**For System:**
- ⚡ **Fast**: O(V + E) SCC detection
- 🔧 **Extensible**: Easy to add other layout algorithms
- 🧪 **Testable**: Unit tests for each component
- 🔄 **Reversible**: Full undo/redo support

## Implementation Phases

**Phase 1 (Week 1-2):** SCC Detection
- Graph construction + Tarjan's algorithm
- Unit tests

**Phase 2 (Week 3-4):** Force Simulation
- Fruchterman-Reingold implementation
- Basic layout working

**Phase 3 (Week 5-6):** Orbital Post-Processing
- Solar system constraints
- Visual testing

**Phase 4 (Week 7):** UI Integration
- Context menu + dialog
- Wire to canvas

**Phase 5 (Week 8):** Polish
- Animation + optimization
- Production ready

## Success Criteria

**Performance:**
- < 5 seconds for 100-node graph
- < 60 seconds for 1000-node graph

**Quality:**
- < 5% edge crossings (compared to random)
- Clear hierarchical structure visible
- Stable/reproducible results

**User Satisfaction:**
- 80%+ prefer over manual layout
- Intuitive without training
- "Makes complex models understandable"

## Comparison to Alternatives

| Algorithm | Aesthetic | Hierarchical | Speed | Use Case |
|-----------|-----------|--------------|-------|----------|
| Random | ❌ Poor | ❌ None | ⚡ Fast | None |
| Grid | ✓ Neat | ❌ None | ⚡ Fast | Simple diagrams |
| Force-Directed | ✅ Great | ❌ None | ⚙️ Medium | General graphs |
| Hierarchical | ✓ Good | ✅ Tree-like | ⚙️ Medium | Workflows |
| **SCC Solar** | ✅ Great | ✅ Semantic | ⚙️ Medium | **Complex systems** |

## Why This Matters

Large Petri net models (100+ nodes) are:
- ❌ **Hard to understand** when manually arranged
- ❌ **Time-consuming** to layout by hand
- ❌ **Inconsistent** across different users
- ❌ **Fragile** when model changes

This algorithm **automatically** creates:
- ✅ Clear visual hierarchy
- ✅ Semantic grouping
- ✅ Professional appearance
- ✅ Reproducible results

Perfect for:
- 🏭 Industrial process models
- 🧬 Biological pathways
- 🔄 Workflow systems
- 📊 Resource allocation
- 🎯 System architectures

---

## Next Steps

1. **Approve plan** → Proceed to implementation
2. **Review detailed spec** → See FORCE_DIRECTED_LAYOUT_SCC_PLAN.md
3. **Prototype Phase 1** → SCC detection (2 weeks)
4. **Iterate based on feedback** → Refine algorithm

**Questions? Ready to proceed?** 🚀
